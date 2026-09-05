"""
Widget de configuración de ajustes adicionales.

Combina:
- Multiplicador para tutores (ajuste_tutores)
- Multiplicador para no tutores (ajuste_no_tutores)
- Información del algoritmo de asignación (solo lectura)
"""

from PyQt6.QtCore import QRegularExpression, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QGroupBox, QLabel, QLineEdit, QVBoxLayout

from presentation.theme import legacy_styles as styles

ALGORITMO_LABELS = {
    "v4.0": "Rápido (v4 Híbrido)",
    "rapido": "Rápido (v4 Híbrido)",
    "cpsat": "Óptimo (CP-SAT)",
    "optimo": "Óptimo (CP-SAT)",
    "cp-sat": "Óptimo (CP-SAT)",
}


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
        self._algoritmo_actual = "v4.0"
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Crea la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(6, 6, 6, 6)

        # ===== Multiplicador tutores =====
        label_tutores = QLabel("Multiplicador tutores:")
        label_tutores.setStyleSheet(
            styles.STYLE_LABEL_FIELD + "font-size: 12px; margin-bottom: 1px;"
        )
        layout.addWidget(label_tutores)

        self.ajuste_tutores_input = QLineEdit()
        self.ajuste_tutores_input.setAccessibleName("Campo multiplicador de tutores")
        self.ajuste_tutores_input.setPlaceholderText("0.90")
        self.ajuste_tutores_input.setStyleSheet(
            styles.STYLE_INPUT + "padding: 3px; margin-bottom: 2px;"
        )
        self.ajuste_tutores_input.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]*"))
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
            styles.STYLE_LABEL_FIELD + "font-size: 12px; margin-bottom: 1px;"
        )
        layout.addWidget(label_no_tutores)

        self.ajuste_no_tutores_input = QLineEdit()
        self.ajuste_no_tutores_input.setAccessibleName("Campo multiplicador de no tutores")
        self.ajuste_no_tutores_input.setPlaceholderText("1.00")
        self.ajuste_no_tutores_input.setStyleSheet(
            styles.STYLE_INPUT + "padding: 3px; margin-bottom: 2px;"
        )
        self.ajuste_no_tutores_input.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]*"))
        )
        self.ajuste_no_tutores_input.setToolTip(
            "Factor multiplicador para no tutores (valores > 1.0 aumentan su carga)\n"
            "Ejemplo: 1.10 = 10% más guardias que un profesor normal"
        )
        self.ajuste_no_tutores_input.textChanged.connect(self.config_changed.emit)
        layout.addWidget(self.ajuste_no_tutores_input)

        # ===== Información de algoritmo (solo lectura) =====
        label_algoritmo = QLabel("Algoritmos disponibles:")
        label_algoritmo.setStyleSheet(
            styles.STYLE_LABEL_FIELD + "font-size: 12px; margin-bottom: 1px; margin-top: 4px;"
        )
        layout.addWidget(label_algoritmo)

        # Label informativo con todos los algoritmos
        self.algoritmo_info = QLabel()
        self.algoritmo_info.setWordWrap(True)
        self.algoritmo_info.setStyleSheet(
            styles.STYLE_INPUT + "padding: 10px 12px; background-color: #f8f8f8; color: #334155; "
            "font-size: 12px; line-height: 1.45; border: 1px solid #d7dee7;"
        )
        self.algoritmo_info.setToolTip(
            "ALGORITMOS DISPONIBLES ACTUALMENTE:\n\n"
            "• Rápido (v4 Híbrido)\n"
            "  Heurístico y ágil para uso general.\n\n"
            "• Óptimo (CP-SAT)\n"
            "  Más lento, pero busca la mejor solución posible.\n\n"
            "Selecciona el algoritmo según tus necesidades de velocidad o calidad de solución."
        )
        self._actualizar_info_algoritmo()
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
                - algoritmo: str (algoritmo actual válido)
        """
        return {
            "tutores": float(self.ajuste_tutores_input.text() or 1.0),
            "no_tutores": float(self.ajuste_no_tutores_input.text() or 1.0),
            "algoritmo": self._algoritmo_actual,
        }

    def set_ajustes(
        self,
        tutores: float = 1.0,
        no_tutores: float = 1.0,
        algoritmo: str = "v4.0",
    ) -> None:
        """
        Establece los valores de ajustes.

        Args:
            tutores: Multiplicador para tutores (default: 1.0)
            no_tutores: Multiplicador para no tutores (default: 1.0)
            algoritmo: Algoritmo actual guardado en configuración
        """
        self.ajuste_tutores_input.setText(str(tutores))
        self.ajuste_no_tutores_input.setText(str(no_tutores))
        self._algoritmo_actual = self._normalizar_algoritmo(algoritmo)
        self._actualizar_info_algoritmo()

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

        return True, ""

    def _normalizar_algoritmo(self, algoritmo: str | None) -> str:
        algoritmo_normalizado = (algoritmo or "").strip().lower()
        if algoritmo_normalizado in ("cpsat", "optimo", "cp-sat"):
            return "cpsat"
        return "v4.0"

    def _actualizar_info_algoritmo(self) -> None:
        algoritmo_activo = ALGORITMO_LABELS.get(self._algoritmo_actual, "Rápido (v4 Híbrido)")
        self.algoritmo_info.setText(
            "Activo: "
            f"{algoritmo_activo}\n\n"
            "Disponibles actualmente:\n"
            "• Rápido (v4 Híbrido): heurístico, más ágil para el día a día.\n"
            "• Óptimo (CP-SAT): más lento, pero busca la mejor solución posible.\n\n"
            "Cambia el algoritmo según tus necesidades de velocidad o calidad de resultado."
        )
