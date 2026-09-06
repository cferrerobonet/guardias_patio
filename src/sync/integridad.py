"""Huella del volcado que viaja junto a los datos (SYNC-020).

Un fichero truncado que conserve una sección válida pasaba la comprobación
estructural. Con la huella, quien descarga sabe si lo que ha llegado es lo que
se subió. La huella lleva el número de versión al que pertenece: si no coincide
con el del volcado es la huella la que se quedó atrás, no los datos, y se ignora.
Subirla y comprobarla son extras: nunca impiden subir, y sólo impiden aceptar
una descarga cuando hay huella de esa misma versión y no cuadra.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from sync.cuentas import _ruta_temporal_segura

logger = logging.getLogger(__name__)

NOMBRE_HUELLA = "guardias_patio_data.json.sha256"


def huella_del_fichero(ruta: Path) -> str:
    """SHA-256 de los bytes tal cual: sirve para saber si llegó entero."""
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def publicar_huella(gestor, volcado: Path, version: int) -> None:
    """Deja en el servidor la huella del volcado recién subido.

    `gestor` es el `SyncManager`: aporta el backend, la carpeta local y la ruta remota.
    """
    ruta_local = gestor.local_data_dir / NOMBRE_HUELLA
    remota = gestor.get_remote_path(NOMBRE_HUELLA)
    try:
        ruta_local.write_text(
            json.dumps(
                {
                    "sync_version": version,
                    "sha256": huella_del_fichero(volcado),
                    "bytes": volcado.stat().st_size,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        if not gestor.backend.upload_file(ruta_local, remota):
            logger.warning("No se pudo subir la huella del volcado")
    except (OSError, ValueError, RuntimeError) as e:
        logger.warning(f"No se pudo subir la huella del volcado: {e}")


def comprobar_descarga(gestor, descargado: Path, version: int) -> Optional[str]:
    """Motivo si lo descargado no coincide con su huella; None si vale o no hay huella."""
    backend = gestor.backend
    remota = gestor.get_remote_path(NOMBRE_HUELLA)
    tmp = _ruta_temporal_segura(".sha256")
    try:
        if not backend.file_exists(remota) or not backend.download_file(remota, tmp):
            logger.info("El servidor no tiene huella del volcado; se comprueba por estructura")
            return None
        datos = json.loads(tmp.read_text(encoding="utf-8"))
        esperada = str(datos.get("sha256", ""))
        if int(datos.get("sync_version", -1)) != version or not esperada:
            logger.warning("La huella del servidor es de otra versión; se ignora")
            return None
    except (OSError, ValueError, TypeError, RuntimeError) as e:
        logger.warning(f"No se pudo leer la huella del servidor ({e}); se ignora")
        return None
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    if huella_del_fichero(descargado) == esperada:
        return None
    return (
        "Los datos descargados no coinciden con la huella que dejó la última "
        "subida: el fichero del servidor está dañado o incompleto"
    )
