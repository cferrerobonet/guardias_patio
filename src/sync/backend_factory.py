"""
Factory para crear backends de sincronización según configuración.
"""

import logging

from config import get_sftp_config, validate_sftp_config
from core.paths import get_data_directory
from sync.sync_manager import LocalSyncBackend, SFTPSyncBackend, SyncBackend

logger = logging.getLogger(__name__)


def create_sync_backend(backend_type: str = "sftp") -> SyncBackend:
    """
    Crea un backend de sincronización según el tipo especificado.

    Args:
        backend_type: Tipo de backend ('local' o 'sftp')

    Returns:
        SyncBackend configurado

    Raises:
        ValueError: Si la configuración es inválida
        ImportError: Si faltan dependencias
    """
    if backend_type == "local":
        # Backend local para desarrollo/testing
        # NOTA: Solo se usa si SFTP no está configurado
        # Usa el directorio data/ del proyecto para evitar duplicación
        local_path = get_data_directory()
        logger.info(f"Creando LocalSyncBackend en: {local_path}")
        return LocalSyncBackend(local_path)

    elif backend_type == "sftp":
        # Backend SFTP para producción
        if not validate_sftp_config():
            raise ValueError(
                "Configuración SFTP incompleta. "
                "Verifica que exista el archivo .env con las credenciales."
            )

        try:
            import paramiko
        except ImportError:
            raise ImportError("Paramiko no está instalado. Ejecuta: pip install paramiko")

        config = get_sftp_config()
        logger.info(f"Creando SFTPSyncBackend para {config['host']}")

        return SFTPSyncBackend(
            host=config["host"],
            port=config["port"],
            username=config["username"],
            password=config["password"],
            base_dir=config["base_dir"],
        )

    else:
        raise ValueError(f"Backend desconocido: {backend_type}")


class SyncConfigurationError(RuntimeError):
    """
    No se puede sincronizar con el servidor.

    Se lanza tanto si no hay configuración como si la hay pero no sirve. Nunca se
    sustituye por un almacenamiento local a espaldas del usuario: una app que dice
    haber guardado en la nube cuando no lo ha hecho pierde datos sin que nadie se
    entere.
    """


def get_default_backend() -> SyncBackend:
    """
    Devuelve el backend de sincronización con el servidor.

    Returns:
        SyncBackend contra el servidor configurado.

    Raises:
        SyncConfigurationError: si no hay servidor configurado o no se puede usar.
            Quien llama decide qué hacer, y debe decírselo al usuario.
    """
    if not validate_sftp_config():
        raise SyncConfigurationError(
            "No hay servidor de sincronización configurado. "
            "Revisa los datos de conexión en Ajustes."
        )

    try:
        return create_sync_backend("sftp")
    except (ConnectionError, OSError, ValueError, RuntimeError, ImportError) as e:
        logger.error(f"No se pudo crear el backend SFTP: {e}", exc_info=True)
        raise SyncConfigurationError(
            f"No se puede conectar con el servidor de sincronización: {e}"
        ) from e
