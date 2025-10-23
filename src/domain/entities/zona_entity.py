"""
Domain Entity: Zona

Representa una zona de recreo en el dominio de negocio.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ZonaEntity:
    """
    Entidad de dominio que representa una zona de recreo.

    Attributes:
        id: Identificador único de la zona
        nombre_zona: Nombre descriptivo de la zona
        descripcion: Descripción detallada (opcional)
        capacidad_profesores: Número de profesores asignables (opcional)
        activa: Si la zona está activa para asignación

    Examples:
        >>> zona = ZonaEntity(id=1, nombre_zona="Patio Principal")
        >>> print(zona.nombre_display)
        Patio Principal
        >>> zona.puede_asignar_profesor()
        True
    """

    # Identidad
    id: Optional[int] = None

    # Información básica
    nombre_zona: str = ""
    descripcion: Optional[str] = None

    # Capacidad
    capacidad_profesores: Optional[int] = None

    # Estado
    activa: bool = True

    @property
    def nombre_display(self) -> str:
        """Nombre para mostrar en la interfaz."""
        return self.nombre_zona

    @property
    def tiene_capacidad_limitada(self) -> bool:
        """Verifica si la zona tiene un límite de profesores."""
        return self.capacidad_profesores is not None

    def puede_asignar_profesor(self, profesores_actuales: int = 0) -> bool:
        """
        Verifica si se puede asignar un profesor adicional a la zona.

        Args:
            profesores_actuales: Número actual de profesores en la zona

        Returns:
            True si se puede asignar un profesor más

        Examples:
            >>> zona = ZonaEntity(id=1, nombre_zona="Patio", capacidad_profesores=3)
            >>> zona.puede_asignar_profesor(profesores_actuales=2)
            True
            >>> zona.puede_asignar_profesor(profesores_actuales=3)
            False
        """
        if not self.activa:
            return False

        if not self.tiene_capacidad_limitada:
            return True

        # Verificar que capacidad_profesores no sea None antes de comparar
        if self.capacidad_profesores is None:
            return True

        return profesores_actuales < self.capacidad_profesores

    def __str__(self) -> str:
        """Representación en string."""
        if self.tiene_capacidad_limitada:
            return f"{self.nombre_zona} (cap: {self.capacidad_profesores})"
        return self.nombre_zona

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ZonaEntity(id={self.id}, nombre='{self.nombre_zona}')"

    def __eq__(self, other: object) -> bool:
        """Comparación por identidad (ID)."""
        if not isinstance(other, ZonaEntity):
            return False
        if self.id is not None and other.id is not None:
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Hash basado en ID."""
        if self.id is not None:
            return hash(("ZonaEntity", self.id))
        return hash(("ZonaEntity", id(self)))
