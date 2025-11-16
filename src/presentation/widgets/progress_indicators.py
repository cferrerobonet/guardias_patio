"""
Progress Indicators - Widgets para Operaciones Largas.

Este módulo proporciona diálogos y widgets para mostrar progreso
en operaciones que toman tiempo (generación de guardias, exportación, etc.).

Sprint 8 - Task 8.7
Migrado a presentation/widgets en Sprint 11 - Task 11.1.2
"""

import time
from typing import Callable, Optional

from PyQt6.QtCore import QMutex, Qt, QThread, QTimer, QWaitCondition, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from utils.ui_helpers import get_corporate_icon


class ProgressDialog(QDialog):
    """
    Diálogo de progreso para operaciones largas con cancelación.

    Muestra:
    - Título de la operación
    - Mensaje descriptivo
    - Barra de progreso (0-100%)
    - Log detallado de la operación
    - Botón de cancelación

    Ejemplo:
        dialog = ProgressDialog(
            parent=self,
            title="Generando Guardias",
            message="Procesando calendario escolar...",
            show_details=True
        )
        dialog.show()

        for i, item in enumerate(items):
            if dialog.fue_cancelado():
                break
            # ... procesar item ...
            dialog.actualizar_progreso(i + 1, len(items))

        dialog.close()
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Procesando...",
        message: str = "Por favor espere...",
        cancelable: bool = True,
        minimum: int = 0,
        maximum: int = 100,
        show_details: bool = True
    ):
        """
        Inicializar diálogo de progreso.

        Args:
            parent: Widget padre
            title: Título de la ventana
            message: Mensaje descriptivo
            cancelable: Si True, muestra botón de cancelar
            minimum: Valor mínimo de la barra (default 0)
            maximum: Valor máximo de la barra (default 100)
            show_details: Si True, muestra área de detalles con log
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setWindowIcon(get_corporate_icon())
        self.setModal(True)  # Bloquear interacción con ventana padre
        self.setMinimumWidth(600)
        self.setMinimumHeight(400 if show_details else 200)

        # Deshabilitar botón de maximizar (solo permitir cerrar y minimizar)
        # En macOS, usar WindowType.Sheet puede ser más estable
        import platform
        if platform.system() == 'Darwin':  # macOS
            self.setWindowFlags(
                Qt.WindowType.Sheet |
                Qt.WindowType.WindowTitleHint |
                Qt.WindowType.CustomizeWindowHint
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.Dialog |
                Qt.WindowType.WindowTitleHint |
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.CustomizeWindowHint
            )

        # Prevenir cierre accidental
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._cancelado = False
        self._cancelable = cancelable
        self._show_details = show_details
        self._start_time = time.time()
        self._timer = None

        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Mensaje principal
        self.label_mensaje = QLabel(message)
        self.label_mensaje.setWordWrap(True)
        self.label_mensaje.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #1976D2;
            }
        """)
        layout.addWidget(self.label_mensaje)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(minimum)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #CCCCCC;
                border-radius: 5px;
                text-align: center;
                height: 30px;
                font-size: 13px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #66BB6A);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Contador de tiempo (entre barra y detalle)
        self.label_tiempo = QLabel("Tiempo: 00:00:00")
        self.label_tiempo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_tiempo.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #757575;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.label_tiempo)

        # Label de detalle (ej: "5/100 procesados")
        self.label_detalle = QLabel("")
        self.label_detalle.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #555555;
            }
        """)
        layout.addWidget(self.label_detalle)

        # Área de detalles con log (si show_details=True)
        if show_details:
            # Label para el área de detalles
            label_log = QLabel("📋 Detalles del proceso:")
            label_log.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    font-weight: bold;
                    color: #666666;
                    margin-top: 5px;
                }
            """)
            layout.addWidget(label_log)

            # TextEdit para el log
            self.text_log = QTextEdit()
            self.text_log.setReadOnly(True)
            self.text_log.setStyleSheet("""
                QTextEdit {
                    background-color: #F5F5F5;
                    border: 1px solid #DDDDDD;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    padding: 8px;
                }
            """)
            self.text_log.setMaximumHeight(200)
            layout.addWidget(self.text_log)
        else:
            self.text_log = None

        # Botón cancelar
        if cancelable:
            self.btn_cancelar = QPushButton("Cancelar")
            self.btn_cancelar.clicked.connect(self._cancelar)
            self.btn_cancelar.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
                QPushButton:pressed {
                    background-color: #B71C1C;
                }
            """)
            layout.addWidget(self.btn_cancelar)

        self.setLayout(layout)

        # Iniciar timer para actualizar contador de tiempo
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._actualizar_tiempo)
        self._timer.start(1000)  # Actualizar cada segundo

    def actualizar_progreso(self, actual: int, total: int, detalle: str = ""):
        """
        Actualizar barra de progreso.

        Args:
            actual: Valor actual (items procesados)
            total: Valor total (items totales)
            detalle: Texto descriptivo adicional
        """
        if total > 0:
            porcentaje = int((actual / total) * 100)
            self.progress_bar.setValue(porcentaje)

        # Actualizar label de detalle
        if detalle:
            self.label_detalle.setText(detalle)
            # También añadir al log si está habilitado
            if self.text_log is not None:
                self.agregar_al_log(detalle)
        else:
            self.label_detalle.setText(f"{actual} / {total}")

    def agregar_al_log(self, mensaje: str):
        """
        Añadir un mensaje al log detallado.

        Args:
            mensaje: Mensaje a añadir
        """
        if self.text_log is not None:
            # Añadir con timestamp visual
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            linea = f"[{timestamp}] {mensaje}"

            self.text_log.append(linea)
            # Auto-scroll al final
            self.text_log.verticalScrollBar().setValue(
                self.text_log.verticalScrollBar().maximum()
            )

    def set_mensaje(self, mensaje: str):
        """
        Cambiar el mensaje principal.

        Args:
            mensaje: Nuevo mensaje
        """
        self.label_mensaje.setText(mensaje)
        # También añadir al log
        if self.text_log is not None:
            self.agregar_al_log(f"📌 {mensaje}")

    def _cancelar(self):
        """Manejar click en botón cancelar."""
        # Detener el timer
        if self._timer:
            self._timer.stop()

        self._cancelado = True
        self.label_mensaje.setText("⏳ Cancelando operación...")
        if hasattr(self, 'btn_cancelar'):
            self.btn_cancelar.setEnabled(False)

    def _actualizar_tiempo(self):
        """Actualizar el contador de tiempo transcurrido."""
        elapsed = int(time.time() - self._start_time)
        horas = elapsed // 3600
        minutos = (elapsed % 3600) // 60
        segundos = elapsed % 60
        self.label_tiempo.setText(f"Tiempo: {horas:02d}:{minutos:02d}:{segundos:02d}")

    def fue_cancelado(self) -> bool:
        """
        Verificar si el usuario canceló la operación.

        Returns:
            bool: True si fue cancelado, False si no
        """
        return self._cancelado

    def completar(self, mensaje_final: str = "✓ Operación completada"):
        """
        Marcar operación como completada.

        Args:
            mensaje_final: Mensaje a mostrar al completar
        """
        # Detener el timer
        if self._timer:
            self._timer.stop()
            self._actualizar_tiempo()  # Última actualización

        self.progress_bar.setValue(self.progress_bar.maximum())
        self.label_mensaje.setText(mensaje_final)

        if hasattr(self, 'btn_cancelar'):
            self.btn_cancelar.setText("Cerrar")
            self.btn_cancelar.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
            self.btn_cancelar.clicked.disconnect()
            self.btn_cancelar.clicked.connect(self.accept)


    def closeEvent(self, event):
        """
        Manejar evento de cierre para evitar cierres accidentales durante operaciones.
        """
        from utils.logger import get_logger
        logger = get_logger(__name__)

        # Si el diálogo fue cancelado o completado, permitir cierre
        if self._cancelado or self.progress_bar.value() >= self.progress_bar.maximum():
            logger.info("Diálogo de progreso cerrado normalmente")
            if self._timer:
                self._timer.stop()
            event.accept()
        else:
            # Operación en curso - prevenir cierre accidental
            logger.warning("Intento de cerrar diálogo durante operación en curso")
            event.ignore()


