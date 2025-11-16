"""
Configuracion Repository Interface

Define operaciones para acceder a la configuración del sistema.
"""

from abc import abstractmethod

from domain.repositories.base_repository import IBaseRepository


class IConfiguracionRepository(IBaseRepository):
    """
    Interfaz del repositorio de configuración.

    La configuración es un singleton en el sistema.
    """

    @abstractmethod
    def get_active(self):
        """
        Obtiene la configuración activa del sistema.

        Returns:
            Configuración activa o None
        """
        pass

    @abstractmethod
    def get_first(self):
        """
        Obtiene la primera configuración (normalmente la única).

        Returns:
            Primera configuración o None
        """
        pass
