"""
Punto de entrada para la aplicación con diseño CCleaner
========================================================
Ejecutar: python src/main_ccleaner.py
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurar logging ANTES de cualquier import
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

from presentation.ccleaner_main_window import CCleanerMainWindow
from presentation.forms.login_dialog import LoginDialog
from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMessageBox
from sync import SyncManager, get_default_backend
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
        thread_name = getattr(thread, 'name', 'Unknown')
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

        # Llamar al manejador original
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = exception_hook
    logger.info("✓ Manejador global de excepciones instalado")

    # Crear la aplicación
    app = QApplication(sys.argv)

    # Aplicar branding corporativo a todos los QMessageBox
    apply_corporate_branding()

    # ==========================================
    # Validar Configuración Inicial (SFTP/SMTP)
    # ==========================================

    from presentation.dialogs.initial_config_dialog import InitialConfigDialog

    # Verificar si es necesario configurar SFTP/SMTP
    if InitialConfigDialog.is_configuration_needed():
        logger.info("Configuración inicial requerida. Mostrando diálogo...")

        config_dialog = InitialConfigDialog()
        if config_dialog.exec() != InitialConfigDialog.DialogCode.Accepted:
            logger.info("Usuario canceló la configuración inicial. Saliendo...")
            QMessageBox.critical(
                None,
                "Configuración Incompleta",
                "No se puede iniciar la aplicación sin configurar SFTP.\n\n"
                "El servidor SFTP es necesario para garantizar copias de seguridad "
                "y sincronización de datos.",
            )
            sys.exit(0)

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

    # Configurar fuente global
    font = QFont("-apple-system")
    font.setPointSize(14)
    app.setFont(font)

    # Aplicar stylesheet global a toda la aplicación
    from presentation.themes.ccleaner_theme import get_complete_stylesheet

    app.setStyleSheet(get_complete_stylesheet())

    # ==========================================
    # Sistema de Login y Sincronización SFTP
    # ==========================================

    # Mostrar diálogo de login
    login_dialog = LoginDialog()
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
        logger.info("Usuario canceló el login. Saliendo de la aplicación.")
        sys.exit(0)

    username = login_dialog.authenticated_user
    logger.info(f"Usuario autenticado: {username}")

    # Inicializar base de datos específica del usuario
    from database.db_manager import initialize_user_database

    engine, SessionFactory = initialize_user_database(username)
    logger.info(f"Base de datos del usuario '{username}' inicializada")

    # Crear sesión de base de datos (necesaria para sync)
    session = SessionFactory()

    # 🔄 Ejecutar migración automática al sistema Multi-Curso si es necesario
    logger.error("🔧 INICIANDO: Migración Multi-Curso")
    try:
        from services.migrar_a_multi_curso import ejecutar_migracion_si_necesario

        if ejecutar_migracion_si_necesario(session):
            logger.info("✅ Migración al sistema Multi-Curso completada")
        else:
            logger.info("✅ Sistema Multi-Curso: datos ya migrados")
    except Exception as e:
        logger.error(f"⚠ Error en migración Multi-Curso: {e}")
        # Continuar de todos modos - la migración no es crítica para funcionar

    logger.error("🔧 INICIANDO: Sistema de sincronización")
    # Inicializar sistema de sincronización
    sync_manager = None
    session_lock_manager = None
    try:
        backend = get_default_backend()
        sync_manager = SyncManager(backend, username)

        # Sistema de bloqueo de sesión única
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog
        from sync.session_lock import SessionLock, SessionLockManager

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
                    result = locked_dialog.exec()

                    if result == SessionLockedDialog.DialogCode.Rejected:
                        # Usuario canceló
                        logger.info("Usuario canceló debido a sesión bloqueada")
                        session.close()
                        sys.exit(0)
                    # Si aceptó (Reintentar), continúa el loop
                else:
                    logger.error("No se pudo obtener información del bloqueo")
                    break
        else:
            # Se agotaron los reintentos
            QMessageBox.critical(
                None,
                "Sesión Bloqueada",
                "No se pudo iniciar sesión después de varios intentos.\n"
                "El usuario está activo en otro dispositivo.",
            )
            session.close()
            sys.exit(1)

        # Crear gestor de heartbeat
        session_lock_manager = SessionLockManager(session_lock)

        # Sincronizar datos al iniciar (descargar desde la nube e importar a DB)
        logger.info("Iniciando sincronización al arranque...")
        if sync_manager.sync_on_startup(session=session):
            logger.info("✓ Sincronización inicial completada")
        else:
            logger.warning("⚠ La sincronización inicial tuvo problemas (continuar de todos modos)")

    except Exception as e:
        logger.error(f"Error al inicializar sincronización: {e}")
        from PyQt6.QtCore import Qt
        from utils.ui_helpers import MESSAGEBOX_STYLE, get_corporate_icon

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Aviso de Sincronización")
        msg.setWindowIcon(get_corporate_icon())
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        msg.setText("No se pudo conectar al servidor de sincronización.")
        msg.setInformativeText(
            "La aplicación funcionará en modo local.\n\n"
            "Los datos se guardarán solo en este equipo."
        )
        msg.setStyleSheet(MESSAGEBOX_STYLE)
        msg.exec()

    # ==========================================
    # Ventana Principal
    # ==========================================

    exit_code = 1  # Código de salida por defecto (error)

    try:
        # Crear ventana principal
        logger.info("Creando ventana principal...")
        window = CCleanerMainWindow(session, sync_manager=sync_manager)  # noqa: F841
        logger.info("Ventana principal creada exitosamente")

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

        print("=" * 80)
        print("ERROR FATAL:")
        print("=" * 80)
        traceback.print_exc()
        print("=" * 80)
        exit_code = 1  # Código de error

    finally:
        # Detener heartbeat
        if session_lock_manager:
            session_lock_manager.stop_heartbeat()

        # Sincronizar datos al cerrar (exportar DB a JSON y subir a la nube)
        if sync_manager:
            # Verificar si el backend está disponible antes de intentar sincronizar
            backend_disponible = True
            if hasattr(sync_manager.backend, 'sftp'):
                backend_disponible = sync_manager.backend.sftp is not None
            elif hasattr(sync_manager.backend, 'base_path'):
                backend_disponible = sync_manager.backend.base_path is not None

            if backend_disponible:
                logger.info("Cerrando aplicación. Sincronizando cambios...")

                # Importar el diálogo de progreso
                from presentation.widgets.sync_progress_dialog import SyncProgressDialog

                # Crear diálogo de progreso
                progress_dialog = SyncProgressDialog()
                progress_dialog.show()

                # Callback de progreso
                def on_progress(step: str, details: dict):
                    """Actualiza el diálogo según el paso de sincronización."""
                    if step == "exporting":
                        # Contar registros (aproximado)
                        from models.models import Ausencia, Guardia, Profesor, Zona

                        try:
                            total = (
                                session.query(Profesor).count()
                                + session.query(Zona).count()
                                + session.query(Guardia).count()
                                + session.query(Ausencia).count()
                            )
                            progress_dialog.set_step_exporting(total)
                        except Exception as e:
                            logger.error(f"Error contando registros: {e}")
                            progress_dialog.set_step_exporting(0)

                    elif step == "connecting":
                        progress_dialog.set_step_connecting()

                    elif step == "uploading":
                        file_size_kb = details.get("file_size_kb", 0)
                        progress_dialog.set_step_uploading(file_size_kb)

                    elif step == "complete":
                        progress_dialog.set_step_complete(success=True)

                    elif step == "error":
                        error_msg = details.get("message", "Error desconocido")
                        progress_dialog.set_step_error(error_msg)

                try:
                    # Ejecutar sincronización con callback de progreso
                    success = sync_manager.sync_on_shutdown(
                        session=session, progress_callback=on_progress
                    )

                    if success:
                        logger.info("✓ Sincronización final completada")
                    else:
                        logger.warning("⚠ La sincronización final tuvo problemas")

                except Exception as e:
                    logger.error(f"Error en sincronización final: {e}")
                    progress_dialog.set_step_error(str(e))

                # Esperar a que el usuario cierre el diálogo
                progress_dialog.exec()
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

        sys.exit(exit_code)


if __name__ == "__main__":
    main()
