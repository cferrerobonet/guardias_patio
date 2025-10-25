"""
Guardias de Patio - Aplicación Principal.

Entry point de la aplicación de gestión de guardias de patio.
"""

import os
import sys
from typing import NoReturn

from core.app_initializer import initialize_application, initialize_logging, run_smoke_test
from presentation.main_window import MainWindow
from utils.screen_validator import ScreenValidator

# Configurar logging al inicio
initialize_logging()


def main() -> NoReturn:
    """Función principal de la aplicación."""
    # Smoke test para validación
    run_smoke_test()

    # Inicializar aplicación y obtener instancia
    app = initialize_application()
    if not app:
        sys.exit(1)

    # Validar resolución de pantalla ANTES de crear la ventana principal
    # Solo en modo normal (no en tests o CI/CD)
    is_testing = os.environ.get('PYTEST_CURRENT_TEST') is not None
    is_ci = os.environ.get('CI') is not None or os.environ.get('GITHUB_ACTIONS') is not None

    if not is_testing and not is_ci:
        if not ScreenValidator.validate_resolution():
            ScreenValidator.show_resolution_warning()
            sys.exit(1)

        # Mostrar advertencia si está por debajo de lo recomendado
        if not ScreenValidator.show_resolution_warning():
            sys.exit(0)

    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

