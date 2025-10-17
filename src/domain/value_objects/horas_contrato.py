"""
Value Object: Horas de Contrato

Representa las horas de contrato de un profesor con validación automática.
Es inmutable y se compara por valor.
"""

from dataclasses import dataclass
from typing import ClassVar

from config import settings
from core.exceptions import InvalidHorasContratoError


@dataclass(frozen=True)
class HorasContrato:
    """
    Horas de contrato validadas de un profesor.

    Attributes:
        value: Cantidad de horas (debe estar entre min y max configurado)

    Raises:
        InvalidHorasContratoError: Si las horas no están en el rango válido

    Examples:
        >>> horas = HorasContrato(25.0)
        >>> print(horas.value)
        25.0
        >>> horas.porcentaje_jornada(40.0)
        62.5
    """

    value: float

    # Límites desde configuración
    MIN_HORAS: ClassVar[float] = settings.min_horas_contrato
    MAX_HORAS: ClassVar[float] = settings.max_horas_contrato

    def __post_init__(self) -> None:
        """Valida las horas después de la inicialización."""
        if not isinstance(self.value, (int, float)):
            raise InvalidHorasContratoError(
                horas=self.value,
                message=f"Las horas deben ser un número, recibido: {type(self.value).__name__}"
            )

        if self.value < self.MIN_HORAS:
            raise InvalidHorasContratoError(
                horas=self.value,
                message=(
                    f"Las horas de contrato ({self.value}) no pueden ser menores a "
                    f"{self.MIN_HORAS}"
                )
            )

        if self.value > self.MAX_HORAS:
            raise InvalidHorasContratoError(
                horas=self.value,
                message=f"Las horas de contrato ({self.value}) no pueden exceder {self.MAX_HORAS}"
            )

    def porcentaje_jornada(self, jornada_completa: float = 40.0) -> float:
        """
        Calcula el porcentaje de jornada respecto a una jornada completa.

        Args:
            jornada_completa: Horas de una jornada completa (default: 40.0)

        Returns:
            Porcentaje de jornada (0-100)

        Examples:
            >>> horas = HorasContrato(25.0)
            >>> horas.porcentaje_jornada()
            62.5
        """
        return (self.value / jornada_completa) * 100

    def es_jornada_completa(self, threshold: float = 0.95) -> bool:
        """
        Verifica si representa una jornada completa.

        Args:
            threshold: Porcentaje mínimo para considerar jornada completa (default: 0.95 = 95%)

        Returns:
            True si es >= threshold * jornada completa

        Examples:
            >>> HorasContrato(38.0).es_jornada_completa()
            True
            >>> HorasContrato(20.0).es_jornada_completa()
            False
        """
        return self.porcentaje_jornada() >= (threshold * 100)

    def __str__(self) -> str:
        """Representación en string."""
        return f"{self.value:.1f}h"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"HorasContrato({self.value})"

    def __float__(self) -> float:
        """Permite conversión a float."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Comparación por valor."""
        if isinstance(other, HorasContrato):
            return self.value == other.value
        if isinstance(other, (int, float)):
            return self.value == other
        return False

    def __lt__(self, other: 'HorasContrato') -> bool:
        """Permite comparaciones de menor que."""
        if isinstance(other, HorasContrato):
            return self.value < other.value
        if isinstance(other, (int, float)):
            return self.value < other
        return NotImplemented

    def __le__(self, other: 'HorasContrato') -> bool:
        """Permite comparaciones de menor o igual."""
        if isinstance(other, HorasContrato):
            return self.value <= other.value
        if isinstance(other, (int, float)):
            return self.value <= other
        return NotImplemented
