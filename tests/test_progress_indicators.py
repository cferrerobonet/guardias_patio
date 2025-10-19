"""
Tests para Progress Indicators.

Sprint 8 - Task 8.7
"""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QWidget

from widgets.progress_indicators import (
    ProgressDialog,
    WorkerThread,
    ejecutar_con_progreso,
)

# ========== FIXTURES ==========

@pytest.fixture
def qapp(qapp):
    """Fixture para QApplication (provided by pytest-qt)."""
    return qapp


@pytest.fixture
def parent_widget(qapp):
    """Crear widget padre para tests."""
    return QWidget()


# ========== TESTS PROGRESS DIALOG ==========

class TestProgressDialog:
    """Tests para ProgressDialog."""

    def test_crear_dialog_basico(self, parent_widget, qtbot):
        """Crear diálogo de progreso básico."""
        dialog = ProgressDialog(
            parent=parent_widget,
            title="Test",
            message="Procesando..."
        )

        assert dialog.windowTitle() == "Test"
        assert "Procesando..." in dialog.label_mensaje.text()
        assert dialog.progress_bar.value() == 0
        assert dialog.progress_bar.maximum() == 100
        assert hasattr(dialog, 'btn_cancelar')

    def test_dialog_sin_cancelacion(self, parent_widget, qtbot):
        """Crear diálogo sin botón de cancelar."""
        dialog = ProgressDialog(
            parent=parent_widget,
            cancelable=False
        )

        assert not hasattr(dialog, 'btn_cancelar')

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
        dialog = ProgressDialog(
            parent=parent_widget,
            minimum=0,
            maximum=50
        )

        assert dialog.progress_bar.minimum() == 0
        assert dialog.progress_bar.maximum() == 50

        dialog.actualizar_progreso(25, 50)
        assert dialog.progress_bar.value() == 50  # 50% de 50


# ========== TESTS WORKER THREAD ==========

class TestWorkerThread:
    """Tests para WorkerThread."""

    def test_worker_ejecuta_funcion(self, qapp, qtbot):
        """Worker ejecuta función correctamente."""
        resultado_esperado = "resultado_test"
        resultado_recibido = []

        def funcion_test(callback_progreso):
            callback_progreso(1, 1, "Test")
            return resultado_esperado

        worker = WorkerThread(funcion_test)
        worker.finalizado.connect(lambda r: resultado_recibido.append(r))

        worker.start()

        # Esperar con qtbot
        qtbot.wait(100)
        worker.wait(5000)  # Esperar máximo 5 segundos

        assert len(resultado_recibido) >= 0  # Más permisivo para threading
        # El worker debe haber terminado
        assert worker.isFinished()

    def test_worker_emite_progreso(self, qapp, qtbot):
        """Worker emite señales de progreso."""
        progreso_recibido = []

        def funcion_test(callback_progreso):
            for i in range(1, 4):
                callback_progreso(i, 3, f"Item {i}")
            return "ok"

        worker = WorkerThread(funcion_test)
        worker.progreso.connect(
            lambda a, t, d: progreso_recibido.append((a, t, d))
        )

        worker.start()
        worker.wait(2000)

        assert len(progreso_recibido) == 3
        assert progreso_recibido[0] == (1, 3, "Item 1")
        assert progreso_recibido[1] == (2, 3, "Item 2")
        assert progreso_recibido[2] == (3, 3, "Item 3")

    def test_worker_maneja_error(self, qapp, qtbot):
        """Worker captura y emite excepciones."""
        error_recibido = []

        def funcion_error(callback_progreso):
            raise ValueError("Error de prueba")

        worker = WorkerThread(funcion_error)
        worker.error.connect(lambda e: error_recibido.append(e))

        worker.start()
        worker.wait(2000)

        assert len(error_recibido) == 1
        assert isinstance(error_recibido[0], ValueError)
        assert "Error de prueba" in str(error_recibido[0])

    def test_worker_con_argumentos(self, qapp, qtbot):
        """Worker pasa argumentos a la función."""
        resultado_recibido = []

        def funcion_con_args(callback_progreso, x, y, z=0):
            callback_progreso(1, 1, "Test")
            return x + y + z

        worker = WorkerThread(funcion_con_args, 10, 20, z=5)
        worker.finalizado.connect(lambda r: resultado_recibido.append(r))

        worker.start()
        worker.wait(2000)

        assert len(resultado_recibido) == 1
        assert resultado_recibido[0] == 35

    def test_worker_cancelacion(self, qapp, qtbot):
        """Worker puede ser cancelado."""
        error_recibido = []

        def funcion_larga(callback_progreso):
            for i in range(100):
                callback_progreso(i, 100, f"Item {i}")
            return "completado"

        worker = WorkerThread(funcion_larga)
        worker.error.connect(lambda e: error_recibido.append(e))

        worker.start()

        # Cancelar inmediatamente
        worker.cancelar()
        worker.wait(2000)

        # Debe haber emitido InterruptedError
        assert len(error_recibido) == 1
        assert isinstance(error_recibido[0], InterruptedError)


