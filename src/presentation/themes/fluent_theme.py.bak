"""
Microsoft Fluent Design System - Tema y Estilos.

Sistema de diseño basado en Microsoft Fluent para una UI moderna y profesional.
Incluye paleta de colores, tipografía, espaciado y componentes reutilizables.
"""

# ========== PALETA DE COLORES ESTILO CCLEANER ==========

# Colores del Sidebar (Tema Oscuro)
SIDEBAR_BG = "#3E4857"           # Fondo sidebar oscuro
SIDEBAR_BG_DARK = "#2D3845"      # Fondo sidebar más oscuro
SIDEBAR_TEXT = "#FFFFFF"         # Texto blanco en sidebar
SIDEBAR_TEXT_DIM = "#B0B8C4"     # Texto secundario en sidebar
SIDEBAR_HOVER = "#4A5668"        # Hover en sidebar
SIDEBAR_ACTIVE = "#5B6B7F"       # Item activo en sidebar
SIDEBAR_BORDER = "#2A3340"       # Bordes en sidebar

# Colores principales de acción
PRIMARY_BLUE = "#007ACC"         # Azul primario (botones principales)
PRIMARY_BLUE_HOVER = "#005A9E"   # Hover azul
PRIMARY_BLUE_LIGHT = "#E6F2FA"   # Fondos azul claro

# Grises para el canvas/contenido
CONTENT_BG = "#FFFFFF"           # Fondo blanco puro
CONTENT_BG_ALT = "#F8F9FA"       # Fondo alternativo
BORDER_LIGHT = "#E1E4E8"         # Bordes claros
BORDER_MEDIUM = "#D1D5DB"        # Bordes normales
TEXT_PRIMARY = "#1F2937"         # Texto principal negro
TEXT_SECONDARY = "#6B7280"       # Texto secundario gris
TEXT_DISABLED = "#9CA3AF"        # Texto deshabilitado

# Colores semánticos
FLUENT_SUCCESS = "#107C10"      # Verde éxito
FLUENT_SUCCESS_LIGHT = "#DFF6DD" # Fondo success
FLUENT_WARNING = "#CA5010"      # Naranja warning
FLUENT_WARNING_LIGHT = "#FFF4CE" # Fondo warning
FLUENT_ERROR = "#D13438"        # Rojo error
FLUENT_ERROR_LIGHT = "#FDE7E9"  # Fondo error
FLUENT_INFO = "#0078D4"         # Info (mismo que primary)

# Colores adicionales
FLUENT_PURPLE = "#5C2D91"       # Púrpura para métricas
FLUENT_TEAL = "#038387"         # Teal para estadísticas
FLUENT_ORANGE = "#D83B01"       # Naranja intenso

# ========== TIPOGRAFÍA ==========

FONT_FAMILY_BASE = "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, sans-serif"
FONT_FAMILY_MONO = "Consolas, Monaco, 'Courier New', monospace"

# Tamaños de fuente (escala Fluent)
FONT_SIZE_10 = 10  # Caption
FONT_SIZE_12 = 12  # Body small
FONT_SIZE_14 = 14  # Body (base)
FONT_SIZE_16 = 16  # Subtitle
FONT_SIZE_18 = 18  # Subtitle large
FONT_SIZE_20 = 20  # Title
FONT_SIZE_24 = 24  # Title large
FONT_SIZE_28 = 28  # Display
FONT_SIZE_32 = 32  # Display large

# Pesos de fuente
FONT_WEIGHT_REGULAR = "400"
FONT_WEIGHT_SEMIBOLD = "600"
FONT_WEIGHT_BOLD = "700"

# ========== ESPACIADO (Grid de 8px) ==========

SPACING_XS = 4
SPACING_S = 8
SPACING_M = 12
SPACING_L = 16
SPACING_XL = 20
SPACING_XXL = 24
SPACING_XXXL = 32

# ========== BORDER RADIUS ==========

RADIUS_SMALL = 2
RADIUS_MEDIUM = 4
RADIUS_LARGE = 8

# ========== SOMBRAS ==========

SHADOW_CARD = "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)"
SHADOW_CARD_HOVER = "0 3px 6px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.12)"
SHADOW_MODAL = "0 6px 16px rgba(0,0,0,0.15)"
SHADOW_DEPTH_4 = "0 1.6px 3.6px 0 rgba(0,0,0,0.132), 0 0.3px 0.9px 0 rgba(0,0,0,0.108)"
SHADOW_DEPTH_8 = "0 3.2px 7.2px 0 rgba(0,0,0,0.132), 0 0.6px 1.8px 0 rgba(0,0,0,0.108)"

# ========== ESTILOS DE COMPONENTES ==========

def get_main_window_style():
    """Estilo para la ventana principal."""
    return f"""
        QMainWindow, QWidget {{
            background-color: {FLUENT_GRAY_20};
            color: {FLUENT_GRAY_190};
            font-family: {FONT_FAMILY_BASE};
            font-size: {FONT_SIZE_14}px;
        }}
    """

