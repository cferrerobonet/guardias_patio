"""Huella del servidor SSH: comprobarla, mostrarla y confiar en ella (SEC-008).

La conexión rechaza los servidores que no estén en `~/.ssh/known_hosts`, que es lo
correcto, pero un equipo nuevo no tiene ese fichero y la única pista —«ejecuta
`ssh-keyscan`»— quedaba en el registro. Aquí está lo que hace falta para
enseñarle la huella a quien está delante y anotarla si la confirma.
"""

import base64
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def ruta_known_hosts() -> Path:
    return Path.home() / ".ssh" / "known_hosts"


def _entrada(host: str, port: int) -> str:
    """SSH escribe el puerto no estándar entre corchetes."""
    return host if int(port) == 22 else f"[{host}]:{int(port)}"


def huella_sha256(clave) -> str:
    """El mismo formato que enseña `ssh` al conectar: `SHA256:…`."""
    digest = hashlib.sha256(clave.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def esta_confiado(host: str, port: int = 22, ruta: Optional[Path] = None) -> bool:
    """¿Está ya este servidor en el fichero de servidores conocidos?"""
    import paramiko

    fichero = ruta or ruta_known_hosts()
    if not fichero.exists():
        return False
    try:
        conocidos = paramiko.HostKeys(str(fichero))
    except (OSError, ValueError) as e:
        logger.warning(f"No se pudo leer {fichero}: {e}")
        return False
    return conocidos.lookup(_entrada(host, port)) is not None


def clave_del_servidor(host: str, port: int = 22, timeout: int = 15) -> Tuple[str, object]:
    """Pregunta al servidor por su clave pública. Devuelve `(tipo, clave)`.

    No confía en ella: sólo la trae para poder enseñarla. Quien está delante
    decide si es la que espera.
    """
    import paramiko

    from sync.backends import ERRORES_DE_TRANSPORTE

    transport = paramiko.Transport((host, int(port)))
    try:
        transport.start_client(timeout=timeout)
        clave = transport.get_remote_server_key()
        return clave.get_name(), clave
    finally:
        try:
            transport.close()
        except ERRORES_DE_TRANSPORTE:
            pass  # cerrar nunca debe tapar el error de arriba


def confiar(host: str, port: int, clave, ruta: Optional[Path] = None) -> bool:
    """Anota la clave en el fichero de servidores conocidos. Devuelve si pudo."""
    import paramiko

    fichero = ruta or ruta_known_hosts()
    try:
        fichero.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        conocidos = paramiko.HostKeys(str(fichero)) if fichero.exists() else paramiko.HostKeys()
        conocidos.add(_entrada(host, port), clave.get_name(), clave)
        conocidos.save(str(fichero))
        fichero.chmod(0o600)
        logger.info(f"Servidor {_entrada(host, port)} añadido a {fichero}")
        return True
    except (OSError, ValueError) as e:
        logger.error(f"No se pudo guardar la clave del servidor en {fichero}: {e}")
        return False
