"""
SQLAlchemy CursoEscolar Repository Implementation
"""

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from domain.entities.curso_escolar_entity import CursoEscolarEntity
from domain.repositories.curso_escolar_repository import ICursoEscolarRepository
from infrastructure.database.models import CursoEscolar
from infrastructure.mappers.curso_escolar_mapper import CursoEscolarMapper


class SQLAlchemyCursoEscolarRepository(ICursoEscolarRepository):
    """
    Implementación SQLAlchemy del repositorio de cursos escolares.
    Retorna entidades de dominio CursoEscolarEntity, nunca modelos ORM.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, entity_id: int) -> Optional[CursoEscolarEntity]:
        model = self.session.query(CursoEscolar).get(entity_id)
        return CursoEscolarMapper.to_entity(model) if model else None

    def get_all(self) -> list[CursoEscolarEntity]:
        return [CursoEscolarMapper.to_entity(m) for m in self.session.query(CursoEscolar).all()]

    def save(self, entity: CursoEscolarEntity) -> CursoEscolarEntity:
        if entity.id:
            model = self.session.query(CursoEscolar).get(entity.id) or CursoEscolar()
        else:
            model = CursoEscolar()
        CursoEscolarMapper.to_model(entity, model)
        self.session.add(model)
        self.session.flush()
        return CursoEscolarMapper.to_entity(model)

    def delete(self, entity_id: int) -> bool:
        model = self.session.query(CursoEscolar).get(entity_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return self.session.query(CursoEscolar).filter_by(id=entity_id).first() is not None

    def count(self) -> int:
        return self.session.query(CursoEscolar).count()

    def find_active(self) -> Optional[CursoEscolarEntity]:
        model = self.session.query(CursoEscolar).filter_by(activo=True).first()
        return CursoEscolarMapper.to_entity(model) if model else None

    def find_by_year(self, anio_inicio: int) -> Optional[CursoEscolarEntity]:
        model = self.session.query(CursoEscolar).filter_by(anio_inicio=anio_inicio).first()
        return CursoEscolarMapper.to_entity(model) if model else None

    def deactivate_all(self) -> None:
        self.session.query(CursoEscolar).update({CursoEscolar.activo: False})
        self.session.flush()

    def find_by_date_range(
        self, fecha_inicio: str, fecha_fin: str
    ) -> list[CursoEscolarEntity]:
        models = (
            self.session.query(CursoEscolar)
            .filter(
                or_(
                    CursoEscolar.fecha_inicio.between(fecha_inicio, fecha_fin),
                    CursoEscolar.fecha_fin.between(fecha_inicio, fecha_fin),
                    (
                        (CursoEscolar.fecha_inicio <= fecha_inicio)
                        & (CursoEscolar.fecha_fin >= fecha_fin)
                    ),
                )
            )
            .all()
        )
        return [CursoEscolarMapper.to_entity(m) for m in models]
