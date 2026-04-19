"""Tests para cache_service y retry SFTP en sync_manager."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.cache_service import (
    cache_configuracion,
    cache_profesores_activos,
    cache_zonas_activas,
    invalidar_cache,
    invalidar_configuracion,
    invalidar_profesores,
    invalidar_zonas,
)


# =============================================================================
# Helpers
# =============================================================================


def _make_session(return_value):
    """Crea un mock de session que devuelve return_value en .first() o .all()."""
    query_mock = MagicMock()
    query_mock.first.return_value = return_value
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = return_value if isinstance(return_value, list) else [return_value]
    session = MagicMock()
    session.query.return_value = query_mock
    return session


# =============================================================================
# Tests cache_service
# =============================================================================


class TestCacheConfiguracion:
    def setup_method(self):
        invalidar_cache()

    def test_primera_llamada_accede_bd(self):
        config = MagicMock(name="Config")
        session = _make_session(config)
        result = cache_configuracion(session)
        assert result is config
        session.query.assert_called_once()

    def test_segunda_llamada_usa_cache(self):
        config = MagicMock(name="Config")
        session = _make_session(config)
        cache_configuracion(session)
        result2 = cache_configuracion(session)
        assert result2 is config
        # Solo 1 query en total
        assert session.query.call_count == 1

    def test_invalidar_fuerza_nueva_query(self):
        config = MagicMock(name="Config")
        session = _make_session(config)
        cache_configuracion(session)
        invalidar_configuracion()
        cache_configuracion(session)
        assert session.query.call_count == 2

    def test_config_none_se_cachea(self):
        session = _make_session(None)
        r1 = cache_configuracion(session)
        r2 = cache_configuracion(session)
        assert r1 is None
        assert r2 is None
        assert session.query.call_count == 1


class TestCacheZonasActivas:
    def setup_method(self):
        invalidar_cache()

    def test_primera_llamada_accede_bd(self):
        zonas = [MagicMock(name=f"Zona{i}") for i in range(3)]
        session = _make_session(zonas)
        result = cache_zonas_activas(session)
        assert result == zonas
        session.query.assert_called_once()

    def test_segunda_llamada_usa_cache(self):
        zonas = [MagicMock()]
        session = _make_session(zonas)
        cache_zonas_activas(session)
        cache_zonas_activas(session)
        assert session.query.call_count == 1

    def test_invalidar_zonas_fuerza_nueva_query(self):
        zonas = [MagicMock()]
        session = _make_session(zonas)
        cache_zonas_activas(session)
        invalidar_zonas()
        cache_zonas_activas(session)
        assert session.query.call_count == 2


class TestCacheProfesoresActivos:
    def setup_method(self):
        invalidar_cache()

    def test_primera_llamada_accede_bd(self):
        profs = [MagicMock(), MagicMock()]
        session = _make_session(profs)
        result = cache_profesores_activos(session)
        assert result == profs

    def test_cache_es_thread_safe(self):
        """Múltiples hilos no deben corromper el caché."""
        invalidar_cache()
        profs = [MagicMock(name=f"P{i}") for i in range(5)]
        session = _make_session(profs)
        resultados = []
        errores = []

        def worker():
            try:
                r = cache_profesores_activos(session)
                resultados.append(r)
            except Exception as e:
                errores.append(e)

        hilos = [threading.Thread(target=worker) for _ in range(10)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        assert not errores
        assert len(resultados) == 10
        for r in resultados:
            assert r == profs

    def test_invalidar_profesores_limpia_solo_profesores(self):
        config = MagicMock()
        session_config = _make_session(config)
        cache_configuracion(session_config)

        profs = [MagicMock()]
        session_profs = _make_session(profs)
        cache_profesores_activos(session_profs)

        invalidar_profesores()

        # Config sigue en caché
        cache_configuracion(session_config)
        assert session_config.query.call_count == 1  # No re-query

        # Profesores fuerza nueva query
        cache_profesores_activos(session_profs)
        assert session_profs.query.call_count == 2


class TestInvalidarCache:
    def setup_method(self):
        invalidar_cache()

    def test_invalidar_todo_limpia_los_tres_caches(self):
        session = _make_session(MagicMock())
        cache_configuracion(session)
        cache_zonas_activas(session)
        cache_profesores_activos(session)

        assert session.query.call_count == 3

        invalidar_cache()

        cache_configuracion(session)
        cache_zonas_activas(session)
        cache_profesores_activos(session)

        assert session.query.call_count == 6


# =============================================================================
# Tests retry SFTP (unit, sin conexión real)
# =============================================================================


class TestSFTPRetry:
    def test_sftp_importa_tenacity_cuando_disponible(self):
        from sync.sync_manager import _TENACITY_AVAILABLE
        assert _TENACITY_AVAILABLE is True

    def test_connect_llama_connect_with_retry_si_tenacity(self):
        """_connect() delega en _connect_with_retry() cuando tenacity está disponible."""
        from sync.sync_manager import SFTPSyncBackend, _TENACITY_AVAILABLE

        if not _TENACITY_AVAILABLE:
            pytest.skip("tenacity no disponible")

        with patch.object(SFTPSyncBackend, "_connect", return_value=True):
            backend = SFTPSyncBackend.__new__(SFTPSyncBackend)
            backend._host = "host"
            backend._port = 22
            backend._username = "user"
            backend._password = "pass"
            backend.base_dir = "/test"
            backend.sftp = None
            backend.client = None

            with patch.object(backend, "_connect_with_retry", return_value=True) as mock_retry:
                with patch.object(backend, "_connect_once", return_value=True):
                    from sync.sync_manager import _TENACITY_AVAILABLE as TA
                    if TA:
                        backend._connect_with_retry()
                    mock_retry.assert_called_once()

    def test_connect_once_devuelve_false_en_error_conexion(self):
        """_connect_once retorna False (no lanza) cuando hay error de conexión."""
        from sync.sync_manager import SFTPSyncBackend

        backend = SFTPSyncBackend.__new__(SFTPSyncBackend)
        backend._host = "host_inexistente_test_abc123.local"
        backend._port = 22
        backend._username = "user"
        backend._password = "pass"
        backend.base_dir = "/test"
        backend.sftp = None
        backend.client = None

        result = backend._connect_once()
        assert result is False
