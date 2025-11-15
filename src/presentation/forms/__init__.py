"""
Forms

Formularios principales de la aplicación.
Cada form es un QWidget que representa una pantalla completa.
"""

from .asignacion_calculo_form import AsignacionCalculoForm
from .asignacion_resultados_form import AsignacionResultadosForm
from .base_form import BaseForm
from .dashboard_form import DashboardForm
from .import_export_form import ImportExportForm
from .profesor_form import ProfesorForm
from .zona_form import ZonaForm

__all__ = [
    'BaseForm',
    'ZonaForm',
    'AsignacionCalculoForm',
    'AsignacionResultadosForm',
    'ProfesorForm',
    'ImportExportForm',
    'DashboardForm',
]
