"""
Pydantic Schema para Configuración.

Define el DTO para validación de la configuración del sistema.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class ConfiguracionSchema(BaseModel):
    """
    Schema para Configuración del sistema.

    Valida todos los parámetros de configuración con sus restricciones.

    Se usa para:
    - Validación de configuración en startup
    - Importación/exportación de configuración
    - Formulario de configuración en UI

    Examples:
        >>> config = ConfiguracionSchema(
        ...     max_horas_contrato=25.0,
        ...     ajuste_tutores=10.0,
        ...     ajuste_no_tutores=12.0,
        ...     max_guardias_por_profesor_dia=2
        ... )
        >>> config.model_dump()
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Identidad (para persistencia)
    id: Optional[int] = Field(
        None,
        gt=0,
        description="ID de la configuración (para BD)"
    )

    # Parámetros de horas y jornada
    max_horas_contrato: float = Field(
        25.0,
        gt=0.0,
        le=40.0,
        description="Horas máximas de contrato por semana"
    )

    # Ajustes de guardias
    ajuste_tutores: float = Field(
        10.0,
        gt=0.0,
        le=20.0,
        description="Número de guardias esperadas para tutores"
    )
    ajuste_no_tutores: float = Field(
        12.0,
        gt=0.0,
        le=20.0,
        description="Número de guardias esperadas para no tutores"
    )

    # Límites por día
    max_guardias_por_profesor_dia: int = Field(
        2,
        gt=0,
        le=5,
        description="Máximo de guardias que puede tener un profesor en un día"
    )

    # Configuración de turnos y recreos
    num_recreos_manana: int = Field(
        2,
        ge=1,
        le=3,
        description="Número de recreos en turno de mañana"
    )
    num_recreos_tarde: int = Field(
        1,
        ge=0,
        le=3,
        description="Número de recreos en turno de tarde"
    )

    # Días laborables
    dias_laborables: list[int] = Field(
        default_factory=lambda: [0, 1, 2, 3, 4],  # Lunes a Viernes
        description="Lista de días laborables (0=Lunes, 6=Domingo)"
    )

    # Configuración de notificaciones
    notificar_ausencias: bool = Field(
        True,
        description="Enviar notificaciones de ausencias"
    )
    notificar_sustituciones: bool = Field(
        True,
        description="Enviar notificaciones de sustituciones"
    )
    email_notificaciones: Optional[str] = Field(
        None,
        max_length=200,
        description="Email para notificaciones del sistema"
    )

    # Configuración de exportación
    incluir_email_en_exports: bool = Field(
        False,
        description="Incluir emails en exportaciones PDF/Excel"
    )
    mostrar_zona_en_calendario: bool = Field(
        True,
        description="Mostrar nombre de zona en vista de calendario"
    )

    # Metadatos
    nombre_centro: str = Field(
        "Centro Educativo",
        min_length=1,
        max_length=200,
        description="Nombre del centro educativo"
    )
    curso_escolar: str = Field(
        "2025/2026",
        pattern=r"^\d{4}/\d{4}$",
        description="Curso escolar (formato: YYYY/YYYY)"
    )

    @field_validator("dias_laborables")
    @classmethod
    def validar_dias_laborables(cls, v: list[int]) -> list[int]:
        """Valida que los días laborables estén en rango 0-6."""
        if not all(0 <= dia <= 6 for dia in v):
            raise ValueError(
                "Los días laborables deben estar entre 0 (Lunes) y 6 (Domingo)"
            )
        if len(v) == 0:
            raise ValueError("Debe haber al menos un día laborable")
        # Eliminar duplicados y ordenar
        return sorted(set(v))

    @field_validator("ajuste_no_tutores")
    @classmethod
    def validar_ajuste_no_tutores(cls, v: float, info: ValidationInfo) -> float:
        """Valida que ajuste_no_tutores >= ajuste_tutores."""
        if "ajuste_tutores" in info.data:
            ajuste_tutores = info.data["ajuste_tutores"]
            if v < ajuste_tutores:
                raise ValueError(
                    f"ajuste_no_tutores ({v}) debe ser >= ajuste_tutores ({ajuste_tutores}). "
                    "Los no tutores suelen tener más guardias que los tutores."
                )
        return v

    @field_validator("curso_escolar")
    @classmethod
    def validar_curso_escolar(cls, v: str) -> str:
        """Valida formato y coherencia del curso escolar."""
        partes = v.split("/")
        if len(partes) != 2:
            raise ValueError("El curso escolar debe tener formato YYYY/YYYY")

        try:
            anio1 = int(partes[0])
            anio2 = int(partes[1])
        except ValueError:
            raise ValueError("Los años del curso escolar deben ser números")

        if anio2 != anio1 + 1:
            raise ValueError(
                f"El segundo año ({anio2}) debe ser exactamente un año después "
                f"del primero ({anio1})"
            )

        if anio1 < 2020 or anio1 > 2100:
            raise ValueError("El año debe estar entre 2020 y 2100")

        return v

    @field_validator("email_notificaciones")
    @classmethod
    def validar_email_notificaciones(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Valida email si las notificaciones están activas."""
        if v is not None:
            # Validación básica de email
            if "@" not in v or "." not in v.split("@")[1]:
                raise ValueError("Email de notificaciones no válido")

        # Advertir si notificaciones activas pero sin email
        notificar = (
            info.data.get("notificar_ausencias", False) or
            info.data.get("notificar_sustituciones", False)
        )
        if notificar and v is None:
            # No es error, solo advertencia (el logger lo registrará)
            pass

        return v

    def calcular_guardias_esperadas_profesor(
        self,
        horas_contrato: float,
        es_tutor: bool
    ) -> float:
        """
        Calcula guardias esperadas para un profesor según configuración.

        Args:
            horas_contrato: Horas de contrato del profesor
            es_tutor: Si el profesor es tutor

        Returns:
            Número de guardias esperadas (puede ser decimal)

        Examples:
            >>> config = ConfiguracionSchema()
            >>> config.calcular_guardias_esperadas_profesor(25.0, True)
            10.0
            >>> config.calcular_guardias_esperadas_profesor(20.0, False)
            9.6
        """
        ajuste = self.ajuste_tutores if es_tutor else self.ajuste_no_tutores
        ratio = horas_contrato / self.max_horas_contrato
        return ratio * ajuste

    def es_dia_laborable(self, dia_semana: int) -> bool:
        """
        Verifica si un día de la semana es laborable.

        Args:
            dia_semana: Día de la semana (0=Lunes, 6=Domingo)

        Returns:
            True si es día laborable

        Examples:
            >>> config = ConfiguracionSchema()
            >>> config.es_dia_laborable(0)  # Lunes
            True
            >>> config.es_dia_laborable(6)  # Domingo
            False
        """
        return dia_semana in self.dias_laborables

    def num_recreos_total(self) -> int:
        """
        Calcula el número total de recreos configurados.

        Returns:
            Total de recreos (mañana + tarde)
        """
        return self.num_recreos_manana + self.num_recreos_tarde
