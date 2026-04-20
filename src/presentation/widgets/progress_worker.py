"""
Worker thread para operaciones largas con progreso.

Extraído desde progress_indicators.py para reducir tamaño del módulo principal.
"""

from typing import Callable

from PyQt6.QtCore import QMutex, QThread, QWaitCondition, pyqtSignal

from core.logging import get_logger

_logger = get_logger(__name__)


class WorkerThread(QThread):
    """
    Thread worker para ejecutar operaciones largas en background.
    """

    progreso = pyqtSignal(int, int, str)  # (actual, total, detalle)
    finalizado = pyqtSignal(object)  # resultado
    error = pyqtSignal(Exception)  # excepción
    solicitar_decision = pyqtSignal(object)

    def __init__(self, funcion: Callable, *args, **kwargs):
        super().__init__()
        self.funcion = funcion
        self.args = args
        self.kwargs = kwargs
        self._debe_cancelar = False

        # Para manejo de decisiones del usuario desde worker thread
        self._decision_mutex = QMutex()
        self._decision_condition = QWaitCondition()
        self._decision_result = None

    def run(self):
        """Ejecutar función en thread separado."""
        try:
            def callback_progreso(actual: int, total: int, detalle: str = ""):
                if self._debe_cancelar:
                    raise InterruptedError("Operación cancelada por el usuario")
                self.progreso.emit(actual, total, detalle)

            resultado = self.funcion(callback_progreso, *self.args, **self.kwargs)
            self.finalizado.emit(resultado)

        except InterruptedError as e:
            self.error.emit(e)
        except Exception as e:
            import traceback
            from utils.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error en WorkerThread: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.error.emit(e)

    def cancelar(self):
        """Solicitar cancelación de la operación."""
        self._debe_cancelar = True

    def solicitar_decision_usuario(self, diagnostico):
        """
        Solicitar decisión del usuario desde el worker thread de forma segura.
        """
        from utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            logger.info("🔔 WorkerThread solicitando decisión del usuario...")
            self._decision_result = None
            self.solicitar_decision.emit(diagnostico)

            self._decision_mutex.lock()
            timeout_ms = 300000  # 5 minutos de timeout
            logger.info(f"⏳ Esperando decisión del usuario (timeout: {timeout_ms / 1000}s)...")

            if not self._decision_condition.wait(self._decision_mutex, timeout_ms):
                logger.error("⏱️ TIMEOUT esperando decisión del usuario (5 minutos)")
                logger.error("   El diálogo probablemente no se mostró o el usuario no respondió")
                self._decision_mutex.unlock()
                return "cancelar"

            result = self._decision_result
            self._decision_mutex.unlock()

            logger.info(f"✅ Decisión del usuario recibida: {result}")
            return result

        except (ValueError, TypeError, OSError) as e:
            logger.error(f"❌ Error en solicitar_decision_usuario: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            try:
                self._decision_mutex.unlock()
            except (ValueError, TypeError, OSError) as unlock_error:
                _logger.debug(f"No se pudo desbloquear mutex: {unlock_error}")

            return "error"

    def set_decision_resultado(self, resultado: str):
        """
        Establecer resultado de la decisión del usuario (llamado desde thread principal).
        """
        self._decision_mutex.lock()
        self._decision_result = resultado
        self._decision_condition.wakeOne()
        self._decision_mutex.unlock()
