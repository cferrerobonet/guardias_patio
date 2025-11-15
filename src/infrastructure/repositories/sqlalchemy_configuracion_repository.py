"""
SQLAlchemy Configuracion Repository Implementation
"""

from typing import Optional

from domain.repositories.configuracion_repository import IConfiguracionRepository
from models.models import Configuracion
from sqlalchemy.orm import Session


class SQLAlchemyConfiguracionRepository(IConfiguracionRepository):
    """
    Implementación SQLAlchemy del repositorio de configuración.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, entity_id: int) -> Optional[Configuracion]:
        """Obtiene configuración por ID."""
        return self.session.query(Configuracion).get(entity_id)

    def get_all(self) -> list[Configuracion]:
        """Obtiene todas las configuraciones."""
        return self.session.query(Configuracion).all()

    def save(self, entity: Configuracion) -> Configuracion:
        """Guarda o actualiza configuración."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity_id: int) -> bool:
        """Elimina configuración."""
        config = self.get_by_id(entity_id)
        if config:
            self.session.delete(config)
            self.session.flush()
            return True
        return False

    def get_active(self) -> Optional[Configuracion]:
        """Obtiene la configuración activa."""
        return self.session.query(Configuracion).first()

    def get_first(self) -> Optional[Configuracion]:
        """Obtiene la primera configuración."""
        return self.session.query(Configuracion).first()
