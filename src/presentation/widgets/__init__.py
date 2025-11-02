"""
Widgets refactorizados de la capa de presentación.
"""

from .gestionar_ausencias import GestionarAusenciasForm
from .gestor_sustituciones import GestorSustituciones
from .panel_estadisticas import PanelEstadisticas
from .table_manager import TableManager
from .vista_calendario import VistaCalendario

__all__ = [
    "GestionarAusenciasForm",
    "GestorSustituciones",
    "PanelEstadisticas",
    "TableManager",
    "VistaCalendario",
]
