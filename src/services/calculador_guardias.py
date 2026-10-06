"""
Módulo para calcular la distribución de guardias entre profesores.

Implementa la lógica de cálculo basada en:
- Días lectivos del curso (incluye festivos automáticos y personalizados)
- Número de zonas
- Recreos por día (configurables por turno y zonas por recreo)
- Porcentaje de jornada de cada profesor y ajuste por tutoría
- Turno de trabajo (mañana, tarde, mixto)
- Guardias voluntarias hechas antes del reparto oficial (misma fórmula que
  DistribucionCuotasService: parte de (S + W) menos las voluntarias de cada uno)
"""

import json
import math
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from infrastructure.database.models import Configuracion, Profesor, Zona
from services.gestor_cursos import GestorCursos
from services.validators import TurnoValidator
from utils import get_logger

logger = get_logger(__name__)

# Instancia global del validador de turnos
_turno_validator = TurnoValidator()


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

    Incluye: 9/10, 12/10, 1/11, 6/12, 8/12, 23/12–6/01, 17–19/03, Jueves Santo–+11, 1/05.
    Lectivos fijos: 22/12, 16/03.
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

        # 23/12 a 06/01 (puede cruzar de y a y+1) - 22/12 es LECTIVO
        for day_ in range(23, 32):
            add_if_in_range(date(y, 12, day_))
        for day_ in range(1, 7):
            add_if_in_range(date(y + 1, 1, day_))

        # 17–19 de marzo NO LECTIVOS (Fallas) - 16/03 es LECTIVO
        for day_ in range(17, 20):
            add_if_in_range(date(y, 3, day_))

        # Jueves Santo a +11 días
        easter = _easter_sunday(y)
        jueves_santo = easter - timedelta(days=3)
        for delta in range(0, 12):
            add_if_in_range(jueves_santo + timedelta(days=delta))

    return no_lectivos


def _parse_custom_no_lectivos(csv_text: Optional[str]) -> set:
    fechas = set()
    if not csv_text:
        return fechas
    for token in csv_text.split(","):
        t = token.strip()
        if not t:
            continue
        try:
            y, m, d = [int(x) for x in t.split("-")]
            fechas.add(date(y, m, d))
        except (SQLAlchemyError, ValueError, TypeError, OSError):
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
        if getattr(config, "activar_festivos_automaticos", True)
        else set()
    )
    custom = _parse_custom_no_lectivos(getattr(config, "dias_no_lectivos_personalizados", None))
    no_lectivos = autom | custom

    curr = inicio
    while curr <= fin:
        if curr.weekday() < 5 and curr not in no_lectivos:
            dias.append(curr)
        curr += timedelta(days=1)
    return dias


def fecha_inicio_reparto(config: Configuracion) -> date:
    """Primer día del reparto oficial: el mayor entre el inicio de curso y el inicio oficial.

    Sin `fecha_inicio_reparto_oficial` (None) el reparto empieza con el curso.
    """
    inicio = config.fecha_inicio_curso
    oficial = getattr(config, "fecha_inicio_reparto_oficial", None)
    if isinstance(oficial, date) and (inicio is None or oficial > inicio):
        return oficial
    return inicio


def listar_dias_reparto(config: Configuracion) -> List[date]:
    """Días lectivos que entran en el reparto oficial de guardias.

    Son los de `listar_dias_lectivos` desde `fecha_inicio_reparto(config)`: antes de
    esa fecha sólo hay guardias voluntarias, que no se generan ni se cuentan como ranuras.
    """
    desde = fecha_inicio_reparto(config)
    return [d for d in listar_dias_lectivos(config) if d >= desde]


def voluntarias_de(profesor) -> int:
    """Guardias voluntarias registradas en la ficha (0 si el dato falta o no es un entero)."""
    valor = getattr(profesor, "guardias_voluntarias", 0)
    if isinstance(valor, bool) or not isinstance(valor, int):
        return 0
    return max(0, valor)


