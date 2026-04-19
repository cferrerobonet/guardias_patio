"""
Widget para configuración SMTP.

Este widget encapsula toda la lógica de configuración del servidor SMTP,
incluyendo validación, conexión de prueba y guardado en .env.

Author: Sistema de Guardias de Patio
Version: 3.0
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import ui_styles as styles
from dotenv import load_dotenv
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)
from utils import get_logger
from utils.icons import icon_for_button


class SMTPConfigWidget(QGroupBox):
    """
    Widget de configuración SMTP.

    Este widget gestiona la configuración del servidor SMTP para el envío
    de emails de recuperación de contraseña y notificaciones del sistema.

    Signals:
        config_changed: Emitido cuando se modifica la configuración
        test_requested: Emitido cuando se solicita prueba de conexión
    """

    # Señales
    config_changed = pyqtSignal()
    test_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa el widget de configuración SMTP.

        Args:
            parent: Widget padre (opcional)
        """
        super().__init__("📧 Configuración SMTP", parent)
        self.logger = get_logger(self.__class__.__name__)
        self.setStyleSheet(styles.STYLE_GROUPBOX)

        # Almacenar contraseña real internamente
        self._actual_password = ""

        self._setup_ui()
        self.load_config()

    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario del widget."""
        layout = QVBoxLayout()

        # Servidor SMTP (campo completo con label arriba)
        label_server = QLabel("Servidor SMTP:")
        label_server.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_server)

        # Fila con input de servidor y puerto
        server_row = QHBoxLayout()
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.ionos.es")
        self.smtp_server_input.setStyleSheet(styles.STYLE_INPUT)
        self.smtp_server_input.setReadOnly(True)
        self.smtp_server_input.textChanged.connect(self.config_changed.emit)
        server_row.addWidget(self.smtp_server_input)

        # Puerto (campo corto en la misma fila)
        label_port = QLabel("Puerto:")
        label_port.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.smtp_port_input = QLineEdit()
        self.smtp_port_input.setPlaceholderText("587")
        self.smtp_port_input.setStyleSheet(styles.STYLE_INPUT)
        self.smtp_port_input.setMaximumWidth(80)
        self.smtp_port_input.setReadOnly(True)
        self.smtp_port_input.textChanged.connect(self.config_changed.emit)
        server_row.addWidget(label_port)
        server_row.addWidget(self.smtp_port_input)

        layout.addLayout(server_row)

        # Usuario (campo completo con label arriba)
        label_user = QLabel("Usuario:")
        label_user.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_user)

        # Fila con usuario y contraseña
        user_row = QHBoxLayout()
        self.smtp_user_input = QLineEdit()
        self.smtp_user_input.setPlaceholderText("no_contestar@aplicaciones.epla.es")
        self.smtp_user_input.setStyleSheet(styles.STYLE_INPUT)
        self.smtp_user_input.setReadOnly(True)
        self.smtp_user_input.textChanged.connect(self.config_changed.emit)
        user_row.addWidget(self.smtp_user_input)

        # Contraseña (en la misma fila)
        label_password = QLabel("Contraseña:")
        label_password.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setPlaceholderText("Contraseña del servidor SMTP")
        self.smtp_password_input.setStyleSheet(styles.STYLE_INPUT)
        self.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_password_input.setReadOnly(True)
        self.smtp_password_input.textChanged.connect(self.config_changed.emit)
        user_row.addWidget(label_password)
        user_row.addWidget(self.smtp_password_input)

        layout.addLayout(user_row)

        # Nombre del Remitente (campo completo con label arriba)
        label_nombre = QLabel("Nombre del Remitente:")
        label_nombre.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_nombre)

        self.smtp_from_name_input = QLineEdit()
        self.smtp_from_name_input.setPlaceholderText("Generador de Guardias de Patio")
        self.smtp_from_name_input.setStyleSheet(styles.STYLE_INPUT)
        self.smtp_from_name_input.textChanged.connect(self.config_changed.emit)
        layout.addWidget(self.smtp_from_name_input)

        # Botones SMTP
        smtp_btn_layout = QHBoxLayout()
        smtp_btn_layout.setSpacing(8)

        self.modify_smtp_btn = QPushButton("Modificar Configuración SMTP")
        self.modify_smtp_btn.setIcon(icon_for_button("key"))
        self.modify_smtp_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.modify_smtp_btn.clicked.connect(self._toggle_editable)
        smtp_btn_layout.addWidget(self.modify_smtp_btn, 1)

        self.test_smtp_btn = QPushButton("Probar Conexión SMTP")
        self.test_smtp_btn.setIcon(icon_for_button("test"))
        self.test_smtp_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.test_smtp_btn.clicked.connect(self._test_connection)
        smtp_btn_layout.addWidget(self.test_smtp_btn, 1)

        layout.addLayout(smtp_btn_layout)

        # Nota informativa
        info_label = QLabel("Para Gmail, usa una App Password en lugar de tu contraseña normal.")
        info_label.setStyleSheet(
            """
            QLabel {
                padding: 10px;
                background-color: #eff6ff;
                border-left: 4px solid #3b82f6;
                color: #1e40af;
                font-size: 12px;
                margin-top: 10px;
            }
        """
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.setLayout(layout)
        self._apply_readonly_style(True)

    def _apply_readonly_style(self, readonly: bool) -> None:
        """
        Aplica el estilo apropiado según el estado readonly.

        Args:
            readonly: True para modo solo lectura, False para editable

        Nota: smtp_from_name_input siempre es editable y no se modifica aquí
        """
        if readonly:
            readonly_style = """
                QLineEdit[readOnly="true"] {
                    background-color: #e5e7eb;
                    color: #4b5563;
                    border: 1px solid #d1d5db;
                    padding: 5px;
                }
            """
            self.smtp_server_input.setStyleSheet(readonly_style)
            self.smtp_port_input.setStyleSheet(readonly_style)
            self.smtp_user_input.setStyleSheet(readonly_style)
            self.smtp_password_input.setStyleSheet(readonly_style)
        else:
            self.smtp_server_input.setStyleSheet(styles.STYLE_INPUT)
            self.smtp_port_input.setStyleSheet(styles.STYLE_INPUT)
            self.smtp_user_input.setStyleSheet(styles.STYLE_INPUT)
            self.smtp_password_input.setStyleSheet(styles.STYLE_INPUT)

    def _toggle_editable(self) -> None:
        """
        Alterna entre bloquear y desbloquear los campos SMTP críticos.

        Nota: smtp_from_name_input siempre permanece editable
        """
        is_readonly = self.smtp_server_input.isReadOnly()

        # Si se va a habilitar la edición, mostrar advertencia
        if is_readonly:
            if not self._show_global_warning():
                return

        # Alternar estado (excepto nombre del remitente que siempre es editable)
        new_state = not is_readonly

        self.smtp_server_input.setReadOnly(new_state)
        self.smtp_port_input.setReadOnly(new_state)
        self.smtp_user_input.setReadOnly(new_state)
        self.smtp_password_input.setReadOnly(new_state)

        # Cambiar estilos y texto del botón
        self._apply_readonly_style(new_state)

        if new_state:  # Bloqueado
            self.modify_smtp_btn.setText("Modificar Configuración SMTP")
        else:  # Editable
            self.modify_smtp_btn.setText("Bloquear Configuración SMTP")

    def _show_global_warning(self) -> bool:
        """
        Muestra advertencia sobre la configuración SMTP global.

        Returns:
            True si el usuario acepta, False si cancela
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Configuración SMTP Global")
        msg.setText("<h3>ADVERTENCIA: Configuración SMTP Global</h3>")
        msg.setInformativeText(
            "<p><b>La configuración SMTP es compartida por TODOS los usuarios del sistema.</b></p>"
            "<p>Modificar estos valores puede:</p>"
            "<ul>"
            "<li>Impedir que otros usuarios recuperen sus contraseñas por email</li>"
            "<li>Afectar a todas las notificaciones del sistema</li>"
            "<li>Causar errores en el envío de emails para todos los usuarios</li>"
            "</ul>"
            "<p><b>Estos cambios afectarán a TODOS los usuarios inmediatamente.</b></p>"
            "<p>¿Estás seguro de que deseas continuar?</p>"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        # Personalizar botones
        yes_button = msg.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Continuar")
        yes_button.setStyleSheet("""
            QPushButton {
                min-width: 100px;
                min-height: 35px;
                padding: 5px 15px;
                font-size: 13px;
                background-color: #059669;
                color: white;
                border: 2px solid #047857;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #047857; }
            QPushButton:pressed { background-color: #065f46; }
        """)

        no_button = msg.button(QMessageBox.StandardButton.No)
        no_button.setText("Cancelar")
        no_button.setStyleSheet("""
            QPushButton {
                min-width: 100px;
                min-height: 35px;
                padding: 5px 15px;
                font-size: 13px;
                background-color: #dc2626;
                color: white;
                border: 2px solid #b91c1c;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #b91c1c; }
            QPushButton:pressed { background-color: #991b1b; }
        """)

        return msg.exec() == QMessageBox.StandardButton.Yes

    def load_config(self) -> None:
        """Carga la configuración SMTP desde el archivo .env."""
        load_dotenv()

        self.smtp_server_input.setText(os.getenv("SMTP_SERVER", ""))
        self.smtp_port_input.setText(os.getenv("SMTP_PORT", "587"))
        self.smtp_user_input.setText(os.getenv("SMTP_USER", ""))
        self.smtp_from_name_input.setText(os.getenv("SMTP_FROM_NAME", "Guardias de Patio"))

        # Almacenar la contraseña real internamente
        self._actual_password = os.getenv("SMTP_PASSWORD", "")

        # Mostrar contraseña enmascarada si existe
        if self._actual_password:
            self.smtp_password_input.setText("••••••••")
            self.smtp_password_input.setPlaceholderText("Contraseña configurada")

    def save_config(self) -> bool:
        """
        Guarda la configuración SMTP en el archivo .env.

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        # Mostrar advertencia antes de guardar
        if not self._show_global_warning():
            self.logger.info("Usuario canceló la modificación de configuración SMTP")
            return False

        try:
            smtp_server = self.smtp_server_input.text().strip()
            smtp_port = self.smtp_port_input.text().strip()
            smtp_user = self.smtp_user_input.text().strip()
            smtp_password = self.smtp_password_input.text().strip()
            smtp_from_name = self.smtp_from_name_input.text().strip()

            # Si la contraseña son asteriscos, usar la almacenada
            if smtp_password == "••••••••":
                password_to_save = self._actual_password
            else:
                password_to_save = smtp_password
                self._actual_password = smtp_password

            # Validar que haya datos completos
            if not smtp_server or not smtp_port or not smtp_user or not password_to_save:
                self.logger.warning("Configuración SMTP incompleta, no se guardó")
                return False

            # Usar valor por defecto si no se especifica nombre
            if not smtp_from_name:
                smtp_from_name = "Guardias de Patio"

            # Leer archivo .env actual
            env_path = ".env"
            env_lines = []

            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_lines = f.readlines()

            # Actualizar o agregar variables SMTP
            smtp_vars = {
                "SMTP_SERVER": smtp_server,
                "SMTP_PORT": smtp_port,
                "SMTP_USER": smtp_user,
                "SMTP_PASSWORD": password_to_save,
                "SMTP_FROM_NAME": smtp_from_name,
            }

            updated_vars = set()
            for i, line in enumerate(env_lines):
                for var_name, var_value in smtp_vars.items():
                    if line.startswith(f"{var_name}="):
                        env_lines[i] = f"{var_name}={var_value}\n"
                        updated_vars.add(var_name)

            # Agregar variables que no existían
            for var_name, var_value in smtp_vars.items():
                if var_name not in updated_vars:
                    env_lines.append(f"{var_name}={var_value}\n")

            # Guardar archivo .env
            with open(env_path, "w") as f:
                f.writelines(env_lines)

            self.logger.info("Configuración SMTP guardada correctamente")

            # Recargar para mostrar la contraseña enmascarada
            self.load_config()

            return True

        except (OSError, ValueError) as e:
            self.logger.error(f"Error al guardar SMTP: {str(e)}")
            return False

    def save_from_name_only(self) -> bool:
        """
        Guarda solo el nombre del remitente SMTP en el archivo .env.

        Este método permite actualizar el nombre del remitente sin modificar
        los otros campos críticos de configuración SMTP.

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            smtp_from_name = self.smtp_from_name_input.text().strip()

            # Usar valor por defecto si no se especifica nombre
            if not smtp_from_name:
                smtp_from_name = "Guardias de Patio"

            # Leer archivo .env actual
            env_path = ".env"
            env_lines = []

            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_lines = f.readlines()

            # Buscar y actualizar SMTP_FROM_NAME
            from_name_found = False
            for i, line in enumerate(env_lines):
                if line.startswith("SMTP_FROM_NAME="):
                    env_lines[i] = f"SMTP_FROM_NAME={smtp_from_name}\n"
                    from_name_found = True
                    break

            # Si no existe, agregarlo
            if not from_name_found:
                env_lines.append(f"SMTP_FROM_NAME={smtp_from_name}\n")

            # Guardar archivo .env
            with open(env_path, "w") as f:
                f.writelines(env_lines)

            self.logger.info(f"Nombre del remitente SMTP guardado: {smtp_from_name}")
            return True

        except (OSError, ValueError) as e:
            self.logger.error(f"Error al guardar nombre del remitente SMTP: {str(e)}")
            return False

    def _test_connection(self, destination_email: Optional[str] = None) -> None:
        """
        Prueba la conexión SMTP enviando un email de prueba.

        Args:
            destination_email: Email de destino. Si es None, solicita al usuario.
        """
        try:
            smtp_server = self.smtp_server_input.text().strip()
            smtp_port = self.smtp_port_input.text().strip()
            smtp_user = self.smtp_user_input.text().strip()
            smtp_password = self.smtp_password_input.text().strip()

            # Validaciones básicas
            if not smtp_server or not smtp_port or not smtp_user:
                self._show_error(
                    "Campos incompletos", "Completa todos los campos antes de probar la conexión"
                )
                return

            # Si la contraseña son asteriscos, usar la almacenada
            if smtp_password == "••••••••":
                smtp_password = self._actual_password

            if not smtp_password:
                self._show_error(
                    "Contraseña vacía", "La contraseña SMTP es necesaria para probar la conexión"
                )
                return

            # Si no se proporciona email de destino, pedir uno
            if not destination_email:
                from PyQt6.QtWidgets import QDialog, QInputDialog

                # Crear diálogo personalizado con estilo
                dialog = QInputDialog(self)
                dialog.setWindowTitle("Email de Prueba")
                dialog.setLabelText("Introduce el email donde recibir la prueba:")
                dialog.setTextValue(smtp_user)
                dialog.setInputMode(QInputDialog.InputMode.TextInput)
                dialog.setTextEchoMode(QLineEdit.EchoMode.Normal)

                # Aplicar estilo al diálogo
                dialog.setStyleSheet("""
                    QInputDialog {
                        background-color: white;
                        min-width: 400px;
                    }
                    QLabel {
                        color: #2c3e50;
                        font-size: 13px;
                        padding: 10px;
                    }
                    QLineEdit {
                        padding: 8px;
                        border: 1px solid #dcdcdc;
                        border-radius: 4px;
                        font-size: 13px;
                        background-color: white;
                        color: #2c3e50;
                        min-width: 350px;
                    }
                    QLineEdit:focus {
                        border: 2px solid #3498db;
                    }
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        padding: 8px 20px;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                    QPushButton:pressed {
                        background-color: #21618c;
                    }
                    QPushButton[text="Cancelar"],
                    QPushButton[text="Cancel"] {
                        background-color: #95a5a6;
                    }
                    QPushButton[text="Cancelar"]:hover,
                    QPushButton[text="Cancel"]:hover {
                        background-color: #7f8c8d;
                    }
                """)

                ok = dialog.exec() == QDialog.DialogCode.Accepted
                destination_email = dialog.textValue()

                if not ok or not destination_email or "@" not in destination_email:
                    return

            # Intentar conectar y enviar email de prueba
            self.logger.info(f"Probando conexión SMTP a {smtp_server}:{smtp_port}")

            with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)

                # Obtener nombre del remitente
                smtp_from_name = self.smtp_from_name_input.text().strip()
                if not smtp_from_name:
                    smtp_from_name = "Guardias de Patio"

                # Crear email de prueba usando la plantilla estándar
                from services.email_service import generar_plantilla_email_html

                msg = MIMEMultipart("alternative")
                msg["Subject"] = "✅ Prueba de Configuración SMTP - Guardias de Patio"

                # Para servidores IONOS y similares, usar solo el email
                if "ionos" in smtp_server.lower() or "1and1" in smtp_server.lower():
                    msg["From"] = smtp_user
                else:
                    msg["From"] = f"{smtp_from_name} <{smtp_user}>"

                msg["To"] = destination_email

                # Contenido texto plano
                texto = f"""
Hola,

Este es un email de prueba para verificar que la configuración SMTP está funcionando correctamente.

Servidor: {smtp_server}:{smtp_port}
Usuario: {smtp_user}

Si estás recibiendo este email, significa que el sistema puede enviar emails sin problemas.

---
Sistema de Gestión de Guardias de Patio
                """

                # Contenido HTML con la plantilla corporativa
                contenido_principal = """
      <p>Hola,</p>
      <p>Este es un email de prueba para verificar que la configuración SMTP
      está funcionando correctamente.</p>
                """

                secciones = [
                    {
                        "tipo": "info",
                        "contenido": f"""
        <p style="margin: 5px 0;"><strong>📡 Detalles de la Conexión:</strong></p>
        <p style="margin: 5px 0;">• Servidor: <strong>{smtp_server}:{smtp_port}</strong></p>
        <p style="margin: 5px 0;">• Usuario: <strong>{smtp_user}</strong></p>
                        """,
                    },
                    {
                        "tipo": "success",
                        "contenido": """
        <p style="margin: 5px 0;"><strong>✅ Configuración Correcta</strong></p>
        <p style="margin: 8px 0;">Si estás recibiendo este email, significa que
        el sistema está correctamente configurado para:</p>
        <p style="margin: 5px 0;">• Enviar códigos de recuperación de contraseña</p>
        <p style="margin: 5px 0;">• Enviar calendarios PDF a profesores</p>
        <p style="margin: 5px 0;">• Notificaciones del sistema</p>
                        """,
                    },
                ]

                html = generar_plantilla_email_html(
                    titulo="✅ Prueba de Configuración SMTP",
                    contenido_principal=contenido_principal,
                    secciones=secciones,
                )

                part1 = MIMEText(texto, "plain", "utf-8")
                part2 = MIMEText(html, "html", "utf-8")
                msg.attach(part1)
                msg.attach(part2)

                # Enviar email
                server.send_message(msg)

            # Éxito
            self._show_success(
                "✅ Email de Prueba Enviado",
                f"La conexión SMTP se estableció correctamente y se envió "
                f"un email de prueba.<br><br>"
                f"<b>Servidor:</b> <span style='color: #007ACC; "
                f"font-style: italic;'>{smtp_server}:{smtp_port}</span><br>"
                f"<b>Usuario:</b> <span style='color: #007ACC; "
                f"font-style: italic;'>{smtp_user}</span><br>"
                f"<b>Email enviado a:</b> <span style='color: #007ACC; "
                f"font-style: italic;'>{destination_email}</span><br><br>"
                "Revisa tu bandeja de entrada (y spam) para verificar que llegó el email.",
            )
            self.logger.info(
                f"Prueba de conexión SMTP exitosa - Email enviado a {destination_email}"
            )

        except smtplib.SMTPAuthenticationError:
            self._show_error(
                "❌ Error de Autenticación",
                "No se pudo autenticar con el servidor SMTP.\n\n"
                "Verifica tu usuario y contraseña.\n"
                "Para Gmail, usa una App Password.",
            )
            self.logger.error("Error de autenticación SMTP")

        except (ValueError, TypeError, OSError) as e:
            self._show_error(
                "❌ Error de Conexión",
                f"No se pudo conectar al servidor SMTP:\n\n{str(e)}\n\n"
                "Verifica el servidor, puerto y credenciales.",
            )
            self.logger.error(f"Error al probar SMTP: {str(e)}")

    def _show_error(self, title: str, message: str) -> None:
        """Muestra un mensaje de error."""
        error_msg = QMessageBox(self)
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setWindowTitle(title)
        error_msg.setText(message)
        error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        ok_button = error_msg.button(QMessageBox.StandardButton.Ok)
        ok_button.setText("Entendido")
        ok_button.setStyleSheet("""
            QPushButton {
                min-width: 120px;
                min-height: 35px;
                padding: 5px 15px;
                font-size: 13px;
                background-color: #dc2626;
                color: white;
                border: 2px solid #b91c1c;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #b91c1c; }
            QPushButton:pressed { background-color: #991b1b; }
        """)
        error_msg.exec()

    def _show_success(self, title: str, message: str) -> None:
        """Muestra un mensaje de éxito."""
        success_msg = QMessageBox(self)
        success_msg.setIcon(QMessageBox.Icon.Information)
        success_msg.setWindowTitle(title)
        success_msg.setTextFormat(Qt.TextFormat.RichText)
        success_msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        success_msg.setText(message)
        success_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        ok_button = success_msg.button(QMessageBox.StandardButton.Ok)
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
            QPushButton:hover { background-color: #047857; }
            QPushButton:pressed { background-color: #065f46; }
        """)
        success_msg.exec()

    def get_config_dict(self) -> dict:
        """
        Obtiene la configuración actual como diccionario.

        Returns:
            Diccionario con la configuración SMTP
        """
        smtp_password = self.smtp_password_input.text().strip()
        if smtp_password == "••••••••":
            smtp_password = self._actual_password

        return {
            "smtp_server": self.smtp_server_input.text().strip(),
            "smtp_port": self.smtp_port_input.text().strip(),
            "smtp_user": self.smtp_user_input.text().strip(),
            "smtp_password": smtp_password,
            "smtp_from_name": self.smtp_from_name_input.text().strip() or "Guardias de Patio",
        }

    def set_config_dict(self, config: dict) -> None:
        """
        Establece la configuración desde un diccionario.

        Args:
            config: Diccionario con smtp_server, smtp_port, smtp_user, smtp_password
        """
        self.smtp_server_input.setText(config.get("smtp_server", ""))
        self.smtp_port_input.setText(config.get("smtp_port", "587"))
        self.smtp_user_input.setText(config.get("smtp_user", ""))

        password = config.get("smtp_password", "")
        if password:
            self._actual_password = password
            self.smtp_password_input.setText("••••••••")
        else:
            self._actual_password = ""
            self.smtp_password_input.setText("")

    def test_connection_with_email(self, email: str) -> None:
        """
        Prueba la conexión enviando email a una dirección específica.

        Args:
            email: Dirección de email de destino
        """
        self._test_connection(destination_email=email)
