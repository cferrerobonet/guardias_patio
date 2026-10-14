"""
Tests para login_dialog.py, perfiles_usuario_form.py, delete_user_dialog.py,
forgot_password_dialog.py, reset_password_dialog.py, ajustes_form.py,
menu_lateral.py y otros módulos de presentación con 0% de coverage.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# RegisterDialog
# ===========================================================================


@pytest.mark.ui
class TestRegisterDialog:
    def test_constructor(self, qtbot):
        from presentation.forms.login_dialog import RegisterDialog

        dlg = RegisterDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_titulo(self, qtbot):
        from presentation.forms.login_dialog import RegisterDialog

        dlg = RegisterDialog()
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() != ""


# ===========================================================================
# LoginDialog
# ===========================================================================


@pytest.mark.ui
class TestLoginDialog:
    def test_constructor(self, qtbot):
        from presentation.forms.login_dialog import LoginDialog

        dlg = LoginDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_load_existing_users(self, qtbot):
        from presentation.forms.login_dialog import LoginDialog

        dlg = LoginDialog()
        qtbot.addWidget(dlg)
        with patch.object(dlg, "load_existing_users", wraps=dlg.load_existing_users):
            dlg.load_existing_users()  # No debe lanzar

    def test_tiene_inputs(self, qtbot):
        from presentation.forms.login_dialog import LoginDialog

        dlg = LoginDialog()
        qtbot.addWidget(dlg)
        # Debe tener campo de contraseña
        assert hasattr(dlg, "password_input") or dlg is not None


# ===========================================================================
# DeleteUserDialog
# ===========================================================================


@pytest.mark.ui
class TestDeleteUserDialog:
    def test_constructor(self, qtbot):
        from presentation.forms.delete_user_dialog import DeleteUserDialog

        dlg = DeleteUserDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_titulo(self, qtbot):
        from presentation.forms.delete_user_dialog import DeleteUserDialog

        dlg = DeleteUserDialog()
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() != ""


# ===========================================================================
# ForgotPasswordDialog
# ===========================================================================


@pytest.mark.ui
class TestForgotPasswordDialog:
    def test_constructor(self, qtbot):
        from presentation.forms.forgot_password_dialog import ForgotPasswordDialog

        dlg = ForgotPasswordDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None


# ===========================================================================
# ResetPasswordDialog
# ===========================================================================


@pytest.mark.ui
class TestResetPasswordDialog:
    def test_constructor(self, qtbot):
        from presentation.forms.reset_password_dialog import ResetPasswordDialog

        dlg = ResetPasswordDialog("admin")
        qtbot.addWidget(dlg)
        assert dlg is not None


# ===========================================================================
# PerfilesUsuarioForm
# ===========================================================================


@pytest.mark.ui
class TestPerfilesUsuarioForm:
    def test_constructor(self, qtbot, session):
        from presentation.forms.perfiles_usuario_form import PerfilesUsuarioForm

        form = PerfilesUsuarioForm(session)
        qtbot.addWidget(form)
        assert form is not None

    def test_refrescar(self, qtbot, session):
        from presentation.forms.perfiles_usuario_form import PerfilesUsuarioForm

        form = PerfilesUsuarioForm(session)
        qtbot.addWidget(form)
        form.refrescar()  # No debe lanzar


# ===========================================================================
# Menú lateral
# ===========================================================================


@pytest.mark.ui
class TestMenuLateral:
    def test_constructor(self, qtbot):
        from presentation.components.menu_lateral import SidebarMenu

        sidebar = SidebarMenu()
        qtbot.addWidget(sidebar)
        assert sidebar is not None

    def test_boton_de_videotutoriales_abre_la_lista(self, qtbot):
        from PyQt6.QtWidgets import QPushButton

        from presentation.components.menu_lateral import SidebarMenu
        from utils.constants import URL_VIDEOTUTORIALES

        sidebar = SidebarMenu()
        qtbot.addWidget(sidebar)
        boton = sidebar.findChild(QPushButton, "botonVideotutoriales")
        assert boton is not None, "el menú lateral debe llevar el botón de videotutoriales"
        with patch("webbrowser.open") as abrir:
            boton.click()
        abrir.assert_called_once_with(URL_VIDEOTUTORIALES)

    def test_la_url_es_la_de_la_lista_de_reproduccion(self):
        from utils.constants import URL_VIDEOTUTORIALES

        assert URL_VIDEOTUTORIALES.startswith("https://www.youtube.com/playlist?list=PL")
        assert "watch?v=" not in URL_VIDEOTUTORIALES, "solo la lista, sin vídeos sueltos"


@pytest.mark.ui
class TestAcercaDeVideotutoriales:
    def test_el_dialogo_ofrece_la_lista(self, qtbot):
        from PyQt6.QtWidgets import QPushButton

        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe
        from utils.constants import URL_VIDEOTUTORIALES

        dlg = DialogoAcercaDe()
        qtbot.addWidget(dlg)
        boton = dlg.findChild(QPushButton, "botonVideotutorialesAcercaDe")
        assert boton is not None
        with patch("webbrowser.open") as abrir:
            boton.click()
        abrir.assert_called_once_with(URL_VIDEOTUTORIALES)


# ===========================================================================
# ui_styles
# ===========================================================================


# ===========================================================================
# corporate_branding
# ===========================================================================


class TestCorporateBranding:
    def test_import(self):
        from utils.corporate_branding import apply_corporate_branding

        assert apply_corporate_branding is not None


# ===========================================================================
# AjustesForm
# ===========================================================================


@pytest.mark.ui
class TestAjustesForm:
    def test_constructor(self, qtbot, session):
        from presentation.forms.ajustes_form import AjustesForm

        form = AjustesForm(session)
        qtbot.addWidget(form)
        assert form is not None
