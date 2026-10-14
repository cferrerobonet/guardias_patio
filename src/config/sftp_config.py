"""
Configuración SFTP para sincronización en la nube.
Lee credenciales desde variables de entorno por seguridad.
"""

import os
from pathlib import Path


def _rutas_candidatas() -> "list[Path]":
    """Dónde se busca el `.env`, por orden y sin adivinar.

    Primero la carpeta de datos del usuario, que es donde lo dejan el diálogo de
    configuración inicial y Ajustes, y el único sitio escribible cuando la
    aplicación está empaquetada. Después la raíz del proyecto, que es lo que hay
    en desarrollo. Nunca se busca a partir del directorio actual: dependiendo de
    desde dónde se lance la aplicación podría acabar leyendo un fichero ajeno.
    """
    rutas: "list[Path]" = []
    try:
        from core.paths import get_base_directory

        rutas.append(get_base_directory() / ".env")
    except (ImportError, OSError):
        pass
    rutas.append(Path(__file__).parent.parent.parent / ".env")
    return rutas


def _ruta_del_env() -> Path:
    """El `.env` de esta instalación: el primero de los sitios donde se busca."""
    return _rutas_candidatas()[0]


def _cargar_env() -> None:
    """Trae el `.env` al entorno. Lo ya definido fuera manda, para no pisar tests."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return  # sin python-dotenv se usan las variables del sistema

    for ruta in _rutas_candidatas():
        if ruta.exists():
            load_dotenv(ruta)
            return


def _contrasena_sftp() -> str:
    """La contraseña del servidor, del llavero del sistema si está ahí."""
    from core.credenciales import obtener

    return obtener("SFTP_PASSWORD")


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
def leer_configuracion() -> dict:
    """La configuración tal y como está **ahora**, no como estaba al importar.

    Congelarla en un diccionario al importar dejaba la aplicación empaquetada
    creyendo que no había servidor: este módulo se importa antes de que nadie
    haya leído el `.env` de la carpeta del usuario, así que se quedaba con los
    valores vacíos para toda la sesión y avisaba de que no había nube aunque
    estuviera configurada.
    """
    _cargar_env()
    try:
        puerto = int(os.getenv("SFTP_PORT", "22") or "22")
    except ValueError:
        puerto = 22
    return {
        "host": os.getenv("SFTP_HOST", ""),
        "port": puerto,
        "username": _usuario_sftp(),
        # Del llavero del sistema; el `.env` solo como respaldo (SEC-001).
        "password": _contrasena_sftp(),
        "base_dir": os.getenv("SFTP_BASE_DIR", "/aplicaciones/guardias_patio"),
    }


#: Foto de la configuración al importar. Se conserva porque hay código y tests
#: que la leen, pero quien necesite el valor de verdad usa `get_sftp_config()`.
SFTP_CONFIG = leer_configuracion()


def get_sftp_config() -> dict:
    """
    Obtiene la configuración SFTP.

    Returns:
        dict: Configuración con host, port, username, password, base_dir

    Raises:
        ValueError: Si falta la contraseña
    """
    config = leer_configuracion()
    faltan = [c for c in ("host", "username", "password") if not config[c]]
    if faltan:
        raise ValueError(
            "Falta configuración SFTP: " + ", ".join(faltan) + ". "
            "Configúralo en Ajustes → Servidor de sincronización."
        )

    return config


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
