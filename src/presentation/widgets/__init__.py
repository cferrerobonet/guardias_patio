"""
Widgets refactorizados de la capa de presentación.
"""

from .dashboard_resumen import DashboardResumen
from .gestionar_ausencias import GestionarAusenciasForm
from .gestor_sustituciones import GestorSustituciones
from .notificaciones_panel import NotificacionesPanel
from .panel_estadisticas import PanelEstadisticas
from .reportes_form import ReportesForm
from .vista_calendario import VistaCalendario

__all__ = [
    "DashboardResumen",
    "GestionarAusenciasForm",
    "GestorSustituciones",
    "NotificacionesPanel",
    "PanelEstadisticas",
    "ReportesForm",
    "VistaCalendario",
]
