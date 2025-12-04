"""
Tests para el sistema de monitoreo de performance.
"""

from datetime import datetime

import pytest

from src.core.observability.performance import (
    PerformanceMonitor,
    PerformanceRecord,
    PerformanceStats,
    get_performance_monitor,
)


class TestPerformanceMonitor:
    """Tests para PerformanceMonitor."""

    @pytest.fixture
    def monitor(self):
        """Fixture que proporciona un PerformanceMonitor limpio."""
        mon = PerformanceMonitor(
            slow_threshold_ms=100,
            very_slow_threshold_ms=500,
            max_records=50,
        )
        return mon

    def test_record_fast_operation(self, monitor):
        """Test registrar operación rápida."""
        monitor.record_operation("fast_op", 50.0)

        summary = monitor.get_summary()
        assert summary["total_operations"] == 1
        assert summary["slow_operations"] == 0
        assert summary["slow_percentage"] == 0

    def test_record_slow_operation(self, monitor):
        """Test registrar operación lenta."""
        monitor.record_operation("slow_op", 150.0)

        summary = monitor.get_summary()
        assert summary["total_operations"] == 1
        assert summary["slow_operations"] == 1
        assert summary["slow_percentage"] == 100

        # Verificar que hay alerta (aunque no very_slow)
        slow_ops = monitor.get_slow_operations()
        assert len(slow_ops) == 1
        assert slow_ops[0].operation == "slow_op"
        assert slow_ops[0].is_slow is True

    def test_record_very_slow_operation(self, monitor):
        """Test registrar operación muy lenta genera alerta."""
        monitor.record_operation("very_slow_op", 600.0)

        alerts = monitor.get_alerts()
        assert len(alerts) == 1
        assert "muy lenta" in alerts[0].lower()
        assert "very_slow_op" in alerts[0]

    def test_record_query(self, monitor):
        """Test registrar queries a BD."""
        monitor.record_query("select", "profesores", 25.0)
        monitor.record_query("insert", "guardias", 30.0)

        summary = monitor.get_summary()
        assert summary["total_operations"] == 2
        assert summary["tracked_operation_types"] == 2

    def test_get_slow_operations_limit(self, monitor):
        """Test limitar operaciones lentas retornadas."""
        # Crear muchas operaciones lentas
        for i in range(20):
            monitor.record_operation(f"op_{i}", 100 + i * 10)

        slow_ops = monitor.get_slow_operations(limit=5)
        assert len(slow_ops) <= 5

        # Verificar que están ordenadas por duración (descendente)
        for i in range(len(slow_ops) - 1):
            assert slow_ops[i].duration_ms >= slow_ops[i + 1].duration_ms

    def test_get_slow_operations_time_window(self, monitor):
        """Test filtrar operaciones lentas por ventana de tiempo."""
        # Esta funcionalidad es limitada sin control del tiempo,
        # pero podemos verificar que funciona
        monitor.record_operation("slow_op", 150.0)

        # Buscar en ventana amplia (debería encontrar)
        slow_ops = monitor.get_slow_operations(minutes=60)
        assert len(slow_ops) == 1

        # Buscar en ventana de 0 minutos (no debería encontrar nada)
        slow_ops = monitor.get_slow_operations(minutes=0)
        assert len(slow_ops) == 0

    def test_get_operation_stats(self, monitor):
        """Test obtener estadísticas de operación."""
        # Registrar varias ejecuciones de la misma operación
        durations = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for dur in durations:
            monitor.record_operation("test_op", dur)

        stats = monitor.get_operation_stats("test_op")

        assert stats is not None
        assert stats.operation == "test_op"
        assert stats.count == 10
        assert stats.total_duration_ms == 550
        assert stats.avg_duration_ms == 55
        assert stats.min_duration_ms == 10
        assert stats.max_duration_ms == 100
        # Con 10 elementos, p50 usa índice 5 (valor 60), p95 usa índice 9, p99 usa índice 9
        assert stats.p50_duration_ms == 60
        assert stats.p95_duration_ms == 100
        assert stats.p99_duration_ms == 100
        assert stats.slow_operations == 1  # Solo 100ms es >= 100

    def test_get_operation_stats_nonexistent(self, monitor):
        """Test estadísticas de operación inexistente."""
        stats = monitor.get_operation_stats("nonexistent")
        assert stats is None

    def test_get_all_operations_stats(self, monitor):
        """Test obtener estadísticas de todas las operaciones."""
        monitor.record_operation("op1", 50)
        monitor.record_operation("op1", 60)
        monitor.record_operation("op2", 100)
        monitor.record_operation("op2", 110)
        monitor.record_operation("op3", 200)

        all_stats = monitor.get_all_operations_stats()

        assert len(all_stats) == 3

        # Verificar que están ordenadas por duración promedio (descendente)
        assert all_stats[0].operation == "op3"  # avg=200
        assert all_stats[1].operation == "op2"  # avg=105
        assert all_stats[2].operation == "op1"  # avg=55

    def test_check_degradation_with_insufficient_data(self, monitor):
        """Test degradación sin suficientes datos históricos."""
        # Solo 5 registros (< 10 requeridos)
        for _ in range(5):
            monitor.record_operation("test_op", 50)

        # No debería detectar degradación con pocos datos
        is_degraded = monitor.check_degradation("test_op", 200)
        assert is_degraded is False

    def test_check_degradation_detected(self, monitor):
        """Test detección de degradación."""
        # Crear historial con promedio de 50ms
        for _ in range(15):
            monitor.record_operation("test_op", 50)

        # Operación actual es 3x más lenta (150ms vs 50ms promedio)
        # Umbral es 50 * 1.5 = 75, así que 150 > 75 = degradación
        is_degraded = monitor.check_degradation("test_op", 150)
        assert is_degraded is True

        alerts = monitor.get_alerts()
        assert len(alerts) > 0
        assert "degradación" in alerts[0].lower()

    def test_check_degradation_not_detected(self, monitor):
        """Test no detectar degradación cuando está dentro del rango."""
        # Crear historial con promedio de 100ms
        for _ in range(15):
            monitor.record_operation("test_op", 100)

        # Operación actual: 130ms
        # Umbral: 100 * 1.5 = 150, así que 130 < 150 = NO degradación
        is_degraded = monitor.check_degradation("test_op", 130)
        assert is_degraded is False

    def test_max_records_limit(self, monitor):
        """Test límite máximo de registros."""
        # Configurado con max_records=50
        # Crear más registros
        for i in range(100):
            monitor.record_operation(f"op_{i}", 50)

        summary = monitor.get_summary()
        # Solo debería mantener los últimos 50
        assert summary["total_operations"] == 50

    def test_get_alerts_with_clear(self, monitor):
        """Test obtener y limpiar alertas."""
        monitor.record_operation("very_slow", 600)  # Genera alerta
        monitor.record_operation("very_slow", 700)  # Genera otra alerta

        alerts = monitor.get_alerts(clear=False)
        assert len(alerts) == 2

        # Las alertas aún deberían estar ahí
        alerts2 = monitor.get_alerts(clear=False)
        assert len(alerts2) == 2

        # Ahora limpiar
        alerts3 = monitor.get_alerts(clear=True)
        assert len(alerts3) == 2

        # Ya no debería haber alertas
        alerts4 = monitor.get_alerts()
        assert len(alerts4) == 0

    def test_reset_stats(self, monitor):
        """Test resetear todas las estadísticas."""
        monitor.record_operation("op1", 50)
        monitor.record_operation("op2", 100)
        monitor.record_query("select", "test", 25)

        summary = monitor.get_summary()
        assert summary["total_operations"] > 0
        assert summary["tracked_operation_types"] > 0

        monitor.reset_stats()

        summary = monitor.get_summary()
        assert summary["total_operations"] == 0
        assert summary["tracked_operation_types"] == 0
        assert summary["active_alerts"] == 0

    def test_get_performance_monitor_singleton(self):
        """Test que get_performance_monitor retorna singleton."""
        mon1 = get_performance_monitor()
        mon2 = get_performance_monitor()

        assert mon1 is mon2

        # Cambios en una instancia afectan a la otra
        mon1.record_operation("test", 100)
        summary = mon2.get_summary()
        assert summary["total_operations"] >= 1

    def test_performance_record_dataclass(self):
        """Test PerformanceRecord dataclass."""
        record = PerformanceRecord(
            operation="test_op",
            duration_ms=123.45,
            timestamp=datetime.now(),
            metadata={"key": "value"},
            is_slow=True,
        )

        assert record.operation == "test_op"
        assert record.duration_ms == 123.45
        assert record.is_slow is True
        assert record.metadata["key"] == "value"

    def test_performance_stats_dataclass(self):
        """Test PerformanceStats dataclass."""
        stats = PerformanceStats(
            operation="test_op",
            count=100,
            total_duration_ms=5000,
            avg_duration_ms=50,
            min_duration_ms=10,
            max_duration_ms=200,
            p50_duration_ms=45,
            p95_duration_ms=150,
            p99_duration_ms=180,
            slow_operations=5,
        )

        assert stats.operation == "test_op"
        assert stats.count == 100
        assert stats.avg_duration_ms == 50
        assert stats.slow_operations == 5

    def test_multiple_operations_summary(self, monitor):
        """Test resumen con múltiples tipos de operaciones."""
        # Operaciones rápidas
        for _ in range(7):
            monitor.record_operation("fast", 30)

        # Operaciones lentas
        for _ in range(3):
            monitor.record_operation("slow", 150)

        summary = monitor.get_summary()

        assert summary["total_operations"] == 10
        assert summary["slow_operations"] == 3
        assert summary["slow_percentage"] == 30
        assert summary["tracked_operation_types"] == 2
