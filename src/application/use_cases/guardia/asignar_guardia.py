"""
Use Case: Asignar Guardia

Caso de uso para asignar una guardia a un profesor en una zona específica.
"""

from sqlalchemy.orm import Session

from application.dtos import CrearGuardiaDTO, GuardiaDTO
from core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from core.logging import get_logger
from core.observability import with_metrics
from domain.entities import GuardiaEntity, ProfesorEntity, ZonaEntity
from domain.repositories import IGuardiaRepository, IProfesorRepository, IZonaRepository
from infrastructure.repositories import (
    SQLAlchemyGuardiaRepository,
    SQLAlchemyProfesorRepository,
    SQLAlchemyZonaRepository,
)

logger = get_logger(__name__)


class AsignarGuardiaUseCase:
    """
    Caso de uso para asignar una guardia.

    Valida que el profesor pueda hacer la guardia,
    que no haya conflictos, y la asigna.
    """

    def __init__(self, session: Session):
        """
        Inicializa el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para transacciones
        """
        self.session = session
        self.profesor_repo: IProfesorRepository = SQLAlchemyProfesorRepository(session)
        self.zona_repo: IZonaRepository = SQLAlchemyZonaRepository(session)
        self.guardia_repo: IGuardiaRepository = SQLAlchemyGuardiaRepository(session)

    @with_metrics("asignar_guardia")
    def execute(self, dto: CrearGuardiaDTO) -> GuardiaDTO:
        """
        Ejecuta el caso de uso.

        Args:
            dto: DTO con los datos de la guardia a asignar

        Returns:
            GuardiaDTO con la guardia creada

        Raises:
            NotFoundError: Si el profesor o zona no existe
            ValidationError: Si los datos no son válidos
            BusinessLogicError: Si no se puede asignar la guardia
        """
        try:
            # 1. Obtener profesor y zona
            profesor = self.profesor_repo.get_by_id(dto.profesor_id)
            if not profesor:
                raise NotFoundError(entity_type="Profesor", entity_id=dto.profesor_id)

            zona = self.zona_repo.get_by_id(dto.zona_id)
            if not zona:
                raise NotFoundError(entity_type="Zona", entity_id=dto.zona_id)

            # 2. Validar que el profesor pueda hacer la guardia
            puede, razon = profesor.puede_asignar_guardia(
                fecha=dto.fecha,
                turno_recreo=dto.turno,
                numero_recreo=dto.numero_recreo,
                zona_id=dto.zona_id,
            )

            if not puede:
                raise BusinessLogicError(
                    f"No se puede asignar guardia a {profesor.nombre_completo}: {razon}"
                )

            # 3. Verificar que no haya conflicto (profesor ya tiene guardia en ese momento)
            if self.guardia_repo.existe_guardia_profesor_en_momento(
                profesor_id=dto.profesor_id,
                fecha=dto.fecha,
                turno=dto.turno,
                recreo=dto.numero_recreo,
            ):
                raise BusinessLogicError(
                    f"El profesor {profesor.nombre_completo} ya tiene guardia asignada "
                    f"en {dto.fecha} {dto.turno} recreo {dto.numero_recreo}"
                )

            # 4. Verificar capacidad de la zona (obtener guardias actuales)
            guardias_momento = self.guardia_repo.find_by_fecha_turno_recreo(
                fecha=dto.fecha,
                turno=dto.turno,
                recreo=dto.numero_recreo,
            )

            profesores_en_zona = [
                g.profesor_id for g in guardias_momento if g.zona_id == dto.zona_id
            ]

            if not zona.puede_asignar_profesor(len(profesores_en_zona)):
                raise BusinessLogicError(
                    f"La zona {zona.nombre_zona} ya alcanzó su capacidad máxima"
                )

            # 5. Crear entidad de guardia
            guardia_entity = GuardiaEntity(
                id=None,
                profesor_id=dto.profesor_id,
                zona_id=dto.zona_id,
                fecha=dto.fecha,
                turno=dto.turno,
                recreo=dto.numero_recreo,
                es_sustitucion=dto.es_sustitucion,
                profesor_sustituido_id=dto.profesor_sustituido_id,
            )

            # 6. Guardar en repositorio
            guardia_guardada = self.guardia_repo.save(guardia_entity)
            self.session.commit()

            logger.info(
                "Guardia asignada exitosamente",
                guardia_id=guardia_guardada.id,
                profesor_id=dto.profesor_id,
                zona_id=dto.zona_id,
                fecha=dto.fecha,
            )

            # 7. Convertir a DTO de salida
            return self._entidad_to_dto(guardia_guardada, profesor, zona)

        except (NotFoundError, ValidationError, BusinessLogicError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error("Error al asignar guardia", error=str(e))
            raise ValidationError(f"Error al asignar guardia: {e}") from e

    def _entidad_to_dto(
        self,
        entidad: GuardiaEntity,
        profesor: ProfesorEntity,
        zona: ZonaEntity
    ) -> GuardiaDTO:
        """Convierte una entidad a DTO con información adicional."""
        return GuardiaDTO(
            id=entidad.id or 0,
            fecha=entidad.fecha,
            turno=entidad.turno,
            numero_recreo=entidad.recreo,
            profesor_id=entidad.profesor_id,
            zona_id=entidad.zona_id,
            es_sustitucion=entidad.es_sustitucion,
            profesor_sustituido_id=entidad.profesor_sustituido_id,
            profesor_nombre=profesor.nombre_completo,
            zona_nombre=zona.nombre_zona,
        )
