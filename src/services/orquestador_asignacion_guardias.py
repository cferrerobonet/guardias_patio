"""
Orquestador de asignación de guardias con fallback automático inteligente.
Intenta primero con algoritmo iterativo (rápido) y si falla ofrece al usuario
usar ILP (óptimo) o ajustar manualmente la configuración.
"""

import logging
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from infrastructure.database.models import Configuracion, Guardia, Zona
from sqlalchemy.orm import Session

from src.services.asignador_iterativo import AsignadorIterativo
from src.services.calculador_guardias import _parse_recreos_config
from src.services.diagnosticador_guardias import DiagnosticadorGuardias, DiagnosticoCompleto
from src.services.validador_guardias import ValidadorGuardias

logger = logging.getLogger(__name__)


class EstrategiaUsada(Enum):
    """Estrategia de asignación utilizada."""

    ITERATIVO = "iterativo"
    ILP = "ilp"
    NINGUNA = "ninguna"


@dataclass
class ResultadoOrquestacion:
    """Resultado completo de la orquestación."""

    exitoso: bool
    guardias: List[Guardia]
    estrategia_usada: EstrategiaUsada
    diagnostico: Optional[DiagnosticoCompleto]
    metadatos: Dict
    requiere_intervencion_usuario: bool
    mensaje_usuario: str


