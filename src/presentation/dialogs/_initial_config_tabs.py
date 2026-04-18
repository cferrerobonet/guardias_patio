"""
Constructores de tabs para InitialConfigDialog.
Extraído de initial_config_dialog.py para reducir el tamaño del módulo principal.
Las funciones reciben la instancia del diálogo y establecen sus atributos de widget.
"""

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from utils.icons import icon_for_button


def create_sftp_tab(dialog) -> QWidget:
    """
    Construye el tab de configuración SFTP.
    Establece los atributos de widget SFTP en `dialog` y devuelve el QWidget.
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Explicación SFTP
    info_box = QGroupBox("¿Por qué es obligatorio SFTP?")
    info_layout = QVBoxLayout()

    info_text = QLabel(
        "<p><b>El servidor SFTP es crítico</b> para el funcionamiento de la aplicación:</p>"
        "<ul>"
        "<li><b>Sincronización en la nube:</b> Permite trabajar desde múltiples "
        "dispositivos</li>"
        "<li><b>Copias de seguridad automáticas:</b> Tus datos están siempre "
        "protegidos</li>"
        "<li><b>Recuperación ante fallos:</b> Si pierdes tu dispositivo, tus datos "
        "están seguros</li>"
        "</ul>"
        "<p style='color: #dc2626; font-weight: bold;'>"
        "Sin SFTP configurado, la aplicación no puede garantizar la seguridad "
        "de tus datos ni permitir el trabajo colaborativo."
        "</p>"
    )
    info_text.setWordWrap(True)
    info_text.setStyleSheet("""
        QLabel {
            padding: 15px;
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            border-radius: 5px;
            line-height: 1.5;
        }
    """)

    info_layout.addWidget(info_text)
    info_box.setLayout(info_layout)
    layout.addWidget(info_box)

    # Formulario SFTP
    form_box = QGroupBox("Datos del Servidor SFTP")
    form_layout = QVBoxLayout()

    # Host
    host_row = QHBoxLayout()
    host_label = QLabel("Servidor:")
    host_label.setMinimumWidth(120)
    dialog.sftp_host_input = QLineEdit()
    dialog.sftp_host_input.setPlaceholderText("ejemplo: sftp.example.com")
    dialog.sftp_host_input.textChanged.connect(dialog._on_sftp_changed)
    host_row.addWidget(host_label)
    host_row.addWidget(dialog.sftp_host_input)

    # Puerto
    port_row = QHBoxLayout()
    port_label = QLabel("Puerto:")
    port_label.setMinimumWidth(120)
    dialog.sftp_port_input = QLineEdit()
    dialog.sftp_port_input.setPlaceholderText("22")
    dialog.sftp_port_input.setText("22")
    dialog.sftp_port_input.setMaximumWidth(100)
    dialog.sftp_port_input.textChanged.connect(dialog._on_sftp_changed)
    port_row.addWidget(port_label)
    port_row.addWidget(dialog.sftp_port_input)
    port_row.addStretch()

    # Usuario
    user_row = QHBoxLayout()
    user_label = QLabel("Usuario:")
    user_label.setMinimumWidth(120)
    dialog.sftp_user_input = QLineEdit()
    dialog.sftp_user_input.setPlaceholderText("tu_usuario_sftp")
    dialog.sftp_user_input.textChanged.connect(dialog._on_sftp_changed)
    user_row.addWidget(user_label)
    user_row.addWidget(dialog.sftp_user_input)

    # Contraseña
    password_row = QHBoxLayout()
    password_label = QLabel("Contraseña:")
    password_label.setMinimumWidth(120)
    dialog.sftp_password_input = QLineEdit()
    dialog.sftp_password_input.setPlaceholderText("Contraseña del servidor")
    dialog.sftp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
    dialog.sftp_password_input.textChanged.connect(dialog._on_sftp_changed)
    password_row.addWidget(password_label)
    password_row.addWidget(dialog.sftp_password_input)

    # Directorio base
    basedir_row = QHBoxLayout()
    basedir_label = QLabel("Directorio Base:")
    basedir_label.setMinimumWidth(120)
    dialog.sftp_basedir_input = QLineEdit()
    dialog.sftp_basedir_input.setPlaceholderText("/aplicaciones/guardias_patio")
    dialog.sftp_basedir_input.setText("/aplicaciones/guardias_patio")
    dialog.sftp_basedir_input.textChanged.connect(dialog._on_sftp_changed)
    basedir_row.addWidget(basedir_label)
    basedir_row.addWidget(dialog.sftp_basedir_input)

    form_layout.addLayout(host_row)
    form_layout.addLayout(port_row)
    form_layout.addLayout(user_row)
    form_layout.addLayout(password_row)
    form_layout.addLayout(basedir_row)

    # Botones de acción
    action_row = QHBoxLayout()
    action_row.setSpacing(10)
    dialog.sftp_test_btn = QPushButton("Probar Conexión")
    dialog.sftp_test_btn.setIcon(icon_for_button("test"))
    dialog.sftp_test_btn.setMinimumWidth(180)
    dialog.sftp_test_btn.setMinimumHeight(36)
    dialog.sftp_test_btn.clicked.connect(dialog._test_sftp)
    dialog.sftp_save_btn = QPushButton("Guardar Configuración")
    dialog.sftp_save_btn.setIcon(icon_for_button("save"))
    dialog.sftp_save_btn.setMinimumWidth(180)
    dialog.sftp_save_btn.setMinimumHeight(36)
    dialog.sftp_save_btn.clicked.connect(dialog._save_sftp)
    action_row.addWidget(dialog.sftp_test_btn)
    action_row.addWidget(dialog.sftp_save_btn)

    form_layout.addLayout(action_row)
    form_layout.addSpacing(10)

    # Botón de carga desde JSON encriptado
    load_json_row = QHBoxLayout()
    dialog.sftp_load_json_btn = QPushButton("Cargar configuración desde archivo JSON")
    dialog.sftp_load_json_btn.setIcon(icon_for_button("open"))
    dialog.sftp_load_json_btn.setMinimumHeight(36)
    dialog.sftp_load_json_btn.setStyleSheet("""
        QPushButton {
            background-color: #6366f1;
            color: white;
            padding: 8px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #4f46e5;
        }
    """)
    dialog.sftp_load_json_btn.clicked.connect(dialog._load_sftp_from_json)
    load_json_row.addWidget(dialog.sftp_load_json_btn)

    form_layout.addLayout(load_json_row)

    form_box.setLayout(form_layout)
    layout.addWidget(form_box)

    layout.addStretch()

    widget.setLayout(layout)
    return widget


def create_smtp_tab(dialog) -> QWidget:
    """
    Construye el tab de configuración SMTP.
    Establece los atributos de widget SMTP en `dialog` y devuelve el QWidget.
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Explicación SMTP
    info_box = QGroupBox("Configuración SMTP (Opcional)")
    info_layout = QVBoxLayout()

    info_text = QLabel(
        "<p><b>El servidor SMTP permite enviar emails automáticos</b> desde la aplicación:</p>"
        "<ul>"
        "<li><b>Calendarios por email:</b> Enviar calendarios de guardias a profesores</li>"
        "<li><b>Recuperación de contraseñas:</b> Códigos de recuperación por email</li>"
        "<li><b>Notificaciones:</b> Alertas y avisos importantes</li>"
        "</ul>"
        "<p style='color: #059669;'>"
        "<b>Esta funcionalidad NO es crítica.</b> Si no configuras SMTP ahora, podrás "
        "seguir usando la aplicación normalmente. Solo necesitarás copiar manualmente los "
        "calendarios o códigos de recuperación."
        "</p>"
        "<p style='color: #6b7280; font-size: 13px;'>"
        "<b>Tip:</b> Los datos SMTP son los de la cuenta de email que enviará los mensajes. "
        "Puede ser cualquier cuenta de Gmail, Outlook, etc."
        "</p>"
    )
    info_text.setWordWrap(True)
    info_text.setStyleSheet("""
        QLabel {
            padding: 15px;
            background-color: #d1fae5;
            border-left: 4px solid #10b981;
            border-radius: 5px;
            line-height: 1.5;
        }
    """)

    info_layout.addWidget(info_text)
    info_box.setLayout(info_layout)
    layout.addWidget(info_box)

    # Formulario SMTP
    form_box = QGroupBox("Datos del Servidor SMTP")
    form_layout = QVBoxLayout()

    # Servidor
    server_row = QHBoxLayout()
    server_label = QLabel("Servidor:")
    server_label.setMinimumWidth(120)
    dialog.smtp_server_input = QLineEdit()
    dialog.smtp_server_input.setPlaceholderText("smtp.gmail.com")
    dialog.smtp_server_input.textChanged.connect(dialog._on_smtp_changed)
    server_row.addWidget(server_label)
    server_row.addWidget(dialog.smtp_server_input)

    # Puerto
    smtp_port_row = QHBoxLayout()
    smtp_port_label = QLabel("Puerto:")
    smtp_port_label.setMinimumWidth(120)
    dialog.smtp_port_input = QLineEdit()
    dialog.smtp_port_input.setPlaceholderText("587")
    dialog.smtp_port_input.setText("587")
    dialog.smtp_port_input.setMaximumWidth(100)
    dialog.smtp_port_input.textChanged.connect(dialog._on_smtp_changed)
    smtp_port_row.addWidget(smtp_port_label)
    smtp_port_row.addWidget(dialog.smtp_port_input)
    smtp_port_row.addStretch()

    # Usuario
    smtp_user_row = QHBoxLayout()
    smtp_user_label = QLabel("Email:")
    smtp_user_label.setMinimumWidth(120)
    dialog.smtp_user_input = QLineEdit()
    dialog.smtp_user_input.setPlaceholderText("tu_email@gmail.com")
    dialog.smtp_user_input.textChanged.connect(dialog._on_smtp_changed)
    smtp_user_row.addWidget(smtp_user_label)
    smtp_user_row.addWidget(dialog.smtp_user_input)

    # Contraseña
    smtp_password_row = QHBoxLayout()
    smtp_password_label = QLabel("Contraseña:")
    smtp_password_label.setMinimumWidth(120)
    dialog.smtp_password_input = QLineEdit()
    dialog.smtp_password_input.setPlaceholderText("Contraseña o App Password")
    dialog.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
    dialog.smtp_password_input.textChanged.connect(dialog._on_smtp_changed)
    smtp_password_row.addWidget(smtp_password_label)
    smtp_password_row.addWidget(dialog.smtp_password_input)

    # Nombre del remitente
    smtp_from_name_row = QHBoxLayout()
    smtp_from_name_label = QLabel("Nombre del Remitente:")
    smtp_from_name_label.setMinimumWidth(120)
    dialog.smtp_from_name_input = QLineEdit()
    dialog.smtp_from_name_input.setPlaceholderText("Guardias de Patio")
    dialog.smtp_from_name_input.textChanged.connect(dialog._on_smtp_changed)
    smtp_from_name_row.addWidget(smtp_from_name_label)
    smtp_from_name_row.addWidget(dialog.smtp_from_name_input)

    form_layout.addLayout(server_row)
    form_layout.addLayout(smtp_port_row)
    form_layout.addLayout(smtp_user_row)
    form_layout.addLayout(smtp_password_row)
    form_layout.addLayout(smtp_from_name_row)

    # Botones de acción
    smtp_action_row = QHBoxLayout()
    smtp_action_row.setSpacing(10)
    dialog.smtp_test_btn = QPushButton("Probar Conexión")
    dialog.smtp_test_btn.setIcon(icon_for_button("test"))
    dialog.smtp_test_btn.setMinimumWidth(180)
    dialog.smtp_test_btn.setMinimumHeight(36)
    dialog.smtp_test_btn.clicked.connect(dialog._test_smtp)
    dialog.smtp_save_btn = QPushButton("Guardar Configuración")
    dialog.smtp_save_btn.setIcon(icon_for_button("save"))
    dialog.smtp_save_btn.setMinimumWidth(180)
    dialog.smtp_save_btn.setMinimumHeight(36)
    dialog.smtp_save_btn.clicked.connect(dialog._save_smtp)
    smtp_action_row.addWidget(dialog.smtp_test_btn)
    smtp_action_row.addWidget(dialog.smtp_save_btn)

    form_layout.addLayout(smtp_action_row)
    form_layout.addSpacing(10)

    # Botón de carga desde JSON encriptado
    smtp_load_json_row = QHBoxLayout()
    dialog.smtp_load_json_btn = QPushButton("Cargar configuración desde archivo JSON")
    dialog.smtp_load_json_btn.setIcon(icon_for_button("open"))
    dialog.smtp_load_json_btn.setMinimumHeight(36)
    dialog.smtp_load_json_btn.setStyleSheet("""
        QPushButton {
            background-color: #6366f1;
            color: white;
            padding: 8px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #4f46e5;
        }
    """)
    dialog.smtp_load_json_btn.clicked.connect(dialog._load_smtp_from_json)
    smtp_load_json_row.addWidget(dialog.smtp_load_json_btn)

    form_layout.addLayout(smtp_load_json_row)

    form_box.setLayout(form_layout)
    layout.addWidget(form_box)

    layout.addStretch()

    widget.setLayout(layout)
    return widget
