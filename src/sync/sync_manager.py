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
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from core.paths import get_user_data_directory

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
        except (ValueError, OSError) as e:
            logger.warning(f"No se pudo renombrar {remote_src} → {remote_dst}: {e}")
            return False


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
        except (OSError, ValueError) as e:
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
        except (OSError, ValueError) as e:
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
        except (ValueError, OSError) as e:
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
        except (OSError, ValueError) as e:
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
        except (OSError, ValueError) as e:
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


def hash_username(username: str) -> str:
    """
    Identificador de carpeta para un usuario.

    Es el mismo cálculo en todas partes: la carpeta del servidor, la base de datos
    local y el fichero de bloqueo tienen que coincidir.
    """
    return hashlib.sha256(username.encode()).hexdigest()[:16]


def remote_account_path(username: str) -> str:
    """Ruta del fichero de cuenta dentro de la carpeta del usuario en el servidor."""
    return f"users/{hash_username(username)}/cuenta.json"


class RemoteAccounts:
    """
    Cuentas guardadas junto a los datos, en el servidor.

    Es lo que permite entrar con el mismo usuario y contraseña desde cualquier
    equipo, y lo que impide que alguien se apropie del nombre de otro: si la
    cuenta ya existe en el servidor, no se puede volver a registrar.
    """

    def __init__(self, backend: "SyncBackend"):
        self.backend = backend

    def fetch(self, username: str) -> Optional[dict]:
        """Devuelve la ficha de la cuenta, o None si no existe o no hay conexión."""
        remote_path = remote_account_path(username)
        tmp_path = _ruta_temporal_segura(".json")
        try:
            if not self.backend.file_exists(remote_path):
                return None
            if not self.backend.download_file(remote_path, tmp_path):
                return None
            return json.loads(tmp_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"No se pudo leer la cuenta del servidor: {e}")
            return None
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def has_data(self, username: str) -> bool:
        """
        ¿Esa cuenta ya tiene datos en el servidor?

        Sirve para las cuentas antiguas, creadas antes de que la ficha se guardara
        en el servidor: existe su carpeta con datos pero no hay contraseña con la
        que comprobar quién es. En ese caso no se puede dejar registrar el nombre,
        porque bastaría con saberlo para llevarse los datos de otra persona.
        """
        try:
            return self.backend.file_exists(
                f"users/{hash_username(username)}/guardias_patio_data.json"
            )
        except (OSError, ValueError, RuntimeError):
            return False

    def publish(self, username: str, ficha: dict) -> bool:
        """Guarda la ficha de la cuenta en el servidor."""
        remote_path = remote_account_path(username)
        tmp_path = _ruta_temporal_segura(".json")
        try:
            publicable = {
                "username": username,
                "password_hash": ficha.get("password_hash"),
                "email": ficha.get("email", ""),
                "created_at": ficha.get("created_at"),
                "updated_at": datetime.now().isoformat(),
            }
            tmp_path.write_text(json.dumps(publicable, indent=2), encoding="utf-8")
            return self.backend.upload_file(tmp_path, remote_path)
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"No se pudo publicar la cuenta en el servidor: {e}")
            return False
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass


def _count_json_records(path: Path) -> int:
    """Cuenta el total de registros en un JSON de exportación para comparar volumen de datos."""
    try:
        import json as _json
        data = _json.loads(path.read_text(encoding="utf-8"))
        keys = ("profesores", "guardias", "zonas", "cursos_escolares", "ausencias")
        return sum(len(data.get(k, [])) for k in keys)
    except (ValueError, KeyError):
        return 0


def _ruta_temporal_segura(sufijo: str = ".json") -> Path:
    """Devuelve la ruta de un temporal ya creado, sólo accesible por su dueño.

    `tempfile.mktemp()` sólo inventaba un nombre: entre que lo devolvía y se
    escribía en él, cualquiera podía dejar ahí un enlace simbólico apuntando a
    otro sitio. `mkstemp()` crea el fichero en el mismo acto (SEC-003).
    """
    descriptor, ruta = tempfile.mkstemp(suffix=sufijo)
    os.close(descriptor)
    return Path(ruta)


