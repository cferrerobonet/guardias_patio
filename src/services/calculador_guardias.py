"""
Módulo para calcular la distribución de guardias entre profesores.

Implementa la lógica de cálculo basada en:
- Días lectivos del curso (incluye festivos automáticos y personalizados)
- Número de zonas
- Recreos por día (configurables por turno y zonas por recreo)
- Porcentaje de jornada de cada profesor y ajuste por tutoría
- Turno de trabajo (mañana, tarde, mixto)
"""

import json
import math
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from models.models import Configuracion, Profesor, Zona
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


def calcular_dias_lectivos(fecha_inicio: datetime, fecha_fin: datetime) -> int:
    """
    Calcula el número de días lectivos entre dos fechas.

    Excluye sábados y domingos. En el futuro puede excluir festivos.

    Args:
        fecha_inicio: Fecha de inicio del curso
        fecha_fin: Fecha de fin del curso

    Returns:
        Número de días lectivos (lunes a viernes)
    """
    if fecha_inicio > fecha_fin:
        return 0

    dias_lectivos = 0
    fecha_actual = fecha_inicio

    while fecha_actual <= fecha_fin:
        # 0=lunes, 1=martes, ..., 5=sábado, 6=domingo
        if fecha_actual.weekday() < 5:  # lunes a viernes
            dias_lectivos += 1
        fecha_actual += timedelta(days=1)

    return dias_lectivos


