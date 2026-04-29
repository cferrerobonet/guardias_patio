"""Tests de UI para FestivosWidget — configuración de festivos y días no lectivos."""

import pytest
from PyQt6.QtWidgets import QApplication

from presentation.forms.config_widgets.festivos_widget import FestivosWidget


@pytest.fixture
def widget(qapp):
    w = FestivosWidget()
    w.show()
    QApplication.processEvents()
    yield w
    w.close()


class TestFestivosRenderizado:
    def test_widget_se_crea_sin_crash(self, widget):
        assert widget is not None

    def test_inputs_existen(self, widget):
        assert hasattr(widget, "festivos_auto_input")
        assert hasattr(widget, "no_lectivos_input")

    def test_estado_inicial_vacio(self, widget):
        assert widget.festivos_auto_input.text() == ""
        assert widget.no_lectivos_input.text() == ""


class TestFestivosGetSet:
    def test_set_activar_true_muestra_1(self, widget):
        widget.set_festivos_config(activar_automaticos=True, dias_no_lectivos="")
        assert widget.festivos_auto_input.text() == "1"

    def test_set_activar_false_muestra_0(self, widget):
        widget.set_festivos_config(activar_automaticos=False, dias_no_lectivos="")
        assert widget.festivos_auto_input.text() == "0"

    def test_set_dias_no_lectivos(self, widget):
        widget.set_festivos_config(activar_automaticos=True, dias_no_lectivos="2025-10-09, 2025-12-08")
        assert widget.no_lectivos_input.text() == "2025-10-09, 2025-12-08"

    def test_get_config_activo(self, widget):
        widget.set_festivos_config(activar_automaticos=True, dias_no_lectivos="2025-10-09")
        cfg = widget.get_festivos_config()
        assert cfg["activar_automaticos"] is True
        assert cfg["dias_no_lectivos"] == "2025-10-09"

    def test_get_config_inactivo(self, widget):
        widget.set_festivos_config(activar_automaticos=False, dias_no_lectivos="")
        cfg = widget.get_festivos_config()
        assert cfg["activar_automaticos"] is False

    def test_get_config_vacio_usa_default_activo(self, widget):
        """Input vacío se interpreta como activado (default=1)."""
        widget.festivos_auto_input.setText("")
        cfg = widget.get_festivos_config()
        assert cfg["activar_automaticos"] is True


class TestFestivosValidacion:
    def test_validacion_ok_con_fechas_correctas(self, widget):
        widget.set_festivos_config(activar_automaticos=True, dias_no_lectivos="2025-10-09, 2025-12-08")
        ok, msg = widget.validar()
        assert ok is True
        assert msg == ""

    def test_validacion_ok_sin_dias_no_lectivos(self, widget):
        widget.set_festivos_config(activar_automaticos=True, dias_no_lectivos="")
        ok, _ = widget.validar()
        assert ok is True

    def test_validacion_falla_festivos_auto_invalido(self, widget):
        widget.festivos_auto_input.setText("si")
        ok, msg = widget.validar()
        assert ok is False
        assert msg != ""

    def test_validacion_falla_fecha_formato_incorrecto(self, widget):
        widget.set_festivos_config(activar_automaticos=True, dias_no_lectivos="09/10/2025")
        ok, msg = widget.validar()
        assert ok is False

    def test_validacion_falla_fecha_inexistente(self, widget):
        widget.set_festivos_config(activar_automaticos=True, dias_no_lectivos="2025-13-45")
        ok, msg = widget.validar()
        assert ok is False

    def test_signal_config_changed_emitido(self, widget, qtbot):
        """Modificar festivos_auto_input emite config_changed."""
        with qtbot.waitSignal(widget.config_changed, timeout=1000):
            widget.festivos_auto_input.setText("0")
