"""
Use Case: Eliminar una zona.

Permite eliminar una zona del sistema, verificando que no tenga guardias asignadas.
"""

from core.exceptions import BusinessLogicError, NotFoundError
from core.observability import with_metrics
from infrastructure.database.models import Guardia, Zona
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from utils.logger import get_logger
from utils.repository_cache import invalidate_zonas_cache

logger = get_logger(__name__)


class EliminarZonaUseCase:
    """
    Caso de uso para eliminar una zona.

    Elimina una zona del sistema verificando que no tenga guardias asignadas.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("eliminar_zona")
    def execute(self, zona_id: int) -> None:
        """
        Ejecutar la eliminación de una zona.

        Args:
            zona_id: ID de la zona a eliminar

        Raises:
            NotFoundError: Si no existe una zona con ese ID
            BusinessLogicError: Si la zona tiene guardias asignadas
        """
        # Buscar la zona
        zona = self.session.query(Zona).filter(Zona.id == zona_id).first()

        if not zona:
            raise NotFoundError(f"No se encontró la zona con ID {zona_id}")

        # Verificar que no tenga guardias asignadas
        guardias_count = self.session.query(Guardia).filter(Guardia.zona_id == zona_id).count()

        if guardias_count > 0:
            raise BusinessLogicError(
                f"No se puede eliminar la zona '{zona.nombre_zona}' "
                f"porque tiene {guardias_count} guardia(s) asignada(s). "
                "Elimine primero las guardias asociadas."
            )

        try:
            nombre_zona = zona.nombre_zona
            self.session.delete(zona)
            self.session.commit()

            # Invalidar cache de zonas
            invalidate_zonas_cache()
            logger.info(f"Zona eliminada y cache invalidado: {nombre_zona} (ID: {zona_id})")

        except SQLAlchemyError as e:
            self.session.rollback()
            raise BusinessLogicError(f"Error al eliminar la zona: {str(e)}") from e
