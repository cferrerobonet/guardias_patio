"""Tests de validación de borde en formularios UI."""

from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.zona_form import ZonaForm


@pytest.fixture
def profesor_form(qapp, session):
    f = ProfesorForm(session)
    f.show()
    QApplication.processEvents()
    f._abrir_formulario_nuevo()
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def zona_form(qapp, session):
    f = ZonaForm(session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


class TestValidacionesProfesor:
    def test_nombre_demasiado_corto_muestra_advertencia(self, qtbot, profesor_form):
        """Nombre de 2 caracteres rechazado por validación."""
        profesor_form.datos_basicos_widget.nombre_completo_input.setText("AB")
        profesor_form.horario_widget.horas_input.setText("25")
        QApplication.processEvents()

        with patch.object(profesor_form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(profesor_form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_email_malformado_muestra_advertencia(self, qtbot, profesor_form):
        """Email sin @ rechazado por validación."""
        profesor_form.datos_basicos_widget.nombre_completo_input.setText("APELLIDO, Nombre")
        profesor_form.datos_basicos_widget.email_input.setText("sinArrobaEjemplo")
        profesor_form.horario_widget.horas_input.setText("25")
        QApplication.processEvents()

        with patch.object(profesor_form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(profesor_form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_horas_cero_muestra_advertencia(self, qtbot, profesor_form):
        """Horas de contrato = 0 rechazado."""
        profesor_form.datos_basicos_widget.nombre_completo_input.setText("APELLIDO, Nombre")
        profesor_form.horario_widget.horas_input.setText("0")
        QApplication.processEvents()

        with patch.object(profesor_form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(profesor_form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_horas_excesivas_muestra_advertencia(self, qtbot, profesor_form):
        """Horas de contrato > 40 rechazado."""
        profesor_form.datos_basicos_widget.nombre_completo_input.setText("APELLIDO, Nombre")
        profesor_form.horario_widget.horas_input.setText("41")
        QApplication.processEvents()

        with patch.object(profesor_form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(profesor_form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_nombre_sin_coma_muestra_advertencia(self, qtbot, profesor_form):
        """Nombre sin formato 'APELLIDOS, NOMBRE' rechazado."""
        profesor_form.datos_basicos_widget.nombre_completo_input.setText("SinFormatoNombre")
        profesor_form.horario_widget.horas_input.setText("25")
        QApplication.processEvents()

        with patch.object(profesor_form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(profesor_form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()


class TestValidacionesZona:
    def test_zona_nombre_vacio_muestra_advertencia(self, qtbot, zona_form):
        """Nombre de zona vacío rechazado."""
        zona_form.nombre_zona_input.clear()
        QApplication.processEvents()

        with patch.object(zona_form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(zona_form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()


class TestValidacionesWidgetRestricciones:
    def test_restricciones_widget_rechaza_checkbox_activo_sin_seleccion(self, qtbot, profesor_form):
        """Activar restricciones sin marcar ningún recreo debe ser rechazado."""
        profesor_form.datos_basicos_widget.nombre_completo_input.setText("APELLIDO, Nombre")
        profesor_form.horario_widget.horas_input.setText("25")
        profesor_form.restricciones_widget.usar_restricciones_checkbox.setChecked(True)
        QApplication.processEvents()

        for (dia, recreo), btn in profesor_form.restricciones_widget.semana_widget._celdas.items():
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)
        profesor_form.restricciones_widget.restricciones_dias.clear()
        QApplication.processEvents()

        with patch.object(profesor_form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(profesor_form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()
