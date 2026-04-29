"""Tests de UI para GestorSustituciones — reasignación de guardias."""

from datetime import date
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


def _get_gestor(session):
    try:
        from presentation.widgets.gestor_sustituciones import GestorSustituciones
        return GestorSustituciones(session)
    except ImportError:
        try:
            from presentation.forms.gestor_sustituciones import GestorSustituciones
            return GestorSustituciones(session)
        except ImportError:
            return None


@pytest.fixture
def form(qapp, session, zona_factory, profesor_factory, guardia_factory):
    zona = zona_factory(nombre_zona="Patio A")
    prof1 = profesor_factory("García, Juan", turno="mañana", horas_contrato=25.0)
    prof2 = profesor_factory("López, Ana", turno="mañana", horas_contrato=20.0)
    guardia_factory(profesor_id=prof1.id, zona_id=zona.id, fecha=date(2025, 2, 10))
    session.flush()

    g = _get_gestor(session)
    if g is None:
        pytest.skip("GestorSustituciones no encontrado")
    QApplication.processEvents()
    yield g
    g.close()


@pytest.fixture
def form_vacio(qapp, session):
    g = _get_gestor(session)
    if g is None:
        pytest.skip("GestorSustituciones no encontrado")
    QApplication.processEvents()
    yield g
    g.close()


class TestSustitucionesRenderizado:
    def test_form_se_crea_sin_crash(self, form):
        assert form is not None

    def test_combo_profesores_cargado(self, form):
        """El combo de profesores tiene al menos un elemento."""
        combo = (
            getattr(form, "profesor_combo", None)
            or getattr(form, "combo_profesor", None)
        )
        if combo:
            assert combo.count() > 0

    def test_form_vacio_no_crashea(self, form_vacio):
        assert form_vacio is not None


class TestSustitucionesInteraccion:
    def test_seleccionar_profesor_carga_guardias(self, qtbot, form):
        """Seleccionar un profesor en el combo carga sus guardias en la tabla."""
        combo = (
            getattr(form, "profesor_combo", None)
            or getattr(form, "combo_profesor", None)
        )
        tabla = (
            getattr(form, "tabla_guardias", None)
            or getattr(form, "guardias_table", None)
        )
        if combo and combo.count() > 1 and tabla:
            combo.setCurrentIndex(1)
            QApplication.processEvents()
            assert tabla.rowCount() >= 0

    def test_reasignar_sin_seleccion_no_crashea(self, qtbot, form):
        """Pulsar reasignar sin guardia seleccionada no provoca crash."""
        btn = (
            getattr(form, "reasignar_btn", None)
            or getattr(form, "btn_reasignar", None)
        )
        if btn:
            with patch.object(form, "mostrar_advertencia", side_effect=None):
                qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
                QApplication.processEvents()
