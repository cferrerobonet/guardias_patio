"""
Tests para Progress Indicators.

Sprint 8 - Task 8.7
"""

import pytest
from presentation.widgets.progress_indicators import (
    ProgressDialog,
    WorkerThread,
)
from PyQt6.QtWidgets import QWidget

# ========== FIXTURES ==========


@pytest.fixture
def qapp(qapp):
    """Fixture para QApplication (provided by pytest-qt)."""
    return qapp


@pytest.fixture
def parent_widget(qapp):
    """Crear widget padre para tests."""
    return QWidget()


@pytest.fixture
def cleanup_threads():
    """Fixture para limpiar threads después de cada test."""
    threads = []
    yield threads
    # Cleanup: esperar a que todos los threads terminen
    for worker in threads:
        if worker.isRunning():
            worker.cancelar()
            worker.wait(1000)


# ========== TESTS PROGRESS DIALOG ==========


class TestProgressDialog:
    """Tests para ProgressDialog."""

    def test_crear_dialog_basico(self, parent_widget, qtbot):
        """Crear diálogo de progreso básico."""
        dialog = ProgressDialog(parent=parent_widget, title="Test", message="Procesando...")

        assert dialog.windowTitle() == "Test"
        assert "Procesando..." in dialog.label_mensaje.text()
        assert dialog.progress_bar.value() == 0
        assert dialog.progress_bar.maximum() == 100
        assert hasattr(dialog, "btn_cancelar")

    def test_dialog_sin_cancelacion(self, parent_widget, qtbot):
        """Crear diálogo sin botón de cancelar."""
        dialog = ProgressDialog(parent=parent_widget, cancelable=False)

        assert not hasattr(dialog, "btn_cancelar")

    def test_actualizar_progreso(self, parent_widget, qtbot):
        """Actualizar progreso del diálogo."""
        dialog = ProgressDialog(parent=parent_widget)

        # Actualizar a 50%
        dialog.actualizar_progreso(50, 100)
        assert dialog.progress_bar.value() == 50
        assert "50 / 100" in dialog.label_detalle.text()

        # Actualizar a 100%
        dialog.actualizar_progreso(100, 100)
        assert dialog.progress_bar.value() == 100

    def test_actualizar_progreso_con_detalle(self, parent_widget, qtbot):
        """Actualizar progreso con mensaje de detalle personalizado."""
        dialog = ProgressDialog(parent=parent_widget)

        dialog.actualizar_progreso(25, 100, "Procesando item 25")
        assert dialog.progress_bar.value() == 25
        assert dialog.label_detalle.text() == "Procesando item 25"

    def test_set_mensaje(self, parent_widget, qtbot):
        """Cambiar mensaje principal."""
        dialog = ProgressDialog(parent=parent_widget, message="Original")

        assert "Original" in dialog.label_mensaje.text()

        dialog.set_mensaje("Nuevo mensaje")
        assert "Nuevo mensaje" in dialog.label_mensaje.text()

    def test_cancelar(self, parent_widget, qtbot):
        """Cancelar operación."""
        dialog = ProgressDialog(parent=parent_widget)

        assert not dialog.fue_cancelado()

        # Simular click en cancelar
        dialog._cancelar()

        assert dialog.fue_cancelado()
        assert "Cancelando" in dialog.label_mensaje.text()
        assert not dialog.btn_cancelar.isEnabled()

    def test_completar(self, parent_widget, qtbot):
        """Marcar operación como completada."""
        dialog = ProgressDialog(parent=parent_widget)

        dialog.completar("✓ Todo listo")

        assert dialog.progress_bar.value() == 100
        assert "✓ Todo listo" in dialog.label_mensaje.text()
        assert dialog.btn_cancelar.text() == "Cerrar"

    def test_progreso_con_rango_personalizado(self, parent_widget, qtbot):
        """Usar rango de progreso personalizado."""
        dialog = ProgressDialog(parent=parent_widget, minimum=0, maximum=50)

        assert dialog.progress_bar.minimum() == 0
        assert dialog.progress_bar.maximum() == 50

        dialog.actualizar_progreso(25, 50)
        assert dialog.progress_bar.value() == 50  # 50% de 50


# ========== TESTS WORKER THREAD ==========


