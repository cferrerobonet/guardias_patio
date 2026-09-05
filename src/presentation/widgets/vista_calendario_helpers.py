"""
Helpers de lógica de negocio para VistaCalendario.

Extraído de vista_calendario.py para reducir su tamaño (ARQ-05).
"""

import json
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from infrastructure.database.models import Ausencia as AusenciaModel, Configuracion, Zona


def parse_recreos_config(config: Configuracion) -> List[Dict]:
    """
    Parse la configuración de recreos desde JSON.

    Args:
        config: Objeto Configuracion con campo recreos_config

    Returns:
        Lista de dicts con datos de cada recreo
    """
    if config.recreos_config:
        try:
            return json.loads(config.recreos_config)
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: deducir de campos individuales
    recreos: List[Dict] = []
    recreo_id = 0

    if config.hora_recreo1_manana:
        recreo_id += 1
        recreos.append({"id": recreo_id, "turno": "mañana", "etiqueta": f"Recreo {recreo_id}"})

    if config.hora_recreo2_manana:
        recreo_id += 1
        recreos.append({"id": recreo_id, "turno": "mañana", "etiqueta": f"Recreo {recreo_id}"})

    if config.hora_recreo1_tarde:
        recreo_id += 1
        recreos.append({"id": recreo_id, "turno": "tarde", "etiqueta": f"Recreo {recreo_id}"})

    if config.hora_recreo2_tarde:
        recreo_id += 1
        recreos.append({"id": recreo_id, "turno": "tarde", "etiqueta": f"Recreo {recreo_id}"})

    return recreos


def obtener_zonas_esperadas_por_recreo(
    session, fecha: date
) -> Dict[Tuple[str, int], List[Zona]]:
    """
    Determina qué zonas deberían tener guardia para cada recreo/turno en una fecha.

    Args:
        session: Sesión SQLAlchemy
        fecha: Fecha para la cual calcular las zonas esperadas

    Returns:
        Diccionario con clave (turno, recreo) y valor lista de zonas esperadas
    """
    from application.app_services import AppServices

    zonas_por_recreo: Dict[Tuple[str, int], List[Zona]] = {}

    _svc = AppServices(session)
    config = _svc.configuracion_repo.get_first()
    if not config:
        return zonas_por_recreo

    zonas = _svc.zonas.get_all()
    zonas_activas = []
    for zona in zonas:
        zona_activa = True
        if zona.fecha_inicio and fecha < zona.fecha_inicio:
            zona_activa = False
        if zona.fecha_fin and fecha > zona.fecha_fin:
            zona_activa = False
        if zona_activa:
            zonas_activas.append(zona)

    zonas_activas = sorted(
        zonas_activas,
        key=lambda z: (
            int(z.nombre_zona[1]) if z.nombre_zona and z.nombre_zona.startswith("Z") else 999
        ),
    )

    recreos_list = parse_recreos_config(config)

    for recreo_data in recreos_list:
        recreo_id = recreo_data["id"]
        turno = recreo_data.get("turno", "mañana")
        num_zonas = recreo_data.get("zonas", len(zonas_activas))
        zonas_para_recreo = zonas_activas[: min(num_zonas, len(zonas_activas))]
        zonas_por_recreo[(turno, recreo_id)] = zonas_para_recreo

    return zonas_por_recreo


def cargar_datos_periodo(session, fecha_inicio: date, fecha_fin: date) -> tuple:
    """
    Cargar guardias, ausencias y sustituciones de un periodo.

    Args:
        session: Sesión SQLAlchemy
        fecha_inicio: Fecha de inicio del periodo
        fecha_fin: Fecha de fin del periodo

    Returns:
        Tupla de (guardias_por_fecha, ausencias_por_fecha, sustituciones_por_fecha)
    """
    from application.app_services import AppServices
    from infrastructure.database.models import Guardia as GuardiaModel
    from sqlalchemy.orm import joinedload

    _svc = AppServices(session)
    curso_activo = _svc.cursos.find_active()

    if not curso_activo:
        return defaultdict(list), defaultdict(list), defaultdict(list)

    guardias = (
        session.query(GuardiaModel)
        .options(joinedload(GuardiaModel.zona))
        .filter(
            GuardiaModel.curso_id == curso_activo.id,
            GuardiaModel.fecha >= fecha_inicio,
            GuardiaModel.fecha <= fecha_fin,
        )
        .all()
    )

    guardias_por_fecha: defaultdict = defaultdict(list)
    sustituciones_por_fecha: defaultdict = defaultdict(list)

    for g in guardias:
        guardias_por_fecha[g.fecha].append(g)
        if hasattr(g, "profesor_sustituido_id") and g.profesor_sustituido_id:
            sustituciones_por_fecha[g.fecha].append(g)

    ausencias = (
        session.query(AusenciaModel)
        .options(joinedload(AusenciaModel.profesor))
        .filter(
            AusenciaModel.activa == True,  # noqa: E712
            AusenciaModel.fecha_inicio <= fecha_fin,
            AusenciaModel.fecha_fin >= fecha_inicio,
        )
        .all()
    )

    ausencias_por_fecha: defaultdict = defaultdict(list)
    for ausencia in ausencias:
        fecha_actual = max(ausencia.fecha_inicio, fecha_inicio)
        fecha_fin_ausencia = min(ausencia.fecha_fin, fecha_fin)

        while fecha_actual <= fecha_fin_ausencia:
            ausencias_por_fecha[fecha_actual].append(ausencia)
            fecha_actual += timedelta(days=1)

    return guardias_por_fecha, ausencias_por_fecha, sustituciones_por_fecha


def estilo_dia_miniatura(fecha: date, num_guardias: int, fecha_actual: date) -> str:
    """
    Obtener estilo CSS para día en vista anual miniatura.

    Args:
        fecha: Fecha del día
        num_guardias: Número de guardias en ese día
        fecha_actual: Fecha de hoy (para resaltar)

    Returns:
        String con stylesheet CSS
    """
    es_hoy = fecha == fecha_actual

    if es_hoy:
        return """
            QLabel {
                background-color: #FBC02D;
                color: white;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
        """
    elif num_guardias > 0:
        intensidad = min(num_guardias * 20, 200)
        return f"""
            QLabel {{
                background-color: rgb({255 - intensidad}, {242 - intensidad // 2}, 253);
                border: 1px solid #90CAF9;
                border-radius: 3px;
                font-size: 12px;
            }}
        """
    else:
        return """
            QLabel {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 3px;
                font-size: 12px;
            }
        """
