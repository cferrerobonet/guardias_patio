"""
Sistema de temas para la aplicación.

Contiene paletas de colores, tipografía y estilos CSS para
diferentes sistemas de diseño.
"""

# Importar desde el nuevo tema CCleaner
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

# Alias para compatibilidad con código existente
FLUENT_BLUE = PRIMARY_BLUE
FLUENT_SUCCESS = SUCCESS_GREEN
FLUENT_ERROR = ERROR_RED
FLUENT_WARNING = WARNING_ORANGE
FLUENT_GRAY_10 = CONTENT_BG
FLUENT_GRAY_190 = TEXT_PRIMARY
get_complete_fluent_stylesheet = get_complete_stylesheet

__all__ = [
    'FLUENT_BLUE',
    'FLUENT_SUCCESS',
    'FLUENT_ERROR',
    'FLUENT_WARNING',
    'FLUENT_GRAY_10',
    'FLUENT_GRAY_190',
    'PRIMARY_BLUE',
    'SUCCESS_GREEN',
    'ERROR_RED',
    'WARNING_ORANGE',
    'get_complete_fluent_stylesheet',
    'get_complete_stylesheet',
    'get_button_primary_style',
    'get_button_secondary_style',
    'get_input_style',
]

