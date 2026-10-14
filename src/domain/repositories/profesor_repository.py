"""
Profesor Repository Interface

Define las operaciones específicas para acceder a profesores.
"""

from abc import abstractmethod
from datetime import date
from typing import Optional

from domain.entities import ProfesorEntity
from domain.repositories.base_repository import IBaseRepository


class IProfesorRepository(IBaseRepository[ProfesorEntity]):
    """
    Interfaz del repositorio de profesores.

    Define operaciones específicas para gestionar profesores más allá del CRUD básico.
    """

    @abstractmethod
    def find_by_nombre(self, nombre: str) -> list[ProfesorEntity]:
        """
        Busca profesores por nombre (búsqueda parcial).

        Args:
            nombre: Nombre o parte del nombre a buscar

        Returns:
            Lista de profesores que coinciden
        """
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[ProfesorEntity]:
        """
        Busca un profesor por su email corporativo.

        Args:
            email: Email a buscar

        Returns:
            Profesor si existe, None si no
        """
        pass

    @abstractmethod
    def find_by_turno(self, turno: str) -> list[ProfesorEntity]:
        """
        Obtiene todos los profesores de un turno específico.

        Args:
            turno: Turno a buscar ('mañana', 'tarde', 'completo')

        Returns:
            Lista de profesores del turno
        """
        pass

    @abstractmethod
    def find_tutores(self) -> list[ProfesorEntity]:
        """
        Obtiene todos los profesores que son tutores.

        Returns:
            Lista de profesores tutores
        """
        pass

    @abstractmethod
    def find_disponibles_en_fecha(
        self, fecha: date, turno: str, recreo: int
    ) -> list[ProfesorEntity]:
        """
        Obtiene profesores disponibles en una fecha, turno y recreo específicos.

        Args:
            fecha: Fecha a verificar
            turno: Turno ('mañana' o 'tarde')
            recreo: Número de recreo

        Returns:
            Lista de profesores disponibles
        """
        pass

    @abstractmethod
    def find_con_menos_guardias(self, limite: int = 10) -> list[ProfesorEntity]:
        """
        Obtiene los profesores con menos guardias asignadas.

        Args:
            limite: Número máximo de profesores a retornar

        Returns:
            Lista de profesores ordenados por menor cantidad de guardias
        """
        pass

    @abstractmethod
    def contar_guardias_profesor(self, profesor_id: int) -> int:
        """
        Cuenta el total de guardias asignadas a un profesor.

        Args:
            profesor_id: ID del profesor

        Returns:
            Número de guardias asignadas
        """
        pass

    @abstractmethod
    def contar_guardias_profesor_en_fecha(self, profesor_id: int, fecha: date) -> int:
        """
        Cuenta las guardias de un profesor en una fecha específica.

        Args:
            profesor_id: ID del profesor
            fecha: Fecha a verificar

        Returns:
            Número de guardias en esa fecha
        """
        pass
