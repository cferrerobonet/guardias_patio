"""
API REST Router - Profesores

Endpoints para consultar información de profesores.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from application.use_cases.profesor.listar_profesores import ListarProfesoresUseCase
from application.use_cases.profesor.obtener_profesor import ObtenerProfesorUseCase

router = APIRouter(prefix="/profesores", tags=["profesores"])


class ProfesorResponse(BaseModel):
    """Schema de respuesta para profesor."""

    id: int
    nombre_completo: str
    horas_contrato: float
    porcentaje_jornada: float
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
        use_case = ListarProfesoresUseCase(db)
        dtos = use_case.execute()
        if activo is not None:
            dtos = [p for p in dtos if p.activo == activo]
        if turno:
            dtos = [p for p in dtos if p.turno == turno]
        return [
            ProfesorResponse(
                id=p.id,
                nombre_completo=p.nombre_completo,
                horas_contrato=p.horas_contrato,
                porcentaje_jornada=p.porcentaje_jornada,
                turno=p.turno,
                activo=p.activo,
                email=p.email_corporativo,
            )
            for p in dtos
        ]
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
        use_case = ObtenerProfesorUseCase(db)
        dto = use_case.execute(profesor_id)
        if not dto:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        return ProfesorResponse(
            id=dto.id,
            nombre_completo=dto.nombre_completo,
            horas_contrato=dto.horas_contrato,
            porcentaje_jornada=dto.porcentaje_jornada,
            turno=dto.turno,
            activo=dto.activo,
            email=dto.email_corporativo,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
