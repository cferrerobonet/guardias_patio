"""
Estilos UI heredados — sólo para widgets que necesitan setStyleSheet() con overrides inline.
Para botones nuevos usar setProperty("success"/"danger"/"warning", "true") + light.qss.
"""

from presentation.theme.tokens import Colors

# ========== COLORES — aliases de tokens.Colors (fuente única de verdad) ==========
COLOR_PRIMARY = Colors.PRIMARY
COLOR_SUCCESS = Colors.SUCCESS
COLOR_WARNING = Colors.WARNING
COLOR_DANGER = Colors.ERROR
COLOR_INFO = Colors.INFO

COLOR_BG_LIGHT = Colors.SURFACE
COLOR_BG_MEDIUM = Colors.BORDER_DARK
COLOR_TEXT_DARK = Colors.TEXT_PRIMARY
COLOR_TEXT_MEDIUM = Colors.TEXT_SECONDARY

#: Medidas comunes con `light.qss`: 34 px de alto para botones y campos.
_BOTON = """
        font-weight: 600;
        font-size: 14px;
        padding: 6px 14px;
        border-radius: 8px;
        min-height: 20px;
        min-width: 96px;
"""

# ========== ESTILOS DE TÍTULOS ==========

STYLE_TITLE_MAIN = f"""
    QLabel {{
        font-family: "Barlow Condensed", "Barlow";
        font-size: 19px;
        font-weight: 700;
        color: {COLOR_TEXT_DARK};
        background-color: transparent;
        padding: 4px 0px;
        margin-bottom: 6px;
    }}
"""

STYLE_TITLE_SECTION = f"""
    QLabel {{
        font-family: "Barlow Condensed", "Barlow";
        font-size: 16px;
        font-weight: 700;
        color: {COLOR_TEXT_DARK};
        background-color: transparent;
        padding: 0px;
        margin: 0px;
    }}
"""

STYLE_TITLE_SUBSECTION = f"""
    QLabel {{
        font-size: 12px;
        font-weight: 700;
        color: {COLOR_TEXT_MEDIUM};
        margin-top: 8px;
    }}
"""

# ========== ESTILOS DE GROUPBOX ==========

STYLE_GROUPBOX = f"""
    QGroupBox {{
        font-family: "Barlow Condensed", "Barlow";
        font-weight: 700;
        font-size: 16px;
        color: {COLOR_TEXT_DARK};
        border: 1px solid {Colors.BORDER};
        border-radius: 10px;
        margin-top: 18px;
        padding: 14px 10px 10px 10px;
        background-color: {Colors.BACKGROUND};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0px 4px;
        left: 10px;
        top: 0px;
        background-color: transparent;
    }}
"""

# ========== ESTILOS DE BOTONES (legacy) ==========
# Usar solo en widgets que necesiten concatenar CSS inline.
# Código nuevo: btn.setProperty("success", "true")  # gestionado por light.qss

STYLE_BUTTON_PRIMARY = f"""
    QPushButton {{
        background-color: {COLOR_PRIMARY};
        color: {Colors.TEXT_ON_PRIMARY};
        border: 1px solid {COLOR_PRIMARY};{_BOTON}    }}
    QPushButton:hover {{
        background-color: {Colors.PRIMARY_DARK};
        border-color: {Colors.PRIMARY_DARK};
    }}
    QPushButton:pressed {{
        background-color: {Colors.PRIMARY_DARK};
    }}
    QPushButton:disabled {{
        background-color: {Colors.BORDER};
        border-color: {Colors.BORDER};
        color: {Colors.TEXT_SECONDARY};
    }}
"""

STYLE_BUTTON_SUCCESS = f"""
    QPushButton {{
        background-color: {COLOR_SUCCESS};
        color: {Colors.TEXT_ON_PRIMARY};
        border: 1px solid {COLOR_SUCCESS};{_BOTON}    }}
    QPushButton:hover {{
        background-color: {Colors.SUCCESS_DARK};
        border-color: {Colors.SUCCESS_DARK};
    }}
    QPushButton:pressed {{
        background-color: {Colors.SUCCESS_DARK};
    }}
"""

STYLE_BUTTON_WARNING = f"""
    QPushButton {{
        background-color: {COLOR_WARNING};
        color: {Colors.TEXT_ON_PRIMARY};
        border: 1px solid {COLOR_WARNING};{_BOTON}    }}
    QPushButton:hover {{
        background-color: {Colors.SECONDARY_HOVER};
        border-color: {Colors.SECONDARY_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {Colors.SECONDARY_HOVER};
    }}
"""

