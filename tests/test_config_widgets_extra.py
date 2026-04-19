"""
Tests adicionales para widgets de configuración y login.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# SMTPConfigWidget
# ===========================================================================


@pytest.mark.ui
class TestSMTPConfigWidgetExtra:
    def test_load_config(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        w.load_config()  # No debe lanzar

    def test_get_config_dict(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        config = w.get_config_dict()
        assert isinstance(config, dict)

    def test_set_config_dict(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        w.set_config_dict({"host": "smtp.test.com", "port": "587"})  # No debe lanzar

    def test_toggle_editable(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        w._toggle_editable()  # No debe lanzar


# ===========================================================================
# SFTPConfigWidget
# ===========================================================================


@pytest.mark.ui
class TestSFTPConfigWidgetExtra:
    def test_load_config(self, qtbot):
        from presentation.forms.config_widgets.sftp_widget import SFTPConfigWidget

        w = SFTPConfigWidget()
        qtbot.addWidget(w)
        w.load_config()  # No debe lanzar

    def test_get_config_dict(self, qtbot):
        from presentation.forms.config_widgets.sftp_widget import SFTPConfigWidget

        w = SFTPConfigWidget()
        qtbot.addWidget(w)
        config = w.get_config_dict()
        assert isinstance(config, dict)

    def test_toggle_editable(self, qtbot):
        from presentation.forms.config_widgets.sftp_widget import SFTPConfigWidget

        w = SFTPConfigWidget()
        qtbot.addWidget(w)
        w._toggle_editable()  # No debe lanzar


# ===========================================================================
# ZonaForm - métodos adicionales
# ===========================================================================


@pytest.mark.ui
class TestZonaFormExtra:
    def test_nombre_zona_input(self, qtbot, session):
        from presentation.forms.zona_form import ZonaForm

        form = ZonaForm(session)
        qtbot.addWidget(form)
        assert hasattr(form, "nombre_zona_input")

    def test_descripcion_input(self, qtbot, session):
        from presentation.forms.zona_form import ZonaForm

        form = ZonaForm(session)
        qtbot.addWidget(form)
        assert hasattr(form, "descripcion_input")

    def test_seleccionar_todas(self, qtbot, session):
        from presentation.forms.zona_form import ZonaForm

        form = ZonaForm(session)
        qtbot.addWidget(form)
        form.seleccionar_todas()  # No debe lanzar

    def test_setup_shortcuts(self, qtbot, session):
        from presentation.forms.zona_form import ZonaForm

        form = ZonaForm(session)
        qtbot.addWidget(form)
        form._setup_shortcuts()  # No debe lanzar


# ===========================================================================
# LoginDialog - métodos adicionales
# ===========================================================================


@pytest.mark.ui
class TestLoginDialogExtra:
    def test_load_existing_users(self, qtbot):
        from presentation.forms.login_dialog import LoginDialog

        dlg = LoginDialog()
        qtbot.addWidget(dlg)
        dlg.load_existing_users()  # No debe lanzar

    def test_login_dialog_tiene_setup_ui(self, qtbot):
        from presentation.forms.login_dialog import LoginDialog

        dlg = LoginDialog()
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "setup_ui")

    def test_open_register_dialog(self, qtbot):
        from presentation.forms.login_dialog import LoginDialog

        dlg = LoginDialog()
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "open_register_dialog")
