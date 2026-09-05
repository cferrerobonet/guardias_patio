"""
Sistema de Temas — capa de compatibilidad.

Las constantes de este módulo son aliases de presentation.theme.tokens.
No añadir constantes nuevas aquí; usar tokens.Colors directamente.
"""

from presentation.theme.tokens import BorderRadius, Colors, FontSize, Spacing

# Sidebar
SIDEBAR_BG = Colors.SIDEBAR_BG
SIDEBAR_BG_DARK = "#2D3845"
SIDEBAR_TEXT = Colors.SIDEBAR_TEXT
SIDEBAR_TEXT_DIM = "#B0B8C4"
SIDEBAR_HOVER = Colors.SIDEBAR_HOVER
SIDEBAR_ACTIVE = "#5B6B7F"
SIDEBAR_BORDER = Colors.SIDEBAR_BORDER

# Acción
PRIMARY_BLUE = Colors.PRIMARY
PRIMARY_BLUE_HOVER = Colors.PRIMARY_DARK
PRIMARY_BLUE_LIGHT = Colors.PRIMARY_LIGHT

# Estado
SUCCESS_GREEN = "#28A745"
SUCCESS_GREEN_LIGHT = "#D4EDDA"
WARNING_ORANGE = "#FFC107"
WARNING_ORANGE_LIGHT = Colors.WARNING_BG
ERROR_RED = Colors.ERROR
ERROR_RED_LIGHT = Colors.ERROR_BG

# Contenido
CONTENT_BG = Colors.BACKGROUND
CONTENT_BG_ALT = Colors.SURFACE
BORDER_LIGHT = Colors.BORDER
BORDER_MEDIUM = Colors.BORDER_DARK
TEXT_PRIMARY = Colors.TEXT_PRIMARY
TEXT_SECONDARY = Colors.TEXT_SECONDARY
TEXT_DISABLED = Colors.TEXT_DISABLED

# Tipografía
FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
FONT_SIZE_SMALL = FontSize.CAPTION
FONT_SIZE_NORMAL = FontSize.BODY
FONT_SIZE_LARGE = FontSize.SUBTITLE
FONT_SIZE_XLARGE = FontSize.TITLE
FONT_SIZE_XXLARGE = FontSize.H2
FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_SEMIBOLD = 600
FONT_WEIGHT_BOLD = 700

# Espaciado
SPACING_XS = Spacing.XS
SPACING_SM = Spacing.SM
SPACING_MD = Spacing.MD
SPACING_LG = Spacing.LG
SPACING_XL = Spacing.XL
SPACING_XXL = Spacing.XXL
SPACING_XXXL = 32

# Bordes
RADIUS_SMALL = BorderRadius.SM
RADIUS_MEDIUM = BorderRadius.MD
RADIUS_LARGE = BorderRadius.LG

# Sombras
SHADOW_SMALL = "0 1px 2px rgba(0, 0, 0, 0.05)"
SHADOW_MEDIUM = "0 2px 4px rgba(0, 0, 0, 0.08)"
SHADOW_LARGE = "0 4px 8px rgba(0, 0, 0, 0.12)"


# ========== ESTILOS DE COMPONENTES ==========


