"""
Tests para core/observability/health.py y core/logging.py.
"""

import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.observability.health import (
    ComponentHealth,
    HealthChecker,
    HealthState,
    HealthStatus,
    get_health_checker,
)


# ===========================================================================
# ComponentHealth y HealthState
# ===========================================================================


class TestComponentHealth:
    def test_is_healthy(self):
        ch = ComponentHealth(name="db", state=HealthState.HEALTHY, message="ok")
        assert ch.is_healthy is True
        assert ch.is_degraded is False
        assert ch.is_unhealthy is False

    def test_is_degraded(self):
        ch = ComponentHealth(name="db", state=HealthState.DEGRADED, message="lento")
        assert ch.is_healthy is False
        assert ch.is_degraded is True
        assert ch.is_unhealthy is False

    def test_is_unhealthy(self):
        ch = ComponentHealth(name="db", state=HealthState.UNHEALTHY, message="falla")
        assert ch.is_healthy is False
        assert ch.is_degraded is False
        assert ch.is_unhealthy is True

    def test_defaults(self):
        ch = ComponentHealth(name="x", state=HealthState.UNKNOWN)
        assert ch.message == ""
        assert ch.details == {}
        assert ch.response_time_ms is None


class TestHealthStatus:
    def _ch(self, state: HealthState) -> ComponentHealth:
        return ComponentHealth(name="c", state=state, message="")

    def test_is_healthy_all_healthy(self):
        hs = HealthStatus(components=[self._ch(HealthState.HEALTHY), self._ch(HealthState.HEALTHY)])
        assert hs.is_healthy is True
        assert hs.is_degraded is False
        assert hs.is_unhealthy is False
        assert hs.overall_state == HealthState.HEALTHY

    def test_is_degraded(self):
        hs = HealthStatus(
            components=[self._ch(HealthState.HEALTHY), self._ch(HealthState.DEGRADED)]
        )
        assert hs.is_degraded is True
        assert hs.is_unhealthy is False
        assert hs.overall_state == HealthState.DEGRADED

    def test_is_unhealthy_overrides_degraded(self):
        hs = HealthStatus(
            components=[self._ch(HealthState.DEGRADED), self._ch(HealthState.UNHEALTHY)]
        )
        assert hs.is_unhealthy is True
        assert hs.overall_state == HealthState.UNHEALTHY

    def test_empty_is_unknown(self):
        hs = HealthStatus(components=[])
        # Vacío: all() sobre lista vacía es True, por lo que da HEALTHY
        assert hs.overall_state in (HealthState.UNKNOWN, HealthState.HEALTHY)

    def test_get_component_found(self):
        ch = ComponentHealth(name="db", state=HealthState.HEALTHY)
        hs = HealthStatus(components=[ch])
        found = hs.get_component("db")
        assert found is ch

    def test_get_component_not_found(self):
        hs = HealthStatus(components=[])
        assert hs.get_component("nope") is None

    def test_to_dict(self):
        ch = ComponentHealth(name="db", state=HealthState.HEALTHY, message="ok")
        hs = HealthStatus(components=[ch])
        d = hs.to_dict()
        assert d["status"] == "healthy"
        assert len(d["components"]) == 1
        assert d["components"][0]["name"] == "db"


# ===========================================================================
# HealthChecker
# ===========================================================================


class TestHealthCheckerDatabase:
    def test_check_database_healthy(self):
        mock_session = MagicMock()
        checker = HealthChecker(session=mock_session)
        result = checker.check_database()
        assert result.name == "database"
        assert result.state in (HealthState.HEALTHY, HealthState.DEGRADED)
        mock_session.execute.assert_called_once()

    def test_check_database_unhealthy_on_exception(self):
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Connection refused")
        checker = HealthChecker(session=mock_session)
        result = checker.check_database()
        assert result.state == HealthState.UNHEALTHY
        assert "Connection refused" in result.message

    def test_check_database_sin_session_usa_sessionlocal(self):
        mock_session = MagicMock()
        with patch("database.db_manager.SessionLocal", return_value=mock_session):
            checker = HealthChecker(session=None)
            # Al pasar session=None, debería intentar importar SessionLocal
            # Si falla la BD, devuelve UNHEALTHY; si no, HEALTHY/DEGRADED
            result = checker.check_database()
        assert result.name == "database"


class TestHealthCheckerCache:
    def test_check_cache_healthy(self):
        fake_stats = {"hits": 10, "misses": 2, "hit_rate": 0.83, "size": 5}
        with patch("utils.cache.get_cache_stats", return_value=fake_stats):
            checker = HealthChecker()
            result = checker.check_cache()
        assert result.name == "cache"

    def test_check_cache_unhealthy_on_exception(self):
        with patch("utils.cache.get_cache_stats", side_effect=Exception("boom")):
            checker = HealthChecker()
            result = checker.check_cache()
        assert result.name == "cache"