def get_sidebar_style():
    """Estilo para el menú lateral."""
    return f"""
        QWidget#sidebar {{
            background-color: {FLUENT_GRAY_10};
            border-right: 1px solid {FLUENT_GRAY_40};
        }}

        QLabel#sidebarTitle {{
            font-size: {FONT_SIZE_16}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {FLUENT_GRAY_190};
            padding: {SPACING_M}px;
            background-color: {FLUENT_GRAY_20};
        }}

        QPushButton#menuButton {{
            background-color: transparent;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_M}px {SPACING_L}px;
            text-align: left;
            color: {FLUENT_GRAY_160};
            font-size: {FONT_SIZE_14}px;
            font-weight: {FONT_WEIGHT_REGULAR};
            min-height: 40px;
        }}

        QPushButton#menuButton:hover {{
            background-color: {FLUENT_GRAY_30};
            color: {FLUENT_GRAY_190};
        }}

        QPushButton#menuButton:pressed {{
            background-color: {FLUENT_GRAY_40};
        }}

        QPushButton#menuButtonActive {{
            background-color: {FLUENT_BLUE_LIGHT};
            color: {FLUENT_BLUE};
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            border-left: 3px solid {FLUENT_BLUE};
        }}

        QPushButton#menuButtonActive:hover {{
            background-color: {FLUENT_BLUE_TINT};
        }}

        QPushButton#collapseButton {{
            background-color: transparent;
            border: none;
            padding: {SPACING_S}px;
            color: {FLUENT_GRAY_130};
        }}

        QPushButton#collapseButton:hover {{
            background-color: {FLUENT_GRAY_30};
            color: {FLUENT_GRAY_190};
        }}

        QLabel#menuCategory {{
            font-size: {FONT_SIZE_12}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {FLUENT_GRAY_130};
            text-transform: uppercase;
            padding: {SPACING_L}px {SPACING_M}px {SPACING_S}px {SPACING_M}px;
        }}
    """

def get_topbar_style():
    """Estilo para la barra superior."""
    return f"""
        QWidget#topbar {{
            background-color: white;
            border-bottom: 1px solid {FLUENT_GRAY_40};
            min-height: 48px;
            max-height: 48px;
        }}

        QLabel#breadcrumb {{
            font-size: {FONT_SIZE_16}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {FLUENT_GRAY_190};
            padding: {SPACING_M}px;
        }}

        QLabel#breadcrumbSeparator {{
            color: {FLUENT_GRAY_90};
            padding: 0 {SPACING_S}px;
        }}

        QPushButton#topbarButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_S}px {SPACING_M}px;
            color: {FLUENT_GRAY_160};
            min-width: 32px;
            min-height: 32px;
        }}

        QPushButton#topbarButton:hover {{
            background-color: {FLUENT_GRAY_20};
            border-color: {FLUENT_GRAY_40};
        }}
    """

def get_card_style():
    """Estilo para cards/paneles."""
    return f"""
        QWidget#card {{
            background-color: white;
            border: 1px solid {FLUENT_GRAY_40};
            border-radius: {RADIUS_LARGE}px;
            padding: {SPACING_L}px;
        }}

        QGroupBox {{
            background-color: white;
            border: 1px solid {FLUENT_GRAY_40};
            border-radius: {RADIUS_LARGE}px;
            margin-top: {SPACING_L}px;
            padding-top: {SPACING_L}px;
            font-size: {FONT_SIZE_14}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {FLUENT_GRAY_190};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: {SPACING_S}px {SPACING_M}px;
            background-color: {FLUENT_GRAY_20};
            border-radius: {RADIUS_MEDIUM}px;
            color: {FLUENT_GRAY_190};
        }}
    """

def get_button_primary_style():
    """Estilo para botón primario."""
    return f"""
        QPushButton {{
            background-color: {FLUENT_BLUE};
            color: white;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_S}px {SPACING_L}px;
            font-size: {FONT_SIZE_14}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: 32px;
            min-width: 100px;
        }}

        QPushButton:hover {{
            background-color: {FLUENT_BLUE_HOVER};
        }}

        QPushButton:pressed {{
            background-color: {FLUENT_BLUE_PRESSED};
        }}

        QPushButton:disabled {{
            background-color: {FLUENT_GRAY_40};
            color: {FLUENT_GRAY_90};
        }}
    """

def get_button_secondary_style():
    """Estilo para botón secundario."""
    return f"""
        QPushButton {{
            background-color: white;
            color: {FLUENT_GRAY_160};
            border: 1px solid {FLUENT_GRAY_60};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_S}px {SPACING_L}px;
            font-size: {FONT_SIZE_14}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: 32px;
            min-width: 100px;
        }}

        QPushButton:hover {{
            background-color: {FLUENT_GRAY_20};
            border-color: {FLUENT_GRAY_90};
        }}

        QPushButton:pressed {{
            background-color: {FLUENT_GRAY_30};
            border-color: {FLUENT_GRAY_130};
        }}

        QPushButton:disabled {{
            background-color: {FLUENT_GRAY_20};
            color: {FLUENT_GRAY_90};
            border-color: {FLUENT_GRAY_40};
        }}
    """

