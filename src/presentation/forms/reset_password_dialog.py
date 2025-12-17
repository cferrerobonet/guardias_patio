"""
Diálogo para resetear contraseña con código de recuperación
"""

import hashlib

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
        self.setWindowTitle("🔐 Cambiar Contraseña")
        self.setWindowIcon(get_corporate_icon())
        self.setModal(True)
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel(f"Cambiar Contraseña de: {self.username}")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #007ACC;
                padding: 20px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(15)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Código de recuperación")
        self.code_input.setMinimumHeight(35)
        form_layout.addRow("🔑 Código:", self.code_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Nueva contraseña")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setMinimumHeight(35)
        form_layout.addRow("🔒 Nueva Contraseña:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirmar nueva contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setMinimumHeight(35)
        self.confirm_password_input.returnPressed.connect(self.reset_password)
        form_layout.addRow("🔒 Confirmar:", self.confirm_password_input)

        layout.addLayout(form_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(40, 20, 40, 20)

        cancel_btn = QPushButton("← Cancelar")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        buttons_layout.addWidget(cancel_btn)

        reset_btn = QPushButton("✓ Cambiar Contraseña")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_password)
        reset_btn.setDefault(True)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        buttons_layout.addWidget(reset_btn)

        layout.addLayout(buttons_layout)

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

        if len(new_password) < 4:
            QMessageBox.warning(
                self, "Contraseña débil", "La contraseña debe tener al menos 4 caracteres"
            )
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

        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if user_data.get("recovery_code_hash") != code_hash:
            QMessageBox.warning(self, "Código inválido", "El código de recuperación no es correcto")
            return

        # Cambiar contraseña
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        user_data["password_hash"] = password_hash

        # Limpiar código de recuperación
        if "recovery_code" in user_data:
            del user_data["recovery_code"]
        if "recovery_code_hash" in user_data:
            del user_data["recovery_code_hash"]

        self.user_auth._save_users()

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Contraseña cambiada")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        msg.setText(
            f"La contraseña de <span style='color: #007ACC; font-style: italic;'>"
            f"{self.username}</span> ha sido cambiada correctamente.<br><br>"
            f"Ahora puedes iniciar sesión con tu nueva contraseña."
        )
        msg.exec()

        self.accept()
