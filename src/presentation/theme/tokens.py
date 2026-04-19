"""
Design tokens centralizados para toda la aplicación.
Contiene paletas de colores, espaciados y tamaños de fuente.
"""

class Colors:
    # Primarios
    PRIMARY = "#007ACC"
    PRIMARY_LIGHT = "#E6F2FA"
    PRIMARY_DARK = "#005A9E"
    
    # Semánticos
    SUCCESS = "#28A745"
    WARNING = "#FFC107"
    ERROR = "#DC3545"
    INFO = "#17A2B8"
    
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
    TITLE = 20
    H2 = 24
    H1 = 28

class BorderRadius:
    SM = 2
    MD = 4
    LG = 6
