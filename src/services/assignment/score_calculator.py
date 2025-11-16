"""
ScoreCalculator - Cálculo de puntuaciones

Responsabilidad: Calcular scores para seleccionar el mejor
profesor candidato para cada slot.
"""

from datetime import date
from typing import Dict, List, Set, Tuple

from models.models import Profesor
from services.assignment.slot_builder import Slot
from utils import get_logger

logger = get_logger(__name__)


class ScoreCalculator:
    """
    Calculador de puntuaciones para selección de profesores.

    Aplica múltiples criterios con pesos para determinar
    el mejor profesor para cada slot.
    """

    def __init__(self):
        # Pesos de cada criterio (ajustables)
        self.peso_equilibrio = 100.0
        self.peso_zona_preferida = 50.0
        self.peso_turno_preferido = 30.0
        self.peso_diversidad = 20.0

    def calcular_score(
        self,
        profesor: Profesor,
        slot: Slot,
        asignaciones_profesor: Dict[int, int],
        cuotas: Dict[int, int],
        guardias_en_fecha: Dict[Tuple[date, int], Set[int]],
        profesores: List[Profesor],
    ) -> float:
        """
        Calcula score total para un profesor en un slot.

        Args:
            profesor: Profesor candidato
            slot: Slot a asignar
            asignaciones_profesor: Guardias ya asignadas
            cuotas: Cuota objetivo por profesor
            guardias_en_fecha: Registro de asignaciones por fecha
            profesores: Lista completa de profesores (para contexto)

        Returns:
            Score total (mayor = mejor)
        """
        score = 0.0

        # Criterio 1: Equilibrio (priorizar quien va más atrasado)
        score += self._score_equilibrio(
            profesor, asignaciones_profesor, cuotas
        )

        # Criterio 2: Zona preferida
        score += self._score_zona_preferida(profesor, slot)

        # Criterio 3: Turno preferido
        score += self._score_turno_preferido(profesor, slot)

        # Criterio 4: Diversidad (evitar repetir mismo profesor)
        score += self._score_diversidad(
            profesor, slot, guardias_en_fecha
        )

        return score

    def _score_equilibrio(
        self,
        profesor: Profesor,
        asignaciones_profesor: Dict[int, int],
        cuotas: Dict[int, int],
    ) -> float:
        """
        Prioriza profesores que van más atrasados respecto a su cuota.

        Returns:
            Score: mayor si está más atrasado
        """
        asignadas = asignaciones_profesor.get(profesor.id, 0)
        cuota = cuotas.get(profesor.id, 1)

        if cuota == 0:
            return 0.0

        # Porcentaje completado de la cuota
        completado = asignadas / cuota

        # Score inverso: quien menos % tiene, más score
        score = self.peso_equilibrio * (1.0 - completado)

        return max(0.0, score)

    def _score_zona_preferida(self, profesor: Profesor, slot: Slot) -> float:
        """
        Bonifica si el slot está en la zona preferida del profesor.

        Returns:
            Score: peso completo si coincide, 0 si no
        """
        if not profesor.zona_preferida_id:
            return 0.0

        if profesor.zona_preferida_id == slot.zona_id:
            return self.peso_zona_preferida

        return 0.0

    def _score_turno_preferido(self, profesor: Profesor, slot: Slot) -> float:
        """
        Bonifica si el turno coincide con el del profesor.

        Returns:
            Score: mayor si coincide exactamente
        """
        if profesor.turno == slot.turno:
            return self.peso_turno_preferido

        # Profesores mixto/completo pueden ambos turnos pero sin bonificación
        return 0.0

    def _score_diversidad(
        self,
        profesor: Profesor,
        slot: Slot,
        guardias_en_fecha: Dict[Tuple[date, int], Set[int]],
    ) -> float:
        """
        Penaliza si el profesor ya tiene guardias recientes.

        Returns:
            Score: negativo si tiene guardias muy recientes
        """
        # Contar guardias en los últimos 3 días
        penalizacion = 0.0

        for dia_offset in range(1, 4):
            # TODO: Restar días para verificar guardias recientes
            # Por ahora, score neutro
            pass

        return penalizacion

    def seleccionar_mejor(
        self,
        candidatos: List[Profesor],
        slot: Slot,
        asignaciones_profesor: Dict[int, int],
        cuotas: Dict[int, int],
        guardias_en_fecha: Dict[Tuple[date, int], Set[int]],
        profesores: List[Profesor],
    ) -> Profesor:
        """
        Selecciona el mejor profesor de una lista de candidatos.

        Args:
            candidatos: Profesores elegibles
            slot: Slot a asignar
            asignaciones_profesor: Guardias asignadas
            cuotas: Cuotas objetivo
            guardias_en_fecha: Registro de asignaciones
            profesores: Lista completa (contexto)

        Returns:
            Mejor profesor según scoring
        """
        if not candidatos:
            raise ValueError("No hay candidatos para seleccionar")

        mejor_profesor = None
        mejor_score = -float("inf")

        for profesor in candidatos:
            score = self.calcular_score(
                profesor,
                slot,
                asignaciones_profesor,
                cuotas,
                guardias_en_fecha,
                profesores,
            )

            if score > mejor_score:
                mejor_score = score
                mejor_profesor = profesor

        if mejor_profesor is None:
            # Fallback: retornar primero
            return candidatos[0]

        return mejor_profesor
