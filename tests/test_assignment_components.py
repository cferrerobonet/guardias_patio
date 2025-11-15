"""
Tests básicos para los componentes de assignment

Verifica que las clases se instancian correctamente.
"""

from datetime import date
from unittest.mock import Mock

import pytest
from services.assignment import (
    AssignmentExecutor,
    ProfesorFilter,
    ScoreCalculator,
    Slot,
    SlotBuilder,
)


class TestSlotBuilder:
    """Tests para SlotBuilder."""

    def test_slot_creation(self):
        """Verifica que se puede crear un Slot."""
        slot = Slot(
            fecha=date(2025, 1, 15),
            recreo_id=1,
            turno="mañana",
            zona_id=1,
        )
        assert slot.fecha == date(2025, 1, 15)
        assert slot.recreo_id == 1
        assert slot.turno == "mañana"
        assert slot.zona_id == 1

    def test_slot_builder_instantiation(self):
        """Verifica que SlotBuilder se instancia correctamente."""
        session_mock = Mock()
        builder = SlotBuilder(session_mock)
        assert builder.session == session_mock


class TestProfesorFilter:
    """Tests para ProfesorFilter."""

    def test_filter_instantiation(self):
        """Verifica que ProfesorFilter se instancia correctamente."""
        session_mock = Mock()
        filter_obj = ProfesorFilter(session_mock)
        assert filter_obj.session == session_mock
        assert filter_obj.ausencia_checker is not None
        assert filter_obj.turno_validator is not None


class TestScoreCalculator:
    """Tests para ScoreCalculator."""

    def test_calculator_instantiation(self):
        """Verifica que ScoreCalculator se instancia correctamente."""
        calculator = ScoreCalculator()
        assert calculator.peso_equilibrio > 0
        assert calculator.peso_zona_preferida > 0

    def test_score_equilibrio_basico(self):
        """Verifica cálculo básico de score de equilibrio."""
        calculator = ScoreCalculator()
        profesor_mock = Mock()
        profesor_mock.id = 1

        asignaciones = {1: 0}  # Profesor sin guardias
        cuotas = {1: 10}  # Cuota de 10

        score = calculator._score_equilibrio(profesor_mock, asignaciones, cuotas)
        # Profesor sin guardias debe tener score alto
        assert score > 50


class TestAssignmentExecutor:
    """Tests para AssignmentExecutor."""

    def test_executor_instantiation(self):
        """Verifica que AssignmentExecutor se instancia correctamente."""
        session_mock = Mock()
        executor = AssignmentExecutor(session_mock)
        assert executor.session == session_mock
        assert executor.slot_builder is not None
        assert executor.profesor_filter is not None
        assert executor.score_calculator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
