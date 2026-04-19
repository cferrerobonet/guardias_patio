"""Tests para core/security/lockout_manager.py."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.security.lockout_manager import (
    LockoutManager,
    LOCKOUT_DURATION_MINUTES,
    MAX_ATTEMPTS,
    PROGRESIVE_DELAYS,
)


@pytest.fixture
def mgr(tmp_path):
    """LockoutManager con directorio temporal."""
    with patch("core.security.lockout_manager.get_user_data_directory", return_value=tmp_path):
        m = LockoutManager("test_hash")
    m.user_dir = tmp_path
    m.lockout_file = tmp_path / "lockout.json"
    return m


class TestLoadSaveLockoutData:
    def test_load_devuelve_dict_vacio_sin_archivo(self, mgr):
        result = mgr._load_lockout_data()
        assert result == {}

    def test_load_devuelve_datos_guardados(self, mgr):
        data = {"usuario": {"attempts": 2, "locked_until": None}}
        mgr.lockout_file.write_text(json.dumps(data), encoding="utf-8")
        result = mgr._load_lockout_data()
        assert result["usuario"]["attempts"] == 2

    def test_load_devuelve_vacio_si_json_invalido(self, mgr):
        mgr.lockout_file.write_text("no es json", encoding="utf-8")
        result = mgr._load_lockout_data()
        assert result == {}

    def test_save_crea_archivo(self, mgr):
        mgr._save_lockout_data({"user": {"attempts": 1}})
        assert mgr.lockout_file.exists()
        saved = json.loads(mgr.lockout_file.read_text())
        assert saved["user"]["attempts"] == 1

    def test_save_captura_excepcion(self, mgr):
        # Hacer que la apertura falle
        with patch("builtins.open", side_effect=OSError("disco lleno")):
            mgr._save_lockout_data({"user": {}})  # no debe lanzar


class TestRecordFailedAttempt:
    def test_primer_intento_no_bloquea(self, mgr):
        is_locked, delay = mgr.record_failed_attempt("profesor1")
        assert is_locked is False
        assert delay == PROGRESIVE_DELAYS[0]

    def test_delay_progresivo(self, mgr):
        for i in range(1, 4):
            is_locked, delay = mgr.record_failed_attempt("profesor2")
        # En el intento 3 el delay debe ser el 3er valor de la lista
        assert delay == PROGRESIVE_DELAYS[2]

    def test_bloqueo_tras_max_intentos(self, mgr):
        for _ in range(MAX_ATTEMPTS - 1):
            mgr.record_failed_attempt("profe_bloqueo")
        is_locked, delay = mgr.record_failed_attempt("profe_bloqueo")
        assert is_locked is False  # el MAX-ésimo intento en sí no bloquea aún en el return
        # Pero el usuario SÍ queda bloqueado para el siguiente intento
        data = mgr._load_lockout_data()
        assert data["profe_bloqueo"]["locked_until"] is not None

    def test_devuelve_locked_y_remaining_si_ya_bloqueado(self, mgr):
        # Bloquear manualmente
        locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        mgr._save_lockout_data({
            "profe_lock": {
                "attempts": 0,
                "locked_until": locked_until.isoformat(),
                "first_attempt_at": datetime.now(timezone.utc).isoformat(),
            }
        })
        is_locked, remaining = mgr.record_failed_attempt("profe_lock")
        assert is_locked is True
        assert remaining > 0

    def test_crea_entrada_para_nuevo_usuario(self, mgr):
        mgr.record_failed_attempt("nuevo_usuario")
        data = mgr._load_lockout_data()
        assert "nuevo_usuario" in data

    def test_limpia_bloqueo_expirado(self, mgr):
        # Crear bloqueo ya expirado
        expired = datetime.now(timezone.utc) - timedelta(minutes=1)
        mgr._save_lockout_data({
            "profe_exp": {
                "attempts": 0,
                "locked_until": expired.isoformat(),
                "first_attempt_at": datetime.now(timezone.utc).isoformat(),
            }
        })
        is_locked, delay = mgr.record_failed_attempt("profe_exp")
        assert is_locked is False


class TestResetAttempts:
    def test_resetea_intentos(self, mgr):
        mgr.record_failed_attempt("profe_reset")
        mgr.reset_attempts("profe_reset")
        data = mgr._load_lockout_data()
        assert data["profe_reset"]["attempts"] == 0
        assert data["profe_reset"]["locked_until"] is None

    def test_no_falla_si_usuario_inexistente(self, mgr):
        mgr.reset_attempts("inexistente")  # no debe lanzar


class TestIsLocked:
    def test_false_si_usuario_inexistente(self, mgr):
        assert mgr.is_locked("nadie") is False

    def test_false_si_no_hay_locked_until(self, mgr):
        mgr._save_lockout_data({
            "profe": {"attempts": 1, "locked_until": None}
        })
        assert mgr.is_locked("profe") is False

    def test_true_si_bloqueado(self, mgr):
        locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        mgr._save_lockout_data({
            "profe_locked": {
                "attempts": 0,
                "locked_until": locked_until.isoformat(),
            }
        })
        assert mgr.is_locked("profe_locked") is True

    def test_false_y_desbloquea_automaticamente_si_expirado(self, mgr):
        expired = datetime.now(timezone.utc) - timedelta(seconds=1)
        mgr._save_lockout_data({
            "profe_exp": {
                "attempts": 0,
                "locked_until": expired.isoformat(),
            }
        })
        result = mgr.is_locked("profe_exp")
        assert result is False
        # El locked_until debe haberse limpiado
        data = mgr._load_lockout_data()
        assert data["profe_exp"]["locked_until"] is None


class TestGetRemainingLockoutTime:
    def test_none_si_no_existe(self, mgr):
        assert mgr.get_remaining_lockout_time("nadie") is None

    def test_none_si_no_bloqueado(self, mgr):
        mgr._save_lockout_data({
            "profe": {"attempts": 1, "locked_until": None}
        })
        assert mgr.get_remaining_lockout_time("profe") is None

    def test_devuelve_segundos_si_bloqueado(self, mgr):
        locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        mgr._save_lockout_data({
            "profe_time": {
                "attempts": 0,
                "locked_until": locked_until.isoformat(),
            }
        })
        remaining = mgr.get_remaining_lockout_time("profe_time")
        assert remaining is not None
        assert remaining > 0
        assert remaining <= 601  # máximo ~10 min + margen

    def test_none_si_expirado(self, mgr):
        expired = datetime.now(timezone.utc) - timedelta(seconds=5)
        mgr._save_lockout_data({
            "profe_exp2": {
                "attempts": 0,
                "locked_until": expired.isoformat(),
            }
        })
        assert mgr.get_remaining_lockout_time("profe_exp2") is None
