"""Qué guarda la aplicación sobre una persona: contarlo y exportarlo (PRIV-003).

Borrar un profesor arrastraba en silencio sus ausencias —incluidas las bajas
médicas— porque la clave foránea está en cascada. Aquí está lo necesario para
decir antes qué se va a perder y para llevarse una copia.
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import inspect, or_

from infrastructure.database.models import Ausencia, Guardia, GuardiaAuditLog, Profesor

logger = logging.getLogger(__name__)


def _valor(v):
    return v.isoformat() if isinstance(v, (date, datetime)) else v


def _fila(obj) -> dict:
    """Todas las columnas de una fila, sin tener que enumerarlas a mano."""
    return {c.key: _valor(getattr(obj, c.key)) for c in inspect(obj).mapper.column_attrs}


def _consultas(session, profesor_id: int):
    guardias = session.query(Guardia).filter(
        or_(Guardia.profesor_id == profesor_id, Guardia.profesor_sustituido_id == profesor_id)
    )
    ausencias = session.query(Ausencia).filter(Ausencia.profesor_id == profesor_id)
    registro = session.query(GuardiaAuditLog).filter(GuardiaAuditLog.profesor_id == profesor_id)
    return guardias, ausencias, registro


def resumen_de_persona(session, profesor_id: int) -> dict:
    """Cuántas filas cuelgan de esta persona, para poder avisar antes de borrar."""
    profesor = session.query(Profesor).filter(Profesor.id == profesor_id).first()
    if profesor is None:
        return {}
    guardias, ausencias, registro = _consultas(session, profesor_id)
    bajas = ausencias.filter(Ausencia.tipo == "baja_medica").count()
    return {
        "nombre_completo": profesor.nombre_completo,
        "guardias": guardias.count(),
        "ausencias": ausencias.count(),
        "bajas_medicas": bajas,
        "registro_de_actividad": registro.count(),
    }


def texto_de_lo_que_se_pierde(resumen: dict) -> str:
    """Frases en plural correcto para el diálogo de borrado. Vacío si no hay nada."""
    piezas = []
    if resumen.get("guardias"):
        n = resumen["guardias"]
        piezas.append(f"{n} guardia{'s' if n != 1 else ''}")
    if resumen.get("ausencias"):
        n, bajas = resumen["ausencias"], resumen.get("bajas_medicas", 0)
        texto = f"{n} ausencia{'s' if n != 1 else ''}"
        if bajas:
            plural = "s" if bajas != 1 else ""
            texto += f" (de ellas {bajas} baja{plural} médica{plural})"
        piezas.append(texto)
    if resumen.get("registro_de_actividad"):
        n = resumen["registro_de_actividad"]
        piezas.append(f"{n} apunte{'s' if n != 1 else ''} del registro de actividad")
    return ", ".join(piezas)


def exportar_persona(session, profesor_id: int, destino: Path) -> Optional[Path]:
    """Guarda en un JSON todo lo que la aplicación sabe de esa persona."""
    profesor = session.query(Profesor).filter(Profesor.id == profesor_id).first()
    if profesor is None:
        return None
    guardias, ausencias, registro = _consultas(session, profesor_id)
    datos = {
        "exportado_el": datetime.now().isoformat(timespec="seconds"),
        "profesor": _fila(profesor),
        "guardias": [_fila(g) for g in guardias.all()],
        "ausencias": [_fila(a) for a in ausencias.all()],
        "registro_de_actividad": [_fila(r) for r in registro.all()],
    }
    try:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(datos, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
        destino.chmod(0o600)
        return destino
    except OSError as e:
        logger.error(f"No se pudo exportar los datos de la persona: {e}")
        return None
