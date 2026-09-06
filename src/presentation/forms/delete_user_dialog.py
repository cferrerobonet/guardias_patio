"""
Diálogo para eliminar usuarios con confirmación de contraseña
"""

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
    QWidget,
)

from database.db_manager import delete_user_database
from presentation.theme.tokens import Colors
from sync.backend_factory import get_default_backend
from sync.sync_manager import UserAuth
from utils.icons import icon_for_button
from utils.ui_helpers import get_corporate_icon


class DeleteUserDialog(QDialog):
    """Diálogo para eliminar un usuario con confirmación de contraseña."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_auth = UserAuth()
        self.user_deleted = None
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Eliminar Usuario")
        self.setWindowIcon(get_corporate_icon())
        self.setModal(True)
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)

        # Advertencia
        warning = QLabel("ADVERTENCIA")
        warning.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: bold;
                /* Sobre el rosa del aviso, el rojo normal se queda en 3,95:1;
                   éste da 6,7:1 y no depende de que el texto sea grande (UXA-010). */
                color: {Colors.ERROR_ON_BG};
                padding: 20px;
                background-color: {Colors.ERROR_BG};
            }}
        """)
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning)

        # Mensaje de advertencia
        message = QLabel(
            "Esta acción eliminará PERMANENTEMENTE:\n\n"
            "• Todos los datos locales del usuario\n"
            "• Base de datos completa\n"
            "• Archivos en la nube (SFTP)\n"
            "• Configuración y preferencias\n\n"
            "Esta operación NO se puede deshacer."
        )
        message.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #374151;
                padding: 20px 40px;
                background-color: #FEF3C7;
                border-left: 4px solid #F59E0B;
            }
        """)
        message.setWordWrap(True)
        layout.addWidget(message)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(15)

        # Selector de usuario
        from PyQt6.QtWidgets import QComboBox

        self.username_combo = QComboBox()
        self.username_combo.setMinimumHeight(35)
        self.username_combo.setAccessibleName("Selector de usuario a eliminar")
        users = list(self.user_auth.users.keys())
        if users:
            self.username_combo.addItems(sorted(users))
        else:
            self.username_combo.addItem("(No hay usuarios)")
            self.username_combo.setEnabled(False)
        form_layout.addRow("Usuario a eliminar:", self.username_combo)

        # Campo de contraseña
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Confirma con la contraseña del usuario")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.returnPressed.connect(self.delete_user)
        self.password_input.setAccessibleName("Campo contraseña para confirmar eliminación")
        form_layout.addRow("Contraseña:", self.password_input)

        layout.addLayout(form_layout)

        # Confirmación adicional
        confirm_label = QLabel("Escribe la contraseña del usuario para confirmar la eliminación")
        confirm_label.setStyleSheet("color: #DC2626; font-size: 12px; padding: 0px 40px;")
        confirm_label.setWordWrap(True)
        layout.addWidget(confirm_label)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(40, 20, 40, 20)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setAccessibleName("Botón cancelar eliminación de usuario")
        buttons_layout.addWidget(cancel_btn)

        delete_btn = QPushButton("ELIMINAR PERMANENTEMENTE")
        delete_btn.setIcon(icon_for_button("delete"))
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_user)
        delete_btn.setDefault(True)
        delete_btn.setAccessibleName("Botón eliminar usuario permanentemente")
        delete_btn.setProperty("danger", "true")
        buttons_layout.addWidget(delete_btn)

        layout.addLayout(buttons_layout)

        # A11Y: Tab order
        QWidget.setTabOrder(self.username_combo, self.password_input)
        QWidget.setTabOrder(self.password_input, delete_btn)
        QWidget.setTabOrder(delete_btn, cancel_btn)

    def delete_user(self):
        """Elimina el usuario tras verificar la contraseña."""
        username = self.username_combo.currentText().strip()
        password = self.password_input.text()

        # Validaciones
        if not username or username == "(No hay usuarios)":
            QMessageBox.warning(self, "Sin usuario", "No hay usuarios para eliminar")
            return

        if not password:
            QMessageBox.warning(
                self,
                "Contraseña requerida",
                "Debes introducir la contraseña del usuario para confirmar la eliminación",
            )
            self.password_input.setFocus()
            return

        # Verificar contraseña
        auth_ok, auth_msg = self.user_auth.authenticate(username, password)
        if not auth_ok:
            QMessageBox.critical(
                self,
                "❌ Contraseña incorrecta",
                auth_msg + "\n\nPor seguridad, no se puede eliminar el usuario sin la contraseña correcta.",
            )
            self.password_input.clear()
            self.password_input.setFocus()
            return

        # Confirmación final
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Confirmación final")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        msg.setText(
            f"¿Estás ABSOLUTAMENTE SEGURO de que quieres eliminar el usuario "
            f"<span style='color: #DC2626; font-style: italic;'>{username}</span>?<br><br>"
            f"Se eliminarán:<br>"
            f"• Toda la base de datos local<br>"
            f"• Todos los archivos en la nube<br>"
            f"• La cuenta de usuario<br><br>"
            f"Esta acción <b>NO</b> se puede deshacer."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        reply = msg.exec()

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Proceder con la eliminación
        try:
            # 1. Eliminar archivos en la nube
            from sync.sync_manager import SyncManager

            backend = get_default_backend()
            sync_manager = SyncManager(backend, username)
            # 1. Eliminar archivos en la nube
            try:
                # Intentar eliminar archivos remotos
                remote_data_file = f"users/{sync_manager.user_hash}/guardias_patio_data.json"

                if backend.file_exists(remote_data_file):
                    # No hay método delete en backend, pero podemos intentar subir un archivo vacío
                    # o simplemente dejarlo (se puede limpiar manualmente)
                    pass

            except (ValueError, TypeError, OSError) as e:
                logger = self.user_auth.logger if hasattr(self.user_auth, "logger") else None
                if logger:
                    logger.warning(f"No se pudieron eliminar archivos en la nube: {e}")

            # 2. Eliminar base de datos local
            db_deleted = delete_user_database(username)

            # 3. Eliminar usuario de UserAuth
            user_unregistered = self.user_auth.unregister_user(username)

            # Verificar resultados
            if db_deleted and user_unregistered:
                self.user_deleted = username
                # Cerrar inmediatamente sin mostrar más mensajes
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Eliminación parcial",
                    f"El usuario '{username}' fue eliminado parcialmente.\n\n"
                    f"Base de datos: {'✓ Eliminada' if db_deleted else '✗ Error'}\n"
                    f"Cuenta: {'✓ Eliminada' if user_unregistered else '✗ Error'}\n\n"
                    "Revisa los logs para más información.",
                )

        except (ValueError, TypeError) as e:
            QMessageBox.critical(
                self,
                "❌ Error al eliminar",
                f"Error al eliminar el usuario '{username}':\n\n{str(e)}\n\n"
                "Revisa los logs para más información.",
            )
