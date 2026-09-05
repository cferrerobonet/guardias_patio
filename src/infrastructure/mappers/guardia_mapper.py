"""
Guardia Mapper

Convierte entre el modelo SQLAlchemy Guardia y la entidad GuardiaEntity.
"""

from typing import Optional

from domain.entities import GuardiaEntity
from infrastructure.database.models import Guardia


class GuardiaMapper:
    """
    Mapper para convertir entre Guardia (SQLAlchemy) y GuardiaEntity (Domain).
    """

    @staticmethod
    def to_entity(model: Guardia) -> GuardiaEntity:
        """
        Convierte un modelo SQLAlchemy a una entidad de dominio.

        Args:
            model: Modelo SQLAlchemy Guardia

        Returns:
            GuardiaEntity
        """
        return GuardiaEntity(
            id=model.id,
            profesor_id=model.profesor_id,
            zona_id=model.zona_id,
            fecha=model.fecha,
            turno=model.turno,
            recreo=model.recreo,
            es_sustitucion=bool(model.es_sustitucion),
            profesor_sustituido_id=model.profesor_sustituido_id,
            notas=model.notas,
        )

    @staticmethod
    def to_model(entity: GuardiaEntity, model: Optional[Guardia] = None) -> Guardia:
        """
        Convierte una entidad de dominio a un modelo SQLAlchemy.

        Args:
            entity: Entidad de dominio
            model: Modelo existente a actualizar (opcional)

        Returns:
            Modelo SQLAlchemy Guardia
        """
        if model is None:
            model = Guardia()

        model.profesor_id = entity.profesor_id
        model.zona_id = entity.zona_id
        model.fecha = entity.fecha
        model.turno = entity.turno
        model.recreo = entity.recreo
        model.es_sustitucion = entity.es_sustitucion
        model.profesor_sustituido_id = entity.profesor_sustituido_id
        model.notas = entity.notas

        return model

    @staticmethod
    def to_entities(models: list[Guardia]) -> list[GuardiaEntity]:
        """Convierte una lista de modelos a entidades."""
        return [GuardiaMapper.to_entity(model) for model in models]
