"""
Use Case: Listar Profesores

Caso de uso para listar todos los profesores del sistema.
Con caching para optimizar lecturas frecuentes.
"""

from typing import Union

from sqlalchemy.orm import Session

from application.dtos import ProfesorDTO
from core.observability import with_metrics
from domain.entities import ProfesorEntity
from domain.repositories import IProfesorRepository
from utils.repository_cache import cache_profesores


class ListarProfesoresUseCase:
    """Caso de uso para listar todos los profesores."""

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

    @with_metrics("listar_profesores")
    @cache_profesores(ttl=180)  # Cache por 3 minutos
    def execute(self) -> list[ProfesorDTO]:
        """
        Ejecuta el caso de uso (con caching).

        Returns:
            Lista de ProfesorDTO con todos los profesores
        """
        entidades = self.repository.get_all()
        return [self._entidad_to_dto(e) for e in entidades]

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
