"""
Tests para AuditoriaGuardiasForm.

Cubre: botón Re-sustituir, filtros, detalle JSON, señal re_sustituir_solicitada.
"""

import json
from datetime import date, timedelta

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import GuardiaAuditLog, Profesor
from presentation.forms.auditoria_guardias_form import AuditoriaGuardiasForm

pytestmark = pytest.mark.ui


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def form_audit(qtbot, session):
    widget = AuditoriaGuardiasForm(session)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def logs_variados(session, profesor_factory):
    """Crea entradas de audit log de distintos tipos."""
    prof1 = profesor_factory(nombre_completo="Profesor Uno")
    prof2 = profesor_factory(nombre_completo="Profesor Dos")

    entries = [
        GuardiaAuditLog(guardia_id=10, accion="CREADA", profesor_id=prof1.id),
        GuardiaAuditLog(
            guardia_id=11,
            accion="SUSTITUIDA",
            profesor_id=prof2.id,
            detalle=json.dumps({"profesor_anterior": "Profesor Uno", "origen": "ausencia"}),
        ),
        GuardiaAuditLog(guardia_id=12, accion="ELIMINADA", profesor_id=prof1.id),
        GuardiaAuditLog(guardia_id=None, accion="GENERADA_BULK", profesor_id=None),
    ]
    session.add_all(entries)
    session.commit()
    return {"profesores": [prof1, prof2], "entries": entries}


# ============================================================================
# TESTS: Botón Re-sustituir — estado inicial y por tipo de fila
# ============================================================================


class TestAuditoriaBotonResustituir:
    def test_boton_deshabilitado_inicialmente(self, form_audit):
        """El botón Re-sustituir empieza deshabilitado."""
        assert not form_audit.btn_resustituir.isEnabled()

    def test_boton_habilitado_al_seleccionar_fila_sustituida(
        self, form_audit, logs_variados
    ):
        """Seleccionar fila SUSTITUIDA habilita el botón."""
        form_audit.cargar_datos()
        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if data and data[1] == "SUSTITUIDA":
                form_audit.tabla.selectRow(row)
                break

        assert form_audit.btn_resustituir.isEnabled()

    def test_boton_deshabilitado_con_fila_creada(self, form_audit, logs_variados):
        """Seleccionar fila CREADA no habilita el botón."""
        form_audit.cargar_datos()
        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if data and data[1] == "CREADA":
                form_audit.tabla.selectRow(row)
                break

        assert not form_audit.btn_resustituir.isEnabled()

    def test_boton_deshabilitado_con_fila_eliminada(self, form_audit, logs_variados):
        """Seleccionar fila ELIMINADA no habilita el botón."""
        form_audit.cargar_datos()
        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if data and data[1] == "ELIMINADA":
                form_audit.tabla.selectRow(row)
                break

        assert not form_audit.btn_resustituir.isEnabled()

    def test_boton_deshabilitado_con_generada_bulk_sin_guardia_id(
        self, form_audit, logs_variados
    ):
        """Fila GENERADA_BULK con guardia_id=None no activa el botón."""
        form_audit.cargar_datos()
        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if data and data[1] == "GENERADA_BULK":
                form_audit.tabla.selectRow(row)
                break

        assert not form_audit.btn_resustituir.isEnabled()

    def test_boton_se_deshabilita_al_deseleccionar(self, form_audit, logs_variados):
        """Deseleccionar deja el botón deshabilitado."""
        form_audit.cargar_datos()
        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if data and data[1] == "SUSTITUIDA":
                form_audit.tabla.selectRow(row)
                break

        assert form_audit.btn_resustituir.isEnabled()
        form_audit.tabla.clearSelection()
        assert not form_audit.btn_resustituir.isEnabled()


# ============================================================================
# TESTS: Señal re_sustituir_solicitada
# ============================================================================


class TestAuditoriaSenal:
    def test_emite_guardia_id_correcto_al_pulsar(
        self, qtbot, form_audit, logs_variados
    ):
        """El botón emite la señal con el guardia_id de la fila seleccionada."""
        form_audit.cargar_datos()
        expected_id = None
        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if data and data[1] == "SUSTITUIDA":
                form_audit.tabla.selectRow(row)
                expected_id = data[0]
                break

        assert expected_id is not None
        received = []
        form_audit.re_sustituir_solicitada.connect(lambda gid: received.append(gid))
        form_audit.btn_resustituir.click()

        assert received == [expected_id]

    def test_no_emite_sin_seleccion(self, form_audit, logs_variados):
        """No emite señal si no hay fila seleccionada."""
        form_audit.cargar_datos()
        form_audit.tabla.clearSelection()

        received = []
        form_audit.re_sustituir_solicitada.connect(lambda gid: received.append(gid))
        form_audit.btn_resustituir.click()

        assert received == []


# ============================================================================
# TESTS: Filtros y contenido de tabla
# ============================================================================


class TestAuditoriaFiltros:
    def test_filtro_por_accion_sustituida_solo_muestra_sustituidas(
        self, form_audit, logs_variados
    ):
        """Filtrar por SUSTITUIDA solo muestra filas de ese tipo."""
        form_audit.combo_accion.setCurrentText("SUSTITUIDA")
        form_audit.cargar_datos()

        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            assert data is not None and data[1] == "SUSTITUIDA"

    def test_detalle_json_se_muestra_parseado(self, form_audit, logs_variados):
        """El campo detalle muestra el JSON expandido, no el texto crudo."""
        form_audit.combo_accion.setCurrentText("SUSTITUIDA")
        form_audit.cargar_datos()

        assert form_audit.tabla.rowCount() >= 1
        detalle_text = form_audit.tabla.item(0, 5).text()
        assert "{" not in detalle_text, "El JSON no debe mostrarse sin parsear"
        assert "origen" in detalle_text or "profesor_anterior" in detalle_text

    def test_label_total_refleja_cantidad(self, form_audit, logs_variados):
        """El label de total refleja el número de registros cargados."""
        form_audit.cargar_datos()
        total = form_audit.tabla.rowCount()
        assert str(total) in form_audit.label_total.text()

    def test_filtro_todas_muestra_todos_los_tipos(self, form_audit, logs_variados):
        """El filtro 'Todas' muestra registros de todos los tipos."""
        form_audit.combo_accion.setCurrentText("Todas")
        form_audit.cargar_datos()

        acciones = set()
        for row in range(form_audit.tabla.rowCount()):
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if data:
                acciones.add(data[1])

        assert len(acciones) > 1, "Con filtro 'Todas' deben aparecer varios tipos"
