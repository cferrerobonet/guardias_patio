"""
Use Case: Eliminar un profesor.

Permite eliminar un profesor del sistema, verificando que no tenga guardias asignadas.
Invalida cache de profesores tras eliminar.
"""

from core.exceptions import BusinessLogicError, NotFoundError
from core.observability import with_metrics
from infrastructure.database.models import Guardia, Profesor
from sqlalchemy.orm import Session
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
            BusinessLogicError: Si el profesor tiene guardias asignadas
        """
        # Buscar el profesor
        profesor = self.session.query(Profesor).filter(Profesor.id == profesor_id).first()

        if not profesor:
            raise NotFoundError(entity_type="Profesor", entity_id=profesor_id)

        # Verificar que no tenga guardias asignadas
        guardias_count = (
            self.session.query(Guardia).filter(Guardia.profesor_id == profesor_id).count()
        )

        if guardias_count > 0:
            raise BusinessLogicError(
                f"No se puede eliminar el profesor '{profesor.nombre_completo}' "
                f"porque tiene {guardias_count} guardia(s) asignada(s). "
                "Elimine primero las guardias asociadas."
            )

        try:
            nombre_profesor = profesor.nombre_completo
            self.session.delete(profesor)
            self.session.commit()

            # Invalidar cache de profesores
            invalidate_profesores_cache()
            logger.info(
                f"Profesor eliminado y cache invalidado: {nombre_profesor} (ID: {profesor_id})"
            )

        except SQLAlchemyError as e:
            self.session.rollback()
            raise BusinessLogicError(f"Error al eliminar el profesor: {str(e)}") from e
