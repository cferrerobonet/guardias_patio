from __future__ import annotations

import copy
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict, List, Optional, Tuple

from models.models import Ausencia, Configuracion, Guardia, Profesor, Zona
from services.calculador_guardias import (
    _parse_recreos_config,
    calcular_guardias_por_profesor,
    listar_dias_lectivos,
)
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


def profesor_ausente(session: Session, profesor_id: int, fecha: date) -> bool:
    """
    Verifica si un profesor está ausente en una fecha específica.

    Args:
        session: Sesión de SQLAlchemy
        profesor_id: ID del profesor a verificar
        fecha: Fecha a verificar

    Returns:
        True si el profesor tiene una ausencia activa en esa fecha, False en caso contrario
    """
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


@dataclass
class Slot:
    fecha: date
    recreo_id: int
    turno: str  # "mañana" | "tarde"
    zona_id: int


def _horario_permitido(
    fecha: date, recreo_id: int, horario_json: Optional[str]
) -> bool:
    """
    Valida si un día+recreo está permitido según la matriz JSON.

    Soporta DOS formatos:
    1. Matriz completa: '{"0": [1, 2], "1": [1, 2], ...}' (día: recreos)
    2. Lista simple: '[1, 2]' (mismos recreos todos los días L-V)

    Si no hay restricciones definidas, permite L-V y todos los recreos.
    """
    if not horario_json:
        # Por defecto: lunes a viernes (0-4), todos los recreos
        return fecha.weekday() < 5

    try:
        import json
        datos = json.loads(horario_json)

        # FORMATO 1: Matriz completa {"0": [1, 2], ...}
        if isinstance(datos, dict):
            dia_str = str(fecha.weekday())

            # Si el día no está en el JSON, no está permitido
            if dia_str not in datos:
                return False

            # Verificar si el recreo está en la lista de recreos del día
            recreos_permitidos = datos[dia_str]
            return recreo_id in recreos_permitidos

        # FORMATO 2: Lista simple [1, 2] - mismos recreos todos los días
        elif isinstance(datos, list):
            # Solo días lectivos (L-V)
            if fecha.weekday() >= 5:
                return False
            # Verificar si el recreo está en la lista
            return recreo_id in datos

        else:
            # Formato desconocido, permitir L-V por defecto
            return fecha.weekday() < 5

    except (json.JSONDecodeError, ValueError, KeyError, TypeError):
        # En caso de error, permitir L-V por defecto
        return fecha.weekday() < 5


def _turno_de_recreo(turno_prof: str, recreo_turno: str) -> bool:
    """Verifica si un profesor puede hacer guardias en un turno de recreo.

    Args:
        turno_prof: Turno del profesor ('completo', 'mañana', 'tarde', 'mixto')
        recreo_turno: Turno del recreo ('mañana' o 'tarde')

    Returns:
        True si el profesor puede hacer guardias en ese turno
    """
    # Profesores de turno completo o mixto pueden hacer guardias en cualquier turno
    if turno_prof in ('completo', 'mixto'):
        return True
    # Profesores de turno específico solo pueden hacer guardias en su turno
    return turno_prof == recreo_turno


def _build_slots(session: Session, config: Configuracion) -> List[Slot]:
    zonas = session.query(Zona).all()
    if not zonas:
        return []

    # Crear diccionario de zonas para acceso rápido
    zonas_dict = {z.id: z for z in zonas}
    zonas_ids = [z.id for z in zonas]

    dias = listar_dias_lectivos(config)
    recreos = _parse_recreos_config(config)
    slots: List[Slot] = []

    if not recreos:
        # Fallback: deducir recreos de horas y construir ids 1..N por turno
        tmp = []
        rid = 0
        if config.hora_recreo1_manana:
            rid += 1
            tmp.append({'id': rid, 'turno': 'mañana'})
        if config.hora_recreo2_manana:
            rid += 1
            tmp.append({'id': rid, 'turno': 'mañana'})
        if config.hora_recreo1_tarde:
            rid += 1
            tmp.append({'id': rid, 'turno': 'tarde'})
        if config.hora_recreo2_tarde:
            rid += 1
            tmp.append({'id': rid, 'turno': 'tarde'})
        recreos = [{**r, 'zonas': len(zonas)} for r in tmp]

    for f in dias:
        for r in recreos:
            for i in range(min(r.get('zonas', 1), len(zonas_ids))):
                zona_id = zonas_ids[i]
                zona = zonas_dict[zona_id]

                # Verificar si la zona está activa en esta fecha
                zona_activa = True
                if zona.fecha_inicio and f < zona.fecha_inicio:
                    zona_activa = False
                if zona.fecha_fin and f > zona.fecha_fin:
                    zona_activa = False

                # Solo crear slot si la zona está activa en esta fecha
                if zona_activa:
                    slots.append(Slot(f, int(r['id']), r.get('turno', 'mañana'), zona_id))

    logger.info(f"Slots creados: {len(slots)} (considerando fechas de zonas)")
    return slots


