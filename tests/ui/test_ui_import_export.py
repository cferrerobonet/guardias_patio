"""Tests de UI para ImportExportForm — importación y exportación de datos."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Profesor


def _get_form(session):
    try:
        from presentation.forms.import_export_form import ImportExportForm
        return ImportExportForm(session)
    except ImportError:
        try:
            from presentation.forms.importar_exportar_form import ImportarExportarForm
            return ImportarExportarForm(session)
        except ImportError:
            return None


@pytest.fixture
def form(qapp, session, profesor_factory):
    profesor_factory("García, Juan", turno="mañana", horas_contrato=25.0)
    session.flush()
    f = _get_form(session)
    if f is None:
        pytest.skip("ImportExportForm no encontrado")
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def valid_json_file(session, profesor_factory):
    """Fichero JSON temporal con datos válidos exportables."""
    prof = profesor_factory("Exportado, Test", turno="mañana", horas_contrato=20.0)
    session.flush()

    data = {
        "profesores": [
            {
                "nombre_completo": "Importado, Profesor",
                "horas_contrato": 25.0,
                "turno": "mañana",
                "tutor": False,
                "porcentaje_jornada": 100.0,
            }
        ]
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f)
        return f.name


class TestImportExportRenderizado:
    def test_form_se_crea_sin_crash(self, form):
        assert form is not None


class TestExportacion:
    def test_exportar_json_no_crashea(self, qtbot, form):
        """Exportar JSON a fichero temporal no provoca crash."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName", return_value=(tmp_path, "")):
                with patch.object(form, "mostrar_exito", side_effect=None):
                    with patch.object(form, "mostrar_error", side_effect=None):
                        if hasattr(form, "exportar_json_btn"):
                            qtbot.mouseClick(form.exportar_json_btn, Qt.MouseButton.LeftButton)
                            QApplication.processEvents()
                        elif hasattr(form, "exportar_json"):
                            form.exportar_json()
                            QApplication.processEvents()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_cancelar_exportar_no_crashea(self, qtbot, form):
        """Cancelar diálogo de exportación no provoca crash."""
        with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")):
            if hasattr(form, "exportar_json_btn"):
                qtbot.mouseClick(form.exportar_json_btn, Qt.MouseButton.LeftButton)
                QApplication.processEvents()
            elif hasattr(form, "exportar_json"):
                form.exportar_json()
                QApplication.processEvents()


class TestImportacion:
    def test_importar_json_valido(self, qtbot, form, valid_json_file, session):
        """Importar JSON válido carga datos sin crash."""
        try:
            with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName", return_value=(valid_json_file, "")):
                with patch.object(form, "mostrar_exito", side_effect=None):
                    with patch.object(form, "mostrar_error", side_effect=None):
                        if hasattr(form, "importar_json_btn"):
                            qtbot.mouseClick(form.importar_json_btn, Qt.MouseButton.LeftButton)
                            QApplication.processEvents()
                        elif hasattr(form, "importar_json"):
                            form.importar_json()
                            QApplication.processEvents()
        finally:
            if os.path.exists(valid_json_file):
                os.unlink(valid_json_file)

    def test_cancelar_importar_no_crashea(self, qtbot, form):
        """Cancelar diálogo de importación no provoca crash."""
        with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName", return_value=("", "")):
            if hasattr(form, "importar_json_btn"):
                qtbot.mouseClick(form.importar_json_btn, Qt.MouseButton.LeftButton)
                QApplication.processEvents()
            elif hasattr(form, "importar_json"):
                form.importar_json()
                QApplication.processEvents()

    def test_importar_json_malformado_no_crashea(self, qtbot, form):
        """Importar JSON roto no provoca crash — solo muestra error."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write("{ esto no es json valido }")
            tmp_path = tmp.name

        try:
            with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName", return_value=(tmp_path, "")):
                with patch.object(form, "mostrar_error", side_effect=None):
                    with patch.object(form, "mostrar_advertencia", side_effect=None):
                        if hasattr(form, "importar_json_btn"):
                            qtbot.mouseClick(form.importar_json_btn, Qt.MouseButton.LeftButton)
                            QApplication.processEvents()
                        elif hasattr(form, "importar_json"):
                            form.importar_json()
                            QApplication.processEvents()
        finally:
            os.unlink(tmp_path)
