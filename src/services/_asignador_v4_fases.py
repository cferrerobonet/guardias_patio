"""
Fases principales del Asignador v4.0 Híbrido.

Contiene las funciones de las fases 2-4: rondas equitativas,
completitud forzada, validación y métricas.
Extraído de asignador_guardias_v4_hibrido.py para reducir tamaño.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from infrastructure.database.models import Profesor
from services._asignador_tipos import ContextoAsignacion, ResultadoGeneracion, Slot
from services._asignador_v4_helpers import (
    _calcular_matriz_elegibilidad,
    _es_elegible,
    _registrar_asignacion,
    _seleccionar_mejor_slot,
)
from utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# FASE 2: ASIGNACIÓN POR RONDAS
# =============================================================================


def _asignar_por_rondas(
    ctx: ContextoAsignacion,
    profesores_ordenados: List[Profesor],
    session,
    reportar_progreso: Callable[[int, str], None],
    matriz_elegibilidad: Optional[Dict[int, int]] = None,
) -> int:
    """
    Asignación por rondas equitativas con ordenación dinámica mejorada.

    En cada ronda, se intenta dar 1 guardia a cada profesor
    que aún no ha alcanzado su cuota.

    MEJORAS DE EQUIDAD v4.1:
    1. DÉFICIT NORMALIZADO: Usa déficit relativo (deficit/cuota) en lugar de
       absoluto para tratar equitativamente a profesores con distintas cuotas.
    2. DESEMPATE ROTATIVO: El desempate cambia cada ronda para evitar que
       siempre los mismos profesores tengan prioridad ante empates.
    3. FACTOR DE ELEGIBILIDAD: Profesores con menos slots elegibles tienen
       prioridad para que no se queden sin opciones.
    """
    max_cuota = max(ctx.cuotas_ideales.values()) if ctx.cuotas_ideales else 0
    asignaciones_totales = 0

    if matriz_elegibilidad is None:
        matriz_elegibilidad = _calcular_matriz_elegibilidad(ctx, session)

    def calcular_deficit_normalizado(p: Profesor) -> float:
        cuota = ctx.cuotas_ideales.get(p.id, 0)
        if cuota == 0:
            return 0.0
        deficit = cuota - ctx.asignadas[p.id]
        return max(0.0, deficit / cuota)

    def calcular_factor_elegibilidad(p: Profesor) -> float:
        elegibles = matriz_elegibilidad.get(p.id, 0)
        cuota = ctx.cuotas_ideales.get(p.id, 0)
        asignadas = ctx.asignadas[p.id]
        restantes = cuota - asignadas

        if restantes <= 0:
            return 0.0

        if elegibles == 0:
            return 1000.0
        ratio = elegibles / restantes
        return 1.0 / max(ratio, 0.1)

    for ronda in range(1, max_cuota + 1):
        asignaciones_ronda = 0

        num_profesores = len(profesores_ordenados)
        profesores_por_deficit = sorted(
            profesores_ordenados,
            key=lambda p: (
                -calcular_deficit_normalizado(p),
                -calcular_factor_elegibilidad(p),
                (p.id + ronda) % num_profesores,
            ),
        )

        for profesor in profesores_por_deficit:
            cuota = ctx.cuotas_ideales.get(profesor.id, 0)

            if ctx.asignadas[profesor.id] >= cuota:
                continue

            if ctx.asignadas[profesor.id] >= ronda:
                continue

            slot = _seleccionar_mejor_slot(profesor, ctx, session, ignorar_cuota=False)

            if slot:
                _registrar_asignacion(profesor, slot, ctx)
                asignaciones_ronda += 1
                asignaciones_totales += 1

        if asignaciones_ronda == 0:
            logger.info(f"  Ronda {ronda}: Sin más asignaciones posibles")
            break

        if ronda % 5 == 0:
            cobertura = len(ctx.calendario) / ctx.total_slots * 100 if ctx.total_slots > 0 else 0
            progreso = 25 + int((ronda / max_cuota) * 35)
            reportar_progreso(progreso, f"Ronda {ronda}: {cobertura:.1f}% cobertura")

    logger.info(f"✓ {asignaciones_totales} guardias asignadas en rondas equitativas")
    return asignaciones_totales


# =============================================================================
# FASE 3: COMPLETITUD FORZADA CON EQUIDAD
# =============================================================================


def _completitud_forzada(
    ctx: ContextoAsignacion,
    session,
    reportar_progreso: Callable[[int, str], None],
) -> Tuple[int, List[Slot]]:
    """
    Garantiza cobertura completa MANTENIENDO EQUIDAD.

    Estrategia:
    1. Primero: asignar a profesores que NO han alcanzado su cuota
    2. Segundo: distribución equitativa de extras (todos +1, luego +2, etc.)
    3. Último recurso: permitir múltiples guardias por día
    """
    slots_sin_cubrir = [s for s in ctx.slots if s not in ctx.slots_ocupados]

    if not slots_sin_cubrir:
        logger.info("✓ 100% cobertura - completitud no necesaria")
        return 0, []

    logger.info(f"  {len(slots_sin_cubrir)} slots pendientes de cobertura")

    asignaciones = 0
    slots_imposibles = []

    # NIVEL 1: Asignar a profesores que NO han alcanzado su cuota
    for slot in list(slots_sin_cubrir):
        if slot in ctx.slots_ocupados:
            continue

        candidatos = [
            p for p in ctx.profesores
            if _es_elegible(p, slot, ctx, session, ignorar_cuota=False)
        ]

        if candidatos:
            candidatos.sort(
                key=lambda p: ctx.cuotas_ideales.get(p.id, 0) - ctx.asignadas[p.id],
                reverse=True,
            )
            _registrar_asignacion(candidatos[0], slot, ctx)
            asignaciones += 1
            slots_sin_cubrir.remove(slot)

    if not slots_sin_cubrir:
        logger.info(f"✓ Completitud nivel 1: {asignaciones} guardias (profesores bajo cuota)")
        return asignaciones, []

    # NIVEL 2: Distribución equitativa de extras
    logger.info(f"  Nivel 2: {len(slots_sin_cubrir)} slots restantes - distribución equitativa")

    def exceso_actual(p: Profesor) -> float:
        return ctx.asignadas[p.id] - ctx.cuotas_ideales.get(p.id, 0)

    def exceso_normalizado(p: Profesor) -> float:
        cuota = ctx.cuotas_ideales.get(p.id, 0)
        if cuota == 0:
            return float("inf")
        exceso = ctx.asignadas[p.id] - cuota
        return exceso / cuota

    max_rondas_extra = 20

    for _ronda_extra in range(max_rondas_extra):
        if not slots_sin_cubrir:
            break

        min_exceso = min(exceso_actual(p) for p in ctx.profesores)
        profesores_esta_ronda = [
            p for p in ctx.profesores if exceso_actual(p) == min_exceso
        ]

        asignaciones_ronda = 0
        for slot in list(slots_sin_cubrir):
            if slot in ctx.slots_ocupados:
                continue

            candidatos = [
                p for p in profesores_esta_ronda
                if _es_elegible(p, slot, ctx, session, ignorar_cuota=True)
            ]

            if candidatos:
                candidatos.sort(key=lambda p: exceso_normalizado(p))
                _registrar_asignacion(candidatos[0], slot, ctx)
                asignaciones += 1
                asignaciones_ronda += 1
                slots_sin_cubrir.remove(slot)

        if asignaciones_ronda == 0:
            break

    if not slots_sin_cubrir:
        logger.info(f"✓ Completitud nivel 2: {asignaciones} guardias (distribución equitativa)")
        return asignaciones, []

    # NIVEL 3: Último recurso - permitir múltiples guardias por día
    logger.warning(f"  Nivel 3: {len(slots_sin_cubrir)} slots - permitiendo múltiples por día")

    for slot in list(slots_sin_cubrir):
        if slot in ctx.slots_ocupados:
            continue

        candidatos = [
            p for p in ctx.profesores
            if _es_elegible(p, slot, ctx, session, ignorar_cuota=True, permitir_multiples_dia=True)
        ]

        if candidatos:
            candidatos.sort(key=lambda p: exceso_normalizado(p))
            profesor = candidatos[0]
            _registrar_asignacion(profesor, slot, ctx)
            asignaciones += 1
            slots_sin_cubrir.remove(slot)
            logger.warning(
                f"  ⚠️ {profesor.nombre_completo} asignado con múltiple guardia el {slot.fecha}"
            )
        else:
            slots_imposibles.append(slot)

    if slots_imposibles:
        logger.error(f"❌ {len(slots_imposibles)} slots sin cobertura posible:")
        for s in slots_imposibles[:5]:
            logger.error(f"    - {s.fecha} {s.turno} R{s.recreo_id} Z{s.zona_id}")

    logger.info(f"✓ Completitud total: {asignaciones} guardias adicionales")
    return asignaciones, slots_imposibles


# =============================================================================
# FASE 4: VALIDACIÓN Y MÉTRICAS
# =============================================================================


def _validar_resultado(
    ctx: ContextoAsignacion,
    slots_imposibles: List[Slot],
) -> ResultadoGeneracion:
    """Valida el resultado y calcula métricas."""
    resultado = ResultadoGeneracion(
        guardias=ctx.calendario,
        resumen_por_profesor=dict(ctx.asignadas),
        total_slots=ctx.total_slots,
        slots_cubiertos=len(ctx.calendario),
        slots_sin_cubrir=len(slots_imposibles),
    )

    resultado.cobertura = (
        resultado.slots_cubiertos / resultado.total_slots * 100 if resultado.total_slots > 0 else 0
    )

    for profesor in ctx.profesores:
        cuota = ctx.cuotas_ideales.get(profesor.id, 0)
        asignadas = ctx.asignadas[profesor.id]

        if asignadas < cuota:
            deficit = cuota - asignadas
            resultado.profesores_con_deficit.append(
                (profesor.id, profesor.nombre_completo, asignadas, cuota)
            )
            if deficit > cuota * 0.15:
                resultado.es_valido = False
                resultado.errores.append(
                    f"{profesor.nombre_completo}: {asignadas}/{cuota} ({deficit} faltantes)"
                )

        elif asignadas > cuota:
            resultado.profesores_con_exceso.append(
                (profesor.id, profesor.nombre_completo, asignadas, cuota)
            )

    if resultado.cobertura < 100:
        resultado.es_valido = False
        resultado.errores.append(
            f"Cobertura incompleta: {resultado.cobertura:.1f}% ({resultado.slots_sin_cubrir} slots)"
        )

    return resultado


def _log_metricas(resultado: ResultadoGeneracion) -> None:
    """Muestra las métricas del resultado."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("MÉTRICAS DE GENERACIÓN v4.0 HÍBRIDO")
    logger.info("=" * 80)
    cobertura = resultado.cobertura
    cubiertos = resultado.slots_cubiertos
    total = resultado.total_slots
    logger.info(f"  Cobertura: {cobertura:.1f}% ({cubiertos}/{total})")
    logger.info(f"  Slots sin cubrir: {resultado.slots_sin_cubrir}")
    logger.info(f"  Profesores con déficit: {len(resultado.profesores_con_deficit)}")
    logger.info(f"  Profesores con exceso: {len(resultado.profesores_con_exceso)}")

    if resultado.profesores_con_deficit:
        logger.info("")
        logger.info("  Profesores con déficit:")
        for _pid, nombre, asig, cuota in resultado.profesores_con_deficit[:10]:
            logger.info(f"    - {nombre}: {asig}/{cuota} (faltan {cuota - asig})")

    if resultado.profesores_con_exceso:
        logger.info("")
        logger.info("  Profesores con exceso:")
        for _pid, nombre, asig, cuota in resultado.profesores_con_exceso[:10]:
            logger.info(f"    - {nombre}: {asig}/{cuota} (sobran {asig - cuota})")

    if resultado.es_valido:
        logger.info("")
        logger.info("✅ RESULTADO VÁLIDO")
    else:
        logger.warning("")
        logger.warning("⚠️ RESULTADO CON PROBLEMAS:")
        for error in resultado.errores:
            logger.warning(f"    - {error}")

    logger.info("=" * 80)
