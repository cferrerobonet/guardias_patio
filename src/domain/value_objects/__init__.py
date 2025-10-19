"""
Value Objects para el dominio de Guardias de Patio.

Los Value Objects son objetos inmutables que encapsulan validación de negocio
y no tienen identidad propia (se comparan por valor, no por ID).
"""

from .email import Email
from .horas_contrato import HorasContrato
from .turno import Turno, TurnoEnum
from .zona_preferida import ZonaPreferida

__all__ = [
    "Email",
    "HorasContrato",
    "Turno",
    "TurnoEnum",
    "ZonaPreferida",
]
