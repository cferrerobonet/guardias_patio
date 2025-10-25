"""
Importación segura de PyQt6.

Proporciona imports de PyQt6 con fallback a stubs si no está disponible.
"""

GUI_AVAILABLE = True

try:
    from PyQt6.QtCore import QDate, QTime
    from PyQt6.QtGui import QKeySequence, QScreen, QShortcut
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDateEdit,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QTimeEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    GUI_AVAILABLE = False
    from core.pyqt_stubs import get_pyqt_stubs

    # Importar stubs
    _stubs = get_pyqt_stubs()
    QApplication = _stubs["QApplication"]
    QWidget = _stubs["QWidget"]
    QLabel = _stubs["QLabel"]
    QLineEdit = _stubs["QLineEdit"]
    QComboBox = _stubs["QComboBox"]
    QDateEdit = _stubs["QDateEdit"]
    QTimeEdit = _stubs["QTimeEdit"]
    QCheckBox = _stubs["QCheckBox"]
    QListWidget = _stubs["QListWidget"]
    QPushButton = _stubs["QPushButton"]
    QHBoxLayout = _stubs["QHBoxLayout"]
    QVBoxLayout = _stubs["QVBoxLayout"]
    QTabWidget = _stubs["QTabWidget"]
    QTextEdit = _stubs["QTextEdit"]
    QMessageBox = _stubs["QMessageBox"]
    QDate = _stubs["QDate"]
    QTime = _stubs["QTime"]
    QKeySequence = _stubs["QKeySequence"]
    QShortcut = _stubs["QShortcut"]
    QScreen = _stubs["QScreen"]


__all__ = [
    "GUI_AVAILABLE",
    "QApplication",
    "QWidget",
    "QLabel",
    "QLineEdit",
    "QComboBox",
    "QDateEdit",
    "QTimeEdit",
    "QCheckBox",
    "QListWidget",
    "QPushButton",
    "QHBoxLayout",
    "QVBoxLayout",
    "QTabWidget",
    "QTextEdit",
    "QMessageBox",
    "QDate",
    "QTime",
    "QKeySequence",
    "QShortcut",
    "QScreen",
]
