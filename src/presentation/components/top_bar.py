"""
Barra superior (Top Bar) con breadcrumbs y acciones rápidas.

Componente que muestra la navegación actual y acciones globales.
"""

from core.qt_imports import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from presentation.themes.fluent_theme import (
    SPACING_M,
    SPACING_S,
    get_topbar_style,
)


class TopBar(QWidget):
    """Barra superior con breadcrumbs y acciones."""

    def __init__(self, parent=None):
        """Inicializa la barra superior."""
        super().__init__(parent)
        self.setObjectName("topbar")

        # Layout principal
        layout = QHBoxLayout()
        layout.setContentsMargins(SPACING_M, SPACING_S, SPACING_M, SPACING_S)
        layout.setSpacing(SPACING_M)

        # Breadcrumb (navegación)
        self.breadcrumb_label = QLabel("Inicio")
        self.breadcrumb_label.setObjectName("breadcrumb")
        layout.addWidget(self.breadcrumb_label)

        layout.addStretch()

        # Botones de acción rápida (usuario, configuración, etc.)
        self.user_btn = QPushButton("👤")
        self.user_btn.setObjectName("topbarButton")
        self.user_btn.setToolTip("Usuario")
        self.user_btn.setFixedSize(36, 36)
        layout.addWidget(self.user_btn)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("topbarButton")
        self.settings_btn.setToolTip("Configuración")
        self.settings_btn.setFixedSize(36, 36)
        layout.addWidget(self.settings_btn)

        self.help_btn = QPushButton("❓")
        self.help_btn.setObjectName("topbarButton")
        self.help_btn.setToolTip("Ayuda")
        self.help_btn.setFixedSize(36, 36)
        layout.addWidget(self.help_btn)

        self.setLayout(layout)

        # Aplicar estilo
        self.setStyleSheet(get_topbar_style())

    def set_breadcrumb(self, text: str):
        """
        Actualiza el breadcrumb con el texto dado.

        Args:
            text: Texto a mostrar en el breadcrumb
        """
        self.breadcrumb_label.setText(text)

    def set_breadcrumb_path(self, items: list[str]):
        """
        Actualiza el breadcrumb con una ruta.

        Args:
            items: Lista de items de la ruta (ej: ["Gestión", "Profesores"])
        """
        if not items:
            self.breadcrumb_label.setText("Inicio")
            return

        # Crear breadcrumb con separadores
        breadcrumb_html = ""
        for i, item in enumerate(items):
            if i > 0:
                breadcrumb_html += ' <span style="color: #A19F9D;">›</span> '
            breadcrumb_html += f'<span>{item}</span>'

        self.breadcrumb_label.setText(breadcrumb_html)
