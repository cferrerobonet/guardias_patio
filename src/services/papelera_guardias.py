"""Papelera de «Limpiar guardias» (FUN-012).

Limpiar borra el calendario entero de un clic. Antes se hacía copia de la base
de datos (FUN-004), pero recuperarla exigía ir a Importar/Exportar, elegir el
fichero y perder por el camino todo lo demás hecho desde entonces.

Aquí las guardias borradas se guardan aparte en un fichero, junto a la base de
datos del usuario, y se pueden devolver con un botón mientras no pasen 24 horas.
Es un deshacer acotado: sólo toca la tabla de guardias.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from core.logging import get_logger
from infrastructure.database.models import Guardia, Profesor, Zona

logger = get_logger(__name__)

NOMBRE_DEL_FICHERO = "papelera_guardias.json"
HORAS_DE_VIDA = 24

_CAMPOS = (
    "id",
    "curso_id",
    "profesor_id",
    "fecha",
    "turno",
    "recreo",
    "zona_id",
    "es_sustitucion",
    "profesor_sustituido_id",
    "notas",
)


def ruta_de_la_papelera(session) -> Optional[Path]:
    """Fichero de papelera del usuario: al lado de su base de datos.

    Devuelve None cuando la sesión no está sobre un fichero (los tests corren en
    memoria), y entonces la papelera simplemente no guarda nada.
    """
    try:
        fichero = session.get_bind().url.database
    except (AttributeError, SQLAlchemyError):
        return None
    if not fichero or fichero == ":memory:":
        return None
    return Path(fichero).parent / NOMBRE_DEL_FICHERO


def limpiar_guardias(session) -> int:
    """Borra todas las guardias dejándolas en la papelera. Devuelve cuántas eran."""
    guardias = session.query(Guardia).all()
    _guardar_en_la_papelera(session, guardias)

    # Se borran una a una y no con un DELETE masivo: así la sesión se entera y
    # las suelta. Con el masivo se quedaba con ellas en memoria y chocaba contra
    # las guardias que después ocupasen sus números.
    for guardia in guardias:
        session.delete(guardia)
    borradas = len(guardias)
    session.commit()
    logger.info(f"Limpieza: {borradas} guardias a la papelera")
    return borradas


def hay_algo_que_deshacer(session) -> Optional[dict]:
    """Resumen de la papelera si aún está a tiempo: `momento` y `cuantas`."""
    contenido = _leer(session)
    if not contenido:
        return None
    momento = _momento_de(contenido)
    if momento is None or datetime.now(timezone.utc) - momento > timedelta(hours=HORAS_DE_VIDA):
        return None
    return {"momento": momento, "cuantas": len(contenido.get("guardias", []))}


def deshacer_la_limpieza(session) -> int:
    """Devuelve a su sitio las guardias de la papelera. Devuelve cuántas vuelven.

    Se saltan las que ya no encajan: profesor o zona borrados desde entonces, o
    una guardia que ya ocupa ese hueco. Vaciar la papelera al terminar evita que
    un segundo clic duplique nada.
    """
    contenido = _leer(session)
    if not contenido:
        return 0

    profesores = {p.id for p in session.query(Profesor.id).all()}
    zonas = {z.id for z in session.query(Zona.id).all()}
    ocupados = {
        (g.curso_id, g.fecha, g.turno, g.recreo, g.zona_id, g.profesor_id)
        for g in session.query(Guardia).all()
    }

    devueltas = 0
    for fila in contenido.get("guardias", []):
        datos = _desde_json(fila)
        if datos is None:
            continue
        if datos["profesor_id"] not in profesores or datos["zona_id"] not in zonas:
            continue
        if datos["profesor_sustituido_id"] not in profesores:
            datos["profesor_sustituido_id"] = None
        clave = (
            datos["curso_id"],
            datos["fecha"],
            datos["turno"],
            datos["recreo"],
            datos["zona_id"],
            datos["profesor_id"],
        )
        if clave in ocupados:
            continue
        session.add(Guardia(**datos))
        ocupados.add(clave)
        devueltas += 1

    session.commit()
    vaciar_la_papelera(session)
    logger.info(f"Deshecha la limpieza: {devueltas} guardias devueltas")
    return devueltas


def vaciar_la_papelera(session) -> None:
    ruta = ruta_de_la_papelera(session)
    if ruta and ruta.exists():
        ruta.unlink()


def _guardar_en_la_papelera(session, guardias) -> None:
    ruta = ruta_de_la_papelera(session)
    if ruta is None:
        return
    contenido = {
        "momento": datetime.now(timezone.utc).isoformat(),
        "guardias": [_a_json(g) for g in guardias],
    }
    try:
        ruta.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        # Sin papelera se pierde el deshacer, pero la limpieza debe seguir su curso.
        logger.warning(f"No se pudo escribir la papelera de guardias: {e}")


def _leer(session) -> Optional[dict]:
    ruta = ruta_de_la_papelera(session)
    if ruta is None or not ruta.exists():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        logger.warning(f"Papelera de guardias ilegible: {e}")
        return None


def _momento_de(contenido: dict) -> Optional[datetime]:
    try:
        momento = datetime.fromisoformat(contenido["momento"])
    except (KeyError, TypeError, ValueError):
        return None
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


def _a_json(guardia) -> dict:
    fila = {campo: getattr(guardia, campo) for campo in _CAMPOS}
    fila["fecha"] = guardia.fecha.isoformat() if guardia.fecha else None
    return fila


def _desde_json(fila: dict) -> Optional[dict]:
    from datetime import date

    try:
        # El identificador no se reutiliza: mientras la papelera esperaba, otra
        # guardia ha podido quedarse con ese número y devolverlo lo pisaría.
        datos = {campo: fila.get(campo) for campo in _CAMPOS if campo != "id"}
        datos["fecha"] = date.fromisoformat(fila["fecha"])
    except (KeyError, TypeError, ValueError):
        return None
    if datos["profesor_id"] is None or datos["zona_id"] is None:
        return None
    return datos
