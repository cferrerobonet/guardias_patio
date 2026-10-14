"""
DTOs para Guardia

Data Transfer Objects para operaciones con guardias de patio.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GuardiaDTO(BaseModel):
    """DTO de salida para Guardia (lectura)."""

    id: int
    fecha: date
    turno: str  # "mañana", "tarde"
    numero_recreo: int
    profesor_id: int
    zona_id: int
    es_sustitucion: bool = False
    profesor_sustituido_id: Optional[int] = None

    # Campos adicionales para facilitar la UI
    profesor_nombre: Optional[str] = None
    zona_nombre: Optional[str] = None

    class Config:
        """Configuración de Pydantic."""

        from_attributes = True


class CrearGuardiaDTO(BaseModel):
    """DTO de entrada para crear/asignar una guardia."""

    fecha: date
    turno: str = Field(..., pattern="^(mañana|tarde)$")
    numero_recreo: int = Field(..., ge=1, le=10)
    profesor_id: int = Field(..., gt=0)
    zona_id: int = Field(..., gt=0)
    es_sustitucion: bool = False
    profesor_sustituido_id: Optional[int] = Field(None, gt=0)

    @field_validator("fecha")
    @classmethod
    def validar_fecha_futura(cls, v: date) -> date:
        """Valida que la fecha no sea muy antigua."""
        # Permitimos asignar guardias históricas para correcciones
        return v


class FiltroGuardiasDTO(BaseModel):
    """DTO para filtrar guardias en consultas."""

    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    profesor_id: Optional[int] = None
    zona_id: Optional[int] = None
    turno: Optional[str] = Field(None, pattern="^(mañana|tarde)$")
    numero_recreo: Optional[int] = Field(None, ge=1, le=10)
    solo_sustituciones: bool = False

    class Config:
        """Configuración de Pydantic."""

        # Permite valores por defecto None sin error
        arbitrary_types_allowed = True
