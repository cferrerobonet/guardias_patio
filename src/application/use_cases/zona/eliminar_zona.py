"""
Use Case: Eliminar una zona.

Permite eliminar una zona del sistema, verificando que no tenga guardias asignadas.
"""

from models.models import Guardia, Zona
from sqlalchemy.orm import Session
from utils.exceptions import BusinessLogicError, NotFoundError
from utils.logger import get_logger

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
        guardias_count = (
            self.session.query(Guardia).filter(Guardia.zona_id == zona_id).count()
        )

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

            logger.info(f"Zona eliminada: {nombre_zona} (ID: {zona_id})")

        except Exception as e:
            self.session.rollback()
            raise BusinessLogicError(f"Error al eliminar la zona: {str(e)}") from e
