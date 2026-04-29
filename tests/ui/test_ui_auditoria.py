"""Tests de UI para AuditoriaGuardiasForm — historial de cambios de guardias."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import GuardiaAuditLog
from presentation.forms.auditoria_guardias_form import AuditoriaGuardiasForm


@pytest.fixture
def form(qapp, session):
    f = AuditoriaGuardiasForm(session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def form_con_registros(qapp, session, profesor_factory, zona_factory):
    zona = zona_factory(nombre_zona="Patio Test")
    prof = profesor_factory("Auditor, Profesor", turno="mañana", horas_contrato=20.0)
    session.flush()

    for accion in ("CREADA", "MODIFICADA", "ELIMINADA"):
        log = GuardiaAuditLog(
            guardia_id=1,
            accion=accion,
            profesor_id=prof.id,
            usuario="test_user",
            timestamp=datetime.now() - timedelta(days=1),
            detalle='{"turno": "mañana"}',
        )
        session.add(log)
    session.commit()

    f = AuditoriaGuardiasForm(session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


class TestAuditoriaRenderizado:
    def test_form_se_crea_sin_crash(self, form):
        assert form is not None

    def test_tabla_existe(self, form):
        assert hasattr(form, "tabla")
        assert not form.tabla.isHidden()

    def test_tabla_columnas(self, form):
        assert form.tabla.columnCount() == 6

    def test_filtros_visibles(self, form):
        assert hasattr(form, "fecha_desde")
        assert hasattr(form, "fecha_hasta")
        assert hasattr(form, "combo_accion")
        assert hasattr(form, "input_profesor")

    def test_bd_vacia_no_crashea(self, form):
        assert form.tabla.rowCount() == 0
        assert "0 registros" in form.label_total.text()


class TestAuditoriaConDatos:
    def test_registros_se_cargan_en_tabla(self, form_con_registros):
        assert form_con_registros.tabla.rowCount() == 3

    def test_label_total_muestra_conteo(self, form_con_registros):
        assert "3 registros" in form_con_registros.label_total.text()

    def test_filtrar_por_accion_creada(self, qtbot, form_con_registros):
        """Filtrar por 'CREADA' reduce las filas a 1."""
        idx = form_con_registros.combo_accion.findText("CREADA")
        form_con_registros.combo_accion.setCurrentIndex(idx)
        form_con_registros.cargar_datos()
        QApplication.processEvents()
        assert form_con_registros.tabla.rowCount() == 1

    def test_filtrar_por_texto_profesor(self, qtbot, form_con_registros):
        """Filtrar por nombre de profesor devuelve sus registros."""
        form_con_registros.input_profesor.setText("Auditor")
        form_con_registros.cargar_datos()
        QApplication.processEvents()
        assert form_con_registros.tabla.rowCount() == 3

    def test_filtrar_texto_inexistente_da_cero(self, qtbot, form_con_registros):
        form_con_registros.input_profesor.setText("XYZ_no_existe")
        form_con_registros.cargar_datos()
        QApplication.processEvents()
        assert form_con_registros.tabla.rowCount() == 0

    def test_limpiar_filtros_restaura_todos(self, qtbot, form_con_registros):
        """Después de filtrar, limpiar restaura todos los registros."""
        idx = form_con_registros.combo_accion.findText("ELIMINADA")
        form_con_registros.combo_accion.setCurrentIndex(idx)
        form_con_registros.cargar_datos()
        QApplication.processEvents()
        assert form_con_registros.tabla.rowCount() == 1

        form_con_registros._limpiar_filtros()
        QApplication.processEvents()
        assert form_con_registros.tabla.rowCount() == 3

    def test_filtro_rango_fechas_excluye_futuros(self, qtbot, form_con_registros):
        """Rango de fechas que excluye ayer no devuelve registros."""
        hoy = date.today()
        form_con_registros.fecha_desde.setDate(QDate(hoy.year, hoy.month, hoy.day))
        form_con_registros.fecha_hasta.setDate(QDate(hoy.year, hoy.month, hoy.day))
        form_con_registros.cargar_datos()
        QApplication.processEvents()
        assert form_con_registros.tabla.rowCount() == 0