class SyncManager:
    """
    Gestor principal de sincronización multi-usuario.
    """

    #: Copias anteriores que se conservan en el servidor antes de reemplazar.
    VERSIONES_CONSERVADAS = 3

    def __init__(self, backend: SyncBackend, username: str):
        self.backend = backend
        self.username = username
        self.user_hash = self._hash_username(username)
        self.local_data_dir = get_user_data_directory() / self.user_hash
        self.local_data_dir.mkdir(parents=True, exist_ok=True)
        #: Versión de los datos con los que trabaja esta sesión.
        self.version_descargada = 0
        #: Hasta que la descarga de arranque salga bien, esta sesión no puede subir.
        self.puede_subir = False
        self.motivo_bloqueo: Optional[str] = None
        #: Por qué no se pudo subir la última vez. None si la última subida fue bien.
        self.motivo_ultimo_fallo: Optional[str] = None

        logger.info(f"SyncManager inicializado para usuario: {username}")

    def _hash_username(self, username: str) -> str:
        """Genera un hash del nombre de usuario para nombres de archivo."""
        return hash_username(username)

    def get_remote_path(self, filename: str) -> str:
        """Obtiene la ruta remota para un archivo del usuario."""
        return f"users/{self.user_hash}/{filename}"

    # ------------------------------------------------------------------
    # Modelo: la copia de la nube es la buena.
    # Una cuenta la usa una persona, que puede cambiar de equipo. El flujo es
    # descargar, editar y subir. Por eso al abrir se reconstruye la base local
    # con lo que hay en la nube (así las bajas se propagan y los identificadores
    # no chocan) y no se permite subir si antes no se pudo descargar.
    # ------------------------------------------------------------------

    def _leer_version(self, path: Path) -> int:
        """Lee el número de versión que lleva dentro un fichero de datos."""
        try:
            datos = json.loads(path.read_text(encoding="utf-8"))
            return int(datos.get("sync_version", 0))
        except (OSError, ValueError, TypeError):
            return 0

    def _es_fichero_de_datos_valido(self, path: Path) -> bool:
        """Comprueba que lo descargado es una exportación y no un fichero a medias."""
        try:
            datos = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.error("El fichero descargado no es un JSON válido")
            return False
        if not isinstance(datos, dict):
            logger.error("El fichero descargado no tiene la estructura esperada")
            return False
        esperadas = {"profesores", "zonas", "configuracion", "guardias", "ausencias",
                     "cursos_escolares"}
        if not (set(datos) & esperadas):
            logger.error("El fichero descargado no contiene ninguna sección conocida")
            return False
        return True

    def _rotar_versiones_remotas(self) -> None:
        """
        Conserva unas cuantas copias anteriores en el servidor antes de reemplazar.

        Son renombrados, así que cuestan poco, y dan a dónde volver si una subida
        resulta ser mala. Es un extra: si falla, la subida sigue adelante.
        """
        nombre = "guardias_patio_data.json"
        try:
            for n in range(self.VERSIONES_CONSERVADAS - 1, 0, -1):
                origen = self.get_remote_path(f"{nombre}.{n}")
                if self.backend.file_exists(origen):
                    self.backend.move_file(origen, self.get_remote_path(f"{nombre}.{n + 1}"))
            actual = self.get_remote_path(nombre)
            if self.backend.file_exists(actual):
                self.backend.move_file(actual, self.get_remote_path(f"{nombre}.1"))
        except (OSError, ValueError) as e:
            logger.warning(f"No se pudieron rotar las versiones remotas: {e}")

    def _hay_datos_locales(self, session) -> bool:
        """¿Merece la pena subir? Sí en cuanto haya algo que perder."""
        try:
            from infrastructure.database.models import Guardia, Profesor, Zona

            return any(
                session.query(modelo).first() is not None
                for modelo in (Profesor, Zona, Guardia)
            )
        except Exception as e:  # noqa: BLE001 - nunca debe impedir abrir la aplicación
            logger.warning(f"No se pudo comprobar si hay datos locales: {e}")
            return False

    def _bloquear_subida(self, motivo: str) -> None:
        self.puede_subir = False
        self.motivo_bloqueo = motivo
        logger.error(f"🔒 Subida bloqueada: {motivo}")

    def sync_on_startup(self, session=None) -> bool:
        """
        Trae los datos de la nube y reconstruye con ellos la base local.

        Si algo impide descargar, la sesión queda sin permiso para subir. Es
        preferible trabajar sabiendo que no hay nube a machacar el trabajo bueno
        con una copia vieja.
        """
        logger.info("Iniciando sincronización de arranque...")
        self.puede_subir = False
        self.motivo_bloqueo = None

        json_filename = "guardias_patio_data.json"
        local_json_path = self.local_data_dir / json_filename
        remote_path = self.get_remote_path(json_filename)

        metadata = self._leer_metadata_local()
        if metadata.get("pendiente_subida"):
            self._bloquear_subida(
                "La sesión anterior no llegó a subir sus cambios. No se descarga nada "
                "para no perderlos; hay que resolver ese envío pendiente primero."
            )
            return False

        try:
            existe_remoto = self.backend.file_exists(remote_path)
        except (OSError, ValueError, RuntimeError) as e:
            self._bloquear_subida(f"No se pudo consultar el servidor: {e}")
            return False

        if not existe_remoto:
            # Cuenta nueva: todavía no hay nada en la nube y lo local es el origen.
            # Cuenta que todavía no tiene nada en la nube. Si este equipo ya tiene
            # datos, se suben ahora mismo: así la carpeta queda creada desde el
            # primer momento y no se depende de que la sesión termine bien.
            self.version_descargada = int(metadata.get("sync_version", 0))
            self.puede_subir = True
            self._guardar_metadata_local(self.version_descargada, pendiente_subida=False)

            if session is not None and self._hay_datos_locales(session):
                logger.info("La nube está vacía y este equipo tiene datos: subiéndolos ahora")
                return self.sync_on_shutdown(session=session)

            logger.info("No hay datos en la nube para esta cuenta ni en este equipo")
            return True

        tmp_path = _ruta_temporal_segura(".json")
        try:
            if not self.backend.download_file(remote_path, tmp_path):
                self._bloquear_subida("No se pudieron descargar los datos de la nube")
                return False

            if not self._es_fichero_de_datos_valido(tmp_path):
                self._bloquear_subida("Los datos descargados no son válidos")
                return False

            version_remota = self._leer_version(tmp_path)

            if session is not None:
                from sync.data_exporter import DataExporter

                logger.info("📥 Reconstruyendo la base local con los datos de la nube...")
                if not DataExporter.import_from_json(session, tmp_path, clear_existing=True):
                    self._bloquear_subida("No se pudieron importar los datos descargados")
                    return False

            shutil.move(str(tmp_path), str(local_json_path))
            self.version_descargada = version_remota
            self.puede_subir = True
            self._guardar_metadata_local(version_remota, pendiente_subida=False)
            logger.info(f"✅ Datos de la nube aplicados (versión {version_remota})")
            return True

        except (OSError, ValueError, RuntimeError) as e:
            self._bloquear_subida(f"Error al sincronizar con la nube: {e}")
            return False
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def sync_on_shutdown(self, session=None, progress_callback=None) -> bool:
        """
        Sube el estado actual, reemplazando el de la nube.

        Antes comprueba que nadie haya subido nada desde que empezó esta sesión.
        Si lo hay, no sobrescribe: deja el envío pendiente y avisa.
        """
        logger.info("Iniciando sincronización de cierre...")

        if not self.puede_subir:
            motivo = self.motivo_bloqueo or "la sesión no descargó los datos al abrir"
            logger.error(f"⛔ No se sube nada: {motivo}")
            if progress_callback:
                progress_callback("error", {"message": motivo})
            return False

        json_filename = "guardias_patio_data.json"
        local_json_path = self.local_data_dir / json_filename
        remote_path = self.get_remote_path(json_filename)
        nueva_version = self.version_descargada + 1

        if session:
            from sync.data_exporter import DataExporter

            logger.info("📤 Exportando base de datos a JSON...")
            if progress_callback:
                progress_callback("exporting", {"message": "Exportando datos de la base de datos"})

            if not DataExporter.export_to_json(
                session, local_json_path, sync_version=nueva_version
            ):
                logger.error("❌ Error al exportar datos a JSON")
                if progress_callback:
                    progress_callback("error", {"message": "Error al exportar datos"})
                return False
        elif not local_json_path.exists():
            logger.error("❌ No hay datos que subir")
            if progress_callback:
                progress_callback("error", {"message": "No hay datos para sincronizar"})
            return False

        file_size_kb = local_json_path.stat().st_size // 1024 if local_json_path.exists() else 0

        if progress_callback:
            progress_callback("connecting", {"message": "Conectando al servidor"})

        # ¿Ha subido alguien algo mientras trabajábamos?
        tmp_path = _ruta_temporal_segura(".json")
        try:
            if self.backend.file_exists(remote_path) and self.backend.download_file(
                remote_path, tmp_path
            ):
                version_remota = self._leer_version(tmp_path)
                if version_remota != self.version_descargada:
                    motivo = (
                        f"El servidor tiene la versión {version_remota} y esta sesión partió "
                        f"de la {self.version_descargada}. No se sobrescribe."
                    )
                    logger.error(f"⛔ {motivo}")
                    # Se guarda el motivo para poder explicárselo a quien está
                    # delante: hasta ahora sólo quedaba en el registro (SYNC-014).
                    self.motivo_ultimo_fallo = motivo
                    self._guardar_metadata_local(self.version_descargada, pendiente_subida=True)
                    if progress_callback:
                        progress_callback("error", {"message": motivo})
                    return False
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"No se pudo comprobar la versión remota: {e}")
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

        if progress_callback:
            progress_callback(
                "uploading",
                {"message": "Subiendo a la nube", "file_size_kb": file_size_kb},
            )

        self.motivo_ultimo_fallo = None
        self._rotar_versiones_remotas()

        try:
            if self.backend.upload_file(local_json_path, remote_path):
                self.version_descargada = nueva_version
                self._guardar_metadata_local(nueva_version, pendiente_subida=False)
                logger.info(f"✅ Datos sincronizados (versión {nueva_version})")
                if progress_callback:
                    progress_callback("complete", {"message": "Sincronización completada"})
                self._save_sync_metadata()
                return True
            raise OSError("el servidor rechazó la subida")
        except (OSError, IOError, RuntimeError) as e:
            logger.error(f"❌ No se pudieron subir los datos: {e}")
            self._guardar_metadata_local(self.version_descargada, pendiente_subida=True)
            if progress_callback:
                progress_callback("error", {"message": f"Error al subir: {e}"})
            return False

    def _ruta_metadata_local(self) -> Path:
        return self.local_data_dir / "last_sync.json"

    def _leer_metadata_local(self) -> dict:
        try:
            return json.loads(self._ruta_metadata_local().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _guardar_metadata_local(self, sync_version: int, pendiente_subida: bool) -> None:
        metadata = self._leer_metadata_local()
        metadata.update(
            {
                "username": self.username,
                "user_hash": self.user_hash,
                "sync_version": sync_version,
                "pendiente_subida": pendiente_subida,
                "last_sync": datetime.now().isoformat(),
            }
        )
        try:
            self._ruta_metadata_local().write_text(
                json.dumps(metadata, indent=2), encoding="utf-8"
            )
        except OSError as e:
            logger.warning(f"No se pudo guardar el estado de sincronización: {e}")

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
        except (OSError, IOError, RuntimeError) as e:
            logger.warning(f"No se pudo subir metadata a la nube: {e}")

    def manual_sync(self) -> bool:
        """Sincronización manual (botón en la UI)."""
        logger.info("Sincronización manual iniciada")
        # Primero descargar cambios remotos
        self.sync_on_startup()
        # Luego subir cambios locales
        return self.sync_on_shutdown()

    def get_last_sync_time(self) -> Optional[datetime]:
        """Devuelve la fecha/hora de la última sincronización exitosa, o None."""
        metadata_path = self.local_data_dir / "last_sync.json"
        try:
            if metadata_path.exists():
                with open(metadata_path) as f:
                    data = json.load(f)
                raw = data.get("last_sync")
                if raw:
                    return datetime.fromisoformat(raw)
        except (OSError, ValueError, KeyError):
            pass
        return None


# ============== SISTEMA DE AUTENTICACIÓN SIMPLE ==============


class UserAuth:
    """
    Sistema de autenticación de usuarios.
    Usa bcrypt para hashing de contraseñas.
    Migra automáticamente hashes SHA-256 legacy a bcrypt en login.
    """

    def __init__(self, users_file: Path = None, backend: "SyncBackend" = None):
        """
        Args:
            users_file: copia local de las cuentas. Sirve de caché para poder entrar
                sin conexión y para guardar el bloqueo por intentos fallidos.
            backend: si se pasa, manda el servidor. La cuenta vive junto a los datos
                del usuario, así que la misma cuenta funciona desde cualquier equipo
                y nadie puede apropiarse de un nombre ya registrado.
        """
        if users_file is None:
            from core.paths import get_data_directory

            users_file = get_data_directory() / "users.json"
        self.users_file = users_file
        self.users = self._load_users()
        self.remote = RemoteAccounts(backend) if backend is not None else None
        #: Explicación del último registro rechazado, para poder decírselo al usuario.
        self.ultimo_motivo_registro = ""

    def _comprobar_nombre_disponible(self, username: str) -> tuple[bool, str]:
        """
        Decide si se puede registrar ese nombre.

        Un nombre de usuario es público y fácil de adivinar, así que registrarlo no
        puede dar acceso a los datos de quien ya lo usa.
        """
        if self.remote is None:
            return True, ""

        if self.remote.fetch(username) is not None:
            return False, (
                f"El usuario «{username}» ya existe. Entra con su contraseña; no hace "
                "falta volver a registrarlo aunque cambies de equipo."
            )

        if self.remote.has_data(username):
            return False, (
                f"El usuario «{username}» ya tiene datos en el servidor, pero su "
                "contraseña todavía no está publicada, así que no se puede comprobar "
                "que seas su propietario.\n\nEntra una vez desde el equipo donde "
                "creaste la cuenta y quedará disponible desde cualquier ordenador."
            )

        return True, ""

    def _traer_cuenta_del_servidor(self, username: str) -> Optional[dict]:
        """
        Copia la ficha del servidor a la caché local antes de comprobar la contraseña.

        Así manda siempre el servidor, pero se conserva el recuento de intentos
        fallidos, que es local, y queda una copia para entrar sin conexión.
        """
        if not self.remote:
            return None
        ficha = self.remote.fetch(username)
        if not ficha or not ficha.get("password_hash"):
            return None

        local = self.users.get(username, {})
        if local.get("password_hash") != ficha["password_hash"]:
            local.update(
                {
                    "password_hash": ficha["password_hash"],
                    "email": ficha.get("email", ""),
                    "created_at": ficha.get("created_at"),
                }
            )
            self.users[username] = local
            self._save_users()
            logger.info(f"Cuenta '{username}' actualizada desde el servidor")
        return ficha

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
            logger.debug("users.json guardado con permisos 600")
        except OSError as e:
            logger.error(f"Error guardando users.json con permisos seguros: {e}")

    def register_user(self, username: str, password: str, email: str = "") -> bool:
        """
        Registra un nuevo usuario.

        Si hay servidor, el nombre se reserva allí: no se puede registrar uno que
        ya exista, porque sus datos son de otra persona.
        """
        if username in self.users:
            logger.warning(f"Usuario {username} ya existe")
            self.ultimo_motivo_registro = (
                f"El usuario «{username}» ya existe en este equipo. Entra con su contraseña."
            )
            return False

        ok, motivo = self._comprobar_nombre_disponible(username)
        if not ok:
            logger.warning(motivo)
            self.ultimo_motivo_registro = motivo
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
        if self.remote is not None:
            self.remote.publish(username, self.users[username])
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

        # El servidor es la referencia; si no responde se usa la copia local.
        ficha_remota = self._traer_cuenta_del_servidor(username)

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
            # Primera vez que esta cuenta se usa con servidor: se publica allí
            # para que funcione desde cualquier equipo.
            if self.remote is not None and ficha_remota is None:
                self.remote.publish(username, user)
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
