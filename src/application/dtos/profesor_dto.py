"""
DTOs para Profesor

Data Transfer Objects para operaciones con profesores.
Validan datos de entrada/salida sin exponer entidades de dominio.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class ProfesorDTO(BaseModel):
    """DTO de salida para Profesor (lectura)."""

    id: int
    nombre_completo: str
    email_corporativo: Optional[EmailStr] = None
    horas_contrato: float
    porcentaje_jornada: float
    turno: str  # "mañana", "tarde", "mixto"
    horas_manana: Optional[float] = None
    horas_tarde: Optional[float] = None
    tutor: bool  # Nombre del campo en el modelo
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    # Solo días laborables por defecto (0-4: Lun-Vie)
    dias_semana_permitidos: list[int] = Field(default_factory=lambda: list(range(5)))
    recreos_permitidos: list[int] = Field(default_factory=lambda: [1, 2, 3, 4])  # Todos

    # Campos calculados
    ajuste_guardias: Optional[float] = None
    guardias_esperadas: Optional[float] = None

    class Config:
        """Configuración de Pydantic."""
        from_attributes = True  # Permite crear desde objetos con atributos


class CrearProfesorDTO(BaseModel):
    """DTO de entrada para crear un profesor."""

    nombre_completo: str = Field(..., min_length=3, max_length=200)
    email_corporativo: Optional[EmailStr] = None
    horas_contrato: float = Field(..., ge=1.0, le=40.0)
    turno: str = Field(..., pattern="^(mañana|tarde|mixto)$")
    horas_manana: Optional[float] = Field(None, ge=0.0, le=40.0)
    horas_tarde: Optional[float] = Field(None, ge=0.0, le=40.0)
    tutor: bool = False  # Nombre del campo en el modelo
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    dias_semana_permitidos: list[int] = Field(default_factory=lambda: list(range(5)))  # 0-4: Lun-Vie
    recreos_permitidos: list[int] = Field(default_factory=lambda: [1, 2, 3, 4])  # Todos los recreos por defecto

    @field_validator("dias_semana_permitidos", mode='before')
    @classmethod
    def validar_dias_semana(cls, v) -> list[int]:
        """Valida que los días de la semana estén entre 0 y 4 (solo días laborables)."""
        # Si es None, usar valor por defecto (Lun-Vie)
        if v is None:
            return list(range(5))
        # Validar que todos los días estén en rango
        if not all(0 <= dia <= 6 for dia in v):
            raise ValueError("Los días de la semana deben estar entre 0 (lunes) y 6 (domingo)")
        return v

    @field_validator("recreos_permitidos", mode='before')
    @classmethod
    def validar_recreos(cls, v) -> list[int]:
        """Valida que los recreos sean números positivos."""
        # Si es None, usar valor por defecto
        if v is None:
            return [1, 2]
        # Validar que todos los recreos sean positivos
        if not all(recreo >= 1 for recreo in v):
            raise ValueError("Los números de recreo deben ser positivos")
        return v

    @field_validator("horas_manana", "horas_tarde")
    @classmethod
    def validar_horas_turno(cls, v: Optional[float], info) -> Optional[float]:
        """Valida que las horas de turno sean coherentes."""
        if v is not None and v < 0:
            raise ValueError("Las horas de turno no pueden ser negativas")
        return v


class ActualizarProfesorDTO(BaseModel):
    """DTO de entrada para actualizar un profesor (todos los campos opcionales)."""

    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=200)
    email_corporativo: Optional[EmailStr] = None
    horas_contrato: Optional[float] = Field(None, ge=1.0, le=40.0)
    turno: Optional[str] = Field(None, pattern="^(mañana|tarde|mixto)$")
    horas_manana: Optional[float] = Field(None, ge=0.0, le=40.0)
    horas_tarde: Optional[float] = Field(None, ge=0.0, le=40.0)
    tutor: Optional[bool] = None  # Nombre del campo en el modelo
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    dias_semana_permitidos: Optional[list[int]] = None
    recreos_permitidos: Optional[list[int]] = None

    @field_validator("dias_semana_permitidos")
    @classmethod
    def validar_dias_semana(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        """Valida que los días de la semana estén entre 0 y 6."""
        if v is not None and not all(0 <= dia <= 6 for dia in v):
            raise ValueError("Los días de la semana deben estar entre 0 (lunes) y 6 (domingo)")
        return v

    @field_validator("recreos_permitidos")
    @classmethod
    def validar_recreos(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        """Valida que los recreos sean números positivos."""
        if v is not None and not all(recreo >= 1 for recreo in v):
            raise ValueError("Los números de recreo deben ser positivos")
        return v
