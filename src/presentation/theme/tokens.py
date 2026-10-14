"""
Design tokens centralizados para toda la aplicación.
Contiene paletas de colores, espaciados, tamaños de fuente y la familia
tipográfica de cada sistema operativo.
"""

import sys

#: Pila tipográfica por sistema. Barlow es la del diseño, compartido con Partes de
#: salida, y viaja dentro de la aplicación (`imagenes/fuentes`, OFL). Detrás, la del
#: sistema por si no se pudiera cargar. `-apple-system` no es una familia real fuera
#: del navegador: en Windows y Linux no resolvía y Qt caía a su fuente por defecto (VIS-003).
FAMILIAS_POR_SISTEMA = {
    "darwin": ["Barlow", "Helvetica Neue", "Helvetica", "Arial"],
    "win32": ["Barlow", "Segoe UI", "Tahoma", "Arial"],
    "linux": ["Barlow", "Cantarell", "Noto Sans", "DejaVu Sans", "Arial"],
}

#: Títulos y cifras: la versión condensada. Datos tabulares (horas, recuentos): monoespaciada.
FAMILIA_TITULOS = "Barlow Condensed"
FAMILIA_MONO = "JetBrains Mono"

#: Cuerpo base por sistema. El mismo valor en puntos no se ve igual en cada uno:
#: la fuente del sistema es de 13 pt en macOS y de 9 pt en Windows. Se mantiene el
#: 14 de macOS, que es con el que están medidas las pantallas actuales.
CUERPO_POR_SISTEMA = {"darwin": 14, "win32": 10, "linux": 10}


def _clave_de_sistema() -> str:
    if sys.platform.startswith("win"):
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def familias_del_sistema() -> list:
    """Familias tipográficas a probar, en orden, en este sistema operativo."""
    return list(FAMILIAS_POR_SISTEMA[_clave_de_sistema()])


def cuerpo_del_sistema() -> int:
    """Tamaño base de la fuente, en puntos, para este sistema operativo."""
    return CUERPO_POR_SISTEMA[_clave_de_sistema()]


def cargar_fuentes() -> None:
    """Registra en Qt las tipografías del diseño. Sin ellas, se usa la del sistema."""
    from PyQt6.QtGui import QFontDatabase

    from core.paths import get_resources_directory

    for ttf in sorted((get_resources_directory() / "fuentes").glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(ttf))

class Colors:
    # Paleta compartida con Partes de salida: verde EPLA, dorado y neutros que tiran
    # ligeramente al verde. El modo oscuro la traduce (`modo_oscuro.py`) y fija los
    # neutros a los mismos valores que la otra aplicación.
    PRIMARY = "#2C7A3A"        # 5,3:1 sobre blanco
    PRIMARY_LIGHT = "#E2F0E3"  # fondo de selección y realces suaves
    PRIMARY_DARK = "#1C5226"   # 9,3:1 — hover, pressed
    FOCUS_RING = "#2C7A3A"     # anillo de foco: 2 px
    FOCUS_HALO = "#B9DCBE"     # halo del anillo, para separarlo del fondo

    # Dorado: etiquetas y avisos de atención
    GOLD = "#B97A12"
    GOLD_SOFT = "#FBF0D9"

    # Semánticos — texto sobre blanco
    SUCCESS = "#2C7A3A"        # 5,3:1 AA
    SUCCESS_DARK = "#1C5226"   # 9,3:1 — hover y bordes de acento
    SUCCESS_BG = "#E2F0E3"     # fondo badge/info-box verde
    SUCCESS_BORDER = "#9FCFA7"
    WARNING = "#9A5B00"        # 5,6:1 AA
    WARNING_BG = "#FFF3DC"     # fondo badge/info-box ámbar
    WARNING_BG_ALT = "#FBF0D9" # variante dorada
    WARNING_BORDER = "#B97A12"
    ERROR = "#A32D2D"          # 7,0:1 AA sobre blanco
    ERROR_ON_BG = "#8A2424"    # 7,3:1 sobre ERROR_BG
    ERROR_BG = "#F8E3E1"
    ERROR_BORDER = "#E0A9A5"
    INFO = "#2E6B73"           # 6,0:1 AA
    INFO_BG = "#EEF2EC"        # fondo badge/info-box
    INFO_BORDER = "#C9D2C5"

    # Botones secundarios
    SECONDARY = "#5D6B60"      # gris verdoso
    SECONDARY_HOVER = "#46524A"

    # Panel de resultados del cálculo: verde muy suave con texto oscuro, para que
    # los valores en dorado y verde se lean (en oscuro lo traduce `modo_oscuro`).
    TERMINAL_BG = "#EEF2EC"
    TERMINAL_BORDER = "#D9E0D5"
    TERMINAL_TEXT = "#1D2A20"
    TERMINAL_ACCENT = "#2C7A3A"

    # Superficies
    BACKGROUND = "#FFFFFF"     # lienzo de contenido
    SURFACE = "#F3F5F1"        # fondo de ventana y campos
    SURFACE_2 = "#EEF2EC"      # barras, menú lateral y cabeceras
    BORDER = "#D9E0D5"         # separadores decorativos
    BORDER_DARK = "#C9D2C5"
    # El borde de un campo de texto delimita dónde se escribe: WCAG pide 3:1 (UXA-010).
    BORDER_CONTROL = "#7D8A80"  # 3,6:1 sobre blanco

    # Texto
    TEXT_PRIMARY = "#1D2A20"
    TEXT_SECONDARY = "#5D6B60"
    TEXT_DISABLED = "#9AA79D"
    TEXT_ON_PRIMARY = "#FFFFFF"

    # Menú lateral: claro, como los ajustes de Partes de salida
    SIDEBAR_BG = "#EEF2EC"
    SIDEBAR_TEXT = "#1D2A20"
    SIDEBAR_HOVER = "#E2E8DF"
    SIDEBAR_BORDER = "#D9E0D5"

