"""UXA-008 — que una tabla se pueda usar sin ver la pantalla.

De las trece tablas de la aplicación, sólo Profesores, Zonas y Perfiles decían
qué contenían. Las demás eran, para un lector de pantalla, «tabla» y nada más.
Tampoco se podían ordenar por la cabecera ni distinguían «vacía» de «aún no ha
cargado»: las dos cosas se ven en blanco.
"""

import re
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QTableWidget

from utils.ui_helpers import dotar_de_contrato, llenando_tabla, pintar_tabla_vacia

RAIZ = Path(__file__).resolve().parents[2]
PRES = RAIZ / "src" / "presentation"


def test_el_contrato_pone_nombre_y_descripcion(qapp):
    tabla = QTableWidget(0, 3)

    dotar_de_contrato(tabla, "Cursos escolares", "Los cursos dados de alta")

    assert tabla.accessibleName() == "Cursos escolares"
    assert tabla.accessibleDescription() == "Los cursos dados de alta"


def test_la_cabecera_tambien_se_nombra(qapp):
    tabla = QTableWidget(0, 3)

    dotar_de_contrato(tabla, "Cursos escolares")

    assert "cursos escolares" in tabla.horizontalHeader().accessibleName()


def test_el_orden_no_se_activa_por_su_cuenta(qapp):
    """Activarlo obliga a llenar dentro de `llenando_tabla`; no puede ser el defecto."""
    tabla = QTableWidget(0, 3)

    dotar_de_contrato(tabla, "Cursos escolares")

    assert tabla.isSortingEnabled() is False


def test_llenar_con_el_orden_activo_no_baraja_las_filas(qapp):
    """Qt recoloca a cada `setItem`: sin la guarda, las celdas acaban cruzadas."""
    from PyQt6.QtWidgets import QTableWidgetItem

    tabla = QTableWidget(0, 2)
    dotar_de_contrato(tabla, "Registros", ordenable=True)

    with llenando_tabla(tabla):
        tabla.setRowCount(3)
        for fila, (fecha, quien) in enumerate(
            [("03/01", "Carlos"), ("01/01", "Ana"), ("02/01", "Berta")]
        ):
            tabla.setItem(fila, 0, QTableWidgetItem(fecha))
            tabla.setItem(fila, 1, QTableWidgetItem(quien))

    parejas = {tabla.item(f, 0).text(): tabla.item(f, 1).text() for f in range(3)}
    assert parejas == {"03/01": "Carlos", "01/01": "Ana", "02/01": "Berta"}
    assert tabla.isSortingEnabled() is True


def test_la_guarda_devuelve_el_orden_como_estaba(qapp):
    tabla = QTableWidget(0, 2)

    with llenando_tabla(tabla):
        pass

    assert tabla.isSortingEnabled() is False


def test_una_tabla_vacia_lo_dice(qapp):
    tabla = QTableWidget(0, 4)

    assert pintar_tabla_vacia(tabla, "No hay nada todavía") is True
    assert tabla.item(0, 0).text() == "No hay nada todavía"
    assert tabla.columnSpan(0, 0) == 4


def test_una_tabla_con_filas_se_queda_como_esta(qapp):
    from PyQt6.QtWidgets import QTableWidgetItem

    tabla = QTableWidget(1, 2)
    tabla.setItem(0, 0, QTableWidgetItem("dato"))

    assert pintar_tabla_vacia(tabla, "No hay nada") is False
    assert tabla.item(0, 0).text() == "dato"


def test_el_mensaje_de_vacio_no_se_puede_editar(qapp):
    from PyQt6.QtCore import Qt

    tabla = QTableWidget(0, 2)
    pintar_tabla_vacia(tabla, "No hay nada")

    assert not tabla.item(0, 0).flags() & Qt.ItemFlag.ItemIsEditable


TABLAS_SIN_CONTRATO_PERMITIDAS = {
    # El calendario pinta sus propias celdas y ya se anuncia como vista.
}


def test_ninguna_tabla_se_queda_sin_presentarse():
    """Ratchet: cada `QTableWidget()` nuevo tiene que decir qué contiene."""
    sin_nombre = []
    for ruta in PRES.rglob("*.py"):
        if "__pycache__" in ruta.parts:
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        creadas = len(re.findall(r"= QTableWidget\(", texto))
        if not creadas:
            continue
        presentadas = texto.count("dotar_de_contrato(") + len(
            re.findall(r"\.setAccessibleName\(", texto)
        )
        if presentadas < creadas and ruta.name not in TABLAS_SIN_CONTRATO_PERMITIDAS:
            sin_nombre.append(ruta.name)
    assert sin_nombre == [], f"Tablas sin presentarse en: {sin_nombre}"


@pytest.mark.parametrize(
    "modulo,atributo,nombre",
    [
        ("presentation.widgets.gestion_cursos_widget", "tabla_cursos", "Cursos escolares"),
        ("presentation.widgets.panel_estadisticas", "tabla_zonas", "Reparto por zona"),
    ],
)
def test_las_tablas_concretas_llevan_su_nombre(modulo, atributo, nombre):
    import importlib
    import inspect

    fuente = inspect.getsource(importlib.import_module(modulo))
    assert f'"{nombre}"' in fuente
    assert f"self.{atributo}," in fuente
