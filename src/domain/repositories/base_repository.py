"""
Base Repository Interface

Define las operaciones CRUD básicas que todos los repositorios deben implementar.
"""

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

# TypeVar para Entity genérica
T = TypeVar("T")


class IBaseRepository(ABC, Generic[T]):
    """
    Interfaz base para todos los repositorios.

    Define operaciones CRUD estándar que cualquier repositorio debe implementar.
    Usa generics para type safety.

    Type Parameter:
        T: Tipo de entidad que maneja el repositorio
    """

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Obtiene una entidad por su ID.

        Args:
            entity_id: ID de la entidad

        Returns:
            Entidad si existe, None si no existe
        """
        pass

    @abstractmethod
    def get_all(self) -> list[T]:
        """
        Obtiene todas las entidades.

        Returns:
            Lista de todas las entidades
        """
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Guarda una entidad (crear o actualizar).

        Args:
            entity: Entidad a guardar

        Returns:
            Entidad guardada (con ID asignado si es nuevo)
        """
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """
        Elimina una entidad por su ID.

        Args:
            entity_id: ID de la entidad a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        pass

    @abstractmethod
    def exists(self, entity_id: int) -> bool:
        """
        Verifica si existe una entidad con el ID dado.

        Args:
            entity_id: ID a verificar

        Returns:
            True si existe, False si no
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Cuenta el total de entidades.

        Returns:
            Número total de entidades
        """
        pass
