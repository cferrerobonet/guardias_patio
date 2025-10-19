"""
Core Observability Module

Sistema centralizado de observabilidad para monitoreo, métricas y salud
de la aplicación Guardias de Patio.
"""

from .decorators import count_calls, track_errors, track_time, with_metrics
from .health import HealthChecker, HealthStatus
from .metrics import MetricsCollector, get_metrics
from .performance import PerformanceMonitor, get_performance_monitor

__all__ = [
    # Metrics
    "MetricsCollector",
    "get_metrics",
    # Health
    "HealthChecker",
    "HealthStatus",
    # Performance
    "PerformanceMonitor",
    "get_performance_monitor",
    # Decorators
    "track_time",
    "count_calls",
    "track_errors",
    "with_metrics",
]