def _parse_recreos_config(config: Configuracion) -> List[dict]:
    """Parsea recreos_config JSON en una lista de dicts normalizados."""
    raw = getattr(config, "recreos_config", None)
    if not raw:
        return []
    try:
        # La entidad de dominio ya trae la lista; el modelo y el DTO, el texto JSON.
        data = raw if isinstance(raw, list) else json.loads(raw)
        out = []
        for r in data:
            out.append(
                {
                    "id": int(r.get("id")),
                    "etiqueta": r.get("etiqueta", ""),
                    "turno": r.get("turno", "mañana"),
                    "zonas": int(r.get("zonas", 1)),
                }
            )
        return out
    except (ValueError, KeyError):
        return []


def turnos_con_recreos(config) -> tuple[bool, bool]:
    """(hay guardias de mañana, hay guardias de tarde) según los recreos guardados.

    Un centro puede no tener recreos de mañana o de tarde (2026-10-06); Ajustes,
    la rejilla de recreos del profesor y la comprobación previa a generar lo
    leen de aquí. Sin lista guardada (configuraciones antiguas), por las horas.
    """
    if config is None:
        return True, True
    lista = _parse_recreos_config(config)
    if lista:
        # Lo que no es de tarde es de mañana: hay listas antiguas con «manana».
        de_tarde = [str(r.get("turno") or "").strip().lower() == "tarde" for r in lista]
        return (not all(de_tarde), any(de_tarde))
    hora = lambda campo: getattr(config, campo, None)  # noqa: E731
    return (
        bool(hora("hora_recreo1_manana") or hora("hora_recreo2_manana")),
        bool(hora("hora_recreo1_tarde") and hora("hora_recreo2_tarde")),
    )


def turnos_con_recreos_guardados(session) -> tuple[bool, bool]:
    """`turnos_con_recreos` de la configuración guardada (para la interfaz)."""
    return turnos_con_recreos(session.query(Configuracion).first())


def ajustar_zonas_de_los_recreos(session, antes: int) -> None:
    """Al cambiar el número de zonas, los recreos que cubrían todas siguen cubriéndolas.

    Ajustes guarda en cada recreo cuántas zonas cubre, y siempre escribe el total
    del momento. Los repartos usan `min(recreo["zonas"], zonas)`: una zona creada
    después de guardar Ajustes se quedaba sin guardias sin que nada avisara
    (2026-10-03).
    """
    ahora = session.query(Zona).filter(Zona.activa.is_(True)).count()
    if ahora == antes:
        return
    for config in session.query(Configuracion).all():
        try:
            recreos = json.loads(config.recreos_config or "[]")
        except ValueError:
            continue
        if not isinstance(recreos, list):
            continue
        cambiado = False
        for recreo in recreos:
            if not isinstance(recreo, dict):
                continue
            zonas = recreo.get("zonas")
            if zonas == antes or (isinstance(zonas, int) and zonas > ahora):
                recreo["zonas"] = ahora
                cambiado = True
        if cambiado:
            config.recreos_config = json.dumps(recreos)
    session.commit()


def calcular_recreos_activos(session) -> Tuple[int, int]:
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
        rm = sum(1 for r in lista if r.get("turno") == "mañana")
        rt = sum(1 for r in lista if r.get("turno") == "tarde")
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
    profesor: Profesor, recreos_manana: int, recreos_tarde: int
) -> float:
    """
    Calcula el factor de participación de un profesor según su turno y horas.

    Para profesores mixtos, calcula la proporción según las horas en cada turno.
    Ejemplo: Si tiene 15h mañana y 15h tarde → factor = 1.0 (puede cubrir todo)
             Si tiene 20h mañana y 10h tarde → factor proporcional a cada turno

    Args:
        profesor: Instancia de Profesor
        recreos_manana: Número de recreos de mañana
        recreos_tarde: Número de recreos de tarde

    Returns:
        Factor de participación (proporción de recreos que puede cubrir)
    """
    horas_manana = getattr(profesor, "horas_manana", 0) or 0
    horas_tarde = getattr(profesor, "horas_tarde", 0) or 0

    return _turno_validator.calcular_factor_participacion(
        profesor.turno, recreos_manana, recreos_tarde, horas_manana, horas_tarde
    )


