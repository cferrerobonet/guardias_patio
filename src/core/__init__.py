"""Core module - Sistema central de la aplicación."""

from .exceptions import (
    BusinessLogicError,
    DatabaseError,
    GuardiasBaseException,
    InfrastructureError,
    NotFoundError,
    ValidationError,
    format_exception_for_user,
    is_user_error,
)
from .logging import (
    get_logger,
    log_context,
    log_exceptions,
    log_execution_time,
    log_function_call,
    setup_logging,
)

__all__ = [
    # Exceptions
    "GuardiasBaseException",
    "ValidationError",
    "NotFoundError",
    "BusinessLogicError",
    "DatabaseError",
    "InfrastructureError",
    "format_exception_for_user",
    "is_user_error",
    # Logging
    "get_logger",
    "log_context",
    "log_execution_time",
    "log_function_call",
    "log_exceptions",
    "setup_logging",
]