STYLE_BUTTON_DANGER = f"""
    QPushButton {{
        background-color: {COLOR_DANGER};
        color: {Colors.TEXT_ON_PRIMARY};
        border: 1px solid {COLOR_DANGER};{_BOTON}    }}
    QPushButton:hover {{
        background-color: {Colors.ERROR_ON_BG};
        border-color: {Colors.ERROR_ON_BG};
    }}
    QPushButton:pressed {{
        background-color: {Colors.ERROR_ON_BG};
    }}
"""

STYLE_BUTTON_SECONDARY = f"""
    QPushButton {{
        background-color: {Colors.BACKGROUND};
        color: {COLOR_TEXT_DARK};
        border: 1px solid {COLOR_BG_MEDIUM};{_BOTON}    }}
    QPushButton:hover {{
        background-color: {Colors.BACKGROUND};
        border-color: {COLOR_PRIMARY};
    }}
    QPushButton:pressed {{
        background-color: {Colors.SURFACE_2};
    }}
"""

# ========== ESTILOS DE INPUTS ==========

STYLE_INPUT = f"""
    QLineEdit, QDateEdit, QTimeEdit, QComboBox, QTextEdit {{
        padding: 6px 9px;
        border: 1px solid {Colors.BORDER_CONTROL};
        border-radius: 7px;
        font-size: 14px;
        background-color: {Colors.SURFACE};
        min-height: 20px;
        color: {COLOR_TEXT_DARK};
    }}
    QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus, QTextEdit:focus {{
        border-color: {Colors.FOCUS_RING};
        background-color: {Colors.BACKGROUND};
    }}
    QLineEdit:disabled, QDateEdit:disabled, QTimeEdit:disabled, QComboBox:disabled {{
        background-color: {Colors.SURFACE_2};
        color: {Colors.TEXT_SECONDARY};
        border-color: {Colors.BORDER};
    }}
"""

# Estilo específico para etiquetas de campos
STYLE_LABEL_FIELD = f"""
    QLabel {{
        font-size: 13px;
        font-weight: 700;
        color: {COLOR_TEXT_DARK};
        margin-bottom: 4px;
        margin-top: 8px;
    }}
"""

# ========== PANEL DE RESULTADOS («pizarra») ==========

STYLE_TERMINAL_RETRO = f"""
    QTextEdit {{
        background-color: {Colors.TERMINAL_BG};
        color: {Colors.TERMINAL_TEXT};
        font-family: "JetBrains Mono", "Menlo", "Consolas", monospace;
        font-size: 13px;
        padding: 12px;
        border: 1px solid {Colors.TERMINAL_BORDER};
        border-radius: 10px;
        selection-background-color: {Colors.PRIMARY};
        selection-color: {Colors.TEXT_ON_PRIMARY};
    }}
    QTextEdit[readOnly="true"] {{
        background-color: {Colors.TERMINAL_BG};
    }}
"""

# ========== FUNCIONES DE UTILIDAD ==========


def create_title_label(text: str, level: str = "main") -> str:
    """
    Crea un QLabel con estilo de título.

    Args:
        text: Texto del título
        level: Nivel del título ("main", "section", "subsection")

    Returns:
        Texto con HTML formateado para el título
    """
    if level == "main":
        return text
    elif level == "section":
        return text
    else:
        return text


def set_max_width_for_inputs(widget, max_width: int = 400):
    """
    Establece un ancho máximo para un widget de input.

    Args:
        widget: Widget al que aplicar el ancho máximo
        max_width: Ancho máximo en píxeles (default: 400)
    """
    widget.setMaximumWidth(max_width)


def apply_compact_layout(layout):
    """
    Aplica márgenes compactos a un layout.

    Args:
        layout: Layout al que aplicar los márgenes
    """
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(8)


# ========== FUNCIONES DE FORMATEO TERMINAL ==========
# Delegadas a terminal_format.py — importar desde allí en código nuevo.
from presentation.theme.terminal_format import (  # noqa: E402, F401
    format_terminal_error,
    format_terminal_header,
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_profesor,
    format_terminal_prompt,
    format_terminal_success,
    format_terminal_value,
    format_terminal_warning,
    wrap_terminal_html,
)
