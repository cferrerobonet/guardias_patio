"""Diálogos modales profesionales para gestión de perfiles."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

import ui_styles as styles
from application.dtos.perfil_dto import ActualizarPerfilDTO, CambiarPasswordDTO, CrearPerfilDTO


class DialogoCrearPerfilProfesional(QDialog):
    """Modal profesional para crear un nuevo perfil."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nuevo Perfil")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("➕ Crear Nuevo Perfil de Usuario")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Se creará un nuevo perfil con su propia base de datos "
            "y configuración independiente."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Nombre de usuario único")
        self.input_usuario.setMinimumHeight(32)
        form_layout.addRow("Usuario:", self.input_usuario)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("correo@ejemplo.com")
        self.input_email.setMinimumHeight(32)
        form_layout.addRow("Email:", self.input_email)

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Mínimo 4 caracteres")
        self.input_password.setMinimumHeight(32)
        form_layout.addRow("Contraseña:", self.input_password)

        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setPlaceholderText("Repetir contraseña")
        self.input_password_confirm.setMinimumHeight(32)
        form_layout.addRow("Confirmar:", self.input_password_confirm)

        layout.addLayout(form_layout)

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        # Estilar botones
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("✅ Crear")
        botones.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet(
            styles.STYLE_BUTTON_SUCCESS
        )
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Cancelar")

        layout.addWidget(botones)

    def get_data(self) -> CrearPerfilDTO:
        """Obtiene los datos del formulario."""
        return CrearPerfilDTO(
            username=self.input_usuario.text().strip(),
            email=self.input_email.text().strip(),
            password=self.input_password.text(),
        )

    def validar(self) -> tuple[bool, str]:
        """Valida los datos antes de aceptar."""
        if not self.input_usuario.text().strip():
            return False, "El nombre de usuario es obligatorio"

        if not self.input_email.text().strip():
            return False, "El email es obligatorio"

        if "@" not in self.input_email.text() or "." not in self.input_email.text():
            return False, "El email no es válido"

        if len(self.input_password.text()) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres"

        if self.input_password.text() != self.input_password_confirm.text():
            return False, "Las contraseñas no coinciden"

        return True, ""

    def accept(self):
        """Override para validar antes de cerrar."""
        valido, mensaje = self.validar()
        if not valido:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Validación", mensaje)
            return

        super().accept()


class DialogoEditarPerfilProfesional(QDialog):
    """Modal profesional para editar un perfil existente."""

    def __init__(self, username: str, email_actual: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"Editar Perfil: {username}")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui(email_actual)

    def _setup_ui(self, email_actual: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Título
        titulo = QLabel(f"✏️ Editar Perfil: {self.username}")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel("Modifica el email del perfil. El nombre de usuario no se puede cambiar.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        label_usuario = QLabel(self.username)
        label_usuario.setStyleSheet("font-weight: bold; color: #333;")
        form_layout.addRow("Usuario:", label_usuario)

        self.input_email = QLineEdit()
        self.input_email.setText(email_actual)
        self.input_email.setPlaceholderText("correo@ejemplo.com")
        self.input_email.setMinimumHeight(32)
        form_layout.addRow("Email:", self.input_email)

        layout.addLayout(form_layout)

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        botones.button(QDialogButtonBox.StandardButton.Ok).setText("💾 Guardar")
        botones.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet(
            styles.STYLE_BUTTON_PRIMARY
        )
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Cancelar")

        layout.addWidget(botones)

    def get_data(self) -> ActualizarPerfilDTO:
        """Obtiene los datos del formulario."""
        return ActualizarPerfilDTO(
            username=self.username,
            email=self.input_email.text().strip(),
        )

    def validar(self) -> tuple[bool, str]:
        """Valida los datos antes de aceptar."""
        if not self.input_email.text().strip():
            return False, "El email es obligatorio"

        if "@" not in self.input_email.text() or "." not in self.input_email.text():
            return False, "El email no es válido"

        return True, ""

    def accept(self):
        """Override para validar antes de cerrar."""
        valido, mensaje = self.validar()
        if not valido:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Validación", mensaje)
            return

        super().accept()


class DialogoCambiarPasswordProfesional(QDialog):
    """Modal profesional para cambiar contraseña."""

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle("Cambiar Contraseña")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Título
        titulo = QLabel(f"🔐 Cambiar Contraseña: {self.username}")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF9800;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel("Por seguridad, debes ingresar tu contraseña actual.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.input_actual = QLineEdit()
        self.input_actual.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_actual.setPlaceholderText("Contraseña actual")
        self.input_actual.setMinimumHeight(32)
        form_layout.addRow("Actual:", self.input_actual)

        self.input_nueva = QLineEdit()
        self.input_nueva.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_nueva.setPlaceholderText("Nueva contraseña (mín. 4 caracteres)")
        self.input_nueva.setMinimumHeight(32)
        form_layout.addRow("Nueva:", self.input_nueva)

        self.input_confirmar = QLineEdit()
        self.input_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirmar.setPlaceholderText("Repetir nueva contraseña")
        self.input_confirmar.setMinimumHeight(32)
        form_layout.addRow("Confirmar:", self.input_confirmar)

        layout.addLayout(form_layout)

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        botones.button(QDialogButtonBox.StandardButton.Ok).setText("🔒 Cambiar")
        botones.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet(
            styles.STYLE_BUTTON_WARNING
        )
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Cancelar")

        layout.addWidget(botones)

    def get_data(self) -> CambiarPasswordDTO:
        """Obtiene los datos del formulario."""
        return CambiarPasswordDTO(
            username=self.username,
            password_actual=self.input_actual.text(),
            password_nueva=self.input_nueva.text(),
            password_confirmacion=self.input_confirmar.text(),
        )

    def validar(self) -> tuple[bool, str]:
        """Valida los datos antes de aceptar."""
        if not self.input_actual.text():
            return False, "Debes ingresar tu contraseña actual"

        if len(self.input_nueva.text()) < 4:
            return False, "La nueva contraseña debe tener al menos 4 caracteres"

        if self.input_nueva.text() != self.input_confirmar.text():
            return False, "Las contraseñas nuevas no coinciden"

        return True, ""

    def accept(self):
        """Override para validar antes de cerrar."""
        valido, mensaje = self.validar()
        if not valido:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Validación", mensaje)
            return

        super().accept()