class WorkerThread(QThread):
    """
    Thread worker para ejecutar operaciones largas en background.

    Emite señales de progreso y resultado para actualizar UI.

    Ejemplo:
        def mi_operacion(actualizar_progreso):
            for i in range(100):
                # ... trabajo ...
                actualizar_progreso(i + 1, 100, f"Procesando item {i+1}")
            return resultado

        worker = WorkerThread(mi_operacion)
        worker.progreso.connect(dialog.actualizar_progreso)
        worker.finalizado.connect(self.on_operacion_completada)
        worker.error.connect(self.on_operacion_error)
        worker.start()
    """

    # Señales
    progreso = pyqtSignal(int, int, str)  # (actual, total, detalle)
    finalizado = pyqtSignal(object)  # resultado
    error = pyqtSignal(Exception)  # excepción
    # Señal para solicitar decisión al usuario (pasa diagnóstico)
    solicitar_decision = pyqtSignal(object)

    def __init__(self, funcion: Callable, *args, **kwargs):
        """
        Inicializar worker thread.

        Args:
            funcion: Función a ejecutar en background
            *args: Argumentos posicionales para la función
            **kwargs: Argumentos nombrados para la función
        """
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
            # Pasar callback de progreso a la función
            def callback_progreso(actual: int, total: int, detalle: str = ""):
                if self._debe_cancelar:
                    raise InterruptedError("Operación cancelada por el usuario")
                self.progreso.emit(actual, total, detalle)

            # Ejecutar función
            resultado = self.funcion(
                callback_progreso,
                *self.args,
                **self.kwargs
            )

            # Emitir resultado
            self.finalizado.emit(resultado)

        except InterruptedError as e:
            # Cancelación del usuario
            self.error.emit(e)
        except Exception as e:
            # Log del error con traceback completo
            import traceback

            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error en WorkerThread: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Emitir error
            self.error.emit(e)

    def cancelar(self):
        """Solicitar cancelación de la operación."""
        self._debe_cancelar = True

    def solicitar_decision_usuario(self, diagnostico):
        """
        Solicitar decisión del usuario desde el worker thread de forma segura.
        Emite señal y espera respuesta en el thread principal.

        Args:
            diagnostico: DiagnosticoCompleto a mostrar al usuario

        Returns:
            str: 'ajustar', 'continuar_ilp' o 'cancelar'
        """
        from utils.logger import get_logger
        logger = get_logger(__name__)

        logger.info("🔔 WorkerThread solicitando decisión del usuario...")

        # Resetear resultado
        self._decision_result = None

        # Emitir señal al thread principal
        self.solicitar_decision.emit(diagnostico)

        # Esperar respuesta con timeout
        self._decision_mutex.lock()
        timeout_ms = 300000  # 5 minutos de timeout
        if not self._decision_condition.wait(self._decision_mutex, timeout_ms):
            logger.error("⏱️ Timeout esperando decisión del usuario")
            self._decision_mutex.unlock()
            return 'cancelar'

        result = self._decision_result
        self._decision_mutex.unlock()

        logger.info(f"✅ Decisión del usuario recibida: {result}")
        return result

    def set_decision_resultado(self, resultado: str):
        """
        Establecer resultado de la decisión del usuario (llamado desde thread principal).

        Args:
            resultado: 'ajustar', 'continuar_ilp' o 'cancelar'
        """
        self._decision_mutex.lock()
        self._decision_result = resultado
        self._decision_condition.wakeOne()
        self._decision_mutex.unlock()


