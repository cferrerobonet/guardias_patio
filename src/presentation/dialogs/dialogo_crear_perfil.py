"""
Diálogo para crear un nuevo perfil de usuario con su base de datos.
"""

from pathlib import Path

from database.db_manager import create_user_database
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


class DialogoCrearPerfil(QDialog):
    """Diálogo para crear un nuevo perfil de usuario."""

    def __init__(self, user_auth: UserAuth, parent=None):
        super().__init__(parent)
        self.user_auth = user_auth
        self.setWindowTitle("Crear Nuevo Perfil")
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("➕ Crear Nuevo Perfil de Usuario")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Se creará un nuevo perfil con su propia base de datos y configuración independiente."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(desc)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Nombre de usuario único")
        form_layout.addRow("Usuario:", self.input_usuario)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("correo@ejemplo.com")
        form_layout.addRow("Email:", self.input_email)

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Contraseña segura")
        form_layout.addRow("Contraseña:", self.input_password)

        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setPlaceholderText("Repetir contraseña")
        form_layout.addRow("Confirmar:", self.input_password_confirm)

        layout.addLayout(form_layout)

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botones_layout.addWidget(btn_cancelar)

        btn_crear = QPushButton("✅ Crear Perfil")
        btn_crear.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_crear.clicked.connect(self.crear_perfil)
        botones_layout.addWidget(btn_crear)

        layout.addLayout(botones_layout)
        self.setLayout(layout)

    def crear_perfil(self):
        """Crea el nuevo perfil con su base de datos."""
        username = self.input_usuario.text().strip()
        email = self.input_email.text().strip()
        password = self.input_password.text()
        password_confirm = self.input_password_confirm.text()

        # Validaciones
        if not username:
            QMessageBox.warning(self, "Error", "El nombre de usuario es obligatorio")
            return

        if not email:
            QMessageBox.warning(self, "Error", "El email es obligatorio")
            return

        if not password:
            QMessageBox.warning(self, "Error", "La contraseña es obligatoria")
            return

        if password != password_confirm:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
            return

        if username in self.user_auth.users:
            QMessageBox.warning(
                self, "Error", f"Ya existe un usuario con el nombre '{username}'"
            )
            return

        try:
            # Crear usuario en UserAuth
            if not self.user_auth.add_user(username, password, email):
                QMessageBox.critical(
                    self, "Error", "No se pudo crear el usuario en el sistema"
                )
                return

            # Crear base de datos para el nuevo usuario
            create_user_database(username)

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error al crear el perfil:\n{str(e)}"
            )
