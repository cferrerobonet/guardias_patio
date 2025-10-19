#!/usr/bin/env python3
"""
Test del branding corporativo en modales.

Ejecuta una pequeña demo que muestra diferentes tipos de modales
para verificar que el logo corporativo se aplica correctamente.
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton, QVBoxLayout, QWidget

from utils.corporate_branding import apply_corporate_branding
from utils.ui_helpers import get_corporate_icon


class TestWindow(QWidget):
    """Ventana de prueba para el branding corporativo."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Branding Corporativo")
        self.setWindowIcon(get_corporate_icon())
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Botón para mensaje de información
        btn_info = QPushButton("🔵 Mostrar Información")
        btn_info.clicked.connect(self.show_info)
        layout.addWidget(btn_info)

        # Botón para advertencia
        btn_warning = QPushButton("🟡 Mostrar Advertencia")
        btn_warning.clicked.connect(self.show_warning)
        layout.addWidget(btn_warning)

        # Botón para error
        btn_error = QPushButton("🔴 Mostrar Error")
        btn_error.clicked.connect(self.show_error)
        layout.addWidget(btn_error)

        # Botón para pregunta
        btn_question = QPushButton("❓ Mostrar Pregunta")
        btn_question.clicked.connect(self.show_question)
        layout.addWidget(btn_question)

        # Botón para salir
        btn_exit = QPushButton("❌ Salir")
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

        self.setLayout(layout)

    def show_info(self):
        """Muestra un mensaje de información."""
        QMessageBox.information(
            self,
            "Guardias Asignadas",
            "2237 guardias eliminadas. Generando calendario nuevo..."
        )

    def show_warning(self):
        """Muestra una advertencia."""
        QMessageBox.warning(
            self,
            "Advertencia",
            "483 slots sin cubrir (puede deberse a falta de elegibilidad de profesores)"
        )

    def show_error(self):
        """Muestra un error."""
        QMessageBox.critical(
            self,
            "Error",
            "No se puede completar la operación:\n\nError de validación en los datos"
        )

    def show_question(self):
        """Muestra una pregunta."""
        respuesta = QMessageBox.question(
            self,
            "Confirmar Acción",
            "¿Deseas eliminar todas las guardias existentes y generar un nuevo calendario?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Confirmado", "Operación confirmada")
        else:
            QMessageBox.information(self, "Cancelado", "Operación cancelada")


def main():
    """Ejecuta la aplicación de prueba."""
    app = QApplication(sys.argv)

    # Aplicar branding corporativo
    print("✅ Aplicando branding corporativo...")
    apply_corporate_branding()

    # Crear y mostrar ventana
    window = TestWindow()
    window.show()

    print("📱 Ventana de prueba abierta")
    print("👆 Haz clic en los botones para probar los diferentes tipos de modales")
    print("🔍 Verifica que el logo corporativo aparece en la barra de título de cada modal")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
