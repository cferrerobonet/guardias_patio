"""
Mappers - Conversión entre Modelos de Persistencia y Entidades de Dominio

Los mappers se encargan de convertir:
- Modelos SQLAlchemy → Domain Entities
- Domain Entities → Modelos SQLAlchemy

Esto mantiene el dominio desacoplado de la persistencia.
"""

from .guardia_mapper import GuardiaMapper
from .profesor_mapper import ProfesorMapper
from .zona_mapper import ZonaMapper

__all__ = [
    "ProfesorMapper",
    "ZonaMapper",
    "GuardiaMapper",
]
