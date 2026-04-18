"""
SQLAlchemy Configuracion Repository Implementation
"""

import json
from typing import Optional

from domain.entities.configuracion_entity import ConfiguracionEntity
from domain.repositories.configuracion_repository import IConfiguracionRepository
from infrastructure.database.models import Configuracion
from infrastructure.mappers.configuracion_mapper import ConfiguracionMapper
from sqlalchemy.orm import Session


class SQLAlchemyConfiguracionRepository(IConfiguracionRepository):
    """
    Implementación SQLAlchemy del repositorio de configuración.
    Retorna entidades de dominio ConfiguracionEntity, nunca modelos ORM.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, entity_id: int) -> Optional[ConfiguracionEntity]:
        model = self.session.query(Configuracion).get(entity_id)
        return ConfiguracionMapper.to_entity(model) if model else None

    def get_all(self) -> list[ConfiguracionEntity]:
        return [ConfiguracionMapper.to_entity(m) for m in self.session.query(Configuracion).all()]

    def save(self, entity: ConfiguracionEntity) -> ConfiguracionEntity:
        if entity.id:
            model = self.session.query(Configuracion).get(entity.id) or Configuracion()
        else:
            model = Configuracion()
        ConfiguracionMapper.to_model(entity, model)
        self.session.add(model)
        self.session.flush()
        return ConfiguracionMapper.to_entity(model)

    def delete(self, entity_id: int) -> bool:
        model = self.session.query(Configuracion).get(entity_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return self.session.query(Configuracion).filter_by(id=entity_id).count() > 0

    def count(self) -> int:
        return self.session.query(Configuracion).count()

    def get_active(self) -> Optional[ConfiguracionEntity]:
        model = self.session.query(Configuracion).first()
        return ConfiguracionMapper.to_entity(model) if model else None

    def get_first(self) -> Optional[ConfiguracionEntity]:
        model = self.session.query(Configuracion).first()
        return ConfiguracionMapper.to_entity(model) if model else None

    def find_by_curso_activo_id(self, curso_id: int) -> Optional[ConfiguracionEntity]:
        model = self.session.query(Configuracion).filter_by(curso_activo_id=curso_id).first()
        return ConfiguracionMapper.to_entity(model) if model else None
