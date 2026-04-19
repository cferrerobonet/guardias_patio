"""
Tests para módulos services/assignment/ con baja cobertura:
- slot_builder.py (28%)
- profesor_filter.py (20%)
- assignment_executor.py (25%)
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# SlotBuilder / Slot
# ===========================================================================


class TestSlot:
    def test_slot_crea_dataclass(self):
        from services.assignment.slot_builder import Slot

        s = Slot(fecha=date(2024, 9, 10), recreo_id=1, turno="mañana", zona_id=2)
        assert s.fecha == date(2024, 9, 10)
        assert s.turno == "mañana"

    def test_slot_turno_tarde(self):
        from services.assignment.slot_builder import Slot

        s = Slot(fecha=date(2024, 9, 11), recreo_id=2, turno="tarde", zona_id=3)
        assert s.zona_id == 3


class TestSlotBuilder:
    def test_constructor(self):
        from services.assignment.slot_builder import SlotBuilder

        session = MagicMock()
        sb = SlotBuilder(session)
        assert sb.session is session

    def test_count_slots_empty(self):
        from services.assignment.slot_builder import SlotBuilder

        sb = SlotBuilder(MagicMock())
        result = sb.count_slots_by_turno([])
        assert result == {"mañana": 0, "tarde": 0}

    def test_count_slots(self):
        from services.assignment.slot_builder import Slot, SlotBuilder

        sb = SlotBuilder(MagicMock())
        slots = [
            Slot(date(2024, 9, 10), 1, "mañana", 1),
            Slot(date(2024, 9, 10), 2, "tarde", 1),
            Slot(date(2024, 9, 11), 1, "mañana", 1),
        ]
        result = sb.count_slots_by_turno(slots)
        assert result["mañana"] == 2
        assert result["tarde"] == 1

    def test_filter_by_date_range(self):
        from services.assignment.slot_builder import Slot, SlotBuilder

        sb = SlotBuilder(MagicMock())
        slots = [
            Slot(date(2024, 9, 10), 1, "mañana", 1),
            Slot(date(2024, 9, 15), 1, "mañana", 1),
            Slot(date(2024, 9, 20), 1, "mañana", 1),
        ]
        result = sb.filter_slots_by_date_range(
            slots, date(2024, 9, 10), date(2024, 9, 15)
        )
        assert len(result) == 2

    def test_filter_by_date_range_empty(self):
        from services.assignment.slot_builder import SlotBuilder

        sb = SlotBuilder(MagicMock())
        result = sb.filter_slots_by_date_range(
            [], date(2024, 9, 10), date(2024, 9, 15)
        )
        assert result == []

    def test_build_slots_sin_dias_lectivos(self):
        from services.assignment.slot_builder import SlotBuilder

        session = MagicMock()
        sb = SlotBuilder(session)

        config = MagicMock()
        config.fecha_inicio = date(2024, 9, 1)
        config.fecha_fin = date(2024, 6, 30)
        config.dias_lectivos = "[]"
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = None

        with patch("services.assignment.slot_builder.listar_dias_lectivos", return_value=[]):
            result = sb.build_slots(config)
        assert result == []

    def test_build_slots_sin_recreos(self):
        from services.assignment.slot_builder import SlotBuilder

        session = MagicMock()
        sb = SlotBuilder(session)
        config = MagicMock()

        with (
            patch(
                "services.assignment.slot_builder.listar_dias_lectivos",
                return_value=[date(2024, 9, 10)],
            ),
            patch("services.assignment.slot_builder._parse_recreos_config", return_value=[]),
        ):
            result = sb.build_slots(config)
        assert result == []


# ===========================================================================
# ProfesorFilter
# ===========================================================================


class TestProfesorFilter:
    def _make_filter(self):
        from services.assignment.profesor_filter import ProfesorFilter

        session = MagicMock()
        with patch("services.assignment.profesor_filter.AusenciaChecker"), patch(
            "services.assignment.profesor_filter.TurnoValidator"
        ):
            pf = ProfesorFilter(session)
        return pf

    def test_constructor(self):
        pf = self._make_filter()
        assert pf.total_evaluaciones == 0

    def test_get_estadisticas_vacio(self):
        from services.assignment.profesor_filter import ProfesorFilter

        session = MagicMock()
        with patch("services.assignment.profesor_filter.AusenciaChecker"), patch(
            "services.assignment.profesor_filter.TurnoValidator"
        ):
            pf = ProfesorFilter(session)
        stats = pf.get_estadisticas()
        assert isinstance(stats, dict)

    def test_limpiar_cache(self):
        from services.assignment.profesor_filter import _limpiar_cache_elegibilidad

        _limpiar_cache_elegibilidad()  # No debe lanzar

    def test_obtener_profesores_elegibles_lista_vacia(self):
        from services.assignment.slot_builder import Slot

        pf = self._make_filter()
        slot = Slot(date(2024, 9, 10), 1, "mañana", 1)
        result = pf.obtener_profesores_elegibles([], slot, {}, {}, {})
        assert result == []


# ===========================================================================
# Use cases con baja cobertura
# ===========================================================================


class TestUseCaseLimpiarGuardias:
    def test_constructor(self):
        from application.use_cases.guardia.limpiar_guardias import LimpiarGuardiasUseCase

        repo = MagicMock()
        uc = LimpiarGuardiasUseCase(repo)
        assert uc is not None

    def test_execute(self):
        from application.use_cases.guardia.limpiar_guardias import LimpiarGuardiasUseCase

        repo = MagicMock()
        repo.delete_all.return_value = None
        uc = LimpiarGuardiasUseCase(repo)
        uc.execute()
        repo.delete_all.assert_called_once()


class TestUseCaseActualizarLogo:
    def test_constructor(self):
        from application.use_cases.perfil.actualizar_logo import ActualizarLogoUseCase

        repo = MagicMock()
        uc = ActualizarLogoUseCase(repo)
        assert uc is not None


class TestCursoEscolarEntity:
    def test_entity_str(self):
        from domain.entities.curso_escolar_entity import CursoEscolarEntity

        e = CursoEscolarEntity(id=1, nombre="2024-25", fecha_inicio=date(2024, 9, 1),
                               fecha_fin=date(2025, 6, 30), activo=True)
        assert e.id == 1
        assert e.activo is True
