"""
Tests para el decorador `with_metrics`.

Verifica que en la ruta de éxito se registren las métricas correspondientes
y que en la ruta de error también se registren los contadores de error.
"""
import pytest

import core.observability.decorators as obs_decorators


class DummyMetrics:
    def __init__(self):
        self.histograms = []
        self.counters = []

    def observe_histogram(self, name, value, labels=None):
        self.histograms.append((name, value, labels))

    def increment_counter(self, name, amount, labels=None):
        self.counters.append((name, amount, labels))

    # helpers for assertions
    def has_counter(self, name, status=None):
        for n, amt, labels in self.counters:
            if n == name:
                if status is None:
                    return True
                if labels and labels.get("status") == status:
                    return True
        return False


def test_with_metrics_success(monkeypatch):
    metrics = DummyMetrics()
    monkeypatch.setattr(obs_decorators, "get_metrics", lambda: metrics)

    @obs_decorators.with_metrics("op_test_success")
    def func(x, y=0):
        return x + y

    res = func(2, y=3)
    assert res == 5

    # Verificar que se registró histograma y contador de success
    assert any(h[0] == "app_request_duration_seconds" for h in metrics.histograms)
    assert metrics.has_counter("app_requests_total", status="success")


def test_with_metrics_error(monkeypatch):
    metrics = DummyMetrics()
    monkeypatch.setattr(obs_decorators, "get_metrics", lambda: metrics)

    @obs_decorators.with_metrics("op_test_error")
    def func_err():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        func_err()

    # Debe haberse registrado contador de error y app_errors_total
    assert metrics.has_counter("app_requests_total", status="error")
    assert any(c[0] == "app_errors_total" for c in metrics.counters)