class TestWorkerThread:
    """Tests para WorkerThread.

    Usamos waitSignal de qtbot para sincronización robusta.
    """

    def test_worker_ejecuta_funcion(self, qapp, qtbot, cleanup_threads):
        """Worker ejecuta función correctamente."""
        resultado_esperado = "resultado_test"

        def funcion_test(callback_progreso):
            callback_progreso(1, 1, "Test")
            return resultado_esperado

        worker = WorkerThread(funcion_test)
        cleanup_threads.append(worker)

        # Usar waitSignal para esperar de forma robusta
        with qtbot.waitSignal(worker.finalizado, timeout=5000) as blocker:
            worker.start()

        # Verificar resultado
        assert blocker.args[0] == resultado_esperado
        assert worker.isFinished()

    def test_worker_emite_progreso(self, qapp, qtbot, cleanup_threads):
        """Worker emite señales de progreso."""
        progreso_recibido = []

        def funcion_test(callback_progreso):
            for i in range(1, 4):
                callback_progreso(i, 3, f"Item {i}")
            return "ok"

        worker = WorkerThread(funcion_test)
        cleanup_threads.append(worker)
        worker.progreso.connect(lambda a, t, d: progreso_recibido.append((a, t, d)))

        # Esperar a que finalice
        with qtbot.waitSignal(worker.finalizado, timeout=5000):
            worker.start()

        # Procesar eventos pendientes para asegurar que las señales de progreso se recibieron
        qtbot.wait(50)

        assert len(progreso_recibido) == 3
        assert progreso_recibido[0] == (1, 3, "Item 1")
        assert progreso_recibido[1] == (2, 3, "Item 2")
        assert progreso_recibido[2] == (3, 3, "Item 3")

    def test_worker_maneja_error(self, qapp, qtbot, cleanup_threads):
        """Worker captura y emite excepciones."""

        def funcion_error(callback_progreso):
            raise ValueError("Error de prueba")

        worker = WorkerThread(funcion_error)
        cleanup_threads.append(worker)

        # Esperar señal de error
        with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
            worker.start()

        # Verificar error
        error = blocker.args[0]
        assert isinstance(error, ValueError)
        assert "Error de prueba" in str(error)

    def test_worker_con_argumentos(self, qapp, qtbot, cleanup_threads):
        """Worker pasa argumentos a la función."""

        def funcion_con_args(callback_progreso, x, y, z=0):
            callback_progreso(1, 1, "Test")
            return x + y + z

        worker = WorkerThread(funcion_con_args, 10, 20, z=5)
        cleanup_threads.append(worker)

        with qtbot.waitSignal(worker.finalizado, timeout=5000) as blocker:
            worker.start()

        assert blocker.args[0] == 35

    def test_worker_cancelacion(self, qapp, qtbot, cleanup_threads):
        """Worker puede ser cancelado."""
        import time

        def funcion_larga(callback_progreso):
            for i in range(100):
                callback_progreso(i, 100, f"Item {i}")
                time.sleep(0.01)  # Pequeña pausa para dar tiempo a cancelar
            return "completado"

        worker = WorkerThread(funcion_larga)
        cleanup_threads.append(worker)

        # Esperar señal de error (InterruptedError)
        with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
            worker.start()
            # Esperar un poco y luego cancelar
            qtbot.wait(50)
            worker.cancelar()

        # Debe haber emitido InterruptedError
        error = blocker.args[0]
        assert isinstance(error, InterruptedError)


# ========== TESTS EJECUTAR CON PROGRESO ==========


