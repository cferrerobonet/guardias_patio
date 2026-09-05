"""
Progress Indicators - Widgets para Operaciones Largas.

Este módulo proporciona diálogos y widgets para mostrar progreso
en operaciones que toman tiempo (generación de guardias, exportación, etc.).

Sprint 8 - Task 8.7
Migrado a presentation/widgets en Sprint 11 - Task 11.1.2
"""

import logging
import time
from typing import Callable, Optional

from PyQt6.QtCore import (
    Qt,
    QTimer,
)
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.logging import get_logger
from presentation.widgets.progress_handlers import DecisionDialogHandler, ProgressLogHandler
from presentation.widgets.progress_worker import WorkerThread
from utils.ui_helpers import get_corporate_icon

_logger = get_logger(__name__)


# Loggers de los algoritmos vivos, los únicos cuyo detalle interesa mostrar durante
# la generación. Los antiguos (iterativo, ilp, orquestador, v3) ya no existen.
LOGGERS_CAPTURADOS = (
    "services.asignador_guardias_cpsat",
    "services.asignador_guardias_v4_hibrido",
)


class ProgressDialog(QDialog):
    """
    Diálogo de progreso para operaciones largas con cancelación.

    Muestra:
    - Barra de progreso
    - Contador de tiempo
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
        show_details: bool = True,
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

        if platform.system() == "Darwin":  # macOS
            self.setWindowFlags(
                Qt.WindowType.Sheet
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.CustomizeWindowHint
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowCloseButtonHint
                | Qt.WindowType.CustomizeWindowHint
            )

        # Prevenir cierre accidental
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._cancelado = False
        self._cancelable = cancelable
        self._show_details = show_details
        self._start_time = time.time()
        self._timer = None
        self._last_progress = 0
        self._progress_history = []  # Para calcular tiempo estimado
        self._cpu_percent = 0.0
        self._log_handler = None  # Handler para capturar logs
        self._niveles_previos = {}  # Niveles de los loggers antes de capturarlos

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

        # Métricas de sistema (CPU y tiempo estimado)
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)

        # CPU Usage
        self.label_cpu = QLabel("💻 CPU: 0%")
        self.label_cpu.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #666;
                padding: 4px 8px;
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        metrics_layout.addWidget(self.label_cpu)

        # Tiempo estimado
        self.label_eta = QLabel("ETA: calculando...")
        self.label_eta.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #666;
                padding: 4px 8px;
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        metrics_layout.addWidget(self.label_eta)

        metrics_layout.addStretch()
        layout.addLayout(metrics_layout)

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
            label_log = QLabel("Detalles del proceso:")
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
            self.btn_cancelar.setProperty("danger", "true")
            layout.addWidget(self.btn_cancelar)

            self.btn_cerrar = QPushButton("Cerrar")
            self.btn_cerrar.setProperty("success", "true")
            self.btn_cerrar.clicked.connect(self.accept)
            self.btn_cerrar.setVisible(False)
            layout.addWidget(self.btn_cerrar)

        self.setLayout(layout)

        # Iniciar timer para actualizar contador de tiempo
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._actualizar_tiempo)
        self._timer.start(1000)  # Actualizar cada segundo

        # Si show_details, instalar handler de logging
        if show_details:
            self._instalar_log_handler()

    def _instalar_log_handler(self):
        """Instala un handler de logging para capturar logs en tiempo real."""
        try:
            self._log_handler = ProgressLogHandler(self)
            self._niveles_previos = {}
            for nombre in LOGGERS_CAPTURADOS:
                logger = logging.getLogger(nombre)
                logger.addHandler(self._log_handler)
                # Sin esto el detalle nunca se ve: el nivel efectivo heredado es
                # WARNING y los info del algoritmo se descartan antes del handler.
                if logger.getEffectiveLevel() > logging.INFO:
                    self._niveles_previos[nombre] = logger.level
                    logger.setLevel(logging.INFO)
        except (ValueError, TypeError, OSError) as e:
            _logger.debug(f"No se pudo instalar log handler: {e}")

    def _desinstalar_log_handler(self):
        """Desinstala el handler de logging."""
        if self._log_handler:
            try:
                for nombre in LOGGERS_CAPTURADOS:
                    logger = logging.getLogger(nombre)
                    logger.removeHandler(self._log_handler)
                    if nombre in self._niveles_previos:
                        logger.setLevel(self._niveles_previos.pop(nombre))
                self._log_handler = None
            except (ValueError, TypeError, OSError) as e:
                _logger.debug(f"No se pudo desinstalar log handler: {e}")

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

            # Actualizar historial de progreso para ETA
            current_time = time.time()
            self._progress_history.append((current_time, porcentaje))

            # Mantener solo últimos 10 puntos
            if len(self._progress_history) > 10:
                self._progress_history.pop(0)

            # Calcular ETA si tenemos suficientes datos
            self._actualizar_eta(porcentaje)

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
            self.text_log.verticalScrollBar().setValue(self.text_log.verticalScrollBar().maximum())

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
        if hasattr(self, "btn_cancelar"):
            self.btn_cancelar.setEnabled(False)

    def _actualizar_tiempo(self):
        """Actualizar el contador de tiempo transcurrido y métricas del sistema."""
        elapsed = int(time.time() - self._start_time)
        horas = elapsed // 3600
        minutos = (elapsed % 3600) // 60
        segundos = elapsed % 60
        self.label_tiempo.setText(f"Tiempo: {horas:02d}:{minutos:02d}:{segundos:02d}")

        # Actualizar CPU usage
        self._actualizar_cpu()

    def _actualizar_cpu(self):
        """Actualizar el uso de CPU y número de cores activos."""
        try:
            import os

            import psutil

            # Obtener uso de CPU total (no bloqueante)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self._cpu_percent = cpu_percent

            # Obtener uso por core para calcular cores activos
            cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)
            total_cores = os.cpu_count() or 1

            # Contar cores activos (> 50% de uso)
            cores_activos = sum(1 for usage in cpu_per_core if usage > 50)

            # Calcular cores equivalentes basados en el uso total
            cores_equivalentes = cpu_percent / 100 * total_cores

            # Actualizar label con color según uso
            if cpu_percent < 30:
                color = "#4CAF50"  # Verde
                emoji = "💻"
            elif cpu_percent < 70:
                color = "#FF9800"  # Naranja
                emoji = "⚡"
            else:
                color = "#F44336"  # Rojo
                emoji = "🔥"

            # Mostrar: % total, cores activos y cores equivalentes
            self.label_cpu.setText(
                f"{emoji} CPU: {cpu_percent:.0f}% "
                f"({cores_activos}/{total_cores} cores, ~{cores_equivalentes:.1f} equiv.)"
            )
            self.label_cpu.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {color};
                    font-weight: bold;
                    padding: 4px 8px;
                    background-color: #f0f0f0;
                    border-radius: 3px;
                }}
            """)
        except ImportError:
            # psutil no disponible
            self.label_cpu.setText("💻 CPU: N/A")
        except (ValueError, TypeError, OSError) as e:
            _logger.debug(f"Error actualizando CPU: {e}")

    def _actualizar_eta(self, porcentaje_actual: int):
        """Calcular y actualizar el tiempo estimado de finalización."""
        if len(self._progress_history) < 2 or porcentaje_actual >= 100:
            return

        # Calcular velocidad promedio (porcentaje por segundo)
        tiempo_inicio, porcentaje_inicio = self._progress_history[0]
        tiempo_actual, _ = self._progress_history[-1]

        tiempo_transcurrido = tiempo_actual - tiempo_inicio
        progreso_realizado = porcentaje_actual - porcentaje_inicio

        if progreso_realizado > 0 and tiempo_transcurrido > 0:
            velocidad = progreso_realizado / tiempo_transcurrido  # % por segundo
            porcentaje_restante = 100 - porcentaje_actual
            segundos_restantes = int(porcentaje_restante / velocidad)

            # Formatear ETA
            if segundos_restantes < 60:
                eta_text = f"{segundos_restantes}s"
            elif segundos_restantes < 3600:
                minutos = segundos_restantes // 60
                segundos = segundos_restantes % 60
                eta_text = f"{minutos}m {segundos}s"
            else:
                horas = segundos_restantes // 3600
                minutos = (segundos_restantes % 3600) // 60
                eta_text = f"{horas}h {minutos}m"

            self.label_eta.setText(f"ETA: {eta_text}")
        else:
            self.label_eta.setText("ETA: calculando...")

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

        if hasattr(self, "btn_cancelar"):
            self.btn_cancelar.setVisible(False)
        if hasattr(self, "btn_cerrar"):
            self.btn_cerrar.setVisible(True)
            self.btn_cerrar.setFocus()

    def closeEvent(self, event):
        """
        Manejar evento de cierre para evitar cierres accidentales durante operaciones.
        También limpia los handlers de log.
        """
        from utils.logger import get_logger

        logger = get_logger(__name__)

        # Si el diálogo fue cancelado o completado, permitir cierre
        if self._cancelado or self.progress_bar.value() >= self.progress_bar.maximum():
            logger.info("Diálogo de progreso cerrado normalmente")
            self._desinstalar_log_handler()
            if self._timer:
                self._timer.stop()
            event.accept()
        else:
            # Operación en curso - prevenir cierre accidental
            logger.warning("Intento de cerrar diálogo durante operación en curso")
            event.ignore()


