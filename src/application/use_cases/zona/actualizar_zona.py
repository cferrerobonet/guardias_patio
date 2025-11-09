"""
Use Case: Actualizar una zona existente.

Permite modificar los datos de una zona registrada en el sistema.
"""

from sqlalchemy.orm import Session

from application.dtos.zona_dto import ActualizarZonaDTO, ZonaDTO
from core.exceptions import BusinessLogicError, NotFoundError
from core.observability import with_metrics
from models.models import Zona
from utils.logger import get_logger
from utils.repository_cache import invalidate_zonas_cache

logger = get_logger(__name__)


class ActualizarZonaUseCase:
    """
    Caso de uso para actualizar una zona existente.

    Permite modificar nombre y/o descripción de una zona.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("actualizar_zona")
    def execute(self, zona_id: int, data: ActualizarZonaDTO) -> ZonaDTO:
        """
        Ejecutar la actualización de una zona.

        Args:
            zona_id: ID de la zona a actualizar
            data: DTO con los datos a actualizar (campos opcionales)

        Returns:
            ZonaDTO con los datos actualizados de la zona

        Raises:
            NotFoundError: Si no existe una zona con ese ID
            BusinessLogicError: Si el nuevo nombre ya está en uso por otra zona
        """
        # Buscar la zona a actualizar
        zona = self.session.query(Zona).filter(Zona.id == zona_id).first()

        if not zona:
            raise NotFoundError(f"No se encontró la zona con ID {zona_id}")

        # Si se va a cambiar el nombre, verificar que no exista otra zona con ese nombre
        if data.nombre_zona and data.nombre_zona != zona.nombre_zona:
            zona_existente = (
                self.session.query(Zona)
                .filter(Zona.nombre_zona == data.nombre_zona)
                .filter(Zona.id != zona_id)
                .first()
            )

            if zona_existente:
                raise BusinessLogicError(f"Ya existe otra zona con el nombre '{data.nombre_zona}'")

        # Actualizar campos si se proporcionan
        if data.nombre_zona is not None:
            zona.nombre_zona = data.nombre_zona

        if data.descripcion is not None:
            zona.descripcion = data.descripcion or None

        # Actualizar fechas (pueden ser None para eliminar restricciones temporales)
        if hasattr(data, "fecha_inicio"):
            zona.fecha_inicio = data.fecha_inicio

        if hasattr(data, "fecha_fin"):
            zona.fecha_fin = data.fecha_fin

        try:
            self.session.commit()
            self.session.refresh(zona)

            # Invalidar cache de zonas
            invalidate_zonas_cache()
            logger.info(f"Zona actualizada y cache invalidado: {zona.nombre_zona} (ID: {zona.id})")

            return ZonaDTO.model_validate(zona)

        except Exception as e:
            self.session.rollback()
            raise BusinessLogicError(f"Error al actualizar la zona: {str(e)}") from e
