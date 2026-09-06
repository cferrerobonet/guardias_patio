"""Dos defectos vistos por CarlosFB sobre la aplicación en marcha (2026-09-06).

1. En Profesores y en Calendario, la última fila —los botones de Nuevo, Editar
   y Eliminar, o la leyenda— quedaba pegada al borde inferior de la ventana y se
   veía cortada. Ni el envoltorio de vista ni las vistas dejaban margen abajo.

2. La ayuda emergente de los botones del menú lateral salía en texto casi negro
   sobre fondo oscuro. `QToolTip` es un `QWidget`, así que le llegaba el `color`
   de la regla global, pero el fondo lo ponía el sistema.
"""

import re
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QScrollArea

RAIZ = Path(__file__).resolve().parents[2]
QSS = RAIZ / "src" / "presentation" / "theme" / "light.qss"


def _luminancia(hexadecimal: str) -> float:
    canales = (int(hexadecimal[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def lineal(v: float) -> float:
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (lineal(c) for c in canales)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contraste(frente: str, fondo: str) -> float:
    a, b = _luminancia(frente), _luminancia(fondo)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


# ---------------------------------------------------------------------------
# El contenido no puede quedar pegado al borde inferior
# ---------------------------------------------------------------------------


def test_el_envoltorio_deja_aire_por_debajo():
    from presentation.ventana_principal import ContentWrapper

    assert ContentWrapper.MARGEN_INFERIOR > 0


def test_ninguna_vista_llega_al_borde_de_la_ventana(qapp, session):
    from PyQt6.QtWidgets import QLabel

    from presentation.ventana_principal import ContentWrapper

    contenido = QLabel("una vista cualquiera")
    envoltorio = ContentWrapper("Prueba", contenido)
    envoltorio.resize(900, 600)
    qapp.processEvents()

    scroll = envoltorio.findChild(QScrollArea)
    assert scroll is not None
    fondo_del_scroll = scroll.geometry().bottom()
    assert fondo_del_scroll < envoltorio.height() - 1


def test_la_vista_sigue_pudiendo_desplazarse(qapp):
    """El margen no puede haberse comido la barra de desplazamiento."""
    from PyQt6.QtWidgets import QLabel

    from presentation.ventana_principal import ContentWrapper

    alto = QLabel("contenido muy alto")
    alto.setMinimumHeight(3000)
    envoltorio = ContentWrapper("Prueba", alto)
    envoltorio.resize(900, 400)
    qapp.processEvents()

    scroll = envoltorio.findChild(QScrollArea)
    assert scroll.widgetResizable() is True
    assert scroll.verticalScrollBar().maximum() > 0


# ---------------------------------------------------------------------------
# La ayuda emergente tiene que leerse
# ---------------------------------------------------------------------------


def _regla_de_tooltip(hoja: str) -> dict:
    bloque = hoja[hoja.index("QToolTip") :]
    bloque = bloque[: bloque.index("}")]
    return dict(re.findall(r"([a-z-]+)\s*:\s*([^;]+);", bloque))


@pytest.mark.parametrize("cual", ["hoja_del_sistema", "hoja_de_la_ventana"])
def test_la_ayuda_emergente_fija_fondo_y_texto(cual):
    """Hay dos hojas y la de la ventana pisa a la de la aplicación: en las dos."""
    if cual == "hoja_del_sistema":
        from presentation.theme.hoja_de_estilos import construir_hoja_de_estilos

        hoja = construir_hoja_de_estilos()
    else:
        from presentation.themes.tema_aplicacion import get_complete_stylesheet

        hoja = get_complete_stylesheet()

    assert "QToolTip" in hoja, "sin regla propia hereda el color y no el fondo"
    regla = _regla_de_tooltip(hoja)
    assert "background-color" in regla
    assert "color" in regla


def test_el_texto_de_la_ayuda_contrasta_con_su_fondo():
    from presentation.theme.tokens import Colors

    assert _contraste(Colors.TEXT_ON_PRIMARY, Colors.TEXT_PRIMARY) >= 4.5


def test_los_botones_del_menu_lateral_llevan_ayuda_al_plegarse(qapp, session):
    """Plegado sólo se ven los iconos: sin la ayuda no se sabe qué es cada uno."""
    import inspect

    from presentation.components.menu_lateral import SidebarMenu

    fuente = inspect.getsource(SidebarMenu.toggle_collapse)
    assert "setToolTip" in fuente
