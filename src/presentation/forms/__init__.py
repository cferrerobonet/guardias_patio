"""
Forms

Formularios principales de la aplicación.
Cada form es un QWidget que representa una pantalla completa.
"""

from .asignacion_guardias_form import AsignacionGuardiasForm
from .base_form import BaseForm
from .calendario_guardias_form import CalendarioGuardiasForm
from .configuracion_form import ConfiguracionForm
from .import_export_form import ImportExportForm
from .profesor_form import ProfesorForm
from .zona_form import ZonaForm

__all__ = [
    'BaseForm',
    'ConfiguracionForm',
    'ZonaForm',
    'AsignacionGuardiasForm',
    'ProfesorForm',
    'ImportExportForm',
    'CalendarioGuardiasForm',
]
