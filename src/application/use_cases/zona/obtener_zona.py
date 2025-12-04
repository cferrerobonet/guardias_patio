"""
Use Case: Obtener una zona por su ID.

Permite recuperar los datos de una zona específica del sistema.
Con caching para optimizar lecturas frecuentes.
"""

from core.exceptions import NotFoundError
from core.observability import with_metrics
from infrastructure.database.models import Zona
from sqlalchemy.orm import Session
from utils.repository_cache import cache_zonas

from application.dtos.zona_dto import ZonaDTO


class ObtenerZonaUseCase:
    """
    Caso de uso para obtener una zona por su ID.

    Recupera los datos completos de una zona existente.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("obtener_zona")
    @cache_zonas(ttl=300)  # Cache por 5 minutos
    def execute(self, zona_id: int) -> ZonaDTO:
        """
        Ejecutar la obtención de una zona (con caching).

        Args:
            zona_id: ID de la zona a obtener

        Returns:
            ZonaDTO con los datos de la zona

        Raises:
            NotFoundError: Si no existe una zona con ese ID
        """
        zona = self.session.query(Zona).filter(Zona.id == zona_id).first()

        if not zona:
            raise NotFoundError(f"No se encontró la zona con ID {zona_id}")

        return ZonaDTO.model_validate(zona)
