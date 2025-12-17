"""
Diálogo para informar al usuario que la sesión está bloqueada.
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from utils.icons import icon_for_button

logger = logging.getLogger(__name__)


class SessionLockedDialog(QDialog):
    """
    Diálogo que informa al usuario que su sesión está bloqueada
    por otro dispositivo/ubicación.
    """

    def __init__(self, lock_info: dict, parent=None):
        super().__init__(parent)
        self.lock_info = lock_info
        self.setWindowTitle("Sesión en uso")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Icono y título
        title_label = QLabel("Sesión Bloqueada")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Mensaje principal
        main_message = QLabel(
            "Este usuario ya tiene una sesión activa en otro dispositivo o ubicación."
        )
        main_message.setWordWrap(True)
        main_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_message.setStyleSheet("font-size: 12px; color: #333;")
        layout.addWidget(main_message)

        # Información de la sesión activa
        info_container = QLabel()
        info_container.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                font-family: monospace;
            }
        """)
        info_container.setWordWrap(True)

        info_text = (
            f"<b>Usuario:</b> {self.lock_info.get('user_id', 'Desconocido')}<br>"
            f"<b>Equipo:</b> {self.lock_info.get('hostname', 'Desconocido')}<br>"
            f"<b>Dirección IP:</b> {self.lock_info.get('ip_address', 'Desconocido')}<br>"
            f"<b>Sesión iniciada:</b> {self._format_datetime(self.lock_info.get('started_at'))}<br>"
            f"<b>Última actividad:</b> "
            f"{self._format_datetime(self.lock_info.get('last_heartbeat'))}"
        )
        info_container.setText(info_text)
        layout.addWidget(info_container)

        # Mensaje explicativo
        explanation = QLabel(
            "Para evitar conflictos y pérdida de datos, solo se permite una sesión "
            "activa por usuario.\n\n"
            "Por favor, cierra la sesión en el otro dispositivo o espera a que "
            "expire automáticamente (90 segundos de inactividad)."
        )
        explanation.setWordWrap(True)
        explanation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        explanation.setStyleSheet("font-size: 11px; color: #666; margin-top: 10px;")
        layout.addWidget(explanation)

        # Botones
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        retry_button = QPushButton("Reintentar")
        retry_button.setIcon(icon_for_button("refresh"))
        retry_button.clicked.connect(self.accept)
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(retry_button)

        cancel_button = QPushButton("Cancelar")
        cancel_button.setIcon(icon_for_button("close"))
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(cancel_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _format_datetime(self, iso_string: str) -> str:
        """Formatea un datetime ISO a formato legible."""
        if not iso_string:
            return "Desconocido"

        try:
            from datetime import datetime

            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return iso_string
