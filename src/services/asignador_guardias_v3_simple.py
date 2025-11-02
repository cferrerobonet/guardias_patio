"""
Asignador de Guardias v3.0 - Algoritmo Simple Determinista
===========================================================

⚠️ IMPORTANTE - DECISIÓN DE ARQUITECTURA:
Este archivo NO es código duplicado. Es un algoritmo alternativo que
coexiste con asignador_guardias.py (v2.9). Los usuarios pueden elegir
qué algoritmo usar mediante el campo 'algoritmo_asignacion' en la
configuración del sistema.

Razón de mantener ambos algoritmos:
- Diferentes estrategias de asignación (simple vs multi-fase)
- Permite comparar resultados y elegir el óptimo
- Backup en caso de problemas con uno u otro
- Flexibilidad para diferentes casos de uso

Enfoque: Asignación profesor por profesor hasta agotar cuotas y slots.

Ventajas vs v2.9:
- Simple y predecible (1 fase vs 7 fases)
- Garantiza 100% cobertura si es matemáticamente posible
- Cada profesor recibe exactamente su cuota
- Más rápido (una pasada vs múltiples iteraciones)
- Fácil de debuggear y mantener

Selección del algoritmo:
- Se configura en: Configuración > algoritmo_asignacion
- Valores posibles: "v2.9" (default) o "v3.0"
- Ver: application/use_cases/asignacion_guardias/generar_guardias.py
"""

from __future__ import annotations

