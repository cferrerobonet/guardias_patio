"""
Domain Entity: Zona

Representa una zona de recreo en el dominio de negocio.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ZonaEntity:
    """
    Entidad de dominio que representa una zona de recreo.

    Attributes:
        id: Identificador único de la zona
        nombre_zona: Nombre descriptivo de la zona
        descripcion: Descripción detallada (opcional)
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

    # Vigencia temporal
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

    # Estado
    activa: bool = True

    @property
    def nombre_display(self) -> str:
        """Nombre para mostrar en la interfaz."""
        return self.nombre_zona

    def puede_asignar_profesor(self) -> bool:
        """Una zona desactivada no recibe guardias."""
        return self.activa

    def __str__(self) -> str:
        """Representación en string."""
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
