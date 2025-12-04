"""
API REST Router - Profesores

Endpoints para consultar información de profesores.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from infrastructure.database.models import Profesor
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db

router = APIRouter(prefix="/profesores", tags=["profesores"])


class ProfesorResponse(BaseModel):
    """Schema de respuesta para profesor."""

    id: int
    nombre_completo: str
    horas_contrato: int
    porcentaje_jornada: int
    turno: str
    activo: bool
    email: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProfesorResponse])
def listar_profesores(
    activo: Optional[bool] = None, turno: Optional[str] = None, db: Session = Depends(get_db)
):
    """
    Lista todos los profesores con filtros opcionales.

    Args:
        activo: Filtrar por estado activo (opcional)
        turno: Filtrar por turno (opcional)
        db: Sesión de base de datos (inyectada)

    Returns:
        List[ProfesorResponse]: Lista de profesores

    Examples:
        GET /api/profesores?activo=true&turno=mañana
    """
    try:
        query = db.query(Profesor)

        if activo is not None:
            query = query.filter(Profesor.activo == activo)
        if turno:
            query = query.filter(Profesor.turno == turno)

        profesores = query.all()
        return profesores

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{profesor_id}", response_model=ProfesorResponse)
def obtener_profesor(profesor_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un profesor por ID.

    Args:
        profesor_id: ID del profesor
        db: Sesión de base de datos (inyectada)

    Returns:
        ProfesorResponse: Datos del profesor

    Examples:
        GET /api/profesores/1
    """
    try:
        profesor = db.query(Profesor).get(profesor_id)
        if not profesor:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        return profesor

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
