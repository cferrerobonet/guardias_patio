"""
Use Case: Listar todas las zonas.

Permite obtener el listado completo de zonas registradas en el sistema.
Con caching para optimizar lecturas frecuentes.
"""

from typing import List

from sqlalchemy.orm import Session

from application.dtos.zona_dto import ZonaDTO
from core.observability import with_metrics
from infrastructure.database.models import Zona
from utils.repository_cache import cache_zonas


class ListarZonasUseCase:
    """
    Caso de uso para listar todas las zonas.

    Recupera el listado completo de zonas ordenadas por nombre.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("listar_zonas")
    @cache_zonas(ttl=300)  # Cache por 5 minutos
    def execute(self) -> List[ZonaDTO]:
        """
        Ejecutar el listado de zonas (con caching).

        Returns:
            Lista de ZonaDTO con todas las zonas del sistema,
            ordenadas alfabéticamente por nombre
        """
        zonas = self.session.query(Zona).order_by(Zona.nombre_zona).all()

        return [ZonaDTO.model_validate(zona) for zona in zonas]
