"""Tests de UI para ZonaForm — CRUD completo de zonas."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Zona
from presentation.forms.zona_form import ZonaForm

from tests.ui.helpers import confirm_no, confirm_yes, dbl_click_row, select_row


@pytest.fixture
def form(qapp, session):
    f = ZonaForm(session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def form_con_zonas(qapp, session, zona_factory):
    zona_factory(nombre_zona="Patio Principal")
    zona_factory(nombre_zona="Zona Deportiva")
    session.flush()
    f = ZonaForm(session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


class TestZonaFormRenderizado:
    def test_tabla_visible(self, form):
        assert form.tabla_zonas.isVisible()

    def test_n_filas_igual_a_zonas_en_bd(self, form, session):
        n = session.query(Zona).count()
        assert form.tabla_zonas.rowCount() == n

    def test_tabla_muestra_zonas_precargadas(self, form_con_zonas, session):
        n = session.query(Zona).count()
        assert form_con_zonas.tabla_zonas.rowCount() == n


class TestZonaFormCrear:
    def test_crear_zona_valida_aparece_en_tabla(self, qtbot, form, session):
        """Crear zona válida la añade a BD y tabla."""
        n_inicial = session.query(Zona).count()
        form.nombre_zona_input.setText("Nueva Zona")
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Zona).count() == n_inicial + 1

    def test_crear_zona_nombre_vacio_muestra_advertencia(self, qtbot, form, session):
        """Guardar sin nombre muestra advertencia."""
        from unittest.mock import patch

        form.nombre_zona_input.clear()
        with patch.object(form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()


class TestZonaFormEditar:
    def test_doble_click_carga_nombre_en_formulario(self, qtbot, form_con_zonas):
        """Doble-click en fila carga el nombre de la zona en el campo."""
        select_row(form_con_zonas.tabla_zonas, 0)
        form_con_zonas.editar_zona()
        QApplication.processEvents()
        assert form_con_zonas.nombre_zona_input.text() != ""

    def test_editar_nombre_actualiza_bd(self, qtbot, form_con_zonas, session):
        """Editar nombre de zona y guardar actualiza la BD."""
        zona = session.query(Zona).first()
        zona_id = zona.id

        select_row(form_con_zonas.tabla_zonas, 0)
        form_con_zonas.editar_zona()
        QApplication.processEvents()

        form_con_zonas.nombre_zona_input.setText("Zona Actualizada")
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form_con_zonas, "mostrar_exito"):
            qtbot.mouseClick(form_con_zonas.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        actualizada = session.get(Zona, zona_id)
        assert actualizada.nombre_zona == "Zona Actualizada"

    def test_cancelar_edicion_no_modifica_bd(self, qtbot, form_con_zonas, session):
        """Cancelar edición sin guardar no modifica la BD."""
        nombre_original = session.query(Zona).first().nombre_zona

        select_row(form_con_zonas.tabla_zonas, 0)
        form_con_zonas.editar_zona()
        QApplication.processEvents()
        form_con_zonas.nombre_zona_input.setText("Nombre Cancelado")

        qtbot.mouseClick(form_con_zonas.cancelar_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()

        session.expire_all()
        assert session.query(Zona).first().nombre_zona == nombre_original


class TestZonaFormEliminar:
    def test_eliminar_con_confirmacion(self, qtbot, form_con_zonas, session):
        """Eliminar zona con confirmación la borra de BD."""
        n_inicial = session.query(Zona).count()
        select_row(form_con_zonas.tabla_zonas, 0)

        with confirm_yes(form_con_zonas):
            qtbot.mouseClick(form_con_zonas.delete_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Zona).count() == n_inicial - 1

    def test_eliminar_cancelado_conserva_zona(self, qtbot, form_con_zonas, session):
        """Cancelar eliminación conserva la zona en BD."""
        n_inicial = session.query(Zona).count()
        select_row(form_con_zonas.tabla_zonas, 0)

        with confirm_no(form_con_zonas):
            qtbot.mouseClick(form_con_zonas.delete_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Zona).count() == n_inicial
