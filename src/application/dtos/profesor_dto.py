"""
DTOs para Profesor

Data Transfer Objects para operaciones con profesores.
Validan datos de entrada/salida sin exponer entidades de dominio.
"""

import re
from datetime import date
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator

# Patrón RFC 5322 simplificado para validar emails
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class ProfesorDTO(BaseModel):
    """DTO de salida para Profesor (lectura)."""

    id: int
    nombre_completo: str
    email_corporativo: Optional[str] = None
    horas_contrato: float
    porcentaje_jornada: float
    turno: str  # "mañana", "tarde", "mixto"
    horas_manana: Optional[float] = None
    horas_tarde: Optional[float] = None
    tutor: bool  # Nombre del campo en el modelo
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    zona_preferida_id: Optional[int] = None  # ID de zona preferida (None = sin preferencia)
    # Solo días laborables por defecto (0-4: Lun-Vie)
    dias_semana_permitidos: list[int] = Field(default_factory=lambda: list(range(5)))
    # Acepta lista [1,2,3,4] o dict {"0": [1,2], "1": [3,4]} para restricciones por día
    recreos_permitidos: Union[list[int], dict[int, list[int]]] = Field(
        default_factory=lambda: [1, 2, 3, 4]
    )

    # Campos calculados
    ajuste_guardias: Optional[float] = None
    guardias_esperadas: Optional[float] = None

    class Config:
        """Configuración de Pydantic."""

        from_attributes = True  # Permite crear desde objetos con atributos


class CrearProfesorDTO(BaseModel):
    """DTO de entrada para crear un profesor."""

    nombre_completo: str = Field(..., min_length=3, max_length=200)
    email_corporativo: Optional[str] = None
    horas_contrato: float = Field(..., ge=1.0, le=40.0)
    turno: str = Field(..., pattern="^(mañana|tarde|mixto)$")
    horas_manana: Optional[float] = Field(None, ge=0.0, le=40.0)
    horas_tarde: Optional[float] = Field(None, ge=0.0, le=40.0)
    tutor: bool = False  # Nombre del campo en el modelo
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    zona_preferida_id: Optional[int] = Field(None, ge=1)  # ID de zona preferida
    # Solo días laborables por defecto (0-4: Lun-Vie)
    dias_semana_permitidos: list[int] = Field(default_factory=lambda: list(range(5)))
    # Acepta lista [1,2,3,4] o dict {"0": [1,2], "1": [3,4]} para restricciones por día
    recreos_permitidos: Union[list[int], dict[int, list[int]]] = Field(
        default_factory=lambda: [1, 2, 3, 4]
    )

    @field_validator("dias_semana_permitidos", mode="before")
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

    @field_validator("recreos_permitidos", mode="before")
    @classmethod
    def validar_recreos(cls, v) -> Union[list[int], dict[int, list[int]]]:
        """Valida recreos (lista simple o diccionario por día)."""
        # Si es None, usar valor por defecto
        if v is None:
            return [1, 2, 3, 4]
        # Si es diccionario vacío, devolver lista por defecto
        if isinstance(v, dict) and not v:
            return [1, 2, 3, 4]
        # Si es diccionario, validar estructura y convertir claves a int
        if isinstance(v, dict):
            try:
                # Convertir claves a int si son strings
                v = {int(k): recreos for k, recreos in v.items()}
                for dia, recreos in v.items():
                    if not isinstance(recreos, list):
                        raise ValueError(f"Los recreos del día {dia} deben ser una lista")
                    if not all(isinstance(r, int) and r >= 1 for r in recreos):
                        raise ValueError(f"Los recreos del día {dia} deben ser números positivos")
                return v
            except (ValueError, TypeError) as e:
                raise ValueError(f"Error en formato de recreos_permitidos: {e}")
        # Si es lista, validar valores
        if isinstance(v, list):
            if not all(isinstance(r, int) and r >= 1 for r in v):
                raise ValueError("Los recreos deben ser números positivos")
            return v
        raise ValueError("recreos_permitidos debe ser lista o diccionario")

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
    email_corporativo: Optional[str] = None
    horas_contrato: Optional[float] = Field(None, ge=1.0, le=40.0)
    turno: Optional[str] = Field(None, pattern="^(mañana|tarde|mixto)$")
    horas_manana: Optional[float] = Field(None, ge=0.0, le=40.0)
    horas_tarde: Optional[float] = Field(None, ge=0.0, le=40.0)
    tutor: Optional[bool] = None  # Nombre del campo en el modelo
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    zona_preferida_id: Optional[int] = Field(None, ge=1)  # ID de zona preferida
    dias_semana_permitidos: Optional[list[int]] = None
    # Acepta lista [1,2,3,4] o dict {"0": [1,2], "1": [3,4]} para restricciones por día
    recreos_permitidos: Optional[Union[list[int], dict[int, list[int]]]] = None

    @field_validator("email_corporativo")
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el email tenga formato válido."""
        if v is not None and not EMAIL_PATTERN.match(v):
            raise ValueError(f"El email '{v}' no tiene un formato válido")
        return v

    @field_validator("dias_semana_permitidos")
    @classmethod
    def validar_dias_semana(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        """Valida que los días de la semana estén entre 0 y 6."""
        if v is not None and not all(0 <= dia <= 6 for dia in v):
            raise ValueError("Los días de la semana deben estar entre 0 (lunes) y 6 (domingo)")
        return v

    @field_validator("recreos_permitidos")
    @classmethod
    def validar_recreos(
        cls, v: Optional[Union[list[int], dict[int, list[int]]]]
    ) -> Optional[Union[list[int], dict[int, list[int]]]]:
        """Valida recreos (lista simple o diccionario por día)."""
        if v is None:
            return None
        # Si es diccionario vacío, devolver None
        if isinstance(v, dict) and not v:
            return None
        # Si es diccionario, validar estructura y convertir claves a int
        if isinstance(v, dict):
            try:
                # Convertir claves a int si son strings
                v = {int(k): recreos for k, recreos in v.items()}
                for dia, recreos in v.items():
                    if not isinstance(recreos, list):
                        raise ValueError(f"Los recreos del día {dia} deben ser una lista")
                    if not all(isinstance(r, int) and r >= 1 for r in recreos):
                        raise ValueError(f"Los recreos del día {dia} deben ser números positivos")
                return v
            except (ValueError, TypeError) as e:
                raise ValueError(f"Error en formato de recreos_permitidos: {e}")
        # Si es lista, validar valores
        if isinstance(v, list):
            if not all(isinstance(r, int) and r >= 1 for r in v):
                raise ValueError("Los recreos deben ser números positivos")
            return v
        raise ValueError("recreos_permitidos debe ser lista o diccionario")
