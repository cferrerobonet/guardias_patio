"""
Funciones de formateo HTML para el panel de salida del generador CP-SAT.

El panel tiene fondo verde muy suave en claro y oscuro en modo oscuro. Los colores
van escritos en el HTML, que `modo_oscuro` no traduce, así que cada papel tiene su
color para los dos modos y se elige al escribir. Todos superan 4,5:1 sobre su fondo.
"""

from presentation.theme import modo_oscuro
from presentation.theme.tokens import TERMINAL_CLARO, TERMINAL_OSCURO

_CLARO, _OSCURO = TERMINAL_CLARO, TERMINAL_OSCURO


def _c(papel: str) -> str:
    return (_OSCURO if modo_oscuro.es_oscuro() else _CLARO)[papel]


def wrap_terminal_html(content: str) -> str:
    styles = "white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;"
    return f'<div style="{styles}">{content}</div>'


def format_terminal_header(text: str) -> str:
    return f'<span style="color: {_c("titulo")}; font-weight: bold;">{text}</span>'


def format_terminal_label(text: str) -> str:
    return f'<span style="color: {_c("etiqueta")};">{text}</span>'


def format_terminal_value(text: str) -> str:
    return f'<span style="color: {_c("valor")};">{text}</span>'


def format_terminal_success(text: str) -> str:
    return f'<span style="color: {_c("exito")};">{text}</span>'


def format_terminal_warning(text: str) -> str:
    return f'<span style="color: {_c("aviso")};">{text}</span>'


def format_terminal_error(text: str) -> str:
    return f'<span style="color: {_c("error")};">{text}</span>'


def format_terminal_info(text: str) -> str:
    return f'<span style="color: {_c("info")};">{text}</span>'


def format_terminal_profesor(text: str) -> str:
    return f'<span style="color: {_c("profesor")};">{text}</span>'


def format_terminal_number(text: str) -> str:
    return f'<span style="color: {_c("valor")}; font-weight: bold;">{text}</span>'


def format_terminal_prompt(text: str) -> str:
    prompt = f'<span style="color: {_c("prompt")};">$</span>'
    return f'{prompt} <span style="color: {_c("exito")};">{text}</span>'
