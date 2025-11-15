"""
Sistema de Sincronización Multi-Usuario
========================================

Gestiona la sincronización de datos entre la aplicación local y la nube.
Soporta múltiples usuarios con datos aislados.
"""

import hashlib
import json
import logging
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.paths import get_data_directory, get_user_data_directory

# Configurar logger
logger = logging.getLogger(__name__)


class SyncBackend(ABC):
    """Interfaz abstracta para backends de sincronización."""

    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Sube un archivo a la nube."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Descarga un archivo de la nube."""
        pass

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """Verifica si un archivo existe en la nube."""
        pass

    @abstractmethod
    def get_last_modified(self, remote_path: str) -> Optional[datetime]:
        """Obtiene la fecha de última modificación."""
        pass


class LocalSyncBackend(SyncBackend):
    """
    Backend de sincronización usando carpeta local compartida.
    Útil para redes locales o testing.
    """

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalSyncBackend inicializado: {self.base_path}")

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        try:
            dest = self.base_path / remote_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest)
            logger.info(f"Archivo subido: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Error subiendo archivo: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        try:
            source = self.base_path / remote_path
            if not source.exists():
                return False
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, local_path)
            logger.info(f"Archivo descargado: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Error descargando archivo: {e}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        return (self.base_path / remote_path).exists()

    def get_last_modified(self, remote_path: str) -> Optional[datetime]:
        path = self.base_path / remote_path
        if path.exists():
            return datetime.fromtimestamp(path.stat().st_mtime)
        return None


class SFTPSyncBackend(SyncBackend):
    """
    Backend de sincronización usando SFTP con verificación de host key.
    Requiere: pip install paramiko

    SEGURIDAD:
    - Utiliza RejectPolicy() por defecto (rechaza hosts desconocidos)
    - Carga host keys desde ~/.ssh/known_hosts
    - Para agregar un host: ssh-keyscan -H <host> >> ~/.ssh/known_hosts
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        base_dir: str = "/guardias_patio",
    ):
        try:
            import paramiko

            self.client = paramiko.SSHClient()

            # 🔒 SEGURIDAD: Cargar host keys conocidas desde archivo del sistema
            known_hosts_path = Path.home() / ".ssh" / "known_hosts"
            if known_hosts_path.exists():
                self.client.load_host_keys(str(known_hosts_path))
                logger.info(f"Host keys cargadas desde {known_hosts_path}")
            else:
                logger.warning(f"Archivo known_hosts no encontrado: {known_hosts_path}")
                logger.warning("Para agregar el host: ssh-keyscan -H <host> >> ~/.ssh/known_hosts")

            # 🔒 SEGURIDAD: Rechazar hosts desconocidos (NO AutoAddPolicy)
            # Esto previene ataques Man-in-the-Middle (MITM)
            self.client.set_missing_host_key_policy(paramiko.RejectPolicy())

            self.client.connect(host, port=port, username=username, password=password)
            self.sftp = self.client.open_sftp()
            self.base_dir = base_dir
            logger.info(f"SFTP conectado a {host}:{port} con verificación de host key ✅")
        except ImportError:
            logger.error("Paramiko no instalado. Ejecutar: pip install paramiko")
            raise
        except paramiko.SSHException as e:
            logger.error(f"Error de host key: {e}")
            logger.error("El servidor no está en known_hosts. Agregarlo con:")
            logger.error(f"  ssh-keyscan -H {host} >> ~/.ssh/known_hosts")
            raise
        except Exception as e:
            logger.error(f"Error conectando SFTP: {e}")
            raise

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        try:
            full_path = f"{self.base_dir}/{remote_path}"
            # Crear directorios remotos si no existen
            self._mkdir_p(str(Path(full_path).parent))
            self.sftp.put(str(local_path), full_path)
            logger.info(f"Archivo subido vía SFTP: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Error subiendo vía SFTP: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        try:
            full_path = f"{self.base_dir}/{remote_path}"
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.sftp.get(full_path, str(local_path))
            logger.info(f"Archivo descargado vía SFTP: {remote_path}")
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error descargando vía SFTP: {e}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        try:
            full_path = f"{self.base_dir}/{remote_path}"
            self.sftp.stat(full_path)
            return True
        except FileNotFoundError:
            return False

    def get_last_modified(self, remote_path: str) -> Optional[datetime]:
        try:
            full_path = f"{self.base_dir}/{remote_path}"
            stat = self.sftp.stat(full_path)
            return datetime.fromtimestamp(stat.st_mtime)
        except Exception:
            return None

    def _mkdir_p(self, remote_dir: str):
        """Crea directorios remotos recursivamente."""
        if remote_dir == "/":
            return
        try:
            self.sftp.stat(remote_dir)
        except FileNotFoundError:
            self._mkdir_p(str(Path(remote_dir).parent))
            self.sftp.mkdir(remote_dir)

    def close(self):
        """Cierra la conexión SFTP."""
        if hasattr(self, "sftp"):
            self.sftp.close()
        if hasattr(self, "client"):
            self.client.close()


class SyncManager:
    """
    Gestor principal de sincronización multi-usuario.
    """

    def __init__(self, backend: SyncBackend, user_id: str):
        self.backend = backend
        self.user_id = user_id
        self.user_hash = self._hash_user_id(user_id)
        self.local_data_dir = get_user_data_directory() / self.user_hash
        self.local_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SyncManager inicializado para usuario: {user_id}")

    def _hash_user_id(self, user_id: str) -> str:
        """Genera un hash del user_id para nombres de archivo."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]

    def get_remote_path(self, filename: str) -> str:
        """Obtiene la ruta remota para un archivo del usuario."""
        return f"users/{self.user_hash}/{filename}"

    def sync_on_startup(self, session=None) -> bool:
        """
        Sincroniza datos al iniciar la aplicación.
        Descarga el JSON de la nube y lo importa a la base de datos.

        Args:
            session: Sesión de SQLAlchemy (opcional, para importar datos)
        """
        logger.info("Iniciando sincronización de inicio...")

        # Archivo JSON con todos los datos
        json_filename = "guardias_patio_data.json"
        local_json_path = self.local_data_dir / json_filename
        remote_path = self.get_remote_path(json_filename)

        success = True

        if self.backend.file_exists(remote_path):
            # Archivo existe en la nube
            remote_modified = self.backend.get_last_modified(remote_path)
            local_modified = None

            if local_json_path.exists():
                local_modified = datetime.fromtimestamp(local_json_path.stat().st_mtime)

            # Descargar si no existe localmente o si el remoto es más nuevo
            if not local_modified or (remote_modified and remote_modified > local_modified):
                logger.info("📥 Descargando datos actualizados desde la nube...")
                if self.backend.download_file(remote_path, local_json_path):
                    logger.info(f"✓ Datos descargados a {local_json_path}")

                    # Importar JSON a la base de datos si se proporciona session
                    if session:
                        from sync.data_exporter import DataExporter
                        logger.info("📊 Importando datos a la base de datos local...")
                        if DataExporter.import_from_json(
                            session, local_json_path, clear_existing=False
                        ):
                            logger.info("✅ Datos importados exitosamente")
                        else:
                            logger.error("❌ Error al importar datos")
                            success = False
                else:
                    success = False
            else:
                logger.info("✓ Datos locales están actualizados")
        else:
            logger.info("ℹ️  No hay datos en la nube aún")

        # Guardar timestamp de última sincronización
        self._save_sync_metadata()

        return success

    def sync_on_shutdown(self, session=None, progress_callback=None) -> bool:
        """
        Sincroniza datos al cerrar la aplicación.
        Exporta la base de datos a JSON y la sube a la nube.

        Args:
            session: Sesión de SQLAlchemy (obligatorio, para exportar datos)
            progress_callback: Función callback para reportar progreso
                               Debe aceptar (step: str, details: dict)
        """
        logger.info("Iniciando sincronización de cierre...")

        # Exportar base de datos a JSON
        json_filename = "guardias_patio_data.json"
        local_json_path = self.local_data_dir / json_filename

        if session:
            from sync.data_exporter import DataExporter
            logger.info("📤 Exportando base de datos a JSON...")

            if progress_callback:
                progress_callback("exporting", {"message": "Exportando datos de la base de datos"})

            if not DataExporter.export_to_json(session, local_json_path):
                logger.error("❌ Error al exportar datos a JSON")
                if progress_callback:
                    progress_callback("error", {"message": "Error al exportar datos"})
                return False
            logger.info("✓ Datos exportados exitosamente")
        else:
            logger.warning("⚠️  No se proporcionó sesión de base de datos, omitiendo exportación")
            if not local_json_path.exists():
                logger.error("❌ No hay datos JSON para sincronizar")
                if progress_callback:
                    progress_callback("error", {"message": "No hay datos para sincronizar"})
                return False

        # Obtener tamaño del archivo para mostrar en progreso
        file_size_kb = 0
        if local_json_path.exists():
            file_size_kb = local_json_path.stat().st_size // 1024

        # Conectar al servidor
        if progress_callback:
            progress_callback("connecting", {"message": "Conectando al servidor SFTP"})

        # Subir JSON a la nube
        success = True
        if local_json_path.exists():
            remote_path = self.get_remote_path(json_filename)
            logger.info("☁️  Subiendo datos a la nube...")

            if progress_callback:
                progress_callback("uploading", {
                    "message": "Subiendo archivo a la nube",
                    "file_size_kb": file_size_kb
                })

            if self.backend.upload_file(local_json_path, remote_path):
                logger.info("✅ Datos sincronizados con la nube")
                if progress_callback:
                    progress_callback("complete", {"message": "Sincronización completada"})
            else:
                logger.error("❌ Error al subir datos a la nube")
                success = False
                if progress_callback:
                    progress_callback("error", {"message": "Error al subir datos a la nube"})
        else:
            logger.warning(f"❌ {json_filename} no existe localmente")
            success = False
            if progress_callback:
                progress_callback("error", {"message": f"{json_filename} no existe"})

        # Guardar timestamp de última sincronización
        self._save_sync_metadata()

        return success

    def _save_sync_metadata(self):
        """Guarda metadata de sincronización."""
        metadata = {
            "user_id": self.user_id,
            "user_hash": self.user_hash,
            "last_sync": datetime.now().isoformat(),
        }

        metadata_path = self.local_data_dir / "last_sync.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # También subir metadata a la nube
        remote_path = self.get_remote_path("last_sync.json")
        self.backend.upload_file(metadata_path, remote_path)

    def manual_sync(self) -> bool:
        """Sincronización manual (botón en la UI)."""
        logger.info("Sincronización manual iniciada")
        # Primero descargar cambios remotos
        self.sync_on_startup()
        # Luego subir cambios locales
        return self.sync_on_shutdown()


# ============== SISTEMA DE AUTENTICACIÓN SIMPLE ==============


class UserAuth:
    """
    Sistema simple de autenticación de usuarios.
    En producción, usar bcrypt/argon2 para passwords.
    """

    def __init__(self, users_file: Path = None):
        # Si no se especifica, usar el directorio de datos de la aplicación
        if users_file is None:
            from core.paths import get_data_directory
            users_file = get_data_directory() / "users.json"
        self.users_file = users_file
        self.users = self._load_users()

    def _load_users(self) -> dict:
        """Carga usuarios desde archivo."""
        if self.users_file.exists():
            with open(self.users_file) as f:
                return json.load(f)
        return {}

    def _save_users(self):
        """Guarda usuarios en archivo."""
        with open(self.users_file, "w") as f:
            json.dump(self.users, f, indent=2)

    def register_user(self, username: str, password: str, email: str = "") -> bool:
        """Registra un nuevo usuario."""
        if username in self.users:
            logger.warning(f"Usuario {username} ya existe")
            return False

        # En producción usar bcrypt:
        # import bcrypt
        # password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        self.users[username] = {
            "password_hash": password_hash,
            "email": email,
            "created_at": datetime.now().isoformat(),
        }

        self._save_users()
        logger.info(f"Usuario registrado: {username}")
        return True

    def authenticate(self, username: str, password: str) -> bool:
        """Autentica un usuario."""
        if username not in self.users:
            return False

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return self.users[username]["password_hash"] == password_hash

    def unregister_user(self, username: str) -> bool:
        """
        Elimina un usuario del sistema de autenticación.

        Args:
            username: Nombre del usuario a eliminar

        Returns:
            bool: True si se eliminó correctamente, False si no existe
        """
        if username not in self.users:
            logger.warning(f"Usuario {username} no existe")
            return False

        del self.users[username]
        self._save_users()
        logger.info(f"Usuario eliminado del sistema de autenticación: {username}")
        return True
