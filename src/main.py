"""
Punto de entrada de la aplicación de escritorio
========================================================
Ejecutar: python src/main.py
"""

import faulthandler
import glob
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.paths import get_logs_directory

# Configurar logging ANTES de cualquier import
log_dir = get_logs_directory()
log_dir.mkdir(parents=True, exist_ok=True)

for _old_log in glob.glob(str(log_dir / "app_*.log")):
    if (datetime.now() - datetime.fromtimestamp(os.path.getmtime(_old_log))).days > 30:
        os.remove(_old_log)

log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Un fallo nativo (Qt, OR-Tools, sqlite) mata el proceso sin dejar traza de Python.
# faulthandler escribe la pila de todos los hilos en ese momento, que es la única
# evidencia disponible cuando la app se cierra de golpe en un build congelado.
_faulthandler_file = open(log_dir / "faulthandler.log", "a", encoding="utf-8")
faulthandler.enable(file=_faulthandler_file, all_threads=True)

# En un build "windowed" no hay consola: sys.stdout es None y StreamHandler(None)
# escribe en stderr o falla. Sólo se añade cuando hay salida real.
_handlers: list[logging.Handler] = [logging.FileHandler(log_file, encoding="utf-8")]
if sys.stdout is not None:
    _handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=_handlers,
)

from PyQt6.QtCore import QLibraryInfo, QLocale, Qt, QTranslator
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMessageBox

from presentation.forms.login_dialog import LoginDialog
from presentation.ventana_principal import VentanaPrincipal
from sync import SyncConfigurationError, SyncManager, get_default_backend
from utils.corporate_branding import apply_corporate_branding

# Configurar logging
logger = logging.getLogger(__name__)
logger.info(f"=== INICIO DE APLICACIÓN === Log: {log_file}")


