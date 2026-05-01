"""
API REST Router - Zonas

Endpoints CRUD para zonas de recreo.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from application.dtos.zona_dto import ActualizarZonaDTO, CrearZonaDTO
from application.use_cases.zona.actualizar_zona import ActualizarZonaUseCase
from application.use_cases.zona.crear_zona import CrearZonaUseCase
from application.use_cases.zona.eliminar_zona import EliminarZonaUseCase
from application.use_cases.zona.listar_zonas import ListarZonasUseCase
from application.use_cases.zona.obtener_zona import ObtenerZonaUseCase
from core.exceptions import BusinessLogicError, NotFoundError

router = APIRouter(prefix="/zonas", tags=["zonas"])


class ZonaResponse(BaseModel):
    """Schema de respuesta para zona."""

    id: int
    nombre_zona: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


def _build_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


@router.get("", response_model=List[ZonaResponse], summary="Listar zonas")
def listar_zonas(db: Session = Depends(get_db)):
    """Lista todas las zonas de recreo."""
    try:
        dtos = ListarZonasUseCase(db).execute()
        return [ZonaResponse(id=z.id, nombre_zona=z.nombre_zona, descripcion=z.descripcion) for z in dtos]
    except (ValueError, OSError) as e:
        raise _build_error("internal_error", str(e), 500)


@router.get("/{zona_id}", response_model=ZonaResponse, summary="Obtener zona por ID")
def obtener_zona(zona_id: int, db: Session = Depends(get_db)):
    """Obtiene una zona por ID."""
    try:
        dto = ObtenerZonaUseCase(db).execute(zona_id)
        if not dto:
            raise _build_error("not_found", f"Zona {zona_id} no encontrada", 404)
        return ZonaResponse(id=dto.id, nombre_zona=dto.nombre_zona, descripcion=dto.descripcion)
    except HTTPException:
        raise
    except NotFoundError:
        raise _build_error("not_found", f"Zona {zona_id} no encontrada", 404)
    except (ValueError, OSError) as e:
        raise _build_error("internal_error", str(e), 500)


@router.post("", response_model=ZonaResponse, status_code=201, summary="Crear zona")
def crear_zona(zona: CrearZonaDTO, db: Session = Depends(get_db)):
    """Crea una nueva zona de recreo."""
    try:
        dto = CrearZonaUseCase(db).execute(zona)
        return ZonaResponse(id=dto.id, nombre_zona=dto.nombre_zona, descripcion=dto.descripcion)
    except BusinessLogicError as e:
        raise _build_error("conflict", str(e), 409)
    except (ValueError, OSError) as e:
        raise _build_error("internal_error", str(e), 500)


@router.put("/{zona_id}", response_model=ZonaResponse, summary="Actualizar zona")
def actualizar_zona(zona_id: int, zona: ActualizarZonaDTO, db: Session = Depends(get_db)):
    """Actualiza una zona existente."""
    try:
        dto = ActualizarZonaUseCase(db).execute(zona_id, zona)
        if not dto:
            raise _build_error("not_found", f"Zona {zona_id} no encontrada", 404)
        return ZonaResponse(id=dto.id, nombre_zona=dto.nombre_zona, descripcion=dto.descripcion)
    except HTTPException:
        raise
    except NotFoundError:
        raise _build_error("not_found", f"Zona {zona_id} no encontrada", 404)
    except BusinessLogicError as e:
        raise _build_error("conflict", str(e), 409)
    except (ValueError, OSError) as e:
        raise _build_error("internal_error", str(e), 500)


@router.delete("/{zona_id}", status_code=204, summary="Eliminar zona")
def eliminar_zona(zona_id: int, db: Session = Depends(get_db)):
    """Elimina una zona del sistema."""
    try:
        EliminarZonaUseCase(db).execute(zona_id)
    except BusinessLogicError as e:
        raise _build_error("conflict", str(e), 409)
    except (ValueError, OSError) as e:
        raise _build_error("internal_error", str(e), 500)