class OrquestadorAsignacionGuardias:
    """
    Orquestador inteligente que:
    1. Intenta asignación iterativa (rápida)
    2. Valida resultado
    3. Si falla, genera diagnóstico y pregunta al usuario
    4. Usuario decide: ajustar manual o usar ILP
    5. Si elige ILP, ejecuta y retorna resultado óptimo
    """

    def __init__(self, db: Session, config: Configuracion, dias_lectivos: List[date]):
        self.db = db
        self.config = config
        self.dias_lectivos = dias_lectivos

        # Cargar recreos y zonas y agregarlos al config
        self._enriquecer_configuracion()

        self.asignador_iterativo = AsignadorIterativo(db, config, dias_lectivos)
        self.diagnosticador = DiagnosticadorGuardias(db, config, dias_lectivos)
        self.validador = ValidadorGuardias(db)

        # Para ILP (carga diferida)
        self.asignador_ilp = None

    def _enriquecer_configuracion(self):
        """Agrega atributos recreos y zonas al objeto config."""
        # Cargar recreos desde recreos_config (JSON)
        recreos_data = _parse_recreos_config(self.config)
        if not recreos_data:
            # Fallback: generar recreos básicos desde las horas configuradas
            recreos_data = []
            rid = 0
            if self.config.hora_recreo1_manana:
                rid += 1
                recreos_data.append({"id": rid, "turno": "mañana", "zonas": 1})
            if self.config.hora_recreo2_manana:
                rid += 1
                recreos_data.append({"id": rid, "turno": "mañana", "zonas": 1})
            if self.config.hora_recreo1_tarde:
                rid += 1
                recreos_data.append({"id": rid, "turno": "tarde", "zonas": 1})
            if self.config.hora_recreo2_tarde:
                rid += 1
                recreos_data.append({"id": rid, "turno": "tarde", "zonas": 1})

        # Crear objetos simples para recreos
        from types import SimpleNamespace

        # IMPORTANTE: Agregar 'numero' que es usado por el asignador ILP
        for r in recreos_data:
            if "numero" not in r:
                r["numero"] = r["id"]  # numero = id por compatibilidad
        self.config.recreos = [SimpleNamespace(**r) for r in recreos_data]

        # Cargar zonas desde la BD
        self.config.zonas = self.db.query(Zona).all()

    def generar_guardias_con_fallback(
        self,
        umbral_cobertura_minima: float = 0.95,  # 95%
        umbral_problemas_criticos: int = 0,  # 0 problemas críticos permitidos
        callback_decision_usuario=None,  # Función que retorna decisión del usuario
        progress_callback=None,  # Función opcional para reportar progreso
    ) -> ResultadoOrquestacion:
        """
        Genera guardias intentando primero iterativo, luego ILP si es necesario.

        Args:
            umbral_cobertura_minima: Cobertura mínima aceptable (0.0 - 1.0)
            umbral_problemas_criticos: Número máximo de problemas críticos permitidos
            callback_decision_usuario: Función callback(diagnostico) -> decision
                Debe retornar: 'ajustar', 'continuar_ilp' o 'cancelar'
            progress_callback: Función opcional para reportar progreso (mensaje, porcentaje)

        Returns:
            ResultadoOrquestacion con el resultado final
        """
        logger.info("=" * 80)
        logger.info("ORQUESTADOR DE ASIGNACIÓN DE GUARDIAS")
        logger.info("Estrategia: Iterativo → Validación → [Usuario] → ILP (si necesario)")
        logger.info("=" * 80)

        # FASE 1: Intentar con algoritmo iterativo
        logger.info("\n" + "=" * 80)
        logger.info("FASE 1: ASIGNACIÓN ITERATIVA (Rápida)")
        logger.info("=" * 80)

        if progress_callback:
            progress_callback("Ejecutando algoritmo iterativo...", 40)

        logger.info("⏳ Llamando a asignador_iterativo.generar_guardias_iterativo...")
        guardias_iterativo, metadatos_iterativo = (
            self.asignador_iterativo.generar_guardias_iterativo(
                max_iteraciones=5, objetivo_cobertura_minima=umbral_cobertura_minima
            )
        )
        logger.info(f"✓ Asignación iterativa completada: {len(guardias_iterativo)} guardias")

        # FASE 2: Validar resultado iterativo
        logger.info("\n" + "=" * 80)
        logger.info("FASE 2: VALIDACIÓN DEL RESULTADO")
        logger.info("=" * 80)

        if progress_callback:
            progress_callback("Validando resultados...", 60)

        diagnostico = self.diagnosticador.diagnosticar_resultado(guardias_iterativo)

        # Mostrar diagnóstico
        logger.info(diagnostico.mensaje_resumen)

        # Decidir si el resultado es aceptable
        cobertura = diagnostico.estadisticas["cobertura_porcentaje"] / 100
        num_criticos = len(diagnostico.problemas_criticos)

        resultado_aceptable = (
            cobertura >= umbral_cobertura_minima and num_criticos <= umbral_problemas_criticos
        )

        if resultado_aceptable:
            logger.info("\n✅ Resultado iterativo es ACEPTABLE")
            logger.info(
                f"   Cobertura: {cobertura * 100:.1f}% (objetivo: {umbral_cobertura_minima * 100:.0f}%)"
            )
            logger.info(
                f"   Problemas críticos: {num_criticos} (máximo: {umbral_problemas_criticos})"
            )

            return ResultadoOrquestacion(
                exitoso=True,
                guardias=guardias_iterativo,
                estrategia_usada=EstrategiaUsada.ITERATIVO,
                diagnostico=diagnostico,
                metadatos=metadatos_iterativo,
                requiere_intervencion_usuario=False,
                mensaje_usuario=self._generar_mensaje_exito(
                    EstrategiaUsada.ITERATIVO, diagnostico, metadatos_iterativo
                ),
            )

        # FASE 3: Resultado no aceptable - Solicitar decisión al usuario
        logger.info("\n" + "=" * 80)
        logger.info("FASE 3: RESULTADO NO ACEPTABLE - SOLICITAR DECISIÓN USUARIO")
        logger.info("=" * 80)
        logger.info(
            f"⚠️  Cobertura: {cobertura * 100:.1f}% (objetivo: {umbral_cobertura_minima * 100:.0f}%)"
        )
        logger.info(f"⚠️  Problemas críticos: {num_criticos}")

        if callback_decision_usuario is None:
            logger.warning("No hay callback de usuario. Retornando resultado parcial.")
            return ResultadoOrquestacion(
                exitoso=False,
                guardias=guardias_iterativo,
                estrategia_usada=EstrategiaUsada.ITERATIVO,
                diagnostico=diagnostico,
                metadatos=metadatos_iterativo,
                requiere_intervencion_usuario=True,
                mensaje_usuario=self._generar_mensaje_requiere_intervencion(diagnostico),
            )

        # Llamar al callback para obtener decisión del usuario
        try:
            logger.info("⏳ Esperando decisión del usuario...")
            decision = callback_decision_usuario(diagnostico)
            logger.info(f"✓ Decisión recibida del usuario: {decision}")
        except Exception as e:
            logger.error(f"❌ Error al obtener decisión del usuario: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            decision = "error"

        logger.info(f"Decisión del usuario: {decision}")

        if decision == "ajustar":
            # Usuario quiere ajustar manualmente
            logger.info("Usuario eligió ajustar configuración manualmente")
            return ResultadoOrquestacion(
                exitoso=False,
                guardias=guardias_iterativo,
                estrategia_usada=EstrategiaUsada.ITERATIVO,
                diagnostico=diagnostico,
                metadatos=metadatos_iterativo,
                requiere_intervencion_usuario=True,
                mensaje_usuario="Por favor, ajuste la configuración según las sugerencias del diagnóstico.",
            )

        elif decision == "continuar_ilp":
            # Usuario quiere intentar con ILP
            return self._ejecutar_fase_ilp(
                guardias_iterativo, diagnostico, metadatos_iterativo, progress_callback
            )

        elif decision == "timeout":
            logger.error("❌ Timeout esperando respuesta del usuario")
            return ResultadoOrquestacion(
                exitoso=False,
                guardias=guardias_iterativo,
                estrategia_usada=EstrategiaUsada.NINGUNA,
                diagnostico=diagnostico,
                metadatos=metadatos_iterativo,
                requiere_intervencion_usuario=True,
                mensaje_usuario=(
                    "El sistema no recibió respuesta del diálogo de decisión en 5 minutos.\n\n"
                    "Cierra otros diálogos en pantalla e inténtalo nuevamente."
                ),
            )

        elif decision == "error":
            logger.error("❌ No se pudo mostrar el diálogo de decisión")
            return ResultadoOrquestacion(
                exitoso=False,
                guardias=guardias_iterativo,
                estrategia_usada=EstrategiaUsada.NINGUNA,
                diagnostico=diagnostico,
                metadatos=metadatos_iterativo,
                requiere_intervencion_usuario=True,
                mensaje_usuario=(
                    "Ocurrió un error al mostrar el diagnóstico para tomar una decisión.\n\n"
                    "Reinicia la aplicación e inténtalo de nuevo."
                ),
            )

        else:  # 'cancelar'
            logger.info("Usuario canceló la operación")
            return ResultadoOrquestacion(
                exitoso=False,
                guardias=[],
                estrategia_usada=EstrategiaUsada.NINGUNA,
                diagnostico=diagnostico,
                metadatos={},
                requiere_intervencion_usuario=False,
                mensaje_usuario="Operación cancelada por el usuario.",
            )

    def _ejecutar_fase_ilp(
        self,
        guardias_iterativo: List[Guardia],
        diagnostico_previo: DiagnosticoCompleto,
        metadatos_previos: Dict,
        progress_callback=None,
    ) -> ResultadoOrquestacion:
        """Ejecuta la fase ILP del orquestador."""
        logger.info("\n" + "=" * 80)
        logger.info("FASE 4: ASIGNACIÓN ILP (Óptima Garantizada)")
        logger.info("=" * 80)

        if progress_callback:
            progress_callback("Ejecutando optimización ILP...", 70)

        try:
            # Importar e inicializar ILP (carga diferida)
            from src.services.asignador_ilp import AsignadorILP

            if self.asignador_ilp is None:
                self.asignador_ilp = AsignadorILP(self.db, self.config, self.dias_lectivos)

            # Ejecutar ILP
            resultado_ilp = self.asignador_ilp.generar_guardias_ilp(
                limite_tiempo_segundos=300,  # 5 minutos
                priorizar_fecha_inicio=True,
                priorizar_equidad=True,
            )

            if progress_callback:
                progress_callback("Analizando solución ILP...", 90)

            if resultado_ilp.exitoso:
                logger.info("✅ ILP encontró solución óptima")

                # Diagnosticar resultado ILP
                diagnostico_ilp = self.diagnosticador.diagnosticar_resultado(resultado_ilp.guardias)

                return ResultadoOrquestacion(
                    exitoso=True,
                    guardias=resultado_ilp.guardias,
                    estrategia_usada=EstrategiaUsada.ILP,
                    diagnostico=diagnostico_ilp,
                    metadatos={
                        "iterativo": metadatos_previos,
                        "ilp": resultado_ilp.estadisticas,
                        "tiempo_ilp": resultado_ilp.tiempo_solucion_segundos,
                    },
                    requiere_intervencion_usuario=False,
                    mensaje_usuario=self._generar_mensaje_exito(
                        EstrategiaUsada.ILP, diagnostico_ilp, resultado_ilp.estadisticas
                    ),
                )
            else:
                # ILP también falló - problema es infactible
                logger.error("❌ ILP no pudo encontrar solución (problema infactible)")
                logger.error(resultado_ilp.diagnostico_infactibilidad)

                return ResultadoOrquestacion(
                    exitoso=False,
                    guardias=[],
                    estrategia_usada=EstrategiaUsada.ILP,
                    diagnostico=diagnostico_previo,
                    metadatos={
                        "iterativo": metadatos_previos,
                        "ilp_infactible": True,
                        "diagnostico_infactibilidad": resultado_ilp.diagnostico_infactibilidad,
                    },
                    requiere_intervencion_usuario=True,
                    mensaje_usuario=(
                        "El problema es matemáticamente INFACTIBLE. "
                        "No existe asignación que cumpla todas las restricciones. "
                        "Revise el diagnóstico y ajuste la configuración."
                    ),
                )

        except ImportError as e:
            logger.error(f"Error: OR-Tools no está instalado. {e}")
            return ResultadoOrquestacion(
                exitoso=False,
                guardias=guardias_iterativo,
                estrategia_usada=EstrategiaUsada.ITERATIVO,
                diagnostico=diagnostico_previo,
                metadatos=metadatos_previos,
                requiere_intervencion_usuario=True,
                mensaje_usuario=(
                    "ILP no disponible (falta instalar OR-Tools). "
                    "Instalar con: pip install ortools\n"
                    "Por ahora, se usa resultado iterativo con problemas."
                ),
            )
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Error inesperado en ILP: {e}", exc_info=True)
            return ResultadoOrquestacion(
                exitoso=False,
                guardias=guardias_iterativo,
                estrategia_usada=EstrategiaUsada.ITERATIVO,
                diagnostico=diagnostico_previo,
                metadatos=metadatos_previos,
                requiere_intervencion_usuario=True,
                mensaje_usuario=f"Error en ILP: {str(e)}",
            )

    def _generar_mensaje_exito(
        self, estrategia: EstrategiaUsada, diagnostico: DiagnosticoCompleto, metadatos: Dict
    ) -> str:
        """Genera mensaje de éxito para el usuario."""
        lineas = []

        lineas.append("✅ ASIGNACIÓN COMPLETADA CON ÉXITO")
        lineas.append("")

        if estrategia == EstrategiaUsada.ITERATIVO:
            lineas.append("🚀 Estrategia: Algoritmo Iterativo (Rápido)")
            if "iteracion_exitosa" in metadatos:
                lineas.append(f"   Iteración exitosa: {metadatos['iteracion_exitosa']}")
        else:
            lineas.append("🎯 Estrategia: ILP - Solución Óptima Matemática")
            if "tiempo_solucion" in metadatos:
                lineas.append(f"   Tiempo de cálculo: {metadatos['tiempo_solucion']:.1f}s")

        lineas.append("")
        stats = diagnostico.estadisticas
        lineas.append("📊 Resultado:")
        lineas.append(
            f"   • Guardias asignadas: {stats['total_guardias_asignadas']} de {stats['total_slots_esperados']}"
        )
        lineas.append(f"   • Cobertura: {stats['cobertura_porcentaje']:.1f}%")
        lineas.append(
            f"   • Participación: {stats['profesores_con_guardias']}/{stats['profesores_activos_totales']} profesores"
        )

        if diagnostico.problemas_medios:
            lineas.append("")
            lineas.append(
                f"ℹ️  Se detectaron {len(diagnostico.problemas_medios)} problema(s) menor(es)"
            )
            lineas.append("   (no afectan la validez de la asignación)")

        return "\n".join(lineas)

    def _generar_mensaje_requiere_intervencion(self, diagnostico: DiagnosticoCompleto) -> str:
        """Genera mensaje cuando se requiere intervención del usuario."""
        lineas = []

        lineas.append("⚠️  LA ASIGNACIÓN REQUIERE SU ATENCIÓN")
        lineas.append("")

        if diagnostico.problemas_criticos:
            lineas.append(
                f"🔴 {len(diagnostico.problemas_criticos)} problema(s) crítico(s) detectado(s)"
            )

        if diagnostico.problemas_altos:
            lineas.append(
                f"🟠 {len(diagnostico.problemas_altos)} problema(s) importante(s) detectado(s)"
            )

        lineas.append("")
        lineas.append("Opciones:")
        lineas.append("  1. Revisar y ajustar configuración manualmente")
        lineas.append("     (disponibilidades, zonas, recreos, ausencias)")
        lineas.append("  2. Continuar con algoritmo ILP avanzado")
        lineas.append("     (garantiza solución óptima si existe)")

        return "\n".join(lineas)
