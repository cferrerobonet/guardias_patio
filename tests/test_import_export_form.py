"""
Tests para ImportExportForm.

Cobertura actual: 11.19%
Objetivo: >70%
"""

import json
import os
import tempfile
from datetime import date, time
from unittest.mock import patch

import pytest
from infrastructure.database.models import Configuracion, Guardia
from presentation.forms.import_export_form import ImportExportForm
from PyQt6.QtWidgets import QCheckBox, QComboBox, QMessageBox, QPushButton, QTextEdit


@pytest.fixture
def datos_completos(session, profesor_factory, zona_factory):
    """Fixture con datos completos para exportar."""
    # Crear profesores
    prof1 = profesor_factory(nombre_completo="PÉREZ, Juan")
    prof2 = profesor_factory(nombre_completo="GARCÍA, Ana")

    # Crear zonas
    zona1 = zona_factory(nombre_zona="Patio A")
    zona2 = zona_factory(nombre_zona="Patio B")

    # Crear configuración
    config = Configuracion(
        anio_inicio_curso=2024,
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(11, 30),
        activar_festivos_automaticos=True,
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
    )
    session.add(config)
    session.commit()

    # Crear guardias
    guardia1 = Guardia(
        profesor_id=prof1.id, fecha=date(2024, 9, 2), turno="mañana", recreo=1, zona_id=zona1.id
    )
    guardia2 = Guardia(
        profesor_id=prof2.id, fecha=date(2024, 9, 2), turno="tarde", recreo=1, zona_id=zona2.id
    )
    session.add_all([guardia1, guardia2])
    session.commit()

    return {
        "profesores": [prof1, prof2],
        "zonas": [zona1, zona2],
        "config": config,
        "guardias": [guardia1, guardia2],
    }


@pytest.mark.ui
class TestImportExportFormBasico:
    """Tests básicos de ImportExportForm."""

    def test_crear_formulario(self, qtbot, session):
        """Test: Se puede crear el formulario de import/export."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert form is not None
        assert "Importar / Exportar" in form.windowTitle() or form.findChild(QTextEdit)

    def test_botones_presentes(self, qtbot, session):
        """Test: Los botones principales están presentes."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert form.exportar_btn is not None
        assert form.importar_btn is not None
        # exportar_pdf_btn no existe en la implementación actual
        # La funcionalidad PDF está en CalendariosPdfWidget
        assert isinstance(form.exportar_btn, QPushButton)
        assert isinstance(form.importar_btn, QPushButton)

    def test_resultado_text_presente(self, qtbot, session):
        """Test: El área de texto para resultados está presente."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert form.resultado_text is not None
        assert isinstance(form.resultado_text, QTextEdit)
        assert form.resultado_text.isReadOnly()

    def test_checkbox_limpiar_presente(self, qtbot, session):
        """Test: El checkbox para limpiar datos está presente."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert form.limpiar_checkbox is not None
        assert isinstance(form.limpiar_checkbox, QCheckBox)
        # Debe estar checked por defecto (recomendado)
        assert form.limpiar_checkbox.isChecked()


