"""
Pydantic Schemas para Profesor.

Define los DTOs (Data Transfer Objects) para validación de datos
relacionados con profesores.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class ProfesorSchema(BaseModel):
    """
    Schema completo de Profesor para lectura (con ID).

    Se usa para:
    - Respuestas de API
    - Exportación de datos
    - Serialización para frontend

    Examples:
        >>> profesor = ProfesorSchema(
        ...     id=1,
        ...     nombre_completo="GARCÍA PÉREZ, Juan",
        ...     email_corporativo="juan.garcia@example.com",
        ...     horas_contrato=25.0,
        ...     porcentaje_jornada=100.0,
        ...     turno="mañana",
        ...     es_tutor=True
        ... )
        >>> profesor.model_dump()
        {'id': 1, 'nombre_completo': 'GARCÍA PÉREZ, Juan', ...}
    """

    model_config = ConfigDict(
        from_attributes=True,  # Permite crear desde ORM models
        str_strip_whitespace=True,  # Limpia espacios
        validate_assignment=True,  # Valida al asignar valores
    )

    # Identidad
    id: int = Field(..., gt=0, description="ID único del profesor")

    # Información básica
    nombre_completo: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Nombre completo del profesor (formato: APELLIDOS, NOMBRE)"
    )
    email_corporativo: Optional[EmailStr] = Field(
        None,
        description="Email corporativo del profesor"
    )

    # Contrato y jornada
    horas_contrato: float = Field(
        ...,
        ge=0.0,
        le=40.0,
        description="Horas de contrato semanales"
    )
    porcentaje_jornada: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Porcentaje de jornada (calculado)"
    )
    turno: str = Field(
        ...,
        pattern="^(mañana|tarde)$",
        description="Turno de trabajo"
    )

    # Características
    es_tutor: bool = Field(
        False,
        description="Indica si es tutor de un grupo"
    )

    # Disponibilidad temporal
    fecha_inicio_guardias: Optional[date] = Field(
        None,
        description="Fecha desde la que puede hacer guardias"
    )
    fecha_fin_guardias: Optional[date] = Field(
        None,
        description="Fecha hasta la que puede hacer guardias"
    )

    # Preferencias (listas simplificadas)
    zona_preferida_id: Optional[int] = Field(
        None,
        ge=0,
        description="ID de la zona preferida (0 = sin preferencia)"
    )
    dias_semana_permitidos: list[int] = Field(
        default_factory=lambda: list(range(5)),  # Solo días laborables (0-4: Lun-Vie)
        description="Lista de días permitidos (0=Lunes, 4=Viernes)"
    )
    recreos_permitidos: list[int] = Field(
        default_factory=lambda: [1, 2],
        description="Lista de recreos permitidos (1, 2, etc.)"
    )

    @field_validator("dias_semana_permitidos", mode='before')
    @classmethod
    def validar_dias_semana(cls, v) -> list[int]:
        """Valida que los días estén en rango 0-6."""
        # Si es None, usar valor por defecto (solo días laborables)
        if v is None:
            return list(range(5))
        # Validar que todos los días estén en rango
        if not all(0 <= dia <= 6 for dia in v):
            raise ValueError("Los días de la semana deben estar entre 0 (Lunes) y 6 (Domingo)")
        return v

    @field_validator("recreos_permitidos", mode='before')
    @classmethod
    def validar_recreos(cls, v) -> list[int]:
        """Valida que los recreos sean positivos."""
        # Si es None, usar valor por defecto
        if v is None:
            return [1, 2]
        # Validar que todos los recreos sean positivos
        if not all(recreo > 0 for recreo in v):
            raise ValueError("Los números de recreo deben ser positivos")
        return v

    @field_validator("fecha_fin_guardias")
    @classmethod
    def validar_fechas(cls, v: Optional[date], info: ValidationInfo) -> Optional[date]:
        """Valida que fecha_fin >= fecha_inicio."""
        if v is not None and "fecha_inicio_guardias" in info.data:
            fecha_inicio = info.data["fecha_inicio_guardias"]
            if fecha_inicio is not None and v < fecha_inicio:
                raise ValueError(
                    f"fecha_fin_guardias ({v}) no puede ser anterior a "
                    f"fecha_inicio_guardias ({fecha_inicio})"
                )
        return v


class ProfesorCreateSchema(BaseModel):
    """
    Schema para creación de Profesor (sin ID).

    Se usa para:
    - Creación de nuevos profesores
    - Importación desde Excel/CSV
    - Formularios de alta

    Examples:
        >>> nuevo_profesor = ProfesorCreateSchema(
        ...     nombre_completo="MARTÍNEZ LÓPEZ, Ana",
        ...     email_corporativo="ana.martinez@example.com",
        ...     horas_contrato=20.0,
        ...     turno="mañana"
        ... )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Campos requeridos
    nombre_completo: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Nombre completo del profesor"
    )
    horas_contrato: float = Field(
        ...,
        ge=0.0,
        le=40.0,
        description="Horas de contrato semanales"
    )
    turno: str = Field(
        default="mañana",
        pattern="^(mañana|tarde)$",
        description="Turno de trabajo"
    )

    # Campos opcionales
    email_corporativo: Optional[EmailStr] = None
    porcentaje_jornada: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Se calcula automáticamente si no se proporciona"
    )
    es_tutor: bool = False
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    zona_preferida_id: Optional[int] = Field(None, ge=0)
    # Solo días laborables por defecto (0-4: Lun-Vie)
    dias_semana_permitidos: list[int] = Field(default_factory=lambda: list(range(5)))
    recreos_permitidos: list[int] = Field(default_factory=lambda: [1, 2])

    @field_validator("dias_semana_permitidos", mode='before')
    @classmethod
    def validar_dias_semana(cls, v) -> list[int]:
        """Valida que los días estén en rango 0-6."""
        # Si es None, usar valor por defecto (solo días laborables)
        if v is None:
            return list(range(5))
        # Validar que todos los días estén en rango
        if not all(0 <= dia <= 6 for dia in v):
            raise ValueError("Los días de la semana deben estar entre 0 (Lunes) y 6 (Domingo)")
        return v

    @field_validator("recreos_permitidos", mode='before')
    @classmethod
    def validar_recreos(cls, v) -> list[int]:
        """Valida que los recreos sean positivos."""
        # Si es None, usar valor por defecto
        if v is None:
            return [1, 2]
        # Validar que todos los recreos sean positivos
        if not all(recreo > 0 for recreo in v):
            raise ValueError("Los números de recreo deben ser positivos")
        return v


