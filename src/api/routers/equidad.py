"""
API REST Router - Equidad

Endpoints para análisis de equidad de guardias.
"""

from dataclasses import asdict

from application.dtos.domain_services_dtos import AnalisisEquidadRequest
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db

router = APIRouter(prefix="/equidad", tags=["equidad"])


@router.get("")
def analizar_equidad(
    configuracion_id: int,
    umbral_desbalance: float = 0.15,
    incluir_cuotas_detalle: bool = False,
    db: Session = Depends(get_db)
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
            incluir_cuotas_detalle=incluir_cuotas_detalle
        )
        response = use_case.execute(request)

        # Convertir DTOs a dict
        return {
            "exitoso": response.exitoso,
            "metricas": asdict(response.metricas),
            "cuotas": [asdict(dto) for dto in response.cuotas],
            "recomendaciones": response.recomendaciones,
            "mensaje": response.mensaje
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
