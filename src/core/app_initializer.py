"""
Inicializador de la aplicación.

Maneja la configuración inicial, logging, y setup de PyQt6.
"""

import os
import sys
from typing import TYPE_CHECKING, Optional

from utils import setup_logging
from utils.corporate_branding import apply_corporate_branding

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication


def initialize_logging() -> None:
    """Configura el sistema de logging."""
    setup_logging()


def configure_qt_plugins() -> None:
    """
    Configura los plugins de Qt.

    Fix para el error de Qt platform plugin, común en aplicaciones
    empaquetadas o entornos específicos.
    """
    try:
        import PyQt6

        qt_plugin_path = os.path.join(
            os.path.dirname(PyQt6.__file__), "Qt", "plugins"
        )
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugin_path
        print(f"Setting QT_QPA_PLATFORM_PLUGIN_PATH to: {qt_plugin_path}")
    except Exception as e:
        print(f"Warning: Could not set QT_QPA_PLATFORM_PLUGIN_PATH: {e}")


def initialize_application() -> Optional["QApplication"]:
    """
    Inicializa la aplicación Qt.

    Returns:
        QApplication instancia o None si no está en modo GUI
    """
    # Modo prueba: evitar GUI en tests
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return None

    try:
        from PyQt6.QtWidgets import QApplication

        configure_qt_plugins()
        app = QApplication(sys.argv)
        apply_corporate_branding()
        return app
    except ImportError:
        print("PyQt6 no disponible. Ejecutando en modo headless.")
        return None


def run_smoke_test() -> None:
    """Ejecuta smoke test básico (usado por tests)."""
    print("¡Hola mundo desde Guardias de Patio!")
