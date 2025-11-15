"""Widgets para el formulario de asignación de guardias.

Widgets disponibles:
- EstadisticasPanel: Muestra estadísticas del curso
- DistribucionPanel: Muestra distribución objetivo de guardias
- ResultadosPanel: Muestra resultados de generación
- IncidenciasPanel: Analiza incidencias y propone soluciones
- EquidadPanel: Análisis de equidad usando Domain Services (Phase 3)
- CuotasPanel: Cálculo de cuotas usando Domain Services (Phase 3)
"""

from .cuotas_panel import CuotasPanel
from .distribucion_panel import DistribucionPanel
from .equidad_panel import EquidadPanel
from .estadisticas_panel import EstadisticasPanel
from .incidencias_panel import IncidenciasPanel
from .resultados_panel import ResultadosPanel

__all__ = [
    "CuotasPanel",
    "EstadisticasPanel",
    "DistribucionPanel",
    "ResultadosPanel",
    "IncidenciasPanel",
    "EquidadPanel",
]
