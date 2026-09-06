"""UXA-010 — que todo el texto llegue al mínimo AA sobre su fondo.

Los tokens se fueron corrigiendo de uno en uno (el primario en v5.58.0, los
verdes de acento después), pero nadie comprobaba el conjunto: cada pareja
color/fondo se validaba a ojo cuando se tocaba. Aquí se miden todas de golpe,
con la fórmula de WCAG, y el test cae si alguien introduce una que no llega.
"""

import pytest

from presentation.theme.tokens import Colors

#: Texto normal. El texto grande (≥18 pt o ≥14 pt en negrita) se conforma con 3.
MINIMO_TEXTO = 4.5
#: Bordes y demás elementos que no son texto pero delimitan un control.
MINIMO_NO_TEXTO = 3.0


def _luminancia(hexadecimal: str) -> float:
    canales = (int(hexadecimal[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def lineal(valor: float) -> float:
        return valor / 12.92 if valor <= 0.03928 else ((valor + 0.055) / 1.055) ** 2.4

    r, g, b = (lineal(c) for c in canales)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(frente: str, fondo: str) -> float:
    a, b = _luminancia(frente), _luminancia(fondo)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


TEXTO_SOBRE_FONDO = [
    ("TEXT_PRIMARY", "BACKGROUND"),
    ("TEXT_PRIMARY", "SURFACE"),
    ("TEXT_SECONDARY", "BACKGROUND"),
    ("TEXT_SECONDARY", "SURFACE"),
    ("PRIMARY", "BACKGROUND"),
    ("PRIMARY_DARK", "BACKGROUND"),
    ("PRIMARY", "PRIMARY_LIGHT"),
    ("SUCCESS", "BACKGROUND"),
    ("SUCCESS", "SUCCESS_BG"),
    ("SUCCESS_DARK", "SUCCESS_BG"),
    ("WARNING", "BACKGROUND"),
    ("WARNING", "WARNING_BG"),
    ("WARNING", "WARNING_BG_ALT"),
    ("ERROR", "BACKGROUND"),
    ("ERROR_ON_BG", "ERROR_BG"),
    ("INFO", "BACKGROUND"),
    ("INFO", "INFO_BG"),
    ("SECONDARY", "BACKGROUND"),
    ("SECONDARY_HOVER", "BACKGROUND"),
    ("TEXT_ON_PRIMARY", "PRIMARY"),
    ("TEXT_ON_PRIMARY", "PRIMARY_DARK"),
    ("TEXT_ON_PRIMARY", "SUCCESS"),
    ("TEXT_ON_PRIMARY", "ERROR"),
    ("TEXT_ON_PRIMARY", "SECONDARY"),
    ("SIDEBAR_TEXT", "SIDEBAR_BG"),
    ("SIDEBAR_TEXT", "SIDEBAR_HOVER"),
    ("TERMINAL_TEXT", "TERMINAL_BG"),
    ("TERMINAL_ACCENT", "TERMINAL_BG"),
]

NO_TEXTO_SOBRE_FONDO = [
    ("FOCUS_RING", "BACKGROUND"),
    ("FOCUS_RING", "SURFACE"),
    ("FOCUS_RING", "FOCUS_HALO"),
    ("BORDER_CONTROL", "BACKGROUND"),
    ("BORDER_CONTROL", "SURFACE"),
    ("ERROR", "ERROR_BG"),
]


@pytest.mark.parametrize("frente,fondo", TEXTO_SOBRE_FONDO)
def test_el_texto_llega_al_minimo_aa(frente, fondo):
    medido = contraste(getattr(Colors, frente), getattr(Colors, fondo))
    assert medido >= MINIMO_TEXTO, f"{frente} sobre {fondo}: {medido:.2f}:1"


@pytest.mark.parametrize("frente,fondo", NO_TEXTO_SOBRE_FONDO)
def test_los_bordes_y_el_foco_se_distinguen(frente, fondo):
    medido = contraste(getattr(Colors, frente), getattr(Colors, fondo))
    assert medido >= MINIMO_NO_TEXTO, f"{frente} sobre {fondo}: {medido:.2f}:1"


def test_el_borde_de_los_campos_no_es_el_decorativo():
    """Con 1,3:1 el recuadro de un campo de texto era casi invisible."""
    qss = (
        __import__("pathlib").Path(__file__).resolve().parents[2]
        / "src" / "presentation" / "theme" / "light.qss"
    ).read_text(encoding="utf-8")
    inicio = qss.index("QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {")
    bloque = qss[inicio : qss.index("}", inicio)]
    assert "@BORDER_CONTROL@" in bloque


def test_el_gris_de_deshabilitado_queda_fuera_a_proposito():
    """WCAG exime a los controles inactivos, pero conviene dejarlo por escrito."""
    assert contraste(Colors.TEXT_DISABLED, Colors.BACKGROUND) < MINIMO_TEXTO
