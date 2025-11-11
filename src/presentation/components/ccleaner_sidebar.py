"""
Sidebar estilo CCleaner
=======================
Menú lateral oscuro con diseño profesional.
"""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

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
        logo_section_layout.setContentsMargins(0, 20, 0, 20)
        logo_section_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Label para el logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(120, 120)
        self.logo_label.setScaledContents(True)

        # Intentar cargar logo corporativo del usuario actual
        self.update_logo()

        logo_section_layout.addWidget(self.logo_label)
        layout.addWidget(logo_section)

        # ========== SELECTOR DE CURSO SIEMPRE VISIBLE ==========
        if self.session:
            from presentation.widgets import SelectorCursoWidget
            
            curso_section = QWidget()
            curso_section.setStyleSheet(f"""
                QWidget {{
                    background-color: {SIDEBAR_BG};
                    padding: 10px;
                }}
                QLabel {{
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 11px;
                    font-weight: bold;
                    padding: 5px;
                }}
            """)
            curso_layout = QVBoxLayout(curso_section)
            curso_layout.setContentsMargins(10, 10, 10, 10)
            curso_layout.setSpacing(5)
            
            # Etiqueta
            curso_label = QLabel("📚 CURSO ACTIVO")
            curso_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            curso_layout.addWidget(curso_label)
            
            # Selector
            self.selector_curso = SelectorCursoWidget(self.session)
            self.selector_curso.setStyleSheet("""
                QComboBox {
                    background-color: #3d566e;
                    color: white;
                    border: 1px solid #5dade2;
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QComboBox:hover {
                    background-color: #4a6584;
                    border: 1px solid #74b9ff;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid white;
                    margin-right: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: #34495e;
                    color: white;
                    selection-background-color: #3498db;
                    border: 1px solid #5dade2;
                }
            """)
            curso_layout.addWidget(self.selector_curso)
            
            layout.addWidget(curso_section)

        # ========== SECCIÓN INFERIOR: MENÚ ==========
        # Área de scroll para los menús
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
        self.add_menu_item(menu_layout, "profesores", "Profesores", "profesores", "account-group")
        self.add_menu_item(menu_layout, "zonas", "Zonas", "zonas", "map-marker")
        self.add_menu_item(menu_layout, "ajustes", "Ajustes", "ajustes", "cog")
        self.add_menu_item(menu_layout, "conectividad", "Conectividad", "conectividad", "email")
        self.add_menu_item(menu_layout, "perfiles", "Perfiles de Usuario", "perfiles", "account")

        menu_layout.addSpacing(SPACING_MD)

        # ========== GUARDIAS ==========
        self.add_category(menu_layout, "GUARDIAS")
        self.add_menu_item(menu_layout, "asignacion", "Asignación", "asignacion", "check-bold")
        self.add_menu_item(menu_layout, "calendario", "Calendario", "calendario", "calendar")

        menu_layout.addSpacing(SPACING_MD)

        # ========== PERSONAL ==========
        self.add_category(menu_layout, "PERSONAL")
        self.add_menu_item(menu_layout, "ausencias", "Ausencias", "ausencias", "hospital-box")
        self.add_menu_item(
            menu_layout, "sustituciones", "Sustituciones", "sustituciones", "swap-horizontal"
        )

        menu_layout.addSpacing(SPACING_MD)

        # ========== HERRAMIENTAS ==========
        self.add_category(menu_layout, "HERRAMIENTAS")
        self.add_menu_item(
            menu_layout, "importar", "Importar/Exportar", "importar", "database-import-export"
        )
        self.add_menu_item(menu_layout, "reportes", "Reportes", "reportes", "file-chart")
        self.add_menu_item(menu_layout, "estadisticas", "Estadísticas", "estadisticas", "chart-bar")

        # Espaciador al final
        menu_layout.addStretch()

        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

    def update_logo(self):
        """Actualiza el logo mostrado (corporativo o por defecto)"""
        if self.logo_label is None:
            return

        # Buscar logo corporativo del usuario actual
        try:
            from PyQt6.QtGui import QPixmap

            from database.db_manager import get_current_user_id
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
        except Exception as e:
            print(f"Error al cargar logo corporativo: {e}")

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
        self, layout: QVBoxLayout, object_name: str, text: str, section: str, icon_name: str = None
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
