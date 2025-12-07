"""Widgets para el formulario de asignación de guardias.

Widgets disponibles:
- CalculoPanel: Panel combinado de estadísticas y cuotas (estilo terminal)
- GeneracionPanel: Panel combinado de generación y resultados (estilo terminal)
- EstadisticasPanel: Muestra estadísticas del curso (estilo terminal)
- CuotasPanel: Cálculo de cuotas usando Domain Services (estilo terminal)
- ResultadosPanel: Resultados de generación con métricas de equidad (estilo terminal)
- IncidenciasPanel: Analiza incidencias y propone soluciones (estilo terminal)
"""

from .calculo_panel import CalculoPanel
from .cuotas_panel import CuotasPanel
from .estadisticas_panel import EstadisticasPanel
from .generacion_panel import GeneracionPanel
from .incidencias_panel import IncidenciasPanel
from .resultados_panel import ResultadosPanel

__all__ = [
    "CalculoPanel",
    "GeneracionPanel",
    "CuotasPanel",
    "EstadisticasPanel",
    "ResultadosPanel",
    "IncidenciasPanel",
]
