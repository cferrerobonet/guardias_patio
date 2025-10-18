"""
DTOs para Zona

Data Transfer Objects para operaciones con zonas de recreo.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ZonaDTO(BaseModel):
    """DTO de salida para Zona (lectura)."""

    id: int
    nombre_zona: str
    descripcion: Optional[str] = None
    capacidad_profesores: Optional[int] = None
    activa: bool = True

    class Config:
        """Configuración de Pydantic."""
        from_attributes = True


class CrearZonaDTO(BaseModel):
    """DTO de entrada para crear una zona."""

    nombre_zona: str = Field(..., min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    capacidad_profesores: Optional[int] = Field(None, ge=1, le=20)
    activa: bool = True


class ActualizarZonaDTO(BaseModel):
    """DTO de entrada para actualizar una zona (campos opcionales)."""

    nombre_zona: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    capacidad_profesores: Optional[int] = Field(None, ge=1, le=20)
    activa: Optional[bool] = None
