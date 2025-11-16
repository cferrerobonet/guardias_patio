"""
Ausencia Repository Interface

Define operaciones para gestionar ausencias de profesores.
"""

from abc import abstractmethod
from datetime import date

from domain.repositories.base_repository import IBaseRepository


class IAusenciaRepository(IBaseRepository):
    """
    Interfaz del repositorio de ausencias.
    """

    @abstractmethod
    def find_by_profesor_and_date(self, profesor_id: int, fecha: date):
        """
        Busca ausencia activa de un profesor en una fecha específica.

        Args:
            profesor_id: ID del profesor
            fecha: Fecha a verificar

        Returns:
            Ausencia si existe y está activa, None en caso contrario
        """
        pass

    @abstractmethod
    def find_by_profesor_and_period(
        self, profesor_id: int, fecha_inicio: date, fecha_fin: date
    ) -> list:
        """
        Busca ausencias de un profesor en un periodo.

        Args:
            profesor_id: ID del profesor
            fecha_inicio: Inicio del periodo
            fecha_fin: Fin del periodo

        Returns:
            Lista de ausencias en el periodo
        """
        pass

    @abstractmethod
    def count_by_profesor(self, profesor_id: int) -> int:
        """
        Cuenta ausencias totales de un profesor.

        Args:
            profesor_id: ID del profesor

        Returns:
            Número de ausencias
        """
        pass

    @abstractmethod
    def find_active_in_date(self, fecha: date) -> list:
        """
        Encuentra todas las ausencias activas en una fecha.

        Args:
            fecha: Fecha a verificar

        Returns:
            Lista de ausencias activas
        """
        pass
