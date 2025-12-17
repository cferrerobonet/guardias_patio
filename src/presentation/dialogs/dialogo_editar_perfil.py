"""
Diálogo para editar un perfil de usuario existente.
"""

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
from utils.icons import icon_for_button


class DialogoEditarPerfil(QDialog):
    """Diálogo para editar un perfil de usuario existente."""

    def __init__(self, user_auth: UserAuth, username: str, parent=None):
        super().__init__(parent)
        self.user_auth = user_auth
        self.username = username
        self.setWindowTitle(f"Editar Perfil: {username}")
        self.setMinimumWidth(450)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel(f"Editar Perfil: {self.username}")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel("Modifica el email del perfil. El nombre de usuario no se puede cambiar.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(desc)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.label_usuario = QLabel(self.username)
        self.label_usuario.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Usuario:", self.label_usuario)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("correo@ejemplo.com")
        form_layout.addRow("Email:", self.input_email)

        layout.addLayout(form_layout)

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botones_layout.addWidget(btn_cancelar)

        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setIcon(icon_for_button("save"))
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_guardar.clicked.connect(self.guardar_cambios)
        botones_layout.addWidget(btn_guardar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)

    def cargar_datos(self):
        """Carga los datos actuales del perfil."""
        if self.username in self.user_auth.users:
            user_data = self.user_auth.users[self.username]
            self.input_email.setText(user_data.get("email", ""))

    def guardar_cambios(self):
        """Guarda los cambios en el perfil."""
        email = self.input_email.text().strip()

        if not email:
            QMessageBox.warning(self, "Error", "El email es obligatorio")
            return

        try:
            # Actualizar email
            if self.username in self.user_auth.users:
                self.user_auth.users[self.username]["email"] = email
                self.user_auth.save_users()
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se encontró el usuario")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar los cambios:\n{str(e)}")
