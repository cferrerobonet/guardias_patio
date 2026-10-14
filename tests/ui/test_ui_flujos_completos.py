"""
Tests de integración E2E — flujos completos de usuario sin mocks de use cases.

Usan BD en memoria real y ejercitan el stack completo desde UI hasta BD.
"""

from datetime import date
from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Profesor, Zona
from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.zona_form import ZonaForm

from tests.ui.helpers import confirm_yes, dbl_click_row, select_row


# ============================================================
# F1: Alta completa de profesor — todos los campos persisten
# ============================================================


class TestF1AltaCompleta:
    def test_alta_profesor_con_zona_persiste_todos_campos(
        self, qapp, session, zona_factory
    ):
        """Crear profesor con zona preferida → verificar que todos los campos persisten."""
        zona = zona_factory(nombre_zona="Patio Test")
        session.flush()

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()

        form._abrir_formulario_nuevo()
        QApplication.processEvents()

        form.datos_basicos_widget.nombre_completo_input.setText("PRUEBA, Flujo E2E")
        form.datos_basicos_widget.email_input.setText("flujo@test.edu")
        form.datos_basicos_widget.tutor_checkbox.setChecked(True)
        form.horario_widget.horas_input.setText("25")
        form.horario_widget.set_turno("mañana")

        combo = form.restricciones_widget.zona_preferida_combo
        for i in range(combo.count()):
            if combo.itemData(i) == zona.id:
                combo.setCurrentIndex(i)
                break
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.submit_btn.click()
            QApplication.processEvents()

        session.expire_all()
        prof = session.query(Profesor).filter_by(nombre_completo="PRUEBA, Flujo E2E").first()
        assert prof is not None
        assert prof.email_corporativo == "flujo@test.edu"
        assert prof.tutor is True
        assert prof.zona_preferida_id == zona.id
        assert prof.horas_contrato == 25.0

        form.close()

    def test_alta_profesor_y_recarga_muestra_datos_correctos(self, qapp, session):
        """Crear profesor → recargar formulario → verificar que aparece en tabla."""
        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()

        n_inicial = form.tabla_profesores.rowCount()

        form._abrir_formulario_nuevo()
        QApplication.processEvents()

        form.datos_basicos_widget.nombre_completo_input.setText("RECARGA, Test")
        form.horario_widget.horas_input.setText("18")
        form.horario_widget.set_turno("tarde")
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.submit_btn.click()
            QApplication.processEvents()

        assert form.tabla_profesores.rowCount() == n_inicial + 1

        form.close()


# ============================================================
# F2: Ciclo CRUD de zona
# ============================================================


class TestF2CRUDZona:
    def test_crear_editar_eliminar_zona(self, qapp, session):
        """Crear zona → editar nombre → eliminar → tabla vacía."""
        form = ZonaForm(session)
        form.show()
        QApplication.processEvents()

        form.nombre_zona_input.setText("Zona Ciclo CRUD")
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.submit_btn.click()
            QApplication.processEvents()

        n_tras_crear = form.tabla_zonas.rowCount()
        assert n_tras_crear >= 1

        select_row(form.tabla_zonas, 0)
        form.editar_zona()
        QApplication.processEvents()

        form.nombre_zona_input.setText("Zona Ciclo CRUD Editada")
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.submit_btn.click()
            QApplication.processEvents()

        session.expire_all()
        zona = session.query(Zona).filter_by(nombre_zona="Zona Ciclo CRUD Editada").first()
        assert zona is not None

        select_row(form.tabla_zonas, 0)
        with confirm_yes(form):
            form.delete_btn.click()
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Zona).filter_by(nombre_zona="Zona Ciclo CRUD Editada").first() is None

        form.close()


# ============================================================
# F3: Editar profesor — verificar zona_preferida persiste (regresión E2E)
# ============================================================


class TestF3RegresionZonaPersiste:
    def test_editar_zona_preferida_persiste_en_bd(self, qapp, session, zona_factory):
        """E2E: Editar zona preferida de un profesor existente y verificar persistencia."""
        zona = zona_factory(nombre_zona="Zona E2E")

        prof = Profesor(
            nombre_completo="E2E, Profesor",
            horas_contrato=20.0,
            porcentaje_jornada=80,
            turno="mañana",
        )
        session.add(prof)
        session.commit()
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        combo = form.restricciones_widget.zona_preferida_combo
        for i in range(combo.count()):
            if combo.itemData(i) == zona.id:
                combo.setCurrentIndex(i)
                break
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.submit_btn.click()
            QApplication.processEvents()

        session.expire_all()
        actualizado = session.get(Profesor, prof_id)
        assert actualizado.zona_preferida_id == zona.id

        form.close()

    def test_limpiar_zona_preferida_persiste_null(self, qapp, session, zona_factory):
        """E2E: Limpiar zona preferida → zona_preferida_id = NULL en BD."""
        zona = zona_factory(nombre_zona="Zona Limpiar")

        prof = Profesor(
            nombre_completo="E2E Limpiar, Zona",
            horas_contrato=20.0,
            porcentaje_jornada=80,
            turno="mañana",
            zona_preferida_id=zona.id,
        )
        session.add(prof)
        session.commit()
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        form.restricciones_widget.zona_preferida_combo.setCurrentIndex(0)  # Sin preferencia
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.submit_btn.click()
            QApplication.processEvents()

        session.expire_all()
        actualizado = session.get(Profesor, prof_id)
        assert actualizado.zona_preferida_id is None

        form.close()


# ============================================================
# F4: Doble edición — datos no se mezclan entre profesores
# ============================================================


class TestF4DatosNoSeMezclan:
    def test_editar_dos_profesores_sucesivamente_no_mezcla_datos(
        self, qapp, session, zona_factory, profesor_factory
    ):
        """Editar prof A → cancelar → editar prof B → datos de B, no A."""
        zona = zona_factory(nombre_zona="Zona Mix")
        prof_a = profesor_factory(
            "PRIMERO, Profesor A",
            turno="mañana",
            horas_contrato=25.0,
            zona_preferida_id=zona.id,
        )
        prof_b = profesor_factory("SEGUNDO, Profesor B", turno="tarde", horas_contrato=18.0)
        session.flush()

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()

        select_row(form.tabla_profesores, 0)
        form.editar_profesor()
        QApplication.processEvents()

        form.cancelar_btn.click()
        QApplication.processEvents()

        select_row(form.tabla_profesores, 1)
        form.editar_profesor()
        QApplication.processEvents()

        nombre_cargado = form.datos_basicos_widget.nombre_completo_input.text()
        zona_id_cargado = form.restricciones_widget.get_zona_preferida_id()

        assert nombre_cargado != ""
        assert zona_id_cargado != zona.id

        form.close()
