"""
Sistema de Sincronización Multi-Usuario
========================================

Gestiona la sincronización de datos entre la aplicación local y la nube.
Soporta múltiples usuarios con datos aislados.
"""

import hashlib
import json
import logging
import os
import re
import shutil
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from core.paths import get_user_data_directory

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

    def _safe_path(self, remote_path: str) -> Path:
        """Resuelve la ruta y verifica que no salga de base_path (path traversal)."""
        resolved = (self.base_path / remote_path).resolve()
        base_resolved = self.base_path.resolve()
        if not str(resolved).startswith(str(base_resolved) + os.sep) and resolved != base_resolved:
            raise ValueError(f"Path no permitido: {remote_path}")
        return resolved

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        try:
            dest = self._safe_path(remote_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest)
            logger.info(f"Archivo subido: {remote_path}")
            return True
        except ValueError as e:
            logger.error(f"Seguridad: {e}")
            return False
        except Exception as e:
            logger.error(f"Error subiendo archivo: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        try:
            source = self._safe_path(remote_path)
            if not source.exists():
                return False
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, local_path)
            logger.info(f"Archivo descargado: {remote_path}")
            return True
        except ValueError as e:
            logger.error(f"Seguridad: {e}")
            return False
        except Exception as e:
            logger.error(f"Error descargando archivo: {e}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        try:
            return self._safe_path(remote_path).exists()
        except ValueError:
            return False

    def get_last_modified(self, remote_path: str) -> Optional[datetime]:
        try:
            path = self._safe_path(remote_path)
        except ValueError:
            return None
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
        self.sftp = None
        self.client = None
        self.base_dir = base_dir
        # Guardar credenciales para reconexión
        self._host = host
        self._port = port
        self._username = username
        self._password = password

        self._connect()

    def _connect(self) -> bool:
        """Establece la conexión SFTP."""
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

            self.client.connect(
                self._host, port=self._port, username=self._username, password=self._password
            )
            self.sftp = self.client.open_sftp()
            logger.info(
                f"SFTP conectado a {self._host}:{self._port} con verificación de host key ✅"
            )
            return True
        except ImportError:
            logger.error("Paramiko no instalado. Ejecutar: pip install paramiko")
            return False
        except Exception as e:
            logger.error(f"Error conectando SFTP: {e}")
            if "paramiko" in str(type(e).__module__):
                logger.error("El servidor no está en known_hosts. Agregarlo con:")
                logger.error(f"  ssh-keyscan -H {self._host} >> ~/.ssh/known_hosts")
            return False

    def _ensure_connected(self) -> bool:
        """Verifica la conexión y reconecta si es necesario."""
        if self.sftp is None:
            logger.info("Conexión SFTP perdida. Reconectando...")
            return self._connect()

        # Verificar si la conexión sigue activa
        try:
            self.sftp.stat(self.base_dir)
            return True
        except Exception:
            logger.info("Conexión SFTP inactiva. Reconectando...")
            self.close()
            return self._connect()

    def _sanitize_path(self, remote_path: str) -> str:
        """
        Valida remote_path contra path traversal.
        Rechaza: "..", "~", rutas absolutas, etc.
        """
        # Normalizar separadores
        remote_path = remote_path.replace("\\", "/").strip()

        # Rechazar rutas absolutas
        if remote_path.startswith("/"):
            raise ValueError(f"Path no permitido (ruta absoluta): {remote_path}")

        # Rechazar traversal
        if ".." in remote_path or remote_path.startswith("~"):
            raise ValueError(f"Path no permitido (traversal): {remote_path}")

        # Rechazar componentes que intenten escapar
        for part in remote_path.split("/"):
            if part in (".", "..", "~") or not part:
                continue  # Permitir ".", "..", "~" como componentes intermedios, no son peligrosos
            if part.startswith("-"):  # Algunos comandos globales problemáticos
                raise ValueError(f"Path no permitido (componente peligroso): {part}")

        return remote_path

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        try:
            remote_path = self._sanitize_path(remote_path)
            if not self._ensure_connected():
                logger.error("No se pudo establecer conexión SFTP")
                return False

            full_path = f"{self.base_dir}/{remote_path}"
            # Crear directorios remotos si no existen
            self._mkdir_p(str(Path(full_path).parent))
            self.sftp.put(str(local_path), full_path)
            logger.info(f"Archivo subido vía SFTP: {remote_path}")
            return True
        except ValueError as e:
            logger.error(f"Seguridad: {e}")
            return False
        except Exception as e:
            logger.error(f"Error subiendo vía SFTP: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        try:
            remote_path = self._sanitize_path(remote_path)
            if not self._ensure_connected():
                logger.error("No se pudo establecer conexión SFTP")
                return False

            full_path = f"{self.base_dir}/{remote_path}"
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.sftp.get(full_path, str(local_path))
            logger.info(f"Archivo descargado vía SFTP: {remote_path}")
            return True
        except ValueError as e:
            logger.error(f"Seguridad: {e}")
            return False
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error descargando vía SFTP: {e}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        try:
            remote_path = self._sanitize_path(remote_path)
            if not self._ensure_connected():
                return False

            full_path = f"{self.base_dir}/{remote_path}"
            self.sftp.stat(full_path)
            return True
        except ValueError:
            return False
        except FileNotFoundError:
            return False

    def get_last_modified(self, remote_path: str) -> Optional[datetime]:
        try:
            remote_path = self._sanitize_path(remote_path)
            if not self._ensure_connected():
                return None
            full_path = f"{self.base_dir}/{remote_path}"
            stat = self.sftp.stat(full_path)
            return datetime.fromtimestamp(stat.st_mtime)
        except ValueError:
            return None
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
        try:
            if hasattr(self, "sftp") and self.sftp is not None:
                self.sftp.close()
        except Exception as e:
            logger.debug(f"Error cerrando sftp: {e}")
        finally:
            self.sftp = None

        try:
            if hasattr(self, "client") and self.client is not None:
                self.client.close()
        except Exception as e:
            logger.debug(f"Error cerrando cliente: {e}")
        finally:
            self.client = None


def _count_json_records(path: Path) -> int:
    """Cuenta el total de registros en un JSON de exportación para comparar volumen de datos."""
    try:
        import json as _json
        data = _json.loads(path.read_text(encoding="utf-8"))
        keys = ("profesores", "guardias", "zonas", "cursos_escolares", "ausencias")
        return sum(len(data.get(k, [])) for k in keys)
    except Exception:
        return 0


class SyncManager:
    """
    Gestor principal de sincronización multi-usuario.
    """

    def __init__(self, backend: SyncBackend, username: str):
        self.backend = backend
        self.username = username
        self.user_hash = self._hash_username(username)
        self.local_data_dir = get_user_data_directory() / self.user_hash
        self.local_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SyncManager inicializado para usuario: {username}")

    def _hash_username(self, username: str) -> str:
        """Genera un hash del nombre de usuario para nombres de archivo."""
        return hashlib.sha256(username.encode()).hexdigest()[:16]

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

                # Descargar a un archivo temporal para comparar antes de sobreescribir
                import tempfile
                tmp_path = Path(tempfile.mktemp(suffix=".json"))
                try:
                    if self.backend.download_file(remote_path, tmp_path):
                        # Guardia de seguridad: no sobreescribir si el remoto tiene menos registros
                        # que el local, para evitar que un JSON vacío/corrupto machaque datos reales.
                        remote_records = _count_json_records(tmp_path)
                        local_records = _count_json_records(local_json_path) if local_json_path.exists() else 0

                        if local_records > 0 and remote_records < local_records:
                            logger.warning(
                                f"⚠️  SYNC BLOQUEADO: el JSON remoto tiene {remote_records} registros "
                                f"pero el local tiene {local_records}. "
                                "Se conservan los datos locales para evitar pérdida de datos."
                            )
                            success = False
                        else:
                            # Reemplazar el local con el remoto
                            import shutil
                            shutil.move(str(tmp_path), str(local_json_path))
                            logger.info(f"✓ Datos descargados a {local_json_path} ({remote_records} registros)")

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
                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()
            else:
                logger.info("✓ Datos locales están actualizados")
        else:
            logger.info("ℹ️  No hay datos en la nube aún")

        # Importar JSON local a la BD si la BD está vacía y el JSON tiene datos.
        # Cubre el caso de reinstalación o nueva compilación donde la BD se crea vacía
        # pero el JSON local (procedente de una sync anterior) ya tiene todos los datos.
        if session and local_json_path.exists() and _count_json_records(local_json_path) > 0:
            try:
                from infrastructure.database.models import Profesor
                db_empty = session.query(Profesor).count() == 0
                if db_empty:
                    from sync.data_exporter import DataExporter
                    logger.info("📊 BD vacía con JSON local disponible — importando datos...")
                    if DataExporter.import_from_json(session, local_json_path, clear_existing=False):
                        logger.info("✅ Datos del JSON local importados a la BD")
                    else:
                        logger.error("❌ Error al importar JSON local a la BD")
            except Exception as e:
                logger.error(f"Error en importación de BD vacía: {e}")

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
                progress_callback(
                    "uploading",
                    {"message": "Subiendo archivo a la nube", "file_size_kb": file_size_kb},
                )

            try:
                if self.backend.upload_file(local_json_path, remote_path):
                    logger.info("✅ Datos sincronizados con la nube")
                    if progress_callback:
                        progress_callback("complete", {"message": "Sincronización completada"})
                else:
                    logger.error("❌ Error al subir datos a la nube")
                    success = False
                    if progress_callback:
                        progress_callback("error", {"message": "Error al subir datos a la nube"})
            except Exception as e:
                logger.error(f"❌ Excepción al subir datos a la nube: {e}")
                success = False
                if progress_callback:
                    progress_callback("error", {"message": f"Error de conexión: {str(e)}"})
        else:
            logger.warning(f"❌ {json_filename} no existe localmente")
            success = False
            if progress_callback:
                progress_callback("error", {"message": f"{json_filename} no existe"})

        # Guardar timestamp de última sincronización
        try:
            self._save_sync_metadata()
        except Exception as e:
            logger.warning(f"Error al guardar metadata de sincronización: {e}")

        return success

    def _save_sync_metadata(self):
        """Guarda metadata de sincronización."""
        metadata = {
            "username": self.username,
            "user_hash": self.user_hash,
            "last_sync": datetime.now().isoformat(),
        }

        metadata_path = self.local_data_dir / "last_sync.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # También subir metadata a la nube
        try:
            remote_path = self.get_remote_path("last_sync.json")
            self.backend.upload_file(metadata_path, remote_path)
        except Exception as e:
            logger.warning(f"No se pudo subir metadata a la nube: {e}")

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
    Sistema de autenticación de usuarios.
    Usa bcrypt para hashing de contraseñas.
    Migra automáticamente hashes SHA-256 legacy a bcrypt en login.
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
        """Guarda usuarios en archivo con permisos restrictivos (0o600)."""
        # Usar os.open() para crear/escribir con permisos seguros desde el inicio
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600  # Solo lectura/escritura para propietario
        
        try:
            fd = os.open(self.users_file, flags, mode)
            with os.fdopen(fd, "w") as f:
                json.dump(self.users, f, indent=2)
            # Asegurar permisos incluso si el archivo existía
            os.chmod(self.users_file, 0o600)
            logger.debug(f"users.json guardado con permisos 600")
        except OSError as e:
            logger.error(f"Error guardando users.json con permisos seguros: {e}")

    def register_user(self, username: str, password: str, email: str = "") -> bool:
        """Registra un nuevo usuario."""
        if username in self.users:
            logger.warning(f"Usuario {username} ya existe")
            return False

        # Validar username: solo alfanuméricos, puntos, guiones, guiones bajos
        if not re.fullmatch(r"[a-zA-Z0-9._\-]+", username):
            logger.warning(f"Username inválido (caracteres no permitidos): {username}")
            return False

        import bcrypt

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        self.users[username] = {
            "password_hash": password_hash,
            "email": email,
            "created_at": datetime.now().isoformat(),
        }

        self._save_users()
        logger.info(f"Usuario registrado: {username}")
        return True

    @staticmethod
    def validate_password_policy(password: str) -> tuple[bool, str]:
        """
        Valida que la contraseña cumpla la política de seguridad.
        Returns (ok, mensaje_error). Si ok=True, mensaje_error es vacío.
        """
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if not any(c.isupper() for c in password):
            return False, "La contraseña debe contener al menos una mayúscula"
        if not any(c.isdigit() for c in password):
            return False, "La contraseña debe contener al menos un número"
        if not any(c in r"!@#$%^&*()_+-=[]{}|;':,./<>?" for c in password):
            return False, "La contraseña debe contener al menos un carácter especial"
        return True, ""

    @staticmethod
    def _is_legacy_sha256(password_hash: str) -> bool:
        """Detecta si un hash es SHA-256 legacy (64 chars hex)."""
        return len(password_hash) == 64 and all(c in "0123456789abcdef" for c in password_hash)

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        """
        Autentica un usuario. Migra hashes SHA-256 legacy a bcrypt.
        Implementa lockout: 5 intentos fallidos → 15 min bloqueado con delay progresivo.
        Returns (ok, mensaje_error). Si ok=True, mensaje_error es vacío.
        """
        import time

        if username not in self.users:
            return False, "Usuario o contraseña incorrectos"

        user = self.users[username]

        # Comprobar bloqueo por intentos fallidos
        locked_until = user.get("locked_until")
        if locked_until:
            lockout_time = datetime.fromisoformat(locked_until)
            if datetime.now() < lockout_time:
                remaining = int((lockout_time - datetime.now()).total_seconds() / 60) + 1
                return False, f"Cuenta bloqueada. Intenta de nuevo en {remaining} minuto(s)"
            else:
                user["failed_login_attempts"] = 0
                user["locked_until"] = None

        import bcrypt

        stored_hash = user["password_hash"]
        authenticated = False

        if self._is_legacy_sha256(stored_hash):
            legacy_hash = hashlib.sha256(password.encode()).hexdigest()
            if stored_hash == legacy_hash:
                new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                user["password_hash"] = new_hash
                self._save_users()
                logger.info(f"Hash de {username} migrado de SHA-256 a bcrypt")
                authenticated = True
        else:
            try:
                authenticated = bcrypt.checkpw(password.encode(), stored_hash.encode())
            except (ValueError, TypeError):
                authenticated = False

        if authenticated:
            user["failed_login_attempts"] = 0
            user["locked_until"] = None
            self._save_users()
            return True, ""
        else:
            attempts = user.get("failed_login_attempts", 0) + 1
            user["failed_login_attempts"] = attempts
            
            # Delay progresivo: 1s, 2s, 4s, 8s, 16s
            progresive_delays = [1, 2, 4, 8, 16]
            delay = progresive_delays[min(attempts - 1, len(progresive_delays) - 1)]
            time.sleep(min(delay, 2))  # Máximo 2 segundos para GUI responsiva
            
            if attempts >= 5:
                user["locked_until"] = (datetime.now() + timedelta(minutes=15)).isoformat()
                logger.warning(f"Usuario {username} bloqueado por 15 minutos tras {attempts} intentos fallidos")
                self._save_users()
                return False, "Demasiados intentos fallidos. Cuenta bloqueada 15 minutos"
            self._save_users()
            return False, "Usuario o contraseña incorrectos"

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
