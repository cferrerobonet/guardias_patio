"""
Tests para LockoutManager y UserAuth.authenticate.

Cubre: intentos fallidos, bloqueo tras 5 fallos, reset, delay progresivo,
autenticación con bcrypt, lockout integrado en authenticate.
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.security.lockout_manager import LockoutManager, MAX_ATTEMPTS, LOCKOUT_DURATION_MINUTES


# ============================================================================
# HELPERS
# ============================================================================


def _make_lockout_manager(tmp_dir: Path) -> LockoutManager:
    """Crea un LockoutManager con directorio temporal aislado."""
    with patch("core.security.lockout_manager.get_user_data_directory", return_value=tmp_dir):
        manager = LockoutManager("test_user_hash")
    return manager


def _make_user_auth(users: dict) -> "UserAuth":
    from sync.sync_manager import UserAuth

    tmp = tempfile.mkstemp(suffix=".json")[1]
    with open(tmp, "w") as f:
        json.dump(users, f)
    return UserAuth(users_file=Path(tmp))


def _bcrypt_hash(password: str) -> str:
    import bcrypt

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ============================================================================
# TESTS: LockoutManager
# ============================================================================


class TestLockoutManager:
    def test_usuario_sin_intentos_no_esta_bloqueado(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        assert mgr.is_locked("alice") is False

    def test_primer_intento_fallido_no_bloquea(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        is_locked, _delay = mgr.record_failed_attempt("alice")
        assert is_locked is False

    def test_cuatro_intentos_no_bloquean(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        for _ in range(MAX_ATTEMPTS - 1):
            is_locked, _ = mgr.record_failed_attempt("bob")
        assert is_locked is False
        assert mgr.is_locked("bob") is False

    def test_cinco_intentos_bloquean(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        for _ in range(MAX_ATTEMPTS):
            mgr.record_failed_attempt("carol")
        assert mgr.is_locked("carol") is True

    def test_reset_desbloquea_usuario(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        for _ in range(MAX_ATTEMPTS):
            mgr.record_failed_attempt("dave")
        assert mgr.is_locked("dave") is True
        mgr.reset_attempts("dave")
        assert mgr.is_locked("dave") is False

    def test_get_remaining_lockout_time_sin_bloqueo_retorna_none(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        assert mgr.get_remaining_lockout_time("unknown_user") is None

    def test_get_remaining_lockout_time_con_bloqueo_retorna_float(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        for _ in range(MAX_ATTEMPTS):
            mgr.record_failed_attempt("eve")
        remaining = mgr.get_remaining_lockout_time("eve")
        assert remaining is not None
        assert remaining > 0
        assert remaining <= LOCKOUT_DURATION_MINUTES * 60

    def test_bloqueo_expirado_se_desbloquea_automaticamente(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        # Inyectar bloqueo ya expirado directamente en el archivo
        lockout_data = {
            "frank": {
                "attempts": 0,
                "locked_until": (
                    datetime.now(timezone.utc) - timedelta(minutes=1)
                ).isoformat(),
                "first_attempt_at": datetime.now(timezone.utc).isoformat(),
            }
        }
        mgr.lockout_file.parent.mkdir(parents=True, exist_ok=True)
        with mgr.lockout_file.open("w") as f:
            json.dump(lockout_data, f)
        assert mgr.is_locked("frank") is False

    def test_delay_primer_intento_es_uno(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        _, delay = mgr.record_failed_attempt("grace")
        assert delay == 1

    def test_delay_segundo_intento_es_dos(self, tmp_path):
        mgr = _make_lockout_manager(tmp_path)
        mgr.record_failed_attempt("heidi")
        _, delay = mgr.record_failed_attempt("heidi")
        assert delay == 2

    def test_intentos_se_persisten_entre_instancias(self, tmp_path):
        mgr1 = _make_lockout_manager(tmp_path)
        for _ in range(MAX_ATTEMPTS):
            mgr1.record_failed_attempt("ivan")
        mgr2 = _make_lockout_manager(tmp_path)
        assert mgr2.is_locked("ivan") is True


# ============================================================================
# TESTS: UserAuth.authenticate
# ============================================================================


class TestUserAuthAuthenticate:
    def test_usuario_inexistente_falla(self):
        auth = _make_user_auth({})
        ok, msg = auth.authenticate("noone", "pass")
        assert ok is False
        assert msg != ""

    def test_password_incorrecta_falla(self):
        auth = _make_user_auth({"alice": {"password_hash": _bcrypt_hash("Correcto1!")}})
        with patch("time.sleep"):
            ok, msg = auth.authenticate("alice", "Incorrecto1!")
        assert ok is False
        assert msg != ""

    def test_credenciales_correctas_autentican(self):
        auth = _make_user_auth({"alice": {"password_hash": _bcrypt_hash("Correcto1!")}})
        ok, msg = auth.authenticate("alice", "Correcto1!")
        assert ok is True
        assert msg == ""

    def test_login_exitoso_resetea_intentos_fallidos(self):
        user_data = {
            "alice": {
                "password_hash": _bcrypt_hash("Correcto1!"),
                "failed_login_attempts": 3,
                "locked_until": None,
            }
        }
        auth = _make_user_auth(user_data)
        ok, _ = auth.authenticate("alice", "Correcto1!")
        assert ok is True
        assert auth.users["alice"].get("failed_login_attempts", 0) == 0

    def test_cinco_intentos_fallidos_bloquean_cuenta(self):
        auth = _make_user_auth({"alice": {"password_hash": _bcrypt_hash("Correcto1!")}})
        with patch("time.sleep"):
            for _ in range(MAX_ATTEMPTS):
                ok, msg = auth.authenticate("alice", "Mal1!")
        assert ok is False
        assert "bloqueada" in msg.lower() or "intentos" in msg.lower()
        assert auth.users["alice"].get("locked_until") is not None

    def test_cuenta_bloqueada_rechaza_password_correcta(self):
        locked_until = (datetime.now() + timedelta(hours=1)).isoformat()
        user_data = {
            "alice": {
                "password_hash": _bcrypt_hash("Correcto1!"),
                "failed_login_attempts": 0,
                "locked_until": locked_until,
            }
        }
        auth = _make_user_auth(user_data)
        ok, msg = auth.authenticate("alice", "Correcto1!")
        assert ok is False
        assert "bloqueada" in msg.lower() or "intenta" in msg.lower()

    def test_bloqueo_expirado_permite_autenticacion(self):
        expired = (datetime.now() - timedelta(minutes=1)).isoformat()
        user_data = {
            "alice": {
                "password_hash": _bcrypt_hash("Correcto1!"),
                "failed_login_attempts": 5,
                "locked_until": expired,
            }
        }
        auth = _make_user_auth(user_data)
        ok, _ = auth.authenticate("alice", "Correcto1!")
        assert ok is True
