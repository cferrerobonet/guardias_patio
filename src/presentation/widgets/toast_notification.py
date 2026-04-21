from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ToastNotification(QWidget):
    """Notificación flotante no intrusiva en esquina inferior derecha."""

    _COLORES = {
        "success": ("#1E7E34", "#D1FAE5", "#166534"),
        "error": ("#DC3545", "#FEE2E2", "#991B1B"),
        "info": ("#007ACC", "#E6F2FA", "#1E40AF"),
        "warning": ("#856404", "#FFF3CD", "#92400E"),
    }

    def __init__(self, parent: QWidget, message: str, tipo: str = "success", duracion_ms: int = 2500):
        super().__init__(parent)
        from PyQt6.QtCore import Qt

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

        self.adjustSize()
        self._posicionar(parent)
        self.show()
        self.raise_()

        QTimer.singleShot(duracion_ms, self.close)

    def _posicionar(self, parent: QWidget):
        try:
            parent_rect = parent.rect()
            global_pos = parent.mapToGlobal(parent_rect.bottomRight())
            x = global_pos.x() - self.width() - 20
            y = global_pos.y() - self.height() - 20
            self.move(x, y)
        except Exception:
            pass
