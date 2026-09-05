"""
API REST Router - Equidad

Endpoints para análisis de equidad de guardias.
"""

from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from application.dtos.domain_services_dtos import AnalisisEquidadRequest
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase

router = APIRouter(prefix="/equidad", tags=["equidad"])


class AnalisisEquidadApiResponse(BaseModel):
    exitoso: bool
    metricas: Dict[str, Any]
    cuotas: List[Dict[str, Any]]
    recomendaciones: List[str]
    mensaje: str


@router.get("", response_model=AnalisisEquidadApiResponse, summary="Análisis de equidad")
def analizar_equidad(
    configuracion_id: int,
    umbral_desbalance: float = 0.15,
    incluir_detalle: bool = False,
    db: Session = Depends(get_db),
):
    """
    Analiza la equidad en la distribución de guardias.

    Args:
        configuracion_id: ID de la configuración del curso
        umbral_desbalance: Umbral para detectar desbalances (default: 0.15)
        incluir_cuotas_detalle: Si incluir detalle de cuotas por profesor
        db: Sesión de base de datos (inyectada)

    Returns:
        dict: Response con análisis de equidad

    Examples:
        GET /api/equidad?configuracion_id=1&umbral_desbalance=0.15
    """
    try:
        use_case = AnalisisEquidadUseCase(db)
        request = AnalisisEquidadRequest(
            configuracion_id=configuracion_id,
            umbral_desbalance=umbral_desbalance,
            incluir_detalle=incluir_detalle,
        )
        response = use_case.execute(request)

        metricas = asdict(response.metricas)
        nivel_equidad = getattr(response.metricas, "nivel_equidad", None)
        metricas["nivel_equidad"] = (
            nivel_equidad if isinstance(nivel_equidad, str) else str(nivel_equidad or "")
        )

        cuotas = []
        for dto in response.cuotas:
            cuota = asdict(dto)
            cuota["porcentaje_cumplimiento"] = dto.porcentaje_cumplimiento
            cuota["deficit"] = dto.deficit
            cuotas.append(cuota)

        return {
            "exitoso": response.exitoso,
            "metricas": metricas,
            "cuotas": cuotas,
            "recomendaciones": response.recomendaciones,
            "mensaje": response.mensaje,
        }
    except (ValueError, TypeError, OSError) as e:
        raise HTTPException(status_code=500, detail=str(e))
