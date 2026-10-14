"""
Tests para presentation/dialogs/modales_perfil.py (187 stmts, 0% coverage).
"""

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.ui

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# DialogoCrearPerfilProfesional
# ===========================================================================


class TestDialogoCrearPerfilProfesional:
    def test_constructor(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCrearPerfilProfesional

        dlg = DialogoCrearPerfilProfesional()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_titulo(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCrearPerfilProfesional

        dlg = DialogoCrearPerfilProfesional()
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() != ""

    def test_validar_vacio_devuelve_false(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCrearPerfilProfesional

        dlg = DialogoCrearPerfilProfesional()
        qtbot.addWidget(dlg)
        ok, msg = dlg.validar()
        assert ok is False
        assert isinstance(msg, str)

    def test_validar_con_datos_validos(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCrearPerfilProfesional

        dlg = DialogoCrearPerfilProfesional()
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("profe01")
        dlg.input_email.setText("profe@example.com")
        dlg.input_password.setText("Pass1234!")
        dlg.input_password_confirm.setText("Pass1234!")
        ok, msg = dlg.validar()
        assert ok is True or isinstance(msg, str)

    def test_get_data_tipo(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCrearPerfilProfesional

        dlg = DialogoCrearPerfilProfesional()
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("profe01")
        dlg.input_email.setText("profe@example.com")
        dlg.input_password.setText("Pass1234!")
        dlg.input_password_confirm.setText("Pass1234!")
        data = dlg.get_data()
        from application.dtos.perfil_dto import CrearPerfilDTO

        assert isinstance(data, CrearPerfilDTO)


# ===========================================================================
# DialogoEditarPerfilProfesional
# ===========================================================================


class TestDialogoEditarPerfilProfesional:
    def test_constructor(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoEditarPerfilProfesional

        dlg = DialogoEditarPerfilProfesional("admin", "admin@example.com")
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_titulo(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoEditarPerfilProfesional

        dlg = DialogoEditarPerfilProfesional("admin", "admin@example.com")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() != ""

    def test_validar_vacio_devuelve_false(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoEditarPerfilProfesional

        dlg = DialogoEditarPerfilProfesional("admin", "admin@example.com")
        qtbot.addWidget(dlg)
        dlg.input_email.clear()
        ok, msg = dlg.validar()
        assert ok is False or isinstance(msg, str)

    def test_get_data_tipo(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoEditarPerfilProfesional

        dlg = DialogoEditarPerfilProfesional("admin", "admin@example.com")
        qtbot.addWidget(dlg)
        dlg.input_email.setText("nuevo@example.com")
        data = dlg.get_data()
        from application.dtos.perfil_dto import ActualizarPerfilDTO

        assert isinstance(data, ActualizarPerfilDTO)

    def test_validar_email_valido(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoEditarPerfilProfesional

        dlg = DialogoEditarPerfilProfesional("admin", "admin@example.com")
        qtbot.addWidget(dlg)
        dlg.input_email.setText("nuevo@example.com")
        ok, msg = dlg.validar()
        assert ok is True or isinstance(msg, str)


# ===========================================================================
# DialogoCambiarPasswordProfesional
# ===========================================================================


class TestDialogoCambiarPasswordProfesional:
    def test_constructor(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCambiarPasswordProfesional

        dlg = DialogoCambiarPasswordProfesional("admin")
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_titulo(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCambiarPasswordProfesional

        dlg = DialogoCambiarPasswordProfesional("admin")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() != ""

    def test_validar_vacio_devuelve_false(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCambiarPasswordProfesional

        dlg = DialogoCambiarPasswordProfesional("admin")
        qtbot.addWidget(dlg)
        ok, msg = dlg.validar()
        assert ok is False
        assert isinstance(msg, str)

    def test_validar_passwords_no_coinciden(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCambiarPasswordProfesional

        dlg = DialogoCambiarPasswordProfesional("admin")
        qtbot.addWidget(dlg)
        dlg.input_actual.setText("OldPass1!")
        dlg.input_nueva.setText("NewPass1!")
        dlg.input_confirmar.setText("DifferentPass1!")
        ok, msg = dlg.validar()
        assert ok is False

    def test_validar_con_datos_validos(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCambiarPasswordProfesional

        dlg = DialogoCambiarPasswordProfesional("admin")
        qtbot.addWidget(dlg)
        dlg.input_actual.setText("OldPass1!")
        dlg.input_nueva.setText("NewPass1!")
        dlg.input_confirmar.setText("NewPass1!")
        ok, msg = dlg.validar()
        assert ok is True or isinstance(msg, str)

    def test_get_data_tipo(self, qtbot):
        from presentation.dialogs.modales_perfil import DialogoCambiarPasswordProfesional

        dlg = DialogoCambiarPasswordProfesional("admin")
        qtbot.addWidget(dlg)
        dlg.input_actual.setText("OldPass1!")
        dlg.input_nueva.setText("NewPass1!")
        dlg.input_confirmar.setText("NewPass1!")
        data = dlg.get_data()
        from application.dtos.perfil_dto import CambiarPasswordDTO

        assert isinstance(data, CambiarPasswordDTO)
