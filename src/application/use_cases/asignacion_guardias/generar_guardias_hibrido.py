"""
Use Case: Generar calendario de guardias con sistema híbrido.

Utiliza el orquestador híbrido que intenta iterativo primero,
muestra diagnóstico si falla, y permite al usuario decidir
si ajustar manualmente o usar ILP.
"""

from typing import Callable, Optional

from core.exceptions import BusinessLogicError
from core.observability import with_metrics
from models.models import Configuracion, Guardia
from services.asignador_guardias import guardar_guardias_en_bd
from services.calculador_guardias import obtener_estadisticas
from services.integrador_orquestador_ui import IntegradorOrquestadorUI
from sqlalchemy.orm import Session
from utils.logger import get_logger

from application.dtos.asignacion_guardias_dto import ResumenGeneracionDTO

logger = get_logger(__name__)


class GenerarGuardiasHibridoUseCase:
    """
    Caso de uso para generar guardias usando el sistema híbrido.

    Utiliza el OrquestadorAsignacionGuardias que:
    1. Intenta algoritmo iterativo (rápido)
    2. Si falla, muestra diagnóstico al usuario
    3. Usuario decide: ajustar manual o usar ILP
    4. Genera guardias con el enfoque elegido
    """

    def __init__(self, session: Session, parent_window=None):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy
            parent_window: Ventana padre para diálogos (opcional)
        """
        self.session = session
        self.parent_window = parent_window

    @with_metrics("generar_guardias_hibrido")
    def execute(
        self,
        eliminar_existentes: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> ResumenGeneracionDTO:
        """
        Ejecutar la generación de guardias con sistema híbrido.

        Args:
            eliminar_existentes: Si True, elimina guardias existentes antes
            progress_callback: Función para reportar progreso (mensaje, porcentaje)

        Returns:
            ResumenGeneracionDTO con el resultado

        Raises:
            BusinessLogicError: Si hay errores en la generación
        """
        try:
            # Eliminar guardias existentes si se solicita
            count_guardias = self.session.query(Guardia).count()

            if count_guardias > 0 and eliminar_existentes:
                if progress_callback:
                    progress_callback("Eliminando guardias existentes...", 10)

                self.session.query(Guardia).delete()
                self.session.commit()
                logger.info(f"✓ Eliminadas {count_guardias} guardias existentes")

            # Obtener estadísticas esperadas
            if progress_callback:
                progress_callback("Calculando distribución esperada...", 20)

            stats = obtener_estadisticas(self.session) or {}
            esperado = stats.get("slots_totales", 0)

            # Verificar configuración
            config = self.session.query(Configuracion).first()
            if not config:
                raise BusinessLogicError("No existe configuración del curso")

            # Usar integrador del sistema híbrido
            if progress_callback:
                progress_callback("Iniciando sistema híbrido...", 30)

            logger.info("🚀 Iniciando generación con sistema híbrido")

            # Crear wrapper para el callback de progreso
            # El integrador llama con (mensaje, porcentaje)
            # pero progress_callback espera (mensaje, porcentaje)
            def callback_wrapper(mensaje: str, porcentaje: int):
                if progress_callback:
                    # Escalar de 0-100 a 30-95 (65% del rango)
                    porcentaje_escalado = 30 + int(porcentaje * 0.65)
                    progress_callback(mensaje, porcentaje_escalado)

            # Obtener el worker thread si estamos ejecutando desde uno
            worker_thread = None
            try:
                from PyQt6.QtCore import QThread
                current_thread = QThread.currentThread()
                thread_type = type(current_thread).__name__
                logger.info(f"🔍 Thread actual: {current_thread} (tipo: {thread_type})")

                # CRÍTICO: Comparar por nombre de clase, no por isinstance
                # porque pueden ser módulos diferentes (src.presentation vs presentation)
                if thread_type == 'WorkerThread':
                    worker_thread = current_thread
                    logger.info("🧵 Ejecutando desde WorkerThread, usando callback thread-safe")
                else:
                    logger.info("🏠 Ejecutando desde thread principal, usando diálogo directo")
            except Exception as e:
                logger.error(f"❌ Error al detectar WorkerThread: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

            # Crear integrador con callback thread-safe si estamos en worker thread
            if worker_thread:
                # Pasar el método thread-safe del worker para decisiones del usuario
                integrador = IntegradorOrquestadorUI(
                    self.session,
                    self.parent_window,
                    callback_decision_custom=worker_thread.solicitar_decision_usuario
                )
            else:
                # Ejecutando desde thread principal, usar el método normal
                integrador = IntegradorOrquestadorUI(self.session, self.parent_window)

            try:
                resultado = integrador.generar_guardias_inteligente(
                    progress_callback=callback_wrapper
                )
            except Exception as e:
                logger.error(f"❌ Error en integrador: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise BusinessLogicError(
                    f"Error crítico durante la generación: {str(e)}"
                ) from e

            if not resultado.exitoso:
                # Verificar el tipo de error según la estrategia usada
                from services.orquestador_asignacion_guardias import EstrategiaUsada

                # CASO 1: Usuario canceló o timeout (NINGUNA estrategia)
                if resultado.estrategia_usada == EstrategiaUsada.NINGUNA:
                    logger.warning("⚠️  Generación cancelada o interrumpida")
                    raise BusinessLogicError(
                        f"Operación interrumpida.\n\n{resultado.mensaje_usuario}"
                    )

                # CASO 2: ILP falló (problema infactible o error técnico)
                elif resultado.estrategia_usada == EstrategiaUsada.ILP:
                    # Si el mensaje contiene "INFACTIBLE", es un problema de configuración
                    if 'INFACTIBLE' in resultado.mensaje_usuario.upper():
                        logger.error("❌ Problema matemáticamente infactible")
                        raise BusinessLogicError(
                            "No se pudo generar un calendario válido.\n\n"
                            "El problema es matemáticamente INFACTIBLE: "
                            "no existe ninguna asignación que cumpla todas las restricciones.\n\n"
                            "💡 Sugerencias:\n"
                            "• Aumenta el número de profesores disponibles\n"
                            "• Reduce el número de zonas por recreo\n"
                            "• Revisa las restricciones de disponibilidad\n\n"
                            f"{resultado.mensaje_usuario}"
                        )
                    else:
                        # Error técnico en ILP
                        logger.error(f"❌ Error técnico en ILP: {resultado.mensaje_usuario}")
                        raise BusinessLogicError(
                            f"Error durante la optimización ILP.\n\n{resultado.mensaje_usuario}"
                        )

                # CASO 3: Iterativo falló y usuario no continuó con ILP
                else:
                    logger.warning("⚠️  Resultado iterativo insuficiente")
                    raise BusinessLogicError(
                        f"No se pudo generar un calendario válido.\n\n"
                        f"Estrategia: {resultado.estrategia_usada.value}\n\n"
                        f"{resultado.mensaje_usuario}"
                    )

            guardias = resultado.guardias

            # Guardar en base de datos
            if progress_callback:
                progress_callback("Guardando guardias en base de datos...", 95)

            guardar_guardias_en_bd(self.session, guardias)

            if progress_callback:
                progress_callback("✅ Proceso completado", 100)

            # Generar resumen
            total_generado = len(guardias)
            diff = esperado - total_generado if esperado else 0

            # Construir resumen por profesor
            resumen_por_profesor = self._construir_resumen_por_profesor(guardias)

            mensaje = self._generar_mensaje(
                total_generado, esperado, diff, str(resultado.estrategia_usada)
            )

            logger.info(
                f"✓ Guardias generadas: {total_generado}/{esperado} "
                f"(estrategia: {resultado.estrategia_usada})"
            )

            return ResumenGeneracionDTO(
                guardias_generadas=total_generado,
                slots_esperados=esperado,
                slots_sin_cubrir=max(0, diff),
                resumen_por_profesor=resumen_por_profesor,
                mensaje=mensaje,
            )

        except BusinessLogicError:
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error al generar guardias: {str(e)}")
            raise BusinessLogicError(f"No se pudo generar: {str(e)}") from e

    def _construir_resumen_por_profesor(self, guardias) -> dict:
        """
        Construir resumen de guardias por profesor.

        Args:
            guardias: Lista de tuplas (dia, recreo, profesor, zona, turno)

        Returns:
            Dict con contador por profesor
        """
        resumen = {}
        for _, _, profesor_id, _, _ in guardias:
            if profesor_id:
                resumen[profesor_id] = resumen.get(profesor_id, 0) + 1
        return resumen

    def _generar_mensaje(
        self, total_generado: int, esperado: int, diff: int, estrategia: str
    ) -> str:
        """
        Generar mensaje descriptivo del resultado.

        Args:
            total_generado: Guardias generadas
            esperado: Slots esperados
            diff: Diferencia
            estrategia: Estrategia usada

        Returns:
            Mensaje descriptivo
        """
        if diff == 0:
            return (
                f"✅ Generación exitosa con {estrategia}\n\n"
                f"• {total_generado} guardias generadas\n"
                f"• Cobertura: 100%\n"
                f"• Todas las zonas y turnos cubiertos"
            )
        elif diff > 0:
            cobertura = (total_generado / esperado * 100) if esperado > 0 else 0
            return (
                f"⚠️ Generación parcial con {estrategia}\n\n"
                f"• {total_generado} de {esperado} guardias generadas\n"
                f"• Cobertura: {cobertura:.1f}%\n"
                f"• {diff} slots sin cubrir"
            )
        else:
            return (
                f"✅ Generación con excedente usando {estrategia}\n\n"
                f"• {total_generado} guardias generadas\n"
                f"• {abs(diff)} guardias adicionales"
            )
