"""
Diálogo para cambiar la contraseña del usuario actual.

Requiere la contraseña actual para verificar la identidad del usuario.
"""

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
)
from sync.sync_manager import UserAuth
from utils.ui_helpers import get_corporate_icon


class ChangePasswordDialog(QDialog):
    """Diálogo para cambiar la contraseña del usuario actual."""

    def __init__(self, username, parent=None):
        """
        Inicializa el diálogo.

        Args:
            username: Nombre del usuario
            parent: Widget padre
        """
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

        # Configurar flags para quitar el botón de maximizar
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

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

        # Descripción
        desc = QLabel("Por seguridad, introduce tu contraseña actual antes de cambiarla.")
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                padding: 0px 20px 10px 20px;
            }
        """)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(15)

        self.current_password_input = QLineEdit()
        self.current_password_input.setPlaceholderText("Contraseña actual")
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.setMinimumHeight(35)
        form_layout.addRow("🔑 Contraseña Actual:", self.current_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Nueva contraseña (mín. 4 caracteres)")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setMinimumHeight(35)
        form_layout.addRow("🔒 Nueva Contraseña:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirmar nueva contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setMinimumHeight(35)
        self.confirm_password_input.returnPressed.connect(self.change_password)
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

        change_btn = QPushButton("✓ Cambiar Contraseña")
        change_btn.setMinimumHeight(40)
        change_btn.clicked.connect(self.change_password)
        change_btn.setDefault(True)
        change_btn.setStyleSheet("""
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
        buttons_layout.addWidget(change_btn)

        layout.addLayout(buttons_layout)

    def change_password(self):
        """Cambia la contraseña del usuario."""
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validar campos vacíos
        if not current_password:
            QMessageBox.warning(self, "Campo vacío", "Por favor introduce tu contraseña actual")
            return

        if not new_password:
            QMessageBox.warning(self, "Campo vacío", "Por favor introduce la nueva contraseña")
            return

        # Validar longitud de nueva contraseña
        if len(new_password) < 4:
            QMessageBox.warning(
                self, "Contraseña débil", "La nueva contraseña debe tener al menos 4 caracteres"
            )
            return

        # Validar confirmación
        if new_password != confirm_password:
            QMessageBox.warning(
                self, "Contraseñas no coinciden", "Las contraseñas nuevas no son iguales"
            )
            self.confirm_password_input.clear()
            return

        # Verificar contraseña actual
        auth_ok, _auth_msg = self.user_auth.authenticate(self.username, current_password)
        if not auth_ok:
            QMessageBox.warning(
                self, "Contraseña incorrecta", "La contraseña actual no es correcta"
            )
            self.current_password_input.clear()
            return

        # Cambiar contraseña
        try:
            user_data = self.user_auth.users.get(self.username)
            if not user_data:
                QMessageBox.critical(self, "Error", "Usuario no encontrado")
                return

            # Actualizar contraseña
            password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            user_data["password_hash"] = password_hash
            self.user_auth._save_users()

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Contraseña cambiada")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                f"La contraseña de <span style='color: #007ACC; font-style: italic;'>"
                f"{self.username}</span> ha sido cambiada correctamente.<br><br>"
                f"La próxima vez que inicies sesión, usa tu nueva contraseña."
            )

            # Añadir botón OK con estilo visible
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            ok_button = msg.button(QMessageBox.StandardButton.Ok)
            ok_button.setText("Entendido")
            ok_button.setStyleSheet("""
                QPushButton {
                    min-width: 120px;
                    min-height: 35px;
                    padding: 5px 15px;
                    font-size: 13px;
                    background-color: #059669;
                    color: white;
                    border: 2px solid #047857;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #047857;
                }
                QPushButton:pressed {
                    background-color: #065f46;
                }
            """)

            msg.exec()

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cambiar la contraseña: {str(e)}")