import ast
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

    # 2. Fecha de inicio y fin de guardias
    if profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias:
        return False

    if profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias:
        return False

    # 3. Horario permitido (días y recreos)
    if profesor.dias_semana_permitidos:
        dia_semana = slot.fecha.weekday()
        # dias_semana_permitidos es JSON/Python literal string, parsear de forma segura
        try:
            # Intentar JSON primero
            dias_permitidos = json.loads(profesor.dias_semana_permitidos)
        except (json.JSONDecodeError, TypeError):
            # Si falla JSON, intentar Python literal
            try:
                dias_permitidos = ast.literal_eval(profesor.dias_semana_permitidos)
            except (ValueError, SyntaxError, TypeError):
                # Si todo falla, asumir todos los días permitidos
                dias_permitidos = list(range(7))

        if dia_semana not in dias_permitidos:
            return False

    if profesor.recreos_permitidos:
        # recreos_permitidos puede ser JSON string con lista o diccionario
        try:
            # Intentar JSON primero
            recreos_perms = json.loads(profesor.recreos_permitidos)
        except (json.JSONDecodeError, TypeError):
            # Si falla JSON, intentar Python literal
            try:
                recreos_perms = ast.literal_eval(profesor.recreos_permitidos)
            except (ValueError, SyntaxError, TypeError):
                # Si todo falla, asumir todos los recreos permitidos
                recreos_perms = [1, 2, 3, 4]

        # Manejar dos formatos:
        # 1. Lista: [1, 2] - recreos permitidos todos los días
        # 2. Diccionario por día: {"0": [1, 2], "1": [1, 2], ...}
        if isinstance(recreos_perms, dict):
            # CORREGIDO: Validar recreos específicos del día de la semana
            dia_semana = slot.fecha.weekday()
            dia_key = str(dia_semana)

            if dia_key in recreos_perms:
                recreos_dia = recreos_perms[dia_key]
                if isinstance(recreos_dia, list):
                    if slot.recreo_id not in recreos_dia:
                        return False
                else:
                    # Si no es lista, no permitir (configuración inválida)
                    return False
            else:
                # Si no hay configuración para este día, no permitir
                return False
        elif isinstance(recreos_perms, list):
            # Lista simple: validar recreo permitido
            if slot.recreo_id not in recreos_perms:
                return False

    # 4. Turno
    # Profesores de turno mixto pueden cubrir tanto mañana como tarde
    if profesor.turno and profesor.turno not in ("ambos", "mixto"):
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
    slots: List[SlotV3], profesor: Profesor, guardias_previas: List[SlotV3] = None
) -> List[SlotV3]:
    """
    Ordena slots por optimalidad para un profesor, priorizando patrones consistentes.

    Criterios de ordenamiento (de mayor a menor prioridad):
    1. Misma zona que guardias previas (si existen) o zona preferida
    2. Mismo recreo que guardias previas (si existen)
    3. Mismo día de semana que guardias previas (si existen)
    4. Agrupar fechas cercanas (semanas consecutivas)
    5. Fecha cronológica
    6. Recreo (orden natural)

    Objetivo: Agrupar guardias en patrones consistentes:
    - Mismo día de la semana cada semana (ej: siempre lunes)
    - Misma zona
    - Mismo recreo
    - Fechas consecutivas cuando es posible

    Args:
        slots: Lista de slots disponibles
        profesor: Profesor para quien se ordenan los slots
        guardias_previas: Lista de slots ya asignados a este profesor

    Returns:
        Lista de slots ordenados por optimalidad
    """
    # Inicializar guardias_previas como lista vacía si es None
    if guardias_previas is None:
        guardias_previas = []

    # Analizar patrones de guardias previas
    zonas_previas = [s.zona_id for s in guardias_previas] if guardias_previas else []
    recreos_previos = [s.recreo_id for s in guardias_previas] if guardias_previas else []
    dias_semana_previos = [s.fecha.weekday() for s in guardias_previas] if guardias_previas else []

    # Calcular zona más frecuente (o preferida)
    zona_objetivo = None
    if zonas_previas:
        # Zona más frecuente en guardias previas
        zona_objetivo = max(set(zonas_previas), key=zonas_previas.count)
    elif hasattr(profesor, "zona_preferida_id") and profesor.zona_preferida_id:
        # Zona preferida del profesor
        zona_objetivo = profesor.zona_preferida_id
    else:
        # Si no hay preferencia, usar la zona más frecuente en todos los slots disponibles
        if slots:
            zonas_disponibles = [s.zona_id for s in slots]
            zona_objetivo = max(set(zonas_disponibles), key=zonas_disponibles.count)

    # Calcular recreo más frecuente
    recreo_objetivo = None
    if recreos_previos:
        recreo_objetivo = max(set(recreos_previos), key=recreos_previos.count)
    else:
        # Si no hay guardias previas, usar el primer recreo disponible
        if slots:
            recreos_disponibles = [s.recreo_id for s in slots]
            recreo_objetivo = min(recreos_disponibles)  # Preferir recreos tempranos

    # Calcular día de semana más frecuente
    dia_semana_objetivo = None
    if dias_semana_previos:
        dia_semana_objetivo = max(set(dias_semana_previos), key=dias_semana_previos.count)
    else:
        # Si no hay guardias previas, usar el primer día de semana disponible
        if slots:
            dias_disponibles = [s.fecha.weekday() for s in slots]
            dia_semana_objetivo = min(dias_disponibles)  # Lunes = 0, preferir inicio de semana

    def clave_ordenamiento(slot: SlotV3) -> Tuple:
        """
        Clave de ordenamiento multi-criterio.

        Menores valores = mayor prioridad
        """
        # 1. Prioridad de zona (0 = zona objetivo, 1 = otra zona)
        zona_match = 0 if zona_objetivo and slot.zona_id == zona_objetivo else 1

        # 2. Prioridad de recreo (0 = recreo objetivo, 1 = otro recreo)
        recreo_match = 0 if recreo_objetivo and slot.recreo_id == recreo_objetivo else 1

        # 3. Prioridad de día de semana (0 = día objetivo, 1 = otro día)
        dia_semana_match = (
            0 if dia_semana_objetivo is not None and slot.fecha.weekday() == dia_semana_objetivo
            else 1
        )

        # 4. Fecha (cronológico) - Agrupar por semanas
        # Usamos el número de semana del año para agrupar fechas cercanas
        semana = slot.fecha.isocalendar()[1]

        # 5. Fecha exacta (cronológico)
        fecha = slot.fecha

        # 6. Recreo (orden natural como desempate)
        recreo_id = slot.recreo_id

        return (
            zona_match,          # Prioridad 1: Mantener misma zona
            recreo_match,        # Prioridad 2: Mantener mismo recreo
            dia_semana_match,    # Prioridad 3: Mantener mismo día de semana
            semana,              # Prioridad 4: Agrupar por semanas consecutivas
            fecha,               # Prioridad 5: Cronológico dentro de la semana
            recreo_id,           # Prioridad 6: Desempate por recreo
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

    # PASO 1: VALIDAR Y CARGAR DATOS (0% - 10%)
    logger.info("=" * 80)
    logger.info("GENERANDO GUARDIAS - ALGORITMO V3 SIMPLE")
    logger.info("=" * 80)
    logger.info("")
    logger.info("PASO 1: Cargando configuración y profesores")
    logger.info("-" * 80)
    reportar_progreso(0, "Iniciando generación de guardias...")
    reportar_progreso(2, "Paso 1: Cargando configuración...")

    config = session.query(Configuracion).first()
    if not config:
        raise ValueError("No se encontró configuración activa")

    reportar_progreso(5, "Paso 1: Cargando profesores activos...")
    profesores = session.query(Profesor).filter(Profesor.activo == True).all()  # noqa: E712
    logger.info(f"  ✓ Configuración: {config.fecha_inicio_curso} a {config.fecha_fin_curso}")
    logger.info(f"  ✓ Profesores activos: {len(profesores)}")
    reportar_progreso(7, f"Paso 1: {len(profesores)} profesores cargados")

    reportar_progreso(8, "Paso 1: Calculando cuotas...")
    cuotas = calcular_guardias_por_profesor(session)
    total_cuota = sum(cuotas.values())
    logger.info(f"  ✓ Cuota total a asignar: {total_cuota} guardias")

    reportar_progreso(10, f"Paso 1: Cuota total = {total_cuota} guardias")

    # PASO 2: GENERAR TODOS LOS SLOTS (10% - 20%)
    logger.info("")
    logger.info("PASO 2: Generando slots disponibles")
    logger.info("-" * 80)
    reportar_progreso(10, "Paso 2: Calculando días lectivos...")

    # Obtener información de días y zonas
    dias_lectivos = listar_dias_lectivos(config)
    zonas = session.query(Zona).all()
    recreos_list = _parse_recreos_config(config)

    reportar_progreso(12, f"Paso 2: {len(dias_lectivos)} días lectivos encontrados")
    reportar_progreso(14, f"Paso 2: {len(zonas)} zonas, {len(recreos_list)} recreos")

    todos_slots = _generar_todos_slots(config, session)
    total_slots = len(todos_slots)

    logger.info(f"  ✓ Días lectivos: {len(dias_lectivos)}")
    logger.info(f"  ✓ Zonas: {len(zonas)}")
    logger.info(f"  ✓ Recreos configurados: {len(recreos_list)}")
    logger.info(f"  ✓ Total slots generados: {total_slots}")

    reportar_progreso(20, f"Paso 2: ✓ {total_slots} slots generados")

    # PASO 3: CALCULAR PRIORIDADES (20% - 30%)
    logger.info("")
    logger.info("PASO 3: Calculando prioridades de asignación")
    logger.info("-" * 80)
    reportar_progreso(20, "Paso 3: Analizando restricciones de profesores...")

    profesores_cuotas = []
    procesados = 0
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

        # Reportar progreso cada 5 profesores
        procesados += 1
        if procesados % 5 == 0 or procesados == len(profesores):
            progreso = 20 + int((procesados / len(profesores)) * 8)
            reportar_progreso(
                progreso,
                f"Paso 3: Analizando profesor {procesados}/{len(profesores)}"
            )

    # Ordenar por prioridad
    reportar_progreso(28, "Paso 3: Ordenando profesores por prioridad...")
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

    reportar_progreso(30, "Paso 3: ✓ Profesores ordenados por prioridad")

    # PASO 4: ASIGNAR GUARDIAS (30% - 90%)
    logger.info("")
    logger.info("PASO 4: Asignando guardias profesor por profesor")
    logger.info("-" * 80)
    reportar_progreso(30, "Paso 4: Iniciando asignación de guardias...")

    slots_ocupados: Set[SlotV3] = set()
    indice_slots = IndiceSlots()  # Para búsquedas O(1)
    guardias_asignadas = 0
    profesores_incompletos = []

    # Diccionario para trackear guardias asignadas por profesor
    slots_por_profesor: Dict[int, List[SlotV3]] = {}

    for idx, pc in enumerate(profesores_ordenados, 1):
        profesor = pc.profesor
        cuota = pc.cuota

        if cuota == 0:
            logger.info(
                f"  [{idx}/{len(profesores_ordenados)}] "
                f"{profesor.nombre_completo}: Sin cuota (0 guardias)"
            )
            reportar_progreso(
                30 + int((idx / len(profesores_ordenados)) * 60),
                f"Paso 4: Procesando {idx}/{len(profesores_ordenados)} profesores"
            )
            continue

        # Filtrar slots válidos para este profesor
        slots_disponibles = [
            slot
            for slot in todos_slots
            if slot not in slots_ocupados
            and _cumple_restricciones(profesor, slot, session)
        ]

        # Obtener guardias previas de este profesor (si las hay)
        guardias_previas = slots_por_profesor.get(profesor.id, [])

        # Ordenar slots por optimalidad, considerando guardias previas
        slots_disponibles = _ordenar_slots_para_profesor(
            slots_disponibles, profesor, guardias_previas
        )

        # Tomar exactamente la cuota (o lo máximo disponible)
        slots_asignar = slots_disponibles[:cuota]
        asignadas = len(slots_asignar)

        # Inicializar lista de slots para este profesor si no existe
        if profesor.id not in slots_por_profesor:
            slots_por_profesor[profesor.id] = []

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

            # Trackear slot asignado para este profesor
            slots_por_profesor[profesor.id].append(slot)

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

        # Reportar progreso detallado
        progreso = 30 + int((idx / len(profesores_ordenados)) * 60)
        cobertura_actual = (guardias_asignadas / total_slots * 100) if total_slots > 0 else 0

        # Mensaje más detallado
        mensaje = (
            f"Paso 4: {profesor.nombre_completo[:30]}... → "
            f"{asignadas}/{cuota} guardias | "
            f"Total: {guardias_asignadas}/{total_slots} ({cobertura_actual:.1f}%)"
        )
        reportar_progreso(progreso, mensaje)

    session.commit()

    reportar_progreso(
        90,
        f"Paso 4: ✓ {guardias_asignadas} guardias creadas ({guardias_asignadas}/{total_slots})"
    )

    # PASO 5: VALIDACIÓN Y ESTADÍSTICAS (90% - 100%)
    logger.info("")
    logger.info("PASO 5: Validación y estadísticas")
    logger.info("-" * 80)
    reportar_progreso(90, "Paso 5: Calculando estadísticas finales...")

    slots_vacios = total_slots - guardias_asignadas
    cobertura = (guardias_asignadas / total_slots * 100) if total_slots > 0 else 0

    reportar_progreso(92, f"Paso 5: Cobertura alcanzada: {cobertura:.1f}%")

    logger.info(f"  ✓ Guardias asignadas: {guardias_asignadas}/{total_slots}")
    logger.info(f"  ✓ Cobertura: {cobertura:.2f}%")
    logger.info(f"  ✓ Slots vacíos: {slots_vacios}")
    logger.info(
        f"  ✓ Profesores con cuota incompleta: {len(profesores_incompletos)}"
    )

    reportar_progreso(
        95,
        f"Paso 5: ✓ {len(profesores_incompletos)} profesores con cuota incompleta"
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

    reportar_progreso(98, "Paso 5: Generación completada, finalizando...")
    reportar_progreso(
        100,
        f"✅ Completado: {guardias_asignadas}/{total_slots} guardias ({cobertura:.1f}% cobertura)"
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
