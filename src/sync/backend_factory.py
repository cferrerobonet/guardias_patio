"""
Factory para crear backends de sincronización según configuración.
"""

import logging
from pathlib import Path

from config import get_sftp_config, validate_sftp_config

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
        # El directorio se crea automáticamente si es necesario
        local_path = Path("cloud_storage_local")
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
            raise ImportError(
                "Paramiko no está instalado. "
                "Ejecuta: pip install paramiko"
            )

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


def get_default_backend() -> SyncBackend:
    """
    Obtiene el backend por defecto (SFTP si está configurado, sino Local).

    Returns:
        SyncBackend configurado
    """
    try:
        # Intentar usar SFTP si está configurado
        if validate_sftp_config():
            logger.info("✓ Configuración SFTP válida. Creando backend SFTP...")
            return create_sync_backend("sftp")
        else:
            logger.warning("⚠ Configuración SFTP no válida")
    except Exception as e:
        logger.error(f"❌ Error al crear backend SFTP: {e}", exc_info=True)

    # Fallback a local
    logger.warning("⚠ Usando backend local como fallback (NO se sincronizará con la nube)")
    return create_sync_backend("local")
