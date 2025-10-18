"""
Use Case: Obtener Guardias

Caso de uso para obtener guardias con filtros opcionales.
"""

from core.logging import get_logger
from domain.entities import GuardiaEntity
from domain.repositories import IGuardiaRepository, IProfesorRepository, IZonaRepository
from infrastructure.repositories import (
    SQLAlchemyGuardiaRepository,
    SQLAlchemyProfesorRepository,
    SQLAlchemyZonaRepository,
)
from sqlalchemy.orm import Session

from application.dtos import FiltroGuardiasDTO, GuardiaDTO

logger = get_logger(__name__)


class ObtenerGuardiasUseCase:
    """
    Caso de uso para obtener guardias con filtros.

    Permite filtrar por fecha, profesor, zona, turno, etc.
    """

    def __init__(self, session: Session):
        """
        Inicializa el caso de uso.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
        self.guardia_repo: IGuardiaRepository = SQLAlchemyGuardiaRepository(session)
        self.profesor_repo: IProfesorRepository = SQLAlchemyProfesorRepository(session)
        self.zona_repo: IZonaRepository = SQLAlchemyZonaRepository(session)

    def execute(self, filtros: FiltroGuardiasDTO) -> list[GuardiaDTO]:
        """
        Ejecuta el caso de uso.

        Args:
            filtros: DTO con los filtros a aplicar

        Returns:
            Lista de GuardiaDTO que cumplen los filtros
        """
        # 1. Obtener guardias según filtros
        guardias: list[GuardiaEntity] = []

        if filtros.fecha_inicio and filtros.fecha_fin:
            # Filtrar por rango de fechas
            guardias = self.guardia_repo.find_by_rango_fechas(
                fecha_inicio=filtros.fecha_inicio,
                fecha_fin=filtros.fecha_fin
            )
        elif filtros.profesor_id:
            # Filtrar por profesor
            guardias = self.guardia_repo.find_by_profesor(filtros.profesor_id)
        elif filtros.zona_id:
            # Filtrar por zona
            guardias = self.guardia_repo.find_by_zona(filtros.zona_id)
        else:
            # Sin filtros específicos, obtener todas
            guardias = self.guardia_repo.get_all()

        # 2. Aplicar filtros adicionales en memoria
        if filtros.turno:
            guardias = [g for g in guardias if g.turno == filtros.turno]

        if filtros.numero_recreo:
            guardias = [g for g in guardias if g.recreo == filtros.numero_recreo]

        if filtros.solo_sustituciones:
            guardias = [g for g in guardias if g.es_sustitucion]

        # 3. Convertir a DTOs con información adicional
        return [self._entidad_to_dto_con_info(g) for g in guardias]

    def _entidad_to_dto_con_info(self, entidad: GuardiaEntity) -> GuardiaDTO:
        """Convierte una entidad a DTO con información de profesor y zona."""
        # Obtener nombres de profesor y zona
        profesor_nombre = None
        zona_nombre = None

        try:
            profesor = self.profesor_repo.get_by_id(entidad.profesor_id)
            if profesor:
                profesor_nombre = profesor.nombre_completo
        except Exception:
            pass

        try:
            zona = self.zona_repo.get_by_id(entidad.zona_id)
            if zona:
                zona_nombre = zona.nombre_zona
        except Exception:
            pass

        return GuardiaDTO(
            id=entidad.id or 0,
            fecha=entidad.fecha,
            turno=entidad.turno,
            numero_recreo=entidad.recreo,
            profesor_id=entidad.profesor_id,
            zona_id=entidad.zona_id,
            es_sustitucion=entidad.es_sustitucion,
            profesor_sustituido_id=entidad.profesor_sustituido_id,
            profesor_nombre=profesor_nombre,
            zona_nombre=zona_nombre,
        )
