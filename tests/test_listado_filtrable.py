"""GUA-UXI-005: búsqueda, filtros que se recuerdan, orden y paginación en las tablas.

El patrón es el de la web de pedidos (`list-view-utils.js`) y el de Partes de salida:
buscador, filtros, «Limpiar filtros», cabeceras ordenables, 10 filas por página con
selector 5/10/15/20/50, pie «Mostrando 1–10 de N» con los extremos desactivados (no
ocultos) y la fila nueva resaltada.
"""

from datetime import date

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

from presentation.widgets.listado_filtrable import (
    Filtro,
    ListadoFiltrable,
    filas_visibles_seleccionadas,
    seleccionar_visibles,
    texto_recuento,
    ventana_paginas,
)
from utils.ui_helpers import pintar_tabla_vacia

pytestmark = pytest.mark.ui

TURNOS = ("Mañana", "Tarde")


def _tabla(filas: int) -> QTableWidget:
    tabla = QTableWidget(0, 3)
    tabla.setHorizontalHeaderLabels(["Nombre", "Turno", "Horas"])
    tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
    _llenar(tabla, filas)
    tabla.setSortingEnabled(True)
    tabla.sortItems(0, Qt.SortOrder.AscendingOrder)
    return tabla


def _llenar(tabla: QTableWidget, filas: int) -> None:
    ordenable = tabla.isSortingEnabled()
    tabla.setSortingEnabled(False)
    tabla.setRowCount(filas)
    for i in range(filas):
        nombre = QTableWidgetItem(f"Profesor {i:02d}")
        nombre.setData(Qt.ItemDataRole.UserRole, 100 + i)
        tabla.setItem(i, 0, nombre)
        tabla.setItem(i, 1, QTableWidgetItem(TURNOS[i % 2]))
        tabla.setItem(i, 2, QTableWidgetItem(str(i)))
    tabla.setSortingEnabled(ordenable)


def _visibles(tabla: QTableWidget) -> list[str]:
    return [tabla.item(r, 0).text() for r in range(tabla.rowCount()) if not tabla.isRowHidden(r)]


def _listado(tabla, clave="prueba", **kw) -> ListadoFiltrable:
    kw.setdefault("filtros", (Filtro.columna("Turno", 1),))
    return ListadoFiltrable(tabla, clave, entidad="profesores", **kw)


# --- Cálculos ---------------------------------------------------------------


def test_cinco_numeros_desde_la_actual_menos_dos():
    assert ventana_paginas(1, 10) == [1, 2, 3, 4, 5]
    assert ventana_paginas(6, 10) == [4, 5, 6, 7, 8]
    assert ventana_paginas(10, 10) == [8, 9, 10]
    assert ventana_paginas(1, 1) == [1]


def test_recuento_como_en_la_web_de_pedidos():
    assert texto_recuento(1, 10, 23, "profesores") == "Mostrando 1–10 de 23 profesores"
    assert texto_recuento(3, 10, 23, "profesores") == "Mostrando 21–23 de 23 profesores"
    assert texto_recuento(1, 10, 0, "profesores") == "Sin resultados"


# --- Paginación -------------------------------------------------------------


def test_diez_por_pagina_de_serie_y_pie_con_recuento(qapp):
    tabla = _tabla(23)
    listado = _listado(tabla)

    assert listado.por_pagina.currentData() == 10
    assert [listado.por_pagina.itemData(i) for i in range(listado.por_pagina.count())] == [
        5, 10, 15, 20, 50,
    ]
    assert len(_visibles(tabla)) == 10
    assert listado.recuento.text() == "Mostrando 1–10 de 23 profesores"
    assert listado.paginas == 3


def test_los_extremos_se_desactivan_pero_no_desaparecen(qapp):
    tabla = _tabla(23)
    listado = _listado(tabla)
    listado.pie.show()

    b = listado.botones
    assert not b["primera"].isEnabled() and not b["anterior"].isEnabled()
    assert b["siguiente"].isEnabled() and b["ultima"].isEnabled()
    assert all(not boton.isHidden() for boton in b.values())

    b["ultima"].click()
    assert listado.pagina == 3
    assert _visibles(tabla) == ["Profesor 20", "Profesor 21", "Profesor 22"]
    assert not b["siguiente"].isEnabled() and not b["ultima"].isEnabled()
    assert all(not boton.isHidden() for boton in b.values())
    assert [n.text() for n in listado.numeros if not n.isHidden()] == ["1", "2", "3"]
    assert [n.isChecked() for n in listado.numeros if not n.isHidden()] == [False, False, True]


