"""
Sistema centralizado de logging estructurado.

Proporciona logging con contexto rico, structured logging (JSON),
y decoradores para logging automático de funciones.

Features:
    - Structured logging con structlog
    - Context managers para contexto automático
    - Decoradores para log de funciones
    - Performance tracking
    - Filtros por nivel
    - Rotación de archivos

Uso básico:
    from core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("profesor_created", profesor_id=1, nombre="Juan")

Uso con decorador:
    from core.logging import log_function_call

    @log_function_call
    def crear_profesor(nombre: str) -> Profesor:
        ...

Uso con context:
    from core.logging import log_context

    with log_context(user_id=123):
        logger.info("operation_complete")
"""

import functools
import logging
import logging.handlers
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None  # type: ignore


# ============================================================================
# CONFIGURACIÓN
# ============================================================================


class LogConfig:
    """Configuración de logging."""

    def __init__(self):
        # Intentar importar settings, sino usar valores por defecto
        try:
            from config import settings

            self.log_level = settings.log_level
            self.log_file = settings.log_file
            self.log_to_console = settings.log_to_console
            self.log_to_file = settings.log_to_file
            self.structured_logging = settings.structured_logging and STRUCTLOG_AVAILABLE
        except ImportError:
            self.log_level = "INFO"
            self.log_file = "logs/guardias_patio.log"
            self.log_to_console = True
            self.log_to_file = True
            self.structured_logging = STRUCTLOG_AVAILABLE

        # Crear directorio de logs
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


config = LogConfig()


# ============================================================================
# CONFIGURACIÓN DE STRUCTLOG
# ============================================================================


def configure_structlog():
    """Configura structlog con processors personalizados."""
    if not STRUCTLOG_AVAILABLE:
        return

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.dev.ConsoleRenderer()
                if config.log_to_console
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ============================================================================
# CONFIGURACIÓN DE LOGGING ESTÁNDAR
# ============================================================================


def setup_standard_logging():
    """Configura logging estándar de Python."""
    # Formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))

    # Console handler
    if config.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.log_level))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler con rotación
    if config.log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            config.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, config.log_level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# ============================================================================
# INICIALIZACIÓN
# ============================================================================


def setup_logging():
    """
    Configura el sistema de logging.

    Debe llamarse al inicio de la aplicación.
    """
    if config.structured_logging:
        configure_structlog()
    else:
        setup_standard_logging()


# ============================================================================
# LOGGER FACTORY
# ============================================================================


def get_logger(name: str):
    """
    Obtiene un logger para el módulo especificado.

    Args:
        name: Nombre del logger (típicamente __name__)

    Returns:
        Logger configurado (structlog o logging estándar)

    Example:
        logger = get_logger(__name__)
        logger.info("mensaje", key="value")
    """
    if config.structured_logging:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================


@contextmanager
def log_context(**context):
    """
    Context manager para añadir contexto temporal al logging.

    Args:
        **context: Pares key-value de contexto

    Example:
        with log_context(user_id=123, operation="create"):
            logger.info("processing")  # Incluirá user_id y operation
    """
    if config.structured_logging and STRUCTLOG_AVAILABLE:
        with structlog.contextvars.bound_contextvars(**context):
            yield
    else:
        # Para logging estándar, no hay contexto automático
        yield


@contextmanager
def log_execution_time(logger, operation: str):
    """
    Context manager para medir y loggear tiempo de ejecución.

    Args:
        logger: Logger a usar
        operation: Nombre de la operación

    Example:
        with log_execution_time(logger, "consulta_profesores"):
            profesores = session.query(Profesor).all()
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        logger.info(
            "operation_completed",
            operation=operation,
            duration_ms=round(elapsed * 1000, 2),
        )


# ============================================================================
# DECORADORES
# ============================================================================


def log_function_call(
    logger: Optional[Any] = None,
    level: str = "info",
    log_args: bool = True,
    log_result: bool = False,
):
    """
    Decorador para loggear llamadas a funciones automáticamente.

    Args:
        logger: Logger a usar (si None, usa nombre de módulo)
        level: Nivel de log ("debug", "info", "warning", "error")
        log_args: Si loggear argumentos de la función
        log_result: Si loggear el resultado de la función

    Example:
        @log_function_call
        def crear_profesor(nombre: str) -> Profesor:
            ...

        @log_function_call(log_result=True)
        def obtener_profesor(id: int) -> Profesor:
            ...
    """

    def decorator(func: Callable) -> Callable:
        func_logger = logger or get_logger(func.__module__)
        log_method = getattr(func_logger, level)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Preparar contexto
            context = {
                "function": func.__name__,
                "module": func.__module__,
            }

            if log_args:
                # Evitar loggear argumentos sensibles
                safe_kwargs = {
                    k: ("***" if "password" in k.lower() or "token" in k.lower() else v)
                    for k, v in kwargs.items()
                }
                context["kwargs"] = safe_kwargs

            # Log inicio
            log_method("function_called", **context)

            # Ejecutar función
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)

                # Log éxito
                elapsed = time.perf_counter() - start_time
                success_context = {
                    **context,
                    "duration_ms": round(elapsed * 1000, 2),
                    "success": True,
                }

                if log_result and result is not None:
                    success_context["result_type"] = type(result).__name__

                log_method("function_completed", **success_context)

                return result

            except Exception as e:
                # Log error
                elapsed = time.perf_counter() - start_time
                error_context = {
                    **context,
                    "duration_ms": round(elapsed * 1000, 2),
                    "success": False,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
                func_logger.error("function_failed", **error_context)
                raise

        return wrapper

    return decorator


def log_exceptions(logger: Optional[Any] = None, reraise: bool = True):
    """
    Decorador para loggear excepciones automáticamente.

    Args:
        logger: Logger a usar
        reraise: Si re-lanzar la excepción después de loggear

    Example:
        @log_exceptions
        def operacion_critica():
            ...
    """

    def decorator(func: Callable) -> Callable:
        func_logger = logger or get_logger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_logger.error(
                    "exception_caught",
                    function=func.__name__,
                    module=func.__module__,
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                    exc_info=True,
                )
                if reraise:
                    raise
                return None

        return wrapper

    return decorator


# ============================================================================
# UTILIDADES
# ============================================================================


def log_system_info(logger):
    """
    Loggea información del sistema al inicio.

    Args:
        logger: Logger a usar
    """
    import platform

    logger.info(
        "system_info",
        python_version=platform.python_version(),
        system=platform.system(),
        machine=platform.machine(),
    )


def log_startup(logger, app_name: str, app_version: str):
    """
    Loggea inicio de la aplicación.

    Args:
        logger: Logger a usar
        app_name: Nombre de la aplicación
        app_version: Versión de la aplicación
    """
    logger.info(
        "application_startup",
        app_name=app_name,
        version=app_version,
    )
    log_system_info(logger)


def log_shutdown(logger):
    """
    Loggea cierre de la aplicación.

    Args:
        logger: Logger a usar
    """
    logger.info("application_shutdown")


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "setup_logging",
    "get_logger",
    "log_context",
    "log_execution_time",
    "log_function_call",
    "log_exceptions",
    "log_system_info",
    "log_startup",
    "log_shutdown",
]
