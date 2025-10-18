"""
Forms

Formularios principales de la aplicación.
Cada form es un QWidget que representa una pantalla completa.
"""

from .asignacion_guardias_form import AsignacionGuardiasForm
from .base_form import BaseForm
from .configuracion_form import ConfiguracionForm
from .zona_form import ZonaForm

__all__ = [
    'BaseForm',
    'ConfiguracionForm',
    'ZonaForm',
    'AsignacionGuardiasForm',
]
