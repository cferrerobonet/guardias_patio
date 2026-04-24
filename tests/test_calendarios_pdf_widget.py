"""
Tests para CalendariosPdfWidget.

Este módulo contiene tests para la funcionalidad de exportación de calendarios PDF
que anteriormente estaba en ImportExportForm.
"""

from datetime import datetime

import pytest
from presentation.forms.reportes_widgets.calendarios_pdf_widget import CalendariosPdfWidget
from PyQt6.QtWidgets import QComboBox, QPushButton


@pytest.fixture
def widget(qtbot, session):
    """Fixture que crea un CalendariosPdfWidget."""
    widget = CalendariosPdfWidget(session)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def widget_con_profesores(qtbot, session, profesor_factory):
    """Fixture con profesores para testear selección."""
    # Crear profesores
    for i in range(3):
        profesor_factory(nombre_completo=f"Profesor Test {i+1}")

    widget = CalendariosPdfWidget(session)
    qtbot.addWidget(widget)
    return widget


# ========================================
# TESTS DE ESTRUCTURA DEL WIDGET
# ========================================


class TestCalendariosPdfWidgetEstructura:
    """Tests de estructura básica del widget."""

    def test_widget_se_crea(self, widget):
        """Test: El widget se crea correctamente."""
        assert widget is not None
        assert isinstance(widget, CalendariosPdfWidget)

    def test_combo_mes_presente(self, widget):
        """Test: El combo de mes está presente."""
        assert widget.pdf_mes_combo is not None
        assert isinstance(widget.pdf_mes_combo, QComboBox)
        # Debe tener 12 meses
        assert widget.pdf_mes_combo.count() == 12

    def test_combo_anio_presente(self, widget):
        """Test: El combo de año está presente."""
        assert widget.pdf_anio_combo is not None
        assert isinstance(widget.pdf_anio_combo, QComboBox)
        # Debe tener al menos 4 años
        assert widget.pdf_anio_combo.count() >= 4

    def test_combo_tipo_presente(self, widget):
        """Test: El combo de tipo de exportación está presente."""
        assert widget.pdf_tipo_combo is not None
        assert isinstance(widget.pdf_tipo_combo, QComboBox)
        assert widget.pdf_tipo_combo.count() == 2

    def test_boton_exportar_presente(self, widget):
        """Test: El botón de exportar PDF está presente."""
        assert widget.exportar_pdf_btn is not None
        assert isinstance(widget.exportar_pdf_btn, QPushButton)


class TestCalendariosPdfWidgetMeses:
    """Tests para la funcionalidad de meses."""

    def test_combo_mes_valores_correctos(self, widget):
        """Test: El combo de mes tiene los meses correctos."""
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
            assert widget.pdf_mes_combo.itemText(i) == mes

    def test_mes_actual_seleccionado_por_defecto(self, widget):
        """Test: El mes actual está seleccionado por defecto."""
        mes_actual = datetime.now().month - 1  # 0-indexed
        assert widget.pdf_mes_combo.currentIndex() == mes_actual

    def test_cambiar_mes_actualiza_combo(self, widget):
        """Test: Cambiar el mes actualiza el valor del combo."""
        widget.pdf_mes_combo.setCurrentIndex(5)  # Junio
        assert widget.pdf_mes_combo.currentIndex() == 5
        assert widget.pdf_mes_combo.currentText() == "Junio"


class TestCalendariosPdfWidgetAnio:
    """Tests para la funcionalidad de año."""

    def test_anio_actual_disponible(self, widget):
        """Test: El año actual está disponible en el combo."""
        anio_actual = str(datetime.now().year)
        anios = [widget.pdf_anio_combo.itemText(i) for i in range(widget.pdf_anio_combo.count())]
        assert anio_actual in anios

    def test_cambiar_anio_actualiza_combo(self, widget):
        """Test: Cambiar el año actualiza el valor del combo."""
        widget.pdf_anio_combo.setCurrentIndex(0)
        primer_anio = widget.pdf_anio_combo.currentText()

        widget.pdf_anio_combo.setCurrentIndex(2)
        assert widget.pdf_anio_combo.currentText() != primer_anio


