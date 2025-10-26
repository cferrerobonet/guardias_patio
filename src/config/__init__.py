"""
Módulo de configuración centralizada.

Proporciona acceso a settings de la aplicación mediante Pydantic.
"""

from .settings import get_settings, settings
from .sftp_config import SFTP_CONFIG, get_sftp_config, validate_sftp_config

__all__ = [
    "settings",
    "get_settings",
    "get_sftp_config",
    "validate_sftp_config",
    "SFTP_CONFIG"
]
