"""
Helpers internos del Asignador v4.0 Híbrido.

Contiene funciones de preparación, elegibilidad, scoring y registro
de asignaciones. Extraído de asignador_guardias_v4_hibrido.py para
reducir tamaño de archivo.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional, Tuple

from infrastructure.database.models import Ausencia, Configuracion, Guardia, Profesor, Zona
from services._asignador_tipos import ContextoAsignacion, Slot
from services.calculador_guardias import _parse_recreos_config, listar_dias_lectivos
from utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# FASE 0: PREPARACIÓN — slots, elegibilidad, cuotas
# =============================================================================


def _generar_recreos_fallback(config: Configuracion) -> List[dict]:
    """Genera recreos a partir de los campos de hora si recreos_config está vacío."""
    recreos = []
    rid = 0

    if config.hora_recreo1_manana:
        rid += 1
        recreos.append({"id": rid, "turno": "mañana", "etiqueta": "R1 Mañana"})
    if config.hora_recreo2_manana:
        rid += 1
        recreos.append({"id": rid, "turno": "mañana", "etiqueta": "R2 Mañana"})
    if config.hora_recreo1_tarde:
        rid += 1
        recreos.append({"id": rid, "turno": "tarde", "etiqueta": "R1 Tarde"})
    if config.hora_recreo2_tarde:
        rid += 1
        recreos.append({"id": rid, "turno": "tarde", "etiqueta": "R2 Tarde"})

    return recreos


def _generar_slots(config: Configuracion, session) -> List[Slot]:
    """
    Genera todos los slots a cubrir considerando:
    - Días lectivos (excluyendo festivos)
    - Recreos configurados (o deducidos de horas)
    - Zonas activas en cada fecha
    - Número de zonas por recreo (campo "zonas" en recreos_config)
    """
    dias_lectivos = listar_dias_lectivos(config)
    zonas = session.query(Zona).all()
    zonas_ids = [z.id for z in zonas]
    zonas_dict = {z.id: z for z in zonas}
    recreos = _parse_recreos_config(config)

    # Fallback: deducir recreos de horas si no hay config JSON
    if not recreos:
        recreos = _generar_recreos_fallback(config)
        if recreos:
            logger.info(f"⚠️ Usando recreos deducidos de horas: {len(recreos)} recreos")

    if not dias_lectivos or not zonas or not recreos:
        logger.warning(
            f"Datos insuficientes: {len(dias_lectivos)} días, "
            f"{len(zonas)} zonas, {len(recreos)} recreos"
        )
        return []

    slots = []
    for dia in dias_lectivos:
        for recreo in recreos:
            num_zonas_recreo = min(recreo.get("zonas", len(zonas)), len(zonas))

            for i in range(num_zonas_recreo):
                if i >= len(zonas_ids):
                    break
                zona_id = zonas_ids[i]
                zona = zonas_dict[zona_id]

                if zona.fecha_inicio and dia < zona.fecha_inicio:
                    continue
                if zona.fecha_fin and dia > zona.fecha_fin:
                    continue

                slots.append(
                    Slot(
                        fecha=dia,
                        turno=recreo.get("turno", "mañana"),
                        recreo_id=int(recreo["id"]),
                        zona_id=zona.id,
                    )
                )

    logger.info(f"✓ {len(slots)} slots generados")
    return slots


def _profesor_ausente(session, profesor_id: int, fecha: date) -> bool:
    """Verifica si un profesor tiene ausencia activa en una fecha."""
    return (
        session.query(Ausencia)
        .filter(
            Ausencia.profesor_id == profesor_id,
            Ausencia.fecha_inicio <= fecha,
            Ausencia.fecha_fin >= fecha,
            Ausencia.activa == True,  # noqa: E712
        )
        .first()
        is not None
    )


def _parse_json_field(value: Optional[str], default: list) -> list:
    """Parsea un campo JSON de forma segura."""
    if not value:
        return default
    try:
        result = json.loads(value)
        return result if isinstance(result, (list, dict)) else default
    except (json.JSONDecodeError, TypeError):
        return default


def _es_elegible(
    profesor: Profesor,
    slot: Slot,
    ctx: ContextoAsignacion,
    session,
    ignorar_cuota: bool = False,
    permitir_multiples_dia: bool = False,
) -> bool:
    """
    Verifica si un profesor puede cubrir un slot.

    Condiciones HARD (nunca se relajan):
    1. Turno compatible
    2. No ausente
    3. Fecha en rango del profesor
    4. Día de semana permitido
    5. Recreo permitido
    6. Slot no ocupado
    7. Una guardia por día (salvo relajación)

    Condiciones SOFT (pueden relajarse):
    8. No exceder cuota
    """
    # 1. TURNO COMPATIBLE
    if profesor.turno and profesor.turno not in ("completo", "mixto", "ambos"):
        if profesor.turno != slot.turno:
            return False

    # 2. NO AUSENTE
    if _profesor_ausente(session, profesor.id, slot.fecha):
        return False

    # 3. FECHA EN RANGO
    if profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias:
        return False
    if profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias:
        return False

    # 4. DÍA DE SEMANA PERMITIDO
    dias_permitidos = _parse_json_field(profesor.dias_semana_permitidos, list(range(7)))
    if isinstance(dias_permitidos, list) and slot.fecha.weekday() not in dias_permitidos:
        return False

    # 5. RECREO PERMITIDO
    recreos_permitidos = _parse_json_field(profesor.recreos_permitidos, [1, 2, 3, 4])
    if isinstance(recreos_permitidos, dict):
        dia_key = str(slot.fecha.weekday())
        recreos_del_dia = recreos_permitidos.get(dia_key, [])
        if slot.recreo_id not in recreos_del_dia:
            return False
    elif isinstance(recreos_permitidos, list):
        if slot.recreo_id not in recreos_permitidos:
            return False

    # 6. SLOT NO OCUPADO
    if slot in ctx.slots_ocupados:
        return False

    # 6b. NO SIMULTANEIDAD (HARD): Un profesor no puede estar en 2 zonas al mismo tiempo
    momento = (profesor.id, slot.fecha, slot.turno, slot.recreo_id)
    if momento in ctx.momentos_ocupados:
        return False

    # 7. UNA GUARDIA POR DÍA
    if not permitir_multiples_dia:
        if (profesor.id, slot.fecha) in ctx.guardias_por_dia:
            return False

    # 8. NO EXCEDER CUOTA (soft)
    if not ignorar_cuota:
        cuota = ctx.cuotas_ideales.get(profesor.id, 0)
        if ctx.asignadas[profesor.id] >= cuota:
            return False

    return True


def _calcular_matriz_elegibilidad(
    ctx: ContextoAsignacion,
    session,
) -> Dict[int, int]:
    """Pre-calcula cuántos slots puede cubrir cada profesor."""
    matriz = defaultdict(int)

    for profesor in ctx.profesores:
        for slot in ctx.slots:
            if _es_elegible(profesor, slot, ctx, session, ignorar_cuota=True):
                matriz[profesor.id] += 1

    return dict(matriz)


def _redistribuir_cuotas_bloqueados(
    ctx: ContextoAsignacion,
    matriz_elegibilidad: Dict[int, int],
) -> None:
    """Redistribuye cuotas de profesores sin elegibilidad entre los demás."""
    profesores_bloqueados = [
        p
        for p in ctx.profesores
        if matriz_elegibilidad.get(p.id, 0) == 0 and ctx.cuotas_ideales.get(p.id, 0) > 0
    ]

    if not profesores_bloqueados:
        return

    cuotas_perdidas = sum(ctx.cuotas_ideales[p.id] for p in profesores_bloqueados)
    profesores_elegibles = [
        p
        for p in ctx.profesores
        if matriz_elegibilidad.get(p.id, 0) > 0 and ctx.cuotas_ideales.get(p.id, 0) > 0
    ]

    if not profesores_elegibles:
        logger.error("⚠️ No hay profesores elegibles para redistribuir cuotas")
        return

    suma_cuotas_elegibles = sum(ctx.cuotas_ideales[p.id] for p in profesores_elegibles)

    for p in profesores_elegibles:
        proporcion = ctx.cuotas_ideales[p.id] / suma_cuotas_elegibles
        incremento = int(cuotas_perdidas * proporcion)
        ctx.cuotas_ideales[p.id] += incremento

    for p in profesores_bloqueados:
        ctx.cuotas_ideales[p.id] = 0

    logger.warning(
        f"⚠️ {len(profesores_bloqueados)} profesores sin elegibilidad. "
        f"Redistribuidas {cuotas_perdidas} guardias."
    )


# =============================================================================
# FASE 1: URGENCIA + FASE 2: SCORING / SELECCIÓN / REGISTRO
# =============================================================================


def _calcular_urgencia(profesor: Profesor, config: Configuracion, dias_totales: int) -> float:
    """
    Calcula la urgencia de asignación de un profesor.

    Menor valor = más urgente (se asigna primero).
    """
    if not profesor.fecha_inicio_guardias:
        return 10000.0

    dias_disponibles = (config.fecha_fin_curso - profesor.fecha_inicio_guardias).days

    if dias_totales > 0:
        proporcion = dias_disponibles / dias_totales
        return proporcion * 1000

    return 5000.0


def _score_slot(
    profesor: Profesor,
    slot: Slot,
    ctx: ContextoAsignacion,
) -> Tuple[int, int, int, int, date, int]:
    """
    Calcula el score de un slot para un profesor.

    Menor valor = mejor slot (se ordenan ASC).

    Criterios (MEJORADO v4.1):
    1. Consecutividad: días seguidos a la última guardia (MÁXIMA PRIORIDAD)
    2. Zona preferida / consistente
    3. Recreo consistente
    4. Día de semana consistente
    5. Fecha cronológica
    6. Recreo (desempate)
    """
    fecha_base = ctx.ultima_fecha.get(profesor.id)

    # 1. CONSECUTIVIDAD
    if fecha_base:
        distancia_dias = abs((slot.fecha - fecha_base).days)
        if distancia_dias == 1:
            consecutividad = 0
        elif distancia_dias <= 3:
            consecutividad = 1
        elif distancia_dias <= 7:
            consecutividad = 2
        else:
            consecutividad = 3 + (distancia_dias // 7)
    else:
        consecutividad = 0
        distancia_dias = 0

    # 2. Zona preferida / consistente
    zona_objetivo = ctx.ultima_zona.get(profesor.id) or getattr(
        profesor, "zona_preferida_id", None
    )
    zona_match = 0 if zona_objetivo and slot.zona_id == zona_objetivo else 1

    # 3. Recreo consistente
    recreo_objetivo = ctx.ultimo_recreo.get(profesor.id)
    recreo_match = 0 if recreo_objetivo and slot.recreo_id == recreo_objetivo else 1

    # 4. Día de semana consistente
    dia_objetivo = fecha_base.weekday() if fecha_base else None
    dia_match = 0 if dia_objetivo is not None and slot.fecha.weekday() == dia_objetivo else 1

    return (consecutividad, zona_match, recreo_match, dia_match, slot.fecha, slot.recreo_id)


def _seleccionar_mejor_slot(
    profesor: Profesor,
    ctx: ContextoAsignacion,
    session,
    ignorar_cuota: bool = False,
) -> Optional[Slot]:
    """Selecciona el mejor slot disponible para un profesor."""
    slots_elegibles = [
        slot
        for slot in ctx.slots
        if _es_elegible(profesor, slot, ctx, session, ignorar_cuota=ignorar_cuota)
    ]

    if not slots_elegibles:
        return None

    slots_elegibles.sort(key=lambda s: _score_slot(profesor, s, ctx))

    return slots_elegibles[0]


def _registrar_asignacion(
    profesor: Profesor,
    slot: Slot,
    ctx: ContextoAsignacion,
) -> None:
    """Registra una asignación de guardia actualizando todo el estado."""
    guardia = Guardia(
        profesor_id=profesor.id,
        fecha=slot.fecha,
        turno=slot.turno,
        recreo=slot.recreo_id,
        zona_id=slot.zona_id,
        curso_id=ctx.curso_id,
    )
    ctx.calendario.append(guardia)

    ctx.asignadas[profesor.id] += 1
    ctx.slots_ocupados.add(slot)
    ctx.guardias_por_dia[(profesor.id, slot.fecha)] = True

    momento = (profesor.id, slot.fecha, slot.turno, slot.recreo_id)
    ctx.momentos_ocupados.add(momento)

    ctx.ultima_zona[profesor.id] = slot.zona_id
    ctx.ultimo_recreo[profesor.id] = slot.recreo_id
    ctx.ultima_fecha[profesor.id] = slot.fecha
