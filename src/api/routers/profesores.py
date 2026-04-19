"""
API REST Router - Profesores

Endpoints para consultar información de profesores.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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


class PaginatedProfesoresResponse(BaseModel):
    """Respuesta paginada de profesores."""

    items: List[ProfesorResponse]
    total: int
    offset: int
    limit: int
    has_more: bool


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


def _build_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


@router.get("", response_model=PaginatedProfesoresResponse)
def listar_profesores(
    activo: Optional[bool] = None,
    turno: Optional[str] = None,
    offset: int = Query(default=0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(default=50, ge=1, le=200, description="Máximo de registros a devolver"),
    db: Session = Depends(get_db),
):
    """
    Lista profesores con filtros y paginación.

    - **offset**: Registros a saltar (para paginación, default 0)
    - **limit**: Máximo de registros (1-200, default 50)
    - **activo**: Filtrar por estado activo
    - **turno**: Filtrar por turno
    """
    try:
        use_case = ListarProfesoresUseCase(db)
        dtos = use_case.execute()
        if activo is not None:
            dtos = [p for p in dtos if p.activo == activo]
        if turno:
            dtos = [p for p in dtos if p.turno == turno]
        total = len(dtos)
        page = dtos[offset : offset + limit]
        return PaginatedProfesoresResponse(
            items=[
                ProfesorResponse(
                    id=p.id,
                    nombre_completo=p.nombre_completo,
                    horas_contrato=p.horas_contrato,
                    porcentaje_jornada=p.porcentaje_jornada,
                    turno=p.turno,
                    activo=p.activo,
                    email=p.email_corporativo,
                )
                for p in page
            ],
            total=total,
            offset=offset,
            limit=limit,
            has_more=(offset + limit) < total,
        )
    except (ValueError, TypeError, OSError, RuntimeError) as e:
        raise _build_error("internal_error", str(e), 500)


@router.get("/{profesor_id}", response_model=ProfesorResponse)
def obtener_profesor(profesor_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un profesor por ID.
    """
    try:
        use_case = ObtenerProfesorUseCase(db)
        dto = use_case.execute(profesor_id)
        if not dto:
            raise _build_error("not_found", f"Profesor {profesor_id} no encontrado", 404)
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
    except (ValueError, TypeError, OSError) as e:
        raise _build_error("internal_error", str(e), 500)
