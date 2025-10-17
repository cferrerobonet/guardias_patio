"""
Guardia Repository Interface

Define las operaciones específicas para acceder a guardias.
"""

from abc import abstractmethod
from datetime import date

from domain.entities import GuardiaEntity
from domain.repositories.base_repository import IBaseRepository


class IGuardiaRepository(IBaseRepository[GuardiaEntity]):
    """
    Interfaz del repositorio de guardias.

    Define operaciones específicas para gestionar guardias asignadas.
    """

    @abstractmethod
    def find_by_fecha(self, fecha: date) -> list[GuardiaEntity]:
        """
        Obtiene todas las guardias de una fecha específica.

        Args:
            fecha: Fecha a buscar

        Returns:
            Lista de guardias en esa fecha
        """
        pass

    @abstractmethod
    def find_by_profesor(self, profesor_id: int) -> list[GuardiaEntity]:
        """
        Obtiene todas las guardias de un profesor.

        Args:
            profesor_id: ID del profesor

        Returns:
            Lista de guardias del profesor
        """
        pass

    @abstractmethod
    def find_by_zona(self, zona_id: int) -> list[GuardiaEntity]:
        """
        Obtiene todas las guardias de una zona.

        Args:
            zona_id: ID de la zona

        Returns:
            Lista de guardias en esa zona
        """
        pass

    @abstractmethod
    def find_by_fecha_turno_recreo(
        self,
        fecha: date,
        turno: str,
        recreo: int
    ) -> list[GuardiaEntity]:
        """
        Obtiene guardias de un momento específico.

        Args:
            fecha: Fecha
            turno: Turno ('mañana' o 'tarde')
            recreo: Número de recreo

        Returns:
            Lista de guardias en ese momento
        """
        pass

    @abstractmethod
    def find_by_rango_fechas(
        self,
        fecha_inicio: date,
        fecha_fin: date
    ) -> list[GuardiaEntity]:
        """
        Obtiene guardias en un rango de fechas.

        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin

        Returns:
            Lista de guardias en el rango
        """
        pass

    @abstractmethod
    def existe_guardia_profesor_en_momento(
        self,
        profesor_id: int,
        fecha: date,
        turno: str,
        recreo: int
    ) -> bool:
        """
        Verifica si un profesor tiene guardia en un momento específico.

        Args:
            profesor_id: ID del profesor
            fecha: Fecha
            turno: Turno
            recreo: Número de recreo

        Returns:
            True si tiene guardia, False si no
        """
        pass

    @abstractmethod
    def existe_guardia_zona_en_momento(
        self,
        zona_id: int,
        fecha: date,
        turno: str,
        recreo: int
    ) -> bool:
        """
        Verifica si una zona tiene guardia asignada en un momento específico.

        Args:
            zona_id: ID de la zona
            fecha: Fecha
            turno: Turno
            recreo: Número de recreo

        Returns:
            True si la zona está ocupada, False si no
        """
        pass

    @abstractmethod
    def contar_guardias_profesor(self, profesor_id: int) -> int:
        """
        Cuenta el total de guardias de un profesor.

        Args:
            profesor_id: ID del profesor

        Returns:
            Número de guardias
        """
        pass

    @abstractmethod
    def contar_guardias_profesor_en_fecha(
        self,
        profesor_id: int,
        fecha: date
    ) -> int:
        """
        Cuenta las guardias de un profesor en una fecha.

        Args:
            profesor_id: ID del profesor
            fecha: Fecha

        Returns:
            Número de guardias en esa fecha
        """
        pass

    @abstractmethod
    def delete_by_fecha_turno_recreo(
        self,
        fecha: date,
        turno: str,
        recreo: int
    ) -> int:
        """
        Elimina todas las guardias de un momento específico.

        Args:
            fecha: Fecha
            turno: Turno
            recreo: Número de recreo

        Returns:
            Número de guardias eliminadas
        """
        pass

    @abstractmethod
    def find_sustituciones(self) -> list[GuardiaEntity]:
        """
        Obtiene todas las guardias que son sustituciones.

        Returns:
            Lista de guardias de sustitución
        """
        pass
