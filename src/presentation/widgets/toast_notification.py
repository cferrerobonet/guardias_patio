from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ToastNotification(QWidget):
    """Notificación flotante no intrusiva en esquina inferior derecha."""

    _COLORES = {
        "success": ("#1E7E34", "#D1FAE5", "#166534"),
        "error": ("#DC3545", "#FEE2E2", "#991B1B"),
        "info": ("#0E5FA8", "#E6F2FA", "#1E40AF"),
        "warning": ("#856404", "#FFF3CD", "#92400E"),
    }

    #: Cuánto se queda cada tipo en pantalla. Un fallo no puede desaparecer solo
    #: a los dos segundos y medio: quien mira a otro lado se queda sin enterarse
    #: de que algo salió mal (UXA-003).
    DURACIONES = {
        "success": 2500,
        "info": 3000,
        "warning": 8000,
        "error": 0,  # 0 = hasta que se pulse
    }

    def __init__(
        self,
        parent: QWidget,
        message: str,
        tipo: str = "success",
        duracion_ms: int | None = None,
    ):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        fg, bg, border = self._COLORES.get(tipo, self._COLORES["info"])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(message)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        label.setWordWrap(False)
        layout.addWidget(label)

        # Un lector de pantalla no ve una ventana flotante sin nombre: sin esto,
        # el aviso pasa completamente desapercibido (UXA-003).
        etiquetas = {
            "success": "Aviso",
            "info": "Información",
            "warning": "Advertencia",
            "error": "Error",
        }
        self.setAccessibleName(f"{etiquetas.get(tipo, 'Aviso')}: {message}")
        label.setAccessibleName(self.accessibleName())
        self.setToolTip(message)

        self.adjustSize()
        self._posicionar(parent)
        self.show()
        self.raise_()

        from utils.ui_helpers import announce

        announce(f"{etiquetas.get(tipo, 'Aviso')}. {message}", label)

        if duracion_ms is None:
            duracion_ms = self.DURACIONES.get(tipo, 2500)
        if duracion_ms > 0:
            QTimer.singleShot(duracion_ms, self.close)
        else:
            # Los errores esperan: se cierran al pulsarlos.
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setText(f"{message}   ✕")
            self.adjustSize()
            self._posicionar(parent)

    def mousePressEvent(self, event):
        """Pulsar el aviso lo cierra, sobre todo los que no caducan solos."""
        self.close()
        super().mousePressEvent(event)

    def _posicionar(self, parent: QWidget):
        try:
            parent_rect = parent.rect()
            global_pos = parent.mapToGlobal(parent_rect.bottomRight())
            x = global_pos.x() - self.width() - 20
            y = global_pos.y() - self.height() - 20
            self.move(x, y)
        except Exception:
            pass
