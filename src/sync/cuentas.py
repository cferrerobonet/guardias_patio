"""La ficha de cuenta que vive en el servidor, junto a los datos del usuario.

Se separa de `sync_manager.py` por lo mismo que los backends: aquel módulo
pasaba de las 1.200 líneas mezclando el transporte, las cuentas y la lógica de
cuándo subir (COD-008). Aquí sólo está leer y publicar la ficha de una cuenta,
que es lo que permite entrar desde cualquier equipo.
"""

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from sync.backends import SyncBackend

logger = logging.getLogger(__name__)


def _ruta_temporal_segura(sufijo: str = ".json") -> Path:
    """Devuelve la ruta de un temporal ya creado, sólo accesible por su dueño.

    `tempfile.mktemp()` sólo inventaba un nombre: entre que lo devolvía y se
    escribía en él, cualquiera podía dejar ahí un enlace simbólico apuntando a
    otro sitio. `mkstemp()` crea el fichero en el mismo acto (SEC-003).
    """
    descriptor, ruta = tempfile.mkstemp(suffix=sufijo)
    os.close(descriptor)
    return Path(ruta)


def hash_username(username: str) -> str:
    """
    Identificador de carpeta para un usuario.

    Es el mismo cálculo en todas partes: la carpeta del servidor, la base de datos
    local y el fichero de bloqueo tienen que coincidir.
    """
    return hashlib.sha256(username.encode()).hexdigest()[:16]


def remote_account_path(username: str) -> str:
    """Ruta del fichero de cuenta dentro de la carpeta del usuario en el servidor."""
    return f"users/{hash_username(username)}/cuenta.json"


class RemoteAccounts:
    """
    Cuentas guardadas junto a los datos, en el servidor.

    Es lo que permite entrar con el mismo usuario y contraseña desde cualquier
    equipo, y lo que impide que alguien se apropie del nombre de otro: si la
    cuenta ya existe en el servidor, no se puede volver a registrar.
    """

    def __init__(self, backend: "SyncBackend"):
        self.backend = backend

    def fetch(self, username: str) -> Optional[dict]:
        """Devuelve la ficha de la cuenta, o None si no existe o no hay conexión."""
        remote_path = remote_account_path(username)
        tmp_path = _ruta_temporal_segura(".json")
        try:
            if not self.backend.file_exists(remote_path):
                return None
            if not self.backend.download_file(remote_path, tmp_path):
                return None
            return json.loads(tmp_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"No se pudo leer la cuenta del servidor: {e}")
            return None
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def has_data(self, username: str) -> bool:
        """
        ¿Esa cuenta ya tiene datos en el servidor?

        Sirve para las cuentas antiguas, creadas antes de que la ficha se guardara
        en el servidor: existe su carpeta con datos pero no hay contraseña con la
        que comprobar quién es. En ese caso no se puede dejar registrar el nombre,
        porque bastaría con saberlo para llevarse los datos de otra persona.
        """
        try:
            return self.backend.file_exists(
                f"users/{hash_username(username)}/guardias_patio_data.json"
            )
        except (OSError, ValueError, RuntimeError):
            return False

    def publish(self, username: str, ficha: dict) -> bool:
        """Guarda la ficha de la cuenta en el servidor."""
        remote_path = remote_account_path(username)
        tmp_path = _ruta_temporal_segura(".json")
        try:
            publicable = {
                "username": username,
                "password_hash": ficha.get("password_hash"),
                "email": ficha.get("email", ""),
                "created_at": ficha.get("created_at"),
                "updated_at": datetime.now().isoformat(),
            }
            tmp_path.write_text(json.dumps(publicable, indent=2), encoding="utf-8")
            return self.backend.upload_file(tmp_path, remote_path)
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"No se pudo publicar la cuenta en el servidor: {e}")
            return False
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
