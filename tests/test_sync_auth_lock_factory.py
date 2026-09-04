"""Tests de sync: UserAuth, SessionLock, backend_factory y utilidades."""

import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sync import backend_factory
from sync.backend_factory import create_sync_backend, get_default_backend
from sync.session_lock import SessionLock, SessionLockManager
from sync.sync_manager import (
    LocalSyncBackend,
    SFTPSyncBackend,
    SyncManager,
    UserAuth,
    _count_json_records,
)


# ---------------------------------------------------------------------------
# UserAuth
# ---------------------------------------------------------------------------


class TestUserAuthPolicy:
    def test_policy_len(self):
        ok, msg = UserAuth.validate_password_policy("Ab1!")
        assert ok is False
        assert "8 caracteres" in msg

    def test_policy_upper(self):
        ok, msg = UserAuth.validate_password_policy("abcd1234!")
        assert ok is False
        assert "mayúscula" in msg

    def test_policy_digit(self):
        ok, msg = UserAuth.validate_password_policy("Abcdefg!")
        assert ok is False
        assert "número" in msg

    def test_policy_special(self):
        ok, msg = UserAuth.validate_password_policy("Abcdefg1")
        assert ok is False
        assert "especial" in msg

    def test_policy_ok(self):
        ok, msg = UserAuth.validate_password_policy("Abcdef1!")
        assert ok is True
        assert msg == ""