def main():
    """Función principal"""
    # Limpiar threads residuales de PyQt antes de crear la aplicación
    import threading

    logger.debug(f"🧹 Threads activos al inicio: {threading.active_count()}")
    for thread in threading.enumerate():
        thread_name = getattr(thread, "name", "Unknown")
        logger.debug(f"   - Thread: {thread_name} (tipo: {type(thread).__name__})")

    # Instalar manejador global de excepciones
    def exception_hook(exctype, value, tb):
        """Captura excepciones no manejadas."""
        import traceback

        logger.critical("=" * 80)
        logger.critical("🚨 EXCEPCIÓN NO MANEJADA DETECTADA")
        logger.critical("=" * 80)
        logger.critical(f"Tipo: {exctype.__name__}")
        logger.critical(f"Valor: {value}")
        logger.critical("Traceback:")
        for line in traceback.format_tb(tb):
            logger.critical(line.rstrip())
        logger.critical("=" * 80)

        # Mostrar diálogo de error al usuario si la app Qt ya está en marcha.
        # PyQt llama a este hook en el hilo donde ocurrió la excepción, así que crear
        # aquí un widget sin comprobarlo tumba el proceso: es justo lo que pasaba con
        # los errores de paramiko en SyncWorker (CRW-005).
        try:
            from PyQt6.QtCore import QThread
            from PyQt6.QtWidgets import QApplication, QMessageBox

            app_qt = QApplication.instance()
            en_hilo_gui = app_qt is not None and QThread.currentThread() is app_qt.thread()

            if app_qt is not None and not en_hilo_gui:
                logger.critical(
                    "Excepción en un hilo secundario: no se muestra diálogo "
                    "(crear widgets fuera del hilo GUI cierra la aplicación)"
                )

            if en_hilo_gui:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Error inesperado")
                msg.setText(
                    "Se ha producido un error inesperado en la aplicación.\n"
                    "El incidente ha sido registrado en el log."
                )
                msg.setDetailedText(
                    f"{exctype.__name__}: {value}\n\n" + "".join(traceback.format_tb(tb))
                )
                msg.exec()
        except (RuntimeError, AttributeError):
            pass  # Si Qt no está disponible, solo loguear

        # Llamar al manejador original
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = exception_hook
    logger.info("✓ Manejador global de excepciones instalado")

    # UX-04: DPI awareness — PassThrough evita escalado redondeado en pantallas HiDPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Crear la aplicación
    app = QApplication(sys.argv)

    # Manejar señales de terminación para graceful shutdown
    import signal

    signal.signal(signal.SIGTERM, lambda s, f: app.quit())
    signal.signal(signal.SIGINT, lambda s, f: app.quit())

    # Aplicar branding corporativo a todos los QMessageBox
    apply_corporate_branding()

    # Fuente y hoja de estilos ANTES de mostrar nada: el diálogo de configuración
    # inicial se abría sin estilos, porque se aplicaban más abajo (VIS-001).
    from presentation.theme.hoja_de_estilos import construir_hoja_de_estilos
    from presentation.theme.tokens import cuerpo_del_sistema, familias_del_sistema

    font = QFont()
    font.setFamilies(familias_del_sistema())
    font.setPointSize(cuerpo_del_sistema())
    app.setFont(font)

    hoja = construir_hoja_de_estilos()
    if hoja:
        app.setStyleSheet(hoja)

    # ==========================================
    # Validar Configuración Inicial (SFTP/SMTP)
    # ==========================================

    from core.paths import get_base_directory
    from presentation.dialogs.initial_config_dialog import InitialConfigDialog

    # Cargar configuración persistente antes de validarla
    env_path = get_base_directory() / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

    # Las contraseñas que sigan en el fichero se llevan al llavero del sistema, se
    # restringen los permisos y se borran los rastros que dejaron las versiones
    # anteriores: carpetas del esquema viejo y volcados con credenciales dentro.
    # Sólo actúa si las contraseñas están ya a salvo en el llavero (SEC-001).
    from core.limpieza_de_rastros import revisar_y_limpiar

    revisar_y_limpiar(get_base_directory())

    # Verificar si es necesario configurar SFTP/SMTP
    if InitialConfigDialog.is_configuration_needed():
        logger.info("Configuración inicial requerida. Mostrando diálogo...")

        config_dialog = InitialConfigDialog()
        if config_dialog.exec() != InitialConfigDialog.DialogCode.Accepted:
            # Antes esto cerraba la aplicación: sin servidor no se podía ni entrar,
            # lo que impedía preparar un curso en un portátil sin red (UXF-005).
            logger.info("Configuración inicial cancelada. Se ofrece el modo local.")
            eleccion = QMessageBox(
                QMessageBox.Icon.Warning,
                "Sin servidor de sincronización",
                "No has configurado el servidor.",
            )
            eleccion.setInformativeText(
                "Puedes trabajar solo en este equipo, pero ten en cuenta que:\n\n"
                "• Los datos NO se copiarán al servidor.\n"
                "• No podrás abrirlos desde otro ordenador.\n"
                "• No habrá copia de seguridad fuera de este equipo.\n\n"
                "Podrás configurarlo más tarde en Ajustes."
            )
            boton_local = eleccion.addButton(
                "Trabajar solo en este equipo", QMessageBox.ButtonRole.AcceptRole
            )
            eleccion.addButton("Salir", QMessageBox.ButtonRole.RejectRole)
            eleccion.setDefaultButton(boton_local)
            eleccion.exec()

            if eleccion.clickedButton() is not boton_local:
                logger.info("El usuario prefiere salir a trabajar sin servidor.")
                return 0

            logger.warning("Arrancando en modo local: esta sesión no sincroniza.")
        else:
            logger.info("✓ Configuración inicial completada")

    # ==========================================
    # Configurar traducción al español
    # ==========================================

    # Configurar el locale para toda la aplicación (calendarios, fechas, números)
    spanish_locale = QLocale(QLocale.Language.Spanish, QLocale.Country.Spain)
    QLocale.setDefault(spanish_locale)

    # Cargar traducciones de Qt (para botones estándar como Yes/No)
    qt_translator = QTranslator()
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)

    if qt_translator.load(
        QLocale(QLocale.Language.Spanish, QLocale.Country.Spain), "qtbase", "_", translations_path
    ):
        app.installTranslator(qt_translator)
        logger.info("✓ Traducción de Qt al español cargada")
    else:
        logger.warning("⚠ No se pudo cargar la traducción de Qt al español")

    # ==========================================
    # Sistema de Login y Sincronización SFTP
    # ==========================================

    # ==========================================
    # Conexión con el servidor, antes del login
    # ==========================================
    # La cuenta vive junto a los datos del usuario en el servidor, así que hace
    # falta la conexión ya para poder validarla desde cualquier equipo.
    backend = None
    sin_sincronizacion = None
    try:
        backend = get_default_backend()
        logger.info("✓ Servidor de sincronización disponible")
    except SyncConfigurationError as e:
        sin_sincronizacion = e
        # Un equipo nuevo no tiene el servidor en `known_hosts` y la conexión se
        # rechaza por seguridad. Antes de rendirse, enseñar la huella del servidor
        # y dejar que quien está delante la confirme (SEC-008).
        from presentation.dialogs.huella_servidor_dialog import confirmar_huella_si_hace_falta

        if confirmar_huella_si_hace_falta():
            try:
                backend = get_default_backend()
                sin_sincronizacion = None
                logger.info("✓ Servidor disponible tras confirmar la huella")
            except SyncConfigurationError as otro:
                sin_sincronizacion = otro

    if sin_sincronizacion is not None:
        logger.error(f"Sin sincronización: {sin_sincronizacion}")
        from utils.ui_helpers import get_corporate_icon

        aviso = QMessageBox()
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowTitle("Sin sincronización con la nube")
        aviso.setWindowIcon(get_corporate_icon())
        aviso.setText("Esta sesión NO se sincronizará con la nube.")
        aviso.setInformativeText(
            f"{sin_sincronizacion}\n\nPodrás entrar con las cuentas de este equipo, pero "
            "todo lo que hagas se guardará únicamente aquí: no se subirá al servidor ni lo "
            "verás desde otro ordenador.\n\nRevisa los datos de conexión en Ajustes."
        )
        aviso.exec()

    # Mostrar diálogo de login
    login_dialog = LoginDialog(backend=backend)
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
        logger.info("Usuario canceló el login. Saliendo de la aplicación.")
        return 0

    username = login_dialog.authenticated_user
    logger.info(f"Usuario autenticado: {username}")

    # Entre aquí y la ventana principal hay pasos que hablan con la red y pueden
    # tardar. Sin esto la pantalla se queda vacía y parece que no arranca (ESC-006).
    from presentation.widgets.pantalla_de_arranque import abrir_pantalla_de_arranque

    arranque = abrir_pantalla_de_arranque()

    def ocultar_arranque() -> None:
        """Quita la pantalla de arranque antes de un aviso.

        Va siempre por encima de todo, así que un `QMessageBox` sin padre queda
        detrás y sus botones no reciben el clic: la aplicación se quedaba
        bloqueada en el aviso, sin poder aceptarlo ni seguir (UXF-012).
        """
        if arranque is not None:
            arranque.hide()

    def paso(mensaje: str) -> None:
        if arranque is not None:
            arranque.paso(mensaje)

    paso("Preparando la base de datos…")

    # Inicializar base de datos específica del usuario
    from database.db_manager import initialize_user_database

    try:
        engine, SessionFactory = initialize_user_database(username)
        logger.info(f"Base de datos del usuario '{username}' inicializada")
    except Exception as e:
        logger.exception(f"Error inicializando base de datos para '{username}': {e}")
        QMessageBox.critical(
            None,
            "Error de inicialización",
            f"No se pudo inicializar la base de datos del usuario.\n\nDetalle: {e}",
        )
        return 1

    # 🔧 ARQ-04: Wiring DI (Fase 2 — Opcional, sin romper compatibilidad legacy)
    # Descomenta estas líneas para usar inyección de dependencias en servicios:
    # from infrastructure.wiring import setup_container
    # setup_container(SessionFactory)
    # logger.debug("Contenedor DI configurado para servicios inyectados")

    # Crear sesión de base de datos (necesaria para sync)
    try:
        session = SessionFactory()
    except Exception as e:
        logger.exception(f"Error creando sesión de base de datos: {e}")
        QMessageBox.critical(
            None,
            "Error de base de datos",
            f"No se pudo abrir la sesión de base de datos.\n\nDetalle: {e}",
        )
        return 1

    # 🔄 Ejecutar migración automática al sistema Multi-Curso si es necesario
    paso("Comprobando el formato de los datos…")
    try:
        from services.migrar_a_multi_curso import ejecutar_migracion_si_necesario

        if ejecutar_migracion_si_necesario(session):
            logger.info("✅ Migración al sistema Multi-Curso completada")
        else:
            logger.info("✅ Sistema Multi-Curso: datos ya migrados")
    except Exception as e:
        logger.error(f"⚠ Error en migración Multi-Curso: {e}")
        # Continuar de todos modos - la migración no es crítica para funcionar

    # Inicializar sistema de sincronización
    sync_manager = None
    session_lock_manager = None
    disable_session_lock = os.getenv("DISABLE_SESSION_LOCK", "0") == "1"
    try:
        if backend is None:
            raise SyncConfigurationError("No hay servidor de sincronización disponible")
        sync_manager = SyncManager(backend, username, clave_datos=login_dialog.clave_datos)

        # Sistema de bloqueo de sesión única
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog
        from sync.session_lock import SessionLock, SessionLockManager

        if disable_session_lock:
            logger.warning("⚠ Bloqueo de sesión desactivado por entorno (DISABLE_SESSION_LOCK=1)")
        else:
            paso("Comprobando que la cuenta no esté abierta en otro equipo…")
            session_lock = SessionLock(backend, username, sync_manager.user_hash)

            # Intentar adquirir el bloqueo de sesión
            max_retries = 3
            for attempt in range(max_retries):
                if session_lock.acquire_lock():
                    logger.info(f"✅ Bloqueo de sesión adquirido (intento {attempt + 1})")
                    break
                else:
                    # Mostrar diálogo informativo
                    lock_info = session_lock.get_lock_info()
                    if lock_info:
                        locked_dialog = SessionLockedDialog(lock_info)
                        ocultar_arranque()
                        result = locked_dialog.exec()

                        if result == SessionLockedDialog.DialogCode.Rejected:
                            # Usuario canceló
                            logger.info("Usuario canceló debido a sesión bloqueada")
                            session.close()
                            return 0
                        # Si aceptó (Reintentar), continúa el loop
                    else:
                        # Sin poder leer el bloqueo no se puede saber si hay otra
                        # sesión abierta. Ante la duda no se entra: entrar y subir
                        # después machacaría el trabajo de quien esté dentro.
                        logger.error("No se pudo obtener información del bloqueo")
                        QMessageBox.critical(
                            None,
                            "No se puede comprobar la sesión",
                            "No se ha podido comprobar si la cuenta está abierta en otro "
                            "equipo.\n\nPara no arriesgar los datos, la aplicación no se "
                            "abrirá. Inténtalo de nuevo cuando haya conexión.",
                        )
                        session.close()
                        return 1
            else:
                # Se agotaron los reintentos
                QMessageBox.critical(
                    None,
                    "Sesión Bloqueada",
                    "No se pudo iniciar sesión después de varios intentos.\n"
                    "El usuario está activo en otro dispositivo.",
                )
                session.close()
                return 1

            # Crear gestor de heartbeat
            session_lock_manager = SessionLockManager(session_lock)

        # Sincronizar datos al iniciar (descargar desde la nube e importar a DB)
        paso("Trayendo los datos de la nube…")
        if sync_manager.sync_on_startup(session=session):
            logger.info("✓ Sincronización inicial completada")
        else:
            # Sin haber traído los datos de la nube, esta sesión trabaja sobre una
            # copia que puede estar vieja. Se avisa y se prohíbe subir al cerrar.
            motivo = sync_manager.motivo_bloqueo or "no se pudieron descargar los datos"
            logger.warning(f"⚠ Sincronización inicial fallida: {motivo}")
            ocultar_arranque()
            aviso = QMessageBox()
            aviso.setIcon(QMessageBox.Icon.Warning)
            aviso.setWindowTitle("Sin datos actualizados")
            aviso.setText("No se han podido traer los datos de la nube.")
            aviso.setInformativeText(
                f"{motivo}\n\nPuedes consultar lo que hay en este equipo, pero los "
                "cambios NO se subirán al cerrar, para no sobrescribir el trabajo "
                "que haya en la nube."
            )
            aviso.exec()

    except SyncConfigurationError as e:
        # Sin nube no se finge que la hay: el usuario tiene que saber que su
        # trabajo se queda en este equipo y no llegará a los demás.
        sync_manager = None
        logger.error(f"Sin sincronización: {e}")
        ocultar_arranque()
        from utils.ui_helpers import get_corporate_icon

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Sin sincronización con la nube")
        msg.setWindowIcon(get_corporate_icon())
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        msg.setText("Esta sesión NO se sincronizará con la nube.")
        msg.setInformativeText(
            f"{e}\n\nTodo lo que hagas se guardará únicamente en este equipo. No se "
            "subirá al servidor ni lo verás desde otro ordenador.\n\n"
            "Revisa los datos de conexión en Ajustes."
        )
        msg.exec()
    except Exception as e:
        sync_manager = None
        logger.exception(f"Error al inicializar sincronización: {e}")
        ocultar_arranque()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Sin sincronización con la nube")
        msg.setText("Esta sesión NO se sincronizará con la nube.")
        msg.setInformativeText(
            f"{e}\n\nTodo lo que hagas se guardará únicamente en este equipo."
        )
        msg.exec()

    # ==========================================
    # Ventana Principal
    # ==========================================

    exit_code = 1  # Código de salida por defecto (error)

    try:
        # Crear ventana principal
        paso("Abriendo la ventana…")
        window = VentanaPrincipal(session, sync_manager=sync_manager)  # noqa: F841
        logger.info("Ventana principal creada exitosamente")
        if arranque is not None:
            arranque.terminar(window)

        # La ventana ya se muestra maximizada desde su __init__
        # No necesitamos hacer nada más aquí

        # Iniciar sistema de heartbeat para mantener el bloqueo activo
        if session_lock_manager:
            session_lock_manager.start_heartbeat(app)

        # Ejecutar la aplicación
        logger.info("Iniciando event loop de Qt...")
        exit_code = app.exec()

    except Exception as e:
        logger.exception(f"Error fatal al crear o ejecutar la ventana principal: {e}")
        import traceback

        traceback.print_exc()
        exit_code = 1  # Código de error

    finally:
        # Detener heartbeat
        if session_lock_manager:
            session_lock_manager.stop_heartbeat()

        # Sincronizar datos al cerrar (exportar DB a JSON y subir a la nube)
        if sync_manager:
            # Siempre intentar sincronizar - el backend puede reconectar si es necesario
            # No verificar si sftp es None porque _ensure_connected() puede reconectar
            backend_disponible = True
            if hasattr(sync_manager.backend, "base_path"):
                # Solo verificar LocalBackend
                backend_disponible = sync_manager.backend.base_path is not None

            if backend_disponible:
                logger.info("Cerrando aplicación. Sincronizando cambios...")

                from presentation.widgets.sync_progress_dialog import SyncProgressDialog, SyncWorker

                progress_dialog = SyncProgressDialog()

                # Worker ejecuta la sync en hilo separado — no bloquea GUI
                worker = SyncWorker(sync_manager)  # abre su propia sesión (CRW-003)

                def on_progress(step: str, details: dict):
                    if step == "exporting":
                        from application.app_services import AppServices

                        try:
                            svc = AppServices(session)
                            total = (
                                len(svc.profesores.get_all())
                                + len(svc.zonas.get_all())
                                + svc.contar_guardias()
                            )
                        except (ValueError, TypeError, AttributeError):
                            total = 0
                        progress_dialog.set_step_exporting(total)
                    elif step == "connecting":
                        progress_dialog.set_step_connecting()
                    elif step == "uploading":
                        progress_dialog.set_step_uploading(details.get("file_size_kb", 0))
                    elif step == "complete":
                        progress_dialog.set_step_complete(success=True)
                    elif step == "error":
                        progress_dialog.set_step_error(details.get("message", "Error desconocido"))

                def on_finished(success: bool):
                    if success:
                        logger.info("✓ Sincronización final completada")
                    else:
                        logger.warning("⚠ La sincronización final tuvo problemas")
                        progress_dialog.set_step_complete(success=False)

                worker.progress_updated.connect(on_progress)
                worker.finished.connect(on_finished)
                worker.start()

                progress_dialog.exec()
                worker.wait()  # Asegurar que el hilo termina antes de liberar recursos
            else:
                logger.info(
                    "Backend de sincronización no disponible. Omitiendo sincronización final."
                )

        # Liberar bloqueo de sesión
        if session_lock_manager:
            session_lock_manager.cleanup()

        # Cerrar sesión de base de datos
        session.close()

        # Cerrar backend de sincronización si existe
        if sync_manager and hasattr(sync_manager.backend, "close"):
            try:
                sync_manager.backend.close()
            except Exception as e:
                logger.error(f"Error al cerrar backend de sincronización: {e}")

        return exit_code


if __name__ == "__main__":
    main()
