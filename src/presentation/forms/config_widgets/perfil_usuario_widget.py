"""
Widget de perfil de usuario.

Muestra y permite editar información del usuario actual:
- Nombre de usuario (solo lectura)
- Email (editable)
- Botón cambiar contraseña
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

import ui_styles as styles


class PerfilUsuarioWidget(QGroupBox):
    """
    Widget para gestionar el perfil del usuario actual.

    Muestra información del usuario y permite:
    - Ver nombre de usuario (solo lectura)
    - Editar email
    - Cambiar contraseña mediante botón

    Signals:
        email_changed: Emitido cuando cambia el email
        password_change_requested: Emitido cuando se solicita cambiar contraseña
    """

    # Señales
    email_changed = pyqtSignal()
    password_change_requested = pyqtSignal()

    def __init__(self, parent=None, user_auth=None, current_username: str = ""):
        """
        Inicializa el widget de perfil de usuario.

        Args:
            parent: Widget padre opcional
            user_auth: Objeto de autenticación de usuario
            current_username: Nombre del usuario actual
        """
        super().__init__("👤 Mi Perfil de Usuario", parent)
        self.setStyleSheet(styles.STYLE_GROUPBOX)
        self.user_auth = user_auth
        self.current_username = current_username
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Crea la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        # ===== Nombre de usuario (solo lectura) =====
        label_username = QLabel("Usuario:")
        label_username.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_username)

        self.username_display = QLineEdit()
        self.username_display.setText(self.current_username)
        self.username_display.setReadOnly(True)
        self.username_display.setStyleSheet(
            """
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
                font-weight: 500;
            }
        """
        )
        layout.addWidget(self.username_display)

        # ===== Email (editable) =====
        label_email = QLabel("Email:")
        label_email.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_email)

        # Obtener email actual del usuario
        current_email = ""
        if self.user_auth and self.current_username:
            user_data = self.user_auth.users.get(self.current_username, {})
            current_email = user_data.get("email", "")

        self.email_input = QLineEdit()
        self.email_input.setText(current_email)
        self.email_input.setPlaceholderText("tu@email.com")
        self.email_input.setStyleSheet(styles.STYLE_INPUT)
        self.email_input.setToolTip(
            "Email para notificaciones del sistema\nSe usa para envío de reportes y alertas"
        )
        self.email_input.textChanged.connect(self.email_changed.emit)
        layout.addWidget(self.email_input)

        # ===== Botón cambiar contraseña =====
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        self.change_password_btn = QPushButton("🔒 Cambiar Contraseña")
        self.change_password_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.change_password_btn.setToolTip("Cambiar la contraseña de acceso al sistema")
        self.change_password_btn.clicked.connect(self.password_change_requested.emit)
        btn_layout.addWidget(self.change_password_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    # ===== API PÚBLICA: GET/SET =====

    def get_email(self) -> str:
        """
        Obtiene el email del usuario.

        Returns:
            str: Email actual del usuario
        """
        return (self.email_input.text() or "").strip()

    def set_email(self, email: str) -> None:
        """
        Establece el email del usuario.

        Args:
            email: Nuevo email del usuario
        """
        self.email_input.setText(email or "")

    def get_username(self) -> str:
        """
        Obtiene el nombre de usuario (solo lectura).

        Returns:
            str: Nombre del usuario actual
        """
        return self.current_username

    def validar(self) -> tuple[bool, str]:
        """
        Valida el email del usuario.

        Returns:
            tuple: (es_valido, mensaje_error)
                - es_valido: True si el email es válido
                - mensaje_error: Descripción del error si no es válido
        """
        email = self.get_email()

        # Email es opcional
        if not email:
            return True, ""

        # Validación básica de formato
        if "@" not in email or "." not in email:
            return False, "El email debe tener un formato válido (ejemplo@dominio.com)"

        # Validación de longitud
        if len(email) < 5 or len(email) > 100:
            return False, "El email debe tener entre 5 y 100 caracteres"

        return True, ""
