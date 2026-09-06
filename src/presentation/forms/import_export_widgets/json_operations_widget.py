"""
Widget para operaciones de JSON (exportar/importar).

Agrupa las funcionalidades de exportación e importación de datos en JSON.
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from presentation.themes.tema_aplicacion import ERROR_RED, TEXT_SECONDARY
from utils.icons import icon_for_button


class JsonOperationsWidget(QWidget):
    """Widget que encapsula las operaciones de exportar/importar JSON."""

    # Señales para comunicar acciones al formulario padre
    exportar_solicitado = pyqtSignal()
    importar_solicitado = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializar el widget de operaciones JSON.

        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Construir la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Sección de exportación
        layout.addWidget(self._crear_grupo_exportar())

        # Sección de importación
        layout.addWidget(self._crear_grupo_importar())

        # Stretch al final
        layout.addStretch()

    def _crear_grupo_exportar(self) -> QGroupBox:
        """Crear grupo de exportación a JSON."""
        grupo = QGroupBox("EXPORTAR DATOS A JSON")

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Información
        info = QLabel(
            "Exporta todos los datos actuales a un archivo JSON para respaldo "
            "o transferencia a otro equipo."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            font-weight: normal;
        """
        )
        layout.addWidget(info)

        # Botón de exportación
        self.exportar_btn = QPushButton("Exportar a JSON...")
        self.exportar_btn.setIcon(icon_for_button("export"))
        self.exportar_btn.clicked.connect(self.exportar_solicitado.emit)
        self.exportar_btn.setMinimumHeight(40)
        layout.addWidget(self.exportar_btn)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_importar(self) -> QGroupBox:
        """Crear grupo de importación desde JSON."""
        grupo = QGroupBox("IMPORTAR DATOS DESDE JSON")

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Advertencia
        info = QLabel("ATENCIÓN: Esto puede ELIMINAR los datos actuales si activas la opción.")
        info.setWordWrap(True)
        info.setStyleSheet(
            f"""
            color: {ERROR_RED};
            font-size: 12px;
            font-weight: bold;
            padding: 5px;
        """
        )
        layout.addWidget(info)

        # Checkbox de limpiar
        self.limpiar_checkbox = QCheckBox("Eliminar datos existentes antes de importar")
        self.limpiar_checkbox.setChecked(True)
        self.limpiar_checkbox.setStyleSheet(
            f"""
            QCheckBox {{
                font-size: 12px;
                font-weight: normal;
                color: {TEXT_SECONDARY};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
        """
        )
        layout.addWidget(self.limpiar_checkbox)

        # Botón de importación
        self.importar_btn = QPushButton("Importar desde JSON...")
        self.importar_btn.setIcon(icon_for_button("import"))
        self.importar_btn.clicked.connect(self.importar_solicitado.emit)
        self.importar_btn.setMinimumHeight(40)
        self.importar_btn.setProperty("warning", "true")
        layout.addWidget(self.importar_btn)

        grupo.setLayout(layout)
        return grupo

    # ========== API PÚBLICA ==========

    def debe_limpiar_datos(self) -> bool:
        """
        Obtener si se debe limpiar datos antes de importar.

        Returns:
            True si el checkbox está marcado
        """
        return self.limpiar_checkbox.isChecked()

    def set_limpiar_datos(self, limpiar: bool):
        """
        Establecer el estado del checkbox de limpiar datos.

        Args:
            limpiar: True para marcar el checkbox
        """
        self.limpiar_checkbox.setChecked(limpiar)

    def habilitar_exportar(self, habilitado: bool):
        """
        Habilitar/deshabilitar el botón de exportar.

        Args:
            habilitado: True para habilitar
        """
        self.exportar_btn.setEnabled(habilitado)

    def habilitar_importar(self, habilitado: bool):
        """
        Habilitar/deshabilitar el botón de importar.

        Args:
            habilitado: True para habilitar
        """
        self.importar_btn.setEnabled(habilitado)