def test_cambiar_las_filas_por_pagina_vuelve_a_la_primera(qapp):
    tabla = _tabla(23)
    listado = _listado(tabla)
    listado.ir(3)

    listado.por_pagina.setCurrentIndex(listado.por_pagina.findData(5))

    assert listado.pagina == 1
    assert len(_visibles(tabla)) == 5
    assert listado.paginas == 5


# --- Búsqueda y filtros -----------------------------------------------------


def test_la_busqueda_no_distingue_tildes_ni_mayusculas(qapp):
    tabla = _tabla(3)
    tabla.item(1, 0).setText("García López, Ana")
    listado = _listado(tabla)

    listado.buscador.setText("garcia ANA")

    assert _visibles(tabla) == ["García López, Ana"]
    assert listado.recuento.text() == "Mostrando 1–1 de 1 profesores"


def test_el_filtro_ofrece_los_valores_de_la_tabla_y_filtra(qapp):
    tabla = _tabla(6)
    listado = _listado(tabla)
    combo = listado.filtros[0].combo

    assert [combo.itemText(i) for i in range(combo.count())] == ["Todos", "Mañana", "Tarde"]
    combo.setCurrentText("Tarde")

    assert _visibles(tabla) == ["Profesor 01", "Profesor 03", "Profesor 05"]


def test_limpiar_filtros_lo_quita_todo_y_solo_se_activa_si_hay_algo(qapp):
    tabla = _tabla(6)
    listado = _listado(tabla)
    assert not listado.limpiar.isEnabled()

    listado.buscador.setText("Profesor 0")
    listado.filtros[0].combo.setCurrentText("Tarde")
    assert listado.limpiar.isEnabled()

    listado.limpiar.click()

    assert listado.buscador.text() == ""
    assert listado.filtros[0].combo.currentText() == "Todos"
    assert len(_visibles(tabla)) == 6
    assert not listado.limpiar.isEnabled()


def test_sin_resultados_lo_dice(qapp):
    tabla = _tabla(4)
    listado = _listado(tabla)

    listado.buscador.setText("nadie se llama así")

    assert _visibles(tabla) == []
    assert listado.recuento.text() == "Sin resultados"
    assert listado.paginas == 1


def test_la_fila_que_explica_la_tabla_vacia_no_se_esconde(qapp):
    tabla = _tabla(0)
    pintar_tabla_vacia(tabla, "Todavía no hay profesores")
    listado = _listado(tabla)
    listado.buscador.setText("x")

    assert not tabla.isRowHidden(0)
    assert listado.total == 0


# --- Lo que se recuerda -----------------------------------------------------


def test_busqueda_filtros_y_filas_por_pagina_se_recuerdan(qapp):
    primero = _listado(_tabla(30), clave="recordar")
    primero.buscador.setText("Profesor 2")
    primero.filtros[0].combo.setCurrentText("Tarde")
    primero.por_pagina.setCurrentIndex(primero.por_pagina.findData(5))

    tabla = _tabla(30)
    segundo = _listado(tabla, clave="recordar")

    assert segundo.buscador.text() == "Profesor 2"
    assert segundo.filtros[0].combo.currentText() == "Tarde"
    assert segundo.por_pagina.currentData() == 5
    assert _visibles(tabla) == ["Profesor 21", "Profesor 23", "Profesor 25", "Profesor 27", "Profesor 29"]


def test_el_filtro_recordado_espera_a_que_la_tabla_se_llene(qapp):
    _listado(_tabla(4), clave="espera").filtros[0].combo.setCurrentText("Tarde")

    tabla = QTableWidget(0, 3)
    tabla.setSortingEnabled(True)
    tabla.sortItems(0, Qt.SortOrder.AscendingOrder)
    listado = _listado(tabla, clave="espera")
    _llenar(tabla, 4)
    QApplication.processEvents()

    assert listado.filtros[0].combo.currentText() == "Tarde"
    assert _visibles(tabla) == ["Profesor 01", "Profesor 03"]


def test_el_orden_elegido_se_recuerda_y_sobrevive_a_la_recarga(qapp):
    tabla = _tabla(12)
    listado = _listado(tabla, clave="orden")
    tabla.sortItems(0, Qt.SortOrder.DescendingOrder)
    listado._guardar()

    # La vista recarga y vuelve a su orden de serie, como hace Profesores
    _llenar(tabla, 12)
    tabla.sortItems(0, Qt.SortOrder.AscendingOrder)
    QApplication.processEvents()
    assert tabla.item(0, 0).text() == "Profesor 11"

    otra = _tabla(12)
    _listado(otra, clave="orden")
    assert otra.item(0, 0).text() == "Profesor 11"


def test_las_preferencias_no_van_a_la_carpeta_de_datos_del_repositorio(qapp, tmp_path):
    from presentation.widgets import listado_filtrable

    assert listado_filtrable._ruta_de_preferencias().parent == tmp_path


