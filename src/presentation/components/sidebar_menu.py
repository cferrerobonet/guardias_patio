"""
Menú lateral (Sidebar) con navegación moderna.

Componente de navegación vertical con iconos, categorías colapsables,
y estados activos/hover.
"""

from typing import Callable, Optional

from core.qt_imports import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    pyqtSignal,
)
from PyQt6.QtCore import Qt

from presentation.themes.ccleaner_theme import (
    SPACING_M,
    SPACING_S,
    get_sidebar_style,
)


class MenuItem:
    """Representa un item del menú."""

    def __init__(
        self,
        id: str,
        title: str,
        icon: str,
        callback: Optional[Callable] = None,
    ):
        """
        Inicializa un item del menú.

        Args:
            id: Identificador único del item
            title: Título visible del item
            icon: Emoji o símbolo de icono
            callback: Función a llamar cuando se hace clic
        """
        self.id = id
        self.title = title
        self.icon = icon
        self.callback = callback


class MenuCategory:
    """Representa una categoría del menú."""

    def __init__(self, title: str, items: list[MenuItem]):
        """
        Inicializa una categoría del menú.

        Args:
            title: Título de la categoría
            items: Lista de MenuItems en esta categoría
        """
        self.title = title
        self.items = items


class SidebarMenu(QWidget):
    """Menú lateral moderno con navegación por secciones."""

    # Señal emitida cuando se cambia de sección
    section_changed = pyqtSignal(str)  # section_id

    def __init__(self, parent=None):
        """Inicializa el menú lateral."""
        super().__init__(parent)
        self.setObjectName("sidebar")

        # Estado
        self.is_collapsed = False
        self.active_item_id = None
        self.menu_buttons = {}  # {item_id: button}

        # Layout principal
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header con logo y botón de colapsar
        self._create_header()

        # Área scrollable para el menú
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Widget contenedor del menú
        self.menu_container = QWidget()
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setContentsMargins(SPACING_S, SPACING_M, SPACING_S, SPACING_M)
        self.menu_layout.setSpacing(SPACING_S)
        self.menu_container.setLayout(self.menu_layout)

        scroll_area.setWidget(self.menu_container)
        self.main_layout.addWidget(scroll_area)

        self.setLayout(self.main_layout)

        # Tamaño inicial
        self.setMinimumWidth(240)
        self.setMaximumWidth(240)

        # Aplicar estilo
        self.setStyleSheet(get_sidebar_style())

    def _create_header(self):
        """Crea el header con logo y botón de colapsar."""
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(SPACING_M, SPACING_M, SPACING_M, SPACING_M)
        header_layout.setSpacing(SPACING_S)

        # Logo/Título
        self.title_label = QLabel("🏫 Guardias")
        self.title_label.setObjectName("sidebarTitle")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Botón de colapsar
        self.collapse_btn = QPushButton("☰")
        self.collapse_btn.setObjectName("collapseButton")
        self.collapse_btn.setFixedSize(32, 32)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self.collapse_btn)

        header.setLayout(header_layout)
        self.main_layout.addWidget(header)

    def add_category(self, category: MenuCategory):
        """
        Añade una categoría con sus items al menú.

        Args:
            category: MenuCategory a añadir
        """
        # Etiqueta de categoría con estilo mejorado
        category_label = QLabel(category.title)
        category_label.setObjectName("menuCategory")
        category_label.setStyleSheet("""
            QLabel#menuCategory {
                color: rgba(255, 255, 255, 0.95);
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 2px;
                text-transform: uppercase;
                padding: 16px 20px 8px 20px;
                margin-top: 12px;
                background-color: transparent;
            }
        """)
        self.menu_layout.addWidget(category_label)

        # Línea separadora sutil debajo de la categoría
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                max-height: 1px;
                margin: 0px 16px 8px 16px;
            }
        """)
        self.menu_layout.addWidget(separator)

        # Items de la categoría
        for item in category.items:
            button = self._create_menu_button(item)
            self.menu_buttons[item.id] = button
            self.menu_layout.addWidget(button)

        # Espaciado más pronunciado después de cada categoría
        self.menu_layout.addSpacing(20)

    def _create_menu_button(self, item: MenuItem) -> QPushButton:
        """
        Crea un botón para un item del menú.

        Args:
            item: MenuItem para crear el botón

        Returns:
            QPushButton configurado
        """
        # SIN ICONOS - solo texto limpio
        button = QPushButton(item.title)
        button.setObjectName("menuButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setMinimumHeight(40)

        # Estilo directo en el botón para asegurar que se aplica
        button.setStyleSheet("""
            QPushButton#menuButton {
                color: rgba(255, 255, 255, 0.95);
                background-color: transparent;
                text-align: left;
                padding: 10px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton#menuButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                color: white;
            }
            QPushButton#menuButtonActive {
                background-color: #007ACC;
                color: white;
                font-weight: 600;
            }
            QPushButton#menuButtonActive:hover {
                background-color: #005A9E;
            }
        """)

        def on_click():
            self.set_active_item(item.id)
            if item.callback:
                item.callback()
            self.section_changed.emit(item.id)

        button.clicked.connect(on_click)
        return button

    def set_active_item(self, item_id: str):
        """
        Marca un item como activo.

        Args:
            item_id: ID del item a marcar como activo
        """
        # Desactivar item anterior
        if self.active_item_id and self.active_item_id in self.menu_buttons:
            old_button = self.menu_buttons[self.active_item_id]
            old_button.setObjectName("menuButton")
            old_button.setStyleSheet(get_sidebar_style())

        # Activar nuevo item
        self.active_item_id = item_id
        if item_id in self.menu_buttons:
            new_button = self.menu_buttons[item_id]
            new_button.setObjectName("menuButtonActive")
            new_button.setStyleSheet(get_sidebar_style())

    def toggle_collapse(self):
        """Alterna entre menú expandido y colapsado."""
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            self.setMaximumWidth(60)
            self.setMinimumWidth(60)
            self.title_label.hide()
            # Mostrar solo iconos en los botones
            for item_id, button in self.menu_buttons.items():
                # Extraer solo el emoji del texto
                text = button.text()
                icon = text.split()[0] if text else ""
                button.setText(icon)
        else:
            self.setMaximumWidth(240)
            self.setMinimumWidth(240)
            self.title_label.show()
            # Restaurar texto completo
            # Necesitaríamos guardar los textos originales, por ahora skip

    def add_spacer(self):
        """Añade un espaciador al final del menú."""
        self.menu_layout.addStretch()
