"""
Corporate Branding Patch

Aplica de forma discreta el logo corporativo a todos los QMessageBox
de la aplicación sin necesidad de modificar cada archivo.
"""

from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox

# Variable para guardar los métodos originales
_original_methods = {}


def _get_corporate_logo_path() -> Path:
    """Obtiene la ruta al logo corporativo."""
    # Desde src/utils/ subir dos niveles y entrar en imagenes/
    return Path(__file__).parent.parent.parent / "imagenes" / "logo.png"


def _apply_corporate_icon(msg_box: QMessageBox) -> None:
    """Aplica el icono corporativo a un QMessageBox."""
    try:
        logo_path = _get_corporate_logo_path()
        if logo_path.exists():
            msg_box.setWindowIcon(QIcon(str(logo_path)))
    except Exception:
        pass  # Fallo silencioso, no interrumpir la funcionalidad


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
        _apply_corporate_icon(self)
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
    _original_methods['exec'] = QMessageBox.exec
    QMessageBox.exec = _wrap_exec(_original_methods['exec'])

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
        QMessageBox.exec = _original_methods['exec']
        _original_methods.clear()
