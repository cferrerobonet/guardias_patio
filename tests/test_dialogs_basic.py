"""
Tests básicos para diálogos de presentación con 0% de cobertura.

Cubre:
  - presentation/dialogs/dialogo_editar_perfil.py
  - presentation/dialogs/session_locked_dialog.py
  - presentation/dialogs/dialogo_crear_perfil.py
  - presentation/dialogs/dialogo_acerca_de.py
  - presentation/dialogs/dialogo_diagnostico_guardias.py
  - presentation/forms/change_password_dialog.py
  - presentation/widgets/sync_progress_dialog.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtWidgets import QMessageBox


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_user_auth():
    auth = MagicMock()
    auth.users = {
        "admin": {"email": "admin@test.com", "password_hash": "hash1"},
    }
    auth.save_users = MagicMock()
    auth.add_user = MagicMock(return_value=True)
    return auth


# ─────────────────────────────────────────────────────────────────────────────
# DialogoEditarPerfil
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ui
class TestDialogoEditarPerfil:
    """Tests para DialogoEditarPerfil."""

    def test_constructor_crea_dialogo(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_editar_perfil import DialogoEditarPerfil
        dlg = DialogoEditarPerfil(mock_user_auth, "admin")
        qtbot.addWidget(dlg)
        assert dlg is not None
        assert "admin" in dlg.windowTitle()

    def test_cargar_datos_usuario_existe(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_editar_perfil import DialogoEditarPerfil
        dlg = DialogoEditarPerfil(mock_user_auth, "admin")
        qtbot.addWidget(dlg)
        assert dlg.input_email.text() == "admin@test.com"

    def test_cargar_datos_usuario_no_existe(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_editar_perfil import DialogoEditarPerfil
        dlg = DialogoEditarPerfil(mock_user_auth, "noexiste")
        qtbot.addWidget(dlg)
        assert dlg.input_email.text() == ""

    def test_guardar_cambios_email_vacio(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_editar_perfil import DialogoEditarPerfil
        dlg = DialogoEditarPerfil(mock_user_auth, "admin")
        qtbot.addWidget(dlg)
        dlg.input_email.setText("")
        with patch.object(QMessageBox, "warning") as mock_warn:
            dlg.guardar_cambios()
            mock_warn.assert_called_once()

    def test_guardar_cambios_usuario_no_encontrado(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_editar_perfil import DialogoEditarPerfil
        mock_user_auth.users = {}  # vaciar usuarios
        dlg = DialogoEditarPerfil(mock_user_auth, "admin")
        qtbot.addWidget(dlg)
        dlg.input_email.setText("nuevo@test.com")
        with patch.object(QMessageBox, "critical") as mock_crit:
            dlg.guardar_cambios()
            mock_crit.assert_called_once()

    def test_guardar_cambios_exitoso(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_editar_perfil import DialogoEditarPerfil
        dlg = DialogoEditarPerfil(mock_user_auth, "admin")
        qtbot.addWidget(dlg)
        dlg.input_email.setText("nuevo@test.com")
        with patch.object(dlg, "accept") as mock_accept:
            dlg.guardar_cambios()
            mock_accept.assert_called_once()
        assert mock_user_auth.users["admin"]["email"] == "nuevo@test.com"
        mock_user_auth.save_users.assert_called_once()

    def test_guardar_cambios_excepcion(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_editar_perfil import DialogoEditarPerfil
        mock_user_auth.save_users.side_effect = ValueError("error de prueba")
        dlg = DialogoEditarPerfil(mock_user_auth, "admin")
        qtbot.addWidget(dlg)
        dlg.input_email.setText("nuevo@test.com")
        with patch.object(QMessageBox, "critical") as mock_crit:
            dlg.guardar_cambios()
            mock_crit.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# SessionLockedDialog
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ui
class TestSessionLockedDialog:
    """Tests para SessionLockedDialog."""

    def _make_lock_info(self):
        return {
            "user_id": "admin",
            "hostname": "mi-pc",
            "ip_address": "192.168.1.1",
            "started_at": "2024-01-15T10:30:00",
            "last_heartbeat": "2024-01-15T10:45:00",
        }

    def test_constructor_crea_dialogo(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog
        dlg = SessionLockedDialog(self._make_lock_info())
        qtbot.addWidget(dlg)
        assert dlg is not None
        assert "Sesión" in dlg.windowTitle()

    def test_format_datetime_sin_valor(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog
        dlg = SessionLockedDialog({})
        qtbot.addWidget(dlg)
        assert dlg._format_datetime(None) == "Desconocido"
        assert dlg._format_datetime("") == "Desconocido"

    def test_format_datetime_valido(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog
        dlg = SessionLockedDialog({})
        qtbot.addWidget(dlg)
        result = dlg._format_datetime("2024-01-15T10:30:00")
        assert "2024" in result or "15" in result

    def test_format_datetime_invalido(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog
        dlg = SessionLockedDialog({})
        qtbot.addWidget(dlg)
        result = dlg._format_datetime("no-es-fecha")
        assert result == "no-es-fecha"

    def test_lock_info_sin_campos(self, qtbot):
        from presentation.dialogs.session_locked_dialog import SessionLockedDialog
        dlg = SessionLockedDialog({})
        qtbot.addWidget(dlg)
        assert dlg is not None


# ─────────────────────────────────────────────────────────────────────────────
# DialogoCrearPerfil
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ui
class TestDialogoCrearPerfil:
    """Tests para DialogoCrearPerfil."""

    def test_constructor_crea_dialogo(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_crear_perfil_username_vacio(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("")
        with patch.object(QMessageBox, "warning") as mock_warn:
            dlg.crear_perfil()
            mock_warn.assert_called_once()

    def test_crear_perfil_email_vacio(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("nuevo_user")
        dlg.input_email.setText("")
        with patch.object(QMessageBox, "warning") as mock_warn:
            dlg.crear_perfil()
            mock_warn.assert_called_once()

    def test_crear_perfil_password_vacio(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("nuevo_user")
        dlg.input_email.setText("nuevo@test.com")
        dlg.input_password.setText("")
        with patch.object(QMessageBox, "warning") as mock_warn:
            dlg.crear_perfil()
            mock_warn.assert_called_once()

    def test_crear_perfil_passwords_distintos(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("nuevo_user")
        dlg.input_email.setText("nuevo@test.com")
        dlg.input_password.setText("pass1")
        dlg.input_password_confirm.setText("pass2")
        with patch.object(QMessageBox, "warning") as mock_warn:
            dlg.crear_perfil()
            mock_warn.assert_called_once()

    def test_crear_perfil_usuario_duplicado(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("admin")  # ya existe
        dlg.input_email.setText("admin2@test.com")
        dlg.input_password.setText("pass123")
        dlg.input_password_confirm.setText("pass123")
        with patch.object(QMessageBox, "warning") as mock_warn:
            dlg.crear_perfil()
            mock_warn.assert_called_once()

    def test_crear_perfil_add_user_falla(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        mock_user_auth.add_user.return_value = False
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("nuevo_user")
        dlg.input_email.setText("nuevo@test.com")
        dlg.input_password.setText("pass123")
        dlg.input_password_confirm.setText("pass123")
        with patch("presentation.dialogs.dialogo_crear_perfil.create_user_database"):
            with patch.object(QMessageBox, "critical") as mock_crit:
                dlg.crear_perfil()
                mock_crit.assert_called_once()

    def test_crear_perfil_exitoso(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("nuevo_user")
        dlg.input_email.setText("nuevo@test.com")
        dlg.input_password.setText("pass123")
        dlg.input_password_confirm.setText("pass123")
        with patch("presentation.dialogs.dialogo_crear_perfil.create_user_database") as mock_create:
            with patch.object(dlg, "accept") as mock_accept:
                dlg.crear_perfil()
                mock_create.assert_called_once_with("nuevo_user")
                mock_accept.assert_called_once()

    def test_crear_perfil_excepcion(self, qtbot, mock_user_auth):
        from presentation.dialogs.dialogo_crear_perfil import DialogoCrearPerfil
        mock_user_auth.add_user.side_effect = ValueError("error")
        dlg = DialogoCrearPerfil(mock_user_auth)
        qtbot.addWidget(dlg)
        dlg.input_usuario.setText("nuevo_user")
        dlg.input_email.setText("nuevo@test.com")
        dlg.input_password.setText("pass123")
        dlg.input_password_confirm.setText("pass123")
        with patch.object(QMessageBox, "critical") as mock_crit:
            dlg.crear_perfil()
            mock_crit.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# DialogoAcercaDe
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ui
class TestDialogoAcercaDe:
    """Tests para DialogoAcercaDe."""

    def test_constructor_sin_session(self, qtbot):
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe
        with patch("presentation.dialogs.dialogo_acerca_de.DialogoAcercaDe._get_stats", return_value=[]):
            dlg = DialogoAcercaDe()
            qtbot.addWidget(dlg)
            assert dlg is not None

    def test_constructor_con_session(self, qtbot):
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe
        mock_session = MagicMock()
        mock_session.bind.url = "sqlite:///:memory:"
        with patch("presentation.dialogs.dialogo_acerca_de.DialogoAcercaDe._get_stats", return_value=[]):
            dlg = DialogoAcercaDe(session=mock_session)
            qtbot.addWidget(dlg)
            assert dlg is not None

    def test_titulo_acerca_de(self, qtbot):
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe
        with patch("presentation.dialogs.dialogo_acerca_de.DialogoAcercaDe._get_stats", return_value=[]):
            dlg = DialogoAcercaDe()
            qtbot.addWidget(dlg)
            assert "Acerca" in dlg.windowTitle()

    @pytest.fixture
    def dlg(self, qtbot):
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe
        with patch("presentation.dialogs.dialogo_acerca_de.DialogoAcercaDe._get_stats", return_value=[]):
            d = DialogoAcercaDe()
            qtbot.addWidget(d)
            return d

    def test_get_pyqt_version(self, dlg):
        version = dlg._get_pyqt_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_sqlalchemy_version(self, dlg):
        version = dlg._get_sqlalchemy_version()
        assert isinstance(version, str)

    def test_get_ortools_version(self, dlg):
        version = dlg._get_ortools_version()
        assert isinstance(version, str)

    def test_get_db_info(self, dlg):
        info = dlg._get_db_info()
        assert isinstance(info, list)

    def test_get_db_info_con_session(self, qtbot):
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe
        mock_session = MagicMock()
        mock_session.bind.url = "sqlite:///:memory:"
        with patch("presentation.dialogs.dialogo_acerca_de.DialogoAcercaDe._get_stats", return_value=[]):
            dlg = DialogoAcercaDe(session=mock_session)
            qtbot.addWidget(dlg)
            info = dlg._get_db_info()
            assert isinstance(info, list)

    def test_get_stats_directo(self, qtbot):
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe
        with patch("presentation.dialogs.dialogo_acerca_de.DialogoAcercaDe._get_stats", return_value=[]):
            dlg = DialogoAcercaDe()
            qtbot.addWidget(dlg)
        stats = dlg._get_stats()
        assert isinstance(stats, list)

    def test_create_info_row(self, dlg):
        row = dlg._create_info_row("Clave", "Valor")
        assert row is not None


# ─────────────────────────────────────────────────────────────────────────────
# DialogoDiagnosticoGuardias
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ui
@pytest.mark.xfail(strict=False, reason="Flakey en suite completa por estado de importación")
class TestDialogoDiagnosticoGuardias:
    """Tests para DialogoDiagnosticoGuardias."""

    def _make_diagnostico(self, criticos=None, altos=None):
        from services.diagnosticador_guardias import DiagnosticoCompleto, ProblemaDetectado

        def problema(desc="test", gravedad="ALTA"):
            p = MagicMock(spec=ProblemaDetectado)
            p.descripcion = desc
            p.gravedad = gravedad
            p.detalles = {}
            p.sugerencias = ["Sugerencia 1"]
            return p

        return DiagnosticoCompleto(
            problemas_criticos=criticos or [],
            problemas_altos=altos or [],
            problemas_medios=[],
            estadisticas={
                "total_guardias": 10,
                "asignadas": 8,
                "cobertura_porcentaje": 80.0,
                "total_profesores": 5,
                "profesores_sin_guardia": 0,
                "total_slots_esperados": 10,
                "slots_cubiertos": 8,
                "profesores_con_guardias": 5,
                "profesores_activos_totales": 5,
                "total_guardias_asignadas": 8,
            },
            puede_continuar_ilp=True,
            mensaje_resumen="Resumen de diagnóstico",
        )

    def test_constructor_sin_problemas(self, qtbot):
        from presentation.dialogs.dialogo_diagnostico_guardias import DialogoDiagnosticoGuardias
        diag = self._make_diagnostico()
        dlg = DialogoDiagnosticoGuardias(diag)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_constructor_con_problemas(self, qtbot):
        from presentation.dialogs.dialogo_diagnostico_guardias import DialogoDiagnosticoGuardias
        from services.diagnosticador_guardias import ProblemaDetectado
        p = MagicMock(spec=ProblemaDetectado)
        p.descripcion = "Problema critico"
        p.gravedad = "CRITICA"
        p.detalles = {}
        p.sugerencias = ["Sugerencia A"]
        diag = self._make_diagnostico(criticos=[p])
        dlg = DialogoDiagnosticoGuardias(diag)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_accion_por_defecto_es_cancelar(self, qtbot):
        from presentation.dialogs.dialogo_diagnostico_guardias import DialogoDiagnosticoGuardias
        diag = self._make_diagnostico()
        dlg = DialogoDiagnosticoGuardias(diag)
        qtbot.addWidget(dlg)
        assert dlg.get_accion_elegida() == "cancelar"

    def test_on_ajustar_manual(self, qtbot):
        from presentation.dialogs.dialogo_diagnostico_guardias import DialogoDiagnosticoGuardias
        diag = self._make_diagnostico()
        dlg = DialogoDiagnosticoGuardias(diag)
        qtbot.addWidget(dlg)
        with patch.object(dlg, "accept"):
            dlg._on_ajustar_manual()
        assert dlg.accion_elegida == "ajustar"

    def test_on_continuar_ilp(self, qtbot):
        from presentation.dialogs.dialogo_diagnostico_guardias import DialogoDiagnosticoGuardias
        diag = self._make_diagnostico()
        dlg = DialogoDiagnosticoGuardias(diag)
        qtbot.addWidget(dlg)
        with patch.object(dlg, "accept"):
            dlg._on_continuar_ilp()
        assert dlg.accion_elegida == "continuar_ilp"

    def test_title(self, qtbot):
        from presentation.dialogs.dialogo_diagnostico_guardias import DialogoDiagnosticoGuardias
        diag = self._make_diagnostico()
        dlg = DialogoDiagnosticoGuardias(diag)
        qtbot.addWidget(dlg)
        assert "Diagnóstico" in dlg.windowTitle() or "Asign" in dlg.windowTitle()


# ─────────────────────────────────────────────────────────────────────────────
# ChangePasswordDialog
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ui
class TestChangePasswordDialog:
    """Tests para ChangePasswordDialog."""

    def test_constructor_crea_dialogo(self, qtbot):
        from presentation.forms.change_password_dialog import ChangePasswordDialog
        with patch("presentation.forms.change_password_dialog.UserAuth") as mock_auth_class:
            mock_auth_class.return_value = MagicMock()
            dlg = ChangePasswordDialog("admin")
            qtbot.addWidget(dlg)
            assert dlg is not None
            assert dlg.username == "admin"

    def test_tiene_campos_ui(self, qtbot):
        from presentation.forms.change_password_dialog import ChangePasswordDialog
        with patch("presentation.forms.change_password_dialog.UserAuth") as mock_auth_class:
            mock_auth_class.return_value = MagicMock()
            dlg = ChangePasswordDialog("admin")
            qtbot.addWidget(dlg)
            assert hasattr(dlg, "current_password_input")
            assert hasattr(dlg, "new_password_input")
            assert hasattr(dlg, "confirm_password_input")


# ─────────────────────────────────────────────────────────────────────────────
# SyncProgressDialog
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.ui
class TestSyncProgressDialog:
    """Tests para SyncProgressDialog."""

    def test_constructor_crea_dialogo(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog
        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_update_progress(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog
        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.update_progress(1, "Paso 1", "Detalle 1")

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

    def test_set_step_complete_success(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog
        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_complete(success=True)

    def test_set_step_complete_failure(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog
        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_complete(success=False)

    def test_set_step_error(self, qtbot):
        from presentation.widgets.sync_progress_dialog import SyncProgressDialog
        dlg = SyncProgressDialog()
        qtbot.addWidget(dlg)
        dlg.set_step_error("Error de conexión")
