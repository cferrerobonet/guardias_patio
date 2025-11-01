"""Widgets para el formulario de asignación de guardias.

Widgets disponibles:
- EstadisticasPanel: Muestra estadísticas del curso
- DistribucionPanel: Muestra distribución objetivo de guardias
- ResultadosPanel: Muestra resultados de generación
- IncidenciasPanel: Analiza incidencias y propone soluciones
"""

from .distribucion_panel import DistribucionPanel
from .estadisticas_panel import EstadisticasPanel
from .incidencias_panel import IncidenciasPanel
from .resultados_panel import ResultadosPanel

__all__ = [
    "EstadisticasPanel",
    "DistribucionPanel",
    "ResultadosPanel",
    "IncidenciasPanel",
]
