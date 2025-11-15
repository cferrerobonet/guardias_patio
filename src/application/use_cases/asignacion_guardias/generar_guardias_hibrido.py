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
            # El integrador llama con (mensaje, porcentaje) pero progress_callback espera (mensaje, porcentaje)
            def callback_wrapper(mensaje: str, porcentaje: int):
                if progress_callback:
                    # Escalar de 0-100 a 30-95 (65% del rango)
                    porcentaje_escalado = 30 + int(porcentaje * 0.65)
                    progress_callback(mensaje, porcentaje_escalado)

            # Usar el integrador
            integrador = IntegradorOrquestadorUI(self.session, self.parent_window)

            resultado = integrador.generar_guardias_inteligente(
                progress_callback=callback_wrapper
            )

            if not resultado.exitoso:
                raise BusinessLogicError(
                    "No se pudo generar un calendario válido. "
                    f"Estrategia usada: {resultado.estrategia_usada}"
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
