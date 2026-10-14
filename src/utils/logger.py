"""
Compatibilidad: redirige a core.logging.

Todos los imports de utils.logger delegan a core.logging.
Usar directamente `from core.logging import get_logger` en código nuevo.
"""

from core.logging import get_logger, log_function_call, setup_logging

__all__ = ["get_logger", "log_function_call", "setup_logging"]
