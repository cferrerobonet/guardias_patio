"""
Widget de configuración de ajustes adicionales.

Combina:
- Multiplicador para tutores (ajuste_tutores)
- Multiplicador para no tutores (ajuste_no_tutores)
- Información del algoritmo de asignación (solo lectura)
"""

import ui_styles as styles
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QLabel, QLineEdit, QVBoxLayout


class AjustesWidget(QGroupBox):
    """
    Widget para gestionar ajustes adicionales de configuración.

    Combina en un solo widget:
    - Multiplicadores de guardias (tutores/no tutores)
    - Selector de algoritmo de asignación

    Signals:
        config_changed: Emitido cuando cambia cualquier valor
    """

    # Señales
    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa el widget de ajustes.

        Args:
            parent: Widget padre opcional
        """
        super().__init__("🔧 Ajustes Adicionales", parent)
        self.setStyleSheet(styles.STYLE_GROUPBOX)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Crea la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(6, 6, 6, 6)

        # ===== Multiplicador tutores =====
        label_tutores = QLabel("Multiplicador tutores:")
        label_tutores.setStyleSheet(
            styles.STYLE_LABEL_FIELD + "font-size: 10px; margin-bottom: 1px;"
        )
        layout.addWidget(label_tutores)

        self.ajuste_tutores_input = QLineEdit()
        self.ajuste_tutores_input.setPlaceholderText("0.90")
        self.ajuste_tutores_input.setStyleSheet(
            styles.STYLE_INPUT + "padding: 3px; margin-bottom: 2px;"
        )
        self.ajuste_tutores_input.setToolTip(
            "Factor multiplicador para tutores (valores < 1.0 reducen su carga de guardias)\n"
            "Ejemplo: 0.90 = 10% menos guardias que un profesor normal"
        )
        self.ajuste_tutores_input.textChanged.connect(self.config_changed.emit)
        layout.addWidget(self.ajuste_tutores_input)

        # ===== Multiplicador no tutores =====
        label_no_tutores = QLabel("Multiplicador no tutores:")
        label_no_tutores.setStyleSheet(
            styles.STYLE_LABEL_FIELD + "font-size: 10px; margin-bottom: 1px;"
        )
        layout.addWidget(label_no_tutores)

        self.ajuste_no_tutores_input = QLineEdit()
        self.ajuste_no_tutores_input.setPlaceholderText("1.00")
        self.ajuste_no_tutores_input.setStyleSheet(
            styles.STYLE_INPUT + "padding: 3px; margin-bottom: 2px;"
        )
        self.ajuste_no_tutores_input.setToolTip(
            "Factor multiplicador para no tutores (valores > 1.0 aumentan su carga)\n"
            "Ejemplo: 1.10 = 10% más guardias que un profesor normal"
        )
        self.ajuste_no_tutores_input.textChanged.connect(self.config_changed.emit)
        layout.addWidget(self.ajuste_no_tutores_input)

        # ===== Información de algoritmo (solo lectura) =====
        label_algoritmo = QLabel("Algoritmo de asignación:")
        label_algoritmo.setStyleSheet(
            styles.STYLE_LABEL_FIELD + "font-size: 10px; margin-bottom: 1px;"
        )
        layout.addWidget(label_algoritmo)

        # Label informativo en lugar de combo
        self.algoritmo_info = QLabel("v3.0 - Simple Determinista ⚡")
        self.algoritmo_info.setStyleSheet(
            styles.STYLE_INPUT +
            "padding: 6px; background-color: #f0f0f0; color: #666; font-weight: bold;"
        )
        self.algoritmo_info.setToolTip(
            "Algoritmo v3.0: Simple determinista que garantiza 100% cobertura.\n"
            "Este algoritmo está optimizado para distribución equitativa."
        )
        layout.addWidget(self.algoritmo_info)

        self.setLayout(layout)

    # ===== API PÚBLICA: GET/SET =====

    def get_ajustes(self) -> dict:
        """
        Obtiene los valores de ajustes.

        Returns:
            dict: Diccionario con claves:
                - tutores: float (multiplicador tutores)
                - no_tutores: float (multiplicador no tutores)
                - algoritmo: str (siempre "v3.0", fijo)
        """
        return {
            "tutores": float(self.ajuste_tutores_input.text() or 1.0),
            "no_tutores": float(self.ajuste_no_tutores_input.text() or 1.0),
            "algoritmo": "v3.0"  # Siempre v3.0
        }

    def set_ajustes(
        self,
        tutores: float = 1.0,
        no_tutores: float = 1.0,
        algoritmo: str = "v3.0"  # Ignorado, siempre v3.0
    ) -> None:
        """
        Establece los valores de ajustes.

        Args:
            tutores: Multiplicador para tutores (default: 1.0)
            no_tutores: Multiplicador para no tutores (default: 1.0)
            algoritmo: Ignorado, el algoritmo siempre es v3.0
        """
        self.ajuste_tutores_input.setText(str(tutores))
        self.ajuste_no_tutores_input.setText(str(no_tutores))
        # No hacemos nada con el algoritmo, siempre es v3.0

    def validar(self) -> tuple[bool, str]:
        """
        Valida los valores de ajustes.

        Returns:
            tuple: (es_valido, mensaje_error)
                - es_valido: True si todos los valores son válidos
                - mensaje_error: Descripción del error si no es válido
        """
        # Validar multiplicador tutores
        try:
            tutores = float(self.ajuste_tutores_input.text() or 1.0)
            if tutores <= 0 or tutores > 2.0:
                return False, "El multiplicador de tutores debe estar entre 0 y 2.0"
        except ValueError:
            return False, "El multiplicador de tutores debe ser un número válido"

        # Validar multiplicador no tutores
        try:
            no_tutores = float(self.ajuste_no_tutores_input.text() or 1.0)
            if no_tutores <= 0 or no_tutores > 2.0:
                return False, "El multiplicador de no tutores debe estar entre 0 y 2.0"
        except ValueError:
            return False, "El multiplicador de no tutores debe ser un número válido"

        # El algoritmo siempre es v3.0, no hay nada que validar

        return True, ""
