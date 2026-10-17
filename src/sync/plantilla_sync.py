"""La plantilla de los avisos viaja con la sincronización (GUA-CON-004).

Hasta la 7.5.1 se guardaba solo en el equipo donde se editaba. Ahora va dentro
del volcado que se sube a la nube, con la fecha de su última edición, y al
descargar gana la edición más reciente:

- si la nube no trae plantilla (volcado de una versión anterior), el equipo
  conserva la suya y la sube en la próxima sincronización;
- si la local es igual de reciente o más, se queda la local;
- si la de la nube es más reciente, sustituye a la local, y la local se guarda
  antes en `plantilla_avisos.anterior.json`: ningún equipo pierde la suya.

Una plantilla guardada antes de la 7.5.2 no tiene fecha de edición: vale la de
modificación del fichero.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from core.logging import get_logger
from services import plantilla_avisos
from services.plantilla_avisos import Plantilla

logger = get_logger(__name__)

CLAVE = "plantilla_avisos"


def _fecha(valor) -> Optional[datetime]:
    if not isinstance(valor, str) or not valor:
        return None
    try:
        fecha = datetime.fromisoformat(valor)
    except ValueError:
        return None
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def _plantilla_de(datos) -> Optional[Plantilla]:
    """La plantilla de un diccionario, o None si no es una plantilla válida."""
    if not isinstance(datos, dict):
        return None
    asunto, cuerpo = datos.get("asunto"), datos.get("cuerpo")
    if not isinstance(asunto, str) or not isinstance(cuerpo, str):
        return None
    serie = Plantilla()
    plantilla = Plantilla(
        asunto=asunto,
        cuerpo=cuerpo,
        adjuntar_pdf=bool(datos.get("adjuntar_pdf", serie.adjuntar_pdf)),
        adjuntar_ical=bool(datos.get("adjuntar_ical", serie.adjuntar_ical)),
    )
    return None if plantilla.errores() else plantilla


def _local() -> Optional[tuple[Plantilla, datetime, str]]:
    """La plantilla de este equipo, su fecha de edición y el texto del fichero."""
    ruta = plantilla_avisos._ruta()
    try:
        texto = ruta.read_text(encoding="utf-8")
        modificada = ruta.stat().st_mtime
        datos = json.loads(texto)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        logger.warning(f"No se pudo leer la plantilla de avisos de este equipo: {e}")
        return None
    plantilla = _plantilla_de(datos)
    if plantilla is None:
        return None
    editada = _fecha(datos.get("editada")) or datetime.fromtimestamp(modificada, timezone.utc)
    return plantilla, editada, texto


def para_exportar() -> Optional[dict]:
    """Lo que se sube con el volcado; None si este equipo no tiene plantilla propia."""
    local = _local()
    if local is None:
        return None
    plantilla, editada, _ = local
    return {**asdict(plantilla), "editada": editada.isoformat()}


def aplicar_descargada(datos) -> bool:
    """Aplica la plantilla de la nube si es más reciente que la local.

    Devuelve True si la ha sustituido. Nunca lanza: un fallo aquí no puede
    estropear la sincronización.
    """
    if datos is None:
        return False
    remota = _plantilla_de(datos)
    editada_remota = _fecha(datos.get("editada")) if isinstance(datos, dict) else None
    if remota is None or editada_remota is None:
        logger.warning("La plantilla de avisos de la nube no es válida; se conserva la local")
        return False
    local = _local()
    if local is not None:
        plantilla_local, editada_local, texto_local = local
        if editada_local >= editada_remota:
            return False
        if plantilla_local == remota:
            return False
    ruta = plantilla_avisos._ruta()
    try:
        if local is not None:
            ruta.with_name("plantilla_avisos.anterior.json").write_text(
                texto_local, encoding="utf-8"
            )
        plantilla_avisos.guardar(remota, editada=editada_remota.isoformat())
    except (OSError, ValueError) as e:
        logger.warning(f"No se pudo aplicar la plantilla de avisos de la nube: {e}")
        return False
    logger.info("Plantilla de avisos actualizada con la de la nube (edición más reciente)")
    return True
