"""
Barra superior estilo CCleaner
===============================
Top bar blanca con breadcrumbs y acciones rápidas.
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from presentation.themes.ccleaner_theme import (
    SPACING_LG,
    get_topbar_style,
)


class TopBar(QWidget):
    """Barra superior con breadcrumbs y acciones"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz de la top bar"""
        self.setFixedHeight(56)
        self.setStyleSheet(get_topbar_style())

        # Layout horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, 0, SPACING_LG, 0)
        layout.setSpacing(SPACING_LG)

        # Breadcrumb (título de sección actual)
        self.breadcrumb_label = QLabel("Inicio")
        self.breadcrumb_label.setObjectName("breadcrumb")
        layout.addWidget(self.breadcrumb_label)

        # Espaciador
        layout.addStretch()

        # Botones de acción rápida (opcional)
        # btn_help = QPushButton("?  Ayuda")
        # btn_help.setObjectName("quickAction")
        # layout.addWidget(btn_help)

    def set_breadcrumb(self, text: str):
        """Actualizar el breadcrumb/título"""
        self.breadcrumb_label.setText(text)