# ========== HELPER FUNCTIONS ==========

def ejecutar_con_progreso(
    parent: QWidget,
    funcion: Callable,
    titulo: str = "Procesando...",
    mensaje: str = "Por favor espere...",
    *args,
    **kwargs
) -> Optional[object]:
    """
    Helper para ejecutar función con diálogo de progreso automático.

    Args:
        parent: Widget padre
        funcion: Función a ejecutar (debe aceptar callback_progreso como primer arg)
        titulo: Título del diálogo
        mensaje: Mensaje del diálogo
        *args: Argumentos para la función
        **kwargs: Argumentos nombrados para la función

    Returns:
        Resultado de la función, o None si fue cancelada/error

    Ejemplo:
        def generar_guardias(callback_progreso, session):
            for i in range(total):
                # ... procesar ...
                callback_progreso(i+1, total, f"Día {i+1}")
            return guardias

        resultado = ejecutar_con_progreso(
            self,
            generar_guardias,
            titulo="Generando Guardias",
            mensaje="Procesando calendario...",
            session=session
        )
    """

    # Crear diálogo con detalles habilitados
    dialog = ProgressDialog(
        parent,
        titulo,
        mensaje,
        cancelable=True,
        show_details=True  # Habilitar área de log detallado
    )

    # Crear worker
    worker = WorkerThread(funcion, *args, **kwargs)

    # Variables para resultado
    resultado_final = [None]
    error_final = [None]

    # Conectar señales
    worker.progreso.connect(
        lambda actual, total, detalle: dialog.actualizar_progreso(actual, total, detalle)
    )

    def on_finalizado(resultado):
        resultado_final[0] = resultado
        dialog.completar("✅ Generación completada exitosamente")

    def on_error(error):
        error_final[0] = error
        # Log del error
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error en worker: {type(error).__name__}: {str(error)}")
        # Cerrar diálogo de forma segura
        try:
            if not isinstance(error, InterruptedError):
                dialog.set_mensaje(f"❌ Error: {str(error)[:100]}...")
                if hasattr(dialog, 'btn_cancelar'):
                    dialog.btn_cancelar.setText("Cerrar")
                    dialog.btn_cancelar.setEnabled(True)
            else:
                dialog.close()
        except Exception as e:
            logger.error(f"Error cerrando diálogo: {e}")
            dialog.close()

    def on_solicitar_decision(diagnostico):
        """Manejar solicitud de decisión del usuario desde el worker thread."""
        from utils.logger import get_logger
        logger = get_logger(__name__)

        logger.info("🔔 Solicitud de decisión recibida en thread principal")

        try:
            # Mostrar diálogo en el thread principal
            from src.presentation.dialogs.dialogo_diagnostico_guardias import (
                DialogoDiagnosticoGuardias,
            )

            dialogo = DialogoDiagnosticoGuardias(diagnostico, dialog)

            if dialogo.exec():
                resultado_decision = dialogo.get_accion_elegida()
            else:
                resultado_decision = 'cancelar'

            logger.info(f"✅ Usuario eligió: {resultado_decision}")

            # Enviar resultado de vuelta al worker
            worker.set_decision_resultado(resultado_decision)

        except Exception as e:
            logger.error(f"❌ Error mostrando diálogo de decisión: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # En caso de error, cancelar
            worker.set_decision_resultado('cancelar')

    worker.finalizado.connect(on_finalizado)
    worker.error.connect(on_error)
    worker.solicitar_decision.connect(on_solicitar_decision)

    # Conectar cancelación
    def on_cancelar():
        if dialog.fue_cancelado():
            worker.cancelar()

    if hasattr(dialog, 'btn_cancelar'):
        dialog.btn_cancelar.clicked.connect(on_cancelar)

    # Iniciar worker
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("🚀 Iniciando WorkerThread para ejecutar tarea")
    worker.start()

    # Mostrar diálogo (bloquea hasta cerrar)
    logger.info("📊 Mostrando ProgressDialog (bloqueante)")
    dialog.exec()
    logger.info("📊 ProgressDialog cerrado")

    # Esperar a que termine el worker
    worker.wait()

    # Manejar error
    if error_final[0]:
        if isinstance(error_final[0], InterruptedError):
            from utils.ui_helpers import show_info
            show_info(
                parent,
                "Operación Cancelada",
                "La operación fue cancelada por el usuario."
            )
        else:
            from utils.ui_helpers import show_error
            show_error(
                parent,
                "Error",
                f"Error durante la operación:\n\n{str(error_final[0])}"
            )
        return None

    return resultado_final[0]
