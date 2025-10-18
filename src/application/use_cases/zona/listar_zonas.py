"""
Use Case: Listar todas las zonas.

Permite obtener el listado completo de zonas registradas en el sistema.
"""

from typing import List

from models.models import Zona
from sqlalchemy.orm import Session

from application.dtos.zona_dto import ZonaDTO


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

    def execute(self) -> List[ZonaDTO]:
        """
        Ejecutar el listado de zonas.

        Returns:
            Lista de ZonaDTO con todas las zonas del sistema,
            ordenadas alfabéticamente por nombre
        """
        zonas = self.session.query(Zona).order_by(Zona.nombre_zona).all()

        return [ZonaDTO.model_validate(zona) for zona in zonas]