def _easter_sunday(year: int) -> date:
    """Calcula la fecha de Domingo de Pascua (algoritmo de Butcher)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _festivos_automaticos_en_rango(
    inicio: date,
    fin: date,
) -> set:
    """Genera el conjunto de fechas no lectivas automáticas dentro del rango.

    Incluye: 9/10, 12/10, 1/11, 6/12, 8/12, 22/12–6/01, 16–19/03, Jueves Santo–+12, 1/05.
    """
    no_lectivos = set()
    if inicio > fin:
        return no_lectivos

    # Años potenciales (curso puede abarcar dos)
    years = {inicio.year, fin.year}
    if inicio.year != fin.year:
        years.add(inicio.year + 1)

    def add_if_in_range(d: date):
        if inicio <= d <= fin and d.weekday() < 5:
            no_lectivos.add(d)

    current = inicio
    while current <= fin:
        # Fines de semana se gestionan aparte en días lectivos, aquí no hace falta añadir
        current += timedelta(days=1)

    for y in years:
        # Fechas fijas en ambos años
        for month, days in (
            (10, [9, 12]),
            (11, [1]),
            (12, [6, 8]),
            (5, [1]),
        ):
            for d in days:
                add_if_in_range(date(y, month, d))

        # 22/12 a 06/01 (puede cruzar de y a y+1)
        for day_ in range(22, 32):
            add_if_in_range(date(y, 12, day_))
        for day_ in range(1, 7):
            add_if_in_range(date(y + 1, 1, day_))

        # 16–19 de marzo
        for day_ in range(16, 20):
            add_if_in_range(date(y, 3, day_))

        # Jueves Santo a +12 días
        easter = _easter_sunday(y)
        jueves_santo = easter - timedelta(days=3)
        for delta in range(0, 13):
            add_if_in_range(jueves_santo + timedelta(days=delta))

    return no_lectivos


def _parse_custom_no_lectivos(csv_text: Optional[str]) -> set:
    fechas = set()
    if not csv_text:
        return fechas
    for token in csv_text.split(','):
        t = token.strip()
        if not t:
            continue
        try:
            y, m, d = [int(x) for x in t.split('-')]
            fechas.add(date(y, m, d))
        except Exception:
            continue
    return fechas


def listar_dias_lectivos(config: Configuracion) -> List[date]:
    """Genera la lista de días lectivos, excluyendo festivos automáticos/personalizados."""
    inicio = config.fecha_inicio_curso
    fin = config.fecha_fin_curso
    dias: List[date] = []
    if inicio > fin:
        return dias

    autom = (
        _festivos_automaticos_en_rango(inicio, fin)
        if getattr(config, 'activar_festivos_automaticos', True)
        else set()
    )
    custom = _parse_custom_no_lectivos(getattr(config, 'dias_no_lectivos_personalizados', None))
    no_lectivos = autom | custom

    curr = inicio
    while curr <= fin:
        if curr.weekday() < 5 and curr not in no_lectivos:
            dias.append(curr)
        curr += timedelta(days=1)
    return dias


def _parse_recreos_config(config: Configuracion) -> List[dict]:
    """Parsea recreos_config JSON en una lista de dicts normalizados."""
    raw = getattr(config, 'recreos_config', None)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        out = []
        for r in data:
            out.append(
                {
                    'id': int(r.get('id')),
                    'etiqueta': r.get('etiqueta', ''),
                    'turno': r.get('turno', 'mañana'),
                    'zonas': int(r.get('zonas', 1)),
                }
            )
        return out
    except Exception:
        return []


def calcular_recreos_activos(session: Session) -> Tuple[int, int]:
    """
    Determina cuántos recreos están activos en mañana y tarde.

    Args:
        session: Sesión de base de datos

    Returns:
        Tupla (recreos_manana, recreos_tarde)
    """
    config = session.query(Configuracion).first()
    if not config:
        return (0, 0)

    # Si hay recreos_config, usarlo
    lista = _parse_recreos_config(config)
    if lista:
        rm = sum(1 for r in lista if r.get('turno') == 'mañana')
        rt = sum(1 for r in lista if r.get('turno') == 'tarde')
        return (rm, rt)

    # Fallback a campos de horas
    recreos_manana = 0
    if config.hora_recreo1_manana:
        recreos_manana += 1
    if config.hora_recreo2_manana:
        recreos_manana += 1

    recreos_tarde = 0
    if config.hora_recreo1_tarde:
        recreos_tarde += 1
    if config.hora_recreo2_tarde:
        recreos_tarde += 1

    return (recreos_manana, recreos_tarde)


def calcular_factor_participacion(
    profesor: Profesor,
    recreos_manana: int,
    recreos_tarde: int
) -> float:
    """
    Calcula el factor de participación de un profesor según su turno.

    Args:
        profesor: Instancia de Profesor
        recreos_manana: Número de recreos de mañana
        recreos_tarde: Número de recreos de tarde

    Returns:
        Factor de participación (0.0 a 2.0 si hay recreos en ambos turnos)
    """
    recreos_totales = recreos_manana + recreos_tarde
    if recreos_totales == 0:
        return 0.0

    if profesor.turno == "mañana":
        return recreos_manana / recreos_totales
    elif profesor.turno == "tarde":
        return recreos_tarde / recreos_totales
    else:  # mixto
        return 1.0


def calcular_distribucion_cruda(
    session: Session
) -> Dict[int, float]:
    """
    Calcula la distribución cruda de guardias por profesor.

    Args:
        session: Sesión de base de datos

    Returns:
        Diccionario {profesor_id: guardias_crudas_float}
    """
    logger.info("Iniciando cálculo de distribución cruda de guardias")

    # Obtener datos necesarios
    config = session.query(Configuracion).first()
    if not config:
        logger.error("No existe configuración del curso")
        raise ValueError("No existe configuración del curso")

    profesores = session.query(Profesor).all()
    if not profesores:
        logger.error("No hay profesores registrados")
        raise ValueError("No hay profesores registrados")
    logger.info(f"Profesores a considerar: {len(profesores)}")

    zonas = session.query(Zona).all()
    if not zonas:
        logger.error("No hay zonas registradas")
        raise ValueError("No hay zonas registradas")
    logger.info(f"Zonas disponibles: {len(zonas)}")

    # Calcular días lectivos con festivos
    dias_list = listar_dias_lectivos(config)
    dias_lectivos = len(dias_list)

    if dias_lectivos == 0:
        raise ValueError("No hay días lectivos en el rango configurado")

    # Calcular recreos activos y slots por día
    recreos_manana, recreos_tarde = calcular_recreos_activos(session)
    recreos_totales_dia = recreos_manana + recreos_tarde

    if recreos_totales_dia == 0:
        raise ValueError("No hay recreos configurados")

    # Calcular slots totales
    num_zonas = len(zonas)
    lista_recreos = _parse_recreos_config(config)
    if lista_recreos:
        # Sumar zonas por recreo, pero no exceder zonas reales disponibles
        zonas_por_dia = sum(min(r.get('zonas', 1), num_zonas) for r in lista_recreos)
        slots_totales = dias_lectivos * zonas_por_dia
    else:
        slots_totales = dias_lectivos * recreos_totales_dia * num_zonas

    # Calcular factor de participación y porcentaje total
    profesores_con_factor = []
    suma_ponderada = 0.0

    for profesor in profesores:
        factor = calcular_factor_participacion(
            profesor,
            recreos_manana,
            recreos_tarde
        )
        # El factor pondera el porcentaje según turnos disponibles y tutoría
        ajuste_tutoria = (
            getattr(config, 'ajuste_tutores', 1.0) if getattr(profesor, 'tutor', False)
            else getattr(config, 'ajuste_no_tutores', 1.0)
        )

        # Calcular proporción de días disponibles si tiene fechas límite
        proporcion_tiempo = 1.0
        if profesor.fecha_inicio_guardias or profesor.fecha_fin_guardias:
            # Determinar rango efectivo del profesor
            inicio_prof = (
                profesor.fecha_inicio_guardias
                if profesor.fecha_inicio_guardias
                else config.fecha_inicio_curso
            )
            fin_prof = (
                profesor.fecha_fin_guardias
                if profesor.fecha_fin_guardias
                else config.fecha_fin_curso
            )

            # Contar días lectivos del profesor dentro del curso
            dias_prof = [d for d in dias_list if inicio_prof <= d <= fin_prof]
            dias_disponibles = len(dias_prof)

            if dias_disponibles > 0:
                proporcion_tiempo = dias_disponibles / dias_lectivos
                logger.debug(
                    f"Profesor {profesor.nombre_completo}: "
                    f"{dias_disponibles}/{dias_lectivos} días disponibles "
                    f"({proporcion_tiempo:.2%})"
                )
            else:
                proporcion_tiempo = 0.0
                logger.warning(
                    f"Profesor {profesor.nombre_completo}: "
                    f"sin días disponibles en el rango configurado"
                )

        participacion = (
            profesor.porcentaje_jornada * factor * ajuste_tutoria * proporcion_tiempo
        )
        profesores_con_factor.append((profesor.id, participacion))
        suma_ponderada += participacion

    if suma_ponderada == 0:
        raise ValueError(
            "La suma de participación ponderada es 0 "
            "(verificar turnos y porcentajes)"
        )

    # Distribuir slots proporcionalmente
    distribucion = {}
    for profesor_id, participacion in profesores_con_factor:
        guardias_crudas = (participacion / suma_ponderada) * slots_totales
        distribucion[profesor_id] = guardias_crudas

    logger.info(f"Distribución cruda calculada para {len(distribucion)} profesores")
    logger.debug(f"Total slots a distribuir: {slots_totales}")
    logger.debug(f"Días lectivos: {dias_lectivos}, Recreos/día: {recreos_totales_dia}")

    return distribucion


def ajustar_redondeo(distribucion_cruda: Dict[int, float]) -> Dict[int, int]:
    """
    Ajusta el redondeo para que la suma sea exacta.

    Aplica floor a todos y reparte los slots sobrantes a quienes tienen
    mayor residuo decimal.

    Args:
        distribucion_cruda: Diccionario con guardias en float

    Returns:
        Diccionario con guardias ajustadas en int
    """
    # Calcular floor y residuos
    distribucion_floor = {}
    residuos = {}
    suma_floor = 0
    suma_total = 0

    for profesor_id, guardias_crudas in distribucion_cruda.items():
        floor_val = math.floor(guardias_crudas)
        distribucion_floor[profesor_id] = floor_val
        residuos[profesor_id] = guardias_crudas - floor_val
        suma_floor += floor_val
        suma_total += guardias_crudas

    # Calcular slots sobrantes
    slots_sobrantes = round(suma_total) - suma_floor

    # Ordenar profesores por residuo (mayor a menor)
    profesores_ordenados = sorted(
        residuos.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Asignar slots sobrantes
    for i in range(slots_sobrantes):
        profesor_id = profesores_ordenados[i][0]
        distribucion_floor[profesor_id] += 1

    return distribucion_floor


def calcular_guardias_por_profesor(session: Session) -> Dict[int, int]:
    """
    Función principal: calcula cuántas guardias corresponden a cada profesor.

    Args:
        session: Sesión de base de datos

    Returns:
        Diccionario {profesor_id: total_guardias_asignadas}

    Raises:
        ValueError: Si faltan datos de configuración, profesores o zonas
    """
    distribucion_cruda = calcular_distribucion_cruda(session)
    distribucion_final = ajustar_redondeo(distribucion_cruda)

    return distribucion_final


def obtener_estadisticas(session: Session) -> Dict:
    """
    Obtiene estadísticas del cálculo para verificación.

    Args:
        session: Sesión de base de datos

    Returns:
        Diccionario con estadísticas del cálculo
    """
    config = session.query(Configuracion).first()
    if not config:
        return {}

    dias_lectivos = len(listar_dias_lectivos(config))

    recreos_manana, recreos_tarde = calcular_recreos_activos(session)
    num_zonas = session.query(Zona).count()
    num_profesores = session.query(Profesor).count()

    lista_recreos = _parse_recreos_config(config)
    if lista_recreos:
        zonas_por_dia = sum(min(r.get('zonas', 1), num_zonas) for r in lista_recreos)
        slots_totales = dias_lectivos * zonas_por_dia
    else:
        slots_totales = dias_lectivos * (recreos_manana + recreos_tarde) * num_zonas

    return {
        "dias_lectivos": dias_lectivos,
        "recreos_manana": recreos_manana,
        "recreos_tarde": recreos_tarde,
        "num_zonas": num_zonas,
        "num_profesores": num_profesores,
        "slots_totales": slots_totales,
    }
