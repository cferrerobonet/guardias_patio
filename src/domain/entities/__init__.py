"""
Domain Entities para el dominio de Guardias de Patio.

Las Entities son objetos con identidad propia (ID) y ciclo de vida.
Contienen lógica de negocio y reglas de dominio.
"""

from .guardia_entity import GuardiaEntity
from .profesor_entity import ProfesorEntity
from .zona_entity import ZonaEntity

__all__ = [
    "ProfesorEntity",
    "ZonaEntity",
    "GuardiaEntity",
]
