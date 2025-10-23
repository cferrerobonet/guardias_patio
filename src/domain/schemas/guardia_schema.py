"""
Pydantic Schemas para Guardia.

Define los DTOs para validación de datos de guardias asignadas.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class GuardiaSchema(BaseModel):
    """
    Schema completo de Guardia para lectura (con ID).

    Se usa para:
    - Respuestas de API
    - Exportación de datos
    - Visualización en calendario

    Examples:
        >>> guardia = GuardiaSchema(
        ...     id=1,
        ...     profesor_id=5,
        ...     zona_id=2,
        ...     fecha=date(2025, 10, 23),
        ...     turno="mañana",
        ...     recreo=1
        ... )
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )

    # Identidad
    id: int = Field(..., gt=0, description="ID único de la guardia")

    # Asignación
    profesor_id: int = Field(
        ...,
        gt=0,
        description="ID del profesor asignado"
    )
    zona_id: int = Field(
        ...,
        gt=0,
        description="ID de la zona asignada"
    )

    # Temporalidad
    fecha: date = Field(
        ...,
        description="Fecha de la guardia"
    )
    turno: str = Field(
        ...,
        pattern="^(mañana|tarde)$",
        description="Turno de la guardia"
    )
    recreo: int = Field(
        ...,
        gt=0,
        le=3,
        description="Número del recreo (1, 2, 3)"
    )

    # Sustitución
    es_sustitucion: bool = Field(
        False,
        description="Indica si es una guardia de sustitución"
    )
    profesor_sustituido_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID del profesor sustituido (si aplica)"
    )

    # Metadatos
    notas: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas adicionales sobre la guardia"
    )

    @field_validator("profesor_sustituido_id")
    @classmethod
    def validar_sustitucion(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Valida coherencia de datos de sustitución."""
        es_sustitucion = info.data.get("es_sustitucion", False)

        # Si es sustitución, debe tener profesor_sustituido_id
        if es_sustitucion and v is None:
            raise ValueError(
                "Si es_sustitucion=True, debe proporcionar profesor_sustituido_id"
            )

        # Si no es sustitución, no debe tener profesor_sustituido_id
        if not es_sustitucion and v is not None:
            raise ValueError(
                "Si es_sustitucion=False, no puede tener profesor_sustituido_id"
            )

        return v


class GuardiaCreateSchema(BaseModel):
    """
    Schema para creación de Guardia (sin ID).

    Se usa para:
    - Asignación de nuevas guardias
    - Importación de horarios
    - Formularios de asignación manual

    Examples:
        >>> nueva_guardia = GuardiaCreateSchema(
        ...     profesor_id=5,
        ...     zona_id=2,
        ...     fecha=date(2025, 10, 23),
        ...     turno="mañana",
        ...     recreo=1
        ... )
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    # Campos requeridos
    profesor_id: int = Field(..., gt=0, description="ID del profesor asignado")
    zona_id: int = Field(..., gt=0, description="ID de la zona asignada")
    fecha: date = Field(..., description="Fecha de la guardia")
    turno: str = Field(
        ...,
        pattern="^(mañana|tarde)$",
        description="Turno de la guardia"
    )
    recreo: int = Field(..., gt=0, le=3, description="Número del recreo")

    # Campos opcionales
    es_sustitucion: bool = False
    profesor_sustituido_id: Optional[int] = Field(None, gt=0)
    notas: Optional[str] = Field(None, max_length=500)

    @field_validator("profesor_sustituido_id")
    @classmethod
    def validar_sustitucion(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Valida coherencia de datos de sustitución."""
        es_sustitucion = info.data.get("es_sustitucion", False)

        if es_sustitucion and v is None:
            raise ValueError(
                "Si es_sustitucion=True, debe proporcionar profesor_sustituido_id"
            )

        if not es_sustitucion and v is not None:
            raise ValueError(
                "Si es_sustitucion=False, no puede tener profesor_sustituido_id"
            )

        return v

    @field_validator("profesor_sustituido_id")
    @classmethod
    def validar_no_auto_sustitucion(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Valida que el profesor no se sustituya a sí mismo."""
        if v is not None:
            profesor_id = info.data.get("profesor_id")
            if v == profesor_id:
                raise ValueError(
                    "Un profesor no puede sustituirse a sí mismo"
                )
        return v


class GuardiaUpdateSchema(BaseModel):
    """
    Schema para actualización parcial de Guardia.

    Todos los campos son opcionales.

    Se usa para:
    - Modificaciones de guardias existentes
    - Cambios de zona o profesor
    - Conversión a/desde sustitución

    Examples:
        >>> actualizacion = GuardiaUpdateSchema(
        ...     zona_id=3,
        ...     notas="Cambio por ausencia"
        ... )
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    # Todos los campos opcionales
    profesor_id: Optional[int] = Field(None, gt=0)
    zona_id: Optional[int] = Field(None, gt=0)
    fecha: Optional[date] = None
    turno: Optional[str] = Field(None, pattern="^(mañana|tarde)$")
    recreo: Optional[int] = Field(None, gt=0, le=3)
    es_sustitucion: Optional[bool] = None
    profesor_sustituido_id: Optional[int] = Field(None, gt=0)
    notas: Optional[str] = Field(None, max_length=500)

    @field_validator("profesor_sustituido_id")
    @classmethod
    def validar_sustitucion(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Valida coherencia de datos de sustitución."""
        # Solo validar si se proporciona es_sustitucion
        if "es_sustitucion" in info.data:
            es_sustitucion = info.data["es_sustitucion"]

            if es_sustitucion and v is None:
                raise ValueError(
                    "Si es_sustitucion=True, debe proporcionar profesor_sustituido_id"
                )

            if not es_sustitucion and v is not None:
                raise ValueError(
                    "Si es_sustitucion=False, no puede tener profesor_sustituido_id"
                )

        return v
