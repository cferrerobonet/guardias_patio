"""
SQLAlchemy Ausencia Repository Implementation
"""

from datetime import date
from typing import Optional

from domain.repositories.ausencia_repository import IAusenciaRepository
from models.models import Ausencia
from sqlalchemy.orm import Session


class SQLAlchemyAusenciaRepository(IAusenciaRepository):
    """
    Implementación SQLAlchemy del repositorio de ausencias.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, entity_id: int) -> Optional[Ausencia]:
        """Obtiene ausencia por ID."""
        return self.session.query(Ausencia).get(entity_id)

    def get_all(self) -> list[Ausencia]:
        """Obtiene todas las ausencias."""
        return self.session.query(Ausencia).all()

    def save(self, entity: Ausencia) -> Ausencia:
        """Guarda o actualiza ausencia."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity_id: int) -> bool:
        """Elimina ausencia."""
        ausencia = self.get_by_id(entity_id)
        if ausencia:
            self.session.delete(ausencia)
            self.session.flush()
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        """Verifica si existe una ausencia con el ID dado."""
        return self.session.query(Ausencia).filter_by(id=entity_id).count() > 0

    def count(self) -> int:
        """Cuenta el total de ausencias."""
        return self.session.query(Ausencia).count()

    def find_by_profesor_and_date(
        self, profesor_id: int, fecha: date
    ) -> Optional[Ausencia]:
        """Busca ausencia activa de un profesor en una fecha."""
        return (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_inicio <= fecha,
                Ausencia.fecha_fin >= fecha,
                Ausencia.activa == True,  # noqa: E712
            )
            .first()
        )

    def find_by_profesor_and_period(
        self, profesor_id: int, fecha_inicio: date, fecha_fin: date
    ) -> list[Ausencia]:
        """Busca ausencias de un profesor en un periodo."""
        return (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_fin >= fecha_inicio,
                Ausencia.fecha_inicio <= fecha_fin,
            )
            .all()
        )

    def count_by_profesor(self, profesor_id: int) -> int:
        """Cuenta ausencias totales de un profesor."""
        return (
            self.session.query(Ausencia)
            .filter(Ausencia.profesor_id == profesor_id)
            .count()
        )

    def find_active_in_date(self, fecha: date) -> list[Ausencia]:
        """Encuentra todas las ausencias activas en una fecha."""
        return (
            self.session.query(Ausencia)
            .filter(
                Ausencia.fecha_inicio <= fecha,
                Ausencia.fecha_fin >= fecha,
                Ausencia.activa == True,  # noqa: E712
            )
            .all()
        )
