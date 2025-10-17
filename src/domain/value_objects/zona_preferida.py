"""
Value Object: Zona Preferida

Representa la zona preferida de un profesor para realizar guardias.
Es inmutable y se compara por valor.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ZonaPreferida:
    """
    Zona preferida de un profesor.

    Attributes:
        zona_id: ID de la zona preferida (None si no tiene preferencia)
        zona_nombre: Nombre de la zona (opcional, para visualización)

    Examples:
        >>> zona = ZonaPreferida(zona_id=1, zona_nombre="Patio Principal")
        >>> print(zona)
        Patio Principal (ID: 1)
        >>> zona.tiene_preferencia
        True
        >>> sin_pref = ZonaPreferida(zona_id=None)
        >>> sin_pref.tiene_preferencia
        False
    """

    zona_id: Optional[int] = None
    zona_nombre: Optional[str] = None

    @property
    def tiene_preferencia(self) -> bool:
        """Verifica si tiene una zona preferida asignada."""
        return self.zona_id is not None

    def coincide_con(self, zona_id: Optional[int]) -> bool:
        """
        Verifica si coincide con una zona específica.

        Args:
            zona_id: ID de la zona a comparar

        Returns:
            True si coincide o si no tiene preferencia (acepta cualquier zona)

        Examples:
            >>> zona = ZonaPreferida(zona_id=1)
            >>> zona.coincide_con(1)
            True
            >>> zona.coincide_con(2)
            False
            >>> sin_pref = ZonaPreferida(zona_id=None)
            >>> sin_pref.coincide_con(1)  # Sin preferencia acepta cualquier zona
            True
        """
        if not self.tiene_preferencia:
            return True  # Sin preferencia = acepta cualquier zona
        return self.zona_id == zona_id

    def __str__(self) -> str:
        """Representación en string."""
        if not self.tiene_preferencia:
            return "Sin preferencia de zona"

        if self.zona_nombre:
            return f"{self.zona_nombre} (ID: {self.zona_id})"
        return f"Zona ID: {self.zona_id}"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ZonaPreferida(zona_id={self.zona_id}, zona_nombre='{self.zona_nombre}')"

    def __bool__(self) -> bool:
        """Permite usar en contextos booleanos."""
        return self.tiene_preferencia

    @classmethod
    def sin_preferencia(cls) -> 'ZonaPreferida':
        """
        Crea una instancia sin preferencia de zona.

        Returns:
            ZonaPreferida sin zona asignada

        Examples:
            >>> zona = ZonaPreferida.sin_preferencia()
            >>> zona.tiene_preferencia
            False
        """
        return cls(zona_id=None, zona_nombre=None)

    @classmethod
    def from_id(cls, zona_id: int, zona_nombre: Optional[str] = None) -> 'ZonaPreferida':
        """
        Crea una instancia con una zona específica.

        Args:
            zona_id: ID de la zona
            zona_nombre: Nombre de la zona (opcional)

        Returns:
            ZonaPreferida con zona asignada

        Examples:
            >>> zona = ZonaPreferida.from_id(1, "Patio Principal")
            >>> zona.tiene_preferencia
            True
        """
        return cls(zona_id=zona_id, zona_nombre=zona_nombre)
