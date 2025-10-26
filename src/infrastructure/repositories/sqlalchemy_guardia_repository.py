"""
SQLAlchemy Guardia Repository

Implementación del repositorio de Guardia usando SQLAlchemy.
"""

from datetime import date
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from core.exceptions import DatabaseError, NotFoundError
from core.logging import get_logger, log_function_call
from domain.entities import GuardiaEntity
from domain.repositories import IGuardiaRepository
from infrastructure.mappers import GuardiaMapper
from models.models import Guardia

logger = get_logger(__name__)


class SQLAlchemyGuardiaRepository(IGuardiaRepository):
    """
    Implementación de IGuardiaRepository usando SQLAlchemy.

    Utiliza GuardiaMapper para convertir entre modelos y entidades.
    """

    def __init__(self, session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión de SQLAlchemy para operaciones de BD
        """
        self.session = session
        self.mapper = GuardiaMapper()

    @log_function_call()
    def get_by_id(self, entity_id: int) -> Optional[GuardiaEntity]:
        """Obtiene una guardia por ID."""
        try:
            model = self.session.query(Guardia).filter(Guardia.id == entity_id).first()
            if model:
                return self.mapper.to_entity(model)
            return None
        except Exception as e:
            logger.error("Error al obtener guardia por ID", guardia_id=entity_id, error=str(e))
            raise DatabaseError(f"Error al obtener guardia {entity_id}: {e}") from e

    @log_function_call()
    def get_all(self) -> list[GuardiaEntity]:
        """Obtiene todas las guardias con eager loading de relaciones."""
        try:
            models = (
                self.session.query(Guardia)
                .options(
                    joinedload(Guardia.profesor),
                    joinedload(Guardia.zona)
                )
                .all()
            )
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error("Error al obtener todas las guardias", error=str(e))
            raise DatabaseError(f"Error al obtener guardias: {e}") from e

    @log_function_call()
    def save(self, entity: GuardiaEntity) -> GuardiaEntity:
        """
        Guarda una guardia (crear o actualizar).

        Si tiene ID, actualiza; si no, crea nuevo.
        """
        try:
            if entity.id:
                # Actualizar existente
                model = self.session.query(Guardia).filter(Guardia.id == entity.id).first()
                if not model:
                    raise NotFoundError(entity_type="Guardia", entity_id=entity.id)
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
            logger.error("Error al guardar guardia", guardia_id=entity.id, error=str(e))
            raise DatabaseError(f"Error al guardar guardia: {e}") from e

    @log_function_call()
    def delete(self, entity_id: int) -> bool:
        """Elimina una guardia por ID."""
        try:
            model = self.session.query(Guardia).filter(Guardia.id == entity_id).first()
            if not model:
                return False

            self.session.delete(model)
            self.session.flush()
            return True

        except Exception as e:
            logger.error("Error al eliminar guardia", guardia_id=entity_id, error=str(e))
            raise DatabaseError(f"Error al eliminar guardia {entity_id}: {e}") from e

    def exists(self, entity_id: int) -> bool:
        """Verifica si existe una guardia por ID."""
        try:
            return (
                self.session.query(Guardia.id)
                .filter(Guardia.id == entity_id)
                .first()
                is not None
            )
        except Exception as e:
            logger.error(
                "Error al verificar existencia de guardia",
                guardia_id=entity_id,
                error=str(e)
            )
            raise DatabaseError(f"Error al verificar guardia {entity_id}: {e}") from e

    def count(self) -> int:
        """Cuenta el total de guardias."""
        try:
            return self.session.query(Guardia).count()
        except Exception as e:
            logger.error("Error al contar guardias", error=str(e))
            raise DatabaseError(f"Error al contar guardias: {e}") from e

    # Métodos específicos de IGuardiaRepository

    @log_function_call()
    def find_by_fecha(self, fecha: date) -> list[GuardiaEntity]:
        """Obtiene todas las guardias de una fecha con eager loading."""
        try:
            models = (
                self.session.query(Guardia)
                .options(
                    joinedload(Guardia.profesor),
                    joinedload(Guardia.zona)
                )
                .filter(Guardia.fecha == fecha)
                .all()
            )
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error("Error al buscar guardias por fecha", fecha=fecha, error=str(e))
            raise DatabaseError(f"Error al buscar guardias por fecha: {e}") from e

    @log_function_call()
    def find_by_profesor(self, profesor_id: int) -> list[GuardiaEntity]:
        """Obtiene todas las guardias de un profesor con eager loading."""
        try:
            models = (
                self.session.query(Guardia)
                .options(joinedload(Guardia.zona))
                .filter(Guardia.profesor_id == profesor_id)
                .all()
            )
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error(
                "Error al buscar guardias por profesor",
                profesor_id=profesor_id,
                error=str(e)
            )
            raise DatabaseError(f"Error al buscar guardias por profesor: {e}") from e

    @log_function_call()
    def find_by_zona(self, zona_id: int) -> list[GuardiaEntity]:
        """Obtiene todas las guardias de una zona con eager loading."""
        try:
            models = (
                self.session.query(Guardia)
                .options(joinedload(Guardia.profesor))
                .filter(Guardia.zona_id == zona_id)
                .all()
            )
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error(
                "Error al buscar guardias por zona",
                zona_id=zona_id,
                error=str(e)
            )
            raise DatabaseError(f"Error al buscar guardias por zona: {e}") from e

    @log_function_call()
    def find_by_fecha_turno_recreo(
        self,
        fecha: date,
        turno: str,
        recreo: int
    ) -> list[GuardiaEntity]:
        """Obtiene todas las guardias de un momento específico."""
        try:
            models = (
                self.session.query(Guardia)
                .filter(
                    and_(
                        Guardia.fecha == fecha,
                        Guardia.turno == turno,
                        Guardia.recreo == recreo
                    )
                )
                .all()
            )
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error(
                "Error al buscar guardias por momento",
                fecha=fecha,
                turno=turno,
                recreo=recreo,
                error=str(e)
            )
            raise DatabaseError(f"Error al buscar guardias por momento: {e}") from e

    @log_function_call()
    def find_by_rango_fechas(
        self,
        fecha_inicio: date,
        fecha_fin: date
    ) -> list[GuardiaEntity]:
        """Obtiene guardias en un rango de fechas."""
        try:
            models = (
                self.session.query(Guardia)
                .filter(
                    and_(
                        Guardia.fecha >= fecha_inicio,
                        Guardia.fecha <= fecha_fin
                    )
                )
                .order_by(Guardia.fecha, Guardia.turno, Guardia.recreo)
                .all()
            )
            return self.mapper.to_entities(models)
        except Exception as e:
            logger.error(
                "Error al buscar guardias por rango",
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                error=str(e)
            )
            raise DatabaseError(f"Error al buscar guardias por rango: {e}") from e

    def existe_guardia_profesor_en_momento(
        self,
        profesor_id: int,
        fecha: date,
        turno: str,
        recreo: int
    ) -> bool:
        """Verifica si un profesor tiene guardia en un momento específico."""
        try:
            return (
                self.session.query(Guardia.id)
                .filter(
                    and_(
                        Guardia.profesor_id == profesor_id,
                        Guardia.fecha == fecha,
                        Guardia.turno == turno,
                        Guardia.recreo == recreo
                    )
                )
                .first()
                is not None
            )
        except Exception as e:
            logger.error(
                "Error al verificar guardia de profesor",
                profesor_id=profesor_id,
                fecha=fecha,
                turno=turno,
                recreo=recreo,
                error=str(e)
            )
            raise DatabaseError(f"Error al verificar guardia de profesor: {e}") from e

    def existe_guardia_zona_en_momento(
        self,
        zona_id: int,
        fecha: date,
        turno: str,
        recreo: int
    ) -> bool:
        """Verifica si una zona tiene alguna guardia en un momento específico."""
        try:
            return (
                self.session.query(Guardia.id)
                .filter(
                    and_(
                        Guardia.zona_id == zona_id,
                        Guardia.fecha == fecha,
                        Guardia.turno == turno,
                        Guardia.recreo == recreo
                    )
                )
                .first()
                is not None
            )
        except Exception as e:
            logger.error(
                "Error al verificar guardia de zona",
                zona_id=zona_id,
                fecha=fecha,
                turno=turno,
                recreo=recreo,
                error=str(e)
            )
            raise DatabaseError(f"Error al verificar guardia de zona: {e}") from e

    @log_function_call()
    def contar_guardias_profesor(self, profesor_id: int) -> int:
        """Cuenta el total de guardias de un profesor."""
        try:
            return (
                self.session.query(Guardia)
                .filter(Guardia.profesor_id == profesor_id)
                .count()
            )
        except Exception as e:
            logger.error(
                "Error al contar guardias de profesor",
                profesor_id=profesor_id,
                error=str(e)
            )
            raise DatabaseError(f"Error al contar guardias de profesor: {e}") from e

    @log_function_call()
    def contar_guardias_profesor_en_fecha(
        self,
        profesor_id: int,
        fecha: date
    ) -> int:
        """Cuenta las guardias de un profesor en una fecha específica."""
        try:
            return (
                self.session.query(Guardia)
                .filter(
                    and_(
                        Guardia.profesor_id == profesor_id,
                        Guardia.fecha == fecha
                    )
                )
                .count()
            )
        except Exception as e:
            logger.error(
                "Error al contar guardias de profesor en fecha",
                profesor_id=profesor_id,
                fecha=fecha,
                error=str(e)
            )
            raise DatabaseError(f"Error al contar guardias de profesor en fecha: {e}") from e

    @log_function_call()
    def delete_by_fecha_turno_recreo(
        self,
        fecha: date,
        turno: str,
        recreo: int
    ) -> int:
        """
        Elimina todas las guardias de un momento específico.

        Returns:
            Número de guardias eliminadas
        """
        try:
            count = (
                self.session.query(Guardia)
                .filter(
                    and_(
                        Guardia.fecha == fecha,
                        Guardia.turno == turno,
                        Guardia.recreo == recreo
                    )
                )
                .delete()
            )
            self.session.flush()
            return count
        except Exception as e:
            logger.error(
                "Error al eliminar guardias por momento",
                fecha=fecha,
                turno=turno,
                recreo=recreo,
                error=str(e)
            )
            raise DatabaseError(f"Error al eliminar guardias por momento: {e}") from e

    @log_function_call()
    def find_sustituciones(self, fecha_inicio: Optional[date] = None) -> list[GuardiaEntity]:
        """
        Encuentra todas las guardias de sustitución.

        Args:
            fecha_inicio: Fecha desde la cual buscar (opcional)

        Returns:
            Lista de guardias que son sustituciones
        """
        try:
            # Por ahora, como no tenemos el campo es_sustitucion en el modelo,
            # retornamos lista vacía
            # TODO: Agregar campo es_sustitucion al modelo Guardia
            return []
        except Exception as e:
            logger.error("Error al buscar sustituciones", error=str(e))
            raise DatabaseError(f"Error al buscar sustituciones: {e}") from e

    @log_function_call()
    def delete_all(self) -> int:
        """
        Elimina todas las guardias del sistema.

        Returns:
            Número de guardias eliminadas
        """
        try:
            # Contar primero cuántas guardias hay
            count = self.session.query(Guardia).count()

            # Eliminar todas las guardias
            self.session.query(Guardia).delete()
            self.session.commit()

            logger.info(f"Eliminadas {count} guardias del sistema")
            return count

        except Exception as e:
            self.session.rollback()
            logger.error("Error al eliminar todas las guardias", error=str(e))
            raise DatabaseError(f"Error al eliminar todas las guardias: {e}") from e
