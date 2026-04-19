"""
API REST Router - Estadísticas

Endpoints para obtener estadísticas y métricas agregadas.
"""

from datetime import date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from infrastructure.database.models import Guardia, Profesor
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import get_db

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


class TopProfesorResponse(BaseModel):
    id: int
    nombre: str
    total_guardias: int


class ResumenEstadisticasResponse(BaseModel):
    total_guardias: int
    asignadas: int
    sin_asignar: int
    cobertura_porcentaje: float
    por_turno: Dict[str, int]
    top_profesor: Optional[TopProfesorResponse] = None


class EstadisticaProfesorResponse(BaseModel):
    id: int
    nombre: str
    total_guardias: int


class EstadisticasPorProfesorResponse(BaseModel):
    profesores: List[EstadisticaProfesorResponse]
    total_profesores: int


@router.get("/resumen", response_model=ResumenEstadisticasResponse)
def obtener_resumen(
    configuracion_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Obtiene un resumen estadístico de guardias.

    Args:
        configuracion_id: ID de la configuración del curso
        fecha_inicio: Filtrar desde fecha (opcional)
        fecha_fin: Filtrar hasta fecha (opcional)
        db: Sesión de base de datos (inyectada)

    Returns:
        dict: Resumen estadístico

    Examples:
        GET /api/estadisticas/resumen?configuracion_id=1
    """
    try:
        query = db.query(Guardia).filter(Guardia.curso_id == configuracion_id)

        if fecha_inicio:
            query = query.filter(Guardia.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Guardia.fecha <= fecha_fin)

        # Total guardias
        total_guardias = query.count()

        # Guardias asignadas vs sin asignar
        asignadas = query.filter(Guardia.profesor_id.isnot(None)).count()
        sin_asignar = total_guardias - asignadas

        # Por turno
        por_turno = (
            db.query(Guardia.turno, func.count(Guardia.id).label("total"))
            .filter(Guardia.curso_id == configuracion_id)
            .group_by(Guardia.turno)
            .all()
        )

        # Profesor con más guardias
        top_profesor = (
            db.query(Guardia.profesor_id, func.count(Guardia.id).label("total"))
            .filter(Guardia.curso_id == configuracion_id, Guardia.profesor_id.isnot(None))
            .group_by(Guardia.profesor_id)
            .order_by(func.count(Guardia.id).desc())
            .first()
        )

        top_profesor_info = None
        if top_profesor:
            profesor = db.query(Profesor).get(top_profesor[0])
            if profesor:
                top_profesor_info = {
                    "id": profesor.id,
                    "nombre": str(profesor.nombre_completo),
                    "total_guardias": top_profesor[1],
                }

        porcentaje = (asignadas / total_guardias * 100) if total_guardias > 0 else 0
        return {
            "total_guardias": total_guardias,
            "asignadas": asignadas,
            "sin_asignar": sin_asignar,
            "cobertura_porcentaje": porcentaje,
            "por_turno": {turno: total for turno, total in por_turno},
            "top_profesor": top_profesor_info,
        }

    except (ValueError, TypeError, OSError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/por-profesor", response_model=EstadisticasPorProfesorResponse)
def estadisticas_por_profesor(configuracion_id: int, db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de guardias por profesor.

    Args:
        configuracion_id: ID de la configuración del curso
        db: Sesión de base de datos (inyectada)

    Returns:
        dict: Estadísticas por profesor

    Examples:
        GET /api/estadisticas/por-profesor?configuracion_id=1
    """
    try:
        # Guardias por profesor
        resultados = (
            db.query(
                Profesor.id,
                Profesor.nombre_completo,
                func.count(Guardia.id).label("total_guardias"),
            )
            .join(Guardia, Guardia.profesor_id == Profesor.id)
            .filter(Guardia.curso_id == configuracion_id)
            .group_by(Profesor.id, Profesor.nombre_completo)
            .order_by(func.count(Guardia.id).desc())
            .all()
        )

        return {
            "profesores": [
                {"id": r[0], "nombre": r[1], "total_guardias": r[2]} for r in resultados
            ],
            "total_profesores": len(resultados),
        }

    except (ValueError, TypeError, OSError) as e:
        raise HTTPException(status_code=500, detail=str(e))
