"""
Módulo de estilos UI para la aplicación de Guardias de Patio.
Define estilos CSS consistentes para toda la interfaz.
"""

# ========== COLORES ==========
COLOR_PRIMARY = "#2196F3"  # Azul principal
COLOR_SUCCESS = "#4CAF50"  # Verde para acciones positivas
COLOR_WARNING = "#FF9800"  # Naranja para ediciones
COLOR_DANGER = "#f44336"  # Rojo para acciones destructivas
COLOR_INFO = "#00BCD4"  # Cyan para información

COLOR_BG_LIGHT = "#f5f5f5"  # Fondo claro
COLOR_BG_MEDIUM = "#e0e0e0"  # Fondo medio
COLOR_TEXT_DARK = "#212121"  # Texto oscuro
COLOR_TEXT_MEDIUM = "#757575"  # Texto medio

# ========== ESTILOS DE TÍTULOS ==========

STYLE_TITLE_MAIN = f"""
    QLabel {{
        font-size: 15px;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        background-color: {COLOR_BG_LIGHT};
        padding: 6px 10px;
        border-left: 4px solid {COLOR_PRIMARY};
        border-radius: 4px;
        margin-bottom: 4px;
    }}
"""

STYLE_TITLE_SECTION = f"""
    QLabel {{
        font-size: 13px;
        font-weight: bold;
        color: {COLOR_TEXT_DARK};
        background-color: transparent;
        padding: 0px 8px;
        border-left: 3px solid {COLOR_PRIMARY};
        margin: 0px;
    }}
"""

STYLE_TITLE_SUBSECTION = f"""
    QLabel {{
        font-size: 12px;
        font-weight: bold;
        color: {COLOR_TEXT_MEDIUM};
        margin-top: 8px;
    }}
"""

# ========== ESTILOS DE GROUPBOX ==========

STYLE_GROUPBOX = f"""
    QGroupBox {{
        font-weight: bold;
        font-size: 13px;
        color: {COLOR_PRIMARY};
        border: 2px solid {COLOR_BG_MEDIUM};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 10px;
        background-color: white;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 4px 10px;
        background-color: {COLOR_BG_LIGHT};
        border-radius: 4px;
    }}
"""

# ========== ESTILOS DE BOTONES ==========

STYLE_BUTTON_PRIMARY = f"""
    QPushButton {{
        background-color: {COLOR_PRIMARY};
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 13px;
        min-width: 120px;
    }}
    QPushButton:hover {{
        background-color: #0b7dda;
    }}
    QPushButton:pressed {{
        background-color: #0a6bc4;
    }}
    QPushButton:disabled {{
        background-color: #cccccc;
        color: #666666;
    }}
"""

STYLE_BUTTON_SUCCESS = f"""
    QPushButton {{
        background-color: {COLOR_SUCCESS};
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 13px;
        min-width: 120px;
    }}
    QPushButton:hover {{
        background-color: #45a049;
    }}
    QPushButton:pressed {{
        background-color: #3d8b40;
    }}
"""

STYLE_BUTTON_WARNING = f"""
    QPushButton {{
        background-color: {COLOR_WARNING};
        color: white;
        font-weight: bold;
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        font-size: 12px;
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: #e68900;
    }}
    QPushButton:pressed {{
        background-color: #cc7a00;
    }}
"""

STYLE_BUTTON_DANGER = f"""
    QPushButton {{
        background-color: {COLOR_DANGER};
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 13px;
        min-width: 120px;
    }}
    QPushButton:hover {{
        background-color: #da190b;
    }}
    QPushButton:pressed {{
        background-color: #c1170a;
    }}
"""

STYLE_BUTTON_SECONDARY = f"""
    QPushButton {{
        background-color: white;
        color: {COLOR_TEXT_DARK};
        font-weight: bold;
        padding: 8px 16px;
        border: 2px solid {COLOR_BG_MEDIUM};
        border-radius: 4px;
        font-size: 12px;
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_BG_LIGHT};
        border-color: {COLOR_PRIMARY};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_BG_MEDIUM};
    }}
"""

# ========== ESTILOS DE INPUTS ==========

STYLE_INPUT = """
    QLineEdit, QDateEdit, QTimeEdit, QComboBox, QTextEdit {{
        padding: 10px;
        border: 2px solid #bdbdbd;
        border-radius: 5px;
        font-size: 14px;
        background-color: #fafafa;
        min-height: 20px;
        color: #212121;
    }}
    QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus, QTextEdit:focus {{
        border-color: #2196F3;
        background-color: white;
        border-width: 3px;
    }}
    QLineEdit:disabled, QDateEdit:disabled, QTimeEdit:disabled, QComboBox:disabled {{
        background-color: #eeeeee;
        color: #999999;
        border-color: #e0e0e0;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #666666;
        margin-right: 8px;
    }}
"""

# Estilo específico para etiquetas de campos
STYLE_LABEL_FIELD = f"""
    QLabel {{
        font-size: 13px;
        font-weight: bold;
        color: {COLOR_TEXT_DARK};
        margin-bottom: 4px;
        margin-top: 8px;
    }}
"""

# ========== ESTILO TERMINAL RETRO ==========

STYLE_TERMINAL_RETRO = """
    QTextEdit {
        background-color: #3C3C3C;
        color: #00FF00;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 12px;
        padding: 12px;
        border: 2px solid #555555;
        border-radius: 4px;
        selection-background-color: #2A4A2A;
        selection-color: #00FF00;
    }
    QTextEdit[readOnly="true"] {
        background-color: #3C3C3C;
    }
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


def wrap_terminal_html(content: str) -> str:
    """
    Envuelve el contenido HTML en un div con word-wrap para terminales.

    Args:
        content: Contenido HTML a envolver

    Returns:
        HTML envuelto con estilos de word-wrap
    """
    styles = "white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;"
    return f'<div style="{styles}">{content}</div>'


def format_terminal_header(text: str) -> str:
    """Formatea un encabezado en estilo terminal (verde brillante)."""
    return f'<span style="color: #00FF00; font-weight: bold;">{text}</span>'


def format_terminal_label(text: str) -> str:
    """Formatea una etiqueta/label (cyan claro)."""
    return f'<span style="color: #00FFFF;">{text}</span>'


def format_terminal_value(text: str) -> str:
    """Formatea un valor numérico (amarillo)."""
    return f'<span style="color: #FFFF00;">{text}</span>'


def format_terminal_success(text: str) -> str:
    """Formatea un mensaje de éxito (verde)."""
    return f'<span style="color: #00FF00;">{text}</span>'


def format_terminal_warning(text: str) -> str:
    """Formatea una advertencia (naranja/ámbar)."""
    return f'<span style="color: #FFA500;">{text}</span>'


def format_terminal_error(text: str) -> str:
    """Formatea un error (rojo)."""
    return f'<span style="color: #FF4444;">{text}</span>'


def format_terminal_info(text: str) -> str:
    """Formatea información secundaria (gris claro)."""
    return f'<span style="color: #AAAAAA;">{text}</span>'


def format_terminal_profesor(text: str) -> str:
    """Formatea nombre de profesor (azul brillante)."""
    return f'<span style="color: #00BFFF;">{text}</span>'


def format_terminal_number(text: str) -> str:
    """Formatea números importantes (amarillo brillante)."""
    return f'<span style="color: #FFFF00; font-weight: bold;">{text}</span>'


def format_terminal_prompt(text: str) -> str:
    """Formatea un prompt de terminal (verde oscuro)."""
    return f'<span style="color: #00AA00;">$</span> <span style="color: #00FF00;">{text}</span>'