@pytest.mark.ui
@pytest.mark.skip(reason="La funcionalidad PDF no está implementada en ImportExportForm actual")
class TestImportExportFormPDF:
    """Tests para la sección de exportación a PDF.

    NOTA: Estos tests están deshabilitados porque la funcionalidad PDF
    se movió a CalendariosPdfWidget y no está en ImportExportForm.
    """

    def test_combo_mes_presente(self, qtbot, session):
        """Test: El combo de mes está presente."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert form.pdf_mes_combo is not None
        assert isinstance(form.pdf_mes_combo, QComboBox)
        # Debe tener 12 meses
        assert form.pdf_mes_combo.count() == 12

    def test_combo_anio_presente(self, qtbot, session):
        """Test: El combo de año está presente."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert form.pdf_anio_combo is not None
        assert isinstance(form.pdf_anio_combo, QComboBox)
        # Debe tener al menos 4 años
        assert form.pdf_anio_combo.count() >= 4

    def test_combo_mes_valores_correctos(self, qtbot, session):
        """Test: El combo de mes tiene los meses correctos."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        meses_esperados = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]

        for i, mes in enumerate(meses_esperados):
            assert form.pdf_mes_combo.itemText(i) == mes

    def test_mes_actual_seleccionado_por_defecto(self, qtbot, session):
        """Test: El mes actual está seleccionado por defecto."""
        from datetime import datetime

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        mes_actual = datetime.now().month - 1  # 0-indexed
        assert form.pdf_mes_combo.currentIndex() == mes_actual


@pytest.mark.ui
class TestImportExportFormExportar:
    """Tests para la funcionalidad de exportación."""

    @patch("presentation.forms.import_export_form.QFileDialog.getSaveFileName")
    @patch("presentation.forms.import_export_form.ExportadorDatos.exportar_todo")
    def test_exportar_datos_exitoso(
        self, mock_exportar, mock_file_dialog, qtbot, session, datos_completos
    ):
        """Test: Exportar datos funciona correctamente."""
        # Configurar mocks
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        temp_file.close()

        mock_file_dialog.return_value = (temp_file.name, "JSON Files (*.json)")
        mock_exportar.return_value = None

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        # Ejecutar exportación
        form.exportar_datos()

        # Verificar que se llamó al exportador
        mock_exportar.assert_called_once()
        assert "exportado" in form.resultado_text.toPlainText().lower()

        # Limpiar
        os.unlink(temp_file.name)

    @patch("presentation.forms.import_export_form.QFileDialog.getSaveFileName")
    def test_exportar_datos_cancelado(self, mock_file_dialog, qtbot, session):
        """Test: Cancelar exportación no hace nada."""
        mock_file_dialog.return_value = ("", "")  # Usuario canceló

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        form.exportar_datos()

        # No debe haber texto de resultado si se canceló
        texto = form.resultado_text.toPlainText()
        assert texto == "" or "cancelado" in texto.lower()

    @patch("presentation.forms.import_export_form.QFileDialog.getSaveFileName")
    @patch("presentation.forms.import_export_form.ExportadorDatos.exportar_todo")
    def test_exportar_datos_error(self, mock_exportar, mock_file_dialog, qtbot, session):
        """Test: Manejo de errores en exportación."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        temp_file.close()

        mock_file_dialog.return_value = (temp_file.name, "JSON Files (*.json)")
        mock_exportar.side_effect = Exception("Error de prueba")

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        form.exportar_datos()

        # Debe mostrar error
        texto = form.resultado_text.toPlainText().lower()
        assert "error" in texto

        # Limpiar
        os.unlink(temp_file.name)


