"""
Widget para configuración SFTP.

Encapsula toda la lógica de configuración del servidor SFTP para
sincronización de copias de seguridad entre diferentes dispositivos.
"""

import os

import paramiko
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


class SFTPConfigWidget(QGroupBox):
    """
    Widget de configuración SFTP.

    Gestiona la configuración del servidor SFTP utilizado para
    sincronizar copias de seguridad entre dispositivos.
    """

    # Señales
    config_changed = pyqtSignal()
    test_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa el widget SFTP.

        Args:
            parent: Widget padre
        """
        super().__init__("Configuración SFTP", parent)
        self.logger = get_logger(self.__class__.__name__)
        self._actual_password = ""
        self._setup_ui()
        self.load_config()

    def _setup_ui(self) -> None:
        """Configura la interfaz del widget SFTP."""
        layout = QVBoxLayout()

        # Servidor SFTP (campo completo con label arriba)
        host_label = QLabel("Servidor SFTP:")
        host_label.setObjectName("fieldLabel")
        layout.addWidget(host_label)

        # Fila con input de host y puerto
        host_row = QHBoxLayout()
        self.sftp_host_input = QLineEdit()
        self.sftp_host_input.setAccessibleName("Campo servidor SFTP")
        self.sftp_host_input.setPlaceholderText("ejemplo: sftp.tuservidor.com")
        self.sftp_host_input.setReadOnly(True)
        host_row.addWidget(self.sftp_host_input)

        # Puerto (campo corto en la misma fila)
        port_label = QLabel("Puerto:")
        port_label.setObjectName("fieldLabel")
        self.sftp_port_input = QLineEdit()
        self.sftp_port_input.setAccessibleName("Campo puerto SFTP")
        self.sftp_port_input.setPlaceholderText("22")
        self.sftp_port_input.setMaximumWidth(80)
        self.sftp_port_input.setReadOnly(True)
        host_row.addWidget(port_label)
        host_row.addWidget(self.sftp_port_input)

        layout.addLayout(host_row)

        # Usuario (campo completo con label arriba)
        user_label = QLabel("Usuario:")
        user_label.setObjectName("fieldLabel")
        layout.addWidget(user_label)

        # Fila con usuario y contraseña
        user_row = QHBoxLayout()
        self.sftp_user_input = QLineEdit()
        self.sftp_user_input.setAccessibleName("Campo usuario SFTP")
        self.sftp_user_input.setPlaceholderText("ejemplo: u123456789")
        self.sftp_user_input.setReadOnly(True)
        user_row.addWidget(self.sftp_user_input)

        # Contraseña (en la misma fila)
        password_label = QLabel("Contraseña:")
        password_label.setObjectName("fieldLabel")
        self.sftp_password_input = QLineEdit()
        self.sftp_password_input.setAccessibleName("Campo contraseña SFTP")
        self.sftp_password_input.setPlaceholderText("Contraseña del servidor SFTP")
        self.sftp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.sftp_password_input.setReadOnly(True)
        user_row.addWidget(password_label)
        user_row.addWidget(self.sftp_password_input)

        layout.addLayout(user_row)

        # Directorio Base (campo completo con label arriba)
        basedir_label = QLabel("Directorio Base:")
        basedir_label.setObjectName("fieldLabel")
        layout.addWidget(basedir_label)

        self.sftp_basedir_input = QLineEdit()
        self.sftp_basedir_input.setAccessibleName("Campo directorio base SFTP")
        self.sftp_basedir_input.setPlaceholderText("ejemplo: /aplicaciones/guardias_patio")
        self.sftp_basedir_input.setReadOnly(True)
        layout.addWidget(self.sftp_basedir_input)

        # Botones de acción
        botones_layout = QHBoxLayout()

        self.modify_sftp_btn = QPushButton("Modificar Configuración SFTP")
        self.modify_sftp_btn.setAccessibleName("Botón modificar configuración SFTP")
        self.modify_sftp_btn.setIcon(icon_for_button("key"))
        self.modify_sftp_btn.setProperty("warning", "true")
        self.modify_sftp_btn.clicked.connect(self._toggle_editable)

        self.test_sftp_btn = QPushButton("Probar Conexión SFTP")
        self.test_sftp_btn.setAccessibleName("Botón probar conexión SFTP")
        self.test_sftp_btn.setIcon(icon_for_button("test"))
        self.test_sftp_btn.clicked.connect(self._test_connection)

        botones_layout.addWidget(self.modify_sftp_btn)
        botones_layout.addWidget(self.test_sftp_btn)

        layout.addLayout(botones_layout)

        # Nota informativa
        info_label = QLabel(
            "El SFTP se usa para sincronizar copias de seguridad entre "
            "dispositivos de forma automática."
        )
        info_label.setObjectName("cajaInformativa")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Aplicar estilo readonly inicial
        self._apply_readonly_style(True)

        self.setLayout(layout)
        self.setTabOrder(self.sftp_host_input, self.sftp_port_input)
        self.setTabOrder(self.sftp_port_input, self.sftp_user_input)
        self.setTabOrder(self.sftp_user_input, self.sftp_password_input)
        self.setTabOrder(self.sftp_password_input, self.sftp_basedir_input)
        self.setTabOrder(self.sftp_basedir_input, self.modify_sftp_btn)
        self.setTabOrder(self.modify_sftp_btn, self.test_sftp_btn)

    def _apply_readonly_style(self, readonly: bool) -> None:
        pass

    def _toggle_editable(self) -> None:
        """Alterna entre modo solo lectura y editable para los campos SFTP."""
        is_readonly = self.sftp_host_input.isReadOnly()

        if is_readonly:
            # Intentar desbloquear - mostrar advertencia
            if not self._show_global_warning():
                # Usuario canceló, no desbloquear
                return

        # Alternar estado de todos los campos SFTP
        new_state = not is_readonly
        self.sftp_host_input.setReadOnly(new_state)
        self.sftp_port_input.setReadOnly(new_state)
        self.sftp_basedir_input.setReadOnly(new_state)
        self.sftp_user_input.setReadOnly(new_state)
        self.sftp_password_input.setReadOnly(new_state)

        # Actualizar estilos
        self._apply_readonly_style(new_state)

        # Actualizar botón
        if new_state:  # Bloqueado (readonly)
            self.modify_sftp_btn.setText("Modificar Configuración SFTP")
        else:  # Editable
            self.modify_sftp_btn.setText("Bloquear Configuración SFTP")

        self.config_changed.emit()

    def _show_global_warning(self) -> bool:
        """
        Muestra una advertencia sobre la configuración SFTP global.

        Returns:
            bool: True si el usuario acepta continuar, False si cancela.
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Configuración SFTP Global")
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        msg.setText(
            "<h3>Advertencia: Configuración SFTP Global</h3>"
            "<p style='margin-top: 10px;'>"
            "Estás a punto de modificar la configuración SFTP que afecta a "
            "<b>todos los usuarios de este sistema</b>.</p>"
            "<p style='margin-top: 10px; color: #b91c1c;'>"
            "<b>IMPORTANTE:</b> Este servidor SFTP se usa para sincronizar "
            "copias de seguridad entre diferentes dispositivos.<br>"
            "Los cambios se guardarán en el archivo <code>.env</code> del sistema."
            "</p>"
            "<p style='margin-top: 10px;'>"
            "¿Estás seguro de que quieres continuar?</p>"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        # Personalizar botones con estilos
        yes_button = msg.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Sí, modificar configuración SFTP")
        yes_button.setStyleSheet(
            """
            QPushButton {
                min-width: 180px;
                min-height: 35px;
                padding: 5px 15px;
                font-size: 13px;
                background-color: #166529;
                color: white;
                border: 2px solid #047857;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
        """
        )

        no_button = msg.button(QMessageBox.StandardButton.No)
        no_button.setText("Cancelar")
        no_button.setStyleSheet(
            """
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
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """
        )

        result = msg.exec()
        return result == QMessageBox.StandardButton.Yes

    def load_config(self) -> None:
        """Carga la configuración SFTP desde el archivo .env."""
        # Cargar variables de entorno
        load_dotenv()

        # Cargar valores en los campos
        self.sftp_host_input.setText(os.getenv("SFTP_HOST", ""))
        self.sftp_port_input.setText(os.getenv("SFTP_PORT", "22"))
        self.sftp_basedir_input.setText(os.getenv("SFTP_BASE_DIR", "/backups"))
        self.sftp_user_input.setText(os.getenv("SFTP_USERNAME", ""))

        # Solo cargar contraseña si existe (por seguridad no la mostramos completa)
        sftp_password = os.getenv("SFTP_PASSWORD", "")
        if sftp_password:
            self._actual_password = sftp_password
            self.sftp_password_input.setText("••••••••")
            self.sftp_password_input.setPlaceholderText("Contraseña configurada")
        else:
            self._actual_password = ""

    def save_config(self) -> bool:
        """
        Guarda la configuración SFTP en el archivo .env.

        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        # Mostrar advertencia antes de guardar
        if not self._show_global_warning():
            # Usuario canceló, no guardar
            self.logger.info("Usuario canceló la modificación de configuración SFTP")
            return False

        try:
            sftp_host = self.sftp_host_input.text().strip()
            sftp_port = self.sftp_port_input.text().strip()
            sftp_basedir = self.sftp_basedir_input.text().strip()
            sftp_user = self.sftp_user_input.text().strip()
            sftp_password = self.sftp_password_input.text().strip()

            # Si la contraseña son asteriscos, no la cambiamos
            if sftp_password and sftp_password != "••••••••":
                password_to_save = sftp_password
                self._actual_password = sftp_password
            else:
                # Mantener la contraseña actual si no se cambió
                password_to_save = self._actual_password

            # Solo guardar si hay datos completos
            if not sftp_host or not sftp_port or not sftp_user or not password_to_save:
                # No hay configuración SFTP completa, no guardamos
                self.logger.warning("Configuración SFTP incompleta, no se guarda")
                return False

            # Un único escritor: las contraseñas van al llavero y el resto
            # al `.env` de la carpeta de datos. Aquí se usaba la ruta
            # relativa ".env", que en la aplicación instalada apunta al
            # directorio de trabajo y no a donde se lee (SEC-001).
            from core.credenciales import guardar_configuracion

            sftp_vars = {
                "SFTP_HOST": sftp_host,
                "SFTP_PORT": sftp_port,
                "SFTP_BASE_DIR": sftp_basedir,
                "SFTP_USERNAME": sftp_user,
                "SFTP_PASSWORD": password_to_save,
            }
            guardar_configuracion(sftp_vars)

            self.logger.info("Configuración SFTP guardada correctamente")

            # Recargar para mostrar la contraseña enmascarada
            self.load_config()

            self.config_changed.emit()

            return True

        except (OSError, ValueError) as e:
            self.logger.error(f"Error al guardar SFTP: {str(e)}")
            return False

    def _test_connection(self) -> None:
        """
        Prueba la conexión SFTP intentando conectar al servidor
        y listar el directorio base.
        """
        try:
            sftp_host = self.sftp_host_input.text().strip()
            sftp_port = self.sftp_port_input.text().strip()
            sftp_basedir = self.sftp_basedir_input.text().strip()
            sftp_user = self.sftp_user_input.text().strip()
            sftp_password = self.sftp_password_input.text().strip()

            # Validaciones básicas
            if not sftp_host or not sftp_port or not sftp_user:
                self._show_error(
                    "Campos incompletos",
                    "Completa host, puerto y usuario antes de probar la conexión",
                )
                return

            # Si la contraseña son asteriscos, usar la real
            if sftp_password == "••••••••":
                sftp_password = self._actual_password

            if not sftp_password:
                self._show_error(
                    "Contraseña vacía",
                    "La contraseña SFTP es necesaria para probar la conexión",
                )
                return

            # Intentar conectar al servidor SFTP
            self.logger.info(f"Probando conexión SFTP a {sftp_host}:{sftp_port}")

            transport = paramiko.Transport((sftp_host, int(sftp_port)))
            transport.connect(username=sftp_user, password=sftp_password)

            sftp = paramiko.SFTPClient.from_transport(transport)

            # Intentar acceder al directorio base
            try:
                files = sftp.listdir(sftp_basedir)
                file_count = len(files)
            except OSError:
                # Sólo el caso «la carpeta no existe»: paramiko lo señala con
                # OSError. Un fallo de transporte debe seguir subiendo al
                # manejador de fuera, no acabar intentando crear la carpeta.
                sftp.mkdir(sftp_basedir)
                file_count = 0

            sftp.close()
            transport.close()

            # Mostrar mensaje de éxito
            self._show_success(sftp_host, sftp_port, sftp_user, sftp_basedir, file_count)

            self.logger.info(
                f"Prueba de conexión SFTP exitosa - {file_count} archivos en {sftp_basedir}"
            )
            self.test_requested.emit()

        except ImportError:
            self._show_error(
                "❌ Dependencia Faltante",
                "La librería 'paramiko' no está instalada.\n\nInstálala con: pip install paramiko",
            )
            self.logger.error("Librería paramiko no instalada")

        except paramiko.AuthenticationException:
            self._show_error(
                "❌ Error de Autenticación",
                "No se pudo autenticar con el servidor SFTP.\n\nVerifica tu usuario y contraseña.",
            )
            self.logger.error("Error de autenticación SFTP")

        except Exception as e:  # noqa: BLE001
            # `except (OSError, ValueError)` dejaba escapar SSHException, que no
            # hereda de OSError: un banner mal leído o una clave de host cambiada
            # reventaban el diálogo en vez de dar un error legible. Es el mismo
            # fallo que se corrigió en el diálogo de configuración inicial (COD-002).
            self._show_error(
                "❌ Error de Conexión",
                f"No se pudo conectar al servidor SFTP:\n\n{type(e).__name__}: {e}\n\n"
                "Verifica el servidor, puerto y credenciales.",
            )
            self.logger.error(f"Error al probar SFTP: {type(e).__name__}: {e}")

    def _show_success(
        self,
        sftp_host: str,
        sftp_port: str,
        sftp_user: str,
        sftp_basedir: str,
        file_count: int,
    ) -> None:
        """
        Muestra mensaje de éxito de conexión SFTP.

        Args:
            sftp_host: Host del servidor
            sftp_port: Puerto del servidor
            sftp_user: Usuario SFTP
            sftp_basedir: Directorio base
            file_count: Número de archivos encontrados
        """
        success_msg = QMessageBox(self)
        success_msg.setIcon(QMessageBox.Icon.Information)
        success_msg.setWindowTitle("Conexión SFTP Exitosa")
        success_msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        success_msg.setText(
            f"La conexión SFTP se estableció correctamente.<br><br>"
            f"<b>Servidor:</b> <span style='color: #0E5FA8; "
            f"font-style: italic;'>{sftp_host}:{sftp_port}</span><br>"
            f"<b>Usuario:</b> <span style='color: #0E5FA8; "
            f"font-style: italic;'>{sftp_user}</span><br>"
            f"<b>Directorio:</b> <span style='color: #0E5FA8; "
            f"font-style: italic;'>{sftp_basedir}</span><br>"
            f"<b>Archivos encontrados:</b> <span style='color: #166529; "
            f"font-weight: bold;'>{file_count}</span><br><br>"
            "El servidor está listo para sincronizar copias de seguridad."
        )

        # Añadir botón OK con estilo visible
        success_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        ok_button = success_msg.button(QMessageBox.StandardButton.Ok)
        ok_button.setText("Entendido")
        ok_button.setObjectName("botonConfirmarVerde")

        success_msg.exec()

    def _show_error(self, title: str, message: str) -> None:
        """
        Muestra un diálogo de error.

        Args:
            title: Título del diálogo
            message: Mensaje de error
        """
        error_msg = QMessageBox(self)
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setWindowTitle(title)
        error_msg.setText(message)
        error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        ok_button = error_msg.button(QMessageBox.StandardButton.Ok)
        ok_button.setText("Entendido")
        ok_button.setStyleSheet(
            """
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
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """
        )
        error_msg.exec()

    def get_config_dict(self) -> dict:
        """
        Obtiene la configuración SFTP como diccionario.

        Returns:
            dict: Configuración SFTP
        """
        return {
            "host": self.sftp_host_input.text().strip(),
            "port": self.sftp_port_input.text().strip(),
            "base_dir": self.sftp_basedir_input.text().strip(),
            "username": self.sftp_user_input.text().strip(),
            "password": self._actual_password,
        }

    def set_config_dict(self, config: dict) -> None:
        """
        Establece la configuración SFTP desde un diccionario.

        Args:
            config: Configuración SFTP
        """
        self.sftp_host_input.setText(config.get("host", ""))
        self.sftp_port_input.setText(config.get("port", "22"))
        self.sftp_basedir_input.setText(config.get("base_dir", "/backups"))
        self.sftp_user_input.setText(config.get("username", ""))

        password = config.get("password", "")
        if password:
            self._actual_password = password
            self.sftp_password_input.setText("••••••••")
        else:
            self._actual_password = ""
            self.sftp_password_input.setText("")

    def test_connection(self) -> None:
        """Método público para probar la conexión SFTP."""
        self._test_connection()