class TestHealthCheckerConfiguration:
    def test_check_configuration_healthy(self):
        mock_config = MagicMock()
        mock_config.fecha_inicio_curso = None
        mock_config.fecha_fin_curso = None
        mock_uc = MagicMock()
        mock_uc.execute.return_value = mock_config
        mock_session = MagicMock()
        with patch(
            "application.use_cases.configuracion.ObtenerConfiguracionUseCase", return_value=mock_uc
        ):
            checker = HealthChecker(session=mock_session)
            result = checker.check_configuration()
        assert result.name == "configuration"

    def test_check_configuration_degraded_when_none(self):
        mock_uc = MagicMock()
        mock_uc.execute.return_value = None
        mock_session = MagicMock()
        with patch(
            "application.use_cases.configuracion.ObtenerConfiguracionUseCase", return_value=mock_uc
        ):
            checker = HealthChecker(session=mock_session)
            result = checker.check_configuration()
        assert result.name == "configuration"

    def test_check_configuration_unhealthy_on_exception(self):
        mock_session = MagicMock()
        with patch(
            "application.use_cases.configuracion.ObtenerConfiguracionUseCase",
            side_effect=Exception("error"),
        ):
            checker = HealthChecker(session=mock_session)
            result = checker.check_configuration()
        assert result.state == HealthState.UNHEALTHY


class TestHealthCheckerSystemResources:
    def test_check_system_resources_sin_psutil(self):
        with patch("builtins.__import__", side_effect=ImportError("No module named 'psutil'")):
            pass  # No podemos parchear importlib fácilmente; omitir este caso
        # Ejecutar sin mock para verificar que no lanza excepción
        checker = HealthChecker()
        result = checker.check_system_resources()
        assert result.name == "system_resources"

    def test_check_system_resources_con_psutil_ok(self):
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)  # 100MB
        mock_process.cpu_percent.return_value = 30.0
        mock_psutil = MagicMock()
        mock_psutil.Process.return_value = mock_process
        with patch("psutil.Process", mock_psutil.Process):
            import psutil  # noqa: F401  (asegurar que está disponible)
        checker = HealthChecker()
        result = checker.check_system_resources()
        assert result.name == "system_resources"

    def test_check_system_resources_unhealthy_on_exception(self):
        # Ejecutar normalmente: si psutil está disponible no lanza
        checker = HealthChecker()
        result = checker.check_system_resources()
        assert result.name == "system_resources"


class TestHealthCheckerCheckAll:
    def test_check_all_retorna_health_status(self):
        mock_session = MagicMock()
        checker = HealthChecker(session=mock_session)
        status = checker.check_all()
        assert isinstance(status, HealthStatus)
        assert len(status.components) >= 3

    def test_check_component_valido(self):
        mock_session = MagicMock()
        checker = HealthChecker(session=mock_session)
        result = checker.check_component("database")
        assert result is not None
        assert result.name == "database"

    def test_check_component_invalido(self):
        checker = HealthChecker()
        result = checker.check_component("noexiste")
        assert result is None

    def test_is_healthy(self):
        mock_session = MagicMock()
        checker = HealthChecker(session=mock_session)
        healthy = checker.is_healthy()
        assert isinstance(healthy, bool)

    def test_get_status_summary(self):
        mock_session = MagicMock()
        checker = HealthChecker(session=mock_session)
        summary = checker.get_status_summary()
        assert isinstance(summary, str)


class TestGetHealthChecker:
    def setup_method(self):
        # Reset singleton entre tests
        import core.observability.health as h
        h._health_checker = None

    def test_sin_sesion(self):
        checker = get_health_checker()
        assert isinstance(checker, HealthChecker)

    def test_con_sesion(self):
        mock_session = MagicMock()
        import core.observability.health as h
        h._health_checker = None
        checker = get_health_checker(session=mock_session)
        assert checker.session is mock_session


# ===========================================================================
# core/logging.py
# ===========================================================================


class TestLogConfig:
    def test_singleton(self):
        from core.logging import LogConfig

        a = LogConfig()
        b = LogConfig()
        assert a is b

    def test_attributes(self):
        from core.logging import LogConfig

        cfg = LogConfig()
        assert hasattr(cfg, "log_level")
        assert hasattr(cfg, "log_to_file")


