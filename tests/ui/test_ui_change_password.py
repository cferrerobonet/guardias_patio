"""Tests de UI para ChangePasswordDialog — validaciones de cambio de contraseña."""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from presentation.forms.change_password_dialog import ChangePasswordDialog


@pytest.fixture
def dialogo(qapp):
    d = ChangePasswordDialog(username="test_user")
    QApplication.processEvents()
    yield d
    d.close()


class TestChangePasswordRenderizado:
    def test_dialogo_se_crea_sin_crash(self, dialogo):
        assert dialogo is not None

    def test_campos_existen(self, dialogo):
        assert hasattr(dialogo, "current_password_input")
        assert hasattr(dialogo, "new_password_input")
        assert hasattr(dialogo, "confirm_password_input")

    def test_campos_son_modo_password(self, dialogo):
        from PyQt6.QtWidgets import QLineEdit
        assert dialogo.current_password_input.echoMode() == QLineEdit.EchoMode.Password
        assert dialogo.new_password_input.echoMode() == QLineEdit.EchoMode.Password
        assert dialogo.confirm_password_input.echoMode() == QLineEdit.EchoMode.Password


class TestChangePasswordValidacion:
    def test_campo_actual_vacio_muestra_advertencia(self, qtbot, dialogo):
        """Contraseña actual vacía → QMessageBox.warning inmediato."""
        dialogo.current_password_input.setText("")
        dialogo.new_password_input.setText("NuevaPass1!")
        dialogo.confirm_password_input.setText("NuevaPass1!")
        QApplication.processEvents()

        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialogo.change_password()
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_nueva_password_vacia_muestra_advertencia(self, qtbot, dialogo):
        """Nueva contraseña vacía → advertencia."""
        dialogo.current_password_input.setText("ActualPass1!")
        dialogo.new_password_input.setText("")
        dialogo.confirm_password_input.setText("")
        QApplication.processEvents()

        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialogo.change_password()
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_password_debil_muestra_advertencia(self, qtbot, dialogo):
        """Contraseña sin mayúscula/símbolo → advertencia de política."""
        dialogo.current_password_input.setText("ActualPass1!")
        dialogo.new_password_input.setText("debil")
        dialogo.confirm_password_input.setText("debil")
        QApplication.processEvents()

        with patch.object(
            dialogo.user_auth, "validate_password_policy", return_value=(False, "Contraseña débil")
        ):
            with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
                dialogo.change_password()
                QApplication.processEvents()
                mock_warn.assert_called_once()

    def test_passwords_no_coinciden_muestra_advertencia(self, qtbot, dialogo):
        """Nueva ≠ confirmación → advertencia."""
        dialogo.current_password_input.setText("ActualPass1!")
        dialogo.new_password_input.setText("NuevaPass1!")
        dialogo.confirm_password_input.setText("OtraPass2@")
        QApplication.processEvents()

        with patch.object(
            dialogo.user_auth, "validate_password_policy", return_value=(True, "")
        ):
            with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
                dialogo.change_password()
                QApplication.processEvents()
                mock_warn.assert_called_once()

    def test_password_actual_incorrecta_muestra_advertencia(self, qtbot, dialogo):
        """Contraseña actual errónea → advertencia."""
        dialogo.current_password_input.setText("Incorrecta1!")
        dialogo.new_password_input.setText("NuevaPass1!")
        dialogo.confirm_password_input.setText("NuevaPass1!")
        QApplication.processEvents()

        with patch.object(dialogo.user_auth, "validate_password_policy", return_value=(True, "")):
            with patch.object(dialogo.user_auth, "authenticate", return_value=(False, "wrong")):
                with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
                    dialogo.change_password()
                    QApplication.processEvents()
                    mock_warn.assert_called_once()

    def test_cambio_exitoso_muestra_dialogo_confirmacion(self, qtbot, dialogo):
        """Credenciales correctas → proceso de cambio ejecutado sin crash."""
        dialogo.current_password_input.setText("ActualPass1!")
        dialogo.new_password_input.setText("NuevaPass1!")
        dialogo.confirm_password_input.setText("NuevaPass1!")
        QApplication.processEvents()

        mock_user_data = {"password_hash": "old_hash"}
        with patch.object(dialogo.user_auth, "validate_password_policy", return_value=(True, "")):
            with patch.object(dialogo.user_auth, "authenticate", return_value=(True, "ok")):
                with patch.object(dialogo.user_auth, "users", {"test_user": mock_user_data}):
                    with patch.object(dialogo.user_auth, "_save_users"):
                        with patch("PyQt6.QtWidgets.QMessageBox.exec", return_value=None):
                            with patch.object(dialogo, "accept"):
                                dialogo.change_password()
                                QApplication.processEvents()
