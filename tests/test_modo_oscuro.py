"""Modo oscuro: traducción de colores al aplicar las hojas y los iconos."""

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import QLabel

from presentation.theme import modo_oscuro as mo


def _luz(color: str) -> float:
    return QColor(color).lightnessF()


def test_fondos_claros_pasan_a_oscuros_y_textos_oscuros_a_claros():
    hoja = mo.traducir_hoja(
        "QLabel { background-color: #FFFFFF; color: #1F2937; border: 1px solid #E1E4E8; }"
    )
    fondo = hoja.split("background-color: ")[1][:7]
    texto = hoja.split("color: ")[2][:7]
    borde = hoja.split("solid ")[1][:7]
    assert _luz(fondo) < 0.2
    assert _luz(texto) > 0.8
    assert _luz(borde) < 0.4


def test_acentos_blancos_translucidos_y_selectores_se_respetan():
    hoja = (
        "QPushButton#menuButton:hover { background-color: #0E5FA8; color: white; }\n"
        "QWidget { background: rgba(255, 255, 255, 0.10); }"
    )
    traducida = mo.traducir_hoja(hoja)
    assert "#menuButton:hover" in traducida
    assert "#0E5FA8" in traducida.upper()
    assert "color: #FFFFFF" in traducida
    assert "rgba(255, 255, 255, 0.10)" in traducida


def test_el_widget_guarda_la_hoja_clara_y_aplica_la_oscura(qtbot, monkeypatch):
    etiqueta = QLabel()
    qtbot.addWidget(etiqueta)
    hoja = "QLabel { background: #FFFFFF; color: #111827; }"

    monkeypatch.setattr(mo, "_oscuro", True)
    mo._hoja_de_widget(etiqueta, hoja)
    assert etiqueta.property(mo._PROPIEDAD) == hoja
    assert "#FFFFFF" not in etiqueta.styleSheet()

    monkeypatch.setattr(mo, "_oscuro", False)
    mo._hoja_de_widget(etiqueta, etiqueta.property(mo._PROPIEDAD))
    assert etiqueta.styleSheet() == hoja


def test_el_icono_se_repinta_con_el_color_del_modo(qtbot, monkeypatch):
    colores = []

    def crear(color):
        colores.append(color)
        pixmap = QPixmap(8, 8)
        pixmap.fill(QColor(color))
        return QIcon(pixmap)

    icono = mo.icono_segun_modo(crear, "#424242")
    monkeypatch.setattr(mo, "_oscuro", False)
    claro = icono.pixmap(QSize(8, 8)).toImage().pixelColor(4, 4)
    monkeypatch.setattr(mo, "_oscuro", True)
    oscuro = icono.pixmap(QSize(8, 8)).toImage().pixelColor(4, 4)

    assert colores[0] == "#424242"
    assert claro.lightnessF() < 0.3 < 0.7 < oscuro.lightnessF()


def test_pintar_a_mano_solo_cambia_en_oscuro(monkeypatch):
    monkeypatch.setattr(mo, "_oscuro", False)
    assert mo.color_fondo("#F9FAFB").name() == "#f9fafb"
    monkeypatch.setattr(mo, "_oscuro", True)
    assert mo.color_fondo("#F9FAFB").lightnessF() < 0.2
    assert mo.color_texto("#374151").lightnessF() > 0.7
