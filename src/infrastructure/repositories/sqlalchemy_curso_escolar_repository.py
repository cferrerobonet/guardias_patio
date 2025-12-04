"""
SQLAlchemy CursoEscolar Repository Implementation
"""

from typing import Optional

from domain.repositories.curso_escolar_repository import ICursoEscolarRepository
from sqlalchemy import or_
from sqlalchemy.orm import Session

from infrastructure.database.models import CursoEscolar


class SQLAlchemyCursoEscolarRepository(ICursoEscolarRepository):
    """
    Implementación SQLAlchemy del repositorio de cursos escolares.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, entity_id: int) -> Optional[CursoEscolar]:
        """Obtiene curso escolar por ID."""
        return self.session.query(CursoEscolar).get(entity_id)

    def get_all(self) -> list[CursoEscolar]:
        """Obtiene todos los cursos escolares."""
        return self.session.query(CursoEscolar).all()

    def save(self, entity: CursoEscolar) -> CursoEscolar:
        """Guarda o actualiza curso escolar."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity_id: int) -> bool:
        """Elimina curso escolar."""
        curso = self.get_by_id(entity_id)
        if curso:
            self.session.delete(curso)
            self.session.flush()
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        """Verifica si existe un curso escolar con el ID dado."""
        return self.session.query(CursoEscolar).filter_by(id=entity_id).count() > 0

    def count(self) -> int:
        """Cuenta el total de cursos escolares."""
        return self.session.query(CursoEscolar).count()

    def find_active(self) -> Optional[CursoEscolar]:
        """Obtiene el curso escolar activo."""
        return self.session.query(CursoEscolar).filter_by(activo=True).first()

    def find_by_year(self, anio_inicio: int) -> Optional[CursoEscolar]:
        """Busca curso por año de inicio."""
        return self.session.query(CursoEscolar).filter_by(anio_inicio=anio_inicio).first()

    def deactivate_all(self) -> None:
        """Desactiva todos los cursos escolares."""
        self.session.query(CursoEscolar).update({CursoEscolar.activo: False})
        self.session.flush()

    def find_by_date_range(self, fecha_inicio: str, fecha_fin: str) -> list[CursoEscolar]:
        """Busca cursos que se solapen con un rango de fechas."""
        return (
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
