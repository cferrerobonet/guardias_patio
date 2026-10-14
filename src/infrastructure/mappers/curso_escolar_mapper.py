"""
CursoEscolar Mapper

Convierte entre el modelo SQLAlchemy CursoEscolar y la entidad CursoEscolarEntity.
"""

from typing import Optional

from domain.entities.curso_escolar_entity import CursoEscolarEntity
from infrastructure.database.models import CursoEscolar


class CursoEscolarMapper:
    """Mapper para convertir entre CursoEscolar (ORM) y CursoEscolarEntity (Domain)."""

    @staticmethod
    def to_entity(model: CursoEscolar) -> CursoEscolarEntity:
        return CursoEscolarEntity(
            id=model.id,
            anio_inicio=model.anio_inicio,
            anio_fin=model.anio_fin,
            nombre=model.nombre,
            fecha_inicio=model.fecha_inicio,
            fecha_fin=model.fecha_fin,
            activo=model.activo,
            cerrado=model.cerrado,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: CursoEscolarEntity, model: Optional[CursoEscolar] = None) -> CursoEscolar:
        if model is None:
            model = CursoEscolar()
        model.anio_inicio = entity.anio_inicio
        model.anio_fin = entity.anio_fin
        model.nombre = entity.nombre
        model.fecha_inicio = entity.fecha_inicio
        model.fecha_fin = entity.fecha_fin
        model.activo = entity.activo
        model.cerrado = entity.cerrado
        if entity.id is not None:
            model.id = entity.id
        return model
