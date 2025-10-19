"""
SQLAlchemy Zona Repository

Implementación del repositorio de Zona usando SQLAlchemy.
"""

from typing import Optional

from sqlalchemy.orm import Session

from core.exceptions import DatabaseError, NotFoundError
from core.logging import get_logger, log_function_call
from domain.entities import ZonaEntity
from domain.repositories import IZonaRepository
from infrastructure.mappers import ZonaMapper
from models.models import Zona

logger = get_logger(__name__)


class SQLAlchemyZonaRepository(IZonaRepository):
    """
    Implementación de IZonaRepository usando SQLAlchemy.

    Utiliza ZonaMapper para convertir entre modelos y entidades.
    """

    def __init__(self, session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión de SQLAlchemy para operaciones de BD
        """
        self.session = session
        self.mapper = ZonaMapper()

    @log_function_call()
    def get_by_id(self, entity_id: int) -> Optional[ZonaEntity]:
        """Obtiene una zona por ID."""
        try:
            model = self.session.query(Zona).filter(Zona.id == entity_id).first()
            if model:
                return self.mapper.to_entity(model)
            return None
        except Exception as e:
            logger.error("Error al obtener zona por ID", zona_id=entity_id, error=str(e))
            raise DatabaseError(f"Error al obtener zona {entity_id}: {e}") from e

    @log_function_call()
    def get_all(self) -> list[ZonaEntity]:
        """Obtiene todas las zonas."""
        try:
            models = self.session.query(Zona).all()
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error("Error al obtener todas las zonas", error=str(e))
            raise DatabaseError(f"Error al obtener zonas: {e}") from e

    @log_function_call()
    def save(self, entity: ZonaEntity) -> ZonaEntity:
        """
        Guarda una zona (crear o actualizar).

        Si tiene ID, actualiza; si no, crea nuevo.
        """
        try:
            if entity.id:
                # Actualizar existente
                model = self.session.query(Zona).filter(Zona.id == entity.id).first()
                if not model:
                    raise NotFoundError(entity_type="Zona", entity_id=entity.id)
                model = self.mapper.to_model(entity, model)
            else:
                # Crear nuevo
                model = self.mapper.to_model(entity)
                self.session.add(model)

            self.session.flush()  # Obtener ID sin commit
            return self.mapper.to_entity(model)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error al guardar zona", zona_id=entity.id, error=str(e))
            raise DatabaseError(f"Error al guardar zona: {e}") from e

    @log_function_call()
    def delete(self, entity_id: int) -> bool:
        """Elimina una zona por ID."""
        try:
            model = self.session.query(Zona).filter(Zona.id == entity_id).first()
            if not model:
                return False

            self.session.delete(model)
            self.session.flush()
            return True

        except Exception as e:
            logger.error("Error al eliminar zona", zona_id=entity_id, error=str(e))
            raise DatabaseError(f"Error al eliminar zona {entity_id}: {e}") from e

    def exists(self, entity_id: int) -> bool:
        """Verifica si existe una zona por ID."""
        try:
            return (
                self.session.query(Zona.id)
                .filter(Zona.id == entity_id)
                .first()
                is not None
            )
        except Exception as e:
            logger.error("Error al verificar existencia de zona", zona_id=entity_id, error=str(e))
            raise DatabaseError(f"Error al verificar zona {entity_id}: {e}") from e

    def count(self) -> int:
        """Cuenta el total de zonas."""
        try:
            return self.session.query(Zona).count()
        except Exception as e:
            logger.error("Error al contar zonas", error=str(e))
            raise DatabaseError(f"Error al contar zonas: {e}") from e

    # Métodos específicos de IZonaRepository

    @log_function_call()
    def find_by_nombre(self, nombre: str) -> Optional[ZonaEntity]:
        """Busca una zona por nombre exacto."""
        try:
            model = (
                self.session.query(Zona)
                .filter(Zona.nombre_zona == nombre)
                .first()
            )
            if model:
                return self.mapper.to_entity(model)
            return None
        except Exception as e:
            logger.error("Error al buscar zona por nombre", nombre=nombre, error=str(e))
            raise DatabaseError(f"Error al buscar zona por nombre: {e}") from e

    @log_function_call()
    def find_activas(self) -> list[ZonaEntity]:
        """Obtiene todas las zonas activas."""
        try:
            # Por ahora no hay campo 'activa' en el modelo actual
            # Retornamos todas las zonas
            models = self.session.query(Zona).all()
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error("Error al obtener zonas activas", error=str(e))
            raise DatabaseError(f"Error al obtener zonas activas: {e}") from e

    @log_function_call()
    def find_con_capacidad_disponible(
        self,
        fecha,
        turno: str,
        recreo: int,
    ) -> list[ZonaEntity]:
        """
        Encuentra zonas con capacidad disponible en un momento específico.

        Args:
            fecha: Fecha de la guardia
            turno: Turno de la guardia
            recreo: Número de recreo

        Returns:
            Lista de zonas con capacidad disponible
        """
        try:
            # Por ahora, retornamos todas las zonas activas
            # En el futuro, podríamos contar las guardias asignadas
            # y filtrar las que tienen capacidad
            models = self.session.query(Zona).all()
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error(
                "Error al buscar zonas con capacidad",
                fecha=fecha,
                turno=turno,
                recreo=recreo,
                error=str(e)
            )
            raise DatabaseError(f"Error al buscar zonas con capacidad: {e}") from e
