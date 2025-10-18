"""
Use Case: Obtener Profesor

Caso de uso para obtener un profesor por ID.
"""

from core.exceptions import NotFoundError
from domain.entities import ProfesorEntity
from domain.repositories import IProfesorRepository
from infrastructure.repositories import SQLAlchemyProfesorRepository
from sqlalchemy.orm import Session

from application.dtos import ProfesorDTO


class ObtenerProfesorUseCase:
    """Caso de uso para obtener un profesor por ID."""

    def __init__(self, session: Session):
        """
        Inicializa el caso de uso.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
        self.repository: IProfesorRepository = SQLAlchemyProfesorRepository(session)

    def execute(self, profesor_id: int) -> ProfesorDTO:
        """
        Ejecuta el caso de uso.

        Args:
            profesor_id: ID del profesor a obtener

        Returns:
            ProfesorDTO con los datos del profesor

        Raises:
            NotFoundError: Si el profesor no existe
        """
        entidad = self.repository.get_by_id(profesor_id)
        if not entidad:
            raise NotFoundError(entity_type="Profesor", entity_id=profesor_id)

        return self._entidad_to_dto(entidad)

    def _entidad_to_dto(self, entidad: ProfesorEntity) -> ProfesorDTO:
        """Convierte una entidad a DTO."""
        return ProfesorDTO(
            id=entidad.id or 0,
            nombre_completo=entidad.nombre_completo,
            email_corporativo=str(entidad.email_corporativo) if entidad.email_corporativo else None,
            horas_contrato=float(entidad.horas_contrato),
            porcentaje_jornada=entidad.porcentaje_jornada,
            turno=entidad.turno.value.value,
            horas_manana=entidad.turno.horas_manana,
            horas_tarde=entidad.turno.horas_tarde,
            es_tutor=entidad.es_tutor,
            fecha_inicio_guardias=entidad.fecha_inicio_guardias,
            fecha_fin_guardias=entidad.fecha_fin_guardias,
            dias_semana_permitidos=entidad.dias_semana_permitidos,
            recreos_permitidos=entidad.recreos_permitidos,
            ajuste_guardias=entidad.ajuste_guardias,
            guardias_esperadas=entidad.guardias_esperadas,
        )
