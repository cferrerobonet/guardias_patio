"""
Widget de configuración de festivos y días no lectivos.

Combina:
- Activación de festivos automáticos (1/0)
- Días no lectivos personalizados (lista de fechas)
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QLabel, QLineEdit, QVBoxLayout

import ui_styles as styles


class FestivosWidget(QGroupBox):
    """
    Widget para gestionar festivos y días no lectivos.

    Combina en un solo widget:
    - Activación de festivos automáticos nacionales
    - Días no lectivos personalizados del centro

    Signals:
        config_changed: Emitido cuando cambia cualquier valor
    """

    # Señales
    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa el widget de festivos.

        Args:
            parent: Widget padre opcional
        """
        super().__init__("🎉 Festivos y Días No Lectivos", parent)
        self.setStyleSheet(styles.STYLE_GROUPBOX)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Crea la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        # ===== Festivos automáticos =====
        label_auto = QLabel("Aplicar festivos automáticos:")
        label_auto.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_auto)

        self.festivos_auto_input = QLineEdit()
        self.festivos_auto_input.setPlaceholderText("1 (sí) / 0 (no)")
        self.festivos_auto_input.setStyleSheet(styles.STYLE_INPUT)
        self.festivos_auto_input.setToolTip(
            "Activar festivos nacionales automáticos:\n"
            "1 = Aplicar festivos oficiales de España\n"
            "0 = No aplicar festivos automáticos"
        )
        self.festivos_auto_input.textChanged.connect(self.config_changed.emit)
        layout.addWidget(self.festivos_auto_input)

        # ===== Días no lectivos personalizados =====
        label_custom = QLabel("Días no lectivos (YYYY-MM-DD):")
        label_custom.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_custom)

        self.no_lectivos_input = QLineEdit()
        self.no_lectivos_input.setPlaceholderText("2025-10-09, 2025-10-12")
        self.no_lectivos_input.setStyleSheet(styles.STYLE_INPUT)
        self.no_lectivos_input.setToolTip(
            "Días no lectivos personalizados del centro\n"
            "Formato: YYYY-MM-DD separados por comas\n"
            "Ejemplo: 2025-10-09, 2025-10-12, 2025-12-23"
        )
        self.no_lectivos_input.textChanged.connect(self.config_changed.emit)
        layout.addWidget(self.no_lectivos_input)

        self.setLayout(layout)

    # ===== API PÚBLICA: GET/SET =====

    def get_festivos_config(self) -> dict:
        """
        Obtiene la configuración de festivos.

        Returns:
            dict: Diccionario con claves:
                - activar_automaticos: bool (True si se activan festivos)
                - dias_no_lectivos: str (fechas separadas por comas)
        """
        auto_text = (self.festivos_auto_input.text() or "1").strip()
        activar = auto_text in ("1", "true", "True")

        return {
            "activar_automaticos": activar,
            "dias_no_lectivos": (self.no_lectivos_input.text() or "").strip(),
        }

    def set_festivos_config(
        self, activar_automaticos: bool = True, dias_no_lectivos: str = ""
    ) -> None:
        """
        Establece la configuración de festivos.

        Args:
            activar_automaticos: Si se activan festivos automáticos
            dias_no_lectivos: Fechas separadas por comas (YYYY-MM-DD)
        """
        self.festivos_auto_input.setText("1" if activar_automaticos else "0")
        self.no_lectivos_input.setText(dias_no_lectivos or "")

    def validar(self) -> tuple[bool, str]:
        """
        Valida la configuración de festivos.

        Returns:
            tuple: (es_valido, mensaje_error)
                - es_valido: True si todos los valores son válidos
                - mensaje_error: Descripción del error si no es válido
        """
        # Validar festivos automáticos
        auto_text = (self.festivos_auto_input.text() or "1").strip()
        if auto_text not in ("0", "1", "true", "True", "false", "False"):
            return False, "Festivos automáticos debe ser 1 (sí) o 0 (no)"

        # Validar formato de días no lectivos
        dias_text = (self.no_lectivos_input.text() or "").strip()
        if dias_text:
            import re

            # Formato: YYYY-MM-DD separados por comas
            pattern = r"^\d{4}-\d{2}-\d{2}(\s*,\s*\d{4}-\d{2}-\d{2})*$"
            if not re.match(pattern, dias_text):
                return False, (
                    "Formato de días no lectivos incorrecto. Use: YYYY-MM-DD separados por comas"
                )

            # Validar que las fechas sean válidas
            from datetime import datetime

            fechas = [f.strip() for f in dias_text.split(",")]
            for fecha in fechas:
                try:
                    datetime.strptime(fecha, "%Y-%m-%d")
                except ValueError:
                    return False, f"Fecha inválida: {fecha}"

        return True, ""
