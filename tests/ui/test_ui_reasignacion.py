"""Tests de UI para DialogoReasignacion — reasignación manual y automática."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import CursoEscolar, Guardia
from presentation.widgets.dialogo_reasignacion import DialogoReasignacion

from tests.ui.helpers import select_row


def _guardia_mock(id_, profesor_nombre, zona_nombre):
    g = MagicMock()
    g.id = id_
    g.fecha = date(2025, 3, 10)
    g.turno = "mañana"
    g.recreo = 1
    g.profesor_id = id_
    g.profesor.nombre_completo = profesor_nombre
    g.zona.nombre_zona = zona_nombre
    return g


@pytest.fixture
def guardias_mock():
    return [
        _guardia_mock(1, "García, Juan", "Patio A"),
        _guardia_mock(2, "López, Ana", "Patio B"),
    ]


@pytest.fixture
def dialogo(qapp, session, guardias_mock):
    d = DialogoReasignacion(guardias=guardias_mock, ausencia_id=1, session=session)
    QApplication.processEvents()
    yield d
    d.close()


@pytest.fixture
def dialogo_vacio(qapp, session):
    d = DialogoReasignacion(guardias=[], ausencia_id=1, session=session)
    QApplication.processEvents()
    yield d
    d.close()


class TestReasignacionRenderizado:
    def test_dialogo_se_crea_sin_crash(self, dialogo):
        assert dialogo is not None

    def test_tabla_muestra_guardias(self, dialogo, guardias_mock):
        assert dialogo.tabla.rowCount() == len(guardias_mock)

    def test_tabla_vacia_no_crashea(self, dialogo_vacio):
        assert dialogo_vacio.tabla.rowCount() == 0

    def test_titulo_incluye_conteo(self, dialogo, guardias_mock):
        found = any(
            str(len(guardias_mock)) in w.text()
            for w in dialogo.findChildren(__import__("PyQt6.QtWidgets", fromlist=["QLabel"]).QLabel)
        )
        assert found

    def test_columnas_tabla(self, dialogo):
        assert dialogo.tabla.columnCount() == 6


class TestReasignacionManual:
    def test_reasignar_manual_sin_seleccion_muestra_warning(self, qtbot, dialogo):
        """Reasignar manual sin fila seleccionada muestra QMessageBox.warning."""
        dialogo.tabla.clearSelection()
        QApplication.processEvents()
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialogo.reasignar_manual()
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_reasignar_manual_sin_disponibles_muestra_warning(self, qtbot, dialogo):
        """Sin profesores disponibles, muestra aviso."""
        select_row(dialogo.tabla, 0)
        QApplication.processEvents()
        with patch(
            "services.gestor_ausencias.GestorAusencias.obtener_profesores_disponibles",
            return_value=[],
        ):
            with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
                dialogo.reasignar_manual()
                QApplication.processEvents()
                mock_warn.assert_called_once()


class TestReasignacionAutomatica:
    def test_reasignar_auto_cancelado_no_modifica(self, qtbot, dialogo, session):
        """Cancelar confirmación no llama a GestorAusencias."""
        with patch(
            "PyQt6.QtWidgets.QMessageBox.question",
            return_value=__import__("PyQt6.QtWidgets", fromlist=["QMessageBox"]).QMessageBox.StandardButton.No,
        ):
            with patch(
                "services.gestor_ausencias.GestorAusencias.reasignar_guardias_automaticamente"
            ) as mock_reasignar:
                dialogo.reasignar_automaticamente()
                QApplication.processEvents()
                mock_reasignar.assert_not_called()

    def test_reasignar_auto_confirmado_llama_servicio(self, qtbot, dialogo):
        """Confirmar reasignación automática llama al servicio."""
        mock_resultado = {"reasignadas": 2, "fallidas": 0}
        with patch(
            "PyQt6.QtWidgets.QMessageBox.question",
            return_value=__import__("PyQt6.QtWidgets", fromlist=["QMessageBox"]).QMessageBox.StandardButton.Yes,
        ):
            with patch(
                "services.gestor_ausencias.GestorAusencias.reasignar_guardias_automaticamente",
                return_value=mock_resultado,
            ) as mock_reasignar:
                dialogo.reasignar_automaticamente()
                QApplication.processEvents()
                mock_reasignar.assert_called_once()
