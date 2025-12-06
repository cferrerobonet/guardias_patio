"""Widgets para el formulario de asignación de guardias.

Widgets disponibles:
- EstadisticasPanel: Muestra estadísticas del curso (estilo terminal)
- CuotasPanel: Cálculo de cuotas usando Domain Services (estilo terminal)
- ResultadosPanel: Resultados de generación con métricas de equidad (estilo terminal)
- IncidenciasPanel: Analiza incidencias y propone soluciones (estilo terminal)
"""

from .cuotas_panel import CuotasPanel
from .estadisticas_panel import EstadisticasPanel
from .incidencias_panel import IncidenciasPanel
from .resultados_panel import ResultadosPanel

__all__ = [
    "CuotasPanel",
    "EstadisticasPanel",
    "ResultadosPanel",
    "IncidenciasPanel",
]
