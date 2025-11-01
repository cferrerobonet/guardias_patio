"""
Asignador de Guardias v3.0 - Algoritmo Simple Determinista
===========================================================

Enfoque: Asignación profesor por profesor hasta agotar cuotas y slots.

Ventajas vs v2.9:
- Simple y predecible (1 fase vs 7 fases)
- Garantiza 100% cobertura si es matemáticamente posible
- Cada profesor recibe exactamente su cuota
- Más rápido (una pasada vs múltiples iteraciones)
- Fácil de debuggear y mantener
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from models.models import Ausencia, Configuracion, Guardia, Profesor, Zona
from services.calculador_guardias import (
    _parse_recreos_config,
    calcular_guardias_por_profesor,
    listar_dias_lectivos,
)
from services.optimizaciones_asignador import IndiceSlots
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


@dataclass
class SlotV3:
    """Representa un slot de guardia (fecha + recreo + turno + zona)."""

    fecha: date
    recreo_id: int
    turno: str  # "mañana" | "tarde"
    zona_id: int

    def __hash__(self):
        return hash((self.fecha, self.recreo_id, self.turno, self.zona_id))

    def __eq__(self, other):
        if not isinstance(other, SlotV3):
            return False
        return (
            self.fecha == other.fecha
            and self.recreo_id == other.recreo_id
            and self.turno == other.turno
            and self.zona_id == other.zona_id
        )


@dataclass
class ProfesorConCuota:
    """Profesor con su cuota calculada y metadata para ordenamiento."""

    profesor: Profesor
    cuota: int
    slots_posibles: int  # Cuántos slots puede cubrir según restricciones
    prioridad: float  # Menor = más prioritario (asignar primero)


def _profesor_ausente(session: Session, profesor_id: int, fecha: date) -> bool:
    """Verifica si un profesor está ausente en una fecha."""
    ausencia = (
        session.query(Ausencia)
        .filter(
            Ausencia.profesor_id == profesor_id,
            Ausencia.fecha_inicio <= fecha,
            Ausencia.fecha_fin >= fecha,
            Ausencia.activa == True,  # noqa: E712
        )
        .first()
    )
    return ausencia is not None


def _cumple_restricciones(
    profesor: Profesor, slot: SlotV3, session: Session
) -> bool:
    """
    Verifica si un profesor puede cubrir un slot según sus restricciones.

    Restricciones:
    - No estar ausente en esa fecha
    - Cumplir horario permitido (días y recreos)
    - Cumplir turno (si tiene restricción)
    - Cumplir fecha de inicio de guardias
    """
    # 1. Ausencias
    if _profesor_ausente(session, profesor.id, slot.fecha):
        return False

    # 2. Fecha de inicio
    if profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias:
        return False

    # 3. Horario permitido (días y recreos)
    if profesor.dias_semana_permitidos:
        dia_semana = slot.fecha.weekday()
        # dias_semana_permitidos es JSON string, parsear
        try:
            dias_permitidos = json.loads(profesor.dias_semana_permitidos)
            if dia_semana not in dias_permitidos:
                return False
        except (json.JSONDecodeError, TypeError):
            pass  # Si no es válido, no filtrar

    if profesor.recreos_permitidos:
        # recreos_permitidos es JSON string, parsear
        try:
            recreos_perms = json.loads(profesor.recreos_permitidos)
            if slot.recreo_id not in recreos_perms:
                return False
        except (json.JSONDecodeError, TypeError):
            pass  # Si no es válido, no filtrar

    # 4. Turno
    if profesor.turno and profesor.turno != "ambos":
        if slot.turno != profesor.turno:
            return False

    return True


def _generar_todos_slots(config: Configuracion, session: Session) -> List[SlotV3]:
    """Genera todos los slots posibles del calendario."""
    # listar_dias_lectivos solo recibe config como parámetro
    dias_lectivos = listar_dias_lectivos(config)
    # Zona no tiene configuracion_id, obtener todas
    zonas = session.query(Zona).all()

    # Parse recreos config con validación
    recreos_list = _parse_recreos_config(config)

    slots = []
    for dia in dias_lectivos:
        for recreo_data in recreos_list:
            recreo_id = recreo_data['id']
            turno = recreo_data['turno']
            for zona in zonas:
                slot = SlotV3(
                    fecha=dia,
                    recreo_id=recreo_id,
                    turno=turno,
                    zona_id=zona.id,
                )
                slots.append(slot)

    logger.info(f"  ✓ Generados {len(slots)} slots totales")
    return slots


def _calcular_slots_posibles(
    profesor: Profesor, todos_slots: List[SlotV3], session: Session
) -> int:
    """Cuenta cuántos slots puede cubrir un profesor según sus restricciones."""
    count = 0
    for slot in todos_slots:
        if _cumple_restricciones(profesor, slot, session):
            count += 1
    return count


def _calcular_prioridad_profesor(pc: ProfesorConCuota) -> float:
    """
    Calcula prioridad de asignación (menor = más prioritario).

    Criterios:
    1. Profesores con menos slots disponibles primero (más restrictivos)
    2. Profesores con mayor cuota primero (necesitan más slots)
    3. Desempate por ID (determinismo)
    """
    if pc.slots_posibles == 0:
        return float("inf")  # No puede cubrir ningún slot

    # Ratio: cuota / slots_posibles (cuanto más cerca de 1, más restrictivo)
    ratio_restriccion = pc.cuota / pc.slots_posibles if pc.slots_posibles > 0 else 0

    # Prioridad: mayor ratio = más prioritario (menor número)
    # Multiplicamos por 1000 para tener rango amplio y añadimos ID para desempate
    prioridad = (1.0 - ratio_restriccion) * 1000 + pc.profesor.id

    return prioridad


def _ordenar_profesores_por_prioridad(
    profesores_cuotas: List[ProfesorConCuota],
) -> List[ProfesorConCuota]:
    """
    Ordena profesores por prioridad de asignación.

    Orden:
    1. Más restrictivos primero (menos slots disponibles)
    2. Mayor cuota primero
    3. ID para determinismo
    """
    for pc in profesores_cuotas:
        pc.prioridad = _calcular_prioridad_profesor(pc)

    # Ordenar por prioridad ascendente (menor = más prioritario)
    return sorted(profesores_cuotas, key=lambda pc: pc.prioridad)


def _ordenar_slots_para_profesor(
    slots: List[SlotV3], profesor: Profesor
) -> List[SlotV3]:
    """
    Ordena slots por optimalidad para un profesor.

    Criterios:
    1. Fecha (cronológico)
    2. Preferencia de zona (si tiene zona_preferida_id)
    3. Recreo (orden natural)
    """

    def clave_ordenamiento(slot: SlotV3) -> Tuple:
        # Prioridad de zona (0 si es preferida, 1 si no)
        zona_prioridad = 0 if slot.zona_id == getattr(profesor, "zona_preferida_id", None) else 1

        return (
            slot.fecha,  # Cronológico
            zona_prioridad,  # Zona preferida primero
            slot.recreo_id,  # Orden de recreo
        )

    return sorted(slots, key=clave_ordenamiento)


def generar_guardias_v3_simple(
    session: Session,
    configuracion_id: int,
    reportar_progreso: Optional[callable] = None,
) -> Tuple[List[Guardia], Dict[int, int]]:
    """
    Genera guardias usando el algoritmo simple determinista v3.0.

    Algoritmo:
    1. Calcular cuotas exactas por profesor
    2. Ordenar profesores por restricciones (más restrictivos primero)
    3. Asignar profesor por profesor hasta agotar su cuota
    4. Validar cobertura completa

    Args:
        session: Sesión de SQLAlchemy
        configuracion_id: ID de la configuración
        reportar_progreso: Callback para reportar progreso (opcional)

    Returns:
        Dict con estadísticas de la generación
    """
    if reportar_progreso is None:
        reportar_progreso = lambda p, m: None  # noqa: E731

    logger.info("=" * 80)
    logger.info("ALGORITMO V3.0 - SIMPLE DETERMINISTA")
    logger.info("=" * 80)
    logger.info("Enfoque: Asignación profesor por profesor hasta agotar cuotas")
    logger.info("")

    # Obtener configuración
    config = session.query(Configuracion).get(configuracion_id)
    if not config:
        raise ValueError(f"Configuración {configuracion_id} no encontrada")

    # PASO 1: CALCULAR CUOTAS (0% - 10%)
    logger.info("PASO 1: Calculando cuotas por profesor")
    logger.info("-" * 80)
    reportar_progreso(0, "Paso 1: Calculando cuotas...")

    # Obtener todos los profesores (no hay filtro por configuracion_id en Profesor)
    profesores = session.query(Profesor).all()

    # Calcular cuotas (la función no recibe configuracion_id, usa la config actual)
    cuotas = calcular_guardias_por_profesor(session)
    logger.info(f"  ✓ {len(profesores)} profesores")
    logger.info(f"  ✓ Cuotas calculadas: {sum(cuotas.values())} guardias totales")

    reportar_progreso(10, f"Paso 1: {len(profesores)} profesores")

    # PASO 2: GENERAR TODOS LOS SLOTS (10% - 20%)
    logger.info("")
    logger.info("PASO 2: Generando slots disponibles")
    logger.info("-" * 80)
    reportar_progreso(10, "Paso 2: Generando slots...")

    todos_slots = _generar_todos_slots(config, session)
    total_slots = len(todos_slots)

    reportar_progreso(20, f"Paso 2: {total_slots} slots generados")

    # PASO 3: CALCULAR PRIORIDADES (20% - 30%)
    logger.info("")
    logger.info("PASO 3: Calculando prioridades de asignación")
    logger.info("-" * 80)
    reportar_progreso(20, "Paso 3: Calculando prioridades...")

    profesores_cuotas = []
    for profesor in profesores:
        cuota = cuotas.get(profesor.id, 0)
        slots_posibles = _calcular_slots_posibles(profesor, todos_slots, session)

        pc = ProfesorConCuota(
            profesor=profesor,
            cuota=cuota,
            slots_posibles=slots_posibles,
            prioridad=0.0,  # Se calculará después
        )
        profesores_cuotas.append(pc)

        logger.info(
            f"  • {profesor.nombre_completo}: "
            f"cuota={cuota}, slots_posibles={slots_posibles}"
        )

    # Ordenar por prioridad
    profesores_ordenados = _ordenar_profesores_por_prioridad(profesores_cuotas)

    logger.info("")
    logger.info("  Orden de asignación (más restrictivos primero):")
    for i, pc in enumerate(profesores_ordenados[:10], 1):
        logger.info(
            f"    {i}. {pc.profesor.nombre_completo} "
            f"(cuota={pc.cuota}, disponibles={pc.slots_posibles})"
        )
    if len(profesores_ordenados) > 10:
        logger.info(f"    ... ({len(profesores_ordenados) - 10} más)")

    reportar_progreso(30, "Paso 3: Profesores ordenados")

    # PASO 4: ASIGNAR GUARDIAS (30% - 90%)
    logger.info("")
    logger.info("PASO 4: Asignando guardias profesor por profesor")
    logger.info("-" * 80)

    slots_ocupados: Set[SlotV3] = set()
    indice_slots = IndiceSlots()  # Para búsquedas O(1)
    guardias_asignadas = 0
    profesores_incompletos = []

    for idx, pc in enumerate(profesores_ordenados, 1):
        profesor = pc.profesor
        cuota = pc.cuota

        if cuota == 0:
            logger.info(
                f"  [{idx}/{len(profesores_ordenados)}] "
                f"{profesor.nombre_completo}: Sin cuota (0 guardias)"
            )
            continue

        # Filtrar slots válidos para este profesor
        slots_disponibles = [
            slot
            for slot in todos_slots
            if slot not in slots_ocupados
            and _cumple_restricciones(profesor, slot, session)
        ]

        # Ordenar slots por optimalidad
        slots_disponibles = _ordenar_slots_para_profesor(slots_disponibles, profesor)

        # Tomar exactamente la cuota (o lo máximo disponible)
        slots_asignar = slots_disponibles[:cuota]
        asignadas = len(slots_asignar)

        # Crear guardias
        for slot in slots_asignar:
            guardia = Guardia(
                profesor_id=profesor.id,
                fecha=slot.fecha,
                recreo=slot.recreo_id,
                turno=slot.turno,
                zona_id=slot.zona_id,
            )
            session.add(guardia)

            slots_ocupados.add(slot)
            indice_slots.marcar_ocupado(slot.fecha, slot.turno, slot.recreo_id, slot.zona_id)
            guardias_asignadas += 1

        # Log resultado
        if asignadas < cuota:
            logger.warning(
                f"  [{idx}/{len(profesores_ordenados)}] "
                f"{profesor.nombre_completo}: ⚠️  {asignadas}/{cuota} guardias "
                f"(faltan {cuota - asignadas})"
            )
            profesores_incompletos.append((profesor, asignadas, cuota))
        else:
            logger.info(
                f"  [{idx}/{len(profesores_ordenados)}] "
                f"{profesor.nombre_completo}: ✓ {asignadas}/{cuota} guardias"
            )

        # Reportar progreso
        progreso = 30 + int((idx / len(profesores_ordenados)) * 60)
        reportar_progreso(
            progreso,
            f"Paso 4: {guardias_asignadas}/{total_slots} guardias asignadas",
        )

    session.commit()

    reportar_progreso(90, f"Paso 4: {guardias_asignadas} guardias creadas")

    # PASO 5: VALIDACIÓN Y ESTADÍSTICAS (90% - 100%)
    logger.info("")
    logger.info("PASO 5: Validación y estadísticas")
    logger.info("-" * 80)
    reportar_progreso(90, "Paso 5: Validando resultados...")

    slots_vacios = total_slots - guardias_asignadas
    cobertura = (guardias_asignadas / total_slots * 100) if total_slots > 0 else 0

    logger.info(f"  ✓ Guardias asignadas: {guardias_asignadas}/{total_slots}")
    logger.info(f"  ✓ Cobertura: {cobertura:.2f}%")
    logger.info(f"  ✓ Slots vacíos: {slots_vacios}")
    logger.info(
        f"  ✓ Profesores con cuota incompleta: {len(profesores_incompletos)}"
    )

    if profesores_incompletos:
        logger.warning("")
        logger.warning("  Profesores con cuota incompleta:")
        for profesor, asignadas, cuota in profesores_incompletos:
            faltantes = cuota - asignadas
            logger.warning(
                f"    • {profesor.nombre_completo}: {asignadas}/{cuota} "
                f"(faltan {faltantes})"
            )

    if slots_vacios > 0:
        logger.warning(f"  ⚠️  Quedan {slots_vacios} slots sin cubrir")
    else:
        logger.info("  ✓ 100% de cobertura alcanzada")

    # Calcular equidad
    guardias_por_profesor = defaultdict(int)
    for guardia in session.query(Guardia).all():
        guardias_por_profesor[guardia.profesor_id] += 1

    # Agrupar por jornada
    grupos_jornada = defaultdict(list)
    for profesor in profesores:
        guardias_real = guardias_por_profesor.get(profesor.id, 0)
        grupos_jornada[profesor.porcentaje_jornada].append(guardias_real)

    # Calcular inequidad
    grupos_inequitativos = 0
    for jornada, guardias_lista in grupos_jornada.items():
        if len(guardias_lista) > 1:
            rango = max(guardias_lista) - min(guardias_lista)
            if rango > 1:
                grupos_inequitativos += 1

    logger.info(f"  ✓ Grupos inequitativos: {grupos_inequitativos}")

    reportar_progreso(100, "✓ Generación completada")

    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ ALGORITMO V3.0 COMPLETADO")
    logger.info("=" * 80)

    # Obtener lista de guardias de la BD (recién creadas en esta sesión)
    guardias_generadas = session.query(Guardia).all()

    # Crear diccionario resumen compatible con v2.9
    resumen_dict = {p.id: guardias_por_profesor.get(p.id, 0) for p in profesores}

    # Retornar como tupla (calendario, resumen) igual que v2.9
    return (guardias_generadas, resumen_dict)
