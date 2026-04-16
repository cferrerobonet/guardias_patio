"""
API REST Router - Guardias

Endpoints para gestión de guardias (consultar, generar, asignar).
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from infrastructure.database.models import Guardia, Profesor, Zona
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from api.dependencies import get_db

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
    curso_id: int

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
        query = db.query(Guardia).filter(Guardia.curso_id == configuracion_id)

        if fecha_inicio:
            query = query.filter(Guardia.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Guardia.fecha <= fecha_fin)
        if profesor_id:
            query = query.filter(Guardia.profesor_id == profesor_id)
        if zona_id:
            query = query.filter(Guardia.zona_id == zona_id)
        if turno:
            query = query.filter(Guardia.turno == turno)

        guardias = (
            query.options(joinedload(Guardia.zona), joinedload(Guardia.profesor))
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for guardia in guardias:
            result.append(
                GuardiaResponse(
                    id=guardia.id,
                    fecha=guardia.fecha,
                    recreo=guardia.recreo,
                    turno=guardia.turno,
                    zona_id=guardia.zona_id,
                    zona_nombre=guardia.zona.nombre if guardia.zona else None,
                    profesor_id=guardia.profesor_id,
                    profesor_nombre=guardia.profesor.nombre_completo if guardia.profesor else None,
                    curso_id=guardia.curso_id,
                )
            )

        return result

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
        query = db.query(Guardia).filter(Guardia.curso_id == configuracion_id)

        if fecha_inicio:
            query = query.filter(Guardia.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Guardia.fecha <= fecha_fin)
        if profesor_id:
            query = query.filter(Guardia.profesor_id == profesor_id)
        if zona_id:
            query = query.filter(Guardia.zona_id == zona_id)
        if turno:
            query = query.filter(Guardia.turno == turno)

        total = query.count()
        return {"total": total}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al contar guardias")
