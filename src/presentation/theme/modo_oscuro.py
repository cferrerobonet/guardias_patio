"""Modo oscuro que sigue al del sistema operativo.

La aplicación está diseñada en claro: sus colores viven en `tokens.py`, en
`light.qss` y en decenas de hojas de estilo en línea. Con el sistema en oscuro,
Qt pintaba oscuro lo que no tenía estilo y la hoja dejaba texto oscuro sobre
esos fondos: zonas negras y pantallas ilegibles.

En vez de duplicar cada color, en modo oscuro se traduce al aplicarse, según
para qué se usa: los fondos y bordes claros pasan a oscuros, los textos oscuros
a claros, y los colores de acento (botones, avisos) se conservan. Las hojas se
guardan en claro en cada widget, así que si el sistema cambia de modo con la
aplicación abierta se vuelven a aplicar en el nuevo.

Sin botón para cambiarlo: manda el sistema. `GUARDIAS_TEMA=oscuro|claro` lo
fuerza, para pruebas.
"""

from __future__ import annotations

import colorsys
import os
import re
import sys
from functools import lru_cache

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QGuiApplication, QIcon, QIconEngine, QPalette
from PyQt6.QtWidgets import QApplication, QWidget

from presentation.theme.tokens import BORDES_OSCUROS, FONDOS_OSCUROS, TEXTOS_OSCUROS, Colors

_PROPIEDAD = "hojaDeEstiloClara"

_oscuro = False
_instalado = False
_hoja_app = ""
_estilo_original = ""
_poner_hoja_widget = QWidget.setStyleSheet
_poner_hoja_app = QApplication.setStyleSheet

_NOMBRES = {"white": "#FFFFFF", "black": "#000000"}
_COLOR = re.compile(
    r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b|rgba?\([^)]*\)|\b(?:white|black)\b",
    re.IGNORECASE,
)
_DECLARACION = re.compile(r"(?<![\w-])([a-z][a-z-]*)(\s*:\s*)([^;{}]*)")


def es_oscuro() -> bool:
    return _oscuro


# --------------------------------------------------------------------------
# Traducción de colores
# --------------------------------------------------------------------------


def _hls(color: str) -> tuple[float, float, float]:
    c = QColor(color)
    return colorsys.rgb_to_hls(c.redF(), c.greenF(), c.blueF())


def _hex(h: float, luz: float, s: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, luz)), max(0.0, min(1.0, s)))
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


_FONDOS, _TEXTOS, _BORDES = FONDOS_OSCUROS, TEXTOS_OSCUROS, BORDES_OSCUROS


def _es_acento(luz: float, s: float) -> bool:
    return s >= 0.3 and 0.15 < luz <= 0.85


@lru_cache(maxsize=2048)
def fondo(color: str) -> str:
    """Un fondo claro pasa a oscuro; uno de acento se oscurece para el texto claro."""
    if color.upper() in _FONDOS:
        return _FONDOS[color.upper()]
    h, luz, s = _hls(color)
    if _es_acento(luz, s):
        return _hex(h, min(luz, 0.42), s)
    if luz > 0.5:
        return _hex(h, 0.11 + (1 - luz) * 0.62, s * 0.5)
    return _hex(h, luz, s)


@lru_cache(maxsize=2048)
def texto(color: str) -> str:
    """Un texto oscuro pasa a claro; uno claro (blanco sobre acento) se queda."""
    if color.upper() in _TEXTOS:
        return _TEXTOS[color.upper()]
    h, luz, s = _hls(color)
    if luz < 0.55:
        return _hex(h, 1 - luz * 0.75, s)
    return _hex(h, luz, s)


@lru_cache(maxsize=2048)
def borde(color: str) -> str:
    if color.upper() in _BORDES:
        return _BORDES[color.upper()]
    h, luz, s = _hls(color)
    if _es_acento(luz, s):
        return _hex(h, luz, s)
    if luz > 0.5:
        return _hex(h, 0.2 + (1 - luz) * 0.6, s * 0.5)
    return _hex(h, luz, s)


def _uso(propiedad: str):
    if propiedad in ("color", "selection-color") or propiedad.endswith("-text-color"):
        return texto
    if "background" in propiedad:
        return fondo
    return borde


def _traducir_color(valor: str, regla) -> str:
    original = _NOMBRES.get(valor.lower(), valor)
    if original.lower().startswith("rgb"):
        partes = [p.strip() for p in original[original.index("(") + 1 : -1].split(",")]
        try:
            numeros = [float(p) for p in partes]
        except ValueError:
            return valor
        # Los velos translúcidos (sombras, realces) funcionan igual en los dos modos.
        if len(numeros) not in (3, 4) or (len(numeros) == 4 and numeros[3] not in (1, 255)):
            return valor
        color = QColor(*(int(n) for n in numeros[:3]))
    else:
        color = QColor(original)
    if not color.isValid():
        return valor
    return regla(color.name())


@lru_cache(maxsize=4096)
def traducir_hoja(hoja: str) -> str:
    """La hoja de estilos, con cada color traducido según su propiedad."""
    if not hoja:
        return hoja

    def declaracion(m):
        regla = _uso(m.group(1))
        valor = _COLOR.sub(lambda c: _traducir_color(c.group(0), regla), m.group(3))
        return m.group(1) + m.group(2) + valor

    return _DECLARACION.sub(declaracion, hoja)


def color_fondo(color) -> QColor:
    """Para pintar a mano (QPainter, celdas de tabla) un fondo."""
    c = QColor(color)
    return QColor(fondo(c.name())) if _oscuro and c.alpha() == 255 else c


