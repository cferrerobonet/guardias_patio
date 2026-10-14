"""
Validadores de negocio - Fase 1 Quick Wins.

Este paquete contiene validadores centralizados para reducir duplicación de código.
"""

from .ausencia_checker import AusenciaChecker
from .turno_validator import TurnoValidator

__all__ = ["TurnoValidator", "AusenciaChecker"]
