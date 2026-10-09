"""
Sistema de Temas — capa de compatibilidad.

Las constantes de este módulo son aliases de presentation.theme.tokens.
No añadir constantes nuevas aquí; usar tokens.Colors directamente.
"""

from presentation.theme.tokens import BorderRadius, Colors, FontSize, Spacing

# Sidebar
SIDEBAR_BG = Colors.SIDEBAR_BG
SIDEBAR_BG_DARK = Colors.SIDEBAR_HOVER
SIDEBAR_TEXT = Colors.SIDEBAR_TEXT
SIDEBAR_TEXT_DIM = Colors.TEXT_SECONDARY
SIDEBAR_HOVER = Colors.SIDEBAR_HOVER
SIDEBAR_ACTIVE = Colors.BACKGROUND
SIDEBAR_BORDER = Colors.SIDEBAR_BORDER

# Acción
PRIMARY_BLUE = Colors.PRIMARY
PRIMARY_BLUE_HOVER = Colors.PRIMARY_DARK
PRIMARY_BLUE_LIGHT = Colors.PRIMARY_LIGHT

# Estado
SUCCESS_GREEN = Colors.SUCCESS
SUCCESS_GREEN_LIGHT = Colors.SUCCESS_BG
WARNING_ORANGE = Colors.GOLD
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
FONT_FAMILY = "'Barlow', 'Helvetica Neue', 'Segoe UI', Arial, sans-serif"
FONT_FAMILY_TITULOS = "'Barlow Condensed', " + FONT_FAMILY
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
    """Menú lateral claro, como el de los ajustes de Partes de salida."""
    return f"""
        QWidget#sidebar {{
            background-color: {SIDEBAR_BG};
            border-right: 1px solid {SIDEBAR_BORDER};
        }}

        QLabel#sidebarTitle {{
            color: {SIDEBAR_TEXT};
            font-family: {FONT_FAMILY_TITULOS};
            font-size: 19px;
            font-weight: {FONT_WEIGHT_BOLD};
            padding: {SPACING_MD}px;
        }}

        QLabel#menuCategory {{
            color: {TEXT_SECONDARY};
            background-color: transparent;
            font-size: 12px;
            font-weight: {FONT_WEIGHT_BOLD};
            padding: {SPACING_MD}px {SPACING_LG}px {SPACING_XS}px {SPACING_LG}px;
            margin-top: {SPACING_LG}px;
            margin-bottom: {SPACING_XS}px;
            border: none;
        }}

        QPushButton#menuButton {{
            background-color: transparent;
            color: {SIDEBAR_TEXT};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            padding: 7px {SPACING_MD}px;
            text-align: left;
            border: 1px solid transparent;
            border-radius: {RADIUS_MEDIUM}px;
            margin: 1px 10px;
        }}

        QPushButton#menuButton:hover {{
            background-color: {SIDEBAR_HOVER};
        }}

        QPushButton#menuButtonActive {{
            background-color: {CONTENT_BG};
            color: {PRIMARY_BLUE};
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: {FONT_WEIGHT_BOLD};
            padding: 7px {SPACING_MD}px;
            text-align: left;
            border: 1px solid {BORDER_LIGHT};
            border-radius: {RADIUS_MEDIUM}px;
            margin: 1px 10px;
        }}

        QPushButton#collapseButton {{
            background-color: transparent;
            color: {TEXT_SECONDARY};
            font-size: 16px;
            border: none;
            border-radius: {RADIUS_SMALL}px;
        }}

        QPushButton#collapseButton:hover {{
            background-color: {SIDEBAR_HOVER};
            color: {TEXT_PRIMARY};
        }}

        QFrame[frameShape="4"] {{
            background-color: {BORDER_LIGHT};
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
            border-radius: {RADIUS_LARGE}px;
        }}

        QTableWidget::item, QTableView::item {{
            padding: {SPACING_SM}px;
        }}

        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {PRIMARY_BLUE_LIGHT};
            color: {TEXT_PRIMARY};
        }}

        QHeaderView::section {{
            background-color: {Colors.SURFACE_2};
            color: {TEXT_SECONDARY};
            font-size: 13px;
            font-weight: {FONT_WEIGHT_BOLD};
            padding: 7px {SPACING_SM}px;
            border: none;
            border-bottom: 1px solid {BORDER_LIGHT};
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
    """Reglas que sólo existen en la ventana principal.

    Lo común (botones, campos, tablas, pestañas, barras, cajas) está en `light.qss`,
    que se aplica a toda la aplicación. Esta hoja repetía esas reglas con otros
    valores y, al aplicarse a la ventana, los imponía: por eso había campos y
    botones de alturas distintas según la pantalla.
    """
    return f"""
        /* Una ayuda emergente es un QWidget: sin regla propia hereda el color del
           texto pero no el fondo. Esta hoja se aplica a la ventana y manda sobre la
           de la aplicación, así que hay que repetirla aquí. */
        QToolTip {{
            background-color: {TEXT_PRIMARY};
            color: {Colors.TEXT_ON_PRIMARY};
            border: none;
            border-radius: 6px;
            padding: 5px 8px;
            font-size: 13px;
        }}

        /* Cancelar y No: secundarios, blancos con borde */
        QMessageBox QPushButton[text="No"],
        QMessageBox QPushButton[text="Cancelar"],
        QDialogButtonBox QPushButton[text="No"],
        QDialogButtonBox QPushButton[text="Cancelar"],
        QDialog QPushButton[text="No"],
        QDialog QPushButton[text="Cancelar"] {{
            background-color: {CONTENT_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_MEDIUM};
        }}

        QMessageBox QPushButton[text="No"]:hover,
        QMessageBox QPushButton[text="Cancelar"]:hover,
        QDialogButtonBox QPushButton[text="No"]:hover,
        QDialogButtonBox QPushButton[text="Cancelar"]:hover,
        QDialog QPushButton[text="No"]:hover,
        QDialog QPushButton[text="Cancelar"]:hover {{
            border-color: {PRIMARY_BLUE};
        }}

        /* ========== LABELS SEMÁNTICOS ========== */
        QLabel#labelCaption {{
            color: {TEXT_SECONDARY};
            font-size: {FONT_SIZE_SMALL}px;
        }}

        QLabel#labelTitle {{
            font-family: {FONT_FAMILY_TITULOS};
            font-size: 22px;
            font-weight: {FONT_WEIGHT_BOLD};
            color: {TEXT_PRIMARY};
        }}

        QLabel#labelSubtitle {{
            font-family: {FONT_FAMILY_TITULOS};
            font-size: 19px;
            font-weight: {FONT_WEIGHT_BOLD};
            color: {TEXT_PRIMARY};
        }}

        QLabel#labelSecondary {{
            color: {TEXT_SECONDARY};
            font-size: {FONT_SIZE_NORMAL}px;
        }}

        /* ========== INFO BOXES (objectName) ========== */
        QLabel#infoBoxInfo {{
            background-color: {Colors.INFO_BG};
            border-left: 3px solid {PRIMARY_BLUE};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {TEXT_PRIMARY};
        }}

        QLabel#infoBoxSuccess {{
            background-color: {Colors.SUCCESS_BG};
            border-left: 3px solid {Colors.SUCCESS};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {TEXT_PRIMARY};
        }}

        QLabel#infoBoxWarning {{
            background-color: {Colors.WARNING_BG};
            border-left: 3px solid {Colors.WARNING_BORDER};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {TEXT_PRIMARY};
        }}

        QLabel#infoBoxError {{
            background-color: {Colors.ERROR_BG};
            border-left: 3px solid {ERROR_RED};
            border-radius: {RADIUS_MEDIUM}px;
            padding: {SPACING_SM}px {SPACING_MD}px;
            color: {Colors.ERROR_ON_BG};
        }}
    """
