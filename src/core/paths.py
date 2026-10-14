"""
Gestión centralizada de rutas del sistema.

Proporciona funciones para obtener directorios apropiados según el sistema operativo,
compatibles con aplicaciones empaquetadas y en desarrollo.

⚠️ CRÍTICO: Este módulo es ESENCIAL para que la aplicación funcione correctamente
cuando se compila con PyInstaller.

REGLA DE ORO:
    SIEMPRE usar las funciones de este módulo para obtener rutas de archivos.
    NUNCA usar rutas relativas hardcodeadas como "logs/", "data/", "imagenes/".

Funciones disponibles:
    - get_base_directory()       → Directorio base de la app
    - get_data_directory()       → Datos (bases de datos, users.json)
    - get_logs_directory()       → Logs del sistema
    - get_resources_directory()  → Recursos (imágenes, iconos)
    - get_user_data_directory()  → Datos específicos por usuario

Documentación completa: documentacion/SOLUCION_COMPILACION.md
"""

import os
import platform
import stat
import sys
from pathlib import Path


def get_base_directory() -> Path:
    """
    Obtiene el directorio base de la aplicación.

    En desarrollo: directorio del proyecto
    En producción: Application Support en macOS, AppData en Windows, etc.

    Returns:
        Path: Directorio base apropiado
    """
    system = platform.system()

    # Detectar si estamos en una aplicación empaquetada
    if getattr(sys, "frozen", False):
        # Aplicación empaquetada (PyInstaller)
        if system == "Darwin":  # macOS
            base_dir = Path.home() / "Library" / "Application Support" / "GuardiasDePatio"
        elif system == "Windows":
            app_data = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            base_dir = Path(app_data) / "GuardiasDePatio"
        else:  # Linux y otros
            base_dir = Path.home() / ".local" / "share" / "GuardiasDePatio"
    else:
        # Modo desarrollo: usar directorio del proyecto
        # Subir desde src/ hasta la raíz del proyecto
        base_dir = Path(__file__).parent.parent.parent

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_data_directory() -> Path:
    """
    Obtiene el directorio para almacenar datos de la aplicación.

    Returns:
        Path: Directorio de datos
    """
    if getattr(sys, "frozen", False):
        # En producción, usar el directorio base
        data_dir = get_base_directory() / "data"
    else:
        # En desarrollo, usar data/ en el directorio del proyecto
        data_dir = get_base_directory() / "data"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_directory() -> Path:
    """
    Obtiene el directorio para almacenar logs.

    Returns:
        Path: Directorio de logs
    """
    if getattr(sys, "frozen", False):
        # En producción, usar el directorio base
        logs_dir = get_base_directory() / "logs"
    else:
        # En desarrollo, usar logs/ en el directorio del proyecto
        logs_dir = get_base_directory() / "logs"

    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_user_data_directory() -> Path:
    """
    Obtiene el directorio para datos de usuarios.

    Returns:
        Path: Directorio de datos de usuarios
    """
    user_data_dir = get_data_directory() / "users"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    return user_data_dir


def get_resources_directory() -> Path:
    """
    Obtiene el directorio de recursos (imágenes, iconos, etc.).

    En producción, los recursos se incluyen en el bundle.
    En desarrollo, se usan desde el directorio del proyecto.

    Returns:
        Path: Directorio de recursos
    """
    if getattr(sys, "frozen", False):
        # En PyInstaller, los recursos están en _MEIPASS
        if hasattr(sys, "_MEIPASS"):
            resources_dir = Path(sys._MEIPASS) / "imagenes"
        else:
            # Fallback: usar Contents/Resources en macOS
            if platform.system() == "Darwin":
                app_path = Path(sys.executable).parent.parent
                resources_dir = app_path / "Resources" / "imagenes"
            else:
                resources_dir = Path(sys.executable).parent / "imagenes"
    else:
        # En desarrollo
        resources_dir = get_base_directory() / "imagenes"

    return resources_dir


def get_database_path() -> Path:
    """
    Obtiene la ruta al archivo de base de datos.

    Returns:
        Path: Ruta al archivo de base de datos
    """
    return get_data_directory() / "guardias_patio.db"


__all__ = [
    "get_base_directory",
    "get_data_directory",
    "get_logs_directory",
    "get_user_data_directory",
    "get_resources_directory",
    "get_database_path",
    "proteger_fichero_de_credenciales",
]


def proteger_fichero_de_credenciales(ruta: Path) -> None:
    """Deja el fichero accesible sólo por su dueño (SEC-001).

    El `.env` guarda las contraseñas de SFTP y de correo en claro. Se creaba con
    los permisos por defecto, así que en un equipo compartido cualquier otra
    cuenta podía leerlo. Mientras las credenciales no pasen al almacén de claves
    del sistema, al menos que el fichero no esté abierto de par en par.

    En Windows los permisos POSIX no aplican; ahí la protección la da el propio
    perfil de usuario, así que el fallo se ignora en silencio.
    """
    try:
        os.chmod(ruta, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except (OSError, NotImplementedError):
        pass
