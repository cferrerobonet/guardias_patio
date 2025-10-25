"""
Stubs para PyQt6 cuando no está disponible.

Permite ejecutar tests en entornos CI sin PyQt6 instalado.
"""


class _Stub:
    """Stub genérico para widgets de PyQt6."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return _Stub()

    def __call__(self, *args, **kwargs):
        return self

    # Métodos comunes de widgets
    def setCalendarPopup(self, *a, **k):
        pass

    def setDate(self, *a, **k):
        pass

    def setTime(self, *a, **k):
        pass

    def addItems(self, *a, **k):
        pass

    def setPlaceholderText(self, *a, **k):
        pass

    def setVisible(self, *a, **k):
        pass

    def setReadOnly(self, *a, **k):
        pass

    def setMaximumHeight(self, *a, **k):
        pass

    def addWidget(self, *a, **k):
        pass

    def addLayout(self, *a, **k):
        pass

    def clicked(self, *a, **k):
        return _Stub()

    def connect(self, *a, **k):
        pass

    def currentText(self):
        return ""

    def text(self):
        return ""

    def clear(self):
        pass

    def setChecked(self, *a, **k):
        pass

    def date(self):
        return _Stub()

    def time(self):
        return _Stub()

    def toPyDate(self):
        return None

    def toPyTime(self):
        return None

    def isValid(self):
        return False

    def setWindowTitle(self, *a, **k):
        pass

    def show(self):
        pass

    def exec(self):
        return 0

    def setText(self, *a, **k):
        pass

    def currentTextChanged(self, *a, **k):
        return _Stub()

    def width(self):
        return 1920

    def height(self):
        return 1080


class QMessageBoxStub(_Stub):
    """Stub específico para QMessageBox."""

    class StandardButton:
        Yes = 1
        No = 0

    @staticmethod
    def information(*a, **k):
        pass

    @staticmethod
    def warning(*a, **k):
        pass

    @staticmethod
    def critical(*a, **k):
        pass

    @staticmethod
    def question(*a, **k):
        return 0


class QDateStub:
    """Stub para QDate."""

    @staticmethod
    def currentDate():
        return QDateStub()

    def addMonths(self, n):
        return self

    def __call__(self, *a, **k):
        return self


class QTimeStub:
    """Stub para QTime."""

    def __init__(self, *a, **k):
        pass


class QScreenStub(_Stub):
    """Stub para QScreen."""

    def geometry(self):
        """Retorna un stub con width() y height()."""
        return _Stub()


def get_pyqt_stubs():
    """
    Retorna un diccionario con todos los stubs de PyQt6.

    Returns:
        dict: Diccionario con nombres de clases y sus stubs
    """
    return {
        "QApplication": _Stub,
        "QWidget": _Stub,
        "QLabel": _Stub,
        "QLineEdit": _Stub,
        "QComboBox": _Stub,
        "QDateEdit": _Stub,
        "QTimeEdit": _Stub,
        "QCheckBox": _Stub,
        "QListWidget": _Stub,
        "QPushButton": _Stub,
        "QHBoxLayout": _Stub,
        "QVBoxLayout": _Stub,
        "QTabWidget": _Stub,
        "QTextEdit": _Stub,
        "QMessageBox": QMessageBoxStub,
        "QDate": QDateStub,
        "QTime": QTimeStub,
        "QKeySequence": _Stub,
        "QShortcut": _Stub,
        "QScreen": QScreenStub,
    }
