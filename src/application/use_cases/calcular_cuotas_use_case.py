"""
Use Case: Calcular Cuotas de Guardias

Orquesta el cálculo de cuotas usando DistribucionCuotasService.
Este Use Case NO contiene lógica de negocio, solo coordina.
"""

import logging
from typing import List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from application.dtos.domain_services_dtos import (
    CalcularCuotasRequest,
    CalcularCuotasResponse,
    CuotaProfesorDTO,
)
from infrastructure.database.models import Configuracion, Profesor
from services.distribucion_cuotas_service import DistribucionCuotasService

logger = logging.getLogger(__name__)


class CalcularCuotasUseCase:
    """
    Use Case para calcular distribución de cuotas de guardias.

    Responsabilidades:
    - Validar request
    - Obtener datos necesarios (profesores activos)
    - Delegar cálculo a DistribucionCuotasService
    - Mapear resultado a DTOs
    - Retornar response
    """

    def __init__(self, session: Session):
        self.session = session
        self.distribucion_service = DistribucionCuotasService(session)

    def execute(self, request: CalcularCuotasRequest) -> CalcularCuotasResponse:
        """
        Ejecuta el caso de uso.

        Args:
            request: Parámetros de la operación

        Returns:
            Response con cuotas calculadas
        """
        try:
            logger.info(f"Calculando cuotas para configuración {request.configuracion_id}")

            # 1. Validar que existe la configuración
            config = self.session.query(Configuracion).get(request.configuracion_id)
            if not config:
                return CalcularCuotasResponse(
                    exitoso=False,
                    cuotas={},
                    cuotas_detalle=[],
                    total_guardias=0,
                    mensaje=f"Configuración {request.configuracion_id} no encontrada",
                )

            # 2. Obtener profesores
            query = self.session.query(Profesor)
            if request.solo_activos:
                query = query.filter(Profesor.activo.is_(True))
            profesores = query.all()

            if not profesores:
                return CalcularCuotasResponse(
                    exitoso=False,
                    cuotas={},
                    cuotas_detalle=[],
                    total_guardias=0,
                    mensaje="No hay profesores para calcular cuotas",
                )

            # 3. Delegar cálculo a Domain Service
            cuotas = self.distribucion_service.calcular_cuotas(profesores)

            # 4. Mapear a DTOs
            cuotas_detalle = self._mapear_cuotas_a_dtos(cuotas, profesores)
            total_guardias = sum(cuotas.values())

            logger.info(
                f"✓ Cuotas calculadas: {len(cuotas)} profesores, {total_guardias} guardias totales"
            )

            return CalcularCuotasResponse(
                exitoso=True,
                cuotas=cuotas,
                cuotas_detalle=cuotas_detalle,
                total_guardias=total_guardias,
                mensaje=f"Cuotas calculadas correctamente para {len(cuotas)} profesores",
            )

        except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
            logger.error(f"Error calculando cuotas: {e}", exc_info=True)
            return CalcularCuotasResponse(
                exitoso=False,
                cuotas={},
                cuotas_detalle=[],
                total_guardias=0,
                mensaje=f"Error al calcular cuotas: {str(e)}",
            )

    def _mapear_cuotas_a_dtos(
        self, cuotas: dict[int, int], profesores: List[Profesor]
    ) -> List[CuotaProfesorDTO]:
        """Mapea cuotas a DTOs con información de profesores."""
        profesores_dict = {p.id: p for p in profesores}

        cuotas_dto = []
        for profesor_id, cuota in cuotas.items():
            profesor = profesores_dict.get(profesor_id)
            if profesor:
                cuotas_dto.append(
                    CuotaProfesorDTO(
                        profesor_id=profesor_id,
                        profesor_nombre=profesor.nombre_completo,
                        cuota_esperada=cuota,
                        porcentaje_jornada=profesor.porcentaje_jornada,
                        cuota_asignada=0,  # Se llenará cuando haya guardias asignadas
                        turno=profesor.turno or "mixto",
                    )
                )

        # Ordenar por cuota descendente
        return sorted(cuotas_dto, key=lambda x: x.cuota_esperada, reverse=True)