class ProfesorUpdateSchema(BaseModel):
    """
    Schema para actualización parcial de Profesor.

    Todos los campos son opcionales. Solo se actualizan los campos
    proporcionados.

    Se usa para:
    - Actualizaciones parciales (PATCH)
    - Modificaciones de configuración
    - Formularios de edición

    Examples:
        >>> actualizacion = ProfesorUpdateSchema(
        ...     horas_contrato=30.0,
        ...     es_tutor=True
        ... )
        >>> # Solo actualiza esos 2 campos
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Todos los campos opcionales
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=200)
    email_corporativo: Optional[EmailStr] = None
    horas_contrato: Optional[float] = Field(None, ge=0.0, le=40.0)
    porcentaje_jornada: Optional[float] = Field(None, ge=0.0, le=100.0)
    turno: Optional[str] = Field(None, pattern="^(mañana|tarde)$")
    es_tutor: Optional[bool] = None
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None
    zona_preferida_id: Optional[int] = Field(None, ge=0)
    dias_semana_permitidos: Optional[list[int]] = None
    recreos_permitidos: Optional[list[int]] = None

    @field_validator("dias_semana_permitidos")
    @classmethod
    def validar_dias_semana(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        """Valida que los días estén en rango 0-6."""
        if v is not None and not all(0 <= dia <= 6 for dia in v):
            raise ValueError("Los días de la semana deben estar entre 0 (Lunes) y 6 (Domingo)")
        return v

    @field_validator("recreos_permitidos")
    @classmethod
    def validar_recreos(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        """Valida que los recreos sean positivos."""
        if v is not None and not all(recreo > 0 for recreo in v):
            raise ValueError("Los números de recreo deben ser positivos")
        return v
