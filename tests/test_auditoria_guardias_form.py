"""
Tests para AuditoriaGuardiasForm.

Cubre: botón Re-sustituir, filtros, detalle JSON, señal re_sustituir_solicitada y
la ventana de solo lectura que se abre desde Ajustes (GUA-UXI-009).
"""

import json
from datetime import date, datetime, timedelta

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QTableWidget

from infrastructure.database.models import GuardiaAuditLog, Profesor
from presentation.forms.auditoria_guardias_form import AuditoriaGuardiasForm

pytestmark = pytest.mark.ui


# ============================================================================
# FIXTURES
# ============================================================================


def _filtro(form, etiqueta):
    return next(f for f in form.listado.filtros if f.etiqueta == etiqueta).combo


def _visibles(tabla):
    return [r for r in range(tabla.rowCount()) if not tabla.isRowHidden(r)]


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
        """Filtrar por «Sustitución» solo deja a la vista filas de ese tipo."""
        form_audit.cargar_datos()
        _filtro(form_audit, "Acción").setCurrentText("⇄ Sustitución")

        visibles = _visibles(form_audit.tabla)
        assert len(visibles) == 1
        for row in visibles:
            data = form_audit.tabla.item(row, 0).data(Qt.ItemDataRole.UserRole)
            assert data is not None and data[1] == "SUSTITUIDA"

    def test_detalle_json_se_muestra_parseado(self, form_audit, logs_variados):
        """El campo detalle muestra el JSON expandido, no el texto crudo."""
        form_audit.cargar_datos()
        _filtro(form_audit, "Acción").setCurrentText("⇄ Sustitución")

        fila = _visibles(form_audit.tabla)[0]
        detalle_text = form_audit.tabla.item(fila, 5).text()
        assert "{" not in detalle_text, "El JSON no debe mostrarse sin parsear"
        assert "origen" in detalle_text or "profesor_anterior" in detalle_text

    def test_recuento_refleja_cantidad(self, form_audit, logs_variados):
        """El pie dice cuántos cambios hay."""
        form_audit.cargar_datos()
        assert form_audit.listado.recuento.text() == "4 cambios"

    def test_sin_filtros_muestra_todos_los_tipos(self, form_audit, logs_variados):
        form_audit.cargar_datos()

        acciones = {
            form_audit.tabla.item(r, 0).data(Qt.ItemDataRole.UserRole)[1]
            for r in _visibles(form_audit.tabla)
        }
        assert acciones == {"CREADA", "SUSTITUIDA", "ELIMINADA", "GENERADA_BULK"}


# ============================================================================
# TESTS: Desde Ajustes, solo lectura y patrón común de listado (GUA-UXI-009)
# ============================================================================


@pytest.fixture
def muchos_cambios(session, profesor_factory):
    prof = profesor_factory(nombre_completo="Ficticio, Profesor")
    ahora = datetime.now()
    session.add_all(
        GuardiaAuditLog(
            guardia_id=100 + i,
            accion="MODIFICADA" if i % 2 else "CREADA",
            profesor_id=prof.id,
            usuario="jefatura" if i % 3 else "otra_cuenta",
            timestamp=ahora - timedelta(hours=i),
        )
        for i in range(40)
    )
    session.commit()


