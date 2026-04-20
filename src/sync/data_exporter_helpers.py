"""
Helpers de serialización y configuración para DataExporter.

Extraído de data_exporter.py para reducir su tamaño (ARQ-05).
"""

import base64
import logging
import os
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_FERNET_KEY_ENV = "GUARDIAS_FERNET_KEY"


# ---------------------------------------------------------------------------
# Cifrado de credenciales
# ---------------------------------------------------------------------------

def get_fernet() -> Fernet:
    """Devuelve una instancia Fernet con la clave persistente del sistema."""
    key = os.environ.get(_FERNET_KEY_ENV)
    if not key:
        key_path = Path.home() / ".guardias_patio_key"
        if key_path.exists():
            key = key_path.read_text().strip()
        else:
            key = Fernet.generate_key().decode()
            key_path.write_text(key)
            key_path.chmod(0o600)
    return Fernet(key.encode() if isinstance(key, str) else key)


def encriptar_password(password: str) -> str:
    """Encripta una contraseña usando Fernet."""
    if not password:
        return ""
    return get_fernet().encrypt(password.encode("utf-8")).decode("utf-8")


def desencriptar_password(encrypted_password: str) -> str:
    """Desencripta una contraseña Fernet; en caso de fallo intenta base64."""
    if not encrypted_password:
        return ""
    try:
        return get_fernet().decrypt(encrypted_password.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        try:
            return base64.b64decode(encrypted_password.encode("utf-8")).decode("utf-8")
        except (ValueError, TypeError, OSError):
            logger.warning("No se pudo desencriptar credencial, usando valor original.")
            return encrypted_password


# ---------------------------------------------------------------------------
# Serialización de fechas y horas
# ---------------------------------------------------------------------------

def serialize_date(obj: Any) -> str:
    """Serializa objetos date/datetime a string ISO."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Convierte string ISO a objeto date."""
    if not date_str:
        return None
    try:
        if isinstance(date_str, date):
            return date_str
        return datetime.fromisoformat(date_str).date()
    except (ValueError, AttributeError):
        logger.warning(f"No se pudo parsear fecha: {date_str}")
        return None


def parse_time(time_str: Optional[str]) -> Optional[time]:
    """Convierte string ISO a objeto time."""
    if not time_str:
        return None
    try:
        if isinstance(time_str, time):
            return time_str
        return datetime.fromisoformat(f"2000-01-01T{time_str}").time()
    except (ValueError, AttributeError):
        logger.warning(f"No se pudo parsear hora: {time_str}")
        return None


# ---------------------------------------------------------------------------
# Exportación/importación de configuración SMTP
# ---------------------------------------------------------------------------

def export_smtp_config() -> Optional[Dict[str, str]]:
    """
    Exporta la configuración SMTP desde el archivo .env.

    Esta configuración es GLOBAL y compartida entre todos los usuarios.

    Returns:
        Dict con configuración SMTP o None si no existe
    """
    from dotenv import load_dotenv

    load_dotenv()

    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = os.getenv("SMTP_PORT", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "")

    if smtp_server and smtp_port and smtp_user and smtp_password:
        return {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_password": encriptar_password(smtp_password),
            "smtp_from_name": smtp_from_name,
        }
    return None


def import_smtp_config(smtp_data: Dict[str, str]) -> bool:
    """
    Importa la configuración SMTP GLOBAL al archivo .env.

    Args:
        smtp_data: Dict con configuración SMTP

    Returns:
        True si se importó correctamente
    """
    try:
        smtp_server = smtp_data.get("smtp_server", "")
        smtp_port = smtp_data.get("smtp_port", "")
        smtp_user = smtp_data.get("smtp_user", "")
        smtp_password_encrypted = smtp_data.get("smtp_password", "")
        smtp_from_name = smtp_data.get("smtp_from_name", "Guardias de Patio")

        if not smtp_server or not smtp_port or not smtp_user or not smtp_password_encrypted:
            logger.warning("Configuración SMTP incompleta en JSON")
            return False

        smtp_password = desencriptar_password(smtp_password_encrypted)

        env_path = ".env"
        env_lines: list[str] = []

        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_lines = f.readlines()

        smtp_vars = {
            "SMTP_SERVER": smtp_server,
            "SMTP_PORT": smtp_port,
            "SMTP_USER": smtp_user,
            "SMTP_PASSWORD": smtp_password,
            "SMTP_FROM_NAME": smtp_from_name,
        }

        updated_vars: set[str] = set()
        for i, line in enumerate(env_lines):
            for var_name, var_value in smtp_vars.items():
                if line.startswith(f"{var_name}="):
                    env_lines[i] = f"{var_name}={var_value}\n"
                    updated_vars.add(var_name)

        for var_name, var_value in smtp_vars.items():
            if var_name not in updated_vars:
                env_lines.append(f"{var_name}={var_value}\n")

        with open(env_path, "w") as f:
            f.writelines(env_lines)

        logger.info("Configuración SMTP GLOBAL actualizada desde JSON")
        return True

    except (OSError, ValueError) as e:
        logger.error(f"Error al importar configuración SMTP: {e}")
        return False


# ---------------------------------------------------------------------------
# Exportación/importación de configuración SFTP
# ---------------------------------------------------------------------------

def export_sftp_config() -> Optional[Dict[str, str]]:
    """
    Exporta la configuración SFTP desde el archivo .env.

    Esta configuración es GLOBAL y compartida entre todos los usuarios.

    Returns:
        Dict con configuración SFTP o None si no existe
    """
    from dotenv import load_dotenv

    load_dotenv()

    sftp_host = os.getenv("SFTP_HOST", "")
    sftp_port = os.getenv("SFTP_PORT", "")
    sftp_basedir = os.getenv("SFTP_BASE_DIR", "")
    sftp_user = os.getenv("SFTP_USERNAME", "")
    sftp_password = os.getenv("SFTP_PASSWORD", "")

    if sftp_host and sftp_port and sftp_user and sftp_password:
        return {
            "sftp_host": sftp_host,
            "sftp_port": sftp_port,
            "sftp_base_dir": sftp_basedir,
            "sftp_username": sftp_user,
            "sftp_password": encriptar_password(sftp_password),
        }
    return None


def import_sftp_config(sftp_data: Dict[str, str]) -> bool:
    """
    Importa la configuración SFTP GLOBAL al archivo .env.

    Args:
        sftp_data: Dict con configuración SFTP

    Returns:
        True si se importó correctamente
    """
    try:
        sftp_host = sftp_data.get("sftp_host", "")
        sftp_port = sftp_data.get("sftp_port", "")
        sftp_basedir = sftp_data.get("sftp_base_dir", "")
        sftp_user = sftp_data.get("sftp_username", "")
        sftp_password_encrypted = sftp_data.get("sftp_password", "")

        if not sftp_host or not sftp_port or not sftp_user or not sftp_password_encrypted:
            logger.warning("Configuración SFTP incompleta en JSON")
            return False

        sftp_password = desencriptar_password(sftp_password_encrypted)

        env_path = ".env"
        env_lines: list[str] = []

        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_lines = f.readlines()

        sftp_vars = {
            "SFTP_HOST": sftp_host,
            "SFTP_PORT": sftp_port,
            "SFTP_BASE_DIR": sftp_basedir,
            "SFTP_USERNAME": sftp_user,
            "SFTP_PASSWORD": sftp_password,
        }

        updated_vars: set[str] = set()
        for i, line in enumerate(env_lines):
            for var_name, var_value in sftp_vars.items():
                if line.startswith(f"{var_name}="):
                    env_lines[i] = f"{var_name}={var_value}\n"
                    updated_vars.add(var_name)

        for var_name, var_value in sftp_vars.items():
            if var_name not in updated_vars:
                env_lines.append(f"{var_name}={var_value}\n")

        with open(env_path, "w") as f:
            f.writelines(env_lines)

        logger.info("Configuración SFTP GLOBAL actualizada desde JSON")
        return True

    except (OSError, ValueError) as e:
        logger.error(f"Error al importar configuración SFTP: {e}")
        return False
