"""Tests adicionales para core/observability/decorators.py y metrics.py."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.observability.metrics import MetricsCollector, MetricValue, MetricType
from core.observability.decorators import (
    count_calls,
    track_cache_access,
    track_database_query,
    track_errors,
    track_time,
)


# ---------------------------------------------------------------------------
# MetricsCollector
# ---------------------------------------------------------------------------
class TestMetricsCollectorExtra:
    def setup_method(self):
        with patch("core.observability.metrics.PROMETHEUS_AVAILABLE", False):
            self.m = MetricsCollector()
        self.m.clear_memory_store()

    def test_increment_counter_sin_labels(self):
        self.m.increment_counter("test_counter", 1.0)
        assert self.m._memory_counters.get("test_counter", 0) == 1.0

    def test_increment_counter_con_labels(self):
        self.m.increment_counter("op_total", 1.0, {"operation": "crear", "status": "ok"})
        key = "op_total:{'operation': 'crear', 'status': 'ok'}"
        assert self.m._memory_counters.get(key, 0) == 1.0

    def test_increment_counter_acumula(self):
        self.m.increment_counter("acc", 2.0)
        self.m.increment_counter("acc", 3.0)
        assert self.m._memory_counters["acc"] == 5.0

    def test_set_gauge_sin_labels(self):
        self.m.set_gauge("profesores_total", 42.0)
        assert self.m._memory_gauges.get("profesores_total") == 42.0

    def test_set_gauge_con_labels(self):
        self.m.set_gauge("gauged", 10.0, {"tipo": "A"})
        key = "gauged:{'tipo': 'A'}"
        assert self.m._memory_gauges.get(key) == 10.0

    def test_observe_histogram_sin_labels(self):
        self.m.observe_histogram("durations", 0.5)
        assert "durations" in self.m._memory_histograms
        assert 0.5 in self.m._memory_histograms["durations"]

    def test_observe_histogram_con_labels(self):
        self.m.observe_histogram("durations", 0.1, {"operation": "test"})
        key = "durations:{'operation': 'test'}"
        assert key in self.m._memory_histograms

    def test_timer_exito(self):
        with self.m.timer("operacion_test"):
            pass
        assert "operacion_test_duration" in self.m._memory_histograms

    def test_timer_excepcion_registra_y_relanza(self):
        with pytest.raises(ValueError):
            with self.m.timer("op_error"):
                raise ValueError("fallo")
        assert "op_error_duration" in self.m._memory_histograms

    def test_record_cache_hit(self):
        self.m.record_cache_hit("profesor")
        key = "app_cache_hits_total:{'cache_type': 'profesor'}"
        assert self.m._memory_counters.get(key, 0) == 1.0

    def test_record_cache_miss(self):
        self.m.record_cache_miss("zona")
        key = "app_cache_misses_total:{'cache_type': 'zona'}"
        assert self.m._memory_counters.get(key, 0) == 1.0

    def test_record_database_query_success(self):
        self.m.record_database_query("select", 0.01, success=True)
        key = "db_queries_total:{'query_type': 'select', 'status': 'success'}"
        assert self.m._memory_counters.get(key, 0) == 1.0

    def test_record_database_query_error(self):
        self.m.record_database_query("insert", 0.05, success=False)
        key = "db_queries_total:{'query_type': 'insert', 'status': 'error'}"
        assert self.m._memory_counters.get(key, 0) == 1.0

    def test_update_business_metrics_todos(self):
        self.m.update_business_metrics(
            profesores_count=10, guardias_count=50,
            guardias_hoy=5, ausencias_activas=3
        )
        assert self.m._memory_gauges.get("profesores_total") == 10.0
        assert self.m._memory_gauges.get("guardias_total") == 50.0
        assert self.m._memory_gauges.get("guardias_asignadas_hoy") == 5.0
        assert self.m._memory_gauges.get("ausencias_activas") == 3.0

    def test_update_business_metrics_ninguno(self):
        before = dict(self.m._memory_gauges)
        self.m.update_business_metrics()
        assert self.m._memory_gauges == before

    def test_get_metrics_text_devuelve_string(self):
        text = self.m.get_metrics_text()
        assert isinstance(text, str)

    def test_get_memory_store_devuelve_copia(self):
        self.m.increment_counter("test_store", 1.0)
        store = self.m.get_memory_store()
        assert len(store) >= 1
        assert all(isinstance(m, MetricValue) for m in store)

    def test_clear_memory_store_limpia_todo(self):
        self.m.increment_counter("tmp", 1.0)
        self.m.observe_histogram("h", 1.0)
        self.m.set_gauge("g", 1.0)
        self.m.clear_memory_store()
        assert len(self.m._memory_store) == 0
        assert len(self.m._memory_counters) == 0
        assert len(self.m._memory_gauges) == 0
        assert len(self.m._memory_histograms) == 0

    def test_get_summary_contiene_claves(self):
        summary = self.m.get_summary()
        assert "prometheus_available" in summary
        assert "memory_store_size" in summary

    def test_memory_store_limita_tamanio(self):
        self.m._max_memory_size = 5
        for i in range(10):
            self.m.increment_counter(f"metric_{i}", 1.0)
        assert len(self.m._memory_store) <= 5

    def test_update_system_metrics_no_lanza(self):
        # update_system_metrics requiere PROMETHEUS_AVAILABLE + psutil; sin ellos no lanza
        with patch("core.observability.metrics.PROMETHEUS_AVAILABLE", False):
            self.m.update_system_metrics()  # No debe lanzar


# ---------------------------------------------------------------------------
# MetricType y MetricValue
# ---------------------------------------------------------------------------
class TestMetricTypesExtra:
    def test_enum_counter(self):
        assert MetricType.COUNTER.value == "counter"

    def test_enum_histogram(self):
        assert MetricType.HISTOGRAM.value == "histogram"

    def test_metric_value_defaults(self):
        mv = MetricValue(name="test", value=5.0)
        assert mv.labels == {}
        assert mv.timestamp is not None


# ---------------------------------------------------------------------------
# Decorador track_time
# ---------------------------------------------------------------------------
class TestTrackTimeExtra:
    def setup_method(self):
        with patch("core.observability.metrics.PROMETHEUS_AVAILABLE", False):
            self.metrics = MetricsCollector()

    def test_funcion_retorna_valor(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_time("op_test")
            def mi_funcion(x, y):
                return x + y

            assert mi_funcion(2, 3) == 5

    def test_con_excepcion_registra_y_relanza(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_time("op_exc")
            def falla():
                raise ValueError("error esperado")

            with pytest.raises(ValueError, match="error esperado"):
                falla()

    def test_sin_nombre_infiere_desde_funcion(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_time()
            def operacion_sin_nombre():
                return True

            assert operacion_sin_nombre() is True

    def test_preserva_metadatos_funcion(self):
        @track_time("irrelevante")
        def funcion_con_docstring():
            """Docstring."""
            pass

        assert funcion_con_docstring.__name__ == "funcion_con_docstring"


# ---------------------------------------------------------------------------
# Decorador count_calls
# ---------------------------------------------------------------------------
class TestCountCallsExtra:
    def setup_method(self):
        with patch("core.observability.metrics.PROMETHEUS_AVAILABLE", False):
            self.metrics = MetricsCollector()

    def test_exito_incrementa_success(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @count_calls()
            def op():
                return "ok"

            op()
        key = "app_requests_total:{'operation': 'op', 'status': 'success'}"
        assert self.metrics._memory_counters.get(key, 0) == 1.0

    def test_error_incrementa_error(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @count_calls()
            def op_error():
                raise RuntimeError("boom")

            with pytest.raises(RuntimeError):
                op_error()
        key = "app_requests_total:{'operation': 'op_error', 'status': 'error'}"
        assert self.metrics._memory_counters.get(key, 0) == 1.0


# ---------------------------------------------------------------------------
# Decorador track_errors
# ---------------------------------------------------------------------------
class TestTrackErrorsExtra:
    def setup_method(self):
        with patch("core.observability.metrics.PROMETHEUS_AVAILABLE", False):
            self.metrics = MetricsCollector()

    def test_sin_error_devuelve_valor(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_errors("mi_op")
            def sin_error():
                return 99

            assert sin_error() == 99

    def test_con_error_registra_en_metrics(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_errors("op_con_error")
            def con_error():
                raise TypeError("tipo incorrecto")

            with pytest.raises(TypeError):
                con_error()
        assert any("app_errors_total" in k for k in self.metrics._memory_counters)

    def test_sin_nombre_usa_funcion(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_errors()
            def mi_func():
                raise ValueError("x")

            with pytest.raises(ValueError):
                mi_func()


# ---------------------------------------------------------------------------
# Decorador track_database_query
# ---------------------------------------------------------------------------
class TestTrackDatabaseQueryExtra:
    def setup_method(self):
        with patch("core.observability.metrics.PROMETHEUS_AVAILABLE", False):
            self.metrics = MetricsCollector()

    def test_select_exitoso(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_database_query("select")
            def query():
                return [1, 2]

            assert query() == [1, 2]
        assert any("db_queries_total" in k and "success" in k
                   for k in self.metrics._memory_counters)

    def test_insert_con_error(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_database_query("insert")
            def query_falla():
                raise Exception("BD caída")

            with pytest.raises(Exception):
                query_falla()
        assert any("db_queries_total" in k and "error" in k
                   for k in self.metrics._memory_counters)


# ---------------------------------------------------------------------------
# Decorador track_cache_access
# ---------------------------------------------------------------------------
class TestTrackCacheAccessExtra:
    def setup_method(self):
        with patch("core.observability.metrics.PROMETHEUS_AVAILABLE", False):
            self.metrics = MetricsCollector()

    def test_resultado_no_none_es_hit(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_cache_access("profesor")
            def get_val():
                return "cached_value"

            assert get_val() == "cached_value"
        key = "app_cache_hits_total:{'cache_type': 'profesor'}"
        assert self.metrics._memory_counters.get(key, 0) == 1.0

    def test_resultado_none_es_miss(self):
        with patch("core.observability.decorators.get_metrics", return_value=self.metrics):
            @track_cache_access("zona")
            def get_none():
                return None

            get_none()
        key = "app_cache_misses_total:{'cache_type': 'zona'}"
        assert self.metrics._memory_counters.get(key, 0) == 1.0
