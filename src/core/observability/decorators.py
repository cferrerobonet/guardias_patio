"""
Decoradores para Observabilidad

Decoradores que facilitan el tracking automático de métricas
en funciones y métodos sin acoplamiento directo.
"""

import functools
import time
from typing import Callable, Optional

from utils.logger import get_logger

from .metrics import get_metrics

logger = get_logger(__name__)


def track_time(operation_name: Optional[str] = None):
    """
    Decorador que mide el tiempo de ejecución de una función.

    Args:
        operation_name: Nombre de la operación (usa nombre de función si None)

    Usage:
        @track_time("crear_profesor")
        def crear_profesor(data):
            pass

        @track_time()  # Usa nombre de función
        def actualizar_profesor(id, data):
            pass
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Registrar métricas de éxito
                metrics.observe_histogram(
                    "app_request_duration_seconds",
                    duration,
                    {"operation": op_name},
                )
                metrics.increment_counter(
                    "app_requests_total",
                    1.0,
                    {"operation": op_name, "status": "success"},
                )

                logger.debug(
                    f"⏱️  {op_name} ejecutado en {duration*1000:.2f}ms",
                    extra={
                        "operation": op_name,
                        "duration_ms": duration * 1000,
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Registrar métricas de error
                metrics.observe_histogram(
                    "app_request_duration_seconds",
                    duration,
                    {"operation": op_name},
                )
                metrics.increment_counter(
                    "app_requests_total",
                    1.0,
                    {"operation": op_name, "status": "error"},
                )
                metrics.increment_counter(
                    "app_errors_total",
                    1.0,
                    {"error_type": type(e).__name__, "operation": op_name},
                )

                logger.error(
                    f"❌ {op_name} falló después de {duration*1000:.2f}ms",
                    extra={
                        "operation": op_name,
                        "duration_ms": duration * 1000,
                        "error_type": type(e).__name__,
                    },
                    exc_info=e,
                )

                raise

        return wrapper

    return decorator


def count_calls(metric_name: Optional[str] = None):
    """
    Decorador que cuenta las llamadas a una función.

    Args:
        metric_name: Nombre de la métrica (usa nombre de función si None)

    Usage:
        @count_calls("profesor_creado")
        def crear_profesor(data):
            pass
    """

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()

            try:
                result = func(*args, **kwargs)
                metrics.increment_counter(
                    "app_requests_total",
                    1.0,
                    {"operation": func.__name__, "status": "success"},
                )
                return result
            except Exception:
                metrics.increment_counter(
                    "app_requests_total",
                    1.0,
                    {"operation": func.__name__, "status": "error"},
                )
                raise

        return wrapper

    return decorator


def track_errors(operation_name: Optional[str] = None):
    """
    Decorador que rastrea errores en una función.

    Args:
        operation_name: Nombre de la operación (usa nombre de función si None)

    Usage:
        @track_errors("crear_profesor")
        def crear_profesor(data):
            pass
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                metrics = get_metrics()
                metrics.increment_counter(
                    "app_errors_total",
                    1.0,
                    {"error_type": type(e).__name__, "operation": op_name},
                )

                logger.error(
                    f"Error en {op_name}: {type(e).__name__}",
                    extra={
                        "operation": op_name,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                    exc_info=e,
                )

                raise

        return wrapper

    return decorator


def track_database_query(query_type: str):
    """
    Decorador que rastrea queries a la base de datos.

    Args:
        query_type: Tipo de query (select, insert, update, delete)

    Usage:
        @track_database_query("select")
        def obtener_profesores():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                metrics.record_database_query(query_type, duration, success=True)

                return result

            except Exception:
                duration = time.time() - start_time
                metrics.record_database_query(query_type, duration, success=False)
                raise

        return wrapper

    return decorator


def track_cache_access(cache_type: str = "default"):
    """
    Decorador que rastrea accesos al cache.

    Detecta automáticamente hits y misses basándose en si la función
    retorna None (miss) o un valor (hit).

    Args:
        cache_type: Tipo de cache

    Usage:
        @track_cache_access("profesor")
        def get_from_cache(key):
            return cache.get(key)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            metrics = get_metrics()

            if result is None:
                metrics.record_cache_miss(cache_type)
            else:
                metrics.record_cache_hit(cache_type)

            return result

        return wrapper

    return decorator


def with_metrics(operation: Optional[str] = None):
    """
    Decorador completo que combina tracking de tiempo, conteo y errores.

    Args:
        operation: Nombre de la operación

    Usage:
        @with_metrics("crear_profesor")
        def crear_profesor(data):
            pass
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Métricas de éxito
                metrics.observe_histogram(
                    "app_request_duration_seconds",
                    duration,
                    {"operation": op_name},
                )
                metrics.increment_counter(
                    "app_requests_total",
                    1.0,
                    {"operation": op_name, "status": "success"},
                )

                logger.debug(
                    f"✅ {op_name} completado",
                    extra={
                        "operation": op_name,
                        "duration_ms": duration * 1000,
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Métricas de error
                metrics.observe_histogram(
                    "app_request_duration_seconds",
                    duration,
                    {"operation": op_name},
                )
                metrics.increment_counter(
                    "app_requests_total",
                    1.0,
                    {"operation": op_name, "status": "error"},
                )
                metrics.increment_counter(
                    "app_errors_total",
                    1.0,
                    {"error_type": type(e).__name__, "operation": op_name},
                )

                logger.error(
                    f"❌ {op_name} falló",
                    extra={
                        "operation": op_name,
                        "duration_ms": duration * 1000,
                        "error_type": type(e).__name__,
                    },
                    exc_info=e,
                )

                raise

        return wrapper

    return decorator
