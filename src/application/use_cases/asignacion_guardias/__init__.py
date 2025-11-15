"""
Use Cases para Asignación de Guardias.

Exporta los casos de uso relacionados con la generación y distribución de guardias.
"""

from .calcular_distribucion import CalcularDistribucionUseCase
from .generar_guardias import GenerarGuardiasUseCase
from .generar_guardias_hibrido import GenerarGuardiasHibridoUseCase
from .obtener_estadisticas import ObtenerEstadisticasUseCase

__all__ = [
    "ObtenerEstadisticasUseCase",
    "CalcularDistribucionUseCase",
    "GenerarGuardiasUseCase",
]