class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24

class FontSize:
    # Escala del contrato de diseño. 12 px es el mínimo absoluto legible: por
    # debajo había 86 usos, algunos de 7 px (VIS-003).
    CAPTION = 12   # metadatos, celdas densas
    SMALL = 13     # cuerpo de tablas y formularios
    BODY = 14      # cuerpo general
    SUBTITLE = 16
    H3 = 18
    TITLE = 20
    H2 = 24
    H1 = 28

class BorderRadius:
    # Radios del diseño de Partes de salida: 7–8 px campos y botones, 10 px cajas.
    SM = 4
    MD = 7
    LG = 10


#: Modo oscuro: cada color de la paleta tiene su pareja fija, la misma que usa Partes de
#: salida, según se use de fondo, de texto o de borde. Lo que no está aquí lo traduce
#: `modo_oscuro.py` con sus reglas.
FONDOS_OSCUROS = {
    "#FFFFFF": "#1A211C", "#F3F5F1": "#121713", "#EEF2EC": "#222B24",
    "#E2E8DF": "#2A342C", "#E2F0E3": "#1F3524", "#FBF0D9": "#3A2E17",
    "#FFF3DC": "#3A2C14", "#F8E3E1": "#3A1F1F", "#D9E0D5": "#323D35",
    "#C9D2C5": "#3A463D",
}
TEXTOS_OSCUROS = {
    "#1D2A20": "#E4EBE5", "#2F3B32": "#C9D3CB", "#46524A": "#B3BFB6",
    "#5D6B60": "#9AA89D", "#9AA79D": "#6B776E", "#2C7A3A": "#5FBF6E",
    "#1C5226": "#7FD08C", "#B97A12": "#E3A94A", "#9A5B00": "#F0B45A",
    "#A32D2D": "#F08A8A", "#8A2424": "#F08A8A", "#2E6B73": "#7CC0C8",
}
BORDES_OSCUROS = {
    "#D9E0D5": "#323D35", "#C9D2C5": "#3A463D", "#7D8A80": "#5E6B61",
    "#9FCFA7": "#2F5A37", "#E0A9A5": "#6B3333",
}


#: Colores del texto del panel de resultados (HTML), por papel, en claro y en oscuro.
TERMINAL_CLARO = {
    "titulo": "#1C5226", "etiqueta": "#46524A", "valor": "#7A4800", "exito": "#1C5226",
    "aviso": "#9A5B00", "error": "#A32D2D", "info": "#5D6B60", "profesor": "#2E6B73",
    "prompt": "#2C7A3A",
}
TERMINAL_OSCURO = {
    "titulo": "#7FD08C", "etiqueta": "#B3BFB6", "valor": "#E3A94A", "exito": "#7FD08C",
    "aviso": "#F0B45A", "error": "#F08A8A", "info": "#9AA89D", "profesor": "#7CC0C8",
    "prompt": "#5FBF6E",
}