@pytest.mark.ui
class TestImportExportFormImportar:
    """Tests para la funcionalidad de importación."""

    @patch("presentation.forms.import_export_form.QFileDialog.getOpenFileName")
    @patch("presentation.forms.import_export_form.ExportadorDatos.importar_todo")
    @patch("presentation.forms.import_export_form.QMessageBox.question")
    @patch("presentation.forms.import_export_form.QMessageBox.information")
    def test_importar_datos_exitoso(
        self,
        mock_info,
        mock_question,
        mock_importar,
        mock_file_dialog,
        qtbot,
        session,
        datos_completos,
    ):
        """Test: Importar datos funciona correctamente."""
        # Crear archivo temporal con datos JSON
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump({"profesores": [], "zonas": [], "guardias": []}, temp_file)
        temp_file.close()

        # Configurar mocks
        mock_file_dialog.return_value = (temp_file.name, "JSON Files (*.json)")
        mock_question.return_value = QMessageBox.StandardButton.Yes
        mock_importar.return_value = {
            "profesores": 2,
            "zonas": 2,
            "configuracion": 1,
            "guardias": 2,
        }

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        # Ejecutar importación
        form.importar_datos()

        # Verificar que se llamó al importador
        mock_importar.assert_called_once()
        assert "importado" in form.resultado_text.toPlainText().lower()

        # Limpiar
        os.unlink(temp_file.name)

    @patch("presentation.forms.import_export_form.QFileDialog.getOpenFileName")
    def test_importar_datos_cancelado(self, mock_file_dialog, qtbot, session):
        """Test: Cancelar importación no hace nada."""
        mock_file_dialog.return_value = ("", "")  # Usuario canceló

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        form.importar_datos()

        # No debe haber texto de resultado si se canceló
        texto = form.resultado_text.toPlainText()
        assert texto == "" or "cancelado" in texto.lower()

    @patch("presentation.forms.import_export_form.QFileDialog.getOpenFileName")
    @patch("presentation.forms.import_export_form.QMessageBox.question")
    def test_importar_datos_confirmacion_rechazada(
        self, mock_question, mock_file_dialog, qtbot, session
    ):
        """Test: Rechazar confirmación cancela la importación."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        temp_file.close()

        mock_file_dialog.return_value = (temp_file.name, "JSON Files (*.json)")
        mock_question.return_value = QMessageBox.StandardButton.No  # Usuario rechaza

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        form.importar_datos()

        # No debe haber mensaje de éxito
        texto = form.resultado_text.toPlainText().lower()
        assert "importado correctamente" not in texto

        # Limpiar
        os.unlink(temp_file.name)


@pytest.mark.ui
@pytest.mark.skip(reason="La funcionalidad exportar_pdfs no está en ImportExportForm")
class TestImportExportFormPDFExport:
    """Tests para la exportación a PDF.

    NOTA: Estos tests están deshabilitados porque la funcionalidad PDF
    se movió a CalendariosPdfWidget y no está en ImportExportForm.
    """

    @patch("presentation.forms.import_export_form.QFileDialog.getExistingDirectory")
    @patch("presentation.forms.import_export_form.ExportadorPDF.exportar_todos_los_profesores")
    def test_exportar_pdfs_exitoso(
        self, mock_exportar_todos, mock_dir_dialog, qtbot, session, datos_completos
    ):
        """Test: Exportar PDFs funciona correctamente."""
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()

        # Configurar mocks
        mock_dir_dialog.return_value = temp_dir
        mock_exportar_todos.return_value = 2  # 2 PDFs generados

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        # Ejecutar exportación
        form.exportar_pdfs()

        # Verificar que se llamó al generador de PDF
        mock_exportar_todos.assert_called_once()
        assert "pdf" in form.resultado_text.toPlainText().lower()

    @patch("presentation.forms.import_export_form.QFileDialog.getExistingDirectory")
    def test_exportar_pdfs_cancelado(self, mock_dir_dialog, qtbot, session):
        """Test: Cancelar exportación de PDFs no hace nada."""
        mock_dir_dialog.return_value = ""  # Usuario canceló

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        form.exportar_pdfs()

        # No debe haber mensaje de éxito
        texto = form.resultado_text.toPlainText()
        assert texto == "" or "cancelado" in texto.lower()


@pytest.mark.ui
class TestImportExportFormMetodos:
    """Tests para métodos específicos del formulario."""

    def test_exportar_datos_metodo_existe(self, qtbot, session):
        """Test: El método exportar_datos existe."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, "exportar_datos")
        assert callable(form.exportar_datos)

    def test_importar_datos_metodo_existe(self, qtbot, session):
        """Test: El método importar_datos existe."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, "importar_datos")
        assert callable(form.importar_datos)

    @pytest.mark.skip(reason="La funcionalidad exportar_pdfs no está en ImportExportForm")
    def test_exportar_pdfs_metodo_existe(self, qtbot, session):
        """Test: El método exportar_pdfs existe."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, "exportar_pdfs")
        assert callable(form.exportar_pdfs)