def color_texto(color) -> QColor:
    c = QColor(color)
    return QColor(texto(c.name())) if _oscuro and c.alpha() == 255 else c


def color_borde(color) -> QColor:
    c = QColor(color)
    return QColor(borde(c.name())) if _oscuro and c.alpha() == 255 else c


class _IconoSegunModo(QIconEngine):
    """Icono que se pinta con el color del modo de cada momento."""

    def __init__(self, crear, color: str):
        super().__init__()
        self._crear = crear
        self._color = color
        self._iconos: dict = {}

    def _icono(self) -> QIcon:
        if _oscuro not in self._iconos:
            color = texto(QColor(self._color).name()) if _oscuro else self._color
            self._iconos[_oscuro] = self._crear(color)
        return self._iconos[_oscuro]

    def pixmap(self, size, mode, state):
        return self._icono().pixmap(size, mode, state)

    def paint(self, painter, rect, mode, state):
        self._icono().paint(painter, rect, Qt.AlignmentFlag.AlignCenter, mode, state)

    def clone(self):
        return _IconoSegunModo(self._crear, self._color)


def icono_segun_modo(crear, color: str) -> QIcon:
    """`crear(color)` devuelve el QIcon pintado de ese color; en oscuro, aclarado."""
    return QIcon(_IconoSegunModo(crear, color))


# --------------------------------------------------------------------------
# Aplicación
# --------------------------------------------------------------------------


def _paleta(oscuro: bool) -> QPalette:
    f = fondo if oscuro else (lambda c: c)
    t = texto if oscuro else (lambda c: c)
    p = QPalette()
    rol = QPalette.ColorRole
    grupos = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive)
    colores = {
        rol.Window: f(Colors.SURFACE),
        rol.WindowText: t(Colors.TEXT_PRIMARY),
        rol.Base: f(Colors.BACKGROUND),
        rol.AlternateBase: f(Colors.SURFACE),
        rol.Text: t(Colors.TEXT_PRIMARY),
        rol.Button: f(Colors.SURFACE),
        rol.ButtonText: t(Colors.TEXT_PRIMARY),
        rol.BrightText: Colors.TEXT_ON_PRIMARY,
        rol.ToolTipBase: f(Colors.BACKGROUND),
        rol.ToolTipText: t(Colors.TEXT_PRIMARY),
        rol.PlaceholderText: t(Colors.TEXT_SECONDARY),
        rol.Highlight: Colors.PRIMARY,
        rol.HighlightedText: Colors.TEXT_ON_PRIMARY,
        rol.Link: t(Colors.PRIMARY),
        rol.Light: f(Colors.BACKGROUND),
        rol.Midlight: f(Colors.BORDER),
        rol.Mid: f(Colors.BORDER_DARK),
        rol.Dark: f(Colors.BORDER_CONTROL),
        rol.Shadow: "#000000",
    }
    for r, valor in colores.items():
        for g in grupos:
            p.setColor(g, r, QColor(valor))
        p.setColor(QPalette.ColorGroup.Disabled, r, QColor(valor))
    apagado = QColor(Colors.TEXT_DISABLED if not oscuro else "#6B776E")
    for r in (rol.WindowText, rol.Text, rol.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, r, apagado)
    return p


def _detectar() -> bool:
    forzado = os.environ.get("GUARDIAS_TEMA", "").lower()
    if forzado in ("oscuro", "claro"):
        return forzado == "oscuro"
    return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark


def _hoja_de_widget(widget, hoja):
    hoja = hoja or ""
    widget.setProperty(_PROPIEDAD, hoja)
    _poner_hoja_widget(widget, traducir_hoja(hoja) if _oscuro else hoja)


def _hoja_de_app(app, hoja):
    global _hoja_app
    _hoja_app = hoja or ""
    _poner_hoja_app(app, traducir_hoja(_hoja_app) if _oscuro else _hoja_app)


def _aplicar(app: QApplication, oscuro: bool, inicial: bool = False) -> None:
    global _oscuro
    _oscuro = oscuro
    # Windows pinta sus controles nativos siempre en claro: en oscuro, Fusion.
    # macOS los pinta en oscuro por su cuenta y se queda con su estilo.
    if sys.platform != "darwin":
        app.setStyle("Fusion" if oscuro else _estilo_original)
    if oscuro or not inicial:
        app.setPalette(_paleta(oscuro))
    if inicial:
        return
    _poner_hoja_app(app, traducir_hoja(_hoja_app) if oscuro else _hoja_app)
    for w in app.allWidgets():
        hoja = w.property(_PROPIEDAD)
        if hoja:
            _poner_hoja_widget(w, traducir_hoja(hoja) if oscuro else hoja)
        w.update()


def instalar(app: QApplication) -> bool:
    """Aplica el modo del sistema y lo sigue si cambia. Devuelve si es oscuro."""
    global _instalado, _estilo_original
    if _instalado:
        return _oscuro
    _instalado = True
    _estilo_original = app.style().name()
    QWidget.setStyleSheet = _hoja_de_widget
    QApplication.setStyleSheet = _hoja_de_app
    _aplicar(app, _detectar(), inicial=True)

    def cambio(_esquema):
        oscuro = _detectar()
        if oscuro != _oscuro:
            _aplicar(app, oscuro)

    QGuiApplication.styleHints().colorSchemeChanged.connect(cambio)
    return _oscuro
