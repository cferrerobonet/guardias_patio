"""
Tests para utils.logger — verifica que redirige correctamente a core.logging.
"""

from core import logging as core_logging
from utils.logger import get_logger, log_function_call, setup_logging


class TestReexports:
    """Verifica que utils.logger re-exporta core.logging."""

    def test_get_logger_is_core(self):
        assert get_logger is core_logging.get_logger

    def test_setup_logging_is_core(self):
        assert setup_logging is core_logging.setup_logging

    def test_log_function_call_is_core(self):
        assert log_function_call is core_logging.log_function_call

    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
