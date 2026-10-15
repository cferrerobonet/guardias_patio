"""
Use Case: Eliminar un profesor.

Permite eliminar un profesor del sistema, verificando que no tenga guardias asignadas.
Invalida cache de profesores tras eliminar.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.exceptions import BusinessLogicError, NotFoundError
from core.observability import with_metrics
from infrastructure.database.models import Ausencia, Guardia, Profesor
from utils.logger import get_logger
from utils.repository_cache import invalidate_profesores_cache

logger = get_logger(__name__)


class EliminarProfesorUseCase:
    """
    Caso de uso para eliminar un profesor.

    Elimina un profesor del sistema verificando que no tenga guardias asignadas.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("eliminar_profesor")
    def execute(self, profesor_id: int) -> None:
        """
        Ejecutar la eliminación de un profesor.

        Args:
            profesor_id: ID del profesor a eliminar

        Raises:
            NotFoundError: Si no existe un profesor con ese ID
            BusinessLogicError: Si falla el borrado en la base de datos
        """
        # Buscar el profesor
        profesor = self.session.query(Profesor).filter(Profesor.id == profesor_id).first()

        if not profesor:
            raise NotFoundError(entity_type="Profesor", entity_id=profesor_id)

        try:
            nombre_profesor = profesor.nombre_completo
            # Sus guardias se van con él (decisión de CarlosFB, 2026-10-15): la
            # pantalla ya avisa de que se borran y ofrece una copia (PRIV-003), y
            # negarse aquí salía como error técnico. Sus huecos quedan sin cubrir
            # hasta que se regenere. Las guardias en las que sólo figura como
            # sustituido no son suyas y se conservan.
            guardias_borradas = (
                self.session.query(Guardia)
                .filter(Guardia.profesor_id == profesor_id)
                .delete(synchronize_session=False)
            )
            # Sus ausencias se van con él: si no, el ORM intentaba dejarlas sin
            # profesor y el borrado fallaba con un error técnico (2026-10-03).
            for ausencia in self.session.query(Ausencia).filter_by(profesor_id=profesor_id):
                self.session.delete(ausencia)
            self.session.delete(profesor)
            self.session.commit()

            # Invalidar cache de profesores
            invalidate_profesores_cache()
            logger.info(
                f"Profesor eliminado y cache invalidado: {nombre_profesor} (ID: {profesor_id}), "
                f"con {guardias_borradas} guardia(s)"
            )

        except SQLAlchemyError as e:
            self.session.rollback()
            raise BusinessLogicError(f"Error al eliminar el profesor: {str(e)}") from e