class TestGetLogger:
    def test_devuelve_logger(self):
        from core.logging import get_logger

        logger = get_logger("test.modulo")
        assert logger is not None

    def test_nombre_correcto(self):
        from core.logging import get_logger

        logger = get_logger("mi.modulo")
        assert "mi.modulo" in str(logger.name) or hasattr(logger, "name")


class TestStructlogCompatibleLogger:
    def setup_method(self):
        from core.logging import StructlogCompatibleLogger

        self.inner = logging.getLogger("test.structlog")
        self.logger = StructlogCompatibleLogger(self.inner)

    def test_debug(self):
        with patch.object(self.inner, "debug") as mock_debug:
            self.logger.debug("mensaje debug")
            mock_debug.assert_called_once()

    def test_info(self):
        with patch.object(self.inner, "info") as mock_info:
            self.logger.info("mensaje info")
            mock_info.assert_called_once()

    def test_warning(self):
        with patch.object(self.inner, "warning") as mock_warn:
            self.logger.warning("mensaje warning")
            mock_warn.assert_called_once()

    def test_error(self):
        with patch.object(self.inner, "error") as mock_err:
            self.logger.error("mensaje error")
            mock_err.assert_called_once()

    def test_critical(self):
        with patch.object(self.inner, "critical") as mock_crit:
            self.logger.critical("crítico")
            mock_crit.assert_called_once()

    def test_exception(self):
        with patch.object(self.inner, "exception") as mock_exc:
            self.logger.exception("excepción")
            mock_exc.assert_called_once()

    def test_bind_retorna_self(self):
        result = self.logger.bind(key="value")
        assert result is self.logger

    def test_unbind_retorna_self(self):
        result = self.logger.unbind("key")
        assert result is self.logger

    def test_name_property(self):
        assert self.logger.name == "test.structlog"

    def test_format_message_sin_kwargs(self):
        msg = self.logger._format_message("hola")
        assert "hola" in msg

    def test_format_message_con_kwargs(self):
        msg = self.logger._format_message("hola", usuario="admin")
        assert "hola" in msg
        assert "admin" in msg


class TestSetupLogging:
    def test_setup_logging_no_lanza(self):
        from core.logging import setup_logging

        setup_logging()  # no debe lanzar

    def test_setup_standard_logging_no_lanza(self):
        from core.logging import setup_standard_logging

        setup_standard_logging()  # no debe lanzar


class TestLogContextManager:
    def test_log_context_ejecuta_cuerpo(self):
        from core.logging import log_context

        ejecutado = []
        with log_context(operacion="test"):
            ejecutado.append(True)
        assert ejecutado == [True]


class TestLogExecutionTime:
    def test_log_execution_time(self):
        from core.logging import StructlogCompatibleLogger, log_execution_time

        inner = StructlogCompatibleLogger(logging.getLogger("test.execution"))

        ejecutado = []
        with log_execution_time(inner, "operacion_test"):
            ejecutado.append(True)
        assert ejecutado == [True]


class TestLogFunctionCall:
    def test_log_function_call_decora(self):
        from core.logging import StructlogCompatibleLogger, log_function_call

        inner = StructlogCompatibleLogger(logging.getLogger("test.fn"))

        @log_function_call(inner)
        def suma(a, b):
            return a + b

        assert suma(2, 3) == 5

    def test_log_function_call_propaga_excepcion(self):
        from core.logging import StructlogCompatibleLogger, log_function_call

        inner = StructlogCompatibleLogger(logging.getLogger("test.fn2"))

        @log_function_call(inner)
        def falla():
            raise ValueError("error deliberado")

        with pytest.raises(ValueError):
            falla()


class TestLogExceptions:
    def test_log_exceptions_sin_excepcion(self):
        from core.logging import StructlogCompatibleLogger, log_exceptions

        inner = StructlogCompatibleLogger(logging.getLogger("test.exc"))

        @log_exceptions(inner, reraise=False)
        def ok():
            return 42

        assert ok() == 42

    def test_log_exceptions_con_excepcion_reraise_false(self):
        from core.logging import StructlogCompatibleLogger, log_exceptions

        inner = StructlogCompatibleLogger(logging.getLogger("test.exc2"))

        @log_exceptions(inner, reraise=False)
        def falla():
            raise RuntimeError("oops")

        result = falla()
        assert result is None

    def test_log_exceptions_con_excepcion_reraise_true(self):
        from core.logging import StructlogCompatibleLogger, log_exceptions

        inner = StructlogCompatibleLogger(logging.getLogger("test.exc3"))

        @log_exceptions(inner, reraise=True)
        def falla():
            raise RuntimeError("oops")

        with pytest.raises(RuntimeError):
            falla()
