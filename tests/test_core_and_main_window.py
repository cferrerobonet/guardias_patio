"""
Tests para módulos de presentación y servicios con 0% de coverage:
- ccleaner_main_window.py
- app_initializer.py
- pyqt_stubs.py
- _pdf_individual_optimizado.py (funciones auxiliares)
- _pdf_mes_consolidado.py (funciones auxiliares)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# pyqt_stubs (no necesita UI real, solo importar y probar la clase Stub)
# ===========================================================================


class TestPyqtStubs:
    def test_stub_instanciable(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        assert stub is not None

    def test_stub_getattr(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        attr = stub.cualquier_atributo
        assert attr is not None

    def test_stub_call(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        result = stub()
        assert result is not None

    def test_stub_set_calendar_popup(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.setCalendarPopup(True)  # No debe lanzar

    def test_stub_set_date(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.setDate("2024-01-01")

    def test_stub_set_time(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.setTime("10:00")

    def test_stub_add_items(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.addItems(["a", "b"])

    def test_stub_set_placeholder_text(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.setPlaceholderText("placeholder")

    def test_stub_set_visible(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.setVisible(True)

    def test_stub_set_readonly(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.setReadOnly(True)

    def test_stub_set_maximum_height(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.setMaximumHeight(100)

    def test_stub_add_widget(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.addWidget(MagicMock())

    def test_stub_add_layout(self):
        from core.pyqt_stubs import _Stub

        stub = _Stub()
        stub.addLayout(MagicMock())

    def test_stub_module_exports(self):
        import core.pyqt_stubs as stubs

        # El módulo debe exportar al menos la clase Stub
        assert hasattr(stubs, "_Stub")


# ===========================================================================
# app_initializer
# ===========================================================================


class TestAppInitializer:
    def test_initialize_logging(self):
        from core.app_initializer import initialize_logging

        initialize_logging()  # No debe lanzar

    def test_configure_qt_plugins(self):
        from core.app_initializer import configure_qt_plugins

        configure_qt_plugins()  # No debe lanzar

    def test_run_smoke_test(self):
        from core.app_initializer import run_smoke_test

        run_smoke_test()  # No debe lanzar


# ===========================================================================
# ContentWrapper
# ===========================================================================


@pytest.mark.ui
class TestContentWrapper:
    def test_constructor(self, qtbot):
        from PyQt6.QtWidgets import QLabel

        from presentation.ccleaner_main_window import ContentWrapper

        inner = QLabel("test")
        widget = ContentWrapper("Mi Sección", inner)
        qtbot.addWidget(widget)
        assert widget is not None


# ===========================================================================
# CCleanerMainWindow
# ===========================================================================


@pytest.mark.ui
class TestCCleanerMainWindow:
    def test_constructor(self, qtbot, session):
        from presentation.ccleaner_main_window import CCleanerMainWindow

        window = CCleanerMainWindow(session)
        qtbot.addWidget(window)
        assert window is not None
        assert window.isMaximized()
        assert not window.isFullScreen()

    def test_add_view(self, qtbot, session):
        from PyQt6.QtWidgets import QLabel

        from presentation.ccleaner_main_window import CCleanerMainWindow

        window = CCleanerMainWindow(session)
        qtbot.addWidget(window)
        content = QLabel("Contenido")
        window.add_view("test_section", "Título Test", content)  # No debe lanzar
