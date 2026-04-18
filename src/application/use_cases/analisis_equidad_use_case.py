"""
Use Case: Analizar Equidad de Guardias

Orquesta el análisis de equidad usando EquidadGuardiasService.
Coordina la obtención de datos y presentación de resultados.
"""

import logging
from typing import List

from services.distribucion_cuotas_service import DistribucionCuotasService
from services.equidad_guardias_service import EquidadGuardiasService
from infrastructure.database.models import Guardia, Profesor
from sqlalchemy.orm import Session

from application.dtos.domain_services_dtos import (
    AnalisisEquidadRequest,
    AnalisisEquidadResponse,
    CuotaProfesorDTO,
    EquidadMetricasDTO,
)

logger = logging.getLogger(__name__)


class AnalisisEquidadUseCase:
    """
    Use Case para analizar equidad de guardias asignadas.

    Responsabilidades:
    - Obtener guardias actuales
    - Calcular cuotas esperadas
    - Delegar análisis a EquidadGuardiasService
    - Generar recomendaciones
    - Mapear a DTOs
    """

    def __init__(self, session: Session):
        self.session = session
        self.equidad_service = EquidadGuardiasService(session)
        self.distribucion_service = DistribucionCuotasService(session)

    def execute(self, request: AnalisisEquidadRequest) -> AnalisisEquidadResponse:
        """
        Ejecuta el análisis de equidad.

        Args:
            request: Parámetros del análisis

        Returns:
            Response con métricas y recomendaciones
        """
        try:
            logger.info("Iniciando análisis de equidad")

            # 1. Obtener guardias asignadas
            query_guardias = self.session.query(Guardia)
            if request.configuracion_id:
                # Usar select_from para evitar ambigüedad en join
                query_guardias = query_guardias.select_from(Guardia).filter(
                    Guardia.curso_id == request.configuracion_id
                )
            guardias = query_guardias.all()

            if not guardias:
                return AnalisisEquidadResponse(
                    exitoso=False,
                    metricas=self._crear_metricas_vacias(),
                    cuotas=[],
                    recomendaciones=["No hay guardias asignadas para analizar"],
                    mensaje="No hay guardias para analizar",
                )

            # 2. Obtener profesores y calcular cuotas esperadas
            profesores = self.session.query(Profesor).filter(Profesor.activo.is_(True)).all()
            cuotas_esperadas = self.distribucion_service.calcular_cuotas(profesores)

            # 3. Delegar análisis a Domain Service
            indice = self.equidad_service.calcular_indice_equidad(guardias, cuotas_esperadas)
            desbalances = self.equidad_service.identificar_desbalances(
                guardias,
                cuotas_esperadas,
                umbral_leve=request.umbral_desbalance,
                umbral_moderado=request.umbral_desbalance * 2,
            )

            # 4. Calcular cuotas asignadas
            cuotas_asignadas = self._calcular_cuotas_asignadas(guardias)

            # 5. Calcular métricas adicionales
            metricas = self._calcular_metricas(
                cuotas_esperadas, cuotas_asignadas, indice, len(desbalances)
            )

            # 6. Mapear cuotas a DTOs
            cuotas_dto = self._mapear_cuotas_a_dtos(cuotas_esperadas, cuotas_asignadas, profesores)

            # 7. Generar recomendaciones
            recomendaciones = self._generar_recomendaciones(metricas, cuotas_dto, desbalances)

            logger.info(
                f"✓ Análisis completado: índice={indice:.2%}, desbalances={len(desbalances)}"
            )

            return AnalisisEquidadResponse(
                exitoso=True,
                metricas=metricas,
                cuotas=cuotas_dto if request.incluir_detalle else [],
                recomendaciones=recomendaciones,
                mensaje=f"Análisis completado. Nivel de equidad: {metricas.nivel_equidad}",
            )

        except Exception as e:
            logger.error(f"Error en análisis de equidad: {e}", exc_info=True)
            return AnalisisEquidadResponse(
                exitoso=False,
                metricas=self._crear_metricas_vacias(),
                cuotas=[],
                recomendaciones=[],
                mensaje=f"Error en análisis: {str(e)}",
            )

    def _calcular_cuotas_asignadas(self, guardias: List[Guardia]) -> dict[int, int]:
        """Cuenta guardias asignadas por profesor."""
        cuotas = {}
        for guardia in guardias:
            if guardia.profesor_id:
                cuotas[guardia.profesor_id] = cuotas.get(guardia.profesor_id, 0) + 1
        return cuotas

    def _calcular_metricas(
        self,
        cuotas_esperadas: dict[int, int],
        cuotas_asignadas: dict[int, int],
        indice: float,
        num_desbalances: int,
    ) -> EquidadMetricasDTO:
        """Calcula métricas de equidad."""
        import statistics

        # Calcular desviaciones
        desviaciones = []
        deficit_count = 0
        exceso_count = 0

        for prof_id, esperada in cuotas_esperadas.items():
            asignada = cuotas_asignadas.get(prof_id, 0)
            if esperada > 0:
                desviacion = abs(asignada - esperada) / esperada
                desviaciones.append(desviacion)

                if asignada < esperada:
                    deficit_count += 1
                elif asignada > esperada:
                    exceso_count += 1

        # Calcular estadísticas
        desv_std = statistics.stdev(desviaciones) if len(desviaciones) > 1 else 0
        coef_var = (
            desv_std / statistics.mean(desviaciones)
            if desviaciones and statistics.mean(desviaciones) > 0
            else 0
        )

        return EquidadMetricasDTO(
            indice_equidad=indice,
            coeficiente_variacion=coef_var,
            desviacion_estandar=desv_std,
            desbalances_detectados=num_desbalances,
            profesores_con_deficit=deficit_count,
            profesores_con_exceso=exceso_count,
        )

    def _mapear_cuotas_a_dtos(
        self,
        cuotas_esperadas: dict[int, int],
        cuotas_asignadas: dict[int, int],
        profesores: List[Profesor],
    ) -> List[CuotaProfesorDTO]:
        """Mapea cuotas a DTOs."""
        profesores_dict = {p.id: p for p in profesores}

        cuotas_dto = []
        for prof_id, esperada in cuotas_esperadas.items():
            profesor = profesores_dict.get(prof_id)
            if profesor:
                cuotas_dto.append(
                    CuotaProfesorDTO(
                        profesor_id=prof_id,
                        profesor_nombre=profesor.nombre_completo,
                        cuota_esperada=esperada,
                        cuota_asignada=cuotas_asignadas.get(prof_id, 0),
                    )
                )

        # Ordenar por deficit descendente
        return sorted(cuotas_dto, key=lambda x: x.deficit, reverse=True)

    def _generar_recomendaciones(
        self, metricas: EquidadMetricasDTO, cuotas: List[CuotaProfesorDTO], desbalances: List[str]
    ) -> List[str]:
        """Genera recomendaciones basadas en métricas."""
        recomendaciones = []

        # Recomendación por nivel de equidad
        if metricas.nivel_equidad == "DEFICIENTE":
            recomendaciones.append(
                "⚠️ CRÍTICO: La distribución tiene equidad deficiente. "
                "Considerar regenerar calendario con algoritmo más estricto."
            )
        elif metricas.nivel_equidad == "ACEPTABLE":
            recomendaciones.append(
                "⚠️ La distribución es aceptable pero mejorable. "
                "Revisar restricciones de profesores."
            )

        # Recomendaciones por déficit/exceso
        if metricas.profesores_con_deficit > 5:
            recomendaciones.append(
                f"📊 {metricas.profesores_con_deficit} profesores con déficit. "
                "Verificar disponibilidad y restricciones."
            )

        if metricas.profesores_con_exceso > 5:
            recomendaciones.append(
                f"📊 {metricas.profesores_con_exceso} profesores con exceso. "
                "Considerar redistribuir guardias."
            )

        # Top 3 profesores con mayor déficit
        if cuotas:
            top_deficit = [c for c in cuotas if c.deficit > 0][:3]
            if top_deficit:
                recomendaciones.append(
                    "👥 Profesores con mayor déficit: "
                    + ", ".join(f"{c.profesor_nombre} (-{c.deficit})" for c in top_deficit)
                )

        # Si no hay recomendaciones, todo bien
        if not recomendaciones:
            recomendaciones.append(
                "✅ La distribución tiene buena equidad, no se requieren ajustes."
            )

        return recomendaciones

    def _crear_metricas_vacias(self) -> EquidadMetricasDTO:
        """Crea métricas vacías para casos de error."""
        return EquidadMetricasDTO(
            indice_equidad=0.0,
            coeficiente_variacion=0.0,
            desviacion_estandar=0.0,
            desbalances_detectados=0,
            profesores_con_deficit=0,
            profesores_con_exceso=0,
        )
