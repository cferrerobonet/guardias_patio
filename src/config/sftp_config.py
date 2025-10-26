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


# Configuración SFTP (1&1 IONOS)
SFTP_CONFIG = {
    "host": os.getenv("SFTP_HOST", "home491590459.1and1-data.host"),
    "port": int(os.getenv("SFTP_PORT", "22")),
    "username": os.getenv("SFTP_USER", "u74704514"),
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
    if not SFTP_CONFIG["password"]:
        raise ValueError(
            "Falta configuración SFTP. "
            "Asegúrate de tener un archivo .env con SFTP_PASSWORD configurado."
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
