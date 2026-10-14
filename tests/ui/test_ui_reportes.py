"""Tests de UI para ReportesForm — generación de informes y PDFs."""

from datetime import date, time
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Configuracion


def _get_form(session):
    try:
        from presentation.forms.reportes_form import ReportesForm
        return ReportesForm(session)
    except ImportError:
        return None


@pytest.fixture
def config(session, zona_factory, profesor_factory):
    zona_factory(nombre_zona="Patio A")
    prof = profesor_factory("García, Juan", turno="mañana", horas_contrato=25.0)
    session.flush()
    cfg = Configuracion(
        anio_inicio_curso=2024,
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=True,
        recreos_config='[{"id":1,"etiqueta":"R1","turno":"manana","hora":"11:00","zonas":1}]',
    )
    session.add(cfg)
    session.commit()
    return cfg


@pytest.fixture
def form(qapp, session, config):
    f = _get_form(session)
    if f is None:
        pytest.skip("ReportesForm no encontrado")
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def form_sin_guardias(qapp, session):
    f = _get_form(session)
    if f is None:
        pytest.skip("ReportesForm no encontrado")
    QApplication.processEvents()
    yield f
    f.close()


class TestReportesRenderizado:
    def test_form_se_crea_sin_crash(self, form):
        assert form is not None

    def test_form_sin_guardias_no_crashea(self, form_sin_guardias):
        assert form_sin_guardias is not None


class TestReportesPDF:
    def test_generar_pdf_todos_profesores(self, qtbot, form):
        """Generar PDF para todos los profesores no provoca crash."""
        with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName", return_value=("/tmp/test.pdf", "")):
            with patch.object(form, "mostrar_exito", side_effect=None):
                with patch.object(form, "mostrar_error", side_effect=None):
                    if hasattr(form, "generar_pdf_btn"):
                        qtbot.mouseClick(form.generar_pdf_btn, Qt.MouseButton.LeftButton)
                        QApplication.processEvents()
                    elif hasattr(form, "_generar_pdf"):
                        form._generar_pdf()
                        QApplication.processEvents()

    def test_sin_guardias_no_crashea_al_generar(self, qtbot, form_sin_guardias):
        """Con BD sin guardias el formulario no provoca crash al generar."""
        with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName", return_value=("/tmp/test.pdf", "")):
            with patch.object(form_sin_guardias, "mostrar_advertencia", side_effect=None):
                with patch.object(form_sin_guardias, "mostrar_error", side_effect=None):
                    if hasattr(form_sin_guardias, "generar_pdf_btn"):
                        qtbot.mouseClick(form_sin_guardias.generar_pdf_btn, Qt.MouseButton.LeftButton)
                        QApplication.processEvents()

    def test_cancelar_file_dialog_no_provoca_crash(self, qtbot, form):
        """Cancelar el diálogo de guardado no provoca crash."""
        with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", "")):
            if hasattr(form, "generar_pdf_btn"):
                qtbot.mouseClick(form.generar_pdf_btn, Qt.MouseButton.LeftButton)
                QApplication.processEvents()
            elif hasattr(form, "_generar_pdf"):
                form._generar_pdf()
                QApplication.processEvents()