class TestCalendariosPdfWidgetTipoExportacion:
    """Tests para tipos de exportación."""

    def test_tipo_mes_seleccionados_disponible(self, widget):
        """Test: El tipo 'mes seleccionados' está disponible."""
        for i in range(widget.pdf_tipo_combo.count()):
            if widget.pdf_tipo_combo.itemData(i) == "mes_seleccionados":
                return
        pytest.fail("Tipo 'mes_seleccionados' no encontrado")

    def test_tipo_individual_disponible(self, widget):
        """Test: El tipo 'individual' está disponible."""
        for i in range(widget.pdf_tipo_combo.count()):
            if widget.pdf_tipo_combo.itemData(i) == "individual_seleccionados":
                return
        pytest.fail("Tipo 'individual_seleccionados' no encontrado")


class TestCalendariosPdfWidgetProfesores:
    """Tests para selección de profesores."""

    def test_carga_profesores(self, widget_con_profesores):
        """Test: Los profesores se cargan en el widget."""
        # Forzar recarga
        widget_con_profesores.cargar_profesores_checkboxes()

        # Debe haber checkboxes de profesores
        assert len(widget_con_profesores.profesor_checkboxes) == 3

    def test_seleccionar_todos(self, widget_con_profesores):
        """Test: El checkbox seleccionar todos selecciona todos los profesores."""
        from PyQt6.QtCore import Qt

        widget_con_profesores.cargar_profesores_checkboxes()
        # Usar el checkbox de seleccionar todos
        widget_con_profesores.seleccionar_todos_check.setCheckState(Qt.CheckState.Checked)

        for checkbox in widget_con_profesores.profesor_checkboxes:
            assert checkbox.isChecked()

    def test_deseleccionar_todos(self, widget_con_profesores):
        """Test: Desmarcar seleccionar todos deselecciona todos los profesores."""
        from PyQt6.QtCore import Qt

        widget_con_profesores.cargar_profesores_checkboxes()
        widget_con_profesores.seleccionar_todos_check.setCheckState(Qt.CheckState.Checked)
        widget_con_profesores.seleccionar_todos_check.setCheckState(Qt.CheckState.Unchecked)

        for checkbox in widget_con_profesores.profesor_checkboxes:
            assert not checkbox.isChecked()


class TestCalendariosPdfWidgetSenal:
    """Tests para la señal de generación."""

    def test_senal_generar_pdfs_existe(self, widget):
        """Test: La señal generar_pdfs_solicitado existe."""
        assert hasattr(widget, "generar_pdfs_solicitado")

    def test_boton_emite_senal(self, widget, qtbot):
        """Test: El botón emite la señal correcta."""
        with qtbot.waitSignal(widget.generar_pdfs_solicitado, timeout=1000):
            widget.exportar_pdf_btn.click()


class TestCalendariosPdfWidgetRobustez:
    """Tests de robustez."""

    def test_widget_sin_profesores(self, qtbot, session):
        """Test: El widget funciona sin profesores."""
        widget = CalendariosPdfWidget(session)
        qtbot.addWidget(widget)

        # No debe crashear
        assert widget is not None
        assert widget.pdf_mes_combo.count() == 12

    def test_obtener_mes_anio_seleccionado(self, widget):
        """Test: Se puede obtener el mes y año seleccionado."""
        from datetime import datetime
        anio_disponible = str(datetime.now().year)
        widget.pdf_mes_combo.setCurrentIndex(9)  # Octubre
        widget.pdf_anio_combo.setCurrentText(anio_disponible)

        mes = widget.pdf_mes_combo.currentIndex() + 1  # 1-indexed
        anio = int(widget.pdf_anio_combo.currentText())

        assert mes == 10
        assert anio == int(anio_disponible)
