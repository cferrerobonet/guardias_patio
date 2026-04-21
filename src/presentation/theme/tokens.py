"""
Design tokens centralizados para toda la aplicación.
Contiene paletas de colores, espaciados y tamaños de fuente.
"""

class Colors:
    # Primarios
    PRIMARY = "#007ACC"
    PRIMARY_LIGHT = "#E6F2FA"
    PRIMARY_DARK = "#005A9E"

    # Semánticos — texto sobre blanco
    SUCCESS = "#1E7E34"        # 5.2:1 AA
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
    CAPTION = 11
    BODY = 14
    SUBTITLE = 16
    H3 = 18
    TITLE = 20
    H2 = 24
    H1 = 28

class BorderRadius:
    SM = 2
    MD = 4
    LG = 6
