"""
Sistema de temas para la aplicación.

Contiene paletas de colores, tipografía y estilos CSS para
diferentes sistemas de diseño.
"""

# Importar desde el tema CCleaner
from presentation.themes.ccleaner_theme import (
    CONTENT_BG,
    ERROR_RED,
    PRIMARY_BLUE,
    SUCCESS_GREEN,
    TEXT_PRIMARY,
    WARNING_ORANGE,
    get_button_primary_style,
    get_button_secondary_style,
    get_complete_stylesheet,
    get_input_style,
)

__all__ = [
    "PRIMARY_BLUE",
    "SUCCESS_GREEN",
    "ERROR_RED",
    "WARNING_ORANGE",
    "CONTENT_BG",
    "TEXT_PRIMARY",
    "get_complete_stylesheet",
    "get_button_primary_style",
    "get_button_secondary_style",
    "get_input_style",
]