def get_sidebar_style() -> str:
    """Estilo para el sidebar oscuro estilo CCleaner - limpio y moderno"""
    return f"""
        QWidget#sidebar {{
            background-color: {SIDEBAR_BG};
            border-right: 1px solid {SIDEBAR_BORDER};
        }}

        /* Título del sidebar */
        QLabel#sidebarTitle {{
            color: white;
            font-family: {FONT_FAMILY};
            font-size: 18px;
            font-weight: {FONT_WEIGHT_BOLD};
            padding: {SPACING_MD}px;
        }}

        /* Categorías del menú - más grandes y limpias */
        QLabel#menuCategory {{
            color: rgba(255, 255, 255, 0.75);
            background-color: transparent;
            font-family: {FONT_FAMILY};
            font-size: 12px;
            font-weight: {FONT_WEIGHT_BOLD};
            text-transform: uppercase;
            letter-spacing: 1.8px;
            padding: {SPACING_MD}px {SPACING_LG}px {SPACING_XS}px {SPACING_LG}px;
            margin-top: {SPACING_XL}px;
            margin-bottom: {SPACING_XS}px;
            border: none;
        }}

        /* Primera categoría sin margen superior */
        QLabel#menuCategory:first {{
            margin-top: 0;
        }}

        /* Botones de menú - iconos blancos y texto claro */
        QPushButton#menuButton {{
            background-color: transparent;
            color: rgba(255, 255, 255, 0.9);
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_NORMAL};
            padding: {SPACING_MD}px {SPACING_LG}px;
            text-align: left;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            margin: 2px {SPACING_MD}px;
        }}

        QPushButton#menuButton:hover {{
            background-color: rgba(255, 255, 255, 0.10);
            color: white;
        }}

        /* Botón activo con fondo azul */
        QPushButton#menuButtonActive {{
            background-color: {PRIMARY_BLUE};
            color: white;
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            padding: {SPACING_MD}px {SPACING_LG}px;
            text-align: left;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            margin: 2px {SPACING_MD}px;
        }}

        QPushButton#menuButtonActive:hover {{
            background-color: {PRIMARY_BLUE_HOVER};
        }}

        /* Botón de colapsar */
        QPushButton#collapseButton {{
            background-color: transparent;
            color: rgba(255, 255, 255, 0.7);
            font-size: 16px;
            border: none;
            border-radius: {RADIUS_SMALL}px;
        }}

        QPushButton#collapseButton:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
        }}

        /* Separadores */
        QFrame[frameShape="4"] {{
            background-color: rgba(255, 255, 255, 0.08);
            max-height: 1px;
            margin: {SPACING_MD}px {SPACING_LG}px;
        }}
    """


def get_topbar_style() -> str:
    """Estilo para la barra superior blanca"""
    return f"""
        QWidget#topbar {{
            background-color: {CONTENT_BG};
            border-bottom: 1px solid {BORDER_LIGHT};
            padding: 0 {SPACING_LG}px;
        }}

        /* Título de la sección actual */
        QLabel#breadcrumb {{
            color: {TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_LARGE}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
        }}

        /* Botones de acción rápida */
        QPushButton {{
            background-color: transparent;
            color: {TEXT_SECONDARY};
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            border: none;
            border-radius: {RADIUS_SMALL}px;
        }}

        QPushButton:hover {{
            background-color: {CONTENT_BG_ALT};
            color: {TEXT_PRIMARY};
        }}
    """


def get_content_area_style() -> str:
    """Estilo para el área de contenido principal"""
    return f"""
        QWidget#contentArea {{
            background-color: {CONTENT_BG};
        }}
    """


def get_heading1_style() -> str:
    """Título principal (H1)"""
    return f"""
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_XXLARGE}px;
        font-weight: {FONT_WEIGHT_BOLD};
        margin-bottom: {SPACING_LG}px;
    """


def get_heading2_style() -> str:
    """Subtítulo de sección (H2)"""
    return f"""
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_XLARGE}px;
        font-weight: {FONT_WEIGHT_SEMIBOLD};
        margin-top: {SPACING_XL}px;
        margin-bottom: {SPACING_MD}px;
    """


def get_heading3_style() -> str:
    """Subtítulo de subsección (H3)"""
    return f"""
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_LARGE}px;
        font-weight: {FONT_WEIGHT_SEMIBOLD};
        margin-top: {SPACING_LG}px;
        margin-bottom: {SPACING_SM}px;
    """


def get_label_style() -> str:
    """Etiqueta de texto normal"""
    return f"""
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_NORMAL}px;
        font-weight: {FONT_WEIGHT_NORMAL};
    """


def get_label_secondary_style() -> str:
    """Etiqueta de texto secundario"""
    return f"""
        color: {TEXT_SECONDARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_SMALL}px;
        font-weight: {FONT_WEIGHT_NORMAL};
    """


def get_button_primary_style() -> str:
    """Botón primario azul"""
    return f"""
        QPushButton {{
            background-color: {PRIMARY_BLUE};
            color: white;
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_MEDIUM};
            padding: {SPACING_SM}px {SPACING_XL}px;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QPushButton:hover {{
            background-color: {PRIMARY_BLUE_HOVER};
        }}

        QPushButton:pressed {{
            background-color: {PRIMARY_BLUE_HOVER};
            transform: translateY(1px);
        }}

        QPushButton:disabled {{
            background-color: {BORDER_MEDIUM};
            color: {TEXT_DISABLED};
        }}
    """


