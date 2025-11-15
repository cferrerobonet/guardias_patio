"""
Asignador Guardias V4 - Arquitectura Modular

Función de fachada que usa los nuevos componentes especializados
manteniendo compatibilidad con la interfaz existente.
"""

from typing import Callable, Dict, List, Optional, Tuple

from models.models import Configuracion, Guardia, Profesor
from services.assignment import AssignmentExecutor
from services.estadisticas_service import EstadisticasService
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


def generar_calendario_guardias_v4(
    session: Session,
    configuracion_id: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[List[Guardia], List[str]]:
    """
    Genera calendario de guardias usando arquitectura modular.

    NUEVA ARQUITECTURA (v4):
    ========================
    - SlotBuilder: Construye matriz de slots
    - ProfesorFilter: Filtra profesores elegibles
    - ScoreCalculator: Calcula puntuaciones
    - AssignmentExecutor: Orquesta el proceso

    Beneficios:
    ✅ Single Responsibility Principle
    ✅ Fácil testing de cada componente
    ✅ Código más mantenible
    ✅ Reutilización de componentes

    Args:
        session: Sesión de SQLAlchemy
        configuracion_id: ID de configuración (opcional, usa primera si es None)
        progress_callback: Callback(porcentaje, total, mensaje)

    Returns:
        Tupla (calendario_guardias, incidencias)

    Raises:
        ValueError: Si no hay configuración o profesores
    """
    # Obtener configuración
    if configuracion_id:
        config = session.query(Configuracion).get(configuracion_id)
    else:
        config = session.query(Configuracion).first()

    if not config:
        raise ValueError("No se encontró configuración")

    # Obtener profesores activos
    profesores = (
        session.query(Profesor)
        .filter(Profesor.activo == True)  # noqa: E712
        .all()
    )

    if not profesores:
        raise ValueError("No hay profesores activos")

    logger.info(
        f"Iniciando asignación v4: "
        f"{len(profesores)} profesores, "
        f"periodo {config.fecha_inicio} - {config.fecha_fin}"
    )

    # Ejecutar asignación con componentes modulares
    executor = AssignmentExecutor(session)
    calendario, incidencias = executor.ejecutar_asignacion(
        config=config,
        profesores=profesores,
        progress_callback=progress_callback,
    )

    # Guardar en BD
    if calendario:
        executor.guardar_guardias(calendario)
        session.commit()
        logger.info(f"✅ Asignación completada: {len(calendario)} guardias")
    else:
        logger.error("❌ No se generaron guardias")

    return calendario, incidencias


def calcular_estadisticas_asignacion(
    session: Session, calendario: List[Guardia]
) -> Dict[str, any]:
    """
    Calcula estadísticas de una asignación usando EstadisticasService.

    Args:
        session: Sesión de SQLAlchemy
        calendario: Lista de guardias asignadas

    Returns:
        Dict con métricas completas
    """
    if not calendario:
        return {
            "total_guardias": 0,
            "profesores_participantes": 0,
            "cobertura": 0.0,
        }

    # Usar el servicio centralizado
    stats_service = EstadisticasService(session)

    # Obtener profesores activos
    profesores = (
        session.query(Profesor)
        .filter(Profesor.activo == True)  # noqa: E712
        .all()
    )

    # Generar resumen completo
    resumen = stats_service.generar_resumen_completo(
        guardias=calendario,
        profesores=profesores,
    )

    # Log del resumen
    stats_service.log_resumen(resumen)

    return resumen