def get_button_success_style():
    """Estilo para botón de éxito."""
    return f"""
        QPushButton {{
            background-color: {FLUENT_SUCCESS};
            color: white;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_S}px {SPACING_L}px;
            font-size: {FONT_SIZE_14}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: 32px;
            min-width: 100px;
        }}

        QPushButton:hover {{
            background-color: #0E6B0E;
        }}

        QPushButton:pressed {{
            background-color: #0C5A0C;
        }}
    """

def get_button_danger_style():
    """Estilo para botón de peligro."""
    return f"""
        QPushButton {{
            background-color: {FLUENT_ERROR};
            color: white;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_S}px {SPACING_L}px;
            font-size: {FONT_SIZE_14}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: 32px;
            min-width: 100px;
        }}

        QPushButton:hover {{
            background-color: #B22A2E;
        }}

        QPushButton:pressed {{
            background-color: #942326;
        }}
    """

def get_input_style():
    """Estilo para campos de entrada."""
    return f"""
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox,
        QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {{
            background-color: white;
            color: {FLUENT_GRAY_190};
            border: 1px solid {FLUENT_GRAY_60};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_S}px {SPACING_M}px;
            font-size: {FONT_SIZE_14}px;
            min-height: 32px;
        }}

        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
        QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover,
        QDateEdit:hover, QTimeEdit:hover, QDateTimeEdit:hover {{
            border-color: {FLUENT_GRAY_90};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
        QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
            border: 2px solid {FLUENT_BLUE};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled,
        QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled,
        QDateEdit:disabled, QTimeEdit:disabled, QDateTimeEdit:disabled {{
            background-color: {FLUENT_GRAY_20};
            color: {FLUENT_GRAY_90};
            border-color: {FLUENT_GRAY_40};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {FLUENT_GRAY_130};
        }}
    """

def get_label_style():
    """Estilo para etiquetas."""
    return f"""
        QLabel {{
            color: {FLUENT_GRAY_190};
            font-size: {FONT_SIZE_14}px;
            background-color: transparent;
        }}

        QLabel#fieldLabel {{
            font-size: {FONT_SIZE_12}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {FLUENT_GRAY_160};
            margin-bottom: {SPACING_XS}px;
        }}

        QLabel#heading1 {{
            font-size: {FONT_SIZE_24}px;
            font-weight: {FONT_WEIGHT_BOLD};
            color: {FLUENT_GRAY_190};
        }}

        QLabel#heading2 {{
            font-size: {FONT_SIZE_20}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {FLUENT_GRAY_190};
        }}

        QLabel#heading3 {{
            font-size: {FONT_SIZE_16}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {FLUENT_GRAY_190};
        }}

        QLabel#caption {{
            font-size: {FONT_SIZE_12}px;
            color: {FLUENT_GRAY_130};
        }}
    """

def get_table_style():
    """Estilo para tablas."""
    return f"""
        QTableWidget, QTableView {{
            background-color: white;
            border: 1px solid {FLUENT_GRAY_40};
            border-radius: {RADIUS_MEDIUM}px;
            gridline-color: {FLUENT_GRAY_30};
            font-size: {FONT_SIZE_14}px;
        }}

        QTableWidget::item, QTableView::item {{
            padding: {SPACING_S}px;
            color: {FLUENT_GRAY_190};
        }}

        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {FLUENT_BLUE_LIGHT};
            color: {FLUENT_BLUE};
        }}

        QHeaderView::section {{
            background-color: {FLUENT_GRAY_20};
            color: {FLUENT_GRAY_190};
            padding: {SPACING_M}px;
            border: none;
            border-bottom: 1px solid {FLUENT_GRAY_40};
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            font-size: {FONT_SIZE_14}px;
        }}

        QTableWidget::item:hover, QTableView::item:hover {{
            background-color: {FLUENT_GRAY_10};
        }}
    """

def get_scrollbar_style():
    """Estilo para scrollbars."""
    return f"""
        QScrollBar:vertical {{
            background-color: {FLUENT_GRAY_20};
            width: 12px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {FLUENT_GRAY_90};
            border-radius: 6px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {FLUENT_GRAY_130};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background-color: {FLUENT_GRAY_20};
            height: 12px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {FLUENT_GRAY_90};
            border-radius: 6px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {FLUENT_GRAY_130};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """

def get_complete_fluent_stylesheet():
    """Retorna el stylesheet completo para la aplicación."""
    return (
        get_main_window_style() +
        get_sidebar_style() +
        get_topbar_style() +
        get_card_style() +
        get_button_primary_style() +
        get_input_style() +
        get_label_style() +
        get_table_style() +
        get_scrollbar_style()
    )
