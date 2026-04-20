"""
Handlers auxiliares para el sistema de progreso.

Extraído desde progress_indicators.py para reducir tamaño del módulo principal.
"""

import logging

from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtWidgets import QDialog


class ProgressLogHandler(logging.Handler):
    """Handler de logging que redirige mensajes al diálogo de progreso."""

    def __init__(self, progress_dialog):
        super().__init__()
        self.progress_dialog = progress_dialog
        self.setLevel(logging.INFO)

        # Filtrar solo mensajes relevantes para el usuario
        self.keywords = [
            "ITERACIÓN",
            "Cobertura",
            "guardias asignadas",
            "Solución",
            "Ejecutando",
            "Calculando",
            "Preparando",
            "Validando",
            "Generando",
            "Procesando",
            "Analizando",
            "Optimizando",
            "ILP",
            "algoritmo",
            "cores",
            "slots",
            "profesores",
        ]

    def emit(self, record):
        try:
            msg = self.format(record)

            # Filtrar mensajes técnicos no relevantes
            if any(keyword in msg for keyword in self.keywords):
                # Limpiar formato para mejor visualización
                msg_clean = msg.replace("=" * 70, "").strip()
                if msg_clean and self.progress_dialog.text_log:
                    self.progress_dialog.agregar_al_log(msg_clean)
        except (ValueError, TypeError, OSError):
            self.handleError(record)


class DecisionDialogHandler(QObject):
    """
    Maneja la comunicación bidireccional worker↔GUI para solicitar decisiones al usuario.
    """

    def __init__(self, dialog: QDialog, worker):
        super().__init__()
        self._dialog = dialog
        self._worker = worker

    @pyqtSlot(object)
    def handle_decision(self, diagnostico):
        """Mostrar diálogo de decisión al usuario y notificar al worker."""
        from utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info("🔔 DecisionDialogHandler: mostrando diálogo de decisión")

        try:
            from PyQt6.QtWidgets import QMessageBox

            # Construir mensaje a partir del diagnóstico
            if hasattr(diagnostico, "mensaje"):
                msg_text = str(diagnostico.mensaje)
            elif hasattr(diagnostico, "__str__"):
                msg_text = str(diagnostico)
            else:
                msg_text = "Se requiere una decisión para continuar."

            msg = QMessageBox(self._dialog)
            msg.setWindowTitle("Decisión requerida")
            msg.setText(msg_text)
            msg.addButton("Ajustar y continuar", QMessageBox.ButtonRole.AcceptRole)
            msg.addButton("Continuar sin ajustar", QMessageBox.ButtonRole.NoRole)
            msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            msg.exec()

            clicked = msg.clickedButton()
            if clicked and "Cancelar" in clicked.text():
                resultado = "cancelar"
            elif clicked and "sin ajustar" in clicked.text():
                resultado = "continuar_ilp"
            else:
                resultado = "ajustar"

            logger.info(f"✅ Decisión del usuario: {resultado}")
        except Exception as e:
            logger.error(f"Error en handle_decision: {e}")
            resultado = "cancelar"

        self._worker.set_decision_resultado(resultado)
