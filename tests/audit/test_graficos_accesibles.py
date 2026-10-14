"""UXA-009 y UXA-014 — los gráficos dejan de ser rectángulos mudos.

Un `QPainter` no produce nada que un lector de pantalla pueda anunciar: el
gráfico de reparto de guardias era, para quien no lo ve, un hueco vacío. Además
sus rótulos se pintaban a 7 pt —unos 9 px— con «Arial» a secas, fuera del
alcance del ratchet visual, que sólo mira las hojas de estilo.
"""

import pytest

from presentation.widgets.bar_chart_widget import (
    TIPO_MINIMA,
    BarChartWidget,
    PieChartWidget,
    describir_serie,
)

DATOS_BARRAS = [("García, Ana", 12, ""), ("López, Juan", 9, "")]
DATOS_TARTA = [("Patio A", 30.0), ("Patio B", 10.0)]


def test_la_descripcion_lee_las_series(qapp):
    grafico = BarChartWidget(DATOS_BARRAS, titulo="Guardias por profesor")

    descripcion = grafico.accessibleDescription()
    assert "García, Ana: 12" in descripcion
    assert "López, Juan: 9" in descripcion


def test_el_titulo_es_el_nombre_accesible(qapp):
    grafico = BarChartWidget(DATOS_BARRAS, titulo="Guardias por profesor")

    assert grafico.accessibleName() == "Guardias por profesor"


def test_cambiar_los_datos_actualiza_la_descripcion(qapp):
    grafico = BarChartWidget(titulo="Reparto")

    grafico.set_datos(DATOS_BARRAS)

    assert "García, Ana: 12" in grafico.accessibleDescription()


def test_la_tarta_dice_los_porcentajes(qapp):
    grafico = PieChartWidget(DATOS_TARTA, titulo="Guardias por zona")

    descripcion = grafico.accessibleDescription()
    assert "Patio A: 75%" in descripcion
    assert "Patio B: 25%" in descripcion


def test_sin_datos_se_dice_que_no_hay(qapp):
    grafico = BarChartWidget(titulo="Reparto")

    assert "sin datos" in grafico.accessibleDescription()


def test_una_serie_larguisima_se_resume():
    """Dictar doscientos profesores uno a uno sería peor que no decir nada."""
    pares = [(f"Profesor {i}", i) for i in range(50)]

    texto = describir_serie("Reparto", pares, "Gráfico de barras")

    assert "50 series" in texto
    assert "y 38 más" in texto


def test_se_llega_al_grafico_con_el_tabulador(qapp):
    from PyQt6.QtCore import Qt

    grafico = BarChartWidget(DATOS_BARRAS, titulo="Reparto")

    assert grafico.focusPolicy() != Qt.FocusPolicy.NoFocus


def test_la_ayuda_emergente_dice_lo_mismo_que_el_texto_accesible(qapp):
    grafico = BarChartWidget(DATOS_BARRAS, titulo="Reparto")

    assert grafico.toolTip() == grafico.accessibleDescription()


@pytest.mark.parametrize("clase", [BarChartWidget, PieChartWidget])
def test_ningun_rotulo_baja_del_minimo_legible(clase):
    """7 pt en la leyenda y en los valores: por debajo de lo que se puede leer."""
    import inspect
    import re

    fuente = inspect.getsource(inspect.getmodule(clase))
    cuerpos = [int(m) for m in re.findall(r"_fuente\((?:TIPO_\w+|(\d+))", fuente) if m]
    assert all(c >= TIPO_MINIMA for c in cuerpos)
    assert 'QFont("Arial"' not in fuente


def test_los_graficos_usan_la_familia_del_sistema():
    """«Arial» no existe en muchos Linux ni es la familia de interfaz en Windows."""
    import inspect

    from presentation.widgets import bar_chart_widget

    fuente = inspect.getsource(bar_chart_widget._fuente)
    assert "familias_del_sistema" in fuente