# --- Fila nueva ---------------------------------------------------------------


def test_la_fila_nueva_sale_resaltada_y_en_su_pagina(qapp):
    tabla = _tabla(25)
    listado = _listado(tabla)

    listado.resaltar(123)  # «Profesor 23», en la página 3

    assert listado.pagina == 3
    fila = next(r for r in range(tabla.rowCount()) if tabla.item(r, 0).text() == "Profesor 23")
    assert not tabla.isRowHidden(fila)
    assert tabla.item(fila, 0).font().bold()
    assert tabla.item(fila, 0).background().style() != Qt.BrushStyle.NoBrush
    otra = next(r for r in range(tabla.rowCount()) if tabla.item(r, 0).text() == "Profesor 22")
    assert not tabla.item(otra, 0).font().bold()


def test_editar_lleva_a_su_pagina_sin_resaltar(qapp):
    tabla = _tabla(25)
    listado = _listado(tabla)

    listado.mostrar(112)

    assert listado.pagina == 2
    fila = next(r for r in range(tabla.rowCount()) if tabla.item(r, 0).text() == "Profesor 12")
    assert not tabla.item(fila, 0).font().bold()


# --- Seleccionar todo -------------------------------------------------------


def test_seleccionar_todo_no_coge_lo_que_no_se_ve(qapp):
    """`selectAll` de Qt selecciona también las filas ocultas: con un filtro
    puesto, Ctrl+A y Supr borraban registros que no estaban a la vista."""
    tabla = _tabla(23)
    _listado(tabla)

    tabla.selectAll()
    assert len({i.row() for i in tabla.selectionModel().selectedRows()}) == 23
    assert len(filas_visibles_seleccionadas(tabla)) == 10

    seleccionar_visibles(tabla)
    assert len({i.row() for i in tabla.selectionModel().selectedRows()}) == 10


# --- En las vistas ------------------------------------------------------------


def test_profesores_pagina_filtra_por_turno_y_resalta_el_nuevo(qapp, session, profesor_factory):
    from presentation.forms.profesor_form import ProfesorForm

    for i in range(12):
        profesor_factory(
            f"Apellido{i:02d}, Nombre",
            turno="mañana" if i % 2 else "tarde",
            email_corporativo=f"profe{i:02d}@example.com",
        )
    form = ProfesorForm(session)
    QApplication.processEvents()
    tabla = form.tabla_profesores

    assert len(_visibles(tabla)) == 10
    assert form.listado.recuento.text() == "Mostrando 1–10 de 12 profesores"
    turno = next(f for f in form.listado.filtros if f.etiqueta == "Turno").combo
    turno.setCurrentText("Tarde")
    assert len(_visibles(tabla)) == 6

    nuevo = profesor_factory("Zzz, Recién llegado", turno="tarde")
    form.cargar_profesores()
    form.listado.resaltar(nuevo.id)
    fila = next(r for r in range(tabla.rowCount()) if tabla.item(r, 0).text() == "Zzz, Recién llegado")
    assert not tabla.isRowHidden(fila)
    assert tabla.item(fila, 0).font().bold()
    form.close()


def test_profesores_ctrl_a_solo_selecciona_lo_filtrado(qapp, session, profesor_factory):
    from presentation.forms.profesor_form import ProfesorForm

    for i in range(4):
        profesor_factory(f"Profe{i}, Uno", turno="mañana" if i % 2 else "tarde")
    form = ProfesorForm(session)
    QApplication.processEvents()
    form.busqueda_input.setText("Profe1")

    form.seleccionar_todos()

    assert filas_visibles_seleccionadas(form.tabla_profesores) == [
        r for r in range(form.tabla_profesores.rowCount()) if not form.tabla_profesores.isRowHidden(r)
    ]
    assert len(form.tabla_profesores.selectionModel().selectedRows()) == 1
    form.close()


def test_estado_de_la_zona_segun_sus_fechas(qapp):
    from presentation.forms.zona_form import estado_de_la_zona

    tabla = QTableWidget(4, 5)
    for fila, (inicio, fin) in enumerate(
        [("-", "-"), ("01/09/2026", "30/06/2027"), ("01/01/2027", "-"), ("-", "01/10/2026")]
    ):
        tabla.setItem(fila, 3, QTableWidgetItem(inicio))
        tabla.setItem(fila, 4, QTableWidgetItem(fin))
    hoy = date(2026, 10, 16)

    assert [estado_de_la_zona(tabla, f, hoy) for f in range(4)] == [
        "Todo el curso", "Vigente", "Programada", "Terminada",
    ]
