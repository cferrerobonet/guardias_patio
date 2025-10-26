"""
Diálogo para recuperación de contraseña por email
"""

import hashlib
import secrets

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
from services.email_service import get_email_service
from sync.sync_manager import UserAuth
from utils.ui_helpers import get_corporate_icon


class ForgotPasswordDialog(QDialog):
    """Diálogo para solicitar recuperación de contraseña."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_auth = UserAuth()
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("🔑 Recuperar Contraseña")
        self.setWindowIcon(get_corporate_icon())
        self.setModal(True)
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Recuperación de Contraseña")
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

        # Información
        info = QLabel(
            "Introduce tu nombre de usuario o email.\n"
            "Te enviaremos un código de recuperación a tu correo."
        )
        info.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #374151;
                padding: 10px 40px;
            }
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(15)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuario o email")
        self.user_input.setMinimumHeight(35)
        self.user_input.returnPressed.connect(self.send_recovery_email)
        form_layout.addRow("👤 Usuario/Email:", self.user_input)

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

        send_btn = QPushButton("📧 Enviar Código")
        send_btn.setMinimumHeight(40)
        send_btn.clicked.connect(self.send_recovery_email)
        send_btn.setDefault(True)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        buttons_layout.addWidget(send_btn)

        layout.addLayout(buttons_layout)

    def send_recovery_email(self):
        """Envía el email de recuperación."""
        user_input = self.user_input.text().strip()

        if not user_input:
            QMessageBox.warning(
                self,
                "Campo vacío",
                "Por favor introduce tu usuario o email"
            )
            return

        # Buscar usuario
        user_data = None
        username = None

        for user, data in self.user_auth.users.items():
            if user == user_input or data.get("email") == user_input:
                user_data = data
                username = user
                break

        if not user_data:
            QMessageBox.warning(
                self,
                "Usuario no encontrado",
                "No existe ningún usuario con ese nombre o email"
            )
            return

        email = user_data.get("email")
        if not email:
            QMessageBox.warning(
                self,
                "Sin email",
                f"El usuario '{username}' no tiene un email registrado.\n\n"
                "No es posible recuperar la contraseña sin email."
            )
            return

        # Generar código de recuperación
        recovery_code = secrets.token_urlsafe(32)

        # Guardar código en datos del usuario (temporal)
        user_data["recovery_code"] = recovery_code
        user_data["recovery_code_hash"] = hashlib.sha256(
            recovery_code.encode()
        ).hexdigest()
        self.user_auth._save_users()

        # Obtener servicio de email
        email_service = get_email_service()

        if not email_service:
            QMessageBox.critical(
                self,
                "❌ SMTP No Configurado",
                "El sistema de envío de emails no está configurado.\n\n"
                "Por favor contacta al administrador para configurar:\n"
                "• Servidor SMTP\n"
                "• Puerto SMTP\n"
                "• Usuario y Contraseña\n\n"
                "Esto se configura en el menú Configuración."
            )
            return

        # Enviar email de recuperación
        success, message = email_service.send_recovery_code(
            email, username, recovery_code
        )

        if not success:
            QMessageBox.critical(
                self,
                "❌ Error al Enviar Email",
                f"No se pudo enviar el email de recuperación:\n\n{message}\n\n"
                "Verifica que:\n"
                "• Tu email esté correctamente registrado\n"
                "• La configuración SMTP sea correcta\n"
                "• Tengas conexión a Internet\n\n"
                "Si el problema persiste, contacta al administrador."
            )
            return

        # Email enviado correctamente
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("✅ Email Enviado")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        msg.setText(
            f"Se ha enviado un código de recuperación a:<br><br>"
            f"<span style='color: #007ACC; font-style: italic;'>{email}</span><br><br>"
            f"Revisa tu bandeja de entrada (y también la carpeta de spam).<br><br>"
            f"Usa el código recibido en el siguiente paso para restablecer tu contraseña."
        )
        msg.exec()

        # Abrir diálogo de reseteo
        from presentation.forms.reset_password_dialog import ResetPasswordDialog
        reset_dialog = ResetPasswordDialog(username, self)
        if reset_dialog.exec() == QDialog.DialogCode.Accepted:
            self.accept()
