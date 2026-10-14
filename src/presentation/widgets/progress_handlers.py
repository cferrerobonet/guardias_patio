"""
Handlers auxiliares para el sistema de progreso.

Extraído desde progress_indicators.py para reducir tamaño del módulo principal.
"""

import logging

from PyQt6.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QDialog


class _PuenteLog(QObject):
    """Portador de la señal que cruza del hilo que loguea al hilo GUI.

    Vive en el hilo GUI, así que la conexión en cola hace que `_entregar` se ejecute
    siempre ahí, sea cual sea el hilo que emitió.
    """

    linea = pyqtSignal(str)

    def __init__(self, progress_dialog):
        super().__init__()
        self._dialogo = progress_dialog
        self.linea.connect(self._entregar, Qt.ConnectionType.QueuedConnection)

    @pyqtSlot(str)
    def _entregar(self, mensaje: str):
        self._dialogo.agregar_al_log(mensaje)


class ProgressLogHandler(logging.Handler):
    """Handler de logging que redirige mensajes al diálogo de progreso.

    `emit` se ejecuta en el hilo que llama a `logger.info` —el worker o los hilos del
    solver—, así que no puede tocar widgets. Publica en una señal que Qt entrega en
    el hilo GUI mediante conexión en cola (CRW-002).
    """

    def __init__(self, progress_dialog):
        super().__init__()
        self.progress_dialog = progress_dialog
        self.setLevel(logging.INFO)

        self._puente = _PuenteLog(progress_dialog)

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
                if msg_clean:
                    self._puente.linea.emit(msg_clean)
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