# Diccionario global para acumular estadísticas de rechazos (diagnóstico)
_rechazos_globales = defaultdict(int)
_total_evaluaciones = 0


def generar_calendario_guardias(
    session: Session,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Tuple[List[Guardia], Dict[int, int]]:
    """
    Genera el calendario de guardias para el curso con algoritmo mejorado.

    IMPORTANTE - Sobre la distribución calculada vs generada:
    =========================================================
    La distribución calculada (mostrada antes de generar) es un OBJETIVO IDEAL
    basado en porcentajes de jornada, turnos y tutoría de cada profesor.

    Sin embargo, este algoritmo usa MÚLTIPLES PASADAS con relajación progresiva
    de restricciones para garantizar que TODOS los slots se cubran. Por tanto:

    - En las primeras pasadas (1-2): se respetan las cuotas calculadas
    - En pasadas posteriores (3-6): se IGNORAN cuotas para cubrir slots vacíos
    - Resultado: algunos profesores pueden recibir MÁS guardias de las calculadas

    ¿Por qué no se respetan las cuotas exactamente?
    - Prioridad #1: Cubrir TODOS los slots (ningún recreo sin guardia)
    - Prioridad #2: Respetar restricciones de elegibilidad (turno, fechas, etc.)
    - Prioridad #3: Distribuir equitativamente (pero secundario a #1 y #2)

    Si los resultados difieren significativamente de la distribución calculada,
    verifica que la configuración de turnos, recreos_permitidos y fechas sea correcta.

    Mejoras implementadas:
    - Múltiples pasadas para cubrir slots vacíos
    - Relajación progresiva de restricciones
    - Redistribución dinámica de cuotas
    - Priorización de zonas preferidas
    - Garantía de al menos una guardia por profesor elegible

    Pasadas del algoritmo:
    1. Asignación normal con restricciones estándar (30-70%)
    2. Extender cuotas +20% para cubrir más slots (70-85%)
    3. IGNORAR cuotas completamente para cubrir vacíos (85-90%)
    4. Optimización por swapping inteligente (90-92%)
    5. Búsqueda exhaustiva con backtracking (92-96%)
    6. Garantizar al menos una guardia por profesor (96-98%)

    Args:
        session: Sesión de SQLAlchemy
        progress_callback: Función opcional para reportar progreso.
                          Recibe (porcentaje, mensaje_detalle)

    Returns:
        Tuple con (lista de guardias, diccionario de asignaciones por profesor)
    """
    global _rechazos_globales, _total_evaluaciones
    _rechazos_globales.clear()
    _total_evaluaciones = 0

    logger.info("Iniciando generación de calendario de guardias (algoritmo mejorado)")

    def reportar_progreso(porcentaje: int, mensaje: str = ""):
        """Helper para reportar progreso de forma segura."""
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except Exception as e:
                logger.warning(f"Error al reportar progreso: {e}")

    reportar_progreso(0, "Validando configuración...")

    config = session.query(Configuracion).first()
    if not config:
        logger.error("No existe configuración del curso")
        raise ValueError("No existe configuración del curso")

    reportar_progreso(5, "Cargando profesores...")

    profesores = session.query(Profesor).all()
    if not profesores:
        logger.error("No hay profesores registrados")
        raise ValueError("No hay profesores registrados")
    logger.info(f"Profesores disponibles: {len(profesores)}")

    reportar_progreso(10, f"{len(profesores)} profesores cargados")

    zonas = session.query(Zona).all()
    if not zonas:
        logger.error("No hay zonas registradas")
        raise ValueError("No hay zonas registradas")
    logger.info(f"Zonas configuradas: {len(zonas)}")

    reportar_progreso(15, f"{len(zonas)} zonas configuradas")
    reportar_progreso(20, "Calculando cuotas de guardias...")

    cuotas_base = calcular_guardias_por_profesor(session)  # {prof_id: total}
    asignadas = defaultdict(int)
    ultimo_por_zona: Dict[int, Optional[int]] = {z.id: None for z in zonas}
    ultimo_recreo_prof: Dict[int, Optional[int]] = defaultdict(lambda: None)
    ultimo_dia_prof: Dict[int, Optional[date]] = defaultdict(lambda: None)
    zona_preferida_prof: Dict[int, Optional[int]] = defaultdict(lambda: None)
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int], bool] = {}
    guardias_por_dia_prof: Dict[Tuple[int, date], bool] = {}

    reportar_progreso(25, "Construyendo slots de guardias...")

    slots = _build_slots(session, config)
    if not slots:
        reportar_progreso(100, "No hay slots para asignar")
        return ([], {})

    total_slots = len(slots)
    reportar_progreso(30, f"{total_slots} slots de guardias creados")

    calendario: List[Guardia] = []
    random.seed(42)

    # Variables para tracking de slots sin cubrir
    slots_sin_cubrir: List[Slot] = []

    # ========== PASADA 1: Asignación Normal (30% - 70%) ==========
    logger.info("Iniciando PASADA 1: Asignación normal con restricciones estándar")
    reportar_progreso(30, "Pasada 1: Asignación normal...")

    progreso_inicial = 30
    progreso_final = 70
    intervalo_reporte = max(1, total_slots // 30)

    for idx, slot in enumerate(slots):
        if idx % intervalo_reporte == 0:
            rango = progreso_final - progreso_inicial
            porcentaje = progreso_inicial + int((idx / total_slots) * rango)
            guardias_asignadas = len(calendario)
            mensaje = f"Pasada 1: {guardias_asignadas}/{total_slots} guardias"
            reportar_progreso(porcentaje, mensaje)

        # Elegibles con todas las restricciones
        elegibles = _obtener_profesores_elegibles(
            profesores, slot, asignadas, cuotas_base,
            guardias_por_slot_prof, guardias_por_dia_prof,
            session, respetar_cuotas=True, permitir_multiples_guardias_dia=False
        )

        if not elegibles:
            slots_sin_cubrir.append(slot)
            continue

        elegido = _seleccionar_mejor_profesor(
            elegibles, slot, asignadas, cuotas_base,
            ultimo_dia_prof, ultimo_recreo_prof, zona_preferida_prof
        )

        _registrar_guardia(
            calendario, elegido, slot, asignadas,
            ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
            zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
        )

    guardias_pasada1 = len(calendario)
    logger.info(f"Pasada 1 completada: {guardias_pasada1}/{total_slots} guardias asignadas")
    logger.info(f"Slots sin cubrir: {len(slots_sin_cubrir)}")

    # ========== PASADA 2: Relajar cuotas (70% - 85%) ==========
    if slots_sin_cubrir:
        logger.info("Iniciando PASADA 2: Permitiendo exceder cuotas moderadamente")
        reportar_progreso(70, f"Pasada 2: {len(slots_sin_cubrir)} slots pendientes...")

        # Permitir exceder cuotas hasta un 20%
        cuotas_extendidas = {pid: int(cuota * 1.2) for pid, cuota in cuotas_base.items()}
        slots_aun_sin_cubrir: List[Slot] = []

        total_p2 = len(slots_sin_cubrir)
        for idx, slot in enumerate(slots_sin_cubrir):
            if idx % max(1, total_p2 // 10) == 0:
                porcentaje = 70 + int((idx / total_p2) * 15)
                reportar_progreso(porcentaje, f"Pasada 2: {len(calendario)}/{total_slots} guardias")

            elegibles = _obtener_profesores_elegibles(
                profesores, slot, asignadas, cuotas_extendidas,
                guardias_por_slot_prof, guardias_por_dia_prof,
                session, respetar_cuotas=True, permitir_multiples_guardias_dia=False
            )

            if not elegibles:
                slots_aun_sin_cubrir.append(slot)
                continue

            elegido = _seleccionar_mejor_profesor(
                elegibles, slot, asignadas, cuotas_extendidas,
                ultimo_dia_prof, ultimo_recreo_prof, zona_preferida_prof
            )

            _registrar_guardia(
                calendario, elegido, slot, asignadas,
                ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
            )

        logger.info(f"Pasada 2 completada: {len(calendario)}/{total_slots} guardias asignadas")
        logger.info(f"Slots aún sin cubrir: {len(slots_aun_sin_cubrir)}")
        slots_sin_cubrir = slots_aun_sin_cubrir

    # ========== PASADA 3: Ignorar zona preferida (85% - 95%) ==========
    if slots_sin_cubrir:
        logger.info("Iniciando PASADA 3: Ignorando cuotas, manteniendo 1 guardia/día")
        reportar_progreso(85, f"Pasada 3: {len(slots_sin_cubrir)} slots críticos...")

        slots_criticos: List[Slot] = []
        total_p3 = len(slots_sin_cubrir)

        for idx, slot in enumerate(slots_sin_cubrir):
            if idx % max(1, total_p3 // 10) == 0:
                porcentaje = 85 + int((idx / total_p3) * 5)
                reportar_progreso(porcentaje, f"Pasada 3: {len(calendario)}/{total_slots} guardias")

            # Ignorar cuotas completamente pero mantener 1 guardia/día
            elegibles = _obtener_profesores_elegibles(
                profesores, slot, asignadas, cuotas_base,
                guardias_por_slot_prof, guardias_por_dia_prof,
                session, respetar_cuotas=False, permitir_multiples_guardias_dia=False
            )

            if not elegibles:
                slots_criticos.append(slot)
                continue

            elegido = _seleccionar_mejor_profesor(
                elegibles, slot, asignadas, cuotas_base,
                ultimo_dia_prof, ultimo_recreo_prof, zona_preferida_prof
            )

            _registrar_guardia(
                calendario, elegido, slot, asignadas,
                ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
            )

        logger.info(f"Pasada 3 completada: {len(calendario)}/{total_slots} guardias asignadas")
        logger.info(f"Slots críticos restantes: {len(slots_criticos)}")
        slots_sin_cubrir = slots_criticos

    # ========== PASADA 4: SWAPPING INTELIGENTE (90% - 92%) ==========
    if slots_sin_cubrir and len(calendario) > 0:
        logger.info("Iniciando PASADA 4: Swapping inteligente de guardias")
        reportar_progreso(90, "Pasada 4: Optimización por swapping...")

        # Intentar intercambios para liberar profesores
        swaps_exitosos = 0
        max_intentos_swap = min(100, len(slots_sin_cubrir) * 10)

        for intento in range(max_intentos_swap):
            if not slots_sin_cubrir:
                break

            # Seleccionar un slot sin cubrir al azar
            slot_objetivo = random.choice(slots_sin_cubrir)

            # Buscar profesores que podrían cubrir este slot pero están ocupados ese día
            candidatos_swap = []
            for p in profesores:
                # Verificar si podría cubrir el slot excepto por la restricción de día
                if not _turno_de_recreo(p.turno, slot_objetivo.turno):
                    continue
                if p.fecha_inicio_guardias and slot_objetivo.fecha < p.fecha_inicio_guardias:
                    continue
                if p.fecha_fin_guardias and slot_objetivo.fecha > p.fecha_fin_guardias:
                    continue
                if profesor_ausente(session, p.id, slot_objetivo.fecha):
                    continue
                # Verificar si ya tiene guardia ese día
                if (p.id, slot_objetivo.fecha) in guardias_por_dia_prof:
                    candidatos_swap.append(p)

            if not candidatos_swap:
                continue

            # Intentar swap con cada candidato
            for profesor_swap in candidatos_swap:
                # Buscar la guardia que tiene ese día
                guardia_a_mover = None
                for g in calendario:
                    if g.profesor_id == profesor_swap.id and g.fecha == slot_objetivo.fecha:
                        guardia_a_mover = g
                        break

                if not guardia_a_mover:
                    continue

                # Buscar otro profesor que pueda tomar la guardia original
                slot_original = Slot(
                    guardia_a_mover.fecha,
                    guardia_a_mover.recreo,
                    guardia_a_mover.turno,
                    guardia_a_mover.zona_id
                )

                # Crear copia temporal de las estructuras de control
                temp_guardias_slot = copy.copy(guardias_por_slot_prof)
                temp_guardias_dia = copy.copy(guardias_por_dia_prof)

                # Liberar el profesor original
                del temp_guardias_slot[(profesor_swap.id, slot_original.fecha, slot_original.turno, slot_original.recreo_id)]
                del temp_guardias_dia[(profesor_swap.id, slot_original.fecha)]

                # Buscar reemplazo para la guardia original
                elegibles_reemplazo = _obtener_profesores_elegibles(
                    profesores, slot_original, asignadas, cuotas_base,
                    temp_guardias_slot, temp_guardias_dia,
                    session, respetar_cuotas=False, permitir_multiples_guardias_dia=False
                )

                # Excluir el profesor que vamos a mover
                elegibles_reemplazo = [p for p in elegibles_reemplazo if p.id != profesor_swap.id]

                if elegibles_reemplazo:
                    # SWAP EXITOSO!
                    # 1. Remover guardia original
                    calendario.remove(guardia_a_mover)

                    # 2. Asignar al profesor swap al slot objetivo
                    _registrar_guardia(
                        calendario, profesor_swap, slot_objetivo, asignadas,
                        ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                        zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                    )

                    # 3. Asignar reemplazo a la guardia original
                    reemplazo = elegibles_reemplazo[0]
                    _registrar_guardia(
                        calendario, reemplazo, slot_original, asignadas,
                        ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                        zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                    )

                    # 4. Marcar slot objetivo como cubierto
                    slots_sin_cubrir.remove(slot_objetivo)
                    swaps_exitosos += 1
                    logger.debug(f"Swap exitoso: {profesor_swap.nombre_completo} liberado para slot objetivo")
                    break

        logger.info(f"Pasada 4 completada: {swaps_exitosos} swaps exitosos")
        logger.info(f"Slots restantes: {len(slots_sin_cubrir)}")

    # ========== PASADA 5: BÚSQUEDA EXHAUSTIVA CON BACKTRACKING (92% - 94%) ==========
    # NOTA: Esta pasada NO permite múltiples guardias/día
    # Solo hace búsqueda más exhaustiva con los profesores disponibles
    if slots_sin_cubrir and len(slots_sin_cubrir) <= 100:
        logger.info(f"Iniciando PASADA 5: Búsqueda exhaustiva para {len(slots_sin_cubrir)} slots")
        reportar_progreso(92, "Pasada 5: Búsqueda exhaustiva...")

        # Intentar con diferentes ordenamientos y estrategias
        slots_finalmente_sin_cubrir = []

        # Intentar múltiples veces con diferentes semillas aleatorias
        for intento in range(3):  # 3 intentos con diferentes ordenamientos
            if not slots_sin_cubrir:
                break

            # Mezclar aleatoriamente para intentar diferentes ordenamientos
            random.seed(42 + intento)
            slots_mezclados = random.sample(slots_sin_cubrir, len(slots_sin_cubrir))

            slots_temp_sin_cubrir = []

            for slot in slots_mezclados:
                # Intentar sin permitir múltiples guardias/día
                elegibles = _obtener_profesores_elegibles(
                    profesores, slot, asignadas, cuotas_base,
                    guardias_por_slot_prof, guardias_por_dia_prof,
                    session, respetar_cuotas=False, permitir_multiples_guardias_dia=False
                )

                if not elegibles:
                    slots_temp_sin_cubrir.append(slot)
                    continue

                # Seleccionar el profesor con menos guardias asignadas
                elegido = min(elegibles, key=lambda p: asignadas[p.id])

                _registrar_guardia(
                    calendario, elegido, slot, asignadas,
                    ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                    zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                )

            slots_sin_cubrir = slots_temp_sin_cubrir

        slots_finalmente_sin_cubrir = slots_sin_cubrir

        logger.info(f"Pasada 5 completada: {len(calendario)}/{total_slots} guardias asignadas")
        logger.info(f"Slots sin cubrir restantes: {len(slots_finalmente_sin_cubrir)}")

        for slot in slots_finalmente_sin_cubrir:
            logger.warning(
                f"Slot sin cubrir: {slot.fecha} - Recreo {slot.recreo_id} "
                f"- Turno {slot.turno} - Zona {slot.zona_id}"
            )

        slots_sin_cubrir = slots_finalmente_sin_cubrir

    # ========== PASADA 6: GARANTIZAR AL MENOS UNA GUARDIA POR PROFESOR (96% - 98%) ==========
    logger.info(
        "Iniciando PASADA 6: Garantizar que todos los profesores elegibles "
        "tengan al menos una guardia"
    )
    reportar_progreso(96, "Pasada 6: Asegurando guardias para todos...")

    # Identificar profesores elegibles que no tienen guardias
    profesores_sin_guardias = []
    for p in profesores:
        # Un profesor es elegible si:
        # 1. Tiene cuota > 0
        # 2. No tiene guardias asignadas todavía
        if cuotas_base.get(p.id, 0) > 0 and asignadas[p.id] == 0:
            profesores_sin_guardias.append(p)

    if profesores_sin_guardias:
        logger.info(
            f"Encontrados {len(profesores_sin_guardias)} profesores "
            "sin guardias asignadas"
        )

        profesores_asignados_en_pasada6 = 0

        for profesor in profesores_sin_guardias:
            # Buscar un slot donde este profesor pueda ser asignado
            slot_encontrado = False

            # Intentar asignar en cualquier guardia existente mediante swap
            for idx, guardia_existente in enumerate(calendario):
                # Crear slot temporal
                slot_temp = Slot(
                    fecha=guardia_existente.fecha,
                    recreo_id=guardia_existente.recreo,
                    turno=guardia_existente.turno,
                    zona_id=guardia_existente.zona_id
                )

                # Verificar si el profesor puede tomar este slot
                elegibles_para_slot = _obtener_profesores_elegibles(
                    [profesor],
                    slot_temp,
                    asignadas,
                    cuotas_base,
                    guardias_por_slot_prof,
                    guardias_por_dia_prof,
                    session,
                    respetar_cuotas=False,
                    permitir_multiples_guardias_dia=False
                )

                if elegibles_para_slot:
                    # El profesor puede tomar este slot
                    # Buscar otro slot donde el profesor actual pueda ir
                    profesor_actual_id = guardia_existente.profesor_id

                    # Buscar otro slot para el profesor actual
                    for idx2, otra_guardia in enumerate(calendario):
                        if idx == idx2:
                            continue

                        slot_alternativo = Slot(
                            fecha=otra_guardia.fecha,
                            recreo_id=otra_guardia.recreo,
                            turno=otra_guardia.turno,
                            zona_id=otra_guardia.zona_id
                        )

                        # Estado temporal para verificar el swap
                        temp_asignadas = asignadas.copy()
                        temp_guardias_slot = guardias_por_slot_prof.copy()
                        temp_guardias_dia = guardias_por_dia_prof.copy()

                        # Liberar el slot del profesor actual
                        key_slot = (
                            profesor_actual_id,
                            guardia_existente.fecha,
                            guardia_existente.turno,
                            guardia_existente.recreo
                        )
                        key_dia = (profesor_actual_id, guardia_existente.fecha)

                        if key_slot in temp_guardias_slot:
                            del temp_guardias_slot[key_slot]
                        if key_dia in temp_guardias_dia:
                            del temp_guardias_dia[key_dia]

                        # Verificar si profesor actual puede ir al slot alternativo
                        profesor_actual = next(
                            (p for p in profesores if p.id == profesor_actual_id),
                            None
                        )
                        if not profesor_actual:
                            continue

                        elegibles_swap = _obtener_profesores_elegibles(
                            [profesor_actual],
                            slot_alternativo,
                            temp_asignadas,
                            cuotas_base,
                            temp_guardias_slot,
                            temp_guardias_dia,
                            session,
                            respetar_cuotas=False,
                            permitir_multiples_guardias_dia=False
                        )

                        if elegibles_swap:
                            # SWAP EXITOSO!
                            logger.info(
                                f"Swap para {profesor.nombre_completo}: "
                                f"{profesor_actual.nombre_completo} movido"
                            )

                            # Actualizar guardia existente
                            guardia_existente.profesor_id = profesor.id

                            # Actualizar contadores
                            asignadas[profesor.id] += 1

                            # Actualizar tracking
                            new_key_slot = (
                                profesor.id,
                                guardia_existente.fecha,
                                guardia_existente.turno,
                                guardia_existente.recreo
                            )
                            new_key_dia = (profesor.id, guardia_existente.fecha)
                            guardias_por_slot_prof[new_key_slot] = True
                            guardias_por_dia_prof[new_key_dia] = True
                            ultimo_dia_prof[profesor.id] = guardia_existente.fecha
                            ultimo_recreo_prof[profesor.id] = guardia_existente.recreo

                            if zona_preferida_prof[profesor.id] is None:
                                zona_preferida_prof[profesor.id] = (
                                    guardia_existente.zona_id
                                )

                            profesores_asignados_en_pasada6 += 1
                            slot_encontrado = True
                            break

                if slot_encontrado:
                    break

            if not slot_encontrado:
                logger.warning(
                    f"No se pudo asignar guardia a {profesor.nombre_completo}"
                )

        logger.info(
            f"Pasada 6: {profesores_asignados_en_pasada6} profesores "
            "sin guardias ahora tienen al menos una"
        )
    else:
        logger.info("Todos los profesores elegibles ya tienen al menos una guardia")

    reportar_progreso(98, f"{len(calendario)}/{total_slots} guardias asignadas")

    cobertura_porcentaje = (len(calendario) / total_slots * 100) if total_slots > 0 else 0
    logger.info(f"Calendario generado: {len(calendario)} guardias de {total_slots} slots")
    logger.info(f"Cobertura: {cobertura_porcentaje:.1f}%")
    logger.info(f"Slots sin cubrir: {len(slots_sin_cubrir)}")

    # Estadísticas de distribución
    profesores_con_guardias = sum(1 for count in asignadas.values() if count > 0)
    profesores_sin_guardias_final = []
    for p in profesores:
        if cuotas_base.get(p.id, 0) > 0 and asignadas[p.id] == 0:
            profesores_sin_guardias_final.append(p.nombre_completo)

    logger.info(f"Profesores con guardias: {profesores_con_guardias}/{len(profesores)}")
    if profesores_sin_guardias_final:
        logger.warning(
            f"Profesores elegibles sin guardias: {', '.join(profesores_sin_guardias_final)}"
        )

    logger.debug(f"Distribución por profesor: {dict(asignadas)}")

    # Resumen de rechazos globales (diagnóstico)
    if _total_evaluaciones > 0:
        logger.info("=" * 80)
        logger.info("RESUMEN DE FILTROS DE ELEGIBILIDAD")
        logger.info(f"Total de evaluaciones profesor-slot: {_total_evaluaciones}")
        logger.info(f"Total de rechazos: {sum(_rechazos_globales.values())}")
        logger.info("-" * 80)
        for razon, count in sorted(_rechazos_globales.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (count / _total_evaluaciones) * 100
            logger.info(f"  {razon:20s}: {count:6d} ({porcentaje:5.1f}%)")
        logger.info("=" * 80)

    reportar_progreso(100, "Calendario completado")

    return (calendario, dict(asignadas))


def _obtener_profesores_elegibles(
    profesores: List[Profesor],
    slot: Slot,
    asignadas: Dict[int, int],
    cuotas: Dict[int, int],
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int], bool],
    guardias_por_dia_prof: Dict[Tuple[int, date], bool],
    session: Session,
    respetar_cuotas: bool = True,
    permitir_multiples_guardias_dia: bool = False
) -> List[Profesor]:
    """
    Obtiene la lista de profesores elegibles para un slot dado.

    Args:
        profesores: Lista de todos los profesores
        slot: Slot a asignar
        asignadas: Diccionario de guardias asignadas por profesor
        cuotas: Diccionario de cuotas por profesor
        guardias_por_slot_prof: Control de guardias por slot
        guardias_por_dia_prof: Control de guardias por día
        session: Sesión de SQLAlchemy
        respetar_cuotas: Si False, ignora las cuotas de guardias
        permitir_multiples_guardias_dia: Si True, permite >1 guardia/día

    Returns:
        Lista de profesores elegibles
    """
    global _rechazos_globales, _total_evaluaciones

    elegibles: List[Profesor] = []

    # DEBUG: Contadores de razones de rechazo
    rechazados = {
        'cuotas': 0,
        'turno': 0,
        'fecha_inicio': 0,
        'fecha_fin': 0,
        'dias_semana': 0,
        'horario': 0,
        'ausencias': 0,
        'slot_ocupado': 0,
        'dia_ocupado': 0
    }

    for p in profesores:
        _total_evaluaciones += 1

        # Validar cuotas (si se debe respetar)
        if respetar_cuotas and asignadas[p.id] >= cuotas.get(p.id, 0):
            rechazados['cuotas'] += 1
            _rechazos_globales['cuotas'] += 1
            continue

        # Validar turno
        if not _turno_de_recreo(p.turno, slot.turno):
            rechazados['turno'] += 1
            _rechazos_globales['turno'] += 1
            continue

        # Validar fecha de inicio
        if p.fecha_inicio_guardias and slot.fecha < p.fecha_inicio_guardias:
            rechazados['fecha_inicio'] += 1
            _rechazos_globales['fecha_inicio'] += 1
            continue

        # Validar fecha de fin
        if p.fecha_fin_guardias and slot.fecha > p.fecha_fin_guardias:
            rechazados['fecha_fin'] += 1
            _rechazos_globales['fecha_fin'] += 1
            continue

        # Validar días de la semana permitidos
        if p.dias_semana_permitidos:
            try:
                dias_permitidos = [int(d.strip()) for d in p.dias_semana_permitidos.split(",")]
                if slot.fecha.weekday() not in dias_permitidos:
                    rechazados['dias_semana'] += 1
                    _rechazos_globales['dias_semana'] += 1
                    continue
            except (ValueError, AttributeError):
                pass

        # Validar matriz de horario
        if not _horario_permitido(slot.fecha, slot.recreo_id, p.recreos_permitidos):
            rechazados['horario'] += 1
            _rechazos_globales['horario'] += 1
            continue

        # Validar ausencias
        if profesor_ausente(session, p.id, slot.fecha):
            rechazados['ausencias'] += 1
            _rechazos_globales['ausencias'] += 1
            continue

        # CRÍTICO: No puede estar en dos zonas al mismo tiempo
        if (p.id, slot.fecha, slot.turno, slot.recreo_id) in guardias_por_slot_prof:
            rechazados['slot_ocupado'] += 1
            _rechazos_globales['slot_ocupado'] += 1
            continue

        # Validar múltiples guardias por día (si se debe respetar)
        if not permitir_multiples_guardias_dia:
            if (p.id, slot.fecha) in guardias_por_dia_prof:
                rechazados['dia_ocupado'] += 1
                _rechazos_globales['dia_ocupado'] += 1
                continue

        elegibles.append(p)

    # DEBUG: Log cuando hay muy pocos elegibles
    if len(elegibles) <= 5:
        logger.debug(
            f"ELEGIBILIDAD BAJA para slot {slot.fecha} {slot.turno} R{slot.recreo_id}: "
            f"{len(elegibles)}/{len(profesores)} elegibles. "
            f"Rechazados: cuotas={rechazados['cuotas']}, turno={rechazados['turno']}, "
            f"fecha_inicio={rechazados['fecha_inicio']}, fecha_fin={rechazados['fecha_fin']}, "
            f"dias_semana={rechazados['dias_semana']}, horario={rechazados['horario']}, "
            f"ausencias={rechazados['ausencias']}, slot_ocupado={rechazados['slot_ocupado']}, "
            f"dia_ocupado={rechazados['dia_ocupado']}"
        )
        if elegibles:
            nombres = [f"{p.nombre_completo} (turno={p.turno})" for p in elegibles]
            logger.debug(f"  → Elegibles: {', '.join(nombres)}")

    return elegibles


def _seleccionar_mejor_profesor(
    elegibles: List[Profesor],
    slot: Slot,
    asignadas: Dict[int, int],
    cuotas: Dict[int, int],
    ultimo_dia_prof: Dict[int, Optional[date]],
    ultimo_recreo_prof: Dict[int, Optional[int]],
    zona_preferida_prof: Dict[int, Optional[int]]
) -> Profesor:
    """
    Selecciona el mejor profesor de entre los elegibles usando scoring.

    Criterios de selección (en orden de importancia):
    1. Zona preferida (mantener consistencia)
    2. Déficit de guardias (equilibrar carga)
    3. Continuidad de días
    4. Mismo recreo anterior
    5. Aleatorio (desempate)

    Args:
        elegibles: Lista de profesores elegibles
        slot: Slot a asignar
        asignadas: Guardias asignadas por profesor
        cuotas: Cuotas por profesor
        ultimo_dia_prof: Último día asignado por profesor
        ultimo_recreo_prof: Último recreo asignado por profesor
        zona_preferida_prof: Zona preferida de cada profesor

    Returns:
        Profesor seleccionado
    """
    def score(p: Profesor) -> Tuple[int, int, int, int, float]:
        # Zona preferida
        if zona_preferida_prof[p.id] is None:
            s_zona = 0
        elif zona_preferida_prof[p.id] == slot.zona_id:
            s_zona = 100
        else:
            s_zona = -50

        # Déficit de guardias
        deficit = cuotas.get(p.id, 0) - asignadas[p.id]

        # Continuidad de días
        s_continuidad = 1 if (
            ultimo_dia_prof[p.id]
            and (slot.fecha - ultimo_dia_prof[p.id]).days == 1
        ) else 0

        # Mismo recreo
        s_recreo = 1 if ultimo_recreo_prof[p.id] == slot.recreo_id else 0

        return (s_zona, deficit, s_continuidad, s_recreo, random.random())

    return sorted(elegibles, key=score, reverse=True)[0]


def _registrar_guardia(
    calendario: List[Guardia],
    profesor: Profesor,
    slot: Slot,
    asignadas: Dict[int, int],
    ultimo_por_zona: Dict[int, Optional[int]],
    ultimo_recreo_prof: Dict[int, Optional[int]],
    ultimo_dia_prof: Dict[int, Optional[date]],
    zona_preferida_prof: Dict[int, Optional[int]],
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int], bool],
    guardias_por_dia_prof: Dict[Tuple[int, date], bool]
) -> None:
    """
    Registra una guardia asignada y actualiza todas las estructuras de control.

    Args:
        calendario: Lista de guardias (se modifica)
        profesor: Profesor asignado
        slot: Slot asignado
        asignadas: Guardias asignadas por profesor (se modifica)
        ultimo_por_zona: Último profesor por zona (se modifica)
        ultimo_recreo_prof: Último recreo por profesor (se modifica)
        ultimo_dia_prof: Último día por profesor (se modifica)
        zona_preferida_prof: Zona preferida por profesor (se modifica)
        guardias_por_slot_prof: Control de guardias por slot (se modifica)
        guardias_por_dia_prof: Control de guardias por día (se modifica)
    """
    calendario.append(
        Guardia(
            profesor_id=profesor.id,
            fecha=slot.fecha,
            turno=slot.turno,
            recreo=slot.recreo_id,
            zona_id=slot.zona_id,
        )
    )
    asignadas[profesor.id] += 1
    ultimo_por_zona[slot.zona_id] = profesor.id
    ultimo_recreo_prof[profesor.id] = slot.recreo_id
    ultimo_dia_prof[profesor.id] = slot.fecha

    # Asignar zona preferida en primera asignación
    if zona_preferida_prof[profesor.id] is None:
        zona_preferida_prof[profesor.id] = slot.zona_id

    # Marcar slot y día como ocupados
    guardias_por_slot_prof[(profesor.id, slot.fecha, slot.turno, slot.recreo_id)] = True
    guardias_por_dia_prof[(profesor.id, slot.fecha)] = True


def guardar_guardias_en_bd(session: Session, calendario: List[Guardia]) -> None:
    if not calendario:
        logger.warning("No hay guardias para guardar en la base de datos")
        return
    logger.info(f"Guardando {len(calendario)} guardias en la base de datos")
    session.bulk_save_objects(calendario)
    session.commit()
    logger.info("Guardias guardadas exitosamente")