def calcular_slots_reales(session, config: Configuracion) -> int:
    """
    Calcula el número real de slots considerando las fechas de disponibilidad de las zonas.

    IMPORTANTE: Usa la misma lógica que _build_slots() del asignador para garantizar
    consistencia entre la distribución calculada y las guardias generadas.

    Args:
        session: Sesión de base de datos
        config: Configuración del curso

    Returns:
        int: Número total de slots disponibles
    """
    from services._asignador_cpsat_helpers import _generar_slots

    # Los mismos huecos que el generador
    try:
        slots_list = _generar_slots(config, session)
        return len(slots_list)
    except (ValueError, TypeError, OSError) as e:
        logger.error(f"Error al calcular slots reales: {e}")
        return 0


def calcular_distribucion_cruda(session) -> Dict[int, float]:
    """
    Calcula la distribución cruda de guardias por profesor del curso activo.

    Args:
        session: Sesión de base de datos

    Returns:
        Diccionario {profesor_id: guardias_crudas_float}
    """
    logger.info("Iniciando cálculo de distribución cruda de guardias")

    # Obtener curso activo
    curso_activo = GestorCursos.from_session(session).obtener_curso_activo()
    if not curso_activo:
        logger.error("No hay curso activo")
        raise ValueError("No hay curso activo")

    # Obtener configuración global del sistema
    config = session.query(Configuracion).first()
    if not config:
        logger.error("No existe configuración del sistema")
        raise ValueError("No existe configuración del sistema")

    # Obtener profesores activos (no basarse en guardias existentes)
    # Esto permite calcular distribución desde cero
    profesores = (
        session.query(Profesor)
        .filter(Profesor.activo == True)  # noqa: E712
        .all()
    )
    if not profesores:
        logger.error("No hay profesores activos en el sistema")
        raise ValueError("No hay profesores activos en el sistema")
    logger.info(f"Profesores a considerar: {len(profesores)}")

    # Obtener todas las zonas activas
    zonas = session.query(Zona).filter(Zona.activa.is_(True)).all()
    if not zonas:
        logger.error("No hay zonas registradas en el sistema")
        raise ValueError("No hay zonas registradas en el sistema")
    logger.info(f"Zonas disponibles: {len(zonas)}")

    # Calcular días lectivos con festivos (sólo los del reparto oficial)
    dias_list = listar_dias_reparto(config)
    dias_lectivos = len(dias_list)

    if dias_lectivos == 0:
        raise ValueError("No hay días lectivos en el rango configurado")

    # Calcular recreos activos y slots por día
    recreos_manana, recreos_tarde = calcular_recreos_activos(session)
    recreos_totales_dia = recreos_manana + recreos_tarde

    if recreos_totales_dia == 0:
        raise ValueError("No hay recreos configurados")

    # Calcular slots totales considerando fechas de disponibilidad de las zonas
    slots_totales = calcular_slots_reales(session, config)

    if slots_totales == 0:
        raise ValueError("No hay slots disponibles (verificar fechas de zonas)")

    logger.info(f"Slots totales disponibles (con fechas de zonas): {slots_totales}")

    # Calcular factor de participación y porcentaje total
    profesores_con_factor = []
    suma_ponderada = 0.0

    for profesor in profesores:
        # 1. Factor por turno (proporción de recreos disponibles)
        factor_turno = calcular_factor_participacion(profesor, recreos_manana, recreos_tarde)

        # 2. Factor por porcentaje de jornada (ya normalizado 0-100%)
        # Usar porcentaje_jornada en lugar de horas_contrato para evitar
        # problemas con datos incorrectos (ej: 60h cuando máximo es 30h)
        factor_horas = profesor.porcentaje_jornada / 100.0

        # 3. Factor de multiplicación según tutoría (de configuración)
        factor_tutoria = (
            getattr(config, "ajuste_tutores", 1.0)
            if getattr(profesor, "tutor", False)
            else getattr(config, "ajuste_no_tutores", 1.0)
        )

        # 4. Proporción de días disponibles si tiene fechas límite
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
                logger.info(
                    f"  📅 {profesor.nombre_completo}: "
                    f"fecha_inicio={profesor.fecha_inicio_guardias} → "
                    f"{dias_disponibles}/{dias_lectivos} días disponibles "
                    f"({proporcion_tiempo:.1%}), cuota ajustada"
                )
            else:
                proporcion_tiempo = 0.0
                logger.warning(
                    f"  ⚠️  {profesor.nombre_completo}: "
                    f"sin días disponibles en el rango configurado "
                    f"(inicio={inicio_prof}, fin={fin_prof})"
                )

        # Participación total = turno × horas × tutoría × tiempo
        participacion = factor_turno * factor_horas * factor_tutoria * proporcion_tiempo

        logger.debug(
            f"Profesor {profesor.nombre_completo}: "
            f"turno={factor_turno:.2f}, jornada={factor_horas:.2f} "
            f"({profesor.porcentaje_jornada}%), tutoría={factor_tutoria:.2f}, "
            f"tiempo={proporcion_tiempo:.2f} → participación={participacion:.4f}"
        )

        profesores_con_factor.append((profesor.id, participacion))
        suma_ponderada += participacion

    if suma_ponderada == 0:
        raise ValueError("La suma de participación ponderada es 0 (verificar turnos y porcentajes)")

    # Distribuir S + W proporcionalmente y descontar las voluntarias de cada uno.
    # Quien hizo más de las que le tocan queda a 0 y se reparte de nuevo sin él.
    voluntarias = {p.id: voluntarias_de(p) for p in profesores}
    excluidos: set = set()
    while True:
        activos = [(pid, part) for pid, part in profesores_con_factor if pid not in excluidos]
        suma_activos = sum(part for _, part in activos)
        total = slots_totales + sum(voluntarias[pid] for pid, _ in activos)
        distribucion = {pid: 0.0 for pid, _ in profesores_con_factor}
        negativos = []
        for profesor_id, participacion in activos:
            parte = (participacion / suma_activos) * total if suma_activos else 0.0
            guardias_crudas = parte - voluntarias[profesor_id]
            if guardias_crudas < 0:
                negativos.append(profesor_id)
            distribucion[profesor_id] = guardias_crudas
        if not negativos:
            break
        excluidos.update(negativos)
        logger.info(f"{len(negativos)} profesores han hecho más voluntarias de las que les tocan")

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
    profesores_ordenados = sorted(residuos.items(), key=lambda x: x[1], reverse=True)

    # Asignar slots sobrantes
    for i in range(slots_sobrantes):
        profesor_id = profesores_ordenados[i][0]
        distribucion_floor[profesor_id] += 1

    return distribucion_floor


