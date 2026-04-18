#!/usr/bin/env python3
"""
Script de prueba para el diálogo de configuración inicial.

Ejecutar: python scripts/test_initial_config.py
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication

from src.presentation.dialogs.initial_config_dialog import InitialConfigDialog


def main():
    """Prueba el diálogo de configuración inicial."""
    QApplication(sys.argv)

    # Verificar si es necesario mostrar el diálogo
    if InitialConfigDialog.is_configuration_needed():
        print("✅ Se requiere configuración inicial")

        dialog = InitialConfigDialog()
        result = dialog.exec()

        if result == InitialConfigDialog.DialogCode.Accepted:
            print("✅ Configuración completada exitosamente")
        else:
            print("❌ Configuración cancelada")
    else:
        print("✅ La configuración ya está completa")
        print("Mostrando diálogo de todos modos para prueba...")

        dialog = InitialConfigDialog()
        result = dialog.exec()

        if result == InitialConfigDialog.DialogCode.Accepted:
            print("✅ Configuración actualizada")
        else:
            print("❌ No se hicieron cambios")

    sys.exit(0)


if __name__ == "__main__":
    main()
