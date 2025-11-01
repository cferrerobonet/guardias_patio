"""
Widgets refactorizados de la capa de presentación.
"""

from .dashboard_resumen import DashboardResumen
from .gestionar_ausencias import GestionarAusenciasForm
from .gestor_sustituciones import GestorSustituciones
from .panel_estadisticas import PanelEstadisticas
from .reportes_form import ReportesForm
from .table_manager import TableManager
from .vista_calendario import VistaCalendario

__all__ = [
    "DashboardResumen",
    "GestionarAusenciasForm",
    "GestorSustituciones",
    "PanelEstadisticas",
    "ReportesForm",
    "TableManager",
    "VistaCalendario",
]
