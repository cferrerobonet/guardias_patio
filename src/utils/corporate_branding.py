"""
Corporate Branding Patch

Pone el icono de la app a todos los QMessageBox de la aplicación sin necesidad
de modificar cada archivo. El logo de EPLA no es el icono: se queda dentro de la
app (cabeceras, pantalla de inicio, PDF y correos).
"""

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.logging import get_logger
from utils.ui_helpers import get_app_icon

logger = get_logger(__name__)

# Variable para guardar los métodos originales
_original_methods = {}


def aplicar_icono_de_la_app(app: QApplication) -> None:
    """Icono de todas las ventanas; en Windows es también el de la barra de tareas."""
    icono = get_app_icon()
    if not icono.isNull():
        app.setWindowIcon(icono)


def _apply_app_icon(msg_box: QMessageBox) -> None:
    """Aplica el icono de la app a un QMessageBox."""
    try:
        icono = get_app_icon()
        if not icono.isNull():
            msg_box.setWindowIcon(icono)
    except (OSError, RuntimeError) as e:
        logger.debug(f"No se pudo aplicar el icono de la app: {e}")


# Wrapper para los métodos estáticos
def _wrap_static_method(original_method):
    """Crea un wrapper que aplica branding a métodos estáticos."""

    def wrapper(parent, *args, **kwargs):
        # Crear el message box usando el método original
        result = original_method(parent, *args, **kwargs)
        return result

    return wrapper


# Wrapper para exec y show
def _wrap_exec(original_exec):
    """Wrapper para exec() que aplica el icono antes de mostrar."""

    def wrapper(self, *args, **kwargs):
        _apply_app_icon(self)
        return original_exec(self, *args, **kwargs)

    return wrapper


def apply_corporate_branding():
    """
    Aplica el branding corporativo a todos los QMessageBox.

    Debe llamarse una sola vez al inicio de la aplicación.
    """
    global _original_methods

    # Solo aplicar una vez
    if _original_methods:
        return

    # Guardar y reemplazar el método exec
    _original_methods["exec"] = QMessageBox.exec
    QMessageBox.exec = _wrap_exec(_original_methods["exec"])

    # Nota: Los métodos estáticos (information, warning, critical, question)
    # crean su propio QMessageBox internamente y llaman a exec(),
    # por lo que nuestro wrapper de exec() los manejará automáticamente.


def restore_original_methods():
    """
    Restaura los métodos originales de QMessageBox.

    Útil para testing o cleanup.
    """
    global _original_methods

    if _original_methods:
        QMessageBox.exec = _original_methods["exec"]
        _original_methods.clear()
