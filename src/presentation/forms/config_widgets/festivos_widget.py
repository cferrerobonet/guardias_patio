"""
Widget de configuración de festivos y días no lectivos.

Combina:
- Activación de festivos automáticos (1/0)
- Días no lectivos personalizados (lista de fechas)
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QGroupBox, QLabel, QLineEdit, QVBoxLayout

from presentation.theme import legacy_styles as styles


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
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Crea la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(6, 6, 6, 6)

        # ===== Festivos automáticos =====
        # Una casilla: antes era un campo de texto que pedía «1» o «0» (2026-10-03).
        self.festivos_auto_input = QCheckBox("Aplicar los festivos nacionales automáticamente")
        self.festivos_auto_input.setChecked(True)
        self.festivos_auto_input.setToolTip(
            "Marca los festivos oficiales de España como días no lectivos"
        )
        self.festivos_auto_input.toggled.connect(self.config_changed.emit)
        layout.addWidget(self.festivos_auto_input)

        # ===== Días no lectivos personalizados =====
        label_custom = QLabel("Días no lectivos (YYYY-MM-DD):")
        label_custom.setStyleSheet(
            styles.STYLE_LABEL_FIELD + "font-size: 12px; margin-bottom: 1px;"
        )
        layout.addWidget(label_custom)

        self.no_lectivos_input = QLineEdit()
        self.no_lectivos_input.setPlaceholderText("2025-10-09, 2025-10-12")
        self.no_lectivos_input.setStyleSheet(styles.STYLE_INPUT + "padding: 3px;")
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
        return {
            "activar_automaticos": self.festivos_auto_input.isChecked(),
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
        self.festivos_auto_input.setChecked(bool(activar_automaticos))
        self.no_lectivos_input.setText(dias_no_lectivos or "")

    def validar(self) -> tuple[bool, str]:
        """
        Valida la configuración de festivos.

        Returns:
            tuple: (es_valido, mensaje_error)
                - es_valido: True si todos los valores son válidos
                - mensaje_error: Descripción del error si no es válido
        """
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
            # Una fecha imposible (p. ej. día y mes cambiados) pasaba el patrón y
            # el reparto la ignoraba sin decir nada (2026-10-03).
            from datetime import date

            for texto in (t.strip() for t in dias_text.split(",")):
                try:
                    date.fromisoformat(texto)
                except ValueError:
                    return False, f"El día no lectivo {texto} no existe. Revisa día y mes."

            # Validar que las fechas sean válidas
            from datetime import datetime

            fechas = [f.strip() for f in dias_text.split(",")]
            for fecha in fechas:
                try:
                    datetime.strptime(fecha, "%Y-%m-%d")
                except ValueError:
                    return False, f"Fecha inválida: {fecha}"

        return True, ""
