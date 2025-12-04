"""
Use Case: Obtener Profesor

Caso de uso para obtener un profesor por ID.
Con caching para optimizar lecturas frecuentes.
"""

from typing import Union

from core.exceptions import NotFoundError
from core.observability import with_metrics
from domain.entities import ProfesorEntity
from domain.repositories import IProfesorRepository
from sqlalchemy.orm import Session
from utils.repository_cache import cache_profesores

from application.dtos import ProfesorDTO


class ObtenerProfesorUseCase:
    """Caso de uso para obtener un profesor por ID."""

    def __init__(self, repository_or_session: Union[IProfesorRepository, Session]):
        """
        Inicializa el caso de uso.

        Args:
            repository_or_session: Repositorio de profesores o Session (legacy)
        """
        if isinstance(repository_or_session, Session):
            # Compatibilidad hacia atrás: crear repositorio internamente
            from infrastructure.repositories import SQLAlchemyProfesorRepository

            self.repository: IProfesorRepository = SQLAlchemyProfesorRepository(
                repository_or_session
            )
        else:
            # Nueva forma: inyección de dependencias
            self.repository = repository_or_session

    @with_metrics("obtener_profesor")
    @cache_profesores(ttl=180)  # Cache por 3 minutos
    def execute(self, profesor_id: int) -> ProfesorDTO:
        """
        Ejecuta el caso de uso (con caching).

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
            tutor=entidad.es_tutor,  # Entidad usa 'es_tutor', DTO usa 'tutor'
            fecha_inicio_guardias=entidad.fecha_inicio_guardias,
            fecha_fin_guardias=entidad.fecha_fin_guardias,
            dias_semana_permitidos=entidad.dias_semana_permitidos,
            recreos_permitidos=entidad.recreos_permitidos,
            ajuste_guardias=entidad.ajuste_guardias,
            guardias_esperadas=entidad.guardias_esperadas,
        )
