"""
API REST Router - Cuotas

Endpoints para cálculo de cuotas de guardias.
"""

from dataclasses import asdict

from application.use_cases.calcular_cuotas_use_case import (
    CalcularCuotasRequest,
    CalcularCuotasUseCase,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db

router = APIRouter(prefix="/cuotas", tags=["cuotas"])


@router.get("")
def calcular_cuotas(
    configuracion_id: int,
    solo_activos: bool = True,
    db: Session = Depends(get_db)
):
    """
    Calcula las cuotas de guardias para todos los profesores.

    Args:
        configuracion_id: ID de la configuración del curso
        solo_activos: Si True, solo considera profesores activos
        db: Sesión de base de datos (inyectada)

    Returns:
        dict: Response con cuotas calculadas

    Examples:
        GET /api/cuotas?configuracion_id=1&solo_activos=true
    """
    try:
        use_case = CalcularCuotasUseCase(db)
        request = CalcularCuotasRequest(
            configuracion_id=configuracion_id,
            solo_activos=solo_activos
        )
        response = use_case.execute(request)

        # Convertir DTOs a dict para JSON
        return {
            "exitoso": response.exitoso,
            "cuotas": response.cuotas,
            "cuotas_detalle": [asdict(dto) for dto in response.cuotas_detalle],
            "total_guardias": response.total_guardias,
            "mensaje": response.mensaje
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