class TestUserAuthFlow:
    def test_register_ok(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        assert auth.register_user("user.ok", "Abcdef1!", "u@x.com") is True
        assert "user.ok" in auth.users

    def test_register_duplicate(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        auth.register_user("dup", "Abcdef1!", "u@x.com")
        assert auth.register_user("dup", "Abcdef1!", "u@x.com") is False

    def test_register_invalid_username(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        assert auth.register_user("bad user", "Abcdef1!", "u@x.com") is False

    def test_is_legacy_sha256(self):
        assert UserAuth._is_legacy_sha256("a" * 64) is True
        assert UserAuth._is_legacy_sha256("g" * 64) is False
        assert UserAuth._is_legacy_sha256("short") is False

    def test_auth_unknown_user(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        ok, _ = auth.authenticate("nope", "x")
        assert ok is False

    def test_auth_bcrypt_ok(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        auth.register_user("alice", "Abcdef1!", "a@x.com")
        ok, msg = auth.authenticate("alice", "Abcdef1!")
        assert ok is True
        assert msg == ""

    def test_auth_wrong_password_and_lockout(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        auth.register_user("bob", "Abcdef1!", "b@x.com")

        with patch("time.sleep", return_value=None):
            for _ in range(4):
                ok, msg = auth.authenticate("bob", "wrong")
                assert ok is False
                assert "incorrectos" in msg

            ok, msg = auth.authenticate("bob", "wrong")
            assert ok is False
            assert "bloqueada" in msg

        assert auth.users["bob"].get("locked_until") is not None

    def test_auth_locked_user(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        auth.register_user("carol", "Abcdef1!", "c@x.com")
        auth.users["carol"]["locked_until"] = (datetime.now() + timedelta(minutes=10)).isoformat()
        auth._save_users()

        ok, msg = auth.authenticate("carol", "Abcdef1!")
        assert ok is False
        assert "Cuenta bloqueada" in msg

    def test_auth_legacy_sha256_migrates(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        legacy_hash = hashlib.sha256("Abcdef1!".encode()).hexdigest()
        auth.users["legacy"] = {"password_hash": legacy_hash, "email": "l@x.com"}
        auth._save_users()

        ok, msg = auth.authenticate("legacy", "Abcdef1!")
        assert ok is True
        assert msg == ""
        assert UserAuth._is_legacy_sha256(auth.users["legacy"]["password_hash"]) is False

    def test_unregister_user(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        auth.register_user("delme", "Abcdef1!", "d@x.com")
        assert auth.unregister_user("delme") is True
        assert "delme" not in auth.users

    def test_unregister_user_missing(self, tmp_path):
        auth = UserAuth(users_file=tmp_path / "users.json")
        assert auth.unregister_user("ghost") is False


# ---------------------------------------------------------------------------
# SessionLock + manager
# ---------------------------------------------------------------------------


class TestSessionLock:
    def _make_lock(self, tmp_path):
        backend = MagicMock()
        with patch("sync.session_lock.get_user_data_directory", return_value=tmp_path):
            lock = SessionLock(backend=backend, username="u1", user_hash="hash1")
        # Fijar ruta local para todos los métodos del test y evitar dependencia de rutas reales.
        local_lock_path = tmp_path / "hash1" / "session.lock"
        lock._get_local_lock_path = lambda: local_lock_path
        return lock, backend

    def test_get_local_ip_fallback(self, tmp_path):
        backend = MagicMock()
        with (
            patch("sync.session_lock.get_user_data_directory", return_value=tmp_path),
            patch("socket.socket", side_effect=OSError("no net")),
        ):
            lock = SessionLock(backend=backend, username="u", user_hash="h")
        assert lock.session_info["ip_address"] == "127.0.0.1"

    def test_acquire_lock_new(self, tmp_path):
        lock, backend = self._make_lock(tmp_path)
        backend.file_exists.return_value = False
        backend.upload_file.return_value = True

        ok = lock.acquire_lock()
        assert ok is True
        assert lock._get_local_lock_path().exists()

    def test_acquire_lock_active_exists(self, tmp_path):
        lock, backend = self._make_lock(tmp_path)
        backend.file_exists.return_value = True

        # Simular descarga de lock activo
        def _download(remote, local):
            payload = {
                "last_heartbeat": datetime.now().isoformat(),
                "hostname": "h",
                "ip_address": "1.1.1.1",
                "started_at": datetime.now().isoformat(),
            }
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps(payload), encoding="utf-8")
            return True

        backend.download_file.side_effect = _download
        ok = lock.acquire_lock()
        assert ok is False

    def test_acquire_lock_expired_replaced(self, tmp_path):
        lock, backend = self._make_lock(tmp_path)
        backend.file_exists.return_value = True
        backend.upload_file.return_value = True

        def _download(remote, local):
            payload = {"last_heartbeat": (datetime.now() - timedelta(seconds=120)).isoformat()}
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps(payload), encoding="utf-8")
            return True

        backend.download_file.side_effect = _download
        ok = lock.acquire_lock()
        assert ok is True

    def test_update_heartbeat_without_local_file(self, tmp_path):
        lock, _ = self._make_lock(tmp_path)
        assert lock.update_heartbeat() is False

    def test_release_lock(self, tmp_path):
        lock, _ = self._make_lock(tmp_path)
        p = lock._get_local_lock_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
        assert lock.release_lock() is True
        assert not p.exists()

    def test_get_lock_info_not_exists(self, tmp_path):
        lock, backend = self._make_lock(tmp_path)
        backend.file_exists.return_value = False
        assert lock.get_lock_info() is None

    def test_get_lock_info_ok(self, tmp_path):
        lock, backend = self._make_lock(tmp_path)
        backend.file_exists.return_value = True

        def _download(remote, local):
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps({"x": 1}), encoding="utf-8")
            return True

        backend.download_file.side_effect = _download
        assert lock.get_lock_info() == {"x": 1}


class TestSessionLockManager:
    def test_stop_heartbeat(self):
        mgr = SessionLockManager(session_lock=MagicMock())
        timer = MagicMock()
        mgr.heartbeat_timer = timer
        mgr.stop_heartbeat()
        timer.stop.assert_called_once()

    def test_cleanup(self):
        lock = MagicMock()
        mgr = SessionLockManager(session_lock=lock)
        mgr.heartbeat_timer = MagicMock()
        mgr.cleanup()
        lock.release_lock.assert_called_once()


# ---------------------------------------------------------------------------
# backend_factory
# ---------------------------------------------------------------------------


class TestBackendFactory:
    def test_create_local_backend(self, tmp_path):
        with patch("sync.backend_factory.get_data_directory", return_value=tmp_path):
            backend = create_sync_backend("local")
        assert isinstance(backend, LocalSyncBackend)

    def test_create_sftp_invalid_config(self):
        with patch("sync.backend_factory.validate_sftp_config", return_value=False):
            with pytest.raises(ValueError):
                create_sync_backend("sftp")

    def test_create_sftp_success(self):
        config = {
            "host": "example.com",
            "port": 22,
            "username": "u",
            "password": "p",
            "base_dir": "/x",
        }
        with (
            patch("sync.backend_factory.validate_sftp_config", return_value=True),
            patch("sync.backend_factory.get_sftp_config", return_value=config),
            patch.dict("sys.modules", {"paramiko": MagicMock()}),
            patch("sync.backend_factory.SFTPSyncBackend", return_value=MagicMock()) as cls,
        ):
            _ = create_sync_backend("sftp")
        cls.assert_called_once()

    def test_create_unknown_backend(self):
        with pytest.raises(ValueError):
            create_sync_backend("other")

    def test_get_default_backend_prefers_sftp(self):
        fake = MagicMock()
        with (
            patch("sync.backend_factory.validate_sftp_config", return_value=True),
            patch("sync.backend_factory.create_sync_backend", return_value=fake),
        ):
            out = get_default_backend()
        assert out is fake

    def test_get_default_backend_no_cae_a_local_en_silencio(self):
        """Si el servidor falla, se avisa; nunca se guarda en local fingiendo que hay nube."""
        from sync.backend_factory import SyncConfigurationError

        def _side(bt):
            if bt == "sftp":
                raise RuntimeError("boom")
            return MagicMock()

        with (
            patch("sync.backend_factory.validate_sftp_config", return_value=True),
            patch("sync.backend_factory.create_sync_backend", side_effect=_side),
        ):
            with pytest.raises(SyncConfigurationError):
                get_default_backend()

    def test_get_default_backend_sin_configuracion_avisa(self):
        from sync.backend_factory import SyncConfigurationError

        with patch("sync.backend_factory.validate_sftp_config", return_value=False):
            with pytest.raises(SyncConfigurationError):
                get_default_backend()


# ---------------------------------------------------------------------------
# sync_manager utilidades + Local/SFTP helper paths
# ---------------------------------------------------------------------------


class TestSyncUtils:
    def test_count_json_records_ok(self, tmp_path):
        p = tmp_path / "x.json"
        p.write_text(
            json.dumps(
                {
                    "profesores": [1, 2],
                    "guardias": [1],
                    "zonas": [],
                    "cursos_escolares": [1, 2, 3],
                    "ausencias": [1],
                }
            ),
            encoding="utf-8",
        )
        assert _count_json_records(p) == 7

    def test_count_json_records_bad_json(self, tmp_path):
        p = tmp_path / "x.json"
        p.write_text("not-json", encoding="utf-8")
        assert _count_json_records(p) == 0

    def test_local_backend_safe_path_and_traversal(self, tmp_path):
        b = LocalSyncBackend(tmp_path)
        assert b._safe_path("a/b.txt").is_absolute()
        with pytest.raises(ValueError):
            b._safe_path("../../etc/passwd")

    def test_local_backend_upload_download_exists(self, tmp_path):
        b = LocalSyncBackend(tmp_path / "remote")
        src = tmp_path / "src.txt"
        dst = tmp_path / "dst.txt"
        src.write_text("hola", encoding="utf-8")

        assert b.upload_file(src, "users/u/file.txt") is True
        assert b.file_exists("users/u/file.txt") is True
        assert b.download_file("users/u/file.txt", dst) is True
        assert dst.read_text(encoding="utf-8") == "hola"

    def test_local_backend_traversal_is_false(self, tmp_path):
        b = LocalSyncBackend(tmp_path / "remote")
        assert b.file_exists("../../x") is False

    def test_sftp_sanitize_path(self):
        sftp = SFTPSyncBackend.__new__(SFTPSyncBackend)
        assert sftp._sanitize_path("users/a/file.json") == "users/a/file.json"
        with pytest.raises(ValueError):
            sftp._sanitize_path("/etc/passwd")
        with pytest.raises(ValueError):
            sftp._sanitize_path("../secret")
        with pytest.raises(ValueError):
            sftp._sanitize_path("users/-danger")


# ---------------------------------------------------------------------------
# SyncManager
# ---------------------------------------------------------------------------


class TestSyncManagerFlow:
    def _make_manager(self, tmp_path):
        backend = MagicMock()
        with patch("sync.sync_manager.get_user_data_directory", return_value=tmp_path):
            manager = SyncManager(backend=backend, username="user1")
        return manager, backend

    def test_sync_startup_no_remote(self, tmp_path):
        manager, backend = self._make_manager(tmp_path)
        backend.file_exists.return_value = False

        ok = manager.sync_on_startup()

        assert ok is True
        assert (manager.local_data_dir / "last_sync.json").exists()

    def test_sync_startup_descarga_y_reconstruye(self, tmp_path):
        """Al abrir se reconstruye la base local con lo que hay en la nube."""
        manager, backend = self._make_manager(tmp_path)
        backend.file_exists.return_value = True

        def _download(_remote, out_path):
            out_path.write_text(
                json.dumps({"sync_version": 7, "profesores": [{"id": 1}], "guardias": []}),
                encoding="utf-8",
            )
            return True

        backend.download_file.side_effect = _download

        session = MagicMock()
        with patch("sync.data_exporter.DataExporter.import_from_json", return_value=True) as importer:
            ok = manager.sync_on_startup(session=session)

        assert ok is True
        importer.assert_called_once()
        # Reemplazo, no fusión: así las bajas se propagan.
        assert importer.call_args.kwargs["clear_existing"] is True
        assert manager.version_descargada == 7
        assert manager.puede_subir is True

    def test_sync_startup_rechaza_un_fichero_corrupto(self, tmp_path):
        manager, backend = self._make_manager(tmp_path)
        backend.file_exists.return_value = True

        def _download(_remote, out_path):
            out_path.write_text("{esto no es json", encoding="utf-8")
            return True

        backend.download_file.side_effect = _download

        ok = manager.sync_on_startup(session=MagicMock())

        assert ok is False
        assert manager.puede_subir is False

    def test_sin_descarga_no_se_permite_subir(self, tmp_path):
        """El escenario del portátil sin cobertura: no se machaca lo bueno con datos viejos."""
        manager, backend = self._make_manager(tmp_path)
        backend.file_exists.return_value = True
        backend.download_file.return_value = False

        assert manager.sync_on_startup(session=MagicMock()) is False
        assert manager.sync_on_shutdown(session=MagicMock()) is False
        backend.upload_file.assert_not_called()

    def test_no_sobrescribe_si_alguien_subio_entretanto(self, tmp_path):
        manager, backend = self._make_manager(tmp_path)
        manager.puede_subir = True
        manager.version_descargada = 4
        backend.file_exists.return_value = True

        def _download(_remote, out_path):
            out_path.write_text(json.dumps({"sync_version": 9, "profesores": []}), encoding="utf-8")
            return True

        backend.download_file.side_effect = _download

        def _export(_session, out_path, sync_version=0):
            out_path.write_text(json.dumps({"sync_version": sync_version}), encoding="utf-8")
            return True

        with patch("sync.data_exporter.DataExporter.export_to_json", side_effect=_export):
            ok = manager.sync_on_shutdown(session=MagicMock())

        assert ok is False
        backend.upload_file.assert_not_called()
        assert manager._leer_metadata_local()["pendiente_subida"] is True

    def test_una_subida_pendiente_bloquea_la_descarga_siguiente(self, tmp_path):
        """Si la sesión anterior no llegó a subir, no se descarga encima de su trabajo."""
        manager, backend = self._make_manager(tmp_path)
        manager._guardar_metadata_local(3, pendiente_subida=True)

        ok = manager.sync_on_startup(session=MagicMock())

        assert ok is False
        assert manager.puede_subir is False
        backend.download_file.assert_not_called()

    def test_sync_shutdown_without_session_and_no_json(self, tmp_path):
        manager, _backend = self._make_manager(tmp_path)
        ok = manager.sync_on_shutdown(session=None)
        assert ok is False

    def test_sync_shutdown_export_error(self, tmp_path):
        manager, _backend = self._make_manager(tmp_path)
        manager.puede_subir = True
        session = MagicMock()
        with patch("sync.data_exporter.DataExporter.export_to_json", return_value=False):
            ok = manager.sync_on_shutdown(session=session)
        assert ok is False

    def test_sync_shutdown_upload_success_and_progress(self, tmp_path):
        manager, backend = self._make_manager(tmp_path)
        manager.puede_subir = True
        backend.file_exists.return_value = False
        backend.upload_file.return_value = True
        session = MagicMock()
        progress = []

        def _export(_session, out_path, sync_version=0):
            out_path.write_text(json.dumps({"ok": True}), encoding="utf-8")
            return True

        with patch("sync.data_exporter.DataExporter.export_to_json", side_effect=_export):
            ok = manager.sync_on_shutdown(
                session=session,
                progress_callback=lambda step, details: progress.append(step),
            )

        assert ok is True
        assert "exporting" in progress
        assert "uploading" in progress
        assert "complete" in progress

    def test_sync_shutdown_upload_exception(self, tmp_path):
        manager, backend = self._make_manager(tmp_path)
        manager.puede_subir = True
        backend.file_exists.return_value = False
        session = MagicMock()

        def _export(_session, out_path, sync_version=0):
            out_path.write_text(json.dumps({"ok": True}), encoding="utf-8")
            return True

        backend.upload_file.side_effect = RuntimeError("net")
        with patch("sync.data_exporter.DataExporter.export_to_json", side_effect=_export):
            ok = manager.sync_on_shutdown(session=session)
        assert ok is False

    def test_manual_sync_calls_startup_and_shutdown(self, tmp_path):
        manager, _backend = self._make_manager(tmp_path)
        with (
            patch.object(manager, "sync_on_startup", return_value=True) as start,
            patch.object(manager, "sync_on_shutdown", return_value=True) as stop,
        ):
            ok = manager.manual_sync()
        assert ok is True
        start.assert_called_once()
        stop.assert_called_once()
