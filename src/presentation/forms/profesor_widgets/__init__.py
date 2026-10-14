"""
Widgets para el formulario de profesor.

Este módulo contiene widgets reutilizables para el formulario de gestión de profesores.
"""

from .datos_basicos_widget import DatosBasicosWidget
from .horario_widget import HorarioWidget
from .restricciones_widget import RestriccionesWidget

__all__ = [
    "DatosBasicosWidget",
    "HorarioWidget",
    "RestriccionesWidget",
]
