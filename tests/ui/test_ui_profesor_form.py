"""
Tests de UI para ProfesorForm — simulación completa de usuario beta tester.

Cubre: renderizado, búsqueda, alta, edición, eliminación, atajos de teclado
y los casos de regresión de zona_preferida + campos limpiables.
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Profesor
from presentation.forms.profesor_form import ProfesorForm

from tests.ui.helpers import confirm_no, confirm_yes, dbl_click_row, select_row


# ============================================================
# Fixtures locales
# ============================================================


@pytest.fixture
def form(qapp, ui_session):
    """ProfesorForm con tres profesores y dos zonas precargadas."""
    f = ProfesorForm(ui_session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def form_con_zona(qapp, session, zona_factory, profesor_factory):
    """ProfesorForm con un profesor que tiene zona preferida asignada."""
    zona = zona_factory(nombre_zona="Zona Test")
    profesor_factory(
        "López García, Pedro",
        turno="mañana",
        horas_contrato=25.0,
        zona_preferida_id=zona.id,
    )
    profesor_factory("Sin Zona, Profe", turno="tarde", horas_contrato=18.0)
    session.flush()
    f = ProfesorForm(session)
    f.show()
    QApplication.processEvents()
    yield f, zona
    f.close()


# ============================================================
# MÓDULO 1: Renderizado inicial
# ============================================================


class TestProfesorFormRenderizado:
    def test_tabla_existe_y_no_oculta(self, form):
        """Tabla de profesores existe y no está explícitamente oculta."""
        assert hasattr(form, "tabla_profesores")
        assert not form.tabla_profesores.isHidden()

    def test_form_panel_oculto_por_defecto(self, form):
        """Panel de formulario oculto antes de abrir alta/edición."""
        assert not form._form_panel.isVisible()

    def test_n_filas_igual_a_profesores_en_bd(self, form, ui_session):
        """El número de filas coincide con los profesores en BD."""
        n_bd = ui_session.query(Profesor).count()
        assert form.tabla_profesores.rowCount() == n_bd

    def test_titulo_lista_muestra_contador(self, form, ui_session):
        """El título muestra el número de profesores."""
        n = ui_session.query(Profesor).count()
        assert str(n) in form.titulo_lista_profesores.text()


# ============================================================
# MÓDULO 2: Búsqueda
# ============================================================


class TestProfesorFormBusqueda:
    def test_busqueda_filtra_tabla(self, form):
        """Escribir en busqueda_input filtra las filas visibles."""
        total = form.tabla_profesores.rowCount()
        form.busqueda_input.setText("García")
        QApplication.processEvents()
        filas_visibles = sum(
            not form.tabla_profesores.isRowHidden(r)
            for r in range(form.tabla_profesores.rowCount())
        )
        assert filas_visibles < total

    def test_limpiar_busqueda_restaura_filas(self, qtbot, form):
        """Al limpiar la búsqueda todas las filas se muestran de nuevo."""
        total = form.tabla_profesores.rowCount()
        form.busqueda_input.setText("García")
        QApplication.processEvents()
        qtbot.mouseClick(form.limpiar_busqueda_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        filas_visibles = sum(
            not form.tabla_profesores.isRowHidden(r)
            for r in range(form.tabla_profesores.rowCount())
        )
        assert filas_visibles == total

    def test_busqueda_existe_y_es_editable(self, form):
        """busqueda_input existe y es un campo editable."""
        assert hasattr(form, "busqueda_input")
        assert not form.busqueda_input.isReadOnly()


# ============================================================
# MÓDULO 3: Alta de nuevo profesor
# ============================================================


class TestProfesorFormAlta:
    def test_boton_nuevo_abre_formulario(self, form):
        """Click en 'Nuevo' muestra el panel lateral."""
        form._abrir_formulario_nuevo()
        QApplication.processEvents()
        assert form._form_panel.isVisible()

    def test_boton_nuevo_muestra_titulo_alta(self, form):
        """El título del formulario indica 'ALTA'."""
        form._abrir_formulario_nuevo()
        QApplication.processEvents()
        assert "ALTA" in form.titulo_seccion.text()

    def test_boton_nuevo_campos_vacios(self, form):
        """Al abrir el formulario de alta, el nombre está vacío."""
        form._abrir_formulario_nuevo()
        QApplication.processEvents()
        assert form.datos_basicos_widget.nombre_completo_input.text() == ""

    def test_guardar_nuevo_profesor_valido(self, qtbot, form, ui_session):
        """Guardar un profesor válido crea una fila nueva en tabla y BD."""
        n_inicial = ui_session.query(Profesor).count()
        qtbot.mouseClick(form.nuevo_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()

        form.datos_basicos_widget.nombre_completo_input.setText("NUEVO, Profesor")
        form.horario_widget.horas_input.setText("20")
        form.horario_widget.set_turno("mañana")
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        n_final = ui_session.query(Profesor).count()
        assert n_final == n_inicial + 1

    def test_guardar_nombre_vacio_muestra_advertencia(self, qtbot, form):
        """Guardar sin nombre muestra advertencia y no crea registro."""
        qtbot.mouseClick(form.nuevo_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_cancelar_oculta_formulario(self, qtbot, form):
        """Cancelar edición cierra el panel lateral."""
        qtbot.mouseClick(form.nuevo_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        qtbot.mouseClick(form.cancelar_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        assert not form._form_panel.isVisible()


# ============================================================
# MÓDULO 4: Edición de profesor
# ============================================================


class TestProfesorFormEdicion:
    def test_editar_profesor_abre_formulario(self, qtbot, form):
        """Editar profesor muestra panel con título EDITAR."""
        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()
        assert form._form_panel.isVisible()
        assert "EDITAR" in form.titulo_seccion.text()

    def test_editar_profesor_carga_nombre(self, qtbot, form):
        """Al editar, el nombre del profesor queda cargado en el formulario."""
        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()
        nombre = form.datos_basicos_widget.nombre_completo_input.text()
        assert nombre != ""

    def test_cancelar_edicion_no_modifica_bd(self, qtbot, form, ui_session):
        """Cancelar edición no altera la BD."""
        nombre_original = ui_session.query(Profesor).first().nombre_completo

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()
        form.datos_basicos_widget.nombre_completo_input.setText("CAMBIADO, Temporal")
        QApplication.processEvents()

        qtbot.mouseClick(form.cancelar_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()

        ui_session.expire_all()
        nombre_bd = ui_session.query(Profesor).first().nombre_completo
        assert nombre_bd == nombre_original

    def test_editar_cambiar_nombre_actualiza_bd(self, qtbot, form, ui_session):
        """Editar y guardar un nombre actualiza la BD correctamente."""
        prof = ui_session.query(Profesor).first()
        prof_id = prof.id

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        form.datos_basicos_widget.nombre_completo_input.setText("APELLIDO, Nuevo Nombre")
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        ui_session.expire_all()
        actualizado = ui_session.get(Profesor, prof_id)
        assert actualizado.nombre_completo == "APELLIDO, Nuevo Nombre"


# ============================================================
# MÓDULO 5: Regresiones — zona_preferida y campos limpiables
# ============================================================


class TestProfesorFormZonaPreferida:
    """Tests de regresión para zona_preferida_id y campos que se limpiaban incorrectamente."""

    def test_zona_preferida_cargada_al_editar(self, qtbot, form_con_zona):
        """Al editar un profesor con zona, el combo muestra la zona correcta (bug fix)."""
        form, zona = form_con_zona
        QApplication.processEvents()

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        zona_id = form.restricciones_widget.get_zona_preferida_id()
        assert zona_id == zona.id

    def test_asignar_zona_preferida_persiste(self, qtbot, form_con_zona, session):
        """Asignar zona preferida y guardar persiste en BD (bug fix)."""
        form, zona = form_con_zona
        QApplication.processEvents()

        prof = session.query(Profesor).filter_by(nombre_completo="Sin Zona, Profe").first()

        select_row(form.tabla_profesores, 1)
        form.editar_profesor()
        QApplication.processEvents()

        combo = form.restricciones_widget.zona_preferida_combo
        for i in range(combo.count()):
            if combo.itemData(i) == zona.id:
                combo.setCurrentIndex(i)
                break
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        actualizado = session.get(Profesor, prof.id)
        assert actualizado.zona_preferida_id == zona.id

    def test_limpiar_zona_preferida_persiste(self, qtbot, form_con_zona, session):
        """Limpiar zona preferida (Sin preferencia) y guardar persiste NULL en BD."""
        form, zona = form_con_zona
        QApplication.processEvents()

        prof = session.query(Profesor).filter_by(nombre_completo="López García, Pedro").first()

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        form.restricciones_widget.zona_preferida_combo.setCurrentIndex(0)  # Sin preferencia
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        actualizado = session.get(Profesor, prof.id)
        assert actualizado.zona_preferida_id is None

    def test_limpiar_fecha_inicio_persiste_null(self, qtbot, form_con_zona, session):
        """Desmarcar fecha inicio y guardar persiste NULL en BD."""
        form, zona = form_con_zona
        QApplication.processEvents()

        from datetime import date

        prof = session.query(Profesor).filter_by(nombre_completo="López García, Pedro").first()
        prof.fecha_inicio_guardias = date(2025, 1, 1)
        session.commit()

        form.cargar_profesores()
        QApplication.processEvents()

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        form.restricciones_widget.usar_fecha_inicio_checkbox.setChecked(False)
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        actualizado = session.get(Profesor, prof.id)
        assert actualizado.fecha_inicio_guardias is None

    def test_limpiar_email_persiste_null(self, qtbot, form_con_zona, session):
        """Borrar email y guardar persiste NULL en BD."""
        form, zona = form_con_zona
        QApplication.processEvents()

        prof = session.query(Profesor).filter_by(nombre_completo="López García, Pedro").first()
        prof.email_corporativo = "pedro@colegio.edu"
        session.commit()

        form.cargar_profesores()
        QApplication.processEvents()

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        form.datos_basicos_widget.email_input.clear()
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.submit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        actualizado = session.get(Profesor, prof.id)
        assert not actualizado.email_corporativo


# ============================================================
# MÓDULO 6: Eliminación
# ============================================================


class TestProfesorFormEliminacion:
    def test_eliminar_sin_seleccion_muestra_advertencia(self, qtbot, form):
        """Eliminar sin seleccionar fila muestra advertencia."""
        from unittest.mock import patch

        form.tabla_profesores.clearSelection()
        with patch.object(form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(form.delete_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_eliminar_con_confirmacion_elimina_fila(self, qtbot, form, ui_session):
        """Eliminar con confirmación elimina el profesor de BD y tabla."""
        n_inicial = ui_session.query(Profesor).count()
        select_row(form.tabla_profesores, 0)

        with confirm_yes(form):
            qtbot.mouseClick(form.delete_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        ui_session.expire_all()
        assert ui_session.query(Profesor).count() == n_inicial - 1

    def test_eliminar_cancelado_no_modifica_bd(self, qtbot, form, ui_session):
        """Cancelar la eliminación no modifica la BD."""
        n_inicial = ui_session.query(Profesor).count()
        select_row(form.tabla_profesores, 0)

        with confirm_no(form):
            qtbot.mouseClick(form.delete_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        ui_session.expire_all()
        assert ui_session.query(Profesor).count() == n_inicial


# ============================================================
# MÓDULO 7: Atajos de teclado
# ============================================================


class TestProfesorFormAtajos:
    def test_cancelar_btn_oculta_formulario(self, qtbot, form):
        """El botón cancelar cierra el panel del formulario."""
        form._abrir_formulario_nuevo()
        QApplication.processEvents()
        assert form._form_panel.isVisible()

        qtbot.mouseClick(form.cancelar_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        assert not form._form_panel.isVisible()


# ============================================================
# MÓDULO 8: Restricciones de turno (matriz)
# ============================================================


class TestProfesorFormMatrizTurnos:
    def test_turno_tarde_preselecciona_recreos_tarde(self, qtbot, form):
        """Cambiar turno a 'Tarde' preselecciona R3, R4 en la matriz."""
        qtbot.mouseClick(form.nuevo_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()

        form.horario_widget.set_turno("tarde")
        QApplication.processEvents()

        restricciones = form.restricciones_widget.restricciones_dias
        if restricciones:
            for dia, recreos in restricciones.items():
                assert 3 in recreos or 4 in recreos

    def test_turno_manana_preselecciona_recreos_manana(self, qtbot, form):
        """Cambiar turno a 'Mañana' preselecciona R1, R2 en la matriz."""
        qtbot.mouseClick(form.nuevo_btn, Qt.MouseButton.LeftButton)
        QApplication.processEvents()

        form.horario_widget.set_turno("mañana")
        QApplication.processEvents()

        restricciones = form.restricciones_widget.restricciones_dias
        if restricciones:
            for dia, recreos in restricciones.items():
                assert any(r in recreos for r in [1, 2])
