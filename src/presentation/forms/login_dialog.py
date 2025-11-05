"""
Diálogo de Login para Sistema Multi-Usuario
"""


from core.paths import get_resources_directory
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
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
from utils.icon_manager import get_icon
from utils.ui_helpers import get_corporate_icon


class RegisterDialog(QDialog):
    """Diálogo de registro de nuevo usuario con confirmación de contraseña."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_auth = UserAuth()
        self.registered_username = None
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo de registro."""
        self.setWindowTitle("📝 Registrar Nuevo Usuario")
        self.setWindowIcon(get_corporate_icon())
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMaximumWidth(500)
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Crear Nueva Cuenta")
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

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ej: carlos@ceip.es")
        self.username_input.setMinimumHeight(35)
        form_layout.addRow("👤 Usuario:", self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ej: carlos@ejemplo.com (OBLIGATORIO)")
        self.email_input.setMinimumHeight(35)
        form_layout.addRow("📧 Email *:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mínimo 4 caracteres")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        form_layout.addRow("🔑 Contraseña:", self.password_input)

        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Repite la contraseña")
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setMinimumHeight(35)
        self.password_confirm_input.returnPressed.connect(self.register)
        form_layout.addRow("🔑 Confirmar:", self.password_confirm_input)

        layout.addLayout(form_layout)

        # Requisitos de contraseña
        requirements = QLabel("✓ Mínimo 4 caracteres\n✓ Las contraseñas deben coincidir\n✓ Email obligatorio para recuperación")
        requirements.setStyleSheet("color: #6B7280; font-size: 11px; padding: 0px 40px;")
        layout.addWidget(requirements)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(40, 20, 40, 20)

        cancel_btn = QPushButton("❌ Cancelar")
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

        register_btn = QPushButton("✓ Registrarse")
        register_btn.setMinimumHeight(40)
        register_btn.clicked.connect(self.register)
        register_btn.setDefault(True)
        register_btn.setStyleSheet("""
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
        buttons_layout.addWidget(register_btn)

        layout.addLayout(buttons_layout)

    def register(self):
        """Registra un nuevo usuario con validación de contraseñas."""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()

        # Validaciones
        if not username:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Campo vacío")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText("Por favor introduce un nombre de usuario")
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.username_input.setFocus()
            return

        if not email:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Email obligatorio")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText(
                "El email es obligatorio para poder recuperar la contraseña en caso de olvido"
            )
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.email_input.setFocus()
            return

        # Validación básica de email
        if "@" not in email or "." not in email:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Email inválido")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText("Por favor introduce un email válido (ej: usuario@ejemplo.com)")
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.email_input.setFocus()
            return

        if not password:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Campo vacío")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText("Por favor introduce una contraseña")
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.password_input.setFocus()
            return

        if len(password) < 4:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Contraseña débil")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText("La contraseña debe tener al menos 4 caracteres")
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.password_input.setFocus()
            return

        if password != password_confirm:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Contraseñas no coinciden")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText("Las contraseñas introducidas no son iguales.\n"
                       "Por favor, verifica que sean idénticas.")
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.password_confirm_input.clear()
            self.password_confirm_input.setFocus()
            return

        # Intentar registrar
        if self.user_auth.register_user(username, password, email):
            from utils.ui_helpers import MESSAGEBOX_STYLE
            self.registered_username = username
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("✅ Registro exitoso")
            msg.setWindowIcon(get_corporate_icon())
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                f"Usuario <span style='color: #007ACC; font-style: italic;'>{username}</span> "
                f"registrado correctamente.<br><br>"
                f"Ahora puedes iniciar sesión con tus credenciales."
            )
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.accept()
        else:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Usuario existente")
            msg.setWindowIcon(get_corporate_icon())
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                f"El usuario <span style='color: #007ACC; font-style: italic;'>{username}</span> "
                f"ya está registrado.<br>"
                f"Por favor, elige otro nombre de usuario."
            )
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.username_input.selectAll()
            self.username_input.setFocus()


class LoginDialog(QDialog):
    """Diálogo de autenticación de usuario con selector de usuarios y logo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_auth = UserAuth()
        self.authenticated_user = None
        self.setup_ui()
        self.load_existing_users()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Iniciar Sesión - Guardias de Patio")
        self.setWindowIcon(get_icon("login", "#007ACC", 32))
        self.setModal(True)
        self.setMinimumWidth(450)

        # Eliminar botón de maximizar - solo mostrar cerrar
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        # Logo corporativo
        logo_label = QLabel()
        logo_path = get_resources_directory() / "logo.png"

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Escalar el logo manteniendo la proporción
            scaled_pixmap = pixmap.scaled(
                180, 180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Logo alternativo con texto si no existe la imagen
            logo_label.setText("🏫")
            logo_label.setStyleSheet("font-size: 64px;")

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("padding: 10px; background-color: #f8f9fa;")
        layout.addWidget(logo_label)

        # Título
        title = QLabel("Generador de\nGuardias de Patio")
        title.setStyleSheet("""
            QLabel {
                font-size: 34px;
                font-weight: bold;
                color: #007ACC;
                padding: 10px 10px 5px 10px;
                background-color: #f8f9fa;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Créditos
        credits = QLabel("(Created & Powered by CFB - Enero 2026)")
        credits.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #6c757d;
                padding: 0px 20px 20px 20px;
                background-color: #f8f9fa;
            }
        """)
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(15)

        # ComboBox para usuarios existentes
        self.username_combo = QComboBox()
        self.username_combo.setEditable(True)
        self.username_combo.setPlaceholderText("Selecciona o escribe tu usuario")
        self.username_combo.setMinimumHeight(35)
        self.username_combo.setMinimumWidth(240)
        self.username_combo.currentTextChanged.connect(self.on_user_selected)

        # Label con icono para usuario
        user_label = QLabel("👤 Usuario:")
        user_label.setStyleSheet("color: #333; font-weight: 400;")
        form_layout.addRow(user_label, self.username_combo)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Introduce tu contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.setMinimumWidth(240)
        self.password_input.returnPressed.connect(self.login)

        # Label con icono para contraseña
        password_label = QLabel("🔑 Contraseña:")
        password_label.setStyleSheet("color: #333; font-weight: 400;")
        form_layout.addRow(password_label, self.password_input)

        layout.addLayout(form_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(40, 10, 40, 20)

        self.delete_user_btn = QPushButton(" Eliminar")
        self.delete_user_btn.setIcon(get_icon("close", "white", 18))
        self.delete_user_btn.setMinimumHeight(40)
        self.delete_user_btn.clicked.connect(self.open_delete_user_dialog)
        self.delete_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #991B1B;
            }
        """)
        buttons_layout.addWidget(self.delete_user_btn)

        self.register_btn = QPushButton(" Nuevo Usuario")
        self.register_btn.setIcon(get_icon("account-plus", "white", 18))
        self.register_btn.setMinimumHeight(40)
        self.register_btn.clicked.connect(self.open_register_dialog)
        self.register_btn.setStyleSheet("""
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
        buttons_layout.addWidget(self.register_btn)

        self.login_btn = QPushButton(" Iniciar Sesión")
        self.login_btn.setIcon(get_icon("login", "white", 18))
        self.login_btn.setMinimumHeight(40)
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setDefault(True)
        self.login_btn.setStyleSheet("""
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
        buttons_layout.addWidget(self.login_btn)

        layout.addLayout(buttons_layout)

        # Link de recuperación de contraseña
        forgot_password_label = QLabel(
            '<a href="#" style="color: #007ACC;">¿Olvidaste tu contraseña?</a>'
        )
        forgot_password_label.setStyleSheet("padding: 10px; font-size: 12px;")
        forgot_password_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        forgot_password_label.setTextFormat(Qt.TextFormat.RichText)
        forgot_password_label.linkActivated.connect(self.open_forgot_password_dialog)
        forgot_password_label.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(forgot_password_label)

        # Información
        info_label = QLabel("ℹ️ Primera vez? Haz clic en Nuevo Usuario")
        info_label.setStyleSheet("color: #6B7280; font-size: 12px; padding: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def load_existing_users(self):
        """Carga la lista de usuarios existentes en el ComboBox."""
        users = list(self.user_auth.users.keys())

        if users:
            self.username_combo.addItems(sorted(users))
            # Si hay usuarios, seleccionar el primero
            self.username_combo.setCurrentIndex(0)
        else:
            # Si no hay usuarios, dejar vacío para nuevo registro
            self.username_combo.setCurrentText("")

    def on_user_selected(self, username):
        """Callback cuando se selecciona un usuario del combo."""
        if username:
            self.password_input.setFocus()

    def open_register_dialog(self):
        """Abre el diálogo de registro de nuevo usuario."""
        register_dialog = RegisterDialog(self)

        if register_dialog.exec() == QDialog.DialogCode.Accepted:
            # Usuario registrado exitosamente
            registered_user = register_dialog.registered_username

            if registered_user:
                # IMPORTANTE: Recargar usuarios desde archivo (se actualizó en RegisterDialog)
                self.user_auth.users = self.user_auth._load_users()

                # Limpiar y recargar la lista de usuarios
                self.username_combo.clear()
                users = list(self.user_auth.users.keys())

                if users:
                    self.username_combo.addItems(sorted(users))

                    # Seleccionar el usuario recién registrado
                    index = self.username_combo.findText(registered_user)
                    if index >= 0:
                        self.username_combo.setCurrentIndex(index)
                else:
                    # Si por alguna razón no hay usuarios, añadir el registrado
                    self.username_combo.addItem(registered_user)
                    self.username_combo.setCurrentText(registered_user)

                # Poner foco en contraseña
                self.password_input.setFocus()

    def open_delete_user_dialog(self):
        """Abre el diálogo de eliminación de usuario."""
        from presentation.forms.delete_user_dialog import DeleteUserDialog

        delete_dialog = DeleteUserDialog(self)

        if delete_dialog.exec() == QDialog.DialogCode.Accepted:
            # Usuario eliminado exitosamente
            deleted_user = delete_dialog.user_deleted

            if deleted_user:
                # IMPORTANTE: Recargar usuarios desde archivo (se actualizó en DeleteUserDialog)
                self.user_auth.users = self.user_auth._load_users()

                # Recargar la lista de usuarios
                self.username_combo.clear()
                users = list(self.user_auth.users.keys())

                if users:
                    self.username_combo.addItems(sorted(users))
                    self.username_combo.setCurrentIndex(0)
                else:
                    self.username_combo.addItem("(No hay usuarios)")
                    self.username_combo.setEnabled(False)

                # Limpiar contraseña
                self.password_input.clear()

                # Enfocar la ventana de login (no mostrar más diálogos)

    def open_forgot_password_dialog(self):
        """Abre el diálogo de recuperación de contraseña."""
        from presentation.forms.forgot_password_dialog import ForgotPasswordDialog

        forgot_dialog = ForgotPasswordDialog(self)

        if forgot_dialog.exec() == QDialog.DialogCode.Accepted:
            # Contraseña cambiada exitosamente, recargar usuarios
            self.user_auth.users = self.user_auth._load_users()

            # Limpiar campo de contraseña para que el usuario introduzca la nueva
            self.password_input.clear()
            self.password_input.setFocus()

            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("🔄 Datos actualizados")
            msg.setWindowIcon(get_corporate_icon())
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                "Por favor, introduce tu <span style='color: #007ACC; "
                "font-style: italic;'>nueva contraseña</span> para iniciar sesión."
            )
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()

    def login(self):
        """Intenta autenticar al usuario."""
        username = self.username_combo.currentText().strip()
        password = self.password_input.text()

        if not username or not password:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Campos vacíos")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText("Por favor introduce usuario y contraseña")
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            return

        if self.user_auth.authenticate(username, password):
            from utils.ui_helpers import MESSAGEBOX_STYLE
            self.authenticated_user = username
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("✅ Bienvenido")
            msg.setWindowIcon(get_corporate_icon())
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                f"Sesión iniciada correctamente.<br><br>"
                f"Usuario: <span style='color: #007ACC; font-style: italic;'>{username}</span>"
            )
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.accept()
        else:
            from utils.ui_helpers import MESSAGEBOX_STYLE
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("❌ Error de autenticación")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText(
                "Usuario o contraseña incorrectos.\n\n"
                "Por favor, verifica tus credenciales."
            )
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            self.password_input.clear()
            self.password_input.setFocus()

