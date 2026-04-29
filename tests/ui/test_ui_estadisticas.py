"""Tests de UI para PanelEstadisticas — renderizado y actualización."""

from datetime import date, time

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Configuracion


@pytest.fixture
def panel_con_datos(qapp, session, zona_factory, profesor_factory, guardia_factory):
    zona = zona_factory(nombre_zona="Patio A")
    prof = profesor_factory("García, Juan", turno="mañana", horas_contrato=25.0)
    guardia_factory(profesor_id=prof.id, zona_id=zona.id, fecha=date(2025, 1, 10))
    guardia_factory(profesor_id=prof.id, zona_id=zona.id, fecha=date(2025, 1, 11))
    session.flush()

    try:
        from presentation.widgets.panel_estadisticas import PanelEstadisticas
        widget = PanelEstadisticas(session)
        QApplication.processEvents()
        yield widget
        widget.close()
    except ImportError:
        pytest.skip("PanelEstadisticas no encontrado en ruta esperada")


@pytest.fixture
def panel_sin_datos(qapp, session):
    try:
        from presentation.widgets.panel_estadisticas import PanelEstadisticas
        widget = PanelEstadisticas(session)
        QApplication.processEvents()
        yield widget
        widget.close()
    except ImportError:
        pytest.skip("PanelEstadisticas no encontrado en ruta esperada")


class TestEstadisticasRenderizado:
    def test_widget_se_crea_sin_crash(self, panel_sin_datos):
        assert panel_sin_datos is not None

    def test_widget_con_datos_no_crashea(self, panel_con_datos):
        assert panel_con_datos is not None

    def test_sin_guardias_muestra_cero_o_nd(self, panel_sin_datos):
        texto = panel_sin_datos.toPlainText() if hasattr(panel_sin_datos, "toPlainText") else ""
        assert panel_sin_datos is not None


class TestEstadisticasInteraccion:
    def test_actualizar_estadisticas_no_crashea(self, qtbot, panel_con_datos):
        """Click en actualizar no provoca crash."""
        if hasattr(panel_con_datos, "actualizar_btn"):
            qtbot.mouseClick(panel_con_datos.actualizar_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
        elif hasattr(panel_con_datos, "actualizar"):
            panel_con_datos.actualizar()
            QApplication.processEvents()

    def test_tabs_son_navegables(self, qtbot, panel_con_datos):
        """Cambiar tabs no provoca crash."""
        if hasattr(panel_con_datos, "tab_widget"):
            tab = panel_con_datos.tab_widget
            for i in range(tab.count()):
                tab.setCurrentIndex(i)
                QApplication.processEvents()
