"""
Configuración SFTP para sincronización en la nube.
Lee credenciales desde variables de entorno por seguridad.
"""

import os
from pathlib import Path

# Intentar cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv

    # El .env está en la raíz del proyecto (dos niveles arriba de este archivo)
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # python-dotenv no está instalado, usar variables de entorno del sistema
    pass


def _usuario_sftp() -> str:
    """Usuario del servidor, con el nombre de variable que escribe la aplicación.

    Aquí se leía `SFTP_USER`, pero el diálogo de configuración y el widget de
    Ajustes guardan `SFTP_USERNAME`: en un equipo configurado desde la propia
    aplicación esta lectura nunca encontraba nada y caía en un valor fijo escrito
    en el código, así que el usuario que se tecleaba se ignoraba (SEC-001).

    Se acepta `SFTP_USER` como nombre antiguo porque hay equipos con las dos
    claves en su `.env`.
    """
    return os.getenv("SFTP_USERNAME", "") or os.getenv("SFTP_USER", "")


#: Sin valores por defecto: el servidor y el usuario del centro estaban escritos
#: aquí, y este repositorio es público y se compila dentro de cada instalador.
#: Faltando alguno, `validate_sftp_config()` devuelve False y la aplicación pide
#: la configuración en vez de intentar conectarse a un servidor ajeno.
SFTP_CONFIG = {
    "host": os.getenv("SFTP_HOST", ""),
    "port": int(os.getenv("SFTP_PORT", "22")),
    "username": _usuario_sftp(),
    "password": os.getenv("SFTP_PASSWORD", ""),
    "base_dir": os.getenv("SFTP_BASE_DIR", "/aplicaciones/guardias_patio"),
}


def get_sftp_config() -> dict:
    """
    Obtiene la configuración SFTP.

    Returns:
        dict: Configuración con host, port, username, password, base_dir

    Raises:
        ValueError: Si falta la contraseña
    """
    faltan = [c for c in ("host", "username", "password") if not SFTP_CONFIG[c]]
    if faltan:
        raise ValueError(
            "Falta configuración SFTP: " + ", ".join(faltan) + ". "
            "Configúralo en Ajustes → Servidor de sincronización."
        )

    return SFTP_CONFIG.copy()


def validate_sftp_config() -> bool:
    """
    Valida que la configuración SFTP esté completa.

    Returns:
        bool: True si la configuración es válida
    """
    try:
        config = get_sftp_config()
        required_fields = ["host", "username", "password"]
        return all(config.get(field) for field in required_fields)
    except ValueError:
        return False
