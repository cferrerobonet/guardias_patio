"""
Módulo para calcular la distribución de guardias entre profesores.

Implementa la lógica de cálculo basada en:
- Días lectivos del curso
- Número de zonas
- Recreos por día según turnos
- Porcentaje de jornada de cada profesor
- Turno de trabajo (mañana, tarde, mixto)
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Tuple

from sqlalchemy.orm import Session

from src.models.models import Configuracion, Profesor, Zona


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


def calcular_distribucion_base(
    session: Session
) -> Dict[int, float]:
    """
    Calcula la distribución cruda de guardias por profesor.

    Args:
        session: Sesión de base de datos

    Returns:
        Diccionario {profesor_id: guardias_crudas_float}
    """
    # Obtener datos necesarios
    config = session.query(Configuracion).first()
    if not config:
        raise ValueError("No existe configuración del curso")

    profesores = session.query(Profesor).all()
    if not profesores:
        raise ValueError("No hay profesores registrados")

    zonas = session.query(Zona).all()
    if not zonas:
        raise ValueError("No hay zonas registradas")

    # Calcular días lectivos
    dias_lectivos = calcular_dias_lectivos(
        config.fecha_inicio_curso,
        config.fecha_fin_curso
    )

    if dias_lectivos == 0:
        raise ValueError("No hay días lectivos en el rango configurado")

    # Calcular recreos activos
    recreos_manana, recreos_tarde = calcular_recreos_activos(session)
    recreos_totales_dia = recreos_manana + recreos_tarde

    if recreos_totales_dia == 0:
        raise ValueError("No hay recreos configurados")

    # Calcular slots totales
    num_zonas = len(zonas)
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
        # El factor pondera el porcentaje según turnos disponibles
        participacion = profesor.porcentaje_jornada * factor
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
    distribucion_cruda = calcular_distribucion_base(session)
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

    dias_lectivos = calcular_dias_lectivos(
        config.fecha_inicio_curso,
        config.fecha_fin_curso
    )

    recreos_manana, recreos_tarde = calcular_recreos_activos(session)
    num_zonas = session.query(Zona).count()
    num_profesores = session.query(Profesor).count()

    slots_totales = dias_lectivos * (recreos_manana + recreos_tarde) * num_zonas

    return {
        "dias_lectivos": dias_lectivos,
        "recreos_manana": recreos_manana,
        "recreos_tarde": recreos_tarde,
        "num_zonas": num_zonas,
        "num_profesores": num_profesores,
        "slots_totales": slots_totales,
    }
