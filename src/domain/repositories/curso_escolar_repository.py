"""
CursoEscolar Repository Interface

Define operaciones para gestionar cursos escolares.
"""

from abc import abstractmethod
from typing import Optional

from domain.repositories.base_repository import IBaseRepository


class ICursoEscolarRepository(IBaseRepository):
    """
    Interfaz del repositorio de cursos escolares.
    """

    @abstractmethod
    def find_active(self):
        """
        Obtiene el curso escolar activo.

        Returns:
            Curso activo o None
        """
        pass

    @abstractmethod
    def find_by_year(self, anio_inicio: int) -> Optional[object]:
        """
        Busca curso por año de inicio.

        Args:
            anio_inicio: Año de inicio del curso

        Returns:
            Curso escolar o None
        """
        pass

    @abstractmethod
    def deactivate_all(self) -> None:
        """
        Desactiva todos los cursos escolares.
        """
        pass

    @abstractmethod
    def find_by_date_range(self, fecha_inicio: str, fecha_fin: str) -> list:
        """
        Busca cursos que se solapen con un rango de fechas.

        Args:
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)

        Returns:
            Lista de cursos que se solapan
        """
        pass
