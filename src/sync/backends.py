"""Formas de hablar con el sitio donde viven los datos compartidos.

Estaba todo en `sync_manager.py`, que pasaba de las 1.200 líneas y mezclaba dos
cosas distintas: *cómo* se sube un fichero —SFTP, o una carpeta local para
pruebas— y *qué* se sube y cuándo. Esto es lo primero (COD-008).
"""

import logging
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    _TENACITY_AVAILABLE = True
except ImportError:
    _TENACITY_AVAILABLE = False

try:
    import pybreaker
    _sftp_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)
    _smtp_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)
    _PYBREAKER_AVAILABLE = True
except ImportError:
    pybreaker = None  # type: ignore[assignment]
    _PYBREAKER_AVAILABLE = False
    _sftp_breaker = None
    _smtp_breaker = None

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

    def move_file(self, remote_src: str, remote_dst: str) -> bool:
        """
        Renombra un fichero ya subido. Se usa para publicar una subida de forma
        atómica y para rotar versiones anteriores.

        Los backends que no sepan renombrar devuelven False y quien llama decide;
        la rotación es un extra, nunca un requisito para que la subida funcione.
        """
        return False


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
            # Escribir a un temporal y renombrar: si algo se corta a mitad, el
            # fichero bueno sigue intacto en lugar de quedar truncado.
            temporal = dest.with_name(dest.name + ".tmp")
            shutil.copy2(local_path, temporal)
            os.replace(temporal, dest)
            logger.info(f"Archivo subido: {remote_path}")
            return True
        except ValueError as e:
            logger.error(f"Seguridad: {e}")
            return False
        except (ValueError, TypeError, OSError) as e:
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
        except (ValueError, TypeError, OSError) as e:
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

    def move_file(self, remote_src: str, remote_dst: str) -> bool:
        try:
            origen = self._safe_path(remote_src)
            destino = self._safe_path(remote_dst)
            if not origen.exists():
                return False
            destino.parent.mkdir(parents=True, exist_ok=True)
            os.replace(origen, destino)
            return True
        except (OSError, ValueError) as e:
            logger.warning(f"No se pudo renombrar {remote_src} → {remote_dst}: {e}")
            return False


try:
    from paramiko import SSHException as _SSHException
except ImportError:  # paramiko es opcional: sin él no hay backend SFTP

    class _SSHException(Exception):  # type: ignore[no-redef]
        """Sustituto cuando paramiko no está instalado."""


#: Lo que puede fallar al hablar con el servidor. `SSHException` **no** hereda de
#: `OSError`, así que los manejadores que sólo listaban `(OSError, ValueError)`
#: dejaban escapar el error más típico —banner ilegible, clave de host cambiada—
#: y el fallo acababa en el manejador global en vez de dar un mensaje útil (COD-002).
ERRORES_DE_TRANSPORTE = (_SSHException, OSError, ValueError)


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
        """Establece la conexión SFTP con circuit breaker y reintentos exponenciales."""
        if _PYBREAKER_AVAILABLE and _sftp_breaker is not None:
            try:
                if _TENACITY_AVAILABLE:
                    return _sftp_breaker.call(self._connect_with_retry)
                return _sftp_breaker.call(self._connect_once)
            except pybreaker.CircuitBreakerError:
                logger.warning("SFTP: circuit breaker abierto, omitiendo intento de conexión")
                return False
        if _TENACITY_AVAILABLE:
            return self._connect_with_retry()
        return self._connect_once()

    def _connect_once(self) -> bool:
        """Lógica de conexión SFTP sin retry."""
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
                self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                timeout=30,
                banner_timeout=30,
                auth_timeout=30,
            )
            transport = self.client.get_transport()
            if transport is not None:
                transport.set_keepalive(30)
            self.sftp = self.client.open_sftp()
            logger.info(
                f"SFTP conectado a {self._host}:{self._port} con verificación de host key ✅"
            )
            return True
        except ImportError:
            logger.error("Paramiko no instalado. Ejecutar: pip install paramiko")
            return False
        except ERRORES_DE_TRANSPORTE as e:
            logger.error(f"Error conectando SFTP: {e}")
            if "paramiko" in str(type(e).__module__):
                logger.error("El servidor no está en known_hosts. Agregarlo con:")
                logger.error(f"  ssh-keyscan -H {self._host} >> ~/.ssh/known_hosts")
            return False

    def _connect_with_retry(self) -> bool:
        """Conecta con backoff exponencial (3 intentos: 2s, 4s, 8s)."""
        import paramiko

        @retry(
            retry=retry_if_exception_type((OSError, paramiko.SSHException)),
            wait=wait_exponential(multiplier=2, min=2, max=8),
            stop=stop_after_attempt(3),
            reraise=False,
        )
        def _do_connect():
            return self._connect_once()

        try:
            result = _do_connect()
            return result if result is not None else False
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"SFTP: todos los reintentos agotados: {e}")
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
        except Exception as e:
            logger.info(f"Conexión SFTP inactiva ({e}). Reconectando...")
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
            # Subir a un temporal y renombrar. El renombrado en SFTP es atómico,
            # así que un corte de conexión nunca deja el fichero bueno a medias.
            temporal = f"{full_path}.tmp"
            self.sftp.put(str(local_path), temporal)
            try:
                self.sftp.posix_rename(temporal, full_path)
            except (OSError, AttributeError):
                # Servidores sin la extensión posix-rename: borrar y renombrar.
                try:
                    self.sftp.remove(full_path)
                except OSError:
                    pass
                self.sftp.rename(temporal, full_path)
            logger.info(f"Archivo subido vía SFTP: {remote_path}")
            return True
        except ValueError as e:
            logger.error(f"Seguridad: {e}")
            return False
        except ERRORES_DE_TRANSPORTE as e:
            logger.error(f"Error subiendo vía SFTP: {e}")
            return False

    def move_file(self, remote_src: str, remote_dst: str) -> bool:
        try:
            origen = f"{self.base_dir}/{self._sanitize_path(remote_src)}"
            destino = f"{self.base_dir}/{self._sanitize_path(remote_dst)}"
            if not self._ensure_connected():
                return False
            try:
                self.sftp.posix_rename(origen, destino)
            except (OSError, AttributeError):
                try:
                    self.sftp.remove(destino)
                except OSError:
                    pass
                self.sftp.rename(origen, destino)
            return True
        except ERRORES_DE_TRANSPORTE as e:
            logger.warning(f"No se pudo renombrar {remote_src} → {remote_dst}: {e}")
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
        except ERRORES_DE_TRANSPORTE as e:
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
        except (ConnectionError, OSError) as e:
            logger.warning(
                f"Error de conexión o I/O al obtener last_modified para {remote_path}: {e}"
            )
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
        except ERRORES_DE_TRANSPORTE as e:
            logger.debug(f"Error cerrando sftp: {e}")
        finally:
            self.sftp = None

        try:
            if hasattr(self, "client") and self.client is not None:
                self.client.close()
        except (OSError, ValueError) as e:
            logger.debug(f"Error cerrando cliente: {e}")
        finally:
            self.client = None
