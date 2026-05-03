"""
Widgets refactorizados de la capa de presentación.
"""

from .ausencias_sustituciones import AusenciasSustitucionesWidget
from .gestionar_ausencias import GestionarAusenciasForm
from .gestor_sustituciones import GestorSustituciones
from .panel_estadisticas import PanelEstadisticas
from .selector_curso_widget import SelectorCursoWidget
from .table_manager import TableManager
from .toast_notification import ToastNotification
from .vista_calendario import VistaCalendario

__all__ = [
    "AusenciasSustitucionesWidget",
    "GestionarAusenciasForm",
    "GestorSustituciones",
    "PanelEstadisticas",
    "SelectorCursoWidget",
    "TableManager",
    "ToastNotification",
    "VistaCalendario",
]
