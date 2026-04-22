"""
Funciones de formateo HTML para el panel de salida del generador CP-SAT.
Produce spans coloreados sobre fondo oscuro (estilo terminal retro).
"""


def wrap_terminal_html(content: str) -> str:
    styles = "white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;"
    return f'<div style="{styles}">{content}</div>'


def format_terminal_header(text: str) -> str:
    return f'<span style="color: #00FF00; font-weight: bold;">{text}</span>'


def format_terminal_label(text: str) -> str:
    return f'<span style="color: #00FFFF;">{text}</span>'


def format_terminal_value(text: str) -> str:
    return f'<span style="color: #FFFF00;">{text}</span>'


def format_terminal_success(text: str) -> str:
    return f'<span style="color: #00FF00;">{text}</span>'


def format_terminal_warning(text: str) -> str:
    return f'<span style="color: #FFA500;">{text}</span>'


def format_terminal_error(text: str) -> str:
    return f'<span style="color: #FF4444;">{text}</span>'


def format_terminal_info(text: str) -> str:
    return f'<span style="color: #AAAAAA;">{text}</span>'


def format_terminal_profesor(text: str) -> str:
    return f'<span style="color: #00BFFF;">{text}</span>'


def format_terminal_number(text: str) -> str:
    return f'<span style="color: #FFFF00; font-weight: bold;">{text}</span>'


def format_terminal_prompt(text: str) -> str:
    return f'<span style="color: #00AA00;">$</span> <span style="color: #00FF00;">{text}</span>'
