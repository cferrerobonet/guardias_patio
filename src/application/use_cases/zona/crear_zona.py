"""
Use Case: Crear una nueva zona.

Permite registrar una nueva zona de recreo en el sistema.
"""

from models.models import Zona
from sqlalchemy.orm import Session
from utils.exceptions import BusinessLogicError
from utils.logger import get_logger

from application.dtos.zona_dto import CrearZonaDTO, ZonaDTO

logger = get_logger(__name__)


class CrearZonaUseCase:
    """
    Caso de uso para crear una nueva zona.

    Valida los datos y crea un nuevo registro de zona en la base de datos.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    def execute(self, data: CrearZonaDTO) -> ZonaDTO:
        """
        Ejecutar la creación de una nueva zona.

        Args:
            data: DTO con los datos de la zona a crear

        Returns:
            ZonaDTO con los datos de la zona creada (incluido su ID)

        Raises:
            BusinessLogicError: Si ya existe una zona con ese nombre
        """
        # Verificar si ya existe una zona con ese nombre
        zona_existente = (
            self.session.query(Zona)
            .filter(Zona.nombre_zona == data.nombre_zona)
            .first()
        )

        if zona_existente:
            raise BusinessLogicError(
                f"Ya existe una zona con el nombre '{data.nombre_zona}'"
            )

        # Crear la nueva zona
        nueva_zona = Zona(
            nombre_zona=data.nombre_zona,
            descripcion=data.descripcion or None,
        )

        try:
            self.session.add(nueva_zona)
            self.session.commit()
            self.session.refresh(nueva_zona)

            logger.info(f"Zona creada: {nueva_zona.nombre_zona} (ID: {nueva_zona.id})")

            return ZonaDTO.model_validate(nueva_zona)

        except Exception as e:
            self.session.rollback()
            raise BusinessLogicError(f"Error al crear la zona: {str(e)}") from e