@pytest.mark.ui
class TestImportExportFormIntegracion:
    """Tests de integración."""

    @pytest.mark.skip(reason="La funcionalidad PDF no está en ImportExportForm")
    def test_cambiar_mes_actualiza_combo(self, qtbot, session):
        """Test: Cambiar el mes actualiza el combo."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        # Cambiar mes
        form.pdf_mes_combo.setCurrentIndex(5)  # Junio

        assert form.pdf_mes_combo.currentIndex() == 5
        assert form.pdf_mes_combo.currentText() == "Junio"

    @pytest.mark.skip(reason="La funcionalidad PDF no está en ImportExportForm")
    def test_cambiar_anio_actualiza_combo(self, qtbot, session):
        """Test: Cambiar el año actualiza el combo."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        # Cambiar año
        form.pdf_anio_combo.setCurrentIndex(2)

        assert form.pdf_anio_combo.currentIndex() == 2

    def test_checkbox_limpiar_puede_desmarcarse(self, qtbot, session):
        """Test: El checkbox de limpiar puede desmarcarse."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        # Inicialmente checked
        assert form.limpiar_checkbox.isChecked()

        # Desmarcar
        form.limpiar_checkbox.setChecked(False)

        assert not form.limpiar_checkbox.isChecked()


@pytest.mark.ui
class TestImportExportFormRobustez:
    """Tests de robustez y casos edge."""

    def test_form_sin_datos_en_bd(self, qtbot, session):
        """Test: El formulario funciona sin datos en la base de datos."""
        form = ImportExportForm(session)
        qtbot.addWidget(form)

        assert form is not None
        assert form.exportar_btn is not None

    @patch("presentation.forms.import_export_form.QFileDialog.getSaveFileName")
    @patch("presentation.forms.import_export_form.ExportadorDatos.exportar_todo")
    def test_exportar_sin_profesores(self, mock_exportar, mock_file_dialog, qtbot, session):
        """Test: Exportar sin profesores funciona."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        temp_file.close()

        mock_file_dialog.return_value = (temp_file.name, "JSON Files (*.json)")
        mock_exportar.return_value = None

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        form.exportar_datos()

        # Debe ejecutarse sin errores
        mock_exportar.assert_called_once()

        # Limpiar
        os.unlink(temp_file.name)

    @pytest.mark.skip(reason="La funcionalidad exportar_pdfs no está en ImportExportForm")
    @patch("presentation.forms.import_export_form.QFileDialog.getExistingDirectory")
    def test_exportar_pdf_sin_profesores(self, mock_dir_dialog, qtbot, session):
        """Test: Intentar exportar PDF sin profesores muestra mensaje."""
        temp_dir = tempfile.mkdtemp()
        mock_dir_dialog.return_value = temp_dir

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        form.exportar_pdfs()

        # Debe mostrar mensaje de éxito con 0 PDFs generados
        texto = form.resultado_text.toPlainText().lower()
        assert "generado" in texto or "pdf" in texto


@pytest.mark.ui
@pytest.mark.slow
class TestImportExportFormRendimiento:
    """Tests de rendimiento."""

    def test_carga_rapida(self, qtbot, session, datos_completos):
        """Test: El formulario carga rápidamente."""
        import time

        start = time.time()
        form = ImportExportForm(session)
        qtbot.addWidget(form)
        duration = time.time() - start

        assert duration < 1.0, f"Carga demasiado lenta: {duration:.2f}s"

    @patch("presentation.forms.import_export_form.QFileDialog.getSaveFileName")
    @patch("presentation.forms.import_export_form.ExportadorDatos.exportar_todo")
    def test_exportacion_rapida(
        self, mock_exportar, mock_file_dialog, qtbot, session, datos_completos
    ):
        """Test: La exportación es rápida."""
        import time

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        temp_file.close()

        mock_file_dialog.return_value = (temp_file.name, "JSON Files (*.json)")
        mock_exportar.return_value = None

        form = ImportExportForm(session)
        qtbot.addWidget(form)

        start = time.time()
        form.exportar_datos()
        duration = time.time() - start

        assert duration < 3.0, f"Exportación demasiado lenta: {duration:.2f}s"

        # Limpiar
        os.unlink(temp_file.name)
