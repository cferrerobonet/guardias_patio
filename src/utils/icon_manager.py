"""
Alias de compatibilidad para utils.icons.

Este módulo era el gestor de iconos original. Ahora delega en utils.icons
(implementación unificada). Mantener este alias para no romper imports existentes.
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from utils.icons import Icons, get_icon  # noqa: F401
from core.paths import get_resources_directory

logger = logging.getLogger(__name__)


class IconManager:
    """Gestor centralizado de iconos SVG."""

    _instance = None
    _icons_path: Optional[Path] = None

    def __new__(cls):
        """Implementa el patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Inicializa el gestor de iconos.

        CRÍTICO: Usa get_resources_directory() para obtener la ruta correcta
        de los iconos. En desarrollo apunta a 'imagenes/icons/', en producción
        (app compilada) apunta a 'Contents/Resources/imagenes/icons/'.

        NO modificar esto para usar rutas hardcodeadas o relativas, causará
        que los iconos no se carguen en la app compilada.
        """
        if self._icons_path is None:
            # Usar el sistema de rutas adaptativas para desarrollo y producción
            self._icons_path = get_resources_directory() / "icons"

    def get_icon(self, icon_name: str, color: str = "white", size: int = 24) -> QIcon:
        """
        Carga un icono SVG y le aplica un color.

        Args:
            icon_name: Nombre del archivo SVG (sin extensión)
            color: Color a aplicar (nombre o hex). Por defecto "white"
            size: Tamaño del icono en píxeles. Por defecto 24

        Returns:
            QIcon con el icono coloreado

        Example:
            >>> icon_manager = IconManager()
            >>> white_icon = icon_manager.get_icon("account", "white", 24)
            >>> blue_icon = icon_manager.get_icon("calendar", "#0E5FA8", 32)
        """
        # Construir la ruta completa al archivo SVG
        icon_file = self._icons_path / f"{icon_name}.svg"

        if not icon_file.exists():
            logger.debug(f"Icono no encontrado: {icon_file}")
            return QIcon()  # Retorna icono vacío

        # Leer el contenido del SVG
        with open(icon_file, "r", encoding="utf-8") as f:
            svg_content = f.read()

        # Reemplazar el color del SVG de manera más agresiva
        # Los SVGs de Material Design usan diferentes formatos
        svg_content = svg_content.replace('fill="currentColor"', f'fill="{color}"')
        svg_content = svg_content.replace('fill="#000000"', f'fill="{color}"')
        svg_content = svg_content.replace('fill="#000"', f'fill="{color}"')
        svg_content = svg_content.replace('fill="black"', f'fill="{color}"')

        # También reemplazar en el path si no tiene fill explícito
        if "fill=" not in svg_content and "<path" in svg_content:
            svg_content = svg_content.replace("<path", f'<path fill="{color}"')

        # Renderizar el SVG en un pixmap
        renderer = QSvgRenderer()
        renderer.load(svg_content.encode("utf-8"))

        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def get_colored_icon(self, icon_name: str, color: QColor, size: int = 24) -> QIcon:
        """
        Carga un icono SVG y le aplica un QColor.

        Args:
            icon_name: Nombre del archivo SVG (sin extensión)
            color: QColor a aplicar
            size: Tamaño del icono en píxeles

        Returns:
            QIcon con el icono coloreado
        """
        return self.get_icon(icon_name, color.name(), size)

    def list_available_icons(self) -> list[str]:
        """
        Lista todos los iconos SVG disponibles.

        Returns:
            Lista con los nombres de los iconos (sin extensión)
        """
        if not self._icons_path.exists():
            return []

        return [f.stem for f in self._icons_path.glob("*.svg")]


# Instancia global del gestor de iconos
icon_manager = IconManager()


def get_icon(icon_name: str, color: str = "white", size: int = 24) -> QIcon:
    """
    Función de conveniencia para obtener un icono.

    Args:
        icon_name: Nombre del archivo SVG (sin extensión)
        color: Color a aplicar (nombre o hex). Por defecto "white"
        size: Tamaño del icono en píxeles. Por defecto 24

    Returns:
        QIcon con el icono coloreado

    Example:
        >>> from utils.icon_manager import get_icon
        >>> icon = get_icon("account", "white", 20)
    """
    return icon_manager.get_icon(icon_name, color, size)
