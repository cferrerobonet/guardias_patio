"""
Diálogo para resetear contraseña con código de recuperación
"""

import hashlib
from datetime import datetime

import bcrypt
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sync.sync_manager import UserAuth
from utils.ui_helpers import get_corporate_icon


class ResetPasswordDialog(QDialog):
    """Diálogo para resetear la contraseña con código de recuperación."""

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_auth = UserAuth()
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Cambiar Contraseña")
        self.setWindowIcon(get_corporate_icon())
        self.setModal(True)
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel(f"Cambiar Contraseña de: {self.username}")
        title.setObjectName("tituloDialogo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(15)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Código de recuperación")
        self.code_input.setMinimumHeight(35)
        self.code_input.setAccessibleName("Campo código de recuperación")
        form_layout.addRow("🔑 Código:", self.code_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Nueva contraseña")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setMinimumHeight(35)
        self.new_password_input.setAccessibleName("Campo nueva contraseña")
        form_layout.addRow("Nueva Contraseña:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirmar nueva contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setMinimumHeight(35)
        self.confirm_password_input.returnPressed.connect(self.reset_password)
        self.confirm_password_input.setAccessibleName("Campo confirmar nueva contraseña")
        form_layout.addRow("Confirmar:", self.confirm_password_input)

        layout.addLayout(form_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(40, 20, 40, 20)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setAccessibleName("Botón cancelar recuperación de contraseña")
        buttons_layout.addWidget(cancel_btn)

        reset_btn = QPushButton("Cambiar Contraseña")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_password)
        reset_btn.setDefault(True)
        reset_btn.setAccessibleName("Botón confirmar nueva contraseña")
        reset_btn.setProperty("success", "true")
        buttons_layout.addWidget(reset_btn)

        layout.addLayout(buttons_layout)

        # A11Y: Tab order
        QWidget.setTabOrder(self.code_input, self.new_password_input)
        QWidget.setTabOrder(self.new_password_input, self.confirm_password_input)
        QWidget.setTabOrder(self.confirm_password_input, reset_btn)
        QWidget.setTabOrder(reset_btn, cancel_btn)

    def reset_password(self):
        """Resetea la contraseña del usuario."""
        code = self.code_input.text().strip()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not code:
            QMessageBox.warning(
                self, "Campo vacío", "Por favor introduce el código de recuperación"
            )
            return

        if not new_password:
            QMessageBox.warning(self, "Campo vacío", "Por favor introduce la nueva contraseña")
            return

        policy_ok, policy_msg = self.user_auth.validate_password_policy(new_password)
        if not policy_ok:
            QMessageBox.warning(self, "Contraseña débil", policy_msg)
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Contraseñas no coinciden", "Las contraseñas no son iguales")
            self.confirm_password_input.clear()
            return

        # Verificar código
        user_data = self.user_auth.users.get(self.username)
        if not user_data:
            QMessageBox.critical(self, "Error", "Usuario no encontrado")
            return

        # Verificar TTL
        expires_str = user_data.get("recovery_code_expires")
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str)
                if datetime.now() > expires:
                    QMessageBox.warning(
                        self, "Código expirado",
                        "El código de recuperación ha expirado. Solicita uno nuevo."
                    )
                    return
            except (ValueError, TypeError):
                pass

        # Verificar código
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if user_data.get("recovery_code_hash") != code_hash:
            QMessageBox.warning(self, "Código inválido", "El código de recuperación no es correcto")
            return

        # Cambiar contraseña
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user_data["password_hash"] = password_hash

        # Limpiar código de recuperación
        if "recovery_code" in user_data:
            del user_data["recovery_code"]
        if "recovery_code_hash" in user_data:
            del user_data["recovery_code_hash"]
        if "recovery_code_expires" in user_data:
            del user_data["recovery_code_expires"]

        self.user_auth._save_users()

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Contraseña cambiada")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        msg.setText(
            f"La contraseña de <span style='color: #0E5FA8; font-style: italic;'>"
            f"{self.username}</span> ha sido cambiada correctamente.<br><br>"
            f"Ahora puedes iniciar sesión con tu nueva contraseña."
        )
        msg.exec()

        self.accept()
