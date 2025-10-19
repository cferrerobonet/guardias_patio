"""
Utilidades para la interfaz de usuario.

Funciones helper para aplicar marca corporativa de forma discreta.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon
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
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowIcon(get_corporate_icon())
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
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowIcon(get_corporate_icon())
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
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowIcon(get_corporate_icon())
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
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowIcon(get_corporate_icon())
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if default_no:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    return msg_box.exec()
