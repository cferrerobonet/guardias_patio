"""Tests para database/db_manager.py — funciones de gestión de BD de usuario."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database.db_manager import (
    _get_user_backup_dir,
    _hash_username,
    _prune_old_backups,
    backup_database,
    create_user_database,
    delete_user_database,
    get_user_database_path,
    restore_database,
    user_has_database,
)


class TestHashUsername:
    def test_hash_valido(self):
        h = _hash_username("usuario1")
        assert len(h) == 16
        assert h.isalnum()

    def test_mismo_input_mismo_hash(self):
        assert _hash_username("test") == _hash_username("test")

    def test_distinto_input_distinto_hash(self):
        assert _hash_username("a") != _hash_username("b")

    def test_vacio_lanza_error(self):
        with pytest.raises(ValueError):
            _hash_username("")

    def test_solo_espacios_lanza_error(self):
        with pytest.raises(ValueError):
            _hash_username("   ")


class TestGetUserBackupDir:
    def test_devuelve_path_con_hash(self):
        result = _get_user_backup_dir("usuario1")
        assert isinstance(result, Path)
        assert "backups" in result.parts


class TestPruneOldBackups:
    def test_no_elimina_con_max_cero(self, tmp_path):
        f = tmp_path / "guardias_patio_backup_20240101_000000.db"
        f.touch()
        _prune_old_backups(tmp_path, 0)
        assert f.exists()

    def test_no_elimina_si_hay_pocos(self, tmp_path):
        for i in range(3):
            (tmp_path / f"guardias_patio_backup_2024010{i}_000000.db").touch()
        _prune_old_backups(tmp_path, 5)
        assert len(list(tmp_path.glob("*.db"))) == 3

    def test_elimina_backups_excedentes(self, tmp_path):
        import time
        files = []
        for i in range(5):
            f = tmp_path / f"guardias_patio_backup_2024010{i}_000000.db"
            f.touch()
            time.sleep(0.01)
            files.append(f)
        _prune_old_backups(tmp_path, 3)
        remaining = list(tmp_path.glob("*.db"))
        assert len(remaining) == 3


class TestGetUserDatabasePath:
    def test_devuelve_path_correcto(self):
        p = get_user_database_path("usuario1")
        assert isinstance(p, Path)
        assert p.name == "guardias_patio.db"


class TestUserHasDatabase:
    def test_false_si_no_existe(self, tmp_path):
        with patch("database.db_manager.USER_DATA_DIR", tmp_path):
            assert user_has_database("inexistente_usuario_xyz") is False

    def test_true_si_existe(self, tmp_path):
        from database.db_manager import _hash_username
        user_hash = _hash_username("usuario_test")
        db_dir = tmp_path / user_hash
        db_dir.mkdir(parents=True)
        (db_dir / "guardias_patio.db").touch()
        with patch("database.db_manager.USER_DATA_DIR", tmp_path):
            assert user_has_database("usuario_test") is True


class TestCreateUserDatabase:
    def test_crea_bd_exitosamente(self, tmp_path):
        with (
            patch("database.db_manager.USER_DATA_DIR", tmp_path),
            patch("database.db_manager._run_alembic_migrations", return_value=True),
        ):
            result = create_user_database("nuevo_usuario")
        assert result is True

    def test_falla_si_migraciones_fallan(self, tmp_path):
        with (
            patch("database.db_manager.USER_DATA_DIR", tmp_path),
            patch("database.db_manager._run_alembic_migrations", return_value=False),
        ):
            result = create_user_database("nuevo_usuario")
        assert result is False

    def test_devuelve_false_si_excepcion(self, tmp_path):
        with (
            patch("database.db_manager.USER_DATA_DIR", tmp_path),
            patch("database.db_manager._run_alembic_migrations", side_effect=Exception("boom")),
        ):
            result = create_user_database("nuevo_usuario")
        assert result is False


class TestDeleteUserDatabase:
    def test_false_si_no_existe(self, tmp_path):
        with patch("database.db_manager.USER_DATA_DIR", tmp_path):
            result = delete_user_database("inexistente_usuario_xyz")
        assert result is False

    def test_elimina_directorio(self, tmp_path):
        from database.db_manager import _hash_username
        user_hash = _hash_username("usuario_borrar")
        user_dir = tmp_path / user_hash
        user_dir.mkdir(parents=True)
        (user_dir / "guardias_patio.db").touch()

        with patch("database.db_manager.USER_DATA_DIR", tmp_path):
            result = delete_user_database("usuario_borrar")
        assert result is True
        assert not user_dir.exists()


class TestBackupDatabase:
    def test_devuelve_none_si_no_existe_bd(self, tmp_path):
        with patch("database.db_manager.USER_DATA_DIR", tmp_path):
            result = backup_database("usuario_sin_bd")
        assert result is None

    def test_crea_backup_exitoso(self, tmp_path):
        from database.db_manager import _hash_username
        user_hash = _hash_username("usuario_backup")
        db_dir = tmp_path / user_hash
        db_dir.mkdir(parents=True)
        db_file = db_dir / "guardias_patio.db"
        db_file.write_bytes(b"SQLite format 3\x00")

        backup_dir = tmp_path / "backups"
        with patch("database.db_manager.USER_DATA_DIR", tmp_path):
            result = backup_database("usuario_backup", backup_dir=backup_dir)
        assert result is not None
        assert result.exists()

    def test_devuelve_none_si_excepcion(self, tmp_path):
        from database.db_manager import _hash_username
        user_hash = _hash_username("usuario_exc")
        db_dir = tmp_path / user_hash
        db_dir.mkdir(parents=True)
        db_file = db_dir / "guardias_patio.db"
        db_file.write_bytes(b"SQLite format 3\x00")

        with (
            patch("database.db_manager.USER_DATA_DIR", tmp_path),
            patch("shutil.copy2", side_effect=OSError("disco lleno")),
        ):
            result = backup_database("usuario_exc")
        assert result is None


class TestRestoreDatabase:
    def test_false_si_backup_no_existe(self, tmp_path):
        result = restore_database("usuario1", tmp_path / "noexiste.db")
        assert result is False

    def test_false_si_backup_invalido(self, tmp_path):
        bad_file = tmp_path / "bad.db"
        bad_file.write_bytes(b"esto no es sqlite")
        result = restore_database("usuario1", bad_file)
        assert result is False

    def test_restaura_exitosamente(self, tmp_path):
        import sqlite3
        from database.db_manager import _hash_username

        # Crear un backup SQLite válido
        backup_file = tmp_path / "backup.db"
        conn = sqlite3.connect(str(backup_file))
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.close()

        user_hash = _hash_username("usuario_restore")
        with patch("database.db_manager.USER_DATA_DIR", tmp_path):
            result = restore_database("usuario_restore", backup_file)
        assert result is True
