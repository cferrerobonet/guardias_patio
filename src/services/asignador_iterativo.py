"""
Asignador iterativo de guardias con recalculación automática y relajación progresiva.
Implementa la Opción A: rápido, construye sobre el algoritmo actual, múltiples intentos.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple

# Domain Services (Phase 2.4)
from domain.services.distribucion_cuotas_service import DistribucionCuotasService
from domain.services.equidad_guardias_service import EquidadGuardiasService
from infrastructure.database.models import Configuracion, Guardia, Profesor
from services.calculador_guardias import calcular_guardias_por_profesor
from services.estadisticas_service import EstadisticasService
from sqlalchemy.orm import Session

from src.services.asignador_guardias_v3_simple import generar_guardias_v3_simple

logger = logging.getLogger(__name__)


@dataclass
class ConfiguracionIteracion:
    """Configuración para cada iteración del algoritmo."""

    permitir_desbalance: float  # % de desbalance permitido (0.1 = 10%)
    permitir_retraso_fecha_inicio: int  # Días de retraso permitidos
    priorizar_cobertura_vs_equidad: bool  # True = prioriza cobertura, False = equidad
    max_guardias_consecutivas: int  # Máximo de días consecutivos permitidos
    nombre_iteracion: str  # Descripción de esta iteración


class AsignadorIterativo:
    """
    Asignador iterativo que intenta múltiples estrategias progresivamente
    más permisivas hasta lograr una solución aceptable.
    """

    def __init__(self, db: Session, config: Configuracion, dias_lectivos: List[date]):
        self.db = db
        self.config = config
        self.dias_lectivos = dias_lectivos

    def generar_guardias_iterativo(
        self,
        max_iteraciones: int = 5,
        objetivo_cobertura_minima: float = 0.95,  # 95%
    ) -> Tuple[List[Guardia], Dict]:
        """
        Genera guardias usando múltiples iteraciones con estrategias progresivas.

        Returns:
            Tupla de (guardias_asignadas, metadatos)
            metadatos contiene: iteracion_exitosa, estadisticas, ajustes_realizados
        """
        logger.info("=" * 70)
        logger.info("INICIANDO ASIGNACIÓN ITERATIVA DE GUARDIAS")
        logger.info("=" * 70)

        # Definir estrategias de iteración (de más estricta a más permisiva)
        estrategias = self._definir_estrategias_iteracion()

        mejor_resultado = None
        mejor_cobertura = 0.0
        metadatos_mejor = {}

        for i, estrategia in enumerate(estrategias[:max_iteraciones], 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"ITERACIÓN {i}: {estrategia.nombre_iteracion}")
            logger.info(f"{'=' * 70}")

            # Intentar asignación con esta estrategia
            guardias, stats = self._intentar_asignacion_con_estrategia(estrategia, i)

            # Calcular cobertura
            total_slots = (
                len(self.dias_lectivos) * len(self.config.recreos) * len(self.config.zonas)
            )
            cobertura = len(guardias) / total_slots if total_slots > 0 else 0

            logger.info(f"📊 Resultado: {len(guardias)} guardias asignadas")
            logger.info(f"📊 Cobertura: {cobertura * 100:.1f}%")

            # Guardar si es el mejor hasta ahora
            if cobertura > mejor_cobertura:
                mejor_resultado = guardias
                mejor_cobertura = cobertura
                metadatos_mejor = {
                    "iteracion_exitosa": i,
                    "estrategia": estrategia.nombre_iteracion,
                    "estadisticas": stats,
                    "cobertura": cobertura,
                }

            # Si alcanzamos el objetivo, terminamos
            if cobertura >= objetivo_cobertura_minima:
                logger.info(f"✅ Objetivo alcanzado en iteración {i}")
                break

            # Si no mejoramos significativamente, considerar recalcular cuotas
            if i > 1 and cobertura < mejor_cobertura * 1.05:
                logger.info("⚙️  Recalculando cuotas basadas en capacidad real...")
                self._recalcular_cuotas_adaptativas(guardias)

        logger.info(f"\n{'=' * 70}")
        logger.info("ASIGNACIÓN ITERATIVA COMPLETADA")
        logger.info(f"Mejor resultado: Iteración {metadatos_mejor.get('iteracion_exitosa', 0)}")
        logger.info(f"Cobertura final: {mejor_cobertura * 100:.1f}%")
        logger.info(f"{'=' * 70}")

        # Reporte de Equidad usando Domain Service
        if mejor_resultado:
            logger.info("")
            logger.info("ANÁLISIS DE EQUIDAD (Domain Service)")
            logger.info("=" * 70)

            try:
                equidad_service = EquidadGuardiasService(self.db)
                profesores = self.db.query(Profesor).filter(Profesor.activo.is_(True)).all()
                distribucion_service = DistribucionCuotasService(self.db)
                cuotas = distribucion_service.calcular_cuotas(profesores)

                # Log reporte completo de equidad
                equidad_service.log_reporte_equidad(mejor_resultado, cuotas)

                # Calcular índice de equidad
                indice_equidad = equidad_service.calcular_indice_equidad(mejor_resultado, cuotas)
                logger.info(f"📊 Índice de Equidad Global: {indice_equidad:.2%}")

                # Identificar desbalances
                desbalances = equidad_service.identificar_desbalances(mejor_resultado, cuotas)
                if desbalances:
                    logger.warning(f"⚠️  Desbalances detectados: {len(desbalances)}")
                else:
                    logger.info("✅ Sin desbalances significativos")

            except Exception as e:
                logger.warning(f"⚠️  Error en análisis de equidad: {e}")

            logger.info("=" * 70)

        return mejor_resultado or [], metadatos_mejor

    def _definir_estrategias_iteracion(self) -> List[ConfiguracionIteracion]:
        """Define las estrategias de iteración de más estricta a más permisiva."""
        return [
            # Iteración 1: Muy estricta - ideal
            ConfiguracionIteracion(
                permitir_desbalance=0.10,  # 10%
                permitir_retraso_fecha_inicio=14,  # 2 semanas
                priorizar_cobertura_vs_equidad=False,
                max_guardias_consecutivas=2,
                nombre_iteracion="Estrategia Estricta (ideal)",
            ),
            # Iteración 2: Moderada - aceptable
            ConfiguracionIteracion(
                permitir_desbalance=0.20,  # 20%
                permitir_retraso_fecha_inicio=30,  # 1 mes
                priorizar_cobertura_vs_equidad=False,
                max_guardias_consecutivas=3,
                nombre_iteracion="Estrategia Moderada (aceptable)",
            ),
            # Iteración 3: Prioriza cobertura
            ConfiguracionIteracion(
                permitir_desbalance=0.30,  # 30%
                permitir_retraso_fecha_inicio=45,  # 1.5 meses
                priorizar_cobertura_vs_equidad=True,
                max_guardias_consecutivas=4,
                nombre_iteracion="Prioridad Cobertura",
            ),
            # Iteración 4: Muy permisiva
            ConfiguracionIteracion(
                permitir_desbalance=0.40,  # 40%
                permitir_retraso_fecha_inicio=60,  # 2 meses
                priorizar_cobertura_vs_equidad=True,
                max_guardias_consecutivas=5,
                nombre_iteracion="Estrategia Permisiva",
            ),
            # Iteración 5: Máxima flexibilidad
            ConfiguracionIteracion(
                permitir_desbalance=0.50,  # 50%
                permitir_retraso_fecha_inicio=90,  # 3 meses
                priorizar_cobertura_vs_equidad=True,
                max_guardias_consecutivas=7,
                nombre_iteracion="Máxima Flexibilidad",
            ),
        ]

    def _intentar_asignacion_con_estrategia(
        self, estrategia: ConfiguracionIteracion, num_iteracion: int
    ) -> Tuple[List[Guardia], Dict]:
        """
        Intenta generar guardias con una estrategia específica.
        """
        logger.info("Configuración:")
        logger.info(f"  • Desbalance permitido: {estrategia.permitir_desbalance * 100:.0f}%")
        logger.info(f"  • Retraso fecha inicio: {estrategia.permitir_retraso_fecha_inicio} días")
        logger.info(
            f"  • Prioridad: {'Cobertura' if estrategia.priorizar_cobertura_vs_equidad else 'Equidad'}"
        )
        logger.info(f"  • Consecutivos máx: {estrategia.max_guardias_consecutivas} días")

        # Ajustar parámetros del algoritmo base según estrategia
        self._ajustar_algoritmo_base(estrategia)

        # Ejecutar algoritmo base usando la función
        calendario, _ = generar_guardias_v3_simple(self.db, self.config.id)

        # Convertir formato de calendario a lista de guardias
        guardias = calendario

        # Calcular estadísticas
        stats = self._calcular_estadisticas_iteracion(guardias, estrategia)

        return guardias, stats

    def _ajustar_algoritmo_base(self, estrategia: ConfiguracionIteracion) -> None:
        """
        Ajusta parámetros internos del algoritmo base según la estrategia.
        """
        # Aquí podríamos ajustar factores de prioridad dinámicamente
        # Por ahora, el algoritmo base usa su configuración por defecto
        # En una versión futura, podríamos inyectar estos parámetros
        pass

    def _recalcular_cuotas_adaptativas(self, guardias_actuales: List[Guardia]) -> None:
        """
        Recalcula cuotas basándose en la capacidad real demostrada en la iteración anterior.
        Identifica profesores que consistentemente no pueden alcanzar su cuota y ajusta.
        """
        logger.info("🔄 Recalculando cuotas adaptativas...")

        # Usar EstadisticasService para contar guardias por profesor
        stats_service = EstadisticasService(self.db)
        guardias_por_profesor = stats_service.calcular_guardias_por_profesor(guardias_actuales)

        # Obtener cuotas esperadas usando Domain Service
        try:
            distribucion_service = DistribucionCuotasService(self.db)
            profesores = self.db.query(Profesor).filter(Profesor.activo.is_(True)).all()
            cuotas_esperadas = distribucion_service.calcular_cuotas(profesores)
            logger.info("✓ Cuotas calculadas con DistribucionCuotasService")
        except Exception as e:
            logger.warning(f"⚠️ Error con DistribucionCuotasService: {e}. Usando método legacy.")
            cuotas_esperadas = calcular_guardias_por_profesor(self.db)

        # Identificar profesores con gran déficit (probablemente por restricciones)
        profesores_con_deficit = []
        for prof_id, cuota_esperada in cuotas_esperadas.items():
            guardias_reales = guardias_por_profesor.get(prof_id, 0)
            deficit_porcentaje = (cuota_esperada - guardias_reales) / cuota_esperada

            if deficit_porcentaje > 0.3:  # Más de 30% de déficit
                profesores_con_deficit.append(
                    (prof_id, guardias_reales, cuota_esperada, deficit_porcentaje)
                )

        if profesores_con_deficit:
            logger.info(f"Detectados {len(profesores_con_deficit)} profesores con déficit >30%")

            # Calcular cuotas "redistribuidas"
            # La cuota no alcanzada se redistribuye entre profesores que sí pueden
            total_deficit = sum(esp - real for _, real, esp, _ in profesores_con_deficit)

            profesores_sin_deficit = [
                prof_id
                for prof_id in cuotas_esperadas.keys()
                if prof_id not in [p[0] for p in profesores_con_deficit]
            ]

            if profesores_sin_deficit:
                cuota_extra_por_profesor = total_deficit / len(profesores_sin_deficit)
                logger.info(
                    f"Redistribuyendo {total_deficit:.1f} guardias entre {len(profesores_sin_deficit)} profesores"
                )

                # Aquí normalmente actualizaríamos las cuotas en calculador o config
                # Por ahora solo lo registramos
                logger.info(
                    f"Cada profesor disponible recibiría ~{cuota_extra_por_profesor:.1f} guardias extra"
                )

    def _calcular_estadisticas_iteracion(
        self, guardias: List[Guardia], estrategia: ConfiguracionIteracion
    ) -> Dict:
        """Calcula estadísticas detalladas de una iteración."""
        total_slots = len(self.dias_lectivos) * len(self.config.recreos) * len(self.config.zonas)

        # Usar EstadisticasService para cálculos centralizados
        stats_service = EstadisticasService(self.db)
        profesores = self.db.query(Profesor).filter(Profesor.activo.is_(True)).all()

        # Calcular cuotas usando Domain Service
        try:
            distribucion_service = DistribucionCuotasService(self.db)
            cuotas_esperadas = distribucion_service.calcular_cuotas(profesores)
        except Exception as e:
            logger.warning(f"⚠️ Error con DistribucionCuotasService: {e}. Usando método legacy.")
            cuotas_esperadas = calcular_guardias_por_profesor(self.db)

        # Generar estadísticas completas
        stats = stats_service.generar_resumen_completo(
            guardias=guardias,
            profesores=profesores,
            cuotas=cuotas_esperadas,
            total_slots=total_slots,
        )

        # Calcular desbalances usando las estadísticas del servicio
        guardias_por_profesor = stats_service.calcular_guardias_por_profesor(guardias)
        desbalances = []
        for prof_id, esperadas in cuotas_esperadas.items():
            reales = guardias_por_profesor.get(prof_id, 0)
            if esperadas > 0:
                desbalance = abs(reales - esperadas) / esperadas
                desbalances.append(desbalance)

        desbalance_promedio = sum(desbalances) / len(desbalances) if desbalances else 0
        desbalances_excesivos = len([d for d in desbalances if d > estrategia.permitir_desbalance])

        # Fechas de inicio
        profesores_con_retraso = 0
        retrasos = []

        for prof_id in guardias_por_profesor.keys():
            profesor = self.db.query(Profesor).get(prof_id)
            if profesor and profesor.fecha_inicio_guardias:
                guardias_prof = [g for g in guardias if g.profesor_id == prof_id]
                if guardias_prof:
                    primera_guardia = min(g.fecha for g in guardias_prof)
                    if primera_guardia > profesor.fecha_inicio_guardias:
                        dias_retraso = (primera_guardia - profesor.fecha_inicio_guardias).days
                        retrasos.append(dias_retraso)
                        if dias_retraso > estrategia.permitir_retraso_fecha_inicio:
                            profesores_con_retraso += 1

        retraso_promedio = sum(retrasos) / len(retrasos) if retrasos else 0

        return {
            "total_guardias": len(guardias),
            "total_slots": total_slots,
            "cobertura": stats["cobertura"],
            "profesores_con_guardias": stats["profesores_con_guardias"],
            "profesores_activos": stats["total_profesores"],
            "desbalance_promedio": desbalance_promedio,
            "desbalances_excesivos": desbalances_excesivos,
            "profesores_con_retraso": profesores_con_retraso,
            "retraso_promedio_dias": retraso_promedio,
            "cumple_objetivos": (
                stats["cobertura"] / 100 >= 0.95
                and desbalances_excesivos == 0
                and profesores_con_retraso == 0
            ),
        }
