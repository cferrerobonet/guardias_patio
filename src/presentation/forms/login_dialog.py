"""
Diálogo de Login para Sistema Multi-Usuario
"""

from config.settings import get_settings
from core.paths import get_resources_directory
from core.observability import business_metrics
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QRegularExpressionValidator
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
from utils.icons import icon_for_button
from utils.ui_helpers import get_corporate_icon


class RegisterDialog(QDialog):
    """Diálogo de registro de nuevo usuario con confirmación de contraseña."""

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        # Con servidor, el nombre se reserva allí: no se puede registrar uno que
        # ya exista, porque sus datos son de otra persona.
        self.backend = backend
        self.user_auth = UserAuth(backend=backend)
        self.registered_username = None
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo de registro."""
        self.setWindowTitle("Registrar Nuevo Usuario")
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
        # UX-01: validar en tiempo real — sólo caracteres permitidos en username
        username_validator = QRegularExpressionValidator(
            __import__('PyQt6.QtCore', fromlist=['QRegularExpression']).QRegularExpression(
                r"[a-zA-Z0-9._\-@]+"
            )
        )
        self.username_input.setValidator(username_validator)
        self.username_input.setAccessibleName("Campo nombre de usuario")
        form_layout.addRow("👤 Usuario:", self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ej: carlos@ejemplo.com (OBLIGATORIO)")
        self.email_input.setMinimumHeight(35)
        self.email_input.setAccessibleName("Campo email")
        form_layout.addRow("📧 Email *:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mín. 8 chars, mayúscula, número, símbolo")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.setAccessibleName("Campo contraseña")
        form_layout.addRow("🔑 Contraseña:", self.password_input)

        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Repite la contraseña")
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setMinimumHeight(35)
        self.password_confirm_input.setAccessibleName("Campo confirmar contraseña")
        self.password_confirm_input.returnPressed.connect(self.register)
        form_layout.addRow("🔑 Confirmar:", self.password_confirm_input)

        layout.addLayout(form_layout)

        # Requisitos de contraseña
        requirements = QLabel(
            "✓ Mínimo 8 caracteres\n"
            "✓ Al menos una mayúscula, un número y un símbolo\n"
            "✓ Las contraseñas deben coincidir\n"
            "✓ Email obligatorio para recuperación"
        )
        requirements.setStyleSheet("color: #6B7280; font-size: 11px; padding: 0px 40px;")
        layout.addWidget(requirements)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(40, 20, 40, 20)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setIcon(icon_for_button("close"))
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setProperty("secondary", "true")
        buttons_layout.addWidget(cancel_btn)

        register_btn = QPushButton("Registrarse")
        register_btn.setMinimumHeight(40)
        register_btn.clicked.connect(self.register)
        register_btn.setDefault(True)
        register_btn.setProperty("success", "true")
        buttons_layout.addWidget(register_btn)

        layout.addLayout(buttons_layout)

        # UX-03: TabOrder explícito para navegación por teclado
        self.setTabOrder(self.username_input, self.email_input)
        self.setTabOrder(self.email_input, self.password_input)
        self.setTabOrder(self.password_input, self.password_confirm_input)
        self.setTabOrder(self.password_confirm_input, register_btn)
        self.setTabOrder(register_btn, cancel_btn)

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
            msg.exec()
            self.password_input.setFocus()
            return

        if len(password) < 4:
            from utils.ui_helpers import MESSAGEBOX_STYLE

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Campo vacío")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText("Por favor introduce una contraseña")
            msg.exec()
            self.password_input.setFocus()
            return

        # Validar política completa de contraseñas
        policy_ok, policy_msg = self.user_auth.validate_password_policy(password)
        if not policy_ok:
            from utils.ui_helpers import MESSAGEBOX_STYLE

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Contraseña débil")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText(policy_msg)
            msg.exec()
            self.password_input.setFocus()
            return

        if password != password_confirm:
            from utils.ui_helpers import MESSAGEBOX_STYLE

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Contraseñas no coinciden")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText(
                "Las contraseñas introducidas no son iguales.\n"
                "Por favor, verifica que sean idénticas."
            )
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
            msg.setWindowTitle("Registro exitoso")
            msg.setWindowIcon(get_corporate_icon())
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                f"Usuario <span style='color: #007ACC; font-style: italic;'>{username}</span> "
                f"registrado correctamente.<br><br>"
                f"Ahora puedes iniciar sesión con tus credenciales."
            )
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
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                f"El usuario <span style='color: #007ACC; font-style: italic;'>{username}</span> "
                f"ya está registrado.<br>"
                f"Por favor, elige otro nombre de usuario."
            )
            msg.exec()
            self.username_input.selectAll()
            self.username_input.setFocus()


class LoginDialog(QDialog):
    """Diálogo de autenticación de usuario con selector de usuarios y logo."""

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        # Si hay servidor, la cuenta se comprueba contra él, así que la misma
        # cuenta funciona desde cualquier equipo.
        self.backend = backend
        self.user_auth = UserAuth(backend=backend)
        self.authenticated_user = None
        self.setup_ui()
        self.load_existing_users()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Iniciar Sesión - Guardias de Patio")
        self.setWindowIcon(get_icon("login", "#007ACC", 32))
        self.setModal(True)
        self.setFixedSize(720, 480)

        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Panel izquierdo: marca ──────────────────────────────────────────
        brand_panel = QLabel()
        brand_panel.setFixedWidth(280)
        brand_panel.setStyleSheet(
            "QLabel { background-color: #007ACC; }"
        )
        brand_layout = QVBoxLayout(brand_panel)
        brand_layout.setContentsMargins(24, 40, 24, 32)
        brand_layout.setSpacing(0)

        logo_path = get_resources_directory() / "logo.png"
        logo_label = QLabel()
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled = pixmap.scaled(
                120, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_label.setPixmap(scaled)
        else:
            logo_label.setText("🏫")
            logo_label.setStyleSheet("font-size: 52px; background: transparent;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        brand_layout.addWidget(logo_label)

        brand_layout.addSpacing(20)

        app_title = QLabel("Guardias\nde Patio")
        app_title.setStyleSheet(
            "QLabel { font-size: 26px; font-weight: 700; color: white;"
            " background: transparent; line-height: 1.2; }"
        )
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(app_title)

        brand_layout.addSpacing(10)

        app_sub = QLabel("Gestión y asignación\nde guardias escolares")
        app_sub.setStyleSheet(
            "QLabel { font-size: 12px; color: rgba(255,255,255,0.75);"
            " background: transparent; }"
        )
        app_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_sub.setWordWrap(True)
        brand_layout.addWidget(app_sub)

        brand_layout.addStretch()

        version_label = QLabel(f"v{get_settings().app_version}")
        version_label.setStyleSheet(
            "QLabel { font-size: 11px; color: rgba(255,255,255,0.55);"
            " background: transparent; }"
        )
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(version_label)

        credits = QLabel("© 2026 · Carlos Ferrero Bonet")
        credits.setStyleSheet(
            "QLabel { font-size: 10px; color: rgba(255,255,255,0.55);"
            " background: transparent; }"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(credits)

        root_layout.addWidget(brand_panel)

        # ── Panel derecho: formulario ───────────────────────────────────────
        form_panel = QLabel()
        form_panel.setStyleSheet("QLabel { background-color: #FFFFFF; }")
        form_layout_outer = QVBoxLayout(form_panel)
        form_layout_outer.setContentsMargins(40, 40, 40, 32)
        form_layout_outer.setSpacing(0)

        welcome = QLabel("Bienvenido")
        welcome.setStyleSheet(
            "QLabel { font-size: 22px; font-weight: 700; color: #111827;"
            " background: transparent; }"
        )
        form_layout_outer.addWidget(welcome)

        hint = QLabel("Inicia sesión para continuar")
        hint.setStyleSheet(
            "QLabel { font-size: 12px; color: #6B7280; background: transparent; }"
        )
        form_layout_outer.addWidget(hint)
        form_layout_outer.addSpacing(28)

        form_layout = QFormLayout()
        form_layout.setSpacing(14)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.username_combo = QComboBox()
        self.username_combo.setEditable(True)
        self.username_combo.setPlaceholderText("Selecciona o escribe tu usuario")
        self.username_combo.setMinimumHeight(36)
        self.username_combo.setAccessibleName("Campo selector de usuario")
        self.username_combo.currentTextChanged.connect(self.on_user_selected)
        user_label = QLabel("Usuario")
        user_label.setStyleSheet("QLabel { font-size: 12px; font-weight: 600; color: #374151; background: transparent; }")
        form_layout.addRow(user_label, self.username_combo)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Introduce tu contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(36)
        self.password_input.setAccessibleName("Campo contraseña de acceso")
        self.password_input.returnPressed.connect(self.login)
        pwd_label = QLabel("Contraseña")
        pwd_label.setStyleSheet("QLabel { font-size: 12px; font-weight: 600; color: #374151; background: transparent; }")
        form_layout.addRow(pwd_label, self.password_input)

        form_layout_outer.addLayout(form_layout)
        form_layout_outer.addSpacing(8)

        forgot_password_label = QLabel(
            '<a href="#" style="color: #007ACC; text-decoration: none;">¿Olvidaste tu contraseña?</a>'
        )
        forgot_password_label.setStyleSheet("font-size: 11px; background: transparent;")
        forgot_password_label.setTextFormat(Qt.TextFormat.RichText)
        forgot_password_label.linkActivated.connect(self.open_forgot_password_dialog)
        forgot_password_label.setCursor(Qt.CursorShape.PointingHandCursor)
        form_layout_outer.addWidget(forgot_password_label)

        form_layout_outer.addSpacing(20)

        self.login_btn = QPushButton(" Iniciar Sesión")
        self.login_btn.setIcon(get_icon("login", "white", 18))
        self.login_btn.setMinimumHeight(42)
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setDefault(True)
        self.login_btn.setStyleSheet(
            "QPushButton { background-color: #007ACC; color: white; border: none;"
            " border-radius: 6px; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background-color: #005A9E; }"
        )
        form_layout_outer.addWidget(self.login_btn)

        form_layout_outer.addSpacing(12)

        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(8)

        self.register_btn = QPushButton(" Nuevo Usuario")
        self.register_btn.setIcon(get_icon("account-plus", "white", 18))
        self.register_btn.setMinimumHeight(36)
        self.register_btn.clicked.connect(self.open_register_dialog)
        self.register_btn.setProperty("success", "true")
        secondary_layout.addWidget(self.register_btn)

        self.delete_user_btn = QPushButton(" Eliminar")
        self.delete_user_btn.setIcon(get_icon("close", "white", 18))
        self.delete_user_btn.setMinimumHeight(36)
        self.delete_user_btn.clicked.connect(self.open_delete_user_dialog)
        self.delete_user_btn.setProperty("danger", "true")
        secondary_layout.addWidget(self.delete_user_btn)

        form_layout_outer.addLayout(secondary_layout)
        form_layout_outer.addStretch()

        info_label = QLabel("¿Primera vez? Haz clic en Nuevo Usuario")
        info_label.setStyleSheet("QLabel { color: #9CA3AF; font-size: 11px; background: transparent; }")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout_outer.addWidget(info_label)

        root_layout.addWidget(form_panel)

        # TabOrder
        self.setTabOrder(self.username_combo, self.password_input)
        self.setTabOrder(self.password_input, self.login_btn)
        self.setTabOrder(self.login_btn, self.register_btn)
        self.setTabOrder(self.register_btn, self.delete_user_btn)

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
        register_dialog = RegisterDialog(self, backend=self.backend)

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
            msg.setWindowTitle("Datos actualizados")
            msg.setWindowIcon(get_corporate_icon())
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                "Por favor, introduce tu <span style='color: #007ACC; "
                "font-style: italic;'>nueva contraseña</span> para iniciar sesión."
            )
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
            msg.exec()
            return

        auth_ok, auth_msg = self.user_auth.authenticate(username, password)
        if auth_ok:
            self.authenticated_user = username
            business_metrics.login_exitoso(username=username)
            self.accept()
        else:
            from utils.ui_helpers import MESSAGEBOX_STYLE

            business_metrics.login_fallido(username=username, razon=auth_msg)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Error de autenticación")
            msg.setWindowIcon(get_corporate_icon())
            msg.setText(auth_msg)
            msg.exec()
            self.password_input.clear()
            self.password_input.setFocus()