def get_button_secondary_style() -> str:
    """Botón secundario con borde"""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_MEDIUM};
            padding: {SPACING_SM}px {SPACING_XL}px;
            border: 1px solid {BORDER_MEDIUM};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QPushButton:hover {{
            background-color: {CONTENT_BG_ALT};
            border-color: {TEXT_SECONDARY};
        }}

        QPushButton:pressed {{
            background-color: {BORDER_LIGHT};
        }}

        QPushButton:disabled {{
            color: {TEXT_DISABLED};
            border-color: {BORDER_LIGHT};
        }}
    """


def get_input_style() -> str:
    """Campos de entrada de texto"""
    return f"""
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            border: 1px solid {BORDER_MEDIUM};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {PRIMARY_BLUE};
            outline: none;
        }}

        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
            background-color: {CONTENT_BG_ALT};
            color: {TEXT_DISABLED};
            border-color: {BORDER_LIGHT};
        }}
    """


def get_combobox_style() -> str:
    """ComboBox/Select"""
    return f"""
        QComboBox {{
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            border: 1px solid {BORDER_MEDIUM};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QComboBox:hover {{
            border-color: {TEXT_SECONDARY};
        }}

        QComboBox:focus {{
            border-color: {PRIMARY_BLUE};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {TEXT_SECONDARY};
            margin-right: 8px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_MEDIUM};
            selection-background-color: {PRIMARY_BLUE_LIGHT};
            selection-color: {TEXT_PRIMARY};
        }}
    """


def get_table_style() -> str:
    """Tablas"""
    return f"""
        QTableWidget, QTableView {{
            background-color: {CONTENT_BG};
            alternate-background-color: {CONTENT_BG_ALT};
            gridline-color: {BORDER_LIGHT};
            color: {TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            border: 1px solid {BORDER_LIGHT};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QTableWidget::item, QTableView::item {{
            padding: {SPACING_SM}px;
        }}

        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {PRIMARY_BLUE_LIGHT};
            color: {TEXT_PRIMARY};
        }}

        QHeaderView::section {{
            background-color: {CONTENT_BG_ALT};
            color: {TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            padding: {SPACING_SM}px;
            border: none;
            border-bottom: 2px solid {BORDER_LIGHT};
        }}
    """


def get_card_style() -> str:
    """Tarjetas/Cards con sombra sutil"""
    return f"""
        QFrame {{
            background-color: {CONTENT_BG};
            border: 1px solid {BORDER_LIGHT};
            border-radius: {RADIUS_LARGE}px;
            padding: {SPACING_LG}px;
        }}
    """


def get_complete_stylesheet() -> str:
    """Stylesheet completo para la aplicación"""
    return f"""
        /* ========== GLOBAL ========== */
        QWidget {{
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            color: {TEXT_PRIMARY};
        }}

        /* ========== BOTONES GENERALES (sin objectName) ========== */
        QPushButton {{
            background-color: {PRIMARY_BLUE};
            color: white;
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_MEDIUM};
            padding: {SPACING_SM}px {SPACING_LG}px;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            min-height: 32px;
        }}

        QPushButton:hover {{
            background-color: {PRIMARY_BLUE_HOVER};
        }}

        QPushButton:pressed {{
            background-color: {PRIMARY_BLUE_HOVER};
        }}

        QPushButton:disabled {{
            background-color: {BORDER_MEDIUM};
            color: {TEXT_DISABLED};
        }}

        /* ========== BOTONES EN DIÁLOGOS (QMessageBox, QDialogButtonBox, QDialog) ========== */
        QMessageBox QPushButton,
        QDialogButtonBox QPushButton,
        QDialog QPushButton {{
            background-color: {PRIMARY_BLUE} !important;
            color: white !important;
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_MEDIUM};
            padding: {SPACING_SM}px {SPACING_XL}px;
            border: 1px solid {PRIMARY_BLUE} !important;
            border-radius: {RADIUS_MEDIUM}px;
            min-width: 80px;
            min-height: 32px;
        }}

        QMessageBox QPushButton:hover,
        QDialogButtonBox QPushButton:hover,
        QDialog QPushButton:hover {{
            background-color: {PRIMARY_BLUE_HOVER} !important;
            border: 1px solid {PRIMARY_BLUE_HOVER} !important;
        }}

        QMessageBox QPushButton:pressed,
        QDialogButtonBox QPushButton:pressed,
        QDialog QPushButton:pressed {{
            background-color: #005999 !important;
        }}

        /* Asegurar visibilidad de botones secundarios en diálogos */
        QMessageBox QPushButton[text="No"],
        QMessageBox QPushButton[text="Cancelar"],
        QDialogButtonBox QPushButton[text="No"],
        QDialogButtonBox QPushButton[text="Cancelar"],
        QDialog QPushButton[text="No"],
        QDialog QPushButton[text="Cancelar"] {{
            background-color: {CONTENT_BG_ALT} !important;
            color: {TEXT_PRIMARY} !important;
            border: 1px solid {BORDER_MEDIUM} !important;
        }}

        QMessageBox QPushButton[text="No"]:hover,
        QMessageBox QPushButton[text="Cancelar"]:hover,
        QDialogButtonBox QPushButton[text="No"]:hover,
        QDialogButtonBox QPushButton[text="Cancelar"]:hover,
        QDialog QPushButton[text="No"]:hover,
        QDialog QPushButton[text="Cancelar"]:hover {{
            background-color: {BORDER_LIGHT} !important;
            border: 1px solid {TEXT_SECONDARY} !important;
        }}

        /* ========== BOTONES PRIMARIOS ========== */
        QPushButton#primaryButton {{
            background-color: {PRIMARY_BLUE};
            color: white;
            font-weight: {FONT_WEIGHT_MEDIUM};
            padding: {SPACING_SM}px {SPACING_XL}px;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QPushButton#primaryButton:hover {{
            background-color: {PRIMARY_BLUE_HOVER};
        }}

        /* ========== BOTONES SECUNDARIOS ========== */
        QPushButton#secondaryButton {{
            background-color: transparent;
            color: {TEXT_PRIMARY};
            font-weight: {FONT_WEIGHT_MEDIUM};
            padding: {SPACING_SM}px {SPACING_XL}px;
            border: 1px solid {BORDER_MEDIUM};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QPushButton#secondaryButton:hover {{
            background-color: {CONTENT_BG_ALT};
            border-color: {TEXT_SECONDARY};
        }}

        /* ========== BOTONES DE ÉXITO (VERDE) ========== */
        QPushButton[success="true"] {{
            background-color: {SUCCESS_GREEN};
            color: white;
        }}

        QPushButton[success="true"]:hover {{
            background-color: #218838;
        }}

        /* ========== BOTONES DE PELIGRO (ROJO) ========== */
        QPushButton[danger="true"] {{
            background-color: {ERROR_RED};
            color: white;
        }}

        QPushButton[danger="true"]:hover {{
            background-color: #C82333;
        }}

        /* ========== BOTONES DE ADVERTENCIA (NARANJA) ========== */
        QPushButton[warning="true"] {{
            background-color: {WARNING_ORANGE};
            color: white;
        }}

        QPushButton[warning="true"]:hover {{
            background-color: #E0A800;
        }}

        /* ========== BOTONES SECUNDARIOS (GRIS) ========== */
        QPushButton[secondary="true"] {{
            background-color: #6B7280;
            color: white;
        }}

        QPushButton[secondary="true"]:hover {{
            background-color: #4B5563;
        }}

        /* ========== LABELS SEMÁNTICOS ========== */
        QLabel#labelCaption {{
            color: {TEXT_SECONDARY};
            font-size: {FONT_SIZE_SMALL}px;
        }}

        QLabel#labelTitle {{
            font-size: {FONT_SIZE_XLARGE}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {PRIMARY_BLUE};
        }}

        QLabel#labelSubtitle {{
            font-size: {FONT_SIZE_LARGE}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            color: {TEXT_PRIMARY};
        }}

        QLabel#labelSecondary {{
            color: {TEXT_SECONDARY};
            font-size: {FONT_SIZE_NORMAL}px;
        }}

        /* ========== INFO BOXES (objectName) ========== */
        QLabel#infoBoxInfo {{
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-left: 4px solid {PRIMARY_BLUE};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {TEXT_PRIMARY};
        }}

        QLabel#infoBoxSuccess {{
            background-color: #D1FAE5;
            border: 1px solid #6EE7B7;
            border-left: 4px solid #22C55E;
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {TEXT_PRIMARY};
        }}

        QLabel#infoBoxWarning {{
            background-color: #FEF3C7;
            border: 1px solid #F59E0B;
            border-left: 4px solid {WARNING_ORANGE};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {TEXT_PRIMARY};
        }}

        QLabel#infoBoxError {{
            background-color: #FEE2E2;
            border: 1px solid #FCA5A5;
            border-left: 4px solid {ERROR_RED};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {TEXT_PRIMARY};
        }}

        /* ========== SEPARADOR HORIZONTAL ========== */
        QFrame#separator {{
            background-color: {BORDER_LIGHT};
            max-height: 1px;
            border: none;
        }}

        /* ========== GROUPBOX ESTÁNDAR ========== */
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {BORDER_MEDIUM};
            border-radius: 5px;
            margin-top: 16px;
            padding-top: 14px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 6px 12px;
            left: 12px;
            top: -2px;
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
        }}

        /* ========== INPUTS ========== */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
            padding: {SPACING_SM}px {SPACING_MD}px;
            border: 1px solid {BORDER_MEDIUM};
            border-radius: {RADIUS_MEDIUM}px;
            min-height: 28px;
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {PRIMARY_BLUE};
        }}

        /* ========== ÁREAS TERMINAL RETRO (VINTAGE) ========== */
        QTextEdit#terminalRetro {{
            background-color: #0f172a;
            color: #d1d5db;
            border: 1px solid #1f2937;
            border-radius: {RADIUS_MEDIUM}px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            selection-background-color: #14532d;
            selection-color: #dcfce7;
        }}

        /* ========== COMBOBOX ========== */
        QComboBox {{
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
            padding: {SPACING_SM}px {SPACING_MD}px;
            border: 1px solid {BORDER_MEDIUM};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QComboBox:hover {{
            border-color: {TEXT_SECONDARY};
        }}

        QComboBox:focus {{
            border-color: {PRIMARY_BLUE};
        }}

        QComboBox QAbstractItemView {{
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_MEDIUM};
            selection-background-color: {PRIMARY_BLUE_LIGHT};
            selection-color: {TEXT_PRIMARY};
        }}

        /* ========== TABLAS ========== */
        QTableWidget, QTableView {{
            background-color: {CONTENT_BG};
            alternate-background-color: {CONTENT_BG_ALT};
            gridline-color: {BORDER_LIGHT};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_LIGHT};
            border-radius: {RADIUS_MEDIUM}px;
        }}

        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {PRIMARY_BLUE_LIGHT};
            color: {TEXT_PRIMARY};
        }}

        QHeaderView::section {{
            background-color: {CONTENT_BG_ALT};
            color: {TEXT_PRIMARY};
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            padding: {SPACING_SM}px;
            border: none;
            border-bottom: 2px solid {BORDER_LIGHT};
        }}

        /* ========== SCROLLBARS ========== */
        QScrollBar:vertical {{
            background: {CONTENT_BG_ALT};
            width: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background: {BORDER_MEDIUM};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {TEXT_SECONDARY};
        }}

        QScrollBar:horizontal {{
            background: {CONTENT_BG_ALT};
            height: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal {{
            background: {BORDER_MEDIUM};
            border-radius: 6px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {TEXT_SECONDARY};
        }}

        /* ========== LABELS CON ROLES ========== */
        QLabel#heading1 {{
            color: {TEXT_PRIMARY};
            font-size: {FONT_SIZE_XXLARGE}px;
            font-weight: {FONT_WEIGHT_BOLD};
        }}

        QLabel#heading2 {{
            color: {TEXT_PRIMARY};
            font-size: {FONT_SIZE_XLARGE}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
        }}

        QLabel#heading3 {{
            color: {TEXT_PRIMARY};
            font-size: {FONT_SIZE_LARGE}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
        }}

        QLabel#secondary {{
            color: {TEXT_SECONDARY};
            font-size: {FONT_SIZE_SMALL}px;
        }}
    """
