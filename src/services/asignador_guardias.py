from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

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
    Formato esperado: '{"0": [1, 2], "2": [1, 3, 4]}'
    donde clave = día de semana (0-6) y valor = lista de IDs de recreos.

    Si no hay restricciones definidas, permite L-V y todos los recreos.
    """
    if not horario_json:
        # Por defecto: lunes a viernes (0-4), todos los recreos
        return fecha.weekday() < 5

    try:
        import json
        datos = json.loads(horario_json)
        dia_str = str(fecha.weekday())

        # Si el día no está en el JSON, no está permitido
        if dia_str not in datos:
            return False

        # Verificar si el recreo está en la lista de recreos del día
        recreos_permitidos = datos[dia_str]
        return recreo_id in recreos_permitidos

    except (json.JSONDecodeError, ValueError, KeyError):
        # En caso de error, permitir L-V por defecto
        return fecha.weekday() < 5


def _turno_de_recreo(turno_prof: str, recreo_turno: str) -> bool:
    if turno_prof == 'mixto':
        return True
    return turno_prof == recreo_turno


def _build_slots(session: Session, config: Configuracion) -> List[Slot]:
    zonas = session.query(Zona).all()
    if not zonas:
        return []
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
                slots.append(Slot(f, int(r['id']), r.get('turno', 'mañana'), zonas_ids[i]))
    return slots


def generar_calendario_guardias(session: Session) -> Tuple[List[Guardia], Dict[int, int]]:
    logger.info("Iniciando generación de calendario de guardias")

    config = session.query(Configuracion).first()
    if not config:
        logger.error("No existe configuración del curso")
        raise ValueError("No existe configuración del curso")

    profesores = session.query(Profesor).all()
    if not profesores:
        logger.error("No hay profesores registrados")
        raise ValueError("No hay profesores registrados")
    logger.info(f"Profesores disponibles: {len(profesores)}")

    zonas = session.query(Zona).all()
    if not zonas:
        logger.error("No hay zonas registradas")
        raise ValueError("No hay zonas registradas")
    logger.info(f"Zonas configuradas: {len(zonas)}")

    cuotas = calcular_guardias_por_profesor(session)  # {prof_id: total}
    asignadas = defaultdict(int)
    ultimo_por_zona: Dict[int, Optional[int]] = {z.id: None for z in zonas}
    ultimo_recreo_prof: Dict[int, Optional[int]] = defaultdict(lambda: None)
    ultimo_dia_prof: Dict[int, Optional[date]] = defaultdict(lambda: None)
    # NUEVO: Zona preferida de cada profesor (la primera que se le asigna)
    zona_preferida_prof: Dict[int, Optional[int]] = defaultdict(lambda: None)
    # Control de guardias por (fecha, turno, recreo) para cada profesor
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int], bool] = {}
    # REQUISITO: Máximo 1 guardia al día por profesor (sumando mañana + tarde)
    guardias_por_dia_prof: Dict[Tuple[int, date], bool] = {}

    slots = _build_slots(session, config)
    if not slots:
        return ([], {})

    calendario: List[Guardia] = []
    random.seed(42)

    for slot in slots:
        # Elegibles
        elegibles: List[Profesor] = []
        for p in profesores:
            if asignadas[p.id] >= cuotas.get(p.id, 0):
                continue
            if not _turno_de_recreo(p.turno, slot.turno):
                continue
            # VALIDACIÓN: Respetar fecha de inicio de guardias (si está definida)
            if p.fecha_inicio_guardias and slot.fecha < p.fecha_inicio_guardias:
                continue
            # VALIDACIÓN: Respetar fecha de fin de guardias (si está definida)
            if p.fecha_fin_guardias and slot.fecha > p.fecha_fin_guardias:
                continue
            # VALIDACIÓN: Respetar matriz de horario permitido (día × recreo)
            if not _horario_permitido(
                slot.fecha, slot.recreo_id, p.recreos_permitidos
            ):
                continue
            # VALIDACIÓN AUSENCIAS: Excluir profesores ausentes en esta fecha
            if profesor_ausente(session, p.id, slot.fecha):
                logger.debug(f"Profesor {p.nombre_completo} ausente el {slot.fecha}")
                continue
            # VALIDACIÓN CRÍTICA 1: Un profesor NO puede estar en dos zonas al mismo tiempo
            # (mismo día, mismo turno, mismo recreo)
            if (p.id, slot.fecha, slot.turno, slot.recreo_id) in guardias_por_slot_prof:
                continue
            # VALIDACIÓN CRÍTICA 2: Un profesor NO puede hacer más de 1 guardia al día
            # (sumando mañana y tarde)
            if (p.id, slot.fecha) in guardias_por_dia_prof:
                continue
            elegibles.append(p)

        if not elegibles:
            # no se puede cubrir, continuar (se registra hueco no bloqueante)
            continue

        # Scoring con preferencias:
        # PRIORIDAD 1: Zona preferida (mantener al profesor en la misma zona)
        # PRIORIDAD 2: Déficit de guardias (equilibrar carga)
        # PRIORIDAD 3: Continuidad de días consecutivos
        # PRIORIDAD 4: Mismo recreo anterior
        def score(p: Profesor) -> Tuple[int, int, int, int, float]:
            # s_zona: 100 si es su zona preferida, 0 si no tiene aún,
            # -50 si es otra zona
            if zona_preferida_prof[p.id] is None:
                s_zona = 0  # Primera asignación, cualquier zona está bien
            elif zona_preferida_prof[p.id] == slot.zona_id:
                s_zona = 100  # ¡Es su zona preferida! Máxima prioridad
            else:
                s_zona = -50  # No es su zona preferida, penalizar

            # Déficit de guardias (cuántas le faltan)
            deficit = cuotas.get(p.id, 0) - asignadas[p.id]

            # Continuidad de días
            s_continuidad = 1 if (
                ultimo_dia_prof[p.id]
                and (slot.fecha - ultimo_dia_prof[p.id]).days == 1
            ) else 0

            # Mismo recreo
            s_recreo = 1 if ultimo_recreo_prof[p.id] == slot.recreo_id else 0

            return (s_zona, deficit, s_continuidad, s_recreo, random.random())

        elegido = sorted(elegibles, key=score, reverse=True)[0]

        # Registrar
        calendario.append(
            Guardia(
                profesor_id=elegido.id,
                fecha=slot.fecha,
                turno=slot.turno,
                recreo=slot.recreo_id,
                zona_id=slot.zona_id,
            )
        )
        asignadas[elegido.id] += 1
        ultimo_por_zona[slot.zona_id] = elegido.id
        ultimo_recreo_prof[elegido.id] = slot.recreo_id
        ultimo_dia_prof[elegido.id] = slot.fecha

        # IMPORTANTE: Registrar zona preferida del profesor en su primera asignación
        if zona_preferida_prof[elegido.id] is None:
            zona_preferida_prof[elegido.id] = slot.zona_id
            logger.debug(
                f"Zona preferida asignada a {elegido.nombre_completo}: "
                f"Zona {slot.zona_id}"
            )

        # Marcar que este profesor ya tiene guardia en este slot (fecha, turno, recreo)
        guardias_por_slot_prof[(elegido.id, slot.fecha, slot.turno, slot.recreo_id)] = True
        # Marcar que este profesor ya tiene guardia en este día (cualquier turno)
        guardias_por_dia_prof[(elegido.id, slot.fecha)] = True

    logger.info(f"Calendario generado: {len(calendario)} guardias asignadas")
    logger.debug(f"Distribución por profesor: {dict(asignadas)}")
    return (calendario, dict(asignadas))


def guardar_guardias_en_bd(session: Session, calendario: List[Guardia]) -> None:
    if not calendario:
        logger.warning("No hay guardias para guardar en la base de datos")
        return
    logger.info(f"Guardando {len(calendario)} guardias en la base de datos")
    session.bulk_save_objects(calendario)
    session.commit()
    logger.info("Guardias guardadas exitosamente")
