"""
Tests para SessionLock con LocalSyncBackend.

Cubre: acquire (sin/con lock previo), lock expirado, update_heartbeat,
release (elimina archivo local), get_lock_info.
No requiere SFTP — usa LocalSyncBackend como backend.
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sync.sync_manager import LocalSyncBackend
from sync.session_lock import SessionLock


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def backend(tmp_path):
    return LocalSyncBackend(tmp_path / "remote")


@pytest.fixture
def local_dir(tmp_path):
    d = tmp_path / "local"
    d.mkdir()
    return d


@pytest.fixture
def lock(backend, local_dir):
    with patch("sync.session_lock.get_user_data_directory", return_value=local_dir):
        sl = SessionLock(backend, "testuser", "abc123hash")
        yield sl


# ============================================================================
# TESTS: acquire_lock
# ============================================================================


class TestSessionLockAcquire:
    def test_acquire_cuando_no_existe_lock_retorna_true(self, lock):
        result = lock.acquire_lock()
        assert result is True

    def test_acquire_crea_archivo_en_backend(self, lock, backend):
        lock.acquire_lock()
        remote_path = lock._get_remote_lock_path()
        assert backend.file_exists(remote_path)

    def test_segunda_adquisicion_falla(self, backend, local_dir):
        with patch("sync.session_lock.get_user_data_directory", return_value=local_dir):
            lock1 = SessionLock(backend, "testuser", "abc123hash")
            lock2 = SessionLock(backend, "testuser", "abc123hash")
            lock1.acquire_lock()
            result = lock2.acquire_lock()
        assert result is False

    def test_lock_expirado_permite_nueva_adquisicion(self, backend, local_dir):
        with patch("sync.session_lock.get_user_data_directory", return_value=local_dir):
            # Subir un lock con heartbeat expirado
            expired_info = {
                "username": "testuser",
                "hostname": "otherhost",
                "ip_address": "192.168.0.99",
                "pid": 9999,
                "started_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "last_heartbeat": (datetime.now() - timedelta(seconds=60)).isoformat(),
            }
            old_lock = SessionLock(backend, "testuser", "abc123hash")
            remote_path = old_lock._get_remote_lock_path()
            local_tmp = local_dir / "abc123hash" / "session.lock"
            local_tmp.parent.mkdir(parents=True, exist_ok=True)
            with local_tmp.open("w") as f:
                json.dump(expired_info, f)
            backend.upload_file(local_tmp, remote_path)

            new_lock = SessionLock(backend, "testuser", "abc123hash")
            result = new_lock.acquire_lock()
        assert result is True


# ============================================================================
# TESTS: update_heartbeat
# ============================================================================


class TestSessionLockHeartbeat:
    def test_update_heartbeat_sin_lock_retorna_false(self, lock):
        result = lock.update_heartbeat()
        assert result is False

    def test_update_heartbeat_tras_acquire_retorna_true(self, lock):
        lock.acquire_lock()
        result = lock.update_heartbeat()
        assert result is True

    def test_update_heartbeat_actualiza_timestamp(self, lock):
        lock.acquire_lock()
        time.sleep(0.05)
        lock.update_heartbeat()
        info = lock.get_lock_info()
        assert info is not None
        hb = datetime.fromisoformat(info["last_heartbeat"])
        started = datetime.fromisoformat(info["started_at"])
        assert hb >= started


# ============================================================================
# TESTS: release_lock
# ============================================================================


class TestSessionLockRelease:
    def test_release_retorna_true(self, lock):
        lock.acquire_lock()
        assert lock.release_lock() is True

    def test_release_elimina_archivo_local(self, lock):
        lock.acquire_lock()
        local_path = lock._get_local_lock_path()
        assert local_path.exists()
        lock.release_lock()
        assert not local_path.exists()

    def test_release_sin_acquire_retorna_true(self, lock):
        assert lock.release_lock() is True


# ============================================================================
# TESTS: get_lock_info
# ============================================================================


class TestSessionLockInfo:
    def test_get_lock_info_sin_lock_retorna_none(self, lock):
        assert lock.get_lock_info() is None

    def test_get_lock_info_con_lock_retorna_dict(self, lock):
        lock.acquire_lock()
        info = lock.get_lock_info()
        assert isinstance(info, dict)

    def test_get_lock_info_tiene_campos_esperados(self, lock):
        lock.acquire_lock()
        info = lock.get_lock_info()
        for campo in ("username", "hostname", "pid", "started_at", "last_heartbeat"):
            assert campo in info, f"Campo '{campo}' ausente"

    def test_get_lock_info_username_correcto(self, lock):
        lock.acquire_lock()
        info = lock.get_lock_info()
        assert info["username"] == "testuser"
