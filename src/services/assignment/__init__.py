"""
Assignment Package - Componentes de asignación de guardias

Este paquete contiene las clases especializadas para la asignación
de guardias, siguiendo el principio de Single Responsibility:

- SlotBuilder: Construcción de slots
- ProfesorFilter: Filtrado de profesores elegibles
- ScoreCalculator: Cálculo de puntuaciones
- AssignmentExecutor: Orquestación del proceso completo
"""

from services.assignment.assignment_executor import AssignmentExecutor
from services.assignment.profesor_filter import ProfesorFilter
from services.assignment.score_calculator import ScoreCalculator
from services.assignment.slot_builder import Slot, SlotBuilder

__all__ = [
    "Slot",
    "SlotBuilder",
    "ProfesorFilter",
    "ScoreCalculator",
    "AssignmentExecutor",
]
