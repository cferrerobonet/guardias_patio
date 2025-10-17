"""
Zona Mapper

Convierte entre el modelo SQLAlchemy Zona y la entidad ZonaEntity.
"""

from typing import Optional

from domain.entities import ZonaEntity
from models.models import Zona


class ZonaMapper:
    """
    Mapper para convertir entre Zona (SQLAlchemy) y ZonaEntity (Domain).
    """

    @staticmethod
    def to_entity(model: Zona) -> ZonaEntity:
        """
        Convierte un modelo SQLAlchemy a una entidad de dominio.

        Args:
            model: Modelo SQLAlchemy Zona

        Returns:
            ZonaEntity
        """
        return ZonaEntity(
            id=model.id,
            nombre_zona=model.nombre_zona,
            descripcion=model.descripcion,
            capacidad_profesores=None,  # TODO: agregar al modelo si se necesita
            activa=True,  # TODO: agregar al modelo si se necesita
        )

    @staticmethod
    def to_model(entity: ZonaEntity, model: Optional[Zona] = None) -> Zona:
        """
        Convierte una entidad de dominio a un modelo SQLAlchemy.

        Args:
            entity: Entidad de dominio
            model: Modelo existente a actualizar (opcional)

        Returns:
            Modelo SQLAlchemy Zona
        """
        if model is None:
            model = Zona()

        model.nombre_zona = entity.nombre_zona
        model.descripcion = entity.descripcion

        return model

    @staticmethod
    def to_entities(models: list[Zona]) -> list[ZonaEntity]:
        """Convierte una lista de modelos a entidades."""
        return [ZonaMapper.to_entity(model) for model in models]
