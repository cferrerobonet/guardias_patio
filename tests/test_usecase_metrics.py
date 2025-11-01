"""
Tests para verificar que los use cases instrumentados con `with_metrics`
registran las métricas apropiadas.

Se testea `ObtenerEstadisticasUseCase` en ruta de éxito y en ruta de error.
"""
import core.observability.decorators as obs_decorators
import pytest
from application.use_cases.asignacion_guardias.obtener_estadisticas import (
    ObtenerEstadisticasUseCase,
)


class DummyMetrics:
    def __init__(self):
        self.histograms = []
        self.counters = []

    def observe_histogram(self, name, value, labels=None):
        self.histograms.append((name, value, labels))

    def increment_counter(self, name, amount, labels=None):
        self.counters.append((name, amount, labels))

    def has_counter(self, name, status=None):
        for n, amt, labels in self.counters:
            if n == name:
                if status is None:
                    return True
                if labels and labels.get("status") == status:
                    return True
        return False


class DummySession:
    def __init__(self, stats):
        self._stats = stats


def test_obtener_estadisticas_success(monkeypatch):
    metrics = DummyMetrics()
    monkeypatch.setattr(obs_decorators, "get_metrics", lambda: metrics)

    # Mock the service function to return a valid stats dict
    def fake_service(session):
        return {"dias_lectivos": 100, "slots_totales": 200}

    monkeypatch.setattr(
        "application.use_cases.asignacion_guardias.obtener_estadisticas.obtener_stats_servicio",
        fake_service,
    )

    from sqlalchemy.orm import Session

    uc = ObtenerEstadisticasUseCase(Session())

    res = uc.execute()
    assert res.dias_lectivos == 100

    assert any(h[0] == "app_request_duration_seconds" for h in metrics.histograms)
    assert metrics.has_counter("app_requests_total", status="success")


def test_obtener_estadisticas_error(monkeypatch):
    metrics = DummyMetrics()
    monkeypatch.setattr(obs_decorators, "get_metrics", lambda: metrics)

    # Mock the service function to return falsy (simulate no config)
    def fake_service_empty(session):
        return None

    monkeypatch.setattr(
        "application.use_cases.asignacion_guardias.obtener_estadisticas.obtener_stats_servicio",
        fake_service_empty,
    )

    from core.exceptions import BusinessLogicError
    from sqlalchemy.orm import Session

    uc = ObtenerEstadisticasUseCase(Session())

    with pytest.raises(BusinessLogicError):
        uc.execute()

    assert metrics.has_counter("app_requests_total", status="error")
