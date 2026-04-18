"""
API REST Router - Guardias

Endpoints para gestión de guardias (consultar, generar, asignar).
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from application.dtos import FiltroGuardiasDTO
from application.use_cases.guardia.obtener_guardias import ObtenerGuardiasUseCase

router = APIRouter(prefix="/guardias", tags=["guardias"])


class GuardiaResponse(BaseModel):
    """Schema de respuesta para guardia."""

    id: int
    fecha: date
    recreo: int
    turno: str
    zona_id: int
    zona_nombre: Optional[str] = None
    profesor_id: Optional[int] = None
    profesor_nombre: Optional[str] = None
    es_sustitucion: bool = False

    class Config:
        from_attributes = True


@router.get("", response_model=List[GuardiaResponse])
def obtener_guardias(
    configuracion_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    profesor_id: Optional[int] = None,
    zona_id: Optional[int] = None,
    turno: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Obtiene guardias con filtros opcionales.

    Args:
        configuracion_id: ID de la configuración del curso
        fecha_inicio: Filtrar desde fecha (opcional)
        fecha_fin: Filtrar hasta fecha (opcional)
        profesor_id: Filtrar por profesor (opcional)
        zona_id: Filtrar por zona (opcional)
        turno: Filtrar por turno (opcional)
        limit: Máximo de resultados (default: 100, max: 1000)
        offset: Desplazamiento para paginación
        db: Sesión de base de datos (inyectada)

    Returns:
        List[GuardiaResponse]: Lista de guardias

    Examples:
        GET /api/guardias?configuracion_id=1&turno=mañana&limit=50
    """
    try:
        filtros = FiltroGuardiasDTO(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            profesor_id=profesor_id,
            zona_id=zona_id,
            turno=turno,
        )
        use_case = ObtenerGuardiasUseCase(db)
        dtos = use_case.execute(filtros)

        # Filtrar por curso y paginar
        dtos = [g for g in dtos if True]  # curso_id se filtra en el use case si se añade
        paginados = dtos[offset: offset + limit]

        return [
            GuardiaResponse(
                id=g.id,
                fecha=g.fecha,
                recreo=g.numero_recreo,
                turno=g.turno,
                zona_id=g.zona_id,
                zona_nombre=g.zona_nombre,
                profesor_id=g.profesor_id,
                profesor_nombre=g.profesor_nombre,
                es_sustitucion=g.es_sustitucion,
            )
            for g in paginados
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener guardias")


@router.get("/count")
def contar_guardias(
    configuracion_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    profesor_id: Optional[int] = None,
    zona_id: Optional[int] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Cuenta guardias con filtros opcionales.

    Args:
        configuracion_id: ID de la configuración del curso
        fecha_inicio: Filtrar desde fecha (opcional)
        fecha_fin: Filtrar hasta fecha (opcional)
        profesor_id: Filtrar por profesor (opcional)
        zona_id: Filtrar por zona (opcional)
        turno: Filtrar por turno (opcional)
        db: Sesión de base de datos (inyectada)

    Returns:
        dict: Total de guardias

    Examples:
        GET /api/guardias/count?configuracion_id=1&turno=tarde
    """
    try:
        filtros = FiltroGuardiasDTO(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            profesor_id=profesor_id,
            zona_id=zona_id,
            turno=turno,
        )
        use_case = ObtenerGuardiasUseCase(db)
        dtos = use_case.execute(filtros)
        return {"total": len(dtos)}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al contar guardias")

