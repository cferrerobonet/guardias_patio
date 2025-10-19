"""
Tests para el sistema de métricas de observabilidad.
"""

import pytest
from prometheus_client import REGISTRY

from src.core.observability.metrics import MetricsCollector, get_metrics


class TestMetricsCollector:
    """Tests para MetricsCollector."""

    @pytest.fixture(autouse=True)
    def cleanup_registry(self):
        """Limpia el registry de Prometheus antes de cada test."""
        # Limpiar collectors existentes
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass
        yield
        # Limpiar después del test también
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass

    @pytest.fixture
    def metrics(self):
        """Fixture que proporciona un MetricsCollector."""
        return MetricsCollector()

    def test_increment_counter(self, metrics):
        """Test incrementar contador."""
        metrics.increment_counter("test_counter")
        metrics.increment_counter("test_counter")
        metrics.increment_counter("test_counter", value=3)

        stats = metrics.get_stats()
        assert "test_counter" in stats["counters"]
        assert stats["counters"]["test_counter"] == 5

    def test_set_gauge(self, metrics):
        """Test actualizar gauge."""
        metrics.set_gauge("test_gauge", 42)
        stats = metrics.get_stats()
        assert stats["gauges"]["test_gauge"] == 42

        metrics.set_gauge("test_gauge", 100)
        stats = metrics.get_stats()
        assert stats["gauges"]["test_gauge"] == 100

    def test_observe_histogram(self, metrics):
        """Test observar valores en histograma."""
        metrics.observe_histogram("test_histogram", 10)
        metrics.observe_histogram("test_histogram", 20)
        metrics.observe_histogram("test_histogram", 30)

        stats = metrics.get_stats()
        assert "test_histogram" in stats["histograms"]
        assert stats["histograms"]["test_histogram"]["count"] == 3
        assert stats["histograms"]["test_histogram"]["sum"] == 60

    def test_timer_context_manager(self, metrics):
        """Test timer como context manager."""
        import time

        with metrics.timer("test_operation"):
            time.sleep(0.01)  # Sleep 10ms

        stats = metrics.get_stats()
        assert "test_operation_duration" in stats["histograms"]
        assert stats["histograms"]["test_operation_duration"]["count"] == 1
        # Duración debería ser ~10ms
        duration = stats["histograms"]["test_operation_duration"]["sum"]
        assert 5 < duration < 50  # Rango amplio por variabilidad

    def test_track_database_query(self, metrics):
        """Test tracking de queries."""
        metrics.track_database_query("select", 15.5)
        metrics.track_database_query("insert", 25.0)
        metrics.track_database_query("select", 10.0)

        stats = metrics.get_stats()

        # Verificar contadores
        assert stats["counters"]["database_queries_total"] == 3

        # Verificar histograma
        assert "database_query_duration" in stats["histograms"]
        assert stats["histograms"]["database_query_duration"]["count"] == 3

    def test_track_cache_operation(self, metrics):
        """Test tracking de operaciones de cache."""
        metrics.track_cache_operation("hit")
        metrics.track_cache_operation("hit")
        metrics.track_cache_operation("miss")

        stats = metrics.get_stats()

        assert stats["counters"]["cache_operations_total"] == 3
        assert stats["gauges"]["cache_hit_rate"] == pytest.approx(0.666, abs=0.01)

    def test_track_business_metrics(self, metrics):
        """Test métricas de negocio."""
        metrics.track_business_metric("profesores_activos", 25)
        metrics.track_business_metric("guardias_asignadas", 150)

        stats = metrics.get_stats()

        assert stats["gauges"]["profesores_activos"] == 25
        assert stats["gauges"]["guardias_asignadas"] == 150

    def test_track_system_resources(self, metrics):
        """Test tracking de recursos del sistema."""
        metrics.track_system_resources()

        stats = metrics.get_stats()

        # Verificar que se registraron las métricas de sistema
        assert "system_memory_bytes" in stats["gauges"]
        assert "system_cpu_percent" in stats["gauges"]

        # Los valores deben ser positivos
        assert stats["gauges"]["system_memory_bytes"] > 0
        assert stats["gauges"]["system_cpu_percent"] >= 0

    def test_get_prometheus_metrics(self, metrics):
        """Test exportación en formato Prometheus."""
        metrics.increment_counter("test_counter", value=5)
        metrics.set_gauge("test_gauge", 42)

        prom_text = metrics.get_prometheus_metrics()

        assert "test_counter 5" in prom_text
        assert "test_gauge 42" in prom_text
        assert "# TYPE" in prom_text

    def test_reset_metrics(self, metrics):
        """Test resetear métricas."""
        metrics.increment_counter("test")
        metrics.set_gauge("test_gauge", 100)
        metrics.observe_histogram("test_hist", 50)

        stats = metrics.get_stats()
        assert len(stats["counters"]) > 0
        assert len(stats["gauges"]) > 0
        assert len(stats["histograms"]) > 0

        metrics.reset_metrics()

        stats = metrics.get_stats()
        assert len(stats["counters"]) == 0
        assert len(stats["gauges"]) == 0
        assert len(stats["histograms"]) == 0

    def test_get_metrics_singleton(self):
        """Test que get_metrics retorna singleton."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

        # Cambios en una instancia afectan a la otra
        metrics1.increment_counter("test")
        stats = metrics2.get_stats()
        assert stats["counters"]["test"] == 1

    def test_multiple_operations(self, metrics):
        """Test múltiples operaciones combinadas."""
        # Simular flujo real
        metrics.increment_counter("app_starts")

        with metrics.timer("load_data"):
            metrics.track_database_query("select", 45.2)
            metrics.track_cache_operation("miss")
            metrics.track_cache_operation("hit")

        metrics.track_business_metric("profesores_activos", 30)
        metrics.track_system_resources()

        stats = metrics.get_stats()

        # Verificar que todo se registró
        assert stats["counters"]["app_starts"] == 1
        assert stats["counters"]["database_queries_total"] == 1
        assert stats["counters"]["cache_operations_total"] == 2
        assert stats["gauges"]["profesores_activos"] == 30
        assert "load_data_duration" in stats["histograms"]
