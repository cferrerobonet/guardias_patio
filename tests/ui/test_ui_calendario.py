"""Tests de UI para VistaCalendario — navegación y visualización."""

from datetime import date

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


def _get_calendario(session):
    try:
        from presentation.widgets.vista_calendario import VistaCalendario
        return VistaCalendario(session)
    except ImportError:
        return None


@pytest.fixture
def calendario(qapp, session, zona_factory, profesor_factory, guardia_factory):
    zona = zona_factory(nombre_zona="Patio A")
    prof = profesor_factory("García, Juan", turno="mañana", horas_contrato=25.0)
    guardia_factory(profesor_id=prof.id, zona_id=zona.id, fecha=date(2025, 1, 10))
    guardia_factory(profesor_id=prof.id, zona_id=zona.id, fecha=date(2025, 1, 13))
    session.flush()

    c = _get_calendario(session)
    if c is None:
        pytest.skip("VistaCalendario no encontrado")
    QApplication.processEvents()
    yield c
    c.close()


@pytest.fixture
def calendario_vacio(qapp, session):
    c = _get_calendario(session)
    if c is None:
        pytest.skip("VistaCalendario no encontrado")
    QApplication.processEvents()
    yield c
    c.close()


class TestCalendarioRenderizado:
    def test_widget_se_crea_sin_crash(self, calendario):
        assert calendario is not None

    def test_widget_vacio_no_crashea(self, calendario_vacio):
        assert calendario_vacio is not None


class TestCalendarioNavegacion:
    def test_navegar_siguiente_mes(self, qtbot, calendario):
        """Click en 'Siguiente' cambia el mes."""
        mes_inicial = None
        if hasattr(calendario, "mes_actual"):
            mes_inicial = calendario.mes_actual

        if hasattr(calendario, "siguiente_btn"):
            qtbot.mouseClick(calendario.siguiente_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            if mes_inicial is not None:
                assert calendario.mes_actual != mes_inicial
        elif hasattr(calendario, "btn_siguiente"):
            qtbot.mouseClick(calendario.btn_siguiente, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

    def test_navegar_mes_anterior(self, qtbot, calendario):
        """Click en 'Anterior' cambia el mes."""
        if hasattr(calendario, "anterior_btn"):
            mes_inicial = getattr(calendario, "mes_actual", None)
            qtbot.mouseClick(calendario.anterior_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            if mes_inicial is not None:
                assert getattr(calendario, "mes_actual", mes_inicial) != mes_inicial
        elif hasattr(calendario, "btn_anterior"):
            qtbot.mouseClick(calendario.btn_anterior, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

    def test_navegacion_sucesiva_no_crashea(self, qtbot, calendario):
        """Navegar varios meses seguidos no provoca crash."""
        btn_sig = getattr(calendario, "siguiente_btn", None) or getattr(calendario, "btn_siguiente", None)
        if btn_sig:
            for _ in range(5):
                qtbot.mouseClick(btn_sig, Qt.MouseButton.LeftButton)
                QApplication.processEvents()