class TestRegistroDesdeAjustes:
    @pytest.fixture
    def dialogo(self, qtbot, session, muchos_cambios):
        from presentation.forms.ajustes_form import AjustesForm

        ajustes = AjustesForm(session)
        qtbot.addWidget(ajustes)
        assert ajustes.registro_btn.text() == "Registro de cambios"
        dialogo = ajustes.crear_registro_de_cambios()
        assert dialogo.parent() is ajustes
        yield dialogo  # `ajustes` sigue vivo: es el padre del diálogo
        dialogo.close()

    def test_el_boton_de_ajustes_abre_el_registro(self, qtbot, session, dialogos_modales):
        from presentation.forms.ajustes_form import AjustesForm

        ajustes = AjustesForm(session)
        qtbot.addWidget(ajustes)
        ajustes.registro_btn.click()

        assert [d.titulo for d in dialogos_modales] == ["Registro de cambios en guardias"]

    def test_es_solo_de_lectura(self, dialogo):
        registro = dialogo.registro
        tabla = registro.tabla

        assert registro.solo_lectura
        assert tabla.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
        assert registro.btn_resustituir.isHidden()
        a_la_vista = {b.text() for b in dialogo.findChildren(QPushButton) if not b.isHidden()}
        assert a_la_vista == {"Limpiar filtros", "Cerrar"}
        tabla.selectRow(0)
        recibidas = []
        registro.re_sustituir_solicitada.connect(recibidas.append)
        registro._emitir_resustituir()
        assert recibidas == []

    def test_lleva_el_patron_comun_sin_paginacion(self, dialogo):
        registro = dialogo.registro
        listado = registro.listado
        tabla = registro.tabla

        assert listado.buscador.parent() is listado.barra
        assert {f.etiqueta for f in listado.filtros} == {"Acción", "Usuario"}
        assert listado.limpiar.text() == "Limpiar filtros"
        assert tabla.isSortingEnabled()
        assert not hasattr(listado, "por_pagina")
        assert listado.pie.findChildren(QPushButton) == []
        assert len(_visibles(tabla)) == 40
        assert listado.recuento.text() == "40 cambios"

    def test_buscador_filtros_y_limpiar(self, dialogo):
        registro = dialogo.registro
        listado = registro.listado
        tabla = registro.tabla
        assert not listado.limpiar.isEnabled()

        _filtro(registro, "Acción").setCurrentText("✎ Modificada")
        assert len(_visibles(tabla)) == 20
        _filtro(registro, "Usuario").setCurrentText("otra_cuenta")
        assert all(tabla.item(r, 4).text() == "otra_cuenta" for r in _visibles(tabla))
        listado.buscador.setText("115")
        assert [tabla.item(r, 2).text() for r in _visibles(tabla)] == ["115"]
        assert listado.limpiar.isEnabled()

        listado.limpiar.click()
        QApplication.processEvents()

        assert listado.buscador.text() == ""
        assert len(_visibles(tabla)) == 40
        assert not listado.limpiar.isEnabled()

    def test_limpiar_devuelve_el_periodo_de_serie(self, dialogo):
        registro = dialogo.registro
        hoy = date.today()
        registro.fecha_desde.setDate(hoy)
        assert registro.listado.limpiar.isEnabled()

        registro.listado.limpiar.click()
        QApplication.processEvents()

        assert registro.fecha_desde.date().toPyDate() == hoy - timedelta(days=30)
        assert len(_visibles(registro.tabla)) == 40

    def test_las_cabeceras_ordenan_por_fecha_y_numero_de_verdad(self, dialogo):
        tabla = dialogo.registro.tabla

        tabla.sortItems(0, Qt.SortOrder.AscendingOrder)
        assert tabla.item(0, 2).text() == "139"  # el más antiguo
        tabla.sortItems(2, Qt.SortOrder.AscendingOrder)
        assert [tabla.item(r, 2).text() for r in range(3)] == ["100", "101", "102"]
        tabla.sortItems(2, Qt.SortOrder.DescendingOrder)
        assert tabla.item(0, 2).text() == "139"

    def test_cada_etiqueta_pegada_a_su_control(self, dialogo):
        from PyQt6.QtWidgets import QLabel

        dialogo.resize(1500, 700)
        dialogo.show()
        QApplication.processEvents()
        barra = dialogo.registro.listado.barra
        etiquetas = [e for e in barra.findChildren(QLabel) if e.buddy() is not None]
        assert {e.text() for e in etiquetas} == {"Desde:", "Hasta:", "Acción:", "Usuario:"}
        for etiqueta in etiquetas:
            control = etiqueta.buddy()
            fin = etiqueta.mapTo(barra, etiqueta.rect().topLeft()).x() + etiqueta.sizeHint().width()
            inicio = control.mapTo(barra, control.rect().topLeft()).x()
            assert 0 <= inicio - fin <= 12, etiqueta.text()
        dialogo.close()
