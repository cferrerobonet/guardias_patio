"""
Asignador de Guardias v4.0 Híbrido (MEJORADO v4.1)
===================================================

Algoritmo híbrido que combina lo mejor de v2.9 (cobertura) y v3.0 (simplicidad).

PRINCIPIOS DE DISEÑO:
1. COBERTURA PRIMERO: Todo slot debe quedar cubierto (si es matemáticamente posible)
2. EQUIDAD GARANTIZADA: Profesores equivalentes reciben ±1 guardia
3. DETERMINISMO: Mismo input → mismo output (sin aleatoridad)
4. PRIORIDADES CLARAS: Profesores urgentes (fecha_inicio cercana) primero
5. CONSECUTIVIDAD: Guardias de cada profesor en días seguidos (MEJORADO v4.1)
6. PREFERENCIA DE ZONA: Cada profesor en la misma zona siempre que sea posible

MEJORAS v4.1 (Diciembre 2025):
- Scoring mejorado: consecutividad como máxima prioridad
- Bonus fuerte para días consecutivos (distancia=1)
- Penalización progresiva para días lejanos
- Zona preferida como segunda prioridad

FASES DEL ALGORITMO:
- Fase 0: Preparación (slots, cuotas, elegibilidad)
- Fase 1: Pre-asignación urgente (profesores con fecha_inicio)
- Fase 2: Asignación por rondas equitativas
- Fase 3: Completitud forzada (relajación progresiva)
- Fase 4: Validación y métricas

COMPARATIVA:
- v2.9: 7 fases, ~2400 líneas, SA innecesario
- v3.0: 5 pasos, ~923 líneas, sin completitud
- v4.0: 5 fases, ~700 líneas, lo mejor de ambos
- v4.1: + consecutividad + zona como prioridades principales
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Dict, List, Optional, Set, Tuple

from infrastructure.database.models import Ausencia, Configuracion, Guardia, Profesor, Zona
from services.calculador_guardias import (
    _parse_recreos_config,
    calcular_guardias_por_profesor,
    listar_dias_lectivos,
)
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# ESTRUCTURAS DE DATOS
from services._asignador_tipos import ContextoAsignacion, ResultadoGeneracion, Slot  # noqa: F401

# FASE 0: PREPARACIÓN
# =============================================================================


def _generar_recreos_fallback(config: Configuracion) -> List[dict]:
    """
    Genera recreos a partir de los campos de hora si recreos_config está vacío.

    Returns:
        Lista de dicts con id, turno y etiqueta para cada recreo.
    """
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


def _generar_slots(config: Configuracion, session: Session) -> List[Slot]:
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
            # Número de zonas a cubrir en este recreo (default: todas)
            num_zonas_recreo = min(recreo.get("zonas", len(zonas)), len(zonas))

            for i in range(num_zonas_recreo):
                if i >= len(zonas_ids):
                    break
                zona_id = zonas_ids[i]
                zona = zonas_dict[zona_id]

                # Verificar si la zona está activa en esta fecha
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


def _profesor_ausente(session: Session, profesor_id: int, fecha: date) -> bool:
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
    session: Session,
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
        # Formato: {"0": [1,2], "1": [1,2], ...}
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
    session: Session,
) -> Dict[int, int]:
    """
    Pre-calcula cuántos slots puede cubrir cada profesor.

    Útil para detectar profesores bloqueados y redistribuir cuotas.
    """
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
    """
    Redistribuye cuotas de profesores sin elegibilidad entre los demás.
    """
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

    # Redistribuir proporcionalmente
    suma_cuotas_elegibles = sum(ctx.cuotas_ideales[p.id] for p in profesores_elegibles)

    for p in profesores_elegibles:
        proporcion = ctx.cuotas_ideales[p.id] / suma_cuotas_elegibles
        incremento = int(cuotas_perdidas * proporcion)
        ctx.cuotas_ideales[p.id] += incremento

    # Poner cuota 0 a bloqueados
    for p in profesores_bloqueados:
        ctx.cuotas_ideales[p.id] = 0

    logger.warning(
        f"⚠️ {len(profesores_bloqueados)} profesores sin elegibilidad. "
        f"Redistribuidas {cuotas_perdidas} guardias."
    )


# =============================================================================
# FASE 1: PRE-ASIGNACIÓN URGENTE
# =============================================================================


def _calcular_urgencia(profesor: Profesor, config: Configuracion, dias_totales: int) -> float:
    """
    Calcula la urgencia de asignación de un profesor.

    Menor valor = más urgente (se asigna primero).

    Factores:
    1. Profesores con fecha_inicio tienen máxima prioridad
    2. Cuantos menos días disponibles, más urgente
    """
    if not profesor.fecha_inicio_guardias:
        return 10000.0  # Sin urgencia especial

    # Días disponibles desde su fecha_inicio hasta fin de curso
    dias_disponibles = (config.fecha_fin_curso - profesor.fecha_inicio_guardias).days

    if dias_totales > 0:
        proporcion = dias_disponibles / dias_totales
        # Menor proporción = más urgente
        return proporcion * 1000

    return 5000.0


# Nota: El ordenamiento de profesores se hace inline en la fase 1
# para tener acceso a la sesión de BD


# =============================================================================
# FASE 2: ASIGNACIÓN POR RONDAS
# =============================================================================


def _score_slot(
    profesor: Profesor,
    slot: Slot,
    ctx: ContextoAsignacion,
) -> Tuple[int, int, int, int, date, int]:
    """
    Calcula el score de un slot para un profesor.

    Menor valor = mejor slot (se ordenan ASC).

    Criterios (en orden de prioridad) - MEJORADO v4.1:
    1. Consecutividad: días seguidos a la última guardia (MÁXIMA PRIORIDAD)
    2. Zona preferida / consistente
    3. Recreo consistente
    4. Día de semana consistente (menor prioridad)
    5. Fecha cronológica
    6. Recreo (desempate)

    La consecutividad es clave para que cada profesor termine sus guardias
    lo antes posible y tenga períodos libres más largos.
    """
    fecha_base = ctx.ultima_fecha.get(profesor.id)

    # 1. CONSECUTIVIDAD (MÁXIMA PRIORIDAD)
    # Priorizar fechas consecutivas o muy cercanas a la última guardia
    if fecha_base:
        distancia_dias = abs((slot.fecha - fecha_base).days)
        # Bonus fuerte si es día consecutivo
        if distancia_dias == 1:
            consecutividad = 0  # Perfecto: día siguiente
        elif distancia_dias <= 3:
            consecutividad = 1  # Muy cercano
        elif distancia_dias <= 7:
            consecutividad = 2  # Misma semana
        else:
            consecutividad = 3 + (distancia_dias // 7)  # Penalización progresiva
    else:
        # Sin guardias previas, preferir fechas más tempranas
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

    # 4. Día de semana consistente (baja prioridad)
    dia_objetivo = fecha_base.weekday() if fecha_base else None
    dia_match = 0 if dia_objetivo is not None and slot.fecha.weekday() == dia_objetivo else 1

    # Orden de tupla: consecutividad > zona > recreo > día > fecha > recreo_id
    return (consecutividad, zona_match, recreo_match, dia_match, slot.fecha, slot.recreo_id)


def _seleccionar_mejor_slot(
    profesor: Profesor,
    ctx: ContextoAsignacion,
    session: Session,
    ignorar_cuota: bool = False,
) -> Optional[Slot]:
    """
    Selecciona el mejor slot disponible para un profesor.
    """
    slots_elegibles = [
        slot
        for slot in ctx.slots
        if _es_elegible(profesor, slot, ctx, session, ignorar_cuota=ignorar_cuota)
    ]

    if not slots_elegibles:
        return None

    # Ordenar por score (mejor primero)
    slots_elegibles.sort(key=lambda s: _score_slot(profesor, s, ctx))

    return slots_elegibles[0]


def _registrar_asignacion(
    profesor: Profesor,
    slot: Slot,
    ctx: ContextoAsignacion,
) -> None:
    """
    Registra una asignación de guardia actualizando todo el estado.
    """
    # Crear guardia
    guardia = Guardia(
        profesor_id=profesor.id,
        fecha=slot.fecha,
        turno=slot.turno,
        recreo=slot.recreo_id,
        zona_id=slot.zona_id,
        curso_id=ctx.curso_id,
    )
    ctx.calendario.append(guardia)

    # Actualizar estado
    ctx.asignadas[profesor.id] += 1
    ctx.slots_ocupados.add(slot)
    ctx.guardias_por_dia[(profesor.id, slot.fecha)] = True

    # Registrar momento ocupado (NO simultaneidad)
    momento = (profesor.id, slot.fecha, slot.turno, slot.recreo_id)
    ctx.momentos_ocupados.add(momento)

    # Actualizar patrones
    ctx.ultima_zona[profesor.id] = slot.zona_id
    ctx.ultimo_recreo[profesor.id] = slot.recreo_id
    ctx.ultima_fecha[profesor.id] = slot.fecha


def _asignar_por_rondas(
    ctx: ContextoAsignacion,
    profesores_ordenados: List[Profesor],
    session: Session,
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

    Garantiza que TODOS los profesores reciban guardias proporcionalmente
    ANTES de que cualquiera supere su cuota.
    """
    max_cuota = max(ctx.cuotas_ideales.values()) if ctx.cuotas_ideales else 0
    asignaciones_totales = 0

    # Pre-calcular elegibilidad si no se proporcionó
    if matriz_elegibilidad is None:
        matriz_elegibilidad = _calcular_matriz_elegibilidad(ctx, session)

    def calcular_deficit_normalizado(p: Profesor) -> float:
        """
        Calcula déficit normalizado: (cuota - asignadas) / cuota.

        Valor entre 0.0 (cuota alcanzada) y 1.0 (ninguna asignada).
        Esto garantiza equidad entre profesores con distintas cuotas.
        """
        cuota = ctx.cuotas_ideales.get(p.id, 0)
        if cuota == 0:
            return 0.0
        deficit = cuota - ctx.asignadas[p.id]
        return max(0.0, deficit / cuota)

    def calcular_factor_elegibilidad(p: Profesor) -> float:
        """
        Factor de urgencia basado en elegibilidad restante.

        Profesores con menos slots elegibles restantes tienen mayor
        factor (más prioridad) para evitar quedarse sin opciones.
        """
        elegibles = matriz_elegibilidad.get(p.id, 0)
        cuota = ctx.cuotas_ideales.get(p.id, 0)
        asignadas = ctx.asignadas[p.id]
        restantes = cuota - asignadas

        if restantes <= 0:
            return 0.0

        # Ratio elegibles/restantes: menor ratio = más urgente
        if elegibles == 0:
            return 1000.0  # Máxima urgencia
        ratio = elegibles / restantes
        # Invertir: menor ratio -> mayor factor
        return 1.0 / max(ratio, 0.1)

    for ronda in range(1, max_cuota + 1):
        asignaciones_ronda = 0

        # ORDENACIÓN DINÁMICA MEJORADA:
        # 1. Déficit normalizado (principal)
        # 2. Factor de elegibilidad (secundario - prioriza profesores con pocas opciones)
        # 3. Desempate rotativo basado en ronda (evita favorecer siempre los mismos)
        num_profesores = len(profesores_ordenados)
        profesores_por_deficit = sorted(
            profesores_ordenados,
            key=lambda p: (
                -calcular_deficit_normalizado(p),      # Mayor déficit primero
                -calcular_factor_elegibilidad(p),     # Mayor urgencia por elegibilidad
                (p.id + ronda) % num_profesores       # Desempate rotativo
            )
        )

        for profesor in profesores_por_deficit:
            cuota = ctx.cuotas_ideales.get(profesor.id, 0)

            # ¿Ya alcanzó su cuota?
            if ctx.asignadas[profesor.id] >= cuota:
                continue

            # ¿Ya tiene suficientes para esta ronda?
            if ctx.asignadas[profesor.id] >= ronda:
                continue

            # Buscar mejor slot disponible
            slot = _seleccionar_mejor_slot(profesor, ctx, session, ignorar_cuota=False)

            if slot:
                _registrar_asignacion(profesor, slot, ctx)
                asignaciones_ronda += 1
                asignaciones_totales += 1

        if asignaciones_ronda == 0:
            logger.info(f"  Ronda {ronda}: Sin más asignaciones posibles")
            break

        # Reportar progreso cada 5 rondas
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
    session: Session,
    reportar_progreso: Callable[[int, str], None],
) -> Tuple[int, List[Slot]]:
    """
    Garantiza cobertura completa MANTENIENDO EQUIDAD.

    PRINCIPIO: Las guardias extra se distribuyen equitativamente.
    Ningún profesor debe recibir más de 1 guardia extra que otro
    en la misma categoría de jornada.

    Estrategia:
    1. Primero: asignar a profesores que NO han alcanzado su cuota
    2. Segundo: si todos alcanzaron cuota, distribuir extras equitativamente
       (todos suben 1, luego todos suben 2, etc.)
    3. Último recurso: permitir múltiples guardias por día
    """
    slots_sin_cubrir = [s for s in ctx.slots if s not in ctx.slots_ocupados]

    if not slots_sin_cubrir:
        logger.info("✓ 100% cobertura - completitud no necesaria")
        return 0, []

    logger.info(f"  {len(slots_sin_cubrir)} slots pendientes de cobertura")

    asignaciones = 0
    slots_imposibles = []

    # =========================================================================
    # NIVEL 1: Asignar a profesores que NO han alcanzado su cuota
    # =========================================================================
    for slot in list(slots_sin_cubrir):
        if slot in ctx.slots_ocupados:
            continue

        # Buscar profesores elegibles que NO han alcanzado cuota
        candidatos = [
            p for p in ctx.profesores
            if _es_elegible(p, slot, ctx, session, ignorar_cuota=False)
        ]

        if candidatos:
            # Priorizar por déficit (quien más necesita guardias)
            candidatos.sort(
                key=lambda p: ctx.cuotas_ideales.get(p.id, 0) - ctx.asignadas[p.id],
                reverse=True
            )
            _registrar_asignacion(candidatos[0], slot, ctx)
            asignaciones += 1
            slots_sin_cubrir.remove(slot)

    if not slots_sin_cubrir:
        logger.info(f"✓ Completitud nivel 1: {asignaciones} guardias (profesores bajo cuota)")
        return asignaciones, []

    # =========================================================================
    # NIVEL 2: Distribución equitativa de extras (todos +1, luego +2, etc.)
    # =========================================================================
    logger.info(f"  Nivel 2: {len(slots_sin_cubrir)} slots restantes - distribución equitativa")

    # Calcular exceso actual de cada profesor (normalizado por cuota)
    def exceso_actual(p: Profesor) -> float:
        """Exceso absoluto para comparación de niveles."""
        return ctx.asignadas[p.id] - ctx.cuotas_ideales.get(p.id, 0)

    def exceso_normalizado(p: Profesor) -> float:
        """
        Exceso normalizado por cuota para ordenación justa.

        Profesores con menor cuota no deberían absorber más extras proporcionalmente.
        """
        cuota = ctx.cuotas_ideales.get(p.id, 0)
        if cuota == 0:
            return float('inf')  # No asignar a quien no tiene cuota
        exceso = ctx.asignadas[p.id] - cuota
        return exceso / cuota

    max_rondas_extra = 20  # Límite de seguridad

    for ronda_extra in range(max_rondas_extra):
        if not slots_sin_cubrir:
            break

        # En cada ronda, solo asignar a profesores con MENOR exceso
        min_exceso = min(exceso_actual(p) for p in ctx.profesores)

        # Profesores elegibles para esta ronda: los que tienen el menor exceso
        profesores_esta_ronda = [
            p for p in ctx.profesores
            if exceso_actual(p) == min_exceso
        ]

        asignaciones_ronda = 0
        for slot in list(slots_sin_cubrir):
            if slot in ctx.slots_ocupados:
                continue

            # Buscar entre profesores de esta ronda (menor exceso)
            candidatos = [
                p for p in profesores_esta_ronda
                if _es_elegible(p, slot, ctx, session, ignorar_cuota=True)
            ]

            if candidatos:
                # Ordenar por menor exceso NORMALIZADO (equidad proporcional)
                candidatos.sort(key=lambda p: exceso_normalizado(p))
                _registrar_asignacion(candidatos[0], slot, ctx)
                asignaciones += 1
                asignaciones_ronda += 1
                slots_sin_cubrir.remove(slot)

        if asignaciones_ronda == 0:
            # No se pudo asignar en esta ronda, pasar al nivel 3
            break

    if not slots_sin_cubrir:
        logger.info(f"✓ Completitud nivel 2: {asignaciones} guardias (distribución equitativa)")
        return asignaciones, []

    # =========================================================================
    # NIVEL 3: Último recurso - permitir múltiples guardias por día
    # =========================================================================
    logger.warning(f"  Nivel 3: {len(slots_sin_cubrir)} slots - permitiendo múltiples por día")

    for slot in list(slots_sin_cubrir):
        if slot in ctx.slots_ocupados:
            continue

        # Buscar cualquier profesor elegible, priorizando menor exceso
        candidatos = [
            p for p in ctx.profesores
            if _es_elegible(p, slot, ctx, session, ignorar_cuota=True, permitir_multiples_dia=True)
        ]

        if candidatos:
            # Usar exceso normalizado para equidad proporcional
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
    """
    Valida el resultado y calcula métricas.
    """
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

    # Verificar cuotas
    for profesor in ctx.profesores:
        cuota = ctx.cuotas_ideales.get(profesor.id, 0)
        asignadas = ctx.asignadas[profesor.id]

        if asignadas < cuota:
            deficit = cuota - asignadas
            resultado.profesores_con_deficit.append(
                (profesor.id, profesor.nombre_completo, asignadas, cuota)
            )
            if deficit > cuota * 0.15:  # Más del 15% de déficit
                resultado.es_valido = False
                resultado.errores.append(
                    f"{profesor.nombre_completo}: {asignadas}/{cuota} ({deficit} faltantes)"
                )

        elif asignadas > cuota:
            _exceso = asignadas - cuota  # noqa: F841
            resultado.profesores_con_exceso.append(
                (profesor.id, profesor.nombre_completo, asignadas, cuota)
            )

    # Verificar cobertura
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
        for pid, nombre, asig, cuota in resultado.profesores_con_deficit[:10]:
            logger.info(f"    - {nombre}: {asig}/{cuota} (faltan {cuota - asig})")

    if resultado.profesores_con_exceso:
        logger.info("")
        logger.info("  Profesores con exceso:")
        for pid, nombre, asig, cuota in resultado.profesores_con_exceso[:10]:
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
            except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
        session.rollback()
        logger.error(f"Error al guardar guardias: {e}")
        raise