def ejecutar_con_progreso(
    parent: QWidget,
    funcion: Callable,
    titulo: str = "Procesando...",
    mensaje: str = "Por favor espere...",
    *args,
    **kwargs,
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
        show_details=True,  # Habilitar área de log detallado
    )

    # Crear worker
    from utils.logger import get_logger

    logger_worker = get_logger(__name__)
    import traceback

    logger_worker.debug(
        f"🔧 CREANDO WorkerThread para función: {funcion.__name__}\n"
        f"   Stack trace de creación:\n{''.join(traceback.format_stack()[-5:])}"
    )
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
        dialog.completar("Generación completada exitosamente")

    def on_error(error):
        error_final[0] = error
        # Log del error
        from utils.logger import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error en worker: {type(error).__name__}: {str(error)}")

        # Cerrar diálogo de forma segura
        try:
            # CRITICAL FIX: Detener el timer para evitar que siga contando
            if hasattr(dialog, "_timer") and dialog._timer:
                dialog._timer.stop()
                logger.info("⏹️ Timer del diálogo detenido")

            if not isinstance(error, InterruptedError):
                # Mostrar mensaje de error
                dialog.set_mensaje(f"Error: {str(error)[:100]}...")

                # Marcar como completado (con error) para permitir cierre
                dialog._cancelado = True

                # Mostrar botón cerrar
                if hasattr(dialog, "btn_cerrar"):
                    if hasattr(dialog, "btn_cancelar"):
                        dialog.btn_cancelar.setVisible(False)
                    dialog.btn_cerrar.setVisible(True)
                    dialog.btn_cerrar.clicked.disconnect()
                    dialog.btn_cerrar.clicked.connect(dialog.close)
                    logger.info("🔘 Botón cerrar visible")
            else:
                # Si fue cancelación del usuario, simplemente cerrar
                dialog.close()
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Error cerrando diálogo: {e}")
            # Forzar cierre en caso de error
            try:
                dialog.close()
            except (ValueError, TypeError, OSError) as e:
                _logger.debug(f"No se pudo cerrar diálogo: {e}")

    worker.finalizado.connect(on_finalizado)
    worker.error.connect(on_error)
    from PyQt6.QtCore import Qt

    decision_handler = DecisionDialogHandler(dialog, worker)
    dialog._decision_handler = decision_handler
    worker.solicitar_decision.connect(
        decision_handler.handle_decision, Qt.ConnectionType.QueuedConnection
    )

    # Conectar cancelación
    def on_cancelar():
        if dialog.fue_cancelado():
            worker.cancelar()

    if hasattr(dialog, "btn_cancelar"):
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

            show_info(parent, "Operación Cancelada", "La operación fue cancelada por el usuario.")
        else:
            from utils.ui_helpers import show_error

            show_error(parent, "Error", f"Error durante la operación:\n\n{str(error_final[0])}")
        return None

    return resultado_final[0]
