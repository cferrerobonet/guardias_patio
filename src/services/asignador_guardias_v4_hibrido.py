"""
Asignador de Guardias v4.0 Híbrido (MEJORADO v4.1)
===================================================

Orquestador principal. La lógica interna está distribuida en:
- `_asignador_tipos.py`   → dataclasses Slot, ContextoAsignacion, ResultadoGeneracion
- `_asignador_v4_helpers.py` → preparación, elegibilidad, scoring, registro
- `_asignador_v4_fases.py`   → rondas, completitud, validación, métricas

Exporta para compatibilidad con importadores externos:
  generar_guardias_v4_hibrido, guardar_guardias_en_bd,
  ContextoAsignacion, Slot, _generar_slots, _es_elegible,
  _parse_json_field, _calcular_matriz_elegibilidad, _calcular_urgencia,
  _asignar_por_rondas, _completitud_forzada
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from infrastructure.database.models import Configuracion, Guardia, Profesor, Zona
from services._asignador_tipos import ContextoAsignacion, ResultadoGeneracion, Slot  # noqa: F401
from services._asignador_v4_fases import (  # noqa: F401
    _asignar_por_rondas,
    _completitud_forzada,
    _log_metricas,
    _validar_resultado,
)
from services._asignador_v4_helpers import (  # noqa: F401
    _calcular_matriz_elegibilidad,
    _calcular_urgencia,
    _es_elegible,
    _generar_recreos_fallback,
    _generar_slots,
    _parse_json_field,
    _profesor_ausente,
    _redistribuir_cuotas_bloqueados,
    _registrar_asignacion,
    _score_slot,
    _seleccionar_mejor_slot,
)
from services.calculador_guardias import (
    _parse_recreos_config,
    calcular_guardias_por_profesor,
    listar_dias_lectivos,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def generar_guardias_v4_hibrido(
    session: Session,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Tuple[List[Guardia], Dict[int, int]]:
    """
    Genera el calendario de guardias con el algoritmo v4.0 Híbrido.

    Combina:
    - Matriz de elegibilidad y redistribución de v2.9
    - Rondas equitativas de v2.9
    - Ordenamiento de slots optimizado de v3.0
    - Completitud forzada con relajación progresiva

    Args:
        session: Sesión de SQLAlchemy
        progress_callback: Callback para reportar progreso (porcentaje, mensaje)

    Returns:
        Tupla (lista de guardias, diccionario profesor_id -> guardias_asignadas)
    """

    def reportar(porcentaje: int, mensaje: str = ""):
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except (ValueError, TypeError, OSError) as e:
                logger.warning(f"Error en callback de progreso: {e}")

    logger.info("=" * 80)
    logger.info("ALGORITMO V4.0 HÍBRIDO - GENERACIÓN DE GUARDIAS")
    logger.info("=" * 80)

    reportar(0, "Iniciando generación...")

    # =========================================================================
    # FASE 0: PREPARACIÓN
    # =========================================================================
    logger.info("")
    logger.info("FASE 0: PREPARACIÓN")
    logger.info("-" * 80)
    reportar(5, "Fase 0: Cargando configuración...")

    # Obtener configuración
    config = session.query(Configuracion).first()
    if not config:
        raise ValueError("No existe configuración del curso")

    # Obtener curso activo
    from services.gestor_cursos import GestorCursos

    curso_activo = GestorCursos.obtener_curso_activo(session)
    curso_id = curso_activo.id if curso_activo else None

    if curso_id:
        logger.info(f"  ✓ Curso activo: {curso_activo.nombre} (ID: {curso_id})")
    else:
        logger.warning("  ⚠️ No hay curso activo")

    # Obtener profesores activos
    reportar(8, "Fase 0: Cargando profesores...")
    profesores = session.query(Profesor).filter(Profesor.activo == True).all()  # noqa: E712
    if not profesores:
        raise ValueError("No hay profesores activos")
    logger.info(f"  ✓ {len(profesores)} profesores activos")

    # Generar slots
    reportar(10, "Fase 0: Generando slots...")
    slots = _generar_slots(config, session)
    if not slots:
        # Mensaje más descriptivo indicando las posibles causas
        zonas = session.query(Zona).all()
        recreos = _parse_recreos_config(config) or _generar_recreos_fallback(config)
        dias = listar_dias_lectivos(config)
        raise ValueError(
            f"No se pudieron generar slots: "
            f"{len(dias)} días, {len(zonas)} zonas, {len(recreos)} recreos. "
            "Verifique que hay zonas y recreos configurados."
        )

    # Calcular cuotas
    reportar(12, "Fase 0: Calculando cuotas...")
    try:
        from services.distribucion_cuotas_service import DistribucionCuotasService

        distribucion_service = DistribucionCuotasService(session)
        cuotas_ideales = distribucion_service.calcular_cuotas(profesores)
        logger.info("  ✓ Cuotas calculadas con DistribucionCuotasService")
    except (ValueError, TypeError, OSError) as e:
        logger.warning(f"  ⚠️ Fallback a calcular_guardias_por_profesor: {e}")
        cuotas_ideales = calcular_guardias_por_profesor(session)

    # Crear contexto
    ctx = ContextoAsignacion(
        profesores=profesores,
        slots=slots,
        cuotas_ideales=cuotas_ideales,
        curso_id=curso_id,
        total_slots=len(slots),
    )

    # Inicializar tracking
    for p in profesores:
        ctx.ultima_zona[p.id] = getattr(p, "zona_preferida_id", None)
        ctx.ultimo_recreo[p.id] = None
        ctx.ultima_fecha[p.id] = None

    # Matriz de elegibilidad
    reportar(15, "Fase 0: Calculando elegibilidad...")
    matriz_elegibilidad = _calcular_matriz_elegibilidad(ctx, session)

    # Redistribuir cuotas de bloqueados
    _redistribuir_cuotas_bloqueados(ctx, matriz_elegibilidad)

    logger.info(f"  ✓ Cuota total: {sum(ctx.cuotas_ideales.values())} guardias")
    reportar(20, "Fase 0: Preparación completada")

    # =========================================================================
    # FASE 1: PRE-ASIGNACIÓN URGENTE
    # =========================================================================
    logger.info("")
    logger.info("FASE 1: PRE-ASIGNACIÓN URGENTE")
    logger.info("-" * 80)
    reportar(20, "Fase 1: Ordenando profesores por urgencia...")

    # Ordenar profesores por prioridad
    profesores_con_cuota = [
        p
        for p in profesores
        if ctx.cuotas_ideales.get(p.id, 0) > 0 and matriz_elegibilidad.get(p.id, 0) > 0
    ]

    # Función auxiliar para urgencia (evitar problema de scope con session)
    dias_totales = len(listar_dias_lectivos(config))

    def clave_prioridad(p: Profesor) -> Tuple[float, int, int]:
        urgencia = _calcular_urgencia(p, config, dias_totales)
        cuota = -ctx.cuotas_ideales.get(p.id, 0)
        return (urgencia, cuota, p.id)

    profesores_ordenados = sorted(profesores_con_cuota, key=clave_prioridad)

    # Log de profesores urgentes
    profesores_urgentes = [p for p in profesores_ordenados if p.fecha_inicio_guardias]
    if profesores_urgentes:
        logger.info(f"  ⚡ {len(profesores_urgentes)} profesores con fecha_inicio (urgentes)")
        for p in profesores_urgentes[:5]:
            logger.info(f"    - {p.nombre_completo}: inicio {p.fecha_inicio_guardias}")

    reportar(25, f"Fase 1: {len(profesores_ordenados)} profesores listos")

    # =========================================================================
    # FASE 2: ASIGNACIÓN POR RONDAS
    # =========================================================================
    logger.info("")
    logger.info("FASE 2: ASIGNACIÓN POR RONDAS EQUITATIVAS")
    logger.info("-" * 80)
    reportar(25, "Fase 2: Iniciando rondas...")

    _asignaciones_rondas = _asignar_por_rondas(
        ctx, profesores_ordenados, session, reportar, matriz_elegibilidad
    )

    cobertura_rondas = len(ctx.calendario) / ctx.total_slots * 100 if ctx.total_slots > 0 else 0
    logger.info(
        f"  Cobertura tras rondas: {cobertura_rondas:.1f}% ({_asignaciones_rondas} guardias)"
    )
    reportar(60, f"Fase 2: {cobertura_rondas:.1f}% cobertura")

    # =========================================================================
    # FASE 3: COMPLETITUD FORZADA
    # =========================================================================
    logger.info("")
    logger.info("FASE 3: COMPLETITUD FORZADA")
    logger.info("-" * 80)
    reportar(60, "Fase 3: Garantizando cobertura completa...")

    asignaciones_completitud, slots_imposibles = _completitud_forzada(ctx, session, reportar)

    cobertura_final = len(ctx.calendario) / ctx.total_slots * 100 if ctx.total_slots > 0 else 0
    logger.info(f"  Cobertura final: {cobertura_final:.1f}%")
    reportar(90, f"Fase 3: {cobertura_final:.1f}% cobertura")

    # =========================================================================
    # FASE 4: VALIDACIÓN
    # =========================================================================
    logger.info("")
    logger.info("FASE 4: VALIDACIÓN Y MÉTRICAS")
    logger.info("-" * 80)
    reportar(90, "Fase 4: Validando resultado...")

    resultado = _validar_resultado(ctx, slots_imposibles)
    _log_metricas(resultado)

    reportar(100, f"✅ Completado: {resultado.cobertura:.1f}% cobertura")

    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ ALGORITMO V4.0 HÍBRIDO COMPLETADO")
    logger.info("=" * 80)

    return (ctx.calendario, dict(ctx.asignadas))


def guardar_guardias_en_bd(session: Session, guardias: List[Guardia]) -> None:
    """
    Guarda las guardias en la base de datos.

    Las guardias ya están añadidas a la sesión durante la generación,
    solo necesitamos hacer commit.
    """
    try:
        for guardia in guardias:
            if guardia not in session:
                session.add(guardia)
        session.commit()
        logger.info(f"✓ {len(guardias)} guardias guardadas en BD")
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Error de base de datos al guardar guardias: {e}")
        raise
