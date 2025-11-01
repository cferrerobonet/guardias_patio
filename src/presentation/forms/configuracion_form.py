"""
Configuración Form - Refactorizado.

Form para gestionar la configuración del curso escolar.
Sigue el patrón MVP usando Use Cases.
"""

import ui_styles as styles
from application.dtos.configuracion_dto import ActualizarConfiguracionDTO
from application.use_cases.configuracion import (
    ActualizarConfiguracionUseCase,
    ObtenerConfiguracionUseCase,
)
from core.exceptions import NotFoundError
from database.db_manager import get_current_user_id
from PyQt6.QtCore import QDate, Qt, QTime
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session
from sync.sync_manager import UserAuth

from presentation.forms.base_form import BaseForm


class ConfiguracionForm(BaseForm):
    """
    Formulario para gestionar la configuración del curso.

    Permite configurar:
    - Fechas del curso
    - Horarios de recreos
    - Ajustes de tutores/no tutores
    - Festivos y días no lectivos
    - Configuración avanzada
    """

    def __init__(self, session: Session, parent=None):
        """
        Inicializa el formulario de configuración.

        Args:
            session: Sesión de SQLAlchemy
            parent: Widget padre
        """
        super().__init__(session, parent)

        # Inicializar Use Cases
        self.obtener_config_uc = ObtenerConfiguracionUseCase(session)
        self.actualizar_config_uc = ActualizarConfiguracionUseCase(session)

        # Inicializar gestor de usuarios
        self.user_auth = UserAuth()
        self.current_username = get_current_user_id()

        # Configurar UI
        self.setup_ui()

        # Cargar configuración existente si hay
        self.cargar_configuracion()

        # Cargar configuración SMTP
        self.cargar_smtp()

        # Cargar configuración SFTP
        self.cargar_sftp()

    def setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Configuración del Curso")

        # Layout principal que contendrá el scroll area
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Crear el contenedor con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Widget contenedor del contenido
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Título principal
        titulo = QLabel("⚙️ CONFIGURACIÓN DEL CURSO ESCOLAR")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        content_layout.addWidget(titulo)

        # ===== FILA 1: Fechas + Recreos Mañana + Recreos Tarde (3 columnas) =====
        fila1_layout = QHBoxLayout()
        fila1_layout.setSpacing(10)

        # Columna 1: Fechas
        grupo_fechas = self._crear_grupo_fechas()
        fila1_layout.addWidget(grupo_fechas)

        # Columna 2: Recreos Mañana
        grupo_manana = self._crear_grupo_recreos_manana()
        fila1_layout.addWidget(grupo_manana)

        # Columna 3: Recreos Tarde
        grupo_tarde = self._crear_grupo_recreos_tarde()
        fila1_layout.addWidget(grupo_tarde)

        content_layout.addLayout(fila1_layout)

        # ===== FILA 2: Ajustes + Festivos + Perfil (3 columnas) =====
        fila2_layout = QHBoxLayout()
        fila2_layout.setSpacing(10)

        grupo_ajustes = self._crear_grupo_ajustes()
        fila2_layout.addWidget(grupo_ajustes)

        grupo_festivos = self._crear_grupo_festivos()
        fila2_layout.addWidget(grupo_festivos)

        grupo_perfil = self._crear_grupo_perfil_usuario()
        fila2_layout.addWidget(grupo_perfil)

        content_layout.addLayout(fila2_layout)

        # ===== FILA 3: SMTP + SFTP (2 columnas) =====
        fila3_layout = QHBoxLayout()
        fila3_layout.setSpacing(10)

        grupo_smtp = self._crear_grupo_smtp()
        fila3_layout.addWidget(grupo_smtp)

        grupo_sftp = self._crear_grupo_sftp()
        fila3_layout.addWidget(grupo_sftp)

        content_layout.addLayout(fila3_layout)

        # Botones
        btn_layout = self._crear_botones()
        content_layout.addLayout(btn_layout)

        # Espacio flexible
        content_layout.addStretch()

        # Establecer el layout en el widget contenedor
        content_widget.setLayout(content_layout)

        # Agregar el widget al scroll area
        scroll_area.setWidget(content_widget)

        # Agregar el scroll area al layout principal
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def _crear_grupo_fechas(self) -> QGroupBox:
        """Crea el grupo de fechas del curso."""
        grupo = QGroupBox("📅 Fechas del Curso")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        # Fecha inicio
        label_inicio = QLabel("Inicio:")
        label_inicio.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_inicio)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setStyleSheet(styles.STYLE_INPUT)
        layout.addWidget(self.fecha_inicio_input)

        # Fecha fin
        label_fin = QLabel("Fin:")
        label_fin.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_fin)

        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addMonths(9))
        self.fecha_fin_input.setStyleSheet(styles.STYLE_INPUT)
        layout.addWidget(self.fecha_fin_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_recreos_manana(self) -> QGroupBox:
        """Crea el grupo de recreos de mañana."""
        grupo = QGroupBox("☀️ Recreos de Mañana")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(3)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col1.addWidget(label_r1)

        self.recreo1_manana_input = QTimeEdit()
        self.recreo1_manana_input.setTime(QTime(10, 30))
        self.recreo1_manana_input.setStyleSheet(styles.STYLE_INPUT)
        col1.addWidget(self.recreo1_manana_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(3)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col2.addWidget(label_r2)

        self.recreo2_manana_input = QTimeEdit()
        self.recreo2_manana_input.setTime(QTime(12, 0))
        self.recreo2_manana_input.setStyleSheet(styles.STYLE_INPUT)
        col2.addWidget(self.recreo2_manana_input)
        layout.addLayout(col2)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_recreos_tarde(self) -> QGroupBox:
        """Crea el grupo de recreos de tarde."""
        grupo = QGroupBox("🌙 Recreos de Tarde (opcional)")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(3)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col1.addWidget(label_r1)

        self.recreo1_tarde_input = QTimeEdit()
        self.recreo1_tarde_input.setTime(QTime(15, 30))
        self.recreo1_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        col1.addWidget(self.recreo1_tarde_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(3)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col2.addWidget(label_r2)

        self.recreo2_tarde_input = QTimeEdit()
        self.recreo2_tarde_input.setTime(QTime(17, 0))
        self.recreo2_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        col2.addWidget(self.recreo2_tarde_input)
        layout.addLayout(col2)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_ajustes(self) -> QGroupBox:
        """Crea el grupo de ajustes adicionales."""
        grupo = QGroupBox("🔧 Ajustes Adicionales")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        # Multiplicador tutores
        label_tutores = QLabel("Multiplicador tutores:")
        label_tutores.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_tutores)

        self.ajuste_tutores_input = QLineEdit()
        self.ajuste_tutores_input.setPlaceholderText("0.90")
        self.ajuste_tutores_input.setStyleSheet(styles.STYLE_INPUT)
        layout.addWidget(self.ajuste_tutores_input)

        # Multiplicador no tutores
        label_no_tutores = QLabel("Multiplicador no tutores:")
        label_no_tutores.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_no_tutores)

        self.ajuste_no_tutores_input = QLineEdit()
        self.ajuste_no_tutores_input.setPlaceholderText("1.00")
        self.ajuste_no_tutores_input.setStyleSheet(styles.STYLE_INPUT)
        layout.addWidget(self.ajuste_no_tutores_input)

        # Selector de algoritmo
        label_algoritmo = QLabel("Algoritmo de asignación:")
        label_algoritmo.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_algoritmo)

        self.algoritmo_combo = QComboBox()
        self.algoritmo_combo.addItem(
            "v2.9 - Clásico (7 fases)", "v2.9"
        )
        self.algoritmo_combo.addItem(
            "v3.0 - Simple Determinista ⚡", "v3.0"
        )
        self.algoritmo_combo.setStyleSheet(styles.STYLE_INPUT)
        self.algoritmo_combo.setToolTip(
            "v2.9: Algoritmo clásico de 7 fases (CSP, Simulated Annealing)\n"
            "v3.0: Algoritmo simple determinista que garantiza 100% cobertura"
        )
        layout.addWidget(self.algoritmo_combo)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_festivos(self) -> QGroupBox:
        """Crea el grupo de festivos."""
        grupo = QGroupBox("🎉 Festivos y Días No Lectivos")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        label_auto = QLabel("Aplicar festivos automáticos:")
        label_auto.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_auto)

        self.festivos_auto_input = QLineEdit()
        self.festivos_auto_input.setPlaceholderText("1 (sí) / 0 (no)")
        self.festivos_auto_input.setStyleSheet(styles.STYLE_INPUT)
        layout.addWidget(self.festivos_auto_input)

        label_custom = QLabel("Días no lectivos (YYYY-MM-DD):")
        label_custom.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_custom)

        self.no_lectivos_input = QLineEdit()
        self.no_lectivos_input.setPlaceholderText("2025-10-09, 2025-10-12")
        self.no_lectivos_input.setStyleSheet(styles.STYLE_INPUT)
        layout.addWidget(self.no_lectivos_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_perfil_usuario(self) -> QGroupBox:
        """Crea el grupo de perfil de usuario."""
        grupo = QGroupBox("👤 Mi Perfil de Usuario")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        # Obtener datos del usuario actual
        user_data = self.user_auth.users.get(self.current_username, {})
        current_email = user_data.get("email", "")

        # Nombre de usuario (solo lectura)
        label_username = QLabel("Usuario:")
        label_username.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_username)

        self.username_display = QLineEdit()
        self.username_display.setText(self.current_username)
        self.username_display.setReadOnly(True)
        self.username_display.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
                font-weight: 500;
            }
        """)
        layout.addWidget(self.username_display)

        # Email (editable)
        label_email = QLabel("Email:")
        label_email.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_email)

        self.email_input = QLineEdit()
        self.email_input.setText(current_email)
        self.email_input.setPlaceholderText("tu@email.com")
        self.email_input.setStyleSheet(styles.STYLE_INPUT)
        layout.addWidget(self.email_input)

        # Botón de cambiar contraseña
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        self.change_password_btn = QPushButton("🔒 Cambiar Contraseña")
        self.change_password_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.change_password_btn.clicked.connect(self.cambiar_contrasena)
        btn_layout.addWidget(self.change_password_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_smtp(self) -> QGroupBox:
        """Crea el grupo de configuración SMTP."""
        grupo = QGroupBox("📧 Config SMTP")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # FILA 1: Servidor y Puerto (Puerto más corto)
        fila1_layout = QHBoxLayout()
        fila1_layout.setSpacing(10)

        # Servidor (campo largo)
        servidor_container = QVBoxLayout()
        servidor_container.setSpacing(3)
        label_server = QLabel("Servidor SMTP:")
        label_server.setStyleSheet(styles.STYLE_LABEL_FIELD)
        servidor_container.addWidget(label_server)

        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.ionos.es")
        self.smtp_server_input.setReadOnly(True)
        self.smtp_server_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        servidor_container.addWidget(self.smtp_server_input)
        fila1_layout.addLayout(servidor_container, 3)  # 3 partes de espacio

        # Puerto (campo corto)
        puerto_container = QVBoxLayout()
        puerto_container.setSpacing(3)
        label_port = QLabel("Puerto:")
        label_port.setStyleSheet(styles.STYLE_LABEL_FIELD)
        puerto_container.addWidget(label_port)

        self.smtp_port_input = QLineEdit()
        self.smtp_port_input.setPlaceholderText("587")
        self.smtp_port_input.setMaximumWidth(80)
        self.smtp_port_input.setReadOnly(True)
        self.smtp_port_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        puerto_container.addWidget(self.smtp_port_input)
        fila1_layout.addLayout(puerto_container, 1)  # 1 parte de espacio

        layout.addLayout(fila1_layout)

        # FILA 2: Usuario y Contraseña (misma longitud)
        fila2_layout = QHBoxLayout()
        fila2_layout.setSpacing(10)

        # Usuario
        usuario_container = QVBoxLayout()
        usuario_container.setSpacing(3)
        label_user = QLabel("Usuario:")
        label_user.setStyleSheet(styles.STYLE_LABEL_FIELD)
        usuario_container.addWidget(label_user)

        self.smtp_user_input = QLineEdit()
        self.smtp_user_input.setPlaceholderText("correo@ejemplo.com")
        self.smtp_user_input.setReadOnly(True)
        self.smtp_user_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        usuario_container.addWidget(self.smtp_user_input)
        fila2_layout.addLayout(usuario_container, 1)

        # Contraseña
        password_container = QVBoxLayout()
        password_container.setSpacing(3)
        label_password = QLabel("Contraseña:")
        label_password.setStyleSheet(styles.STYLE_LABEL_FIELD)
        password_container.addWidget(label_password)

        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setPlaceholderText("••••••••")
        self.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_password_input.setReadOnly(True)
        self.smtp_password_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        password_container.addWidget(self.smtp_password_input)
        fila2_layout.addLayout(password_container, 1)

        layout.addLayout(fila2_layout)

        # Botones SMTP
        smtp_btn_layout = QHBoxLayout()
        smtp_btn_layout.setSpacing(8)

        self.modify_smtp_btn = QPushButton("🔓 Modificar Configuración SMTP")
        self.modify_smtp_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.modify_smtp_btn.clicked.connect(self.toggle_smtp_editable)
        smtp_btn_layout.addWidget(self.modify_smtp_btn, 1)

        self.test_smtp_btn = QPushButton("✉️ Probar Conexión SMTP")
        self.test_smtp_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.test_smtp_btn.clicked.connect(self.probar_smtp)
        smtp_btn_layout.addWidget(self.test_smtp_btn, 1)

        layout.addLayout(smtp_btn_layout)

        # Nota informativa
        nota = QLabel("💡 Para Gmail, usa una App Password en lugar de tu contraseña normal.")
        nota.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 11px;
                padding: 5px;
                background-color: #f3f4f6;
                border-radius: 3px;
            }
        """)
        nota.setWordWrap(True)
        layout.addWidget(nota)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_sftp(self) -> QGroupBox:
        """Crea el grupo de configuración SFTP."""
        grupo = QGroupBox("☁️ Config SFTP")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # FILA 1: Servidor y Puerto (Puerto más corto)
        fila1_layout = QHBoxLayout()
        fila1_layout.setSpacing(10)

        # Servidor (campo largo)
        servidor_container = QVBoxLayout()
        servidor_container.setSpacing(3)
        label_host = QLabel("Servidor SFTP:")
        label_host.setStyleSheet(styles.STYLE_LABEL_FIELD)
        servidor_container.addWidget(label_host)

        self.sftp_host_input = QLineEdit()
        self.sftp_host_input.setPlaceholderText("home491590459.1and1-data.host")
        self.sftp_host_input.setReadOnly(True)
        self.sftp_host_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        servidor_container.addWidget(self.sftp_host_input)
        fila1_layout.addLayout(servidor_container, 3)  # 3 partes de espacio

        # Puerto (campo corto)
        puerto_container = QVBoxLayout()
        puerto_container.setSpacing(3)
        label_port = QLabel("Puerto:")
        label_port.setStyleSheet(styles.STYLE_LABEL_FIELD)
        puerto_container.addWidget(label_port)

        self.sftp_port_input = QLineEdit()
        self.sftp_port_input.setPlaceholderText("22")
        self.sftp_port_input.setMaximumWidth(80)
        self.sftp_port_input.setReadOnly(True)
        self.sftp_port_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        puerto_container.addWidget(self.sftp_port_input)
        fila1_layout.addLayout(puerto_container, 1)  # 1 parte de espacio

        layout.addLayout(fila1_layout)

        # FILA 2: Usuario y Contraseña (misma longitud)
        fila2_layout = QHBoxLayout()
        fila2_layout.setSpacing(10)

        # Usuario
        usuario_container = QVBoxLayout()
        usuario_container.setSpacing(3)
        label_user = QLabel("Usuario:")
        label_user.setStyleSheet(styles.STYLE_LABEL_FIELD)
        usuario_container.addWidget(label_user)

        self.sftp_user_input = QLineEdit()
        self.sftp_user_input.setPlaceholderText("u123456789")
        self.sftp_user_input.setReadOnly(True)
        self.sftp_user_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        usuario_container.addWidget(self.sftp_user_input)
        fila2_layout.addLayout(usuario_container, 1)

        # Contraseña
        password_container = QVBoxLayout()
        password_container.setSpacing(3)
        label_password = QLabel("Contraseña:")
        label_password.setStyleSheet(styles.STYLE_LABEL_FIELD)
        password_container.addWidget(label_password)

        self.sftp_password_input = QLineEdit()
        self.sftp_password_input.setPlaceholderText("••••••••")
        self.sftp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.sftp_password_input.setReadOnly(True)
        self.sftp_password_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        password_container.addWidget(self.sftp_password_input)
        fila2_layout.addLayout(password_container, 1)

        layout.addLayout(fila2_layout)

        # FILA 3: Directorio Base (campo completo)
        fila3_layout = QVBoxLayout()
        fila3_layout.setSpacing(3)

        label_basedir = QLabel("Directorio Base:")
        label_basedir.setStyleSheet(styles.STYLE_LABEL_FIELD)
        fila3_layout.addWidget(label_basedir)

        self.sftp_basedir_input = QLineEdit()
        self.sftp_basedir_input.setPlaceholderText("/aplicaciones/guardias_patio")
        self.sftp_basedir_input.setReadOnly(True)
        self.sftp_basedir_input.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                background-color: #e5e7eb;
                color: #4b5563;
                border: 1px solid #d1d5db;
                padding: 5px;
            }
        """)
        fila3_layout.addWidget(self.sftp_basedir_input)

        layout.addLayout(fila3_layout)

        # Botones SFTP
        sftp_btn_layout = QHBoxLayout()
        sftp_btn_layout.setSpacing(8)

        self.modify_sftp_btn = QPushButton("🔓 Modificar Configuración SFTP")
        self.modify_sftp_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.modify_sftp_btn.clicked.connect(self.toggle_sftp_editable)
        sftp_btn_layout.addWidget(self.modify_sftp_btn, 1)

        self.test_sftp_btn = QPushButton("☁️ Probar Conexión SFTP")
        self.test_sftp_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.test_sftp_btn.clicked.connect(self.probar_sftp)
        sftp_btn_layout.addWidget(self.test_sftp_btn, 1)

        layout.addLayout(sftp_btn_layout)

        # Nota informativa
        nota = QLabel("💡 El SFTP se usa para sincronizar copias de seguridad entre diferentes dispositivos.")
        nota.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 11px;
                padding: 5px;
                background-color: #f3f4f6;
                border-radius: 3px;
            }
        """)
        nota.setWordWrap(True)
        layout.addWidget(nota)

        grupo.setLayout(layout)
        return grupo

    def _crear_botones(self) -> QHBoxLayout:
        """Crea los botones de acción."""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.save_btn = QPushButton("💾 Guardar Configuración")
        self.save_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.save_btn.clicked.connect(self.guardar_configuracion)

        self.load_btn = QPushButton("🔄 Cargar Actual")
        self.load_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.load_btn.clicked.connect(self.cargar_configuracion)

        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        layout.addStretch()

        return layout

    def guardar_configuracion(self) -> None:
        """
        Guarda la configuración usando el Use Case.

        Valida los datos y ejecuta ActualizarConfiguracionUseCase.
        También guarda la configuración SMTP si fue modificada.
        """
        try:
            # Validar formulario
            es_valido, mensaje = self.validar_formulario()
            if not es_valido:
                self.mostrar_advertencia("Validación", mensaje)
                return

            # Crear DTO con recreos_config generado automáticamente
            dto = ActualizarConfiguracionDTO(
                fecha_inicio_curso=self.fecha_inicio_input.date().toPyDate(),
                fecha_fin_curso=self.fecha_fin_input.date().toPyDate(),
                hora_recreo1_manana=self.recreo1_manana_input.time().toPyTime(),
                hora_recreo2_manana=self.recreo2_manana_input.time().toPyTime(),
                hora_recreo1_tarde=self.recreo1_tarde_input.time().toPyTime(),
                hora_recreo2_tarde=self.recreo2_tarde_input.time().toPyTime(),
                ajuste_tutores=float(self.ajuste_tutores_input.text() or 1.0),
                ajuste_no_tutores=float(self.ajuste_no_tutores_input.text() or 1.0),
                activar_festivos_automaticos=(
                    (self.festivos_auto_input.text() or "1").strip() in ("1", "true", "True")
                ),
                dias_no_lectivos_personalizados=(self.no_lectivos_input.text() or "").strip(),
                recreos_config=self._generar_recreos_config_json(),
                algoritmo_asignacion=self.algoritmo_combo.currentData()  # Nuevo en v3.0
            )

            # Ejecutar Use Case
            config = self.actualizar_config_uc.execute(dto)

            # Guardar email del usuario
            email_guardado = self._guardar_email_interno()

            # Guardar configuración SMTP SOLO si los campos están desbloqueados
            smtp_guardado = False
            smtp_fue_modificado = not self.smtp_server_input.isReadOnly()

            if smtp_fue_modificado:
                smtp_guardado = self.guardar_smtp()

                # Bloquear campos SMTP después de guardar exitosamente
                if smtp_guardado:
                    self.toggle_smtp_editable()  # Bloquear

            # Guardar configuración SFTP SOLO si los campos están desbloqueados
            sftp_guardado = False
            sftp_fue_modificado = not self.sftp_host_input.isReadOnly()

            if sftp_fue_modificado:
                sftp_guardado = self.guardar_sftp()

                # Bloquear campos SFTP después de guardar exitosamente
                if sftp_guardado:
                    self.toggle_sftp_editable()  # Bloquear

            # Mostrar éxito
            # Extraer solo los años de las fechas
            año_inicio = config.fecha_inicio_curso.year
            año_fin = config.fecha_fin_curso.year

            mensaje_exito = (
                f"La configuración del curso "
                f"<span style='color: #007ACC; font-style: italic;'>{año_inicio}-{año_fin}</span> "
                f"ha sido guardada correctamente."
            )

            if smtp_guardado:
                mensaje_exito += "<br><br>La configuración SMTP también se ha guardado."

            if sftp_guardado:
                mensaje_exito += "<br><br>La configuración SFTP también se ha guardado."

            if email_guardado:
                mensaje_exito += "<br><br>Tu email ha sido actualizado."

            self.mostrar_exito("Configuración Guardada", mensaje_exito)

        except Exception as e:
            self.manejar_excepcion(e, "guardar configuración")

    def cargar_configuracion(self) -> None:
        """
        Carga la configuración actual usando el Use Case.

        Si no existe configuración, muestra valores por defecto.
        """
        try:
            # Ejecutar Use Case
            config = self.obtener_config_uc.execute()

            # Cargar datos en el formulario
            self.fecha_inicio_input.setDate(QDate(config.fecha_inicio_curso))
            self.fecha_fin_input.setDate(QDate(config.fecha_fin_curso))
            self.recreo1_manana_input.setTime(QTime(config.hora_recreo1_manana))
            self.recreo2_manana_input.setTime(QTime(config.hora_recreo2_manana))

            if config.hora_recreo1_tarde:
                self.recreo1_tarde_input.setTime(QTime(config.hora_recreo1_tarde))
            if config.hora_recreo2_tarde:
                self.recreo2_tarde_input.setTime(QTime(config.hora_recreo2_tarde))

            self.ajuste_tutores_input.setText(str(config.ajuste_tutores))
            self.ajuste_no_tutores_input.setText(str(config.ajuste_no_tutores))
            self.festivos_auto_input.setText("1" if config.activar_festivos_automaticos else "0")
            self.no_lectivos_input.setText(config.dias_no_lectivos_personalizados or "")

            # Cargar selector de algoritmo (nuevo en v3.0)
            algoritmo = getattr(config, 'algoritmo_asignacion', 'v2.9')
            index = self.algoritmo_combo.findData(algoritmo)
            if index >= 0:
                self.algoritmo_combo.setCurrentIndex(index)

            self.logger.info("Configuración cargada correctamente")

        except NotFoundError:
            # No hay configuración, usar valores por defecto
            self.logger.info("No hay configuración guardada, usando valores por defecto")
        except Exception as e:
            self.manejar_excepcion(e, "cargar configuración")

    def limpiar_formulario(self) -> None:
        """Limpia el formulario (no usado en configuración)."""
        # No aplica para configuración ya que solo hay un registro
        pass

    def _generar_recreos_config_json(self) -> str:
        """
        Genera el JSON de configuración de recreos basado en los valores del formulario.
        
        El número de zonas se obtiene automáticamente contando las zonas en la tabla Zona.

        Returns:
            str: JSON con la configuración de recreos, o cadena vacía si no hay recreos.
        """
        import json
        from datetime import time

        from models.models import Zona

        # Obtener número de zonas desde la tabla Zona
        num_zonas = self.session.query(Zona).count()

        # Si no hay zonas, usar 4 por defecto (compatibilidad)
        if num_zonas == 0:
            num_zonas = 4

        recreos = []

        # Recreo 1 Mañana
        hora_r1_manana = self.recreo1_manana_input.time().toPyTime()
        if hora_r1_manana != time(0, 0):  # Si no es 00:00 (valor por defecto)
            recreos.append({
                "id": 1,
                "etiqueta": "Recreo 1 Mañana",
                "turno": "mañana",
                "hora": hora_r1_manana.strftime("%H:%M"),
                "zonas": num_zonas
            })

        # Recreo 2 Mañana
        hora_r2_manana = self.recreo2_manana_input.time().toPyTime()
        if hora_r2_manana != time(0, 0):
            recreos.append({
                "id": 2,
                "etiqueta": "Recreo 2 Mañana",
                "turno": "mañana",
                "hora": hora_r2_manana.strftime("%H:%M"),
                "zonas": num_zonas
            })

        # Recreo 1 Tarde
        hora_r1_tarde = self.recreo1_tarde_input.time().toPyTime()
        if hora_r1_tarde != time(0, 0):
            recreos.append({
                "id": 3,
                "etiqueta": "Recreo 1 Tarde",
                "turno": "tarde",
                "hora": hora_r1_tarde.strftime("%H:%M"),
                "zonas": num_zonas
            })

        # Recreo 2 Tarde
        hora_r2_tarde = self.recreo2_tarde_input.time().toPyTime()
        if hora_r2_tarde != time(0, 0):
            recreos.append({
                "id": 4,
                "etiqueta": "Recreo 2 Tarde",
                "turno": "tarde",
                "hora": hora_r2_tarde.strftime("%H:%M"),
                "zonas": num_zonas
            })

        return json.dumps(recreos) if recreos else ""

    def validar_formulario(self) -> tuple[bool, str]:
        """
        Valida los datos del formulario.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        # Validar fechas
        fecha_inicio = self.fecha_inicio_input.date().toPyDate()
        fecha_fin = self.fecha_fin_input.date().toPyDate()

        if fecha_fin <= fecha_inicio:
            return False, "La fecha de fin debe ser posterior a la fecha de inicio"

        # Validar ajustes
        try:
            ajuste_tutores = float(self.ajuste_tutores_input.text() or 1.0)
            ajuste_no_tutores = float(self.ajuste_no_tutores_input.text() or 1.0)

            if ajuste_tutores <= 0 or ajuste_tutores > 2:
                return False, "El ajuste de tutores debe estar entre 0 y 2"

            if ajuste_no_tutores <= 0 or ajuste_no_tutores > 2:
                return False, "El ajuste de no tutores debe estar entre 0 y 2"

        except ValueError:
            return False, "Los ajustes deben ser números válidos"

        return True, ""

    def _guardar_email_interno(self) -> bool:
        """Guarda el email del usuario actual internamente.

        Returns:
            bool: True si se guardó correctamente o no hubo cambios, False si hay error de validación.
        """
        try:
            nuevo_email = self.email_input.text().strip()

            # Validar email
            if not nuevo_email:
                return False

            if "@" not in nuevo_email or "." not in nuevo_email:
                return False

            # Verificar si el email cambió
            user_data = self.user_auth.users.get(self.current_username, {})
            email_actual = user_data.get("email", "")

            if nuevo_email == email_actual:
                return False  # No hubo cambios

            # Actualizar email en users.json
            if self.current_username in self.user_auth.users:
                self.user_auth.users[self.current_username]["email"] = nuevo_email
                self.user_auth._save_users()
                self.logger.info(f"Email actualizado para usuario {self.current_username}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error al guardar email: {str(e)}")
            return False

    def guardar_email(self) -> None:
        """Guarda el email del usuario actual."""
        try:
            nuevo_email = self.email_input.text().strip()

            # Validar email
            if not nuevo_email:
                self.mostrar_advertencia(
                    "Email vacío",
                    "El email no puede estar vacío"
                )
                return

            if "@" not in nuevo_email or "." not in nuevo_email:
                self.mostrar_advertencia(
                    "Email inválido",
                    "Por favor introduce un email válido (debe contener @ y .)"
                )
                return

            # Actualizar email en users.json
            if self.current_username in self.user_auth.users:
                self.user_auth.users[self.current_username]["email"] = nuevo_email
                self.user_auth._save_users()

                self.mostrar_exito(
                    "Email Actualizado",
                    f"Tu email ha sido actualizado a: {nuevo_email}"
                )
                self.logger.info(f"Email actualizado para usuario {self.current_username}")
            else:
                self.mostrar_advertencia(
                    "Error",
                    "No se encontró el usuario actual"
                )

        except Exception as e:
            self.manejar_excepcion(e, "actualizar email")

    def cambiar_contrasena(self) -> None:
        """Abre diálogo para cambiar la contraseña."""
        from presentation.forms.change_password_dialog import ChangePasswordDialog

        dialog = ChangePasswordDialog(self.current_username, self)
        dialog.exec()

    def _mostrar_advertencia_smtp_global(self) -> bool:
        """Muestra un modal de advertencia sobre la naturaleza global de la configuración SMTP.

        Returns:
            bool: True si el usuario acepta los riesgos, False si cancela.
        """
        from PyQt6.QtWidgets import QMessageBox

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("⚠️ Configuración SMTP Global")
        msg.setText(
            "<h3>⚠️ ADVERTENCIA: Configuración SMTP Global</h3>"
        )
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
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        # Personalizar textos y estilos de los botones
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
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
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
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """)

        resultado = msg.exec()
        return resultado == QMessageBox.StandardButton.Yes

    def toggle_smtp_editable(self) -> None:
        """Alterna entre bloquear y desbloquear los campos SMTP."""
        # Verificar el estado actual
        is_readonly = self.smtp_server_input.isReadOnly()

        # Si se va a habilitar la edición, mostrar advertencia
        if is_readonly:
            if not self._mostrar_advertencia_smtp_global():
                # Usuario canceló, no hacer nada
                return

        # Alternar estado
        new_state = not is_readonly

        # Aplicar a todos los campos
        self.smtp_server_input.setReadOnly(new_state)
        self.smtp_port_input.setReadOnly(new_state)
        self.smtp_user_input.setReadOnly(new_state)
        self.smtp_password_input.setReadOnly(new_state)

        # Cambiar estilos según el estado
        if new_state:  # Bloqueado
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
            self.modify_smtp_btn.setText("🔓 Modificar Configuración SMTP")
        else:  # Editable
            self.smtp_server_input.setStyleSheet(styles.STYLE_INPUT)
            self.smtp_port_input.setStyleSheet(styles.STYLE_INPUT)
            self.smtp_user_input.setStyleSheet(styles.STYLE_INPUT)
            self.smtp_password_input.setStyleSheet(styles.STYLE_INPUT)
            self.modify_smtp_btn.setText("🔒 Bloquear Configuración SMTP")

            # No limpiar la contraseña, mantener ••••••••
            # Si el usuario quiere cambiarla, que la borre manualmente


    def cargar_smtp(self) -> None:
        """Carga la configuración SMTP desde el archivo .env."""
        import os

        from dotenv import load_dotenv

        # Cargar variables de entorno
        load_dotenv()

        # Cargar valores en los campos
        self.smtp_server_input.setText(os.getenv("SMTP_SERVER", ""))
        self.smtp_port_input.setText(os.getenv("SMTP_PORT", "587"))
        self.smtp_user_input.setText(os.getenv("SMTP_USER", ""))

        # Solo cargar contraseña si existe (por seguridad no la mostramos completa)
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        if smtp_password:
            self.smtp_password_input.setText("••••••••")
            self.smtp_password_input.setPlaceholderText("Contraseña configurada")

    def guardar_smtp(self) -> bool:
        """Guarda la configuración SMTP en el archivo .env.

        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        import os

        # Mostrar advertencia antes de guardar
        if not self._mostrar_advertencia_smtp_global():
            # Usuario canceló, no guardar
            self.logger.info("Usuario canceló la modificación de configuración SMTP")
            return False

        try:
            smtp_server = self.smtp_server_input.text().strip()
            smtp_port = self.smtp_port_input.text().strip()
            smtp_user = self.smtp_user_input.text().strip()
            smtp_password = self.smtp_password_input.text().strip()

            # Si la contraseña son asteriscos, no la cambiamos
            if smtp_password and smtp_password != "••••••••":
                password_to_save = smtp_password
            else:
                # Mantener la contraseña actual si no se cambió
                from dotenv import load_dotenv
                load_dotenv()
                password_to_save = os.getenv("SMTP_PASSWORD", "")

            # Solo guardar si hay datos completos
            if not smtp_server or not smtp_port or not smtp_user or not password_to_save:
                # No hay configuración SMTP completa, no guardamos
                return False

            # Leer el archivo .env actual
            env_path = ".env"
            env_lines = []

            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()

            # Actualizar o agregar variables SMTP
            smtp_vars = {
                "SMTP_SERVER": smtp_server,
                "SMTP_PORT": smtp_port,
                "SMTP_USER": smtp_user,
                "SMTP_PASSWORD": password_to_save,
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
            with open(env_path, 'w') as f:
                f.writelines(env_lines)

            self.logger.info("Configuración SMTP guardada correctamente")

            # Recargar para mostrar la contraseña enmascarada
            self.cargar_smtp()

            return True

        except Exception as e:
            self.logger.error(f"Error al guardar SMTP: {str(e)}")
            return False

    def probar_smtp(self) -> None:
        """Prueba la conexión SMTP enviando un email de prueba al usuario actual."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        from PyQt6.QtWidgets import QMessageBox

        try:
            smtp_server = self.smtp_server_input.text().strip()
            smtp_port = self.smtp_port_input.text().strip()
            smtp_user = self.smtp_user_input.text().strip()
            smtp_password = self.smtp_password_input.text().strip()

            # Validaciones básicas
            if not smtp_server or not smtp_port or not smtp_user:
                self.mostrar_advertencia(
                    "Campos incompletos",
                    "Completa todos los campos antes de probar la conexión"
                )
                return

            # Si la contraseña son asteriscos, cargar la real
            if smtp_password == "••••••••":
                import os

                from dotenv import load_dotenv
                load_dotenv()
                smtp_password = os.getenv("SMTP_PASSWORD", "")

            if not smtp_password:
                self.mostrar_advertencia(
                    "Contraseña vacía",
                    "La contraseña SMTP es necesaria para probar la conexión"
                )
                return

            # Obtener email del usuario actual para enviar la prueba
            user_data = self.user_auth.users.get(self.current_username, {})
            email_destino = user_data.get("email", "")

            if not email_destino or "@" not in email_destino:
                email_destino = self.email_input.text().strip()

            if not email_destino or "@" not in email_destino:
                self.mostrar_advertencia(
                    "Email no configurado",
                    "Debes tener un email configurado en tu perfil para recibir el email de prueba."
                )
                return

            # Intentar conectar y enviar email de prueba
            self.logger.info(f"Probando conexión SMTP a {smtp_server}:{smtp_port}")

            with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)

                # Crear email de prueba
                msg = MIMEMultipart("alternative")
                msg["Subject"] = "✅ Prueba de Configuración SMTP - Guardias de Patio"
                msg["From"] = smtp_user
                msg["To"] = email_destino

                # Contenido del email
                texto = f"""
                Hola {self.current_username},

                Este es un email de prueba para verificar que la configuración SMTP está funcionando correctamente.

                Servidor: {smtp_server}:{smtp_port}
                Usuario: {smtp_user}

                Si estás recibiendo este email, significa que el sistema puede enviar emails de recuperación de contraseña sin problemas.

                ---
                Sistema de Gestión de Guardias de Patio
                """

                html = f"""
                <html>
                  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                      <h2 style="color: #059669; margin-bottom: 20px;">✅ Prueba de Configuración SMTP</h2>

                      <p>Hola <strong>{self.current_username}</strong>,</p>

                      <p>Este es un email de prueba para verificar que la configuración SMTP está funcionando correctamente.</p>

                      <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Servidor:</strong> {smtp_server}:{smtp_port}</p>
                        <p style="margin: 5px 0;"><strong>Usuario:</strong> {smtp_user}</p>
                      </div>

                      <p style="color: #059669; font-weight: bold;">
                        Si estás recibiendo este email, significa que el sistema puede enviar emails de recuperación de contraseña sin problemas.
                      </p>

                      <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                      <p style="font-size: 12px; color: #6b7280;">
                        Sistema de Gestión de Guardias de Patio
                      </p>
                    </div>
                  </body>
                </html>
                """

                part1 = MIMEText(texto, "plain")
                part2 = MIMEText(html, "html")
                msg.attach(part1)
                msg.attach(part2)

                # Enviar email
                server.send_message(msg)

            # Éxito
            success_msg = QMessageBox(self)
            success_msg.setIcon(QMessageBox.Icon.Information)
            success_msg.setWindowTitle("✅ Email de Prueba Enviado")
            success_msg.setTextFormat(Qt.TextFormat.RichText)
            success_msg.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint
            )
            success_msg.setText(
                f"La conexión SMTP se estableció correctamente y se envió un email de prueba.<br><br>"
                f"<b>Servidor:</b> <span style='color: #007ACC; font-style: italic;'>{smtp_server}:{smtp_port}</span><br>"
                f"<b>Usuario:</b> <span style='color: #007ACC; font-style: italic;'>{smtp_user}</span><br>"
                f"<b>Email enviado a:</b> <span style='color: #007ACC; font-style: italic;'>{email_destino}</span><br><br>"
                "Revisa tu bandeja de entrada (y spam) para verificar que llegó el email."
            )

            # Añadir botón OK con estilo visible
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
                QPushButton:hover {
                    background-color: #047857;
                }
                QPushButton:pressed {
                    background-color: #065f46;
                }
            """)

            success_msg.exec()
            self.logger.info(f"Prueba de conexión SMTP exitosa - Email enviado a {email_destino}")

        except smtplib.SMTPAuthenticationError:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("❌ Error de Autenticación")
            error_msg.setText(
                "No se pudo autenticar con el servidor SMTP.\n\n"
                "Verifica tu usuario y contraseña.\n"
                "Para Gmail, usa una App Password."
            )
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
                QPushButton:hover {
                    background-color: #b91c1c;
                }
                QPushButton:pressed {
                    background-color: #991b1b;
                }
            """)
            error_msg.exec()
            self.logger.error("Error de autenticación SMTP")

        except Exception as e:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("❌ Error de Conexión")
            error_msg.setText(
                f"No se pudo conectar al servidor SMTP:\n\n{str(e)}\n\n"
                "Verifica el servidor, puerto y credenciales."
            )
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
                QPushButton:hover {
                    background-color: #b91c1c;
                }
                QPushButton:pressed {
                    background-color: #991b1b;
                }
            """)
            error_msg.exec()
            self.logger.error(f"Error al probar SMTP: {str(e)}")

    # =================================================================================
    # MÉTODOS SFTP
    # =================================================================================

    def toggle_sftp_editable(self) -> None:
        """
        Alterna entre modo solo lectura y editable para los campos SFTP.
        Muestra una advertencia de seguridad al desbloquear.
        """
        is_readonly = self.sftp_host_input.isReadOnly()

        if is_readonly:
            # Intentar desbloquear - mostrar advertencia
            if not self._mostrar_advertencia_sftp_global():
                # Usuario canceló, no desbloquear
                return

        # Alternar estado de todos los campos SFTP
        new_state = not is_readonly
        self.sftp_host_input.setReadOnly(new_state)
        self.sftp_port_input.setReadOnly(new_state)
        self.sftp_basedir_input.setReadOnly(new_state)
        self.sftp_user_input.setReadOnly(new_state)
        self.sftp_password_input.setReadOnly(new_state)

        # Actualizar estilos según el estado
        if new_state:  # Bloqueado (readonly)
            readonly_style = """
                QLineEdit {
                    background-color: #e5e7eb;
                    color: #4b5563;
                    border: 1px solid #d1d5db;
                    padding: 5px;
                }
            """
            self.sftp_host_input.setStyleSheet(readonly_style)
            self.sftp_port_input.setStyleSheet(readonly_style)
            self.sftp_basedir_input.setStyleSheet(readonly_style)
            self.sftp_user_input.setStyleSheet(readonly_style)
            self.sftp_password_input.setStyleSheet(readonly_style)
            self.modify_sftp_btn.setText("🔓 Modificar Configuración SFTP")
        else:  # Editable
            self.sftp_host_input.setStyleSheet(styles.STYLE_INPUT)
            self.sftp_port_input.setStyleSheet(styles.STYLE_INPUT)
            self.sftp_basedir_input.setStyleSheet(styles.STYLE_INPUT)
            self.sftp_user_input.setStyleSheet(styles.STYLE_INPUT)
            self.sftp_password_input.setStyleSheet(styles.STYLE_INPUT)
            self.modify_sftp_btn.setText("🔒 Bloquear Configuración SFTP")

            # No limpiar la contraseña, mantener ••••••••
            # Si el usuario quiere cambiarla, que la borre manualmente

    def _mostrar_advertencia_sftp_global(self) -> bool:
        """
        Muestra una advertencia sobre la configuración SFTP global.

        Returns:
            bool: True si el usuario acepta continuar, False si cancela.
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QMessageBox

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("⚠️ Configuración SFTP Global")
        msg.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        msg.setText(
            "<h3>⚠️ Advertencia: Configuración SFTP Global</h3>"
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
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        # Personalizar botones con estilos
        yes_button = msg.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Sí, modificar configuración SFTP")
        yes_button.setStyleSheet("""
            QPushButton {
                min-width: 180px;
                min-height: 35px;
                padding: 5px 15px;
                font-size: 13px;
                background-color: #059669;
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
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """)

        result = msg.exec()
        return result == QMessageBox.StandardButton.Yes

    def cargar_sftp(self) -> None:
        """Carga la configuración SFTP desde el archivo .env."""
        import os

        from dotenv import load_dotenv

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
            self.sftp_password_input.setText("••••••••")
            self.sftp_password_input.setPlaceholderText("Contraseña configurada")

    def guardar_sftp(self) -> bool:
        """
        Guarda la configuración SFTP en el archivo .env.

        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        import os

        # Mostrar advertencia antes de guardar
        if not self._mostrar_advertencia_sftp_global():
            # Usuario canceló, no guardar
            self.logger.info(
                "Usuario canceló la modificación de configuración SFTP"
            )
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
            else:
                # Mantener la contraseña actual si no se cambió
                from dotenv import load_dotenv

                load_dotenv()
                password_to_save = os.getenv("SFTP_PASSWORD", "")

            # Solo guardar si hay datos completos
            if not sftp_host or not sftp_port or not sftp_user or not password_to_save:
                # No hay configuración SFTP completa, no guardamos
                return False

            # Leer el archivo .env actual
            env_path = ".env"
            env_lines = []

            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_lines = f.readlines()

            # Actualizar o agregar variables SFTP
            sftp_vars = {
                "SFTP_HOST": sftp_host,
                "SFTP_PORT": sftp_port,
                "SFTP_BASE_DIR": sftp_basedir,
                "SFTP_USERNAME": sftp_user,
                "SFTP_PASSWORD": password_to_save,
            }

            updated_vars = set()
            for i, line in enumerate(env_lines):
                for var_name, var_value in sftp_vars.items():
                    if line.startswith(f"{var_name}="):
                        env_lines[i] = f"{var_name}={var_value}\n"
                        updated_vars.add(var_name)

            # Agregar variables que no existían
            for var_name, var_value in sftp_vars.items():
                if var_name not in updated_vars:
                    env_lines.append(f"{var_name}={var_value}\n")

            # Guardar archivo .env
            with open(env_path, "w") as f:
                f.writelines(env_lines)

            self.logger.info("Configuración SFTP guardada correctamente")

            # Recargar para mostrar la contraseña enmascarada
            self.cargar_sftp()

            return True

        except Exception as e:
            self.logger.error(f"Error al guardar SFTP: {str(e)}")
            return False

    def probar_sftp(self) -> None:
        """
        Prueba la conexión SFTP intentando conectar al servidor
        y listar el directorio base.
        """
        from PyQt6.QtWidgets import QMessageBox

        try:
            import paramiko

            sftp_host = self.sftp_host_input.text().strip()
            sftp_port = self.sftp_port_input.text().strip()
            sftp_basedir = self.sftp_basedir_input.text().strip()
            sftp_user = self.sftp_user_input.text().strip()
            sftp_password = self.sftp_password_input.text().strip()

            # Validaciones básicas
            if not sftp_host or not sftp_port or not sftp_user:
                self.mostrar_advertencia(
                    "Campos incompletos",
                    "Completa host, puerto y usuario antes de probar la conexión",
                )
                return

            # Si la contraseña son asteriscos, cargar la real
            if sftp_password == "••••••••":
                import os

                from dotenv import load_dotenv

                load_dotenv()
                sftp_password = os.getenv("SFTP_PASSWORD", "")

            if not sftp_password:
                self.mostrar_advertencia(
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
            except Exception:
                # Si no existe el directorio, intentar crearlo
                sftp.mkdir(sftp_basedir)
                file_count = 0

            sftp.close()
            transport.close()

            # Mostrar mensaje de éxito
            success_msg = QMessageBox(self)
            success_msg.setIcon(QMessageBox.Icon.Information)
            success_msg.setWindowTitle("✅ Conexión SFTP Exitosa")
            success_msg.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            success_msg.setText(
                f"La conexión SFTP se estableció correctamente.<br><br>"
                f"<b>Servidor:</b> <span style='color: #007ACC; "
                f"font-style: italic;'>{sftp_host}:{sftp_port}</span><br>"
                f"<b>Usuario:</b> <span style='color: #007ACC; "
                f"font-style: italic;'>{sftp_user}</span><br>"
                f"<b>Directorio:</b> <span style='color: #007ACC; "
                f"font-style: italic;'>{sftp_basedir}</span><br>"
                f"<b>Archivos encontrados:</b> <span style='color: #059669; "
                f"font-weight: bold;'>{file_count}</span><br><br>"
                "El servidor está listo para sincronizar copias de seguridad."
            )

            # Añadir botón OK con estilo visible
            success_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            ok_button = success_msg.button(QMessageBox.StandardButton.Ok)
            ok_button.setText("Entendido")
            ok_button.setStyleSheet(
                """
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
                QPushButton:hover {
                    background-color: #047857;
                }
                QPushButton:pressed {
                    background-color: #065f46;
                }
            """
            )

            success_msg.exec()
            self.logger.info(
                f"Prueba de conexión SFTP exitosa - {file_count} archivos en {sftp_basedir}"
            )

        except ImportError:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("❌ Dependencia Faltante")
            error_msg.setText(
                "La librería 'paramiko' no está instalada.\n\n"
                "Instálala con: pip install paramiko"
            )
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
            self.logger.error("Librería paramiko no instalada")

        except paramiko.AuthenticationException:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("❌ Error de Autenticación")
            error_msg.setText(
                "No se pudo autenticar con el servidor SFTP.\n\n"
                "Verifica tu usuario y contraseña."
            )
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
            self.logger.error("Error de autenticación SFTP")

        except Exception as e:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("❌ Error de Conexión")
            error_msg.setText(
                f"No se pudo conectar al servidor SFTP:\n\n{str(e)}\n\n"
                "Verifica el servidor, puerto y credenciales."
            )
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
            self.logger.error(f"Error al probar SFTP: {str(e)}")
