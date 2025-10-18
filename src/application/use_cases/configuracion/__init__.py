"""
Use Cases para Configuración.

Casos de uso para gestionar la configuración del curso escolar.
"""

from .actualizar_configuracion import ActualizarConfiguracionUseCase
from .obtener_configuracion import ObtenerConfiguracionUseCase

__all__ = [
    'ObtenerConfiguracionUseCase',
    'ActualizarConfiguracionUseCase',
]
