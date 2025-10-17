"""
Value Object: Turno

Representa el turno de un profesor (mañana, tarde, completo).
Es inmutable y se compara por valor.
"""

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Optional

from config import settings
from core.exceptions import ValidationError


class TurnoEnum(str, Enum):
    """Enumeración de turnos válidos."""
    MANANA = "mañana"
    TARDE = "tarde"
    MIXTO = "mixto"  # Turno mixto (mañana y tarde)

    @classmethod
    def from_string(cls, value: str) -> 'TurnoEnum':
        """Convierte un string a TurnoEnum."""
        value_lower = value.lower().strip()
        for turno in cls:
            if turno.value == value_lower:
                return turno
        raise ValidationError(
            message=f"Turno inválido: '{value}'. Valores válidos: {[t.value for t in cls]}"
        )


@dataclass(frozen=True)
class Turno:
    """
    Turno de trabajo de un profesor.

    Attributes:
        value: El turno (mañana, tarde, completo)
        horas_manana: Horas asignadas al turno de mañana (opcional, para turno completo)
        horas_tarde: Horas asignadas al turno de tarde (opcional, para turno completo)

    Raises:
        ValidationError: Si el turno no es válido o las horas no son consistentes

    Examples:
        >>> turno = Turno(TurnoEnum.MANANA)
        >>> print(turno.value)
        mañana
        >>> turno.es_manana
        True
        >>> turno_mixto = Turno(TurnoEnum.COMPLETO, horas_manana=15.0, horas_tarde=10.0)
        >>> turno_mixto.es_completo
        True
    """

    value: TurnoEnum
    horas_manana: Optional[float] = None
    horas_tarde: Optional[float] = None

    # Turnos válidos desde configuración
    TURNOS_VALIDOS: ClassVar[list[str]] = settings.turnos_validos

    def __post_init__(self) -> None:
        """Valida el turno después de la inicialización."""
        # Validar que el turno esté en los válidos
        if self.value.value not in self.TURNOS_VALIDOS:
            raise ValidationError(
                message=(
                    f"Turno '{self.value.value}' no está en turnos válidos: "
                    f"{self.TURNOS_VALIDOS}"
                )
            )

        # Si es turno mixto, validar que tenga horas asignadas
        if self.value == TurnoEnum.MIXTO:
            if self.horas_manana is None and self.horas_tarde is None:
                raise ValidationError(
                    message="Turno mixto requiere especificar horas_manana y/o horas_tarde"
                )

            # Validar que las horas sean positivas
            if self.horas_manana is not None and self.horas_manana < 0:
                raise ValidationError(
                    message=f"horas_manana no puede ser negativa: {self.horas_manana}"
                )

            if self.horas_tarde is not None and self.horas_tarde < 0:
                raise ValidationError(
                    message=f"horas_tarde no puede ser negativa: {self.horas_tarde}"
                )

        # Si no es turno mixto, no debería tener horas específicas
        elif self.horas_manana is not None or self.horas_tarde is not None:
            raise ValidationError(
                message=(
                    f"Turno '{self.value.value}' no debe tener horas_manana/horas_tarde "
                    "especificadas"
                )
            )

    @property
    def es_manana(self) -> bool:
        """Verifica si es turno de mañana."""
        return self.value == TurnoEnum.MANANA

    @property
    def es_tarde(self) -> bool:
        """Verifica si es turno de tarde."""
        return self.value == TurnoEnum.TARDE

    @property
    def es_mixto(self) -> bool:
        """Verifica si es turno mixto (mañana y tarde)."""
        return self.value == TurnoEnum.MIXTO

    @property
    def es_completo(self) -> bool:
        """Alias para es_mixto (compatibilidad)."""
        return self.es_mixto

    @property
    def trabaja_manana(self) -> bool:
        """Verifica si trabaja en turno de mañana."""
        return self.es_manana or (self.es_mixto and (self.horas_manana or 0) > 0)

    @property
    def trabaja_tarde(self) -> bool:
        """Verifica si trabaja en turno de tarde."""
        return self.es_tarde or (self.es_mixto and (self.horas_tarde or 0) > 0)

    def puede_hacer_guardia_en_turno(self, turno_recreo: str) -> bool:
        """
        Verifica si el profesor puede hacer una guardia en un turno específico.

        Args:
            turno_recreo: El turno del recreo ('mañana' o 'tarde')

        Returns:
            True si puede hacer guardia en ese turno

        Examples:
            >>> turno = Turno(TurnoEnum.MANANA)
            >>> turno.puede_hacer_guardia_en_turno("mañana")
            True
            >>> turno.puede_hacer_guardia_en_turno("tarde")
            False
        """
        if turno_recreo.lower() == "mañana":
            return self.trabaja_manana
        elif turno_recreo.lower() == "tarde":
            return self.trabaja_tarde
        return False

    def __str__(self) -> str:
        """Representación en string."""
        if self.es_mixto and (self.horas_manana or self.horas_tarde):
            return f"{self.value.value} (M:{self.horas_manana or 0}h, T:{self.horas_tarde or 0}h)"
        return self.value.value

    def __repr__(self) -> str:
        """Representación para debugging."""
        if self.horas_manana or self.horas_tarde:
            return (
                f"Turno({self.value}, horas_manana={self.horas_manana}, "
                f"horas_tarde={self.horas_tarde})"
            )
        return f"Turno({self.value})"

    @classmethod
    def from_string(
        cls,
        value: str,
        horas_manana: Optional[float] = None,
        horas_tarde: Optional[float] = None
    ) -> 'Turno':
        """
        Crea un Turno desde un string.

        Args:
            value: String del turno ('mañana', 'tarde', 'completo')
            horas_manana: Horas de mañana (opcional)
            horas_tarde: Horas de tarde (opcional)

        Returns:
            Instancia de Turno

        Raises:
            ValidationError: Si el valor no es válido
        """
        turno_enum = TurnoEnum.from_string(value)
        return cls(turno_enum, horas_manana, horas_tarde)
