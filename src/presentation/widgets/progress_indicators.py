"""
Progress Indicators - Widgets para Operaciones Largas.

Este módulo proporciona diálogos y widgets para mostrar progreso
en operaciones que toman tiempo (generación de guardias, exportación, etc.).

Sprint 8 - Task 8.7
Migrado a presentation/widgets en Sprint 11 - Task 11.1.2
"""

from typing import Callable, Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProgressDialog(QDialog):
    """
    Diálogo de progreso para operaciones largas con cancelación.
    
    Muestra:
    - Título de la operación
    - Mensaje descriptivo
    - Barra de progreso (0-100%)
    - Botón de cancelación
    
    Ejemplo:
        dialog = ProgressDialog(
            parent=self,
            title="Generando Guardias",
            message="Procesando calendario escolar..."
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
        maximum: int = 100
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
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setModal(True)  # Bloquear interacción con ventana padre
        self.setMinimumWidth(400)

        self._cancelado = False
        self._cancelable = cancelable

        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Mensaje
        self.label_mensaje = QLabel(message)
        self.label_mensaje.setWordWrap(True)
        self.label_mensaje.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #333333;
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
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Label de detalle (ej: "5/100 procesados")
        self.label_detalle = QLabel("")
        self.label_detalle.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666666;
            }
        """)
        layout.addWidget(self.label_detalle)

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
        else:
            self.label_detalle.setText(f"{actual} / {total}")

    def set_mensaje(self, mensaje: str):
        """
        Cambiar el mensaje principal.
        
        Args:
            mensaje: Nuevo mensaje
        """
        self.label_mensaje.setText(mensaje)

    def _cancelar(self):
        """Manejar click en botón cancelar."""
        self._cancelado = True
        self.label_mensaje.setText("⏳ Cancelando operación...")
        if hasattr(self, 'btn_cancelar'):
            self.btn_cancelar.setEnabled(False)

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

        except Exception as e:
            # Emitir error
            self.error.emit(e)

    def cancelar(self):
        """Solicitar cancelación de la operación."""
        self._debe_cancelar = True


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
    from PyQt6.QtWidgets import QMessageBox

    # Crear diálogo
    dialog = ProgressDialog(parent, titulo, mensaje)

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
        dialog.completar()

    def on_error(error):
        error_final[0] = error
        dialog.close()

    worker.finalizado.connect(on_finalizado)
    worker.error.connect(on_error)

    # Conectar cancelación
    def on_cancelar():
        if dialog.fue_cancelado():
            worker.cancelar()

    if hasattr(dialog, 'btn_cancelar'):
        dialog.btn_cancelar.clicked.connect(on_cancelar)

    # Iniciar worker
    worker.start()

    # Mostrar diálogo (bloquea hasta cerrar)
    dialog.exec()

    # Esperar a que termine el worker
    worker.wait()

    # Manejar error
    if error_final[0]:
        if isinstance(error_final[0], InterruptedError):
            QMessageBox.information(
                parent,
                "Operación Cancelada",
                "La operación fue cancelada por el usuario."
            )
        else:
            QMessageBox.critical(
                parent,
                "Error",
                f"Error durante la operación:\n\n{str(error_final[0])}"
            )
        return None

    return resultado_final[0]
