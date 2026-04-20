"""
Use Case: Crear Profesor

Caso de uso para crear un nuevo profesor en el sistema.
Invalida cache de profesores tras crear.
"""

from typing import Optional, Union

from core.exceptions import ValidationError
from core.logging import get_logger
from core.observability import with_metrics
from core.observability import business_metrics
from domain.entities import ProfesorEntity
from domain.repositories import IProfesorRepository
from domain.value_objects import Email, HorasContrato, Turno, ZonaPreferida
from sqlalchemy.orm import Session
from utils.repository_cache import invalidate_profesores_cache

from application.dtos import CrearProfesorDTO, ProfesorDTO

logger = get_logger(__name__)


class CrearProfesorUseCase:
    """
    Caso de uso para crear un nuevo profesor.

    Valida los datos de entrada, crea la entidad de dominio,
    y la persiste en la base de datos.
    """

    def __init__(
        self,
        session_or_repo: Union[Session, IProfesorRepository],
        repository: Optional[IProfesorRepository] = None,
        mapper=None,
    ):
        """
        Inicializa el caso de uso.

        Args:
            session_or_repo: Session (legacy) o IProfesorRepository (nueva forma)
            repository: Repositorio (si se pasa session como primer param)
            mapper: Mapper opcional (no se usa actualmente)
        """
        if isinstance(session_or_repo, Session):
            self.session = session_or_repo
            if repository is not None:
                # Nueva forma con inyección
                self.repository: IProfesorRepository = repository
            else:
                # Compatibilidad hacia atrás
                from infrastructure.repositories import SQLAlchemyProfesorRepository

                self.repository = SQLAlchemyProfesorRepository(session_or_repo)
        else:
            # session_or_repo es un repositorio directamente
            self.repository = session_or_repo
            self.session = None  # No disponible en este modo
        self.mapper = mapper

    def execute(self, dto: CrearProfesorDTO) -> ProfesorDTO:
        """
        Ejecuta el caso de uso.

        Args:
            dto: DTO con los datos del profesor a crear

        Returns:
            ProfesorDTO con el profesor creado

        Raises:
            ValidationError: Si los datos no son válidos
        """
        return self._execute_with_metrics(dto)

    @with_metrics("crear_profesor")
    def _execute_with_metrics(self, dto: CrearProfesorDTO) -> ProfesorDTO:
        """Ejecuta la lógica con métricas."""
        try:
            # 1. Validar que el nombre no esté duplicado
            profesor_existente = self.repository.find_by_nombre(dto.nombre_completo)
            if profesor_existente:
                raise ValidationError(
                    f"Ya existe un profesor con el nombre '{dto.nombre_completo}'"
                )

            # 2. Crear Value Objects
            email = Email.from_optional(dto.email_corporativo) if dto.email_corporativo else None
            horas = HorasContrato(dto.horas_contrato)
            turno = Turno.from_string(dto.turno, dto.horas_manana, dto.horas_tarde)

            # 3. Zona preferida - crear desde ID si se proporciona
            zona_preferida = ZonaPreferida.sin_preferencia()
            if dto.zona_preferida_id:
                zona_preferida = ZonaPreferida.from_id(dto.zona_preferida_id)

            # 3. Crear entidad de dominio
            entidad = ProfesorEntity(
                id=None,
                nombre_completo=dto.nombre_completo,
                email_corporativo=email,
                horas_contrato=horas,
                porcentaje_jornada=horas.porcentaje_jornada(),
                turno=turno,
                es_tutor=dto.tutor,  # DTO usa 'tutor', entidad usa 'es_tutor'
                fecha_inicio_guardias=dto.fecha_inicio_guardias,
                fecha_fin_guardias=dto.fecha_fin_guardias,
                zona_preferida=zona_preferida,
                dias_semana_permitidos=dto.dias_semana_permitidos,
                recreos_permitidos=dto.recreos_permitidos,
            )

            # 7. Guardar en repositorio
            entidad_guardada = self.repository.save(entidad)

            # 4. Guardar en repositorio
            entidad_guardada = self.repository.save(entidad)

            # 5. Invalidar cache de profesores
            invalidate_profesores_cache()

            logger.info(
                "Profesor creado exitosamente",
                profesor_id=entidad_guardada.id,
                nombre=entidad_guardada.nombre_completo,
            )
            business_metrics.profesor_creado(
                profesor_id=entidad_guardada.id or 0,
                nombre=entidad_guardada.nombre_completo,
                turno=entidad_guardada.turno.value.value,
                horas_contrato=float(entidad_guardada.horas_contrato),
            )

            # 6. Convertir a DTO de salida
            return self._entidad_to_dto(entidad_guardada)

        except ValidationError:
            self.session.rollback()
            raise
        except (ValueError, TypeError, OSError) as e:
            self.session.rollback()
            logger.error("Error al crear profesor", error=str(e))
            raise ValidationError(f"Error al crear profesor: {e}") from e
        except Exception as e:
            self.session.rollback()
            logger.error("Error inesperado al crear profesor", error=str(e))
            raise ValidationError(f"Error al crear profesor: {e}") from e

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
            zona_preferida_id=entidad.zona_preferida.zona_id
            if entidad.zona_preferida.tiene_preferencia
            else None,
            dias_semana_permitidos=entidad.dias_semana_permitidos,
            recreos_permitidos=entidad.recreos_permitidos,
            ajuste_guardias=entidad.ajuste_guardias,
            guardias_esperadas=entidad.guardias_esperadas,
        )
