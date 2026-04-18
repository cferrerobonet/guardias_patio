"""
SQLAlchemy Ausencia Repository Implementation
"""

from datetime import date
from typing import Optional

from domain.entities.ausencia_entity import AusenciaEntity
from domain.repositories.ausencia_repository import IAusenciaRepository
from infrastructure.database.models import Ausencia
from infrastructure.mappers.ausencia_mapper import AusenciaMapper
from sqlalchemy.orm import Session


class SQLAlchemyAusenciaRepository(IAusenciaRepository):
    """
    Implementación SQLAlchemy del repositorio de ausencias.
    Retorna entidades de dominio AusenciaEntity, nunca modelos ORM.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, entity_id: int) -> Optional[AusenciaEntity]:
        model = self.session.query(Ausencia).get(entity_id)
        return AusenciaMapper.to_entity(model) if model else None

    def get_all(self) -> list[AusenciaEntity]:
        return [AusenciaMapper.to_entity(m) for m in self.session.query(Ausencia).all()]

    def save(self, entity: AusenciaEntity) -> AusenciaEntity:
        if entity.id:
            model = self.session.query(Ausencia).get(entity.id) or Ausencia()
        else:
            model = Ausencia()
        AusenciaMapper.to_model(entity, model)
        self.session.add(model)
        self.session.flush()
        return AusenciaMapper.to_entity(model)

    def delete(self, entity_id: int) -> bool:
        model = self.session.query(Ausencia).get(entity_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return self.session.query(Ausencia).filter_by(id=entity_id).first() is not None

    def count(self) -> int:
        return self.session.query(Ausencia).count()

    def find_by_profesor_and_date(self, profesor_id: int, fecha: date) -> Optional[AusenciaEntity]:
        model = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_inicio <= fecha,
                Ausencia.fecha_fin >= fecha,
                Ausencia.activa == True,  # noqa: E712
            )
            .first()
        )
        return AusenciaMapper.to_entity(model) if model else None

    def find_by_profesor_and_period(
        self, profesor_id: int, fecha_inicio: date, fecha_fin: date
    ) -> list[AusenciaEntity]:
        models = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_fin >= fecha_inicio,
                Ausencia.fecha_inicio <= fecha_fin,
            )
            .all()
        )
        return [AusenciaMapper.to_entity(m) for m in models]

    def count_by_profesor(self, profesor_id: int) -> int:
        return self.session.query(Ausencia).filter(Ausencia.profesor_id == profesor_id).count()

    def find_active_in_date(self, fecha: date) -> list[AusenciaEntity]:
        models = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.fecha_inicio <= fecha,
                Ausencia.fecha_fin >= fecha,
                Ausencia.activa == True,  # noqa: E712
            )
            .all()
        )
        return [AusenciaMapper.to_entity(m) for m in models]

    def find_active_in_rango(self, fecha_inicio: date, fecha_fin: date) -> list[AusenciaEntity]:
        """Retorna ausencias activas que se solapan con el rango dado."""
        models = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.activa == True,  # noqa: E712
                Ausencia.fecha_inicio <= fecha_fin,
                Ausencia.fecha_fin >= fecha_inicio,
            )
            .all()
        )
        return [AusenciaMapper.to_entity(m) for m in models]