class TestEjecutarConProgreso:
    """Tests para ejecutar_con_progreso.

    Nota: ejecutar_con_progreso es complejo de testear por su naturaleza modal.
    Probamos el comportamiento indirectamente a través de mocks más específicos.
    """

    def test_worker_thread_con_args_y_kwargs(self, qapp, qtbot, cleanup_threads):
        """Verificar que WorkerThread procesa correctamente args y kwargs."""

        def funcion_con_params(callback_progreso, x, y, operacion="suma"):
            callback_progreso(1, 1, "Calculando...")
            if operacion == "suma":
                return x + y
            return x * y

        worker = WorkerThread(funcion_con_params, 5, 3, operacion="mult")
        cleanup_threads.append(worker)

        with qtbot.waitSignal(worker.finalizado, timeout=5000) as blocker:
            worker.start()

        assert blocker.args[0] == 15  # 5 * 3

    def test_progress_dialog_workflow_completo(self, parent_widget, qapp, qtbot):
        """Probar flujo completo del ProgressDialog sin usar ejecutar_con_progreso."""
        dialog = ProgressDialog(
            parent=parent_widget, title="Test Workflow", message="Iniciando...", show_details=True
        )

        # Simular progreso
        for i in range(1, 6):
            dialog.actualizar_progreso(i, 5, f"Paso {i} de 5")
            qtbot.wait(10)

        # Completar
        dialog.completar("✅ Finalizado")

        assert dialog.progress_bar.value() == 100
        assert "Finalizado" in dialog.label_mensaje.text()
        assert dialog.btn_cancelar.text() == "Cerrar"

    def test_progress_dialog_con_cancelacion(self, parent_widget, qapp, qtbot):
        """Probar cancelación del ProgressDialog."""
        dialog = ProgressDialog(
            parent=parent_widget, title="Test Cancelación", message="Procesando...", cancelable=True
        )

        # Cancelar
        dialog._cancelar()

        assert dialog.fue_cancelado()
        assert "Cancelando" in dialog.label_mensaje.text()
        assert not dialog.btn_cancelar.isEnabled()


# ========== TESTS DE INTEGRACIÓN REALISTAS ==========


class TestIntegracionProgressIndicators:
    """Tests de integración con escenarios realistas."""

    def test_simular_procesamiento_items(self, parent_widget, qapp, qtbot):
        """Simular procesamiento de múltiples items."""
        dialog = ProgressDialog(
            parent=parent_widget, title="Procesando Items", message="Cargando datos..."
        )

        items = list(range(10))

        for i, item in enumerate(items):
            if dialog.fue_cancelado():
                break

            # Simular trabajo
            qtbot.wait(10)

            # Actualizar progreso
            dialog.actualizar_progreso(i + 1, len(items), f"Procesando item {item}")

        dialog.completar()

        assert dialog.progress_bar.value() == 100

    def test_manejo_error_durante_procesamiento(self, qapp, qtbot, cleanup_threads):
        """Manejar error durante procesamiento."""

        def funcion_con_error(callback_progreso):
            callback_progreso(1, 3, "Paso 1")
            callback_progreso(2, 3, "Paso 2")
            raise RuntimeError("Error en paso 2")

        worker = WorkerThread(funcion_con_error)
        cleanup_threads.append(worker)

        with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
            worker.start()

        error = blocker.args[0]
        assert isinstance(error, RuntimeError)
        assert "Error en paso 2" in str(error)


# ========== TESTS DE PERFORMANCE ==========


class TestPerformanceProgressIndicators:
    """Tests de performance de los indicadores de progreso."""

    def test_actualizaciones_rapidas(self, parent_widget, qtbot):
        """Manejar actualizaciones rápidas de progreso."""
        dialog = ProgressDialog(parent=parent_widget)

        # Actualizar 1000 veces
        import time

        inicio = time.time()

        for i in range(1000):
            dialog.actualizar_progreso(i + 1, 1000)

        duracion = time.time() - inicio

        # Debe ser muy rápido (< 1 segundo)
        assert duracion < 1.0
        assert dialog.progress_bar.value() == 100

    def test_worker_con_muchos_items(self, qapp, qtbot, cleanup_threads):
        """Worker procesa muchos items eficientemente."""
        progreso_count = [0]

        def funcion_muchos_items(callback_progreso):
            for i in range(100):
                callback_progreso(i + 1, 100, f"Item {i}")
            return "ok"

        worker = WorkerThread(funcion_muchos_items)
        cleanup_threads.append(worker)
        worker.progreso.connect(
            lambda a, t, d: progreso_count.__setitem__(0, progreso_count[0] + 1)
        )

        import time

        inicio = time.time()

        with qtbot.waitSignal(worker.finalizado, timeout=5000):
            worker.start()

        duracion = time.time() - inicio

        # Procesar eventos pendientes
        qtbot.wait(50)

        # Debe procesar 100 items en menos de 2 segundos
        assert duracion < 2.0
        assert progreso_count[0] == 100
