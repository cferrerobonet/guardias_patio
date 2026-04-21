"""
Formulario de Conectividad - Configuración SMTP y SFTP.

Gestiona las conexiones externas del sistema:
- Servidor SMTP para envío de correos
- Servidor SFTP para sincronización en la nube
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from presentation.forms.base_form import BaseForm
from presentation.forms.config_widgets import SFTPConfigWidget, SMTPConfigWidget


class ConectividadForm(BaseForm):
    """
    Formulario para gestionar la conectividad del sistema.

    Permite configurar:
    - Servidor SMTP (correo electrónico)
    - Servidor SFTP (sincronización de archivos)
    """

    def __init__(self, session, parent=None):
        """
        Inicializa el formulario de conectividad.

        Args:
            session: Sesión de SQLAlchemy
            parent: Widget padre
        """
        super().__init__(session, parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Conectividad")

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Widget contenedor
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Título principal
        titulo = QLabel("🌐 CONECTIVIDAD")
        titulo.setObjectName("titleMain")
        content_layout.addWidget(titulo)

        # Descripción
        descripcion = QLabel(
            "Configura las conexiones externas del sistema para el envío de correos "
            "y la sincronización de datos en la nube."
        )
        descripcion.setWordWrap(True)
        descripcion.setObjectName("formDescription")
        content_layout.addWidget(descripcion)

        # Layout de 2 columnas para SMTP y SFTP
        conectividad_layout = QHBoxLayout()
        conectividad_layout.setSpacing(15)

        # Widget SMTP
        self.smtp_widget = SMTPConfigWidget(self)
        conectividad_layout.addWidget(self.smtp_widget)

        # Widget SFTP
        self.sftp_widget = SFTPConfigWidget(self)
        conectividad_layout.addWidget(self.sftp_widget)

        content_layout.addLayout(conectividad_layout)

        # Espacio flexible
        content_layout.addStretch()

        # Establecer layouts
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def refrescar(self):
        """Refresca los datos del formulario."""
        # Los widgets SMTP y SFTP gestionan su propia recarga
        pass
