"""
Ausencia Mapper

Convierte entre el modelo SQLAlchemy Ausencia y la entidad AusenciaEntity.
"""

from typing import Optional

from domain.entities.ausencia_entity import AusenciaEntity
from infrastructure.database.models import Ausencia


class AusenciaMapper:
    """Mapper para convertir entre Ausencia (ORM) y AusenciaEntity (Domain)."""

    @staticmethod
    def to_entity(model: Ausencia) -> AusenciaEntity:
        return AusenciaEntity(
            id=model.id,
            profesor_id=model.profesor_id,
            fecha_inicio=model.fecha_inicio,
            fecha_fin=model.fecha_fin,
            tipo=model.tipo,
            motivo=model.motivo,
            documento_path=model.documento_path,
            activa=model.activa,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: AusenciaEntity, model: Optional[Ausencia] = None) -> Ausencia:
        if model is None:
            model = Ausencia()
        model.profesor_id = entity.profesor_id
        model.fecha_inicio = entity.fecha_inicio
        model.fecha_fin = entity.fecha_fin
        model.tipo = entity.tipo
        model.motivo = entity.motivo
        model.documento_path = entity.documento_path
        model.activa = entity.activa
        if entity.id is not None:
            model.id = entity.id
        return model
