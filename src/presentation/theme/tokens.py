"""
Design tokens centralizados para toda la aplicación.
Contiene paletas de colores, espaciados, tamaños de fuente y la familia
tipográfica de cada sistema operativo.
"""

import sys

#: Pila tipográfica por sistema. `-apple-system` no es una familia real fuera del
#: navegador: en Windows y Linux no resolvía y Qt caía a su fuente por defecto,
#: de modo que la aplicación no se veía como se diseñó (VIS-003).
FAMILIAS_POR_SISTEMA = {
    "darwin": ["SF Pro Text", "Helvetica Neue", "Helvetica", "Arial"],
    "win32": ["Segoe UI", "Tahoma", "Arial"],
    "linux": ["Cantarell", "Noto Sans", "DejaVu Sans", "Arial"],
}

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

class Colors:
    # Primarios. El azul anterior (#007ACC) daba 4,51:1 sobre blanco: pasaba el
    # mínimo AA por una centésima y no dejaba margen para los estados hover ni
    # para el anillo de foco. Este da 6,52:1 (VIS-002, UXA-010).
    PRIMARY = "#0E5FA8"        # 6,5:1 sobre blanco
    PRIMARY_LIGHT = "#E6F2FA"  # fondo de selección y realces suaves
    PRIMARY_DARK = "#0C5291"   # 8,0:1 — hover, pressed y foco
    FOCUS_RING = "#0E5FA8"     # anillo de foco: 2 px
    FOCUS_HALO = "#BFD7F2"     # halo del anillo, para separarlo del fondo

    # Semánticos — texto sobre blanco
    SUCCESS = "#1E7E34"        # 5,1:1 AA
    SUCCESS_DARK = "#166529"   # 7,2:1 — hover y bordes de acento
    SUCCESS_BG = "#D1FAE5"     # fondo badge/info-box verde
    SUCCESS_BORDER = "#6EE7B7"
    WARNING = "#856404"        # 5.5:1 AA
    WARNING_BG = "#FFF3CD"     # fondo badge/info-box ámbar
    WARNING_BG_ALT = "#FEF3C7" # variante amber
    WARNING_BORDER = "#F59E0B"
    ERROR = "#DC3545"          # 4.5:1 AA
    ERROR_BG = "#FEE2E2"
    ERROR_BORDER = "#FCA5A5"
    INFO = "#0C6674"           # 6.6:1 AA
    INFO_BG = "#EFF6FF"        # fondo badge/info-box azul
    INFO_BORDER = "#BFDBFE"

    # Botones secundarios
    SECONDARY = "#6B7280"      # gris neutro
    SECONDARY_HOVER = "#4B5563"

    # Terminal retro (paneles vintage)
    TERMINAL_BG = "#0F172A"
    TERMINAL_BORDER = "#1F2937"
    TERMINAL_TEXT = "#D1D5DB"
    TERMINAL_ACCENT = "#22C55E"

    # Superficies
    BACKGROUND = "#FFFFFF"
    SURFACE = "#F8F9FA"
    BORDER = "#E1E4E8"
    BORDER_DARK = "#D1D5DB"

    # Texto
    TEXT_PRIMARY = "#1F2937"
    TEXT_SECONDARY = "#6B7280"
    TEXT_DISABLED = "#9CA3AF"
    TEXT_ON_PRIMARY = "#FFFFFF"

    # Sidebar
    SIDEBAR_BG = "#3E4857"
    SIDEBAR_TEXT = "#FFFFFF"
    SIDEBAR_HOVER = "#4A5668"
    SIDEBAR_BORDER = "#2A3340"

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
    SM = 2
    MD = 4
    LG = 6
