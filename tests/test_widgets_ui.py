"""
Tests para widgets de UI: GestionCursosWidget, ConectividadForm, SMTPConfigWidget,
SFTPConfigWidget y módulos de presentación con 0% de coverage.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# GestionCursosWidget
# ===========================================================================


@pytest.mark.ui
class TestGestionCursosWidget:
    def test_constructor(self, qtbot, session):
        from presentation.widgets.gestion_cursos_widget import GestionCursosWidget

        w = GestionCursosWidget(session)
        qtbot.addWidget(w)
        assert w is not None

    def test_refrescar(self, qtbot, session):
        from presentation.widgets.gestion_cursos_widget import GestionCursosWidget

        w = GestionCursosWidget(session)
        qtbot.addWidget(w)
        w.refrescar()  # No debe lanzar

    def test_obtener_curso_seleccionado_sin_seleccion(self, qtbot, session):
        from presentation.widgets.gestion_cursos_widget import GestionCursosWidget

        w = GestionCursosWidget(session)
        qtbot.addWidget(w)
        # Sin fila seleccionada → None
        result = w._obtener_curso_seleccionado_id()
        assert result is None

    def test_calcular_estadisticas_curso(self, qtbot, session):
        from presentation.widgets.gestion_cursos_widget import GestionCursosWidget

        w = GestionCursosWidget(session)
        qtbot.addWidget(w)
        # Con un curso_id inexistente devuelve dict
        result = w._calcular_estadisticas_curso(999)
        assert isinstance(result, dict)

    def test_show_event(self, qtbot, session):
        from PyQt6.QtGui import QShowEvent

        from presentation.widgets.gestion_cursos_widget import GestionCursosWidget

        w = GestionCursosWidget(session)
        qtbot.addWidget(w)
        event = QShowEvent()
        w.showEvent(event)  # No debe lanzar


# ===========================================================================
# ConectividadForm
# ===========================================================================


@pytest.mark.ui
class TestConectividadForm:
    def test_constructor(self, qtbot, session):
        from presentation.forms.conectividad_form import ConectividadForm

        form = ConectividadForm(session)
        qtbot.addWidget(form)
        assert form is not None

    def test_has_smtp_widget(self, qtbot, session):
        from presentation.forms.conectividad_form import ConectividadForm

        form = ConectividadForm(session)
        qtbot.addWidget(form)
        assert hasattr(form, "smtp_widget")

    def test_has_sftp_widget(self, qtbot, session):
        from presentation.forms.conectividad_form import ConectividadForm

        form = ConectividadForm(session)
        qtbot.addWidget(form)
        assert hasattr(form, "sftp_widget")

    def test_refrescar(self, qtbot, session):
        from presentation.forms.conectividad_form import ConectividadForm

        form = ConectividadForm(session)
        qtbot.addWidget(form)
        form.refrescar()  # No debe lanzar


# ===========================================================================
# SMTPConfigWidget
# ===========================================================================


@pytest.mark.ui
class TestSMTPConfigWidget:
    def test_constructor(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        assert w is not None

    def test_get_config_dict(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        cfg = w.get_config_dict()
        assert isinstance(cfg, dict)

    def test_set_config_dict(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        w.set_config_dict(
            {
                "smtp_host": "mail.example.com",
                "smtp_port": "587",
                "smtp_user": "user@example.com",
                "smtp_password": "pass",
                "smtp_from": "user@example.com",
                "smtp_use_tls": True,
            }
        )

    def test_load_config(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        w.load_config()  # No debe lanzar

    def test_save_config(self, qtbot):
        from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

        w = SMTPConfigWidget()
        qtbot.addWidget(w)
        # save_config puede devolver bool
        with patch.object(w, "_show_global_warning", return_value=False):
            result = w.save_config()
        assert isinstance(result, bool)


# ===========================================================================
# SFTPConfigWidget
# ===========================================================================


@pytest.mark.ui
class TestSFTPConfigWidget:
    def test_constructor(self, qtbot):
        from presentation.forms.config_widgets.sftp_widget import SFTPConfigWidget

        w = SFTPConfigWidget()
        qtbot.addWidget(w)
        assert w is not None

    def test_get_config_dict(self, qtbot):
        from presentation.forms.config_widgets.sftp_widget import SFTPConfigWidget

        w = SFTPConfigWidget()
        qtbot.addWidget(w)
        cfg = w.get_config_dict()
        assert isinstance(cfg, dict)

    def test_load_config(self, qtbot):
        from presentation.forms.config_widgets.sftp_widget import SFTPConfigWidget

        w = SFTPConfigWidget()
        qtbot.addWidget(w)
        w.load_config()  # No debe lanzar


# ===========================================================================
# Config widgets: AjustesWidget, FechasRecreosWidget
# ===========================================================================


@pytest.mark.ui
class TestAjustesWidget:
    def test_constructor(self, qtbot):
        from presentation.forms.config_widgets.ajustes_widget import AjustesWidget

        w = AjustesWidget()
        qtbot.addWidget(w)
        assert w is not None


@pytest.mark.ui
class TestFechasRecreosWidget:
    def test_constructor(self, qtbot):
        from presentation.forms.config_widgets.fechas_recreos_widget import FechasRecreosWidget

        w = FechasRecreosWidget()
        qtbot.addWidget(w)
        assert w is not None


@pytest.mark.ui
class TestFestivosWidget:
    def test_constructor(self, qtbot):
        from presentation.forms.config_widgets.festivos_widget import FestivosWidget

        w = FestivosWidget()
        qtbot.addWidget(w)
        assert w is not None


# ===========================================================================
# ChangePasswordDialog
# ===========================================================================


@pytest.mark.ui
class TestChangePasswordDialog:
    def test_constructor(self, qtbot):
        from presentation.forms.change_password_dialog import ChangePasswordDialog

        with patch("presentation.forms.change_password_dialog.UserAuth") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.users = {"admin": {"email": "admin@test.com", "password_hash": ""}}
            mock_auth_cls.return_value = mock_auth
            dlg = ChangePasswordDialog("admin")
            qtbot.addWidget(dlg)
            assert dlg is not None

    def test_titulo(self, qtbot):
        from presentation.forms.change_password_dialog import ChangePasswordDialog

        with patch("presentation.forms.change_password_dialog.UserAuth") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.users = {}
            mock_auth_cls.return_value = mock_auth
            dlg = ChangePasswordDialog("admin")
            qtbot.addWidget(dlg)
            assert dlg.windowTitle() != ""


# ===========================================================================
# SyncProgressDialog
# ===========================================================================


@pytest.mark.ui
class TestSyncProgressDialog:
    def test_constructor(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog

        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_update_progress(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog

        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.update_progress(1, "Exportando", "Procesando datos...")

    def test_set_step_exporting(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog

        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_exporting(100)

    def test_set_step_connecting(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog

        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_connecting()

    def test_set_step_uploading(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog

        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_uploading(512)

    def test_set_step_complete(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog

        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_complete(success=True)

    def test_set_step_error(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog

        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_error("Error de conexión")


# ===========================================================================
# SessionLockedDialog
# ===========================================================================


@pytest.mark.ui
class TestSessionLockedDialog:
    def test_constructor(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog

        lock_info = {
            "user_id": "admin",
            "hostname": "PC01",
            "ip_address": "192.168.1.1",
            "started_at": "2024-01-15T10:00:00",
            "last_heartbeat": "2024-01-15T10:05:00",
        }
        dlg = SessionLockedDialog(lock_info)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_format_datetime_valido(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog

        dlg = SessionLockedDialog({})
        qtbot.addWidget(dlg)
        result = dlg._format_datetime("2024-01-15T10:00:00")
        assert "2024" in result

    def test_format_datetime_none(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog

        dlg = SessionLockedDialog({})
        qtbot.addWidget(dlg)
        result = dlg._format_datetime(None)
        assert result == "Desconocido"

    def test_format_datetime_invalido(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog

        dlg = SessionLockedDialog({})
        qtbot.addWidget(dlg)
        result = dlg._format_datetime("no-es-fecha")
        assert isinstance(result, str)


# ===========================================================================
# PerfilUsuarioWidget
# ===========================================================================


@pytest.mark.ui
class TestPerfilUsuarioWidget:
    def test_constructor(self, qtbot):
        from presentation.forms.config_widgets.perfil_usuario_widget import PerfilUsuarioWidget

        w = PerfilUsuarioWidget()
        qtbot.addWidget(w)
        assert w is not None