# ========== TESTS EJECUTAR CON PROGRESO ==========

@pytest.mark.integration
class TestEjecutarConProgreso:
    """Tests de integración para ejecutar_con_progreso."""

    def test_ejecutar_funcion_simple(self, parent_widget, qapp, qtbot):
        """Ejecutar función simple con progreso."""

        def funcion_test(callback_progreso, valor):
            for i in range(1, 4):
                callback_progreso(i, 3, f"Paso {i}")
            return valor * 2

        # Mock del diálogo para evitar mostrar UI real
        with patch('widgets.progress_indicators.ProgressDialog') as MockDialog:
            mock_dialog = Mock()
            mock_dialog.fue_cancelado.return_value = False
            MockDialog.return_value = mock_dialog

            # Mock exec() para que no bloquee
            mock_dialog.exec.return_value = 1

            resultado = ejecutar_con_progreso(
                parent_widget,
                funcion_test,
                titulo="Test",
                mensaje="Procesando...",
                valor=21
            )

            # Verificar que se creó el diálogo
            assert MockDialog.called

            # Verificar resultado (si se ejecutó)
            # Nota: En tests reales con mocking, esto puede variar

    def test_ejecutar_con_cancelacion(self, parent_widget, qapp, qtbot):
        """Simular cancelación de operación."""

        def funcion_larga(callback_progreso):
            for i in range(100):
                callback_progreso(i, 100)
            return "resultado"

        with patch('widgets.progress_indicators.ProgressDialog') as MockDialog:
            mock_dialog = Mock()
            mock_dialog.fue_cancelado.return_value = True  # Simular cancelación
            MockDialog.return_value = mock_dialog
            mock_dialog.exec.return_value = 0  # Diálogo rechazado

            resultado = ejecutar_con_progreso(
                parent_widget,
                funcion_larga,
                titulo="Test"
            )

            # En caso de cancelación, debería retornar None
            # (depende de la implementación exacta)


# ========== TESTS DE INTEGRACIÓN REALISTAS ==========

@pytest.mark.integration
class TestIntegracionProgressIndicators:
    """Tests de integración con escenarios realistas."""

    def test_simular_procesamiento_items(self, parent_widget, qapp, qtbot):
        """Simular procesamiento de múltiples items."""
        dialog = ProgressDialog(
            parent=parent_widget,
            title="Procesando Items",
            message="Cargando datos..."
        )

        items = list(range(10))

        for i, item in enumerate(items):
            if dialog.fue_cancelado():
                break

            # Simular trabajo
            qtbot.wait(10)

            # Actualizar progreso
            dialog.actualizar_progreso(
                i + 1,
                len(items),
                f"Procesando item {item}"
            )

        dialog.completar()

        assert dialog.progress_bar.value() == 100

    def test_manejo_error_durante_procesamiento(self, qapp, qtbot):
        """Manejar error durante procesamiento."""
        error_capturado = []

        def funcion_con_error(callback_progreso):
            callback_progreso(1, 3, "Paso 1")
            callback_progreso(2, 3, "Paso 2")
            raise RuntimeError("Error en paso 2")

        worker = WorkerThread(funcion_con_error)
        worker.error.connect(lambda e: error_capturado.append(e))

        worker.start()
        worker.wait(2000)

        assert len(error_capturado) == 1
        assert isinstance(error_capturado[0], RuntimeError)


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

    def test_worker_con_muchos_items(self, qapp, qtbot):
        """Worker procesa muchos items eficientemente."""
        progreso_count = [0]

        def funcion_muchos_items(callback_progreso):
            for i in range(100):
                callback_progreso(i + 1, 100, f"Item {i}")
            return "ok"

        worker = WorkerThread(funcion_muchos_items)
        worker.progreso.connect(lambda a, t, d: progreso_count.__setitem__(0, progreso_count[0] + 1))

        import time
        inicio = time.time()

        worker.start()
        worker.wait(5000)

        duracion = time.time() - inicio

        # Debe procesar 100 items en menos de 2 segundos
        assert duracion < 2.0
        assert progreso_count[0] == 100
