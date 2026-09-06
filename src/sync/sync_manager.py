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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from core.paths import get_user_data_directory

# Los backends viven en `backends.py` desde v5.90.0: este módulo pasaba de las
# 1.200 líneas mezclando cómo se sube un fichero con qué se sube y cuándo. Se
# reexportan porque medio programa los importa desde aquí.
from sync.backends import (
    ERRORES_DE_TRANSPORTE,
    LocalSyncBackend,
    SFTPSyncBackend,
    SyncBackend,
)

# Las cuentas remotas viven en `cuentas.py` desde v5.90.0; se reexportan porque
# el login y la ventana las importan desde aquí.
from sync.cuentas import (
    RemoteAccounts,
    _ruta_temporal_segura,
    hash_username,
    remote_account_path,
)

# Configurar logger
logger = logging.getLogger(__name__)


__all__ = [
    "ERRORES_DE_TRANSPORTE",
    "LocalSyncBackend",
    "RemoteAccounts",
    "SFTPSyncBackend",
    "SyncBackend",
    "SyncManager",
    "hash_username",
    "remote_account_path",
]


def _count_json_records(path: Path) -> int:
    """Cuenta el total de registros en un JSON de exportación para comparar volumen de datos."""
    try:
        import json as _json
        data = _json.loads(path.read_text(encoding="utf-8"))
        keys = ("profesores", "guardias", "zonas", "cursos_escolares", "ausencias")
        return sum(len(data.get(k, [])) for k in keys)
    except (ValueError, KeyError):
        return 0


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

        # Cada media hora se subía la base entera aunque nadie hubiera tocado
        # nada, y crece con el curso. Si el contenido es el mismo que la última
        # vez, no hay nada que subir (ESC-003).
        huella = self.huella_del_contenido(local_json_path)
        if (
            huella is not None
            and huella == self._leer_metadata_local().get("huella_subida")
            and not self._leer_metadata_local().get("pendiente_subida", False)
        ):
            logger.info("✅ Nada que subir: los datos no han cambiado desde la última vez")
            self.motivo_ultimo_fallo = None
            if progress_callback:
                progress_callback("complete", {"message": "Sin cambios que subir"})
            return True

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
                self._guardar_metadata_local(
                    nueva_version, pendiente_subida=False, huella=huella
                )
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

    #: Claves que cambian en cada exportación aunque los datos sean los mismos:
    #: la fecha del volcado y el contador de versión. Si entrasen en la huella,
    #: cada comprobación diría «hay cambios» y la subida sería siempre (ESC-003).
    _CLAVES_VOLATILES = ("export_date", "sync_version")

    @classmethod
    def huella_del_contenido(cls, ruta: Path) -> Optional[str]:
        """Resumen de los datos exportados, sin lo que cambia en cada volcado.

        Sirve para no subir 30 minutos después exactamente lo mismo que ya está
        en el servidor, que es el caso normal cuando nadie ha tocado nada.
        """
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            logger.warning(f"No se pudo calcular la huella de {ruta.name}: {e}")
            return None
        if isinstance(datos, dict):
            datos = {k: v for k, v in datos.items() if k not in cls._CLAVES_VOLATILES}
        texto = json.dumps(datos, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def _ruta_metadata_local(self) -> Path:
        return self.local_data_dir / "last_sync.json"

    def _leer_metadata_local(self) -> dict:
        try:
            return json.loads(self._ruta_metadata_local().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _guardar_metadata_local(
        self, sync_version: int, pendiente_subida: bool, huella: Optional[str] = None
    ) -> None:
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
        if huella is not None:
            metadata["huella_subida"] = huella
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
