"""GUA-UXI-005: búsqueda, filtros que se recuerdan y orden en las tablas.

Buscador, filtros, «Limpiar filtros», cabeceras ordenables, recuento «N de M» y la
fila nueva resaltada y a la vista. Sin paginación por decisión de CarlosFB
(2026-10-17): se ven todas las filas que pasan los filtros. Las etiquetas de los
filtros van pegadas a su desplegable.
"""

from datetime import date

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QComboBox, QPushButton, QTableWidget, QTableWidgetItem

from presentation.widgets.listado_filtrable import (
    Filtro,
    ListadoFiltrable,
    filas_visibles_seleccionadas,
    seleccionar_visibles,
    texto_recuento,
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


def test_recuento_de_lo_que_se_ve():
    assert texto_recuento(23, 23, "profesores") == "23 profesores"
    assert texto_recuento(5, 23, "profesores") == "5 de 23 profesores"
    assert texto_recuento(0, 23, "profesores") == "Sin resultados"


# --- Sin paginación ---------------------------------------------------------


def test_sin_paginacion_se_ven_todas_las_filas(qapp):
    tabla = _tabla(60)
    listado = _listado(tabla)

    assert len(_visibles(tabla)) == 60
    assert listado.total == 60
    assert listado.recuento.text() == "60 profesores"
    assert not hasattr(listado, "por_pagina")
    assert not hasattr(listado, "ir")
    assert listado.pie.findChildren(QPushButton) == []
    assert listado.barra.findChildren(QComboBox) == [listado.filtros[0].combo]


def test_con_filtro_se_ven_todas_las_que_coinciden(qapp):
    tabla = _tabla(60)
    listado = _listado(tabla)

    listado.filtros[0].combo.setCurrentText("Tarde")

    assert len(_visibles(tabla)) == 30
    assert listado.recuento.text() == "30 de 60 profesores"
    listado.buscador.setText("5")
    assert len(_visibles(tabla)) == 10
    assert listado.recuento.text() == "10 de 60 profesores"


def test_las_filas_por_pagina_de_antes_no_estorban(qapp):
    from presentation.widgets.listado_filtrable import guardar_preferencias, leer_preferencias

    guardar_preferencias("antigua", {"por_pagina": 5, "filtros": {"turno": "Tarde"}})
    tabla = _tabla(30)
    listado = _listado(tabla, clave="antigua")

    assert len(_visibles(tabla)) == 15
    listado.buscador.setText("Profesor")
    assert "por_pagina" not in leer_preferencias("antigua")


# --- Búsqueda y filtros -----------------------------------------------------


def test_la_busqueda_no_distingue_tildes_ni_mayusculas(qapp):
    tabla = _tabla(3)
    tabla.item(1, 0).setText("García López, Ana")
    listado = _listado(tabla)

    listado.buscador.setText("garcia ANA")

    assert _visibles(tabla) == ["García López, Ana"]
    assert listado.recuento.text() == "1 de 3 profesores"


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


def test_la_fila_que_explica_la_tabla_vacia_no_se_esconde(qapp):
    tabla = _tabla(0)
    pintar_tabla_vacia(tabla, "Todavía no hay profesores")
    listado = _listado(tabla)
    listado.buscador.setText("x")

    assert not tabla.isRowHidden(0)
    assert listado.total == 0


# --- Lo que se recuerda -----------------------------------------------------


def test_busqueda_y_filtros_se_recuerdan(qapp):
    primero = _listado(_tabla(30), clave="recordar")
    primero.buscador.setText("Profesor 2")
    primero.filtros[0].combo.setCurrentText("Tarde")

    tabla = _tabla(30)
    segundo = _listado(tabla, clave="recordar")

    assert segundo.buscador.text() == "Profesor 2"
    assert segundo.filtros[0].combo.currentText() == "Tarde"
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


def _en_la_vista(tabla: QTableWidget, fila: int) -> bool:
    rect = tabla.visualItemRect(tabla.item(fila, 0))
    return tabla.viewport().rect().intersects(rect)


def _tabla_baja(filas: int) -> QTableWidget:
    tabla = _tabla(filas)
    tabla.resize(400, 200)
    tabla.show()
    QApplication.processEvents()
    return tabla


def test_la_fila_nueva_sale_resaltada_y_a_la_vista(qapp):
    tabla = _tabla_baja(60)
    listado = _listado(tabla)
    fila = next(r for r in range(tabla.rowCount()) if tabla.item(r, 0).text() == "Profesor 55")
    assert not _en_la_vista(tabla, fila)

    listado.resaltar(155)
    QApplication.processEvents()

    assert len(_visibles(tabla)) == 60
    assert not tabla.isRowHidden(fila)
    assert _en_la_vista(tabla, fila)
    assert tabla.item(fila, 0).font().bold()
    assert tabla.item(fila, 0).background().style() != Qt.BrushStyle.NoBrush
    otra = next(r for r in range(tabla.rowCount()) if tabla.item(r, 0).text() == "Profesor 54")
    assert not tabla.item(otra, 0).font().bold()
    tabla.close()


def test_editar_la_lleva_a_la_vista_sin_resaltar(qapp):
    tabla = _tabla_baja(60)
    listado = _listado(tabla)

    listado.mostrar(148)
    QApplication.processEvents()

    fila = next(r for r in range(tabla.rowCount()) if tabla.item(r, 0).text() == "Profesor 48")
    assert _en_la_vista(tabla, fila)
    assert not tabla.item(fila, 0).font().bold()
    tabla.close()


# --- Seleccionar todo -------------------------------------------------------


def test_seleccionar_todo_no_coge_lo_que_no_se_ve(qapp):
    """`selectAll` de Qt selecciona también las filas ocultas: con un filtro
    puesto, Ctrl+A y Supr borraban registros que no estaban a la vista."""
    tabla = _tabla(23)
    listado = _listado(tabla)
    listado.filtros[0].combo.setCurrentText("Tarde")

    tabla.selectAll()
    assert len({i.row() for i in tabla.selectionModel().selectedRows()}) == 23
    assert len(filas_visibles_seleccionadas(tabla)) == 11

    seleccionar_visibles(tabla)
    assert len({i.row() for i in tabla.selectionModel().selectedRows()}) == 11


# --- En las vistas ------------------------------------------------------------


def test_profesores_sin_paginas_filtra_por_turno_y_resalta_el_nuevo(qapp, session, profesor_factory):
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

    assert len(_visibles(tabla)) == 12
    assert form.listado.recuento.text() == "12 profesores"
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


# --- Maquetación: cada etiqueta pegada a su desplegable ---------------------


def _distancias(listado) -> dict[str, int]:
    """Hueco horizontal entre el final del texto de cada etiqueta y su desplegable.

    Antes la fila repartía el ancho sobrante y la etiqueta de Profesores medía
    257 px para un texto de 37: «Turno:» quedaba a más de 200 px de su control.
    """
    huecos = {}
    for etiqueta, filtro in zip(listado.etiquetas, listado.filtros):
        combo = filtro.combo
        assert etiqueta.buddy() is combo
        izquierda = etiqueta.mapTo(listado.barra, etiqueta.rect().topLeft()).x()
        fin = izquierda + etiqueta.sizeHint().width()
        inicio = combo.mapTo(listado.barra, combo.rect().topLeft()).x()
        huecos[filtro.etiqueta] = inicio - fin
        assert etiqueta.width() <= etiqueta.sizeHint().width() + 2, filtro.etiqueta
    return huecos


def _mostrar_ancha(form) -> None:
    form.resize(1600, 900)
    form.show()
    QApplication.processEvents()


def test_profesores_cada_etiqueta_pegada_a_su_desplegable(qapp, session, profesor_factory):
    from presentation.forms.profesor_form import ProfesorForm

    profesor_factory("Apellido, Nombre", turno="tarde", email_corporativo="profe@example.com")
    form = ProfesorForm(session)
    _mostrar_ancha(form)

    huecos = _distancias(form.listado)
    assert set(huecos) == {"Turno", "Tutor"}
    assert all(0 <= h <= 12 for h in huecos.values()), huecos
    form.close()


def test_zonas_cada_etiqueta_pegada_a_su_desplegable(qapp, session):
    from presentation.forms.zona_form import ZonaForm

    form = ZonaForm(session)
    _mostrar_ancha(form)

    huecos = _distancias(form.listado)
    assert set(huecos) == {"Estado"}
    assert all(0 <= h <= 12 for h in huecos.values()), huecos
    buscador = form.listado.buscador
    assert buscador.width() > form.listado.filtros[0].combo.width()
    form.close()


def test_sustituciones_cada_etiqueta_pegada_a_su_desplegable(qapp):
    from PyQt6.QtWidgets import QVBoxLayout, QWidget

    tabla = _tabla(4)
    listado = _listado(tabla, filtros=(Filtro.columna("Turno", 1), Filtro.columna("Horas", 2)))
    ventana = QWidget()
    capa = QVBoxLayout(ventana)
    capa.addWidget(listado.barra)
    capa.addWidget(tabla)
    _mostrar_ancha(ventana)

    assert all(0 <= h <= 12 for h in _distancias(listado).values())
    ventana.close()
