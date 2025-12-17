"""
Sistema de iconos profesionales para la aplicación.

Proporciona iconos SVG monocromáticos que se adaptan al contexto
(fondo claro/oscuro, botones de colores, etc.).

Uso:
    from utils.icons import Icons, get_icon

    # Para botones con fondo de color (blanco)
    btn.setIcon(Icons.get("save"))

    # Para contextos con fondo claro (oscuro)
    btn.setIcon(Icons.get("save", Icons.DARK))

    # Para el color primario de la app
    btn.setIcon(Icons.get("save", Icons.PRIMARY))
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


def _get_icons_directory() -> Path:
    """Obtiene el directorio de iconos según el entorno."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS) / "imagenes" / "icons"
        return Path(sys.executable).parent / "imagenes" / "icons"
    return Path(__file__).parent.parent.parent / "imagenes" / "icons"


class Icons:
    """
    Gestor centralizado de iconos SVG monocromáticos.

    Colores disponibles:
    - WHITE: Para botones con fondo de color (primario, success, danger, warning)
    - DARK: Para fondos claros (formularios, diálogos, GroupBox)
    - PRIMARY: Para acentos (color azul de la app)
    - MUTED: Para elementos secundarios (gris suave)
    """

    # Colores predefinidos
    WHITE = "#FFFFFF"
    DARK = "#424242"      # Gris oscuro profesional
    PRIMARY = "#2196F3"   # Azul de la app
    MUTED = "#757575"     # Gris medio
    SUCCESS = "#4CAF50"   # Verde
    DANGER = "#f44336"    # Rojo
    WARNING = "#FF9800"   # Naranja

    # Mapeo de nombres de iconos a archivos
    _ICON_MAP = {
        # Acciones CRUD
        "add": "plus.svg",
        "plus": "plus.svg",
        "create": "plus.svg",
        "edit": "pencil.svg",
        "pencil": "pencil.svg",
        "delete": "delete.svg",
        "trash": "delete.svg",
        "remove": "delete-outline.svg",
        "save": "content-save.svg",
        "copy": "content-copy.svg",

        # Navegación y búsqueda
        "search": "magnify.svg",
        "find": "magnify.svg",
        "refresh": "refresh.svg",
        "reload": "refresh.svg",
        "back": "chevron-left.svg",
        "next": "chevron-right.svg",
        "open": "open-in-new.svg",
        "menu": "menu.svg",

        # Confirmación / Cancelación
        "check": "check.svg",
        "confirm": "check-bold.svg",
        "close": "close.svg",
        "cancel": "close.svg",
        "clear": "close.svg",
        "pause": "pause.svg",
        "stop": "pause.svg",

        # Visualización
        "view": "eye.svg",
        "eye": "eye.svg",
        "show": "eye.svg",
        "preview": "eye.svg",

        # Importar / Exportar
        "download": "download.svg",
        "import": "download.svg",
        "upload": "upload.svg",
        "export": "upload.svg",
        "database": "database-import-export.svg",

        # Calendario y tiempo
        "calendar": "calendar.svg",
        "date": "calendar-month.svg",
        "schedule": "calendar-month.svg",
        "clock": "clock-outline.svg",
        "time": "clock-outline.svg",
        "today": "calendar.svg",

        # Personas y cuentas
        "user": "account.svg",
        "account": "account.svg",
        "profile": "account.svg",
        "users": "account-group.svg",
        "group": "account-group.svg",
        "team": "account-group.svg",
        "add-user": "account-plus.svg",

        # Estadísticas y reportes
        "chart": "chart-bar.svg",
        "stats": "chart-bar.svg",
        "analytics": "chart-line.svg",
        "report": "file-chart.svg",
        "dashboard": "view-dashboard.svg",

        # Configuración
        "settings": "cog.svg",
        "config": "cog.svg",
        "cog": "cog.svg",

        # Información y alertas
        "info": "information.svg",
        "information": "information-outline.svg",
        "alert": "alert-circle.svg",
        "warning": "alert-circle.svg",
        "bell": "bell.svg",
        "notification": "bell.svg",

        # Específicos de la app
        "zone": "map-marker.svg",
        "location": "map-marker.svg",
        "school": "school.svg",
        "swap": "swap-horizontal.svg",
        "substitute": "swap-horizontal.svg",
        "clipboard": "clipboard-text.svg",
        "list": "clipboard-text.svg",
        "target": "target.svg",
        "assign": "target.svg",

        # Seguridad
        "key": "key.svg",
        "password": "key.svg",
        "lock": "lock.svg",
        "login": "login.svg",
        "email": "email.svg",
        "mail": "email.svg",

        # Acciones especiales
        "test": "flask.svg",
        "flask": "flask.svg",
        "experiment": "flask.svg",
        "skip": "skip-next.svg",
        "skip-next": "skip-next.svg",
        "forward": "skip-next.svg",
        "help": "help-circle.svg",
        "question": "help-circle.svg",
    }

    _cache: dict[tuple[str, str, int], QIcon] = {}
    _icons_dir: Optional[Path] = None

    @classmethod
    def _get_icons_dir(cls) -> Path:
        """Obtiene y cachea el directorio de iconos."""
        if cls._icons_dir is None:
            cls._icons_dir = _get_icons_directory()
        return cls._icons_dir

    @classmethod
    def get(cls, name: str, color: str = WHITE, size: int = 20) -> QIcon:
        """
        Obtiene un icono SVG coloreado.

        Args:
            name: Nombre del icono (ver _ICON_MAP para opciones)
            color: Color del icono (usar constantes de clase)
            size: Tamaño del icono en píxeles

        Returns:
            QIcon con el icono coloreado
        """
        cache_key = (name, color, size)

        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Buscar archivo
        filename = cls._ICON_MAP.get(name.lower())
        if not filename:
            # Intentar como nombre de archivo directo
            filename = f"{name}.svg"

        icon_path = cls._get_icons_dir() / filename

        if not icon_path.exists():
            # Retornar icono vacío si no existe
            return QIcon()

        # Crear icono coloreado
        icon = cls._create_colored_icon(icon_path, color, size)
        cls._cache[cache_key] = icon

        return icon

    @classmethod
    def _create_colored_icon(cls, svg_path: Path, color: str, size: int) -> QIcon:
        """Crea un QIcon a partir de un SVG con el color especificado."""
        # Leer el SVG
        svg_content = svg_path.read_text()

        # Inyectar el color en el SVG
        # Si no tiene fill definido, agregar fill al path
        if 'fill=' not in svg_content:
            svg_content = svg_content.replace('<path', f'<path fill="{color}"')
        else:
            # Reemplazar fill existente
            import re
            svg_content = re.sub(r'fill="[^"]*"', f'fill="{color}"', svg_content)

        # Crear renderer desde el SVG modificado
        renderer = QSvgRenderer(svg_content.encode())

        # Crear pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparente

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    @classmethod
    def get_pixmap(cls, name: str, color: str = WHITE, size: int = 20) -> QPixmap:
        """
        Obtiene un QPixmap del icono (útil para labels).

        Args:
            name: Nombre del icono
            color: Color del icono
            size: Tamaño en píxeles

        Returns:
            QPixmap con el icono
        """
        icon = cls.get(name, color, size)
        return icon.pixmap(QSize(size, size))

    @classmethod
    def clear_cache(cls):
        """Limpia la caché de iconos."""
        cls._cache.clear()

    @classmethod
    def available_icons(cls) -> list[str]:
        """Retorna lista de nombres de iconos disponibles."""
        return sorted(cls._ICON_MAP.keys())


# Función de conveniencia
def get_icon(name: str, color: str = Icons.WHITE, size: int = 20) -> QIcon:
    """
    Atajo para Icons.get().

    Args:
        name: Nombre del icono
        color: Color del icono (default: blanco para botones)
        size: Tamaño en píxeles

    Returns:
        QIcon coloreado
    """
    return Icons.get(name, color, size)


# Funciones de conveniencia para contextos específicos
def icon_for_button(name: str, size: int = 18) -> QIcon:
    """Icono blanco para botones con fondo de color."""
    return Icons.get(name, Icons.WHITE, size)


def icon_for_form(name: str, size: int = 16) -> QIcon:
    """Icono oscuro para formularios con fondo claro."""
    return Icons.get(name, Icons.DARK, size)


def icon_for_primary(name: str, size: int = 16) -> QIcon:
    """Icono en color primario de la app."""
    return Icons.get(name, Icons.PRIMARY, size)


def icon_for_muted(name: str, size: int = 16) -> QIcon:
    """Icono en gris suave para elementos secundarios."""
    return Icons.get(name, Icons.MUTED, size)
