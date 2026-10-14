"""
Zona Repository Interface

Define las operaciones específicas para acceder a zonas.
"""

from abc import abstractmethod
from typing import Optional

from domain.entities import ZonaEntity
from domain.repositories.base_repository import IBaseRepository


class IZonaRepository(IBaseRepository[ZonaEntity]):
    """
    Interfaz del repositorio de zonas.

    Define operaciones específicas para gestionar zonas.
    """

    @abstractmethod
    def find_by_nombre(self, nombre: str) -> Optional[ZonaEntity]:
        """
        Busca una zona por su nombre exacto.

        Args:
            nombre: Nombre de la zona

        Returns:
            Zona si existe, None si no
        """
        pass

    @abstractmethod
    def find_activas(self) -> list[ZonaEntity]:
        """
        Obtiene todas las zonas activas.

        Returns:
            Lista de zonas activas
        """
        pass

    @abstractmethod
    def find_con_capacidad_disponible(self) -> list[ZonaEntity]:
        """
        Obtiene zonas que tienen capacidad disponible.

        Returns:
            Lista de zonas con capacidad
        """
        pass
