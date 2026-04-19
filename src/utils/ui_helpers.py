"""
Utilidades para la interfaz de usuario.

Funciones helper para aplicar marca corporativa de forma discreta.
"""

from pathlib import Path
from typing import Optional

from core.logging import get_logger
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPixmapCache
from PyQt6.QtWidgets import QMessageBox, QWidget

logger = get_logger(__name__)

# Estilos consistentes para todos los QMessageBox
MESSAGEBOX_STYLE = """
    QMessageBox {
        background-color: white !important;
        min-width: 400px;
    }
    QMessageBox QLabel {
        color: #1f2937 !important;
        font-size: 14px;
        padding: 10px;
    }
    QMessageBox QPushButton {
        background-color: #059669 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 24px !important;
        border: 2px solid #047857 !important;
        border-radius: 6px !important;
        min-width: 100px !important;
        min-height: 35px !important;
    }
    QMessageBox QPushButton:hover {
        background-color: #047857 !important;
    }
    QMessageBox QPushButton:pressed {
        background-color: #065f46 !important;
    }
    QMessageBox QPushButton:default {
        background-color: #0284c7 !important;
        border: 2px solid #0369a1 !important;
    }
    QMessageBox QPushButton:default:hover {
        background-color: #0369a1 !important;
    }
"""


def _get_logo_path() -> Path:
    return Path(__file__).parent.parent.parent / "imagenes" / "logo.png"


def _get_cached_pixmap(path: Path) -> Optional[QPixmap]:
    cache_key = str(path)
    cached = QPixmapCache.find(cache_key)
    if cached is not None:
        return cached

    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None

    QPixmapCache.insert(cache_key, pixmap)
    return pixmap


def get_corporate_icon() -> QIcon:
    """
    Obtiene el icono corporativo de forma discreta.

    Returns:
        QIcon con el logo corporativo si existe, icono vacío si no.
    """
    try:
        icon_path = _get_logo_path()
        if icon_path.exists():
            return QIcon(str(icon_path))
    except (OSError, ValueError, RuntimeError):
        pass
    return QIcon()  # Fallback a icono por defecto


def get_corporate_pixmap(size: int = 64) -> Optional[QPixmap]:
    """
    Obtiene el pixmap del logo corporativo escalado.

    Args:
        size: Tamaño del icono en píxeles (por defecto 64x64)

    Returns:
        QPixmap con el logo corporativo escalado, None si no existe.
    """
    try:
        icon_path = _get_logo_path()
        if icon_path.exists():
            pixmap = _get_cached_pixmap(icon_path)
            if pixmap is not None:
                return pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
    except Exception as e:
        logger.warning(f"Error cargando logo corporativo: {e}")
    return None


def apply_corporate_icon_to_messagebox(msg_box: QMessageBox) -> None:
    """
    Aplica el icono corporativo a un QMessageBox de forma confiable.

    En macOS, setIconPixmap() no siempre funciona, así que este método
    intenta múltiples enfoques.

    Args:
        msg_box: El QMessageBox al que aplicar el icono
    """
    try:
        icon_path = _get_logo_path()
        if icon_path.exists():
            pixmap = _get_cached_pixmap(icon_path)
            if pixmap is not None:
                # Escalar el pixmap
                scaled_pixmap = pixmap.scaled(
                    64,
                    64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                # Forzar el uso del pixmap personalizado
                msg_box.setIconPixmap(scaled_pixmap)
                # No establecer un icono estándar, solo el pixmap
                return
    except Exception as e:
        logger.warning(f"Error aplicando icono corporativo: {e}")

    # Fallback: usar icono estándar de pregunta
    msg_box.setIcon(QMessageBox.Icon.Question)


def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
    """
    Muestra un mensaje informativo con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje a mostrar
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo sin establecer icono estándar primero
    apply_corporate_icon_to_messagebox(msg_box)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    msg_box.exec()


def show_warning(parent: Optional[QWidget], title: str, message: str) -> None:
    """
    Muestra una advertencia con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje de advertencia
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    msg_box.exec()


def show_error(parent: Optional[QWidget], title: str, message: str) -> None:
    """
    Muestra un error con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje de error
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    msg_box.exec()


def show_question(
    parent: Optional[QWidget], title: str, message: str, default_no: bool = True
) -> int:
    """
    Muestra una pregunta con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Pregunta
        default_no: Si True, el botón No es el predeterminado

    Returns:
        Código de respuesta del botón presionado
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if default_no:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    return msg_box.exec()


def show_question_with_cancel(
    parent: Optional[QWidget], title: str, message: str, default_button: str = "No"
) -> int:
    """
    Muestra una pregunta con Yes/No/Cancel y logo corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Pregunta
        default_button: Botón predeterminado ("Yes", "No", "Cancel")

    Returns:
        Código de respuesta del botón presionado (QMessageBox.StandardButton)
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
        | QMessageBox.StandardButton.Cancel
    )

    if default_button == "Yes":
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    elif default_button == "Cancel":
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    return msg_box.exec()


def show_confirmation(
    parent: Optional[QWidget], title: str, message: str, default_button: str = "No"
) -> bool:
    """
    Muestra una confirmación Yes/No con logo corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje de confirmación
        default_button: Botón predeterminado ("Yes" o "No")

    Returns:
        True si se presionó Yes, False si se presionó No
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

    if default_button == "Yes":
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    return msg_box.exec() == QMessageBox.StandardButton.Yes
