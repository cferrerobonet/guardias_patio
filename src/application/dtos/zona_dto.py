"""
DTOs para Zona

Data Transfer Objects para operaciones con zonas de recreo.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ZonaDTO(BaseModel):
    """DTO de salida para Zona (lectura)."""

    id: int
    nombre_zona: str
    descripcion: Optional[str] = None

    model_config = {"from_attributes": True}


class CrearZonaDTO(BaseModel):
    """DTO de entrada para crear una zona."""

    nombre_zona: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)

    @field_validator("nombre_zona")
    @classmethod
    def validar_nombre_zona(cls, v: str) -> str:
        """Validar que el nombre de la zona no esté vacío después de strip"""
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("El nombre de la zona no puede estar vacío")
        if len(v_stripped) < 2:
            raise ValueError("El nombre de la zona debe tener al menos 2 caracteres")
        return v_stripped


class ActualizarZonaDTO(BaseModel):
    """DTO de entrada para actualizar una zona."""

    nombre_zona: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)

    @field_validator("nombre_zona")
    @classmethod
    def validar_nombre_zona(cls, v: Optional[str]) -> Optional[str]:
        """Validar que el nombre de la zona no esté vacío después de strip"""
        if v is None:
            return v
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("El nombre de la zona no puede estar vacío")
        if len(v_stripped) < 2:
            raise ValueError("El nombre de la zona debe tener al menos 2 caracteres")
        return v_stripped
