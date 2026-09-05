"""
Diálogo para crear un nuevo perfil de usuario con su base de datos.
"""

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
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

from database.db_manager import create_user_database
from sync.sync_manager import UserAuth
from utils.icons import icon_for_button


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
        titulo = QLabel("Crear Nuevo Perfil de Usuario")
        titulo.setObjectName("dialogTitle")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Se creará un nuevo perfil con su propia base de datos y configuración independiente."
        )
        desc.setWordWrap(True)
        desc.setObjectName("formDescription")
        layout.addWidget(desc)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Nombre de usuario único")
        self.input_usuario.setAccessibleName("Campo nombre de usuario")
        self.input_usuario.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[a-zA-Z0-9_\-\.]{3,50}"))
        )
        form_layout.addRow("Usuario:", self.input_usuario)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("correo@ejemplo.com")
        self.input_email.setAccessibleName("Campo correo electrónico")
        self.input_email.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
            )
        )
        form_layout.addRow("Email:", self.input_email)

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Contraseña segura")
        self.input_password.setAccessibleName("Campo contraseña del nuevo perfil")
        form_layout.addRow("Contraseña:", self.input_password)

        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setPlaceholderText("Repetir contraseña")
        self.input_password_confirm.setAccessibleName("Campo confirmar contraseña del nuevo perfil")
        form_layout.addRow("Confirmar:", self.input_password_confirm)

        layout.addLayout(form_layout)

        # Label de error inline
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #DC3545; font-size: 12px;")
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryButton")
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setAccessibleName("Botón cancelar creación de perfil")
        botones_layout.addWidget(btn_cancelar)

        btn_crear = QPushButton("Crear Perfil")
        btn_crear.setIcon(icon_for_button("check"))
        btn_crear.setAccessibleName("Botón crear nuevo perfil de usuario")
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

        # A11Y: Tab order
        QWidget.setTabOrder(self.input_usuario, self.input_email)
        QWidget.setTabOrder(self.input_email, self.input_password)
        QWidget.setTabOrder(self.input_password, self.input_password_confirm)
        QWidget.setTabOrder(self.input_password_confirm, btn_crear)
        QWidget.setTabOrder(btn_crear, btn_cancelar)

    def _mostrar_error(self, mensaje: str):
        self._error_label.setText(mensaje)
        self._error_label.setVisible(True)

    def crear_perfil(self):
        """Crea el nuevo perfil con su base de datos."""
        username = self.input_usuario.text().strip()
        email = self.input_email.text().strip()
        password = self.input_password.text()
        password_confirm = self.input_password_confirm.text()

        # Validaciones inline
        if not username:
            self._mostrar_error("El nombre de usuario es obligatorio")
            self.input_usuario.setFocus()
            return
        if not email:
            self._mostrar_error("El email es obligatorio")
            self.input_email.setFocus()
            return
        if not password:
            self._mostrar_error("La contraseña es obligatoria")
            self.input_password.setFocus()
            return
        if password != password_confirm:
            self._mostrar_error("Las contraseñas no coinciden")
            self.input_password_confirm.setFocus()
            return
        if username in self.user_auth.users:
            self._mostrar_error(f"Ya existe un usuario con el nombre '{username}'")
            self.input_usuario.setFocus()
            return
        self._error_label.setVisible(False)

        try:
            # Crear usuario en UserAuth
            if not self.user_auth.add_user(username, password, email):
                QMessageBox.critical(self, "Error", "No se pudo crear el usuario en el sistema")
                return

            # Crear base de datos para el nuevo usuario
            create_user_database(username)

            self.accept()

        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Error", f"Error al crear el perfil:\n{str(e)}")
