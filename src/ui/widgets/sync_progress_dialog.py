"""
Diálogo de progreso de sincronización.

Muestra el progreso de la sincronización al cerrar la aplicación,
informando al usuario de cada paso del proceso.
"""

import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)


class SyncProgressDialog(QDialog):
    """
    Diálogo modal que muestra el progreso de sincronización.

    Muestra cada paso del proceso:
    1. Exportando datos de la base de datos
    2. Conectando al servidor SFTP
    3. Subiendo archivo JSON
    4. Finalizando
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sincronizando cambios...")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        self._setup_ui()
        self._current_step = 0
        self._total_steps = 4

    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Título
        title_label = QLabel("Guardando cambios en la nube")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Mensaje de estado
        self.status_label = QLabel("Preparando sincronización...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Detalles (oculto por defecto)
        self.details_label = QLabel("")
        self.details_label.setStyleSheet("color: #666; font-size: 10px;")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)

        # Botón cerrar (oculto hasta que termine)
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setVisible(False)
        layout.addWidget(self.close_button)

    def update_progress(self, step: int, message: str, details: str = ""):
        """
        Actualiza el progreso de la sincronización.

        Args:
            step: Número de paso actual (1-4)
            message: Mensaje principal a mostrar
            details: Detalles adicionales (opcional)
        """
        self._current_step = step
        progress_percent = int((step / self._total_steps) * 100)

        self.status_label.setText(message)
        self.progress_bar.setValue(progress_percent)

        if details:
            self.details_label.setText(details)

        # Forzar actualización de la UI
        self.repaint()
        QTimer.singleShot(0, lambda: None)  # Procesar eventos pendientes

        logger.info(f"Sync progress: {message} ({progress_percent}%)")

    def set_step_exporting(self, total_records: int):
        """Paso 1: Exportando datos."""
        self.update_progress(
            1,
            "📦 Exportando datos de la base de datos",
            f"Procesando {total_records} registros..."
        )

    def set_step_connecting(self):
        """Paso 2: Conectando al servidor."""
        self.update_progress(
            2,
            "🔗 Conectando al servidor SFTP",
            "Estableciendo conexión segura..."
        )

    def set_step_uploading(self, file_size_kb: int):
        """Paso 3: Subiendo archivo."""
        self.update_progress(
            3,
            "⬆️ Subiendo archivo a la nube",
            f"Enviando {file_size_kb} KB al servidor..."
        )

    def set_step_complete(self, success: bool = True):
        """Paso 4: Finalizado."""
        if success:
            self.update_progress(
                4,
                "✅ Sincronización completada con éxito",
                "Todos los cambios se guardaron en la nube"
            )
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #4CAF50;
                }
            """)
        else:
            self.update_progress(
                4,
                "⚠️ Sincronización completada con advertencias",
                "Algunos cambios pueden no haberse guardado"
            )
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #FF9800;
                }
            """)

        # Mostrar botón de cerrar después de 2 segundos
        QTimer.singleShot(2000, self._show_close_button)

    def set_step_error(self, error_message: str):
        """Error en la sincronización."""
        self.update_progress(
            self._current_step,
            "❌ Error en la sincronización",
            error_message
        )
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #F44336;
            }
        """)
        self._show_close_button()

    def _show_close_button(self):
        """Muestra el botón de cerrar."""
        self.close_button.setVisible(True)
        self.close_button.setFocus()
