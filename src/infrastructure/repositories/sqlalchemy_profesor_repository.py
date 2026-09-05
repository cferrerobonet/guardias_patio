"""
SQLAlchemy Profesor Repository

Implementación concreta del repositorio de profesores usando SQLAlchemy.
"""

from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from core.exceptions import DatabaseError, ProfesorNotFoundError
from core.logging import get_logger, log_function_call
from domain.entities import ProfesorEntity
from domain.repositories import IProfesorRepository
from infrastructure.database.models import Guardia, Profesor
from infrastructure.mappers import ProfesorMapper

logger = get_logger(__name__)


class SQLAlchemyProfesorRepository(IProfesorRepository):
    """
    Implementación del repositorio de profesores con SQLAlchemy.

    Maneja la persistencia de profesores en base de datos.
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
        self.mapper = ProfesorMapper

    @log_function_call()
    def get_by_id(self, entity_id: int) -> Optional[ProfesorEntity]:
        """Obtiene un profesor por ID."""
        try:
            model = self.session.query(Profesor).filter(Profesor.id == entity_id).first()
            if model is None:
                return None
            return self.mapper.to_entity(model)
        except SQLAlchemyError as e:
            logger.error("Error al obtener profesor por ID", entity_id=entity_id, error=str(e))
            raise DatabaseError(message=f"Error al obtener profesor {entity_id}", original_error=e)

    @log_function_call()
    def get_all(self) -> list[ProfesorEntity]:
        """Obtiene todos los profesores ordenados alfabéticamente."""
        try:
            models = (
                self.session.query(Profesor)
                .options(joinedload(Profesor.zona_preferida), joinedload(Profesor.curso))
                .order_by(Profesor.nombre_completo)
                .all()
            )
            return self.mapper.to_entities(models)
        except SQLAlchemyError as e:
            logger.error("Error al obtener todos los profesores", error=str(e))
            raise DatabaseError(message="Error al obtener lista de profesores", original_error=e)

    @log_function_call()
    def save(self, entity: ProfesorEntity) -> ProfesorEntity:
        """Guarda un profesor (crear o actualizar)."""
        try:
            if entity.id:
                # Actualizar existente
                model = self.session.query(Profesor).filter(Profesor.id == entity.id).first()
                if model is None:
                    raise ProfesorNotFoundError(profesor_id=entity.id)
                model = self.mapper.update_model_from_entity(model, entity)
            else:
                # Crear nuevo
                model = self.mapper.to_model(entity)
                self.session.add(model)

            self.session.flush()  # Para obtener el ID generado
            entity.id = model.id

            logger.info("Profesor guardado", profesor_id=entity.id, nombre=entity.nombre_completo)
            return entity

        except ProfesorNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error("Error al guardar profesor", profesor_id=entity.id, error=str(e))
            raise DatabaseError(
                message=f"Error al guardar profesor {entity.nombre_completo}", original_error=e
            )

    @log_function_call()
    def delete(self, entity_id: int) -> bool:
        """Elimina un profesor por ID."""
        try:
            model = self.session.query(Profesor).filter(Profesor.id == entity_id).first()
            if model is None:
                return False

            self.session.delete(model)
            logger.info("Profesor eliminado", profesor_id=entity_id)
            return True

        except SQLAlchemyError as e:
            logger.error("Error al eliminar profesor", profesor_id=entity_id, error=str(e))
            raise DatabaseError(message=f"Error al eliminar profesor {entity_id}", original_error=e)

    def exists(self, entity_id: int) -> bool:
        """Verifica si existe un profesor."""
        return self.session.query(Profesor).filter(Profesor.id == entity_id).first() is not None

    def count(self) -> int:
        """Cuenta el total de profesores."""
        return self.session.query(Profesor).count()

    # Métodos específicos de IProfesorRepository

    def find_by_nombre(self, nombre: str) -> list[ProfesorEntity]:
        """Busca profesores por nombre (búsqueda parcial)."""
        try:
            models = (
                self.session.query(Profesor)
                .filter(Profesor.nombre_completo.ilike(f"%{nombre}%"))
                .all()
            )
            return self.mapper.to_entities(models)
        except SQLAlchemyError as e:
            logger.error("Error al buscar por nombre", nombre=nombre, error=str(e))
            raise DatabaseError(message="Error en búsqueda por nombre", original_error=e)

    def find_by_email(self, email: str) -> Optional[ProfesorEntity]:
        """Busca un profesor por email."""
        try:
            model = self.session.query(Profesor).filter(Profesor.email_corporativo == email).first()
            return self.mapper.to_entity(model) if model else None
        except SQLAlchemyError as e:
            logger.error("Error al buscar por email", email=email, error=str(e))
            raise DatabaseError(message="Error en búsqueda por email", original_error=e)

    def find_by_turno(self, turno: str) -> list[ProfesorEntity]:
        """Obtiene profesores de un turno específico."""
        try:
            models = self.session.query(Profesor).filter(Profesor.turno == turno).all()
            return self.mapper.to_entities(models)
        except SQLAlchemyError as e:
            logger.error("Error al buscar por turno", turno=turno, error=str(e))
            raise DatabaseError(message="Error en búsqueda por turno", original_error=e)

    def find_tutores(self) -> list[ProfesorEntity]:
        """Obtiene todos los tutores."""
        try:
            models = self.session.query(Profesor).filter(Profesor.tutor).all()
            return self.mapper.to_entities(models)
        except SQLAlchemyError as e:
            logger.error("Error al buscar tutores", error=str(e))
            raise DatabaseError(message="Error en búsqueda de tutores", original_error=e)

    def find_disponibles_en_fecha(
        self, fecha: date, turno: str, recreo: int
    ) -> list[ProfesorEntity]:
        """Obtiene profesores disponibles en una fecha, turno y recreo."""
        try:
            # Obtener todos los profesores del turno
            profesores = self.find_by_turno(turno)

            # Filtrar por disponibilidad (lógica de dominio)
            disponibles = []
            for profesor in profesores:
                puede, _ = profesor.puede_asignar_guardia(fecha, turno, recreo)
                if puede:
                    disponibles.append(profesor)

            return disponibles

        except (ValueError, TypeError, OSError) as e:
            logger.error(
                "Error al buscar disponibles", fecha=fecha, turno=turno, recreo=recreo, error=str(e)
            )
            raise DatabaseError(message="Error en búsqueda de disponibles", original_error=e)

    def find_con_menos_guardias(self, limite: int = 10) -> list[ProfesorEntity]:
        """Obtiene profesores con menos guardias asignadas."""
        try:
            # Subquery para contar guardias por profesor
            guardias_count = (
                self.session.query(
                    Guardia.profesor_id, func.count(Guardia.id).label("total_guardias")
                )
                .group_by(Guardia.profesor_id)
                .subquery()
            )

            # Query principal con left join para incluir profesores sin guardias
            models = (
                self.session.query(Profesor)
                .outerjoin(guardias_count, Profesor.id == guardias_count.c.profesor_id)
                .order_by(func.coalesce(guardias_count.c.total_guardias, 0))
                .limit(limite)
                .all()
            )

            return self.mapper.to_entities(models)

        except SQLAlchemyError as e:
            logger.error("Error al buscar con menos guardias", limite=limite, error=str(e))
            raise DatabaseError(
                message="Error en búsqueda de profesores con menos guardias", original_error=e
            )

    def contar_guardias_profesor(self, profesor_id: int) -> int:
        """Cuenta el total de guardias de un profesor."""
        return (
            self.session.query(func.count(Guardia.id))
            .filter(Guardia.profesor_id == profesor_id)
            .scalar()
            or 0
        )

    def contar_guardias_profesor_en_fecha(self, profesor_id: int, fecha: date) -> int:
        """Cuenta las guardias de un profesor en una fecha."""
        return (
            self.session.query(func.count(Guardia.id))
            .filter(Guardia.profesor_id == profesor_id, Guardia.fecha == fecha)
            .scalar()
            or 0
        )
