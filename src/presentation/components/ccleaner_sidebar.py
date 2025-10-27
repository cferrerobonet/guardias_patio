"""
Sidebar estilo CCleaner
=======================
Menú lateral oscuro con diseño profesional.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from presentation.themes.ccleaner_theme import (
    SIDEBAR_BG,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    get_sidebar_style,
)
from utils.icon_manager import get_icon


class SidebarMenu(QWidget):
    """Menú lateral estilo CCleaner con categorías"""

    section_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.active_button = None
        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz del sidebar"""
        # Ancho fijo más grande para evitar cortes
        self.setMinimumWidth(260)
        self.setMaximumWidth(260)

        # Aplicar estilo
        self.setStyleSheet(get_sidebar_style())

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Área de scroll para los menús (sin título)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"background-color: {SIDEBAR_BG}; border: none;")

        # Widget contenedor del menú
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, SPACING_LG, 0, SPACING_SM)
        menu_layout.setSpacing(2)

        # ========== GESTIÓN ==========
        self.add_category(menu_layout, "GESTIÓN")
        self.add_menu_item(
            menu_layout, "profesores", "Profesores", "profesores", "account-group"
        )
        self.add_menu_item(menu_layout, "zonas", "Zonas", "zonas", "map-marker")
        self.add_menu_item(
            menu_layout, "configuracion", "Configuración", "configuracion", "cog"
        )

        menu_layout.addSpacing(SPACING_MD)

        # ========== GUARDIAS ==========
        self.add_category(menu_layout, "GUARDIAS")
        self.add_menu_item(
            menu_layout, "asignacion", "Asignación", "asignacion", "check-bold"
        )
        self.add_menu_item(
            menu_layout, "calendario", "Calendario", "calendario", "calendar"
        )

        menu_layout.addSpacing(SPACING_MD)

        # ========== PERSONAL ==========
        self.add_category(menu_layout, "PERSONAL")
        self.add_menu_item(
            menu_layout, "ausencias", "Ausencias", "ausencias", "hospital-box"
        )
        self.add_menu_item(
            menu_layout, "sustituciones", "Sustituciones",
            "sustituciones", "swap-horizontal"
        )

        menu_layout.addSpacing(SPACING_MD)

        # ========== HERRAMIENTAS ==========
        self.add_category(menu_layout, "HERRAMIENTAS")
        self.add_menu_item(
            menu_layout, "importar", "Importar/Exportar",
            "importar", "database-import-export"
        )
        self.add_menu_item(
            menu_layout, "estadisticas", "Estadísticas", "estadisticas", "chart-bar"
        )
        self.add_menu_item(
            menu_layout, "observabilidad", "Observabilidad",
            "observabilidad", "chart-line"
        )

        # Espaciador al final
        menu_layout.addStretch()

        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

    def add_category(self, layout: QVBoxLayout, title: str):
        """Añadir etiqueta de categoría"""
        label = QLabel(title)
        label.setObjectName("categoryLabel")
        label.setStyleSheet("""
            QLabel#categoryLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 2px;
                text-transform: uppercase;
                padding: 20px 20px 8px 20px;
                background-color: transparent;
            }
        """)
        layout.addWidget(label)

        # Línea separadora debajo de categoría
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                max-height: 1px;
                margin: 0px 16px 12px 16px;
            }
        """)
        layout.addWidget(separator)

    def add_menu_item(
        self,
        layout: QVBoxLayout,
        object_name: str,
        text: str,
        section: str,
        icon_name: str = None
    ):
        """Añadir botón de menú con icono SVG"""
        btn = QPushButton(f" {text}")  # Espacio para separar icono del texto
        btn.setObjectName(object_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("section", section)
        btn.setProperty("active", "false")
        btn.setMinimumHeight(44)  # Altura moderada

        # Añadir icono si se proporciona
        if icon_name:
            icon = get_icon(icon_name, "white", 20)  # Iconos de 20px
            btn.setIcon(icon)
            from PyQt6.QtCore import QSize
            btn.setIconSize(QSize(20, 20))  # Tamaño fijo de 20x20

        btn.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 0.95);
                background-color: transparent;
                text-align: left;
                padding: 12px 28px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                color: white;
            }
            QPushButton[active="true"] {
                background-color: #007ACC;
                color: white;
                font-weight: 600;
            }
            QPushButton[active="true"]:hover {
                background-color: #005A9E;
            }
        """)
        btn.clicked.connect(lambda: self.on_menu_clicked(btn, section))
        layout.addWidget(btn)

    def on_menu_clicked(self, button: QPushButton, section: str):
        """Manejar clic en un elemento del menú"""
        # Desactivar el botón anterior
        if self.active_button:
            self.active_button.setProperty("active", "false")
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)

        # Activar el nuevo botón
        button.setProperty("active", "true")
        button.style().unpolish(button)
        button.style().polish(button)
        self.active_button = button

        # Emitir señal
        self.section_changed.emit(section)

    def set_active_section(self, section: str):
        """Establecer sección activa programáticamente"""
        for btn in self.findChildren(QPushButton):
            if btn.property("section") == section:
                self.on_menu_clicked(btn, section)
                break
