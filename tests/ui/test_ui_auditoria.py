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


def _visibles(tabla) -> int:
    return sum(1 for r in range(tabla.rowCount()) if not tabla.isRowHidden(r))


def _accion(form):
    return next(f for f in form.listado.filtros if f.etiqueta == "Acción").combo


def _esta_vacia(tabla) -> bool:
    """Sin resultados: o ninguna fila, o la única fila es el mensaje de vacío."""
    if tabla.rowCount() == 0:
        return True
    celda = tabla.item(0, 0)
    return (
        tabla.rowCount() == 1
        and celda is not None
        and tabla.columnSpan(0, 0) == tabla.columnCount()
    )


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
        assert {f.etiqueta for f in form.listado.filtros} == {"Acción", "Usuario"}
        assert not form.listado.buscador.isHidden()

    def test_bd_vacia_no_crashea(self, form):
        # Desde v5.84.0 la tabla vacía escribe una fila que lo explica: en
        # blanco no se distinguía de «aún no ha cargado» (UXA-008).
        assert _esta_vacia(form.tabla)
        assert form.listado.recuento.text() == "Sin resultados"


class TestAuditoriaConDatos:
    def test_registros_se_cargan_en_tabla(self, form_con_registros):
        assert form_con_registros.tabla.rowCount() == 3

    def test_recuento_muestra_conteo(self, form_con_registros):
        assert form_con_registros.listado.recuento.text() == "3 cambios"

    def test_filtrar_por_accion_creada(self, qtbot, form_con_registros):
        """Filtrar por «Creada» deja una fila a la vista."""
        _accion(form_con_registros).setCurrentText("✚ Creada")
        QApplication.processEvents()
        assert _visibles(form_con_registros.tabla) == 1

    def test_buscar_por_profesor(self, qtbot, form_con_registros):
        """Buscar por nombre de profesor devuelve sus registros."""
        form_con_registros.listado.buscador.setText("Auditor")
        QApplication.processEvents()
        assert _visibles(form_con_registros.tabla) == 3

    def test_buscar_texto_inexistente_da_cero(self, qtbot, form_con_registros):
        form_con_registros.listado.buscador.setText("XYZ_no_existe")
        QApplication.processEvents()
        assert _visibles(form_con_registros.tabla) == 0
        assert form_con_registros.listado.recuento.text() == "Sin resultados"

    def test_limpiar_filtros_restaura_todos(self, qtbot, form_con_registros):
        """Después de filtrar, limpiar restaura todos los registros."""
        _accion(form_con_registros).setCurrentText("✕ Eliminada")
        QApplication.processEvents()
        assert _visibles(form_con_registros.tabla) == 1

        form_con_registros._limpiar_filtros()
        QApplication.processEvents()
        assert _visibles(form_con_registros.tabla) == 3

    def test_filtro_rango_fechas_excluye_futuros(self, qtbot, form_con_registros):
        """Rango de fechas que excluye ayer no devuelve registros."""
        hoy = date.today()
        form_con_registros.fecha_desde.setDate(QDate(hoy.year, hoy.month, hoy.day))
        form_con_registros.fecha_hasta.setDate(QDate(hoy.year, hoy.month, hoy.day))
        form_con_registros.cargar_datos()
        QApplication.processEvents()
        assert _esta_vacia(form_con_registros.tabla)