def calcular_guardias_por_profesor(session) -> Dict[int, int]:
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


def obtener_estadisticas(session) -> Dict:
    """
    Obtiene estadísticas del cálculo para verificación filtradas por curso activo.

    Args:
        session: Sesión de base de datos

    Returns:
        Diccionario con estadísticas del cálculo del curso activo
    """
    # Obtener curso activo
    curso_activo = GestorCursos.from_session(session).obtener_curso_activo()
    if not curso_activo:
        logger.warning("No hay curso activo para obtener estadísticas")
        return {}

    # Obtener configuración global del sistema
    config = session.query(Configuracion).first()
    if not config:
        logger.warning("No hay configuración del sistema")
        return {}

    dias_lectivos = len(listar_dias_reparto(config))

    recreos_manana, recreos_tarde = calcular_recreos_activos(session)

    # Contar zonas disponibles
    num_zonas = session.query(Zona).filter(Zona.activa.is_(True)).count()

    # Contar profesores activos (disponibles para asignación)
    num_profesores = (
        session.query(Profesor)
        .filter(Profesor.activo == True)  # noqa: E712
        .count()
    )

    # Calcular slots totales considerando fechas de disponibilidad de las zonas
    slots_totales = calcular_slots_reales(session, config)

    logger.info(
        f"Estadísticas del curso {curso_activo.nombre}: "
        f"{num_profesores} profesores, {num_zonas} zonas, "
        f"{slots_totales} slots"
    )

    return {
        "dias_lectivos": dias_lectivos,
        "recreos_manana": recreos_manana,
        "recreos_tarde": recreos_tarde,
        "num_zonas": num_zonas,
        "num_profesores": num_profesores,
        "slots_totales": slots_totales,
    }
