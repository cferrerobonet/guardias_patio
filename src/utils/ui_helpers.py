"""
Utilidades para la interfaz de usuario.

Funciones helper para aplicar marca corporativa de forma discreta.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QMessageBox, QWidget


def get_corporate_icon() -> QIcon:
    """
    Obtiene el icono corporativo de forma discreta.

    Returns:
        QIcon con el logo corporativo si existe, icono vacío si no.
    """
    try:
        # Ruta relativa desde src/utils/ hasta imagenes/
        icon_path = Path(__file__).parent.parent.parent / "imagenes" / "logo.png"
        if icon_path.exists():
            return QIcon(str(icon_path))
    except Exception:
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
        icon_path = Path(__file__).parent.parent.parent / "imagenes" / "logo.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                return pixmap.scaled(
                    size, size,
                    aspectRatioMode=1,  # Qt.KeepAspectRatio
                    transformMode=1     # Qt.SmoothTransformation
                )
    except Exception:
        pass
    return None


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

    # Usar logo corporativo en lugar del icono estándar
    pixmap = get_corporate_pixmap(64)
    if pixmap:
        msg_box.setIconPixmap(pixmap)
    else:
        msg_box.setIcon(QMessageBox.Icon.Information)

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

    # Usar logo corporativo en lugar del icono estándar
    pixmap = get_corporate_pixmap(64)
    if pixmap:
        msg_box.setIconPixmap(pixmap)
    else:
        msg_box.setIcon(QMessageBox.Icon.Warning)

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

    # Usar logo corporativo en lugar del icono estándar
    pixmap = get_corporate_pixmap(64)
    if pixmap:
        msg_box.setIconPixmap(pixmap)
    else:
        msg_box.setIcon(QMessageBox.Icon.Critical)

    msg_box.exec()


def show_question(
    parent: Optional[QWidget],
    title: str,
    message: str,
    default_no: bool = True
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

    # Usar logo corporativo en lugar del icono estándar
    pixmap = get_corporate_pixmap(64)
    if pixmap:
        msg_box.setIconPixmap(pixmap)
    else:
        msg_box.setIcon(QMessageBox.Icon.Question)

    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if default_no:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    return msg_box.exec()


def show_question_with_cancel(
    parent: Optional[QWidget],
    title: str,
    message: str,
    default_button: str = "No"
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

    # Usar logo corporativo en lugar del icono estándar
    pixmap = get_corporate_pixmap(64)
    if pixmap:
        msg_box.setIconPixmap(pixmap)
    else:
        msg_box.setIcon(QMessageBox.Icon.Question)

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

    return msg_box.exec()
