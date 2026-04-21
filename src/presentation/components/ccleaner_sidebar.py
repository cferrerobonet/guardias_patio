"""
Sidebar estilo CCleaner
=======================
Menú lateral oscuro con diseño profesional.
"""

from pathlib import Path

from core.logging import get_logger
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from utils.icon_manager import get_icon

from presentation.themes.ccleaner_theme import (
    SIDEBAR_BG,
    get_sidebar_style,
)

logger = get_logger(__name__)

class SidebarMenu(QWidget):
    """Menú lateral estilo CCleaner con categorías"""

    section_changed = pyqtSignal(str)

    def __init__(self, parent=None, session=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.active_button = None
        self.logo_label = None  # Para actualizar el logo dinámicamente
        self.session = session  # Guardar sesión para el selector de curso
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

        # ========== SECCIÓN SUPERIOR: LOGO ==========
        # Área superior con fondo claro para el logo
        logo_section = QWidget()
        logo_section.setStyleSheet("""
            QWidget {
                background-color: #E8E8E8;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        logo_section_layout = QVBoxLayout(logo_section)
        logo_section_layout.setContentsMargins(15, 15, 15, 15)
        logo_section_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_section_layout.setSpacing(10)

        # Label para el logo (centrado)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setMinimumSize(80, 80)
        self.logo_label.setMaximumSize(120, 120)
        self.logo_label.setScaledContents(True)

        # Intentar cargar logo corporativo del usuario actual
        self.update_logo()

        logo_section_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # ========== SELECTOR DE CURSO (centrado en zona clara, sin etiqueta) ==========
        if self.session:
            from presentation.widgets import SelectorCursoWidget

            self.selector_curso = SelectorCursoWidget(self.session)
            self.selector_curso.setMaximumWidth(230)
            self.selector_curso.setStyleSheet("""
                QComboBox {
                    background-color: white;
                    color: #2c3e50;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    padding: 8px 10px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QComboBox:hover {
                    background-color: #f8f9fa;
                    border: 2px solid #2980b9;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 25px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 6px solid #3498db;
                    margin-right: 8px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #2c3e50;
                    selection-background-color: #3498db;
                    selection-color: white;
                    border: 2px solid #3498db;
                    outline: none;
                }
            """)
            logo_section_layout.addWidget(
                self.selector_curso, alignment=Qt.AlignmentFlag.AlignCenter
            )

        layout.addWidget(logo_section)

        # ========== SECCIÓN INFERIOR: MENÚ ==========
        # Área de scroll para los menús
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"background-color: {SIDEBAR_BG}; border: none;")

        # Widget contenedor del menú (comprimido para que quepan todos los items)
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 4, 0, 4)
        menu_layout.setSpacing(0)

        # ========== GESTIÓN ==========
        self.add_category(menu_layout, "GESTIÓN")
        self.add_menu_item(menu_layout, "profesores", "Profesores", "profesores", "account-group")
        self.add_menu_item(menu_layout, "zonas", "Zonas", "zonas", "map-marker")
        self.add_menu_item(menu_layout, "ajustes", "Ajustes", "ajustes", "cog")
        self.add_menu_item(menu_layout, "conectividad", "Conectividad", "conectividad", "email")
        self.add_menu_item(menu_layout, "perfiles", "Perfiles de Usuario", "perfiles", "account")

        menu_layout.addSpacing(4)

        # ========== GUARDIAS ==========
        self.add_category(menu_layout, "GUARDIAS")
        self.add_menu_item(
            menu_layout,
            "asignacion_calculo",
            "Cálculo y Asignación",
            "asignacion_calculo",
            "chart-line",
        )
        self.add_menu_item(menu_layout, "calendario", "Calendario", "calendario", "calendar")

        menu_layout.addSpacing(4)

        # ========== PERSONAL ==========
        self.add_category(menu_layout, "PERSONAL")
        self.add_menu_item(menu_layout, "ausencias", "Ausencias", "ausencias", "hospital-box")
        self.add_menu_item(
            menu_layout, "sustituciones", "Sustituciones", "sustituciones", "swap-horizontal"
        )

        menu_layout.addSpacing(4)

        # ========== HERRAMIENTAS ==========
        self.add_category(menu_layout, "HERRAMIENTAS")
        self.add_menu_item(
            menu_layout, "importar", "Importar/Exportar", "importar", "database-import-export"
        )
        self.add_menu_item(menu_layout, "reportes", "Reportes", "reportes", "file-chart")
        self.add_menu_item(menu_layout, "estadisticas", "Estadísticas", "estadisticas", "chart-bar")

        # Espaciador flexible antes de la información de la app
        menu_layout.addStretch()

        # ========== INFORMACIÓN DE LA APP ==========
        self.add_app_info_section(menu_layout)

        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

    def update_logo(self):
        """Actualiza el logo mostrado (corporativo o por defecto)"""
        if self.logo_label is None:
            return

        # Buscar logo corporativo del usuario actual
        try:
            from database.db_manager import get_current_user_id
            from PyQt6.QtGui import QPixmap

            current_user = get_current_user_id()
            logo_path = Path("imagenes") / f"{current_user}.png"

            if logo_path.exists():
                # Cargar logo corporativo sin borde (fondo claro ya lo tiene la sección)
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    self.logo_label.setPixmap(pixmap)
                    self.logo_label.setStyleSheet("""
                        QLabel {
                            background-color: transparent;
                            border: none;
                            padding: 0px;
                        }
                    """)
                    return
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"Error al cargar logo corporativo: {e}")

        # Si no hay logo corporativo, usar icono por defecto (school.svg)
        # En este caso usamos color oscuro porque el fondo es claro
        icon = get_icon("school", "#3a4149", 100)
        pixmap = icon.pixmap(100, 100)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)

    def add_category(self, layout: QVBoxLayout, title: str):
        """Añadir etiqueta de categoría"""
        label = QLabel(title)
        label.setObjectName("categoryLabel")
        label.setStyleSheet("""
            QLabel#categoryLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                padding: 12px 20px 6px 20px;
                background-color: transparent;
            }
        """)
        layout.addWidget(label)

        # Línea separadora debajo de categoría
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                max-height: 1px;
                margin: 0px 16px 8px 16px;
            }
        """)
        layout.addWidget(separator)

    def add_menu_item(
        self, layout: QVBoxLayout, object_name: str, text: str, section: str, icon_name: str = None
    ):
        """Añadir botón de menú con icono SVG"""
        btn = QPushButton(f" {text}")  # Espacio para separar icono del texto
        btn.setObjectName(object_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("section", section)
        btn.setProperty("active", "false")
        btn.setMinimumHeight(38)  # Altura moderada

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
                padding: 10px 28px;
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

    def add_app_info_section(self, layout: QVBoxLayout):
        """Añadir sección de información de la aplicación en la parte inferior"""
        from utils.constants import APP_VERSION

        # Contenedor de información
        info_container = QWidget()
        info_container.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.15);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(8)

        # Versión (más destacada) - centrada
        version_label = QLabel(f"📦 v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                font-size: 12px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        info_layout.addWidget(version_label)

        # Botón "Acerca de"
        btn_acerca = QPushButton("ℹ️ Acerca de...")
        btn_acerca.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_acerca.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 0.7);
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
            }
        """)
        btn_acerca.clicked.connect(self._show_about_dialog)
        info_layout.addWidget(btn_acerca)

        layout.addWidget(info_container)

    def _show_about_dialog(self):
        """Mostrar el diálogo Acerca de"""
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe

        dialogo = DialogoAcercaDe(self, session=self.session)
        dialogo.exec()

    def set_active_section(self, section: str):
        """Establecer sección activa programáticamente"""
        for btn in self.findChildren(QPushButton):
            if btn.property("section") == section:
                self.on_menu_clicked(btn, section)
                break
