"""
Diálogo de configuración inicial.

Valida y configura SMTP y SFTP al iniciar la aplicación por primera vez
o cuando falte configuración crítica.
"""

import base64
import json
import os
import shutil
import smtplib
import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.paths import get_base_directory
from presentation.dialogs._initial_config_tabs import create_sftp_tab, create_smtp_tab
from utils import get_logger
from utils.icons import icon_for_button
from utils.ui_helpers import aplicar_caja

logger = get_logger(__name__)


class InitialConfigDialog(QDialog):
    """
    Diálogo de configuración inicial SMTP/SFTP.

    Valida que ambas configuraciones estén completas antes de permitir
    el uso de la aplicación. SFTP es obligatorio, SMTP es opcional.
    """

    def __init__(self, parent=None):
        """
        Inicializa el diálogo de configuración inicial.

        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        self.setWindowTitle("Configuración Inicial - Guardias de Patio")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(720)

        # Estado interno
        self._smtp_configured = False
        self._sftp_configured = False
        self._smtp_password = ""
        self._sftp_password = ""

        self._setup_ui()
        self._load_existing_config()
        self._check_configuration()

    def _setup_ui(self) -> None:
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout()

        # Título y explicación
        title_label = QLabel("Configuración Inicial del Sistema")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1f2937;
                padding: 10px;
            }
        """)

        description_label = QLabel(
            "Para garantizar el correcto funcionamiento de la aplicación, "
            "es necesario configurar los sistemas de sincronización y comunicación."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6b7280;
                padding: 10px;
                background-color: #f9fafb;
                border-radius: 5px;
            }
        """)

        layout.addWidget(title_label)
        layout.addWidget(description_label)

        # Tabs para SMTP y SFTP
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
        """)

        # Tab SFTP (CRÍTICO)
        self.sftp_tab = self._create_sftp_tab()
        self.tabs.addTab(self.sftp_tab, "SFTP (Obligatorio)")

        # Tab SMTP (OPCIONAL)
        self.smtp_tab = self._create_smtp_tab()
        self.tabs.addTab(self.smtp_tab, "SMTP (Opcional)")

        layout.addWidget(self.tabs)

        # Indicadores de estado
        status_layout = QHBoxLayout()

        self.smtp_status_label = QLabel("SMTP: No configurado")
        aplicar_caja(self.smtp_status_label, "aviso")

        self.sftp_status_label = QLabel("SFTP: No configurado")
        aplicar_caja(self.sftp_status_label, "error")

        status_layout.addWidget(self.smtp_status_label)
        status_layout.addWidget(self.sftp_status_label)

        layout.addLayout(status_layout)

        # Botones
        button_box = QDialogButtonBox()

        self.skip_smtp_btn = QPushButton("Continuar sin SMTP")
        self.skip_smtp_btn.setIcon(icon_for_button("skip"))
        self.skip_smtp_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        self.skip_smtp_btn.clicked.connect(self._skip_smtp)

        self.continue_btn = QPushButton("Continuar")
        self.continue_btn.setIcon(icon_for_button("check"))
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E7E34;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #166529;
            }
            QPushButton:disabled {
                background-color: #d1d5db;
                color: #9ca3af;
            }
        """)
        self.continue_btn.clicked.connect(self.accept)
        self.continue_btn.setEnabled(False)

        button_box.addButton(self.skip_smtp_btn, QDialogButtonBox.ButtonRole.ActionRole)
        button_box.addButton(self.continue_btn, QDialogButtonBox.ButtonRole.AcceptRole)

        layout.addWidget(button_box)

        self.setLayout(layout)

    def _create_sftp_tab(self) -> QWidget:
        """Crea el tab de configuración SFTP."""
        return create_sftp_tab(self)

    def _create_smtp_tab(self) -> QWidget:
        """Crea el tab de configuración SMTP."""
        return create_smtp_tab(self)

    def _load_existing_config(self) -> None:
        """Carga la configuración existente desde .env."""
        self._migrate_legacy_env_if_needed()
        env_path = self._get_env_path()
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            load_dotenv()

        # SFTP
        self.sftp_host_input.setText(os.getenv("SFTP_HOST", ""))
        self.sftp_port_input.setText(os.getenv("SFTP_PORT", "22"))
        self.sftp_user_input.setText(os.getenv("SFTP_USERNAME", ""))
        self._sftp_password = os.getenv("SFTP_PASSWORD", "")
        #: La conexión sólo se da por buena tras hablar con el servidor (SYNC-002).
        #: Cualquier cambio en los datos vuelve a ponerlo en False.
        self._sftp_probado_ok = False
        if self._sftp_password:
            self.sftp_password_input.setText("••••••••")
            self.sftp_password_input.setPlaceholderText("Contraseña configurada")
        self.sftp_basedir_input.setText(os.getenv("SFTP_BASE_DIR", "/aplicaciones/guardias_patio"))

        # Tocar cualquier dato invalida la prueba anterior: si no, se podría probar
        # con unos datos y guardar otros distintos (SYNC-002).
        for campo in (
            self.sftp_host_input,
            self.sftp_port_input,
            self.sftp_user_input,
            self.sftp_password_input,
            self.sftp_basedir_input,
        ):
            campo.textEdited.connect(self._invalidar_prueba_sftp)

        # SMTP
        self.smtp_server_input.setText(os.getenv("SMTP_SERVER", ""))
        self.smtp_port_input.setText(os.getenv("SMTP_PORT", "587"))
        self.smtp_user_input.setText(os.getenv("SMTP_USER", ""))
        self.smtp_from_name_input.setText(os.getenv("SMTP_FROM_NAME", "Guardias de Patio"))
        self._smtp_password = os.getenv("SMTP_PASSWORD", "")
        if self._smtp_password:
            self.smtp_password_input.setText("••••••••")
            self.smtp_password_input.setPlaceholderText("Contraseña configurada")

    def _check_configuration(self) -> None:
        """Verifica si la configuración está completa y actualiza el estado."""
        # SFTP (obligatorio)
        sftp_complete = all(
            [
                self.sftp_host_input.text().strip(),
                self.sftp_port_input.text().strip(),
                self.sftp_user_input.text().strip(),
                self._sftp_password or self.sftp_password_input.text().strip(),
            ]
        )

        if sftp_complete and self._sftp_configured:
            self.sftp_status_label.setText("SFTP: Configurado correctamente")
            aplicar_caja(self.sftp_status_label, "exito")
        elif sftp_complete:
            self.sftp_status_label.setText("SFTP: Datos completos - Guardar y probar")
            aplicar_caja(self.sftp_status_label, "aviso")
        else:
            self.sftp_status_label.setText("SFTP: Configuración incompleta (OBLIGATORIO)")
            aplicar_caja(self.sftp_status_label, "error")

        # SMTP (opcional)
        smtp_complete = all(
            [
                self.smtp_server_input.text().strip(),
                self.smtp_port_input.text().strip(),
                self.smtp_user_input.text().strip(),
                self._smtp_password or self.smtp_password_input.text().strip(),
            ]
        )

        if smtp_complete and self._smtp_configured:
            self.smtp_status_label.setText("SMTP: Configurado correctamente")
            aplicar_caja(self.smtp_status_label, "exito")
        elif smtp_complete:
            self.smtp_status_label.setText("SMTP: Datos completos - Guardar y probar")
            aplicar_caja(self.smtp_status_label, "aviso")
        else:
            self.smtp_status_label.setText("SMTP: No configurado (OPCIONAL)")
            aplicar_caja(self.smtp_status_label, "aviso")

        # Habilitar botón de continuar solo si SFTP está configurado
        self.continue_btn.setEnabled(self._sftp_configured)

        # Mostrar/ocultar botón de saltar SMTP
        self.skip_smtp_btn.setVisible(not self._sftp_configured or not self._smtp_configured)

    def _on_sftp_changed(self) -> None:
        """Handler cuando cambia algún campo SFTP."""
        self._sftp_configured = False
        self._check_configuration()

    def _on_smtp_changed(self) -> None:
        """Handler cuando cambia algún campo SMTP."""
        self._smtp_configured = False
        self._check_configuration()

    def _invalidar_prueba_sftp(self, *_args) -> None:
        """Los datos han cambiado: hay que volver a probar antes de guardar."""
        self._sftp_probado_ok = False

    def _probar_conexion_sftp(self):
        """Intenta conectar de verdad al servidor. Devuelve `(ok, mensaje)`.

        Sin interfaz, para poder usarla tanto desde el botón «Probar» como antes
        de guardar: dar por buena una configuración porque los campos no están
        vacíos deja al usuario creyendo que sincroniza cuando no lo hace (SYNC-002).
        """
        host = self.sftp_host_input.text().strip()
        port = self.sftp_port_input.text().strip()
        user = self.sftp_user_input.text().strip()
        password = self.sftp_password_input.text().strip()

        # Si la contraseña son asteriscos, usar la almacenada
        if password == "••••••••":
            password = self._sftp_password

        if not all([host, port, user, password]):
            return False, "Faltan datos: completa servidor, puerto, usuario y contraseña."

        transport = None
        try:
            transport = paramiko.Transport((host, int(port)))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            # El directorio base tiene que existir o poder crearse
            basedir = self.sftp_basedir_input.text().strip()
            if basedir:
                try:
                    sftp.stat(basedir)
                except FileNotFoundError:
                    sftp.mkdir(basedir)

            sftp.close()
            return True, f"Conectado a {host} y carpeta de destino accesible."

        except paramiko.AuthenticationException:
            return False, "El servidor rechazó el usuario o la contraseña."
        except Exception as e:  # noqa: BLE001 - paramiko no hereda de OSError
            # `except (OSError, ValueError)` dejaba escapar SSHException, así que
            # una contraseña mal escrita reventaba el diálogo en vez de avisar.
            return False, f"{type(e).__name__}: {e}"
        finally:
            if transport is not None:
                try:
                    transport.close()
                except Exception:  # noqa: BLE001
                    pass

    def _test_sftp(self) -> None:
        """Prueba la conexión SFTP y deja constancia del resultado."""
        ok, mensaje = self._probar_conexion_sftp()
        self._sftp_probado_ok = ok

        if ok:
            QMessageBox.information(
                self,
                "✅ Conexión Exitosa",
                f"{mensaje}\n\nAhora puedes guardar la configuración.",
            )
        else:
            QMessageBox.critical(
                self,
                "❌ Error de Conexión",
                f"No se pudo conectar al servidor SFTP:\n\n{mensaje}\n\n"
                "Verifica los datos e inténtalo de nuevo.",
            )
            logger.error(f"Error al probar SFTP: {mensaje}")

    def _test_smtp(self) -> None:
        """Prueba la conexión SMTP."""
        server = self.smtp_server_input.text().strip()
        port = self.smtp_port_input.text().strip()
        user = self.smtp_user_input.text().strip()
        password = self.smtp_password_input.text().strip()

        # Si la contraseña son asteriscos, usar la almacenada
        if password == "••••••••":
            password = self._smtp_password

        if not all([server, port, user, password]):
            QMessageBox.warning(
                self,
                "Campos Incompletos",
                "Por favor, completa todos los campos SMTP antes de probar la conexión.",
            )
            return

        try:
            # Intentar conectar
            with smtplib.SMTP(server, int(port), timeout=10) as smtp:
                smtp.starttls()
                smtp.login(user, password)

            QMessageBox.information(
                self,
                "✅ Conexión Exitosa",
                f"La conexión SMTP a {server} se estableció correctamente.\n\n"
                "Ahora puedes guardar la configuración.",
            )

        except smtplib.SMTPAuthenticationError:
            QMessageBox.critical(
                self,
                "❌ Error de Autenticación",
                "Usuario o contraseña incorrectos.\n\n"
                "Para Gmail, necesitas usar una App Password, no tu contraseña normal.",
            )

        except (ValueError, TypeError) as e:
            QMessageBox.critical(
                self,
                "❌ Error de Conexión",
                f"No se pudo conectar al servidor SMTP:\n\n{str(e)}\n\n"
                "Verifica los datos e inténtalo de nuevo.",
            )
            logger.error(f"Error al probar SMTP: {e}")

    def _save_sftp(self) -> None:
        """Guarda la configuración SFTP en .env."""
        host = self.sftp_host_input.text().strip()
        port = self.sftp_port_input.text().strip()
        user = self.sftp_user_input.text().strip()
        password = self.sftp_password_input.text().strip()
        basedir = self.sftp_basedir_input.text().strip()

        # Si la contraseña son asteriscos, usar la almacenada
        if password == "••••••••":
            password = self._sftp_password
        else:
            self._sftp_password = password

        if not all([host, port, user, password]):
            QMessageBox.warning(
                self,
                "Campos Incompletos",
                "Por favor, completa todos los campos SFTP antes de guardar.",
            )
            return

        # No se guarda una configuración que no funciona: se comprueba contra el
        # servidor antes (SYNC-002). Si ya se probó con estos mismos datos, no se
        # repite la conexión.
        if not self._sftp_probado_ok:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                ok, mensaje = self._probar_conexion_sftp()
            finally:
                QApplication.restoreOverrideCursor()

            if not ok:
                QMessageBox.critical(
                    self,
                    "❌ No se guardó la configuración",
                    f"No se pudo conectar al servidor SFTP:\n\n{mensaje}\n\n"
                    "La configuración no se guarda: si lo hiciera, la aplicación "
                    "parecería estar sincronizando cuando no lo estaría.",
                )
                logger.error(f"Configuración SFTP rechazada, no conecta: {mensaje}")
                return
            self._sftp_probado_ok = True

        try:
            self._update_env_file(
                {
                    "SFTP_HOST": host,
                    "SFTP_PORT": port,
                    "SFTP_USERNAME": user,
                    "SFTP_PASSWORD": password,
                    "SFTP_BASE_DIR": basedir or "/aplicaciones/guardias_patio",
                }
            )

            self._sftp_configured = True
            self._check_configuration()

            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "La configuración SFTP se ha guardado correctamente.\n\n"
                "Ahora puedes continuar usando la aplicación.",
            )

        except (OSError, ValueError) as e:
            QMessageBox.critical(
                self,
                "❌ Error al Guardar",
                f"No se pudo guardar la configuración SFTP:\n\n{str(e)}",
            )
            logger.error(f"Error al guardar SFTP: {e}")

    def _save_smtp(self) -> None:
        """Guarda la configuración SMTP en .env."""
        server = self.smtp_server_input.text().strip()
        port = self.smtp_port_input.text().strip()
        user = self.smtp_user_input.text().strip()
        password = self.smtp_password_input.text().strip()
        from_name = self.smtp_from_name_input.text().strip()

        # Si la contraseña son asteriscos, usar la almacenada
        if password == "••••••••":
            password = self._smtp_password
        else:
            self._smtp_password = password

        if not all([server, port, user, password]):
            QMessageBox.warning(
                self,
                "Campos Incompletos",
                "Por favor, completa todos los campos SMTP antes de guardar.",
            )
            return

        # Usar valor por defecto si no se especifica nombre
        if not from_name:
            from_name = "Guardias de Patio"

        try:
            self._update_env_file(
                {
                    "SMTP_SERVER": server,
                    "SMTP_PORT": port,
                    "SMTP_USER": user,
                    "SMTP_PASSWORD": password,
                    "SMTP_FROM_NAME": from_name,
                }
            )

            self._smtp_configured = True
            self._check_configuration()

            QMessageBox.information(
                self,
                "✅ Configuración Guardada",
                "La configuración SMTP se ha guardado correctamente.\n\n"
                "Ya puedes enviar emails desde la aplicación.",
            )

        except (ValueError, TypeError) as e:
            QMessageBox.critical(
                self,
                "❌ Error al Guardar",
                f"No se pudo guardar la configuración SMTP:\n\n{str(e)}",
            )
            logger.error(f"Error al guardar SMTP: {e}")

    def _skip_smtp(self) -> None:
        """Permite continuar sin configurar SMTP si SFTP está configurado."""
        if not self._sftp_configured:
            QMessageBox.warning(
                self,
                "⚠️ SFTP Obligatorio",
                "No puedes continuar sin configurar SFTP.\n\n"
                "El servidor SFTP es necesario para garantizar copias de seguridad "
                "y sincronización de datos.",
            )
            return

        reply = QMessageBox.question(
            self,
            "⏭️ Continuar sin SMTP",
            "¿Estás seguro de que quieres continuar sin configurar SMTP?\n\n"
            "Sin SMTP no podrás:\n"
            "• Enviar calendarios por email a profesores\n"
            "• Recuperar contraseñas por email\n"
            "• Recibir notificaciones automáticas\n\n"
            "Podrás configurarlo más tarde desde el menú de configuración.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def _update_env_file(self, variables: dict) -> None:
        """Guarda la configuración: contraseñas al llavero, el resto al `.env`."""
        from core.credenciales import guardar_configuracion

        guardar_configuracion(variables)

    @staticmethod
    def _get_env_path() -> Path:
        return get_base_directory() / ".env"

    @staticmethod
    def _get_legacy_bundle_env_path() -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent / ".env"

    @classmethod
    def _migrate_legacy_env_if_needed(cls) -> None:
        if not getattr(sys, "frozen", False):
            return

        destino = cls._get_env_path()
        origen_legacy = cls._get_legacy_bundle_env_path()

        if destino.exists() or not origen_legacy.exists():
            return

        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen_legacy, destino)
        logger.info(f"Migrado .env legacy a ruta persistente: {destino}")

    @staticmethod
    def is_configuration_needed() -> bool:
        """
        Verifica si es necesario mostrar el diálogo de configuración.

        Returns:
            True si falta configuración SFTP (obligatoria)
        """
        InitialConfigDialog._migrate_legacy_env_if_needed()
        env_path = InitialConfigDialog._get_env_path()
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            load_dotenv()

        # SFTP es obligatorio
        sftp_complete = all(
            [
                os.getenv("SFTP_HOST"),
                os.getenv("SFTP_PORT"),
                os.getenv("SFTP_USERNAME"),
                os.getenv("SFTP_PASSWORD"),
            ]
        )

        return not sftp_complete

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Desencripta un valor codificado en base64."""
        try:
            return base64.b64decode(encrypted_value.encode("utf-8")).decode("utf-8")
        except (OSError, ValueError):
            return encrypted_value  # Si falla, asumir que ya está desencriptado

    def _load_sftp_from_json(self) -> None:
        """Carga la configuración SFTP desde un archivo JSON encriptado."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de configuración SFTP",
            "",
            "Archivos JSON (*.json);;Todos los archivos (*)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Desencriptar y rellenar campos
            if "host" in data:
                self.sftp_host_input.setText(self._decrypt_value(data["host"]))
            if "port" in data:
                self.sftp_port_input.setText(self._decrypt_value(str(data["port"])))
            if "username" in data:
                self.sftp_user_input.setText(self._decrypt_value(data["username"]))
            if "password" in data:
                password = self._decrypt_value(data["password"])
                self.sftp_password_input.setText(password)
                self._sftp_password = password
            if "base_dir" in data:
                self.sftp_basedir_input.setText(self._decrypt_value(data["base_dir"]))

            QMessageBox.information(
                self,
                "✅ Configuración Cargada",
                "Los datos de SFTP se han cargado correctamente.\n\n"
                "Ahora puedes probar la conexión y guardar la configuración.",
            )

            self._check_configuration()

        except json.JSONDecodeError:
            QMessageBox.critical(
                self,
                "❌ Error",
                "El archivo no es un JSON válido.",
            )
        except (OSError, ValueError) as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"No se pudo cargar el archivo:\n{str(e)}",
            )
            logger.error(f"Error cargando JSON SFTP: {e}")

    def _load_smtp_from_json(self) -> None:
        """Carga la configuración SMTP desde un archivo JSON encriptado."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de configuración SMTP",
            "",
            "Archivos JSON (*.json);;Todos los archivos (*)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Desencriptar y rellenar campos
            if "server" in data:
                self.smtp_server_input.setText(self._decrypt_value(data["server"]))
            if "port" in data:
                self.smtp_port_input.setText(self._decrypt_value(str(data["port"])))
            if "email" in data:
                self.smtp_user_input.setText(self._decrypt_value(data["email"]))
            if "password" in data:
                password = self._decrypt_value(data["password"])
                self.smtp_password_input.setText(password)
                self._smtp_password = password
            if "from_name" in data:
                self.smtp_from_name_input.setText(self._decrypt_value(data["from_name"]))

            QMessageBox.information(
                self,
                "✅ Configuración Cargada",
                "Los datos de SMTP se han cargado correctamente.\n\n"
                "Ahora puedes probar la conexión y guardar la configuración.",
            )

            self._check_configuration()

        except json.JSONDecodeError:
            QMessageBox.critical(
                self,
                "❌ Error",
                "El archivo no es un JSON válido.",
            )
        except (ValueError, TypeError) as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"No se pudo cargar el archivo:\n{str(e)}",
            )
            logger.error(f"Error cargando JSON SMTP: {e}")
