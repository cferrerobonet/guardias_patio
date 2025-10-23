"""
Guardias de Patio - Aplicación Principal.

Entry point de la aplicación de gestión de guardias de patio.
"""

import sys

from core.app_initializer import initialize_application, initialize_logging, run_smoke_test
from presentation.main_window import MainWindow

# Configurar logging al inicio
initialize_logging()


def main():
    """Función principal de la aplicación."""
    # Smoke test para validación
    run_smoke_test()

    # Inicializar aplicación y obtener instancia
    app = initialize_application()
    if not app:
        return

    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

