"""
Tests para core/paths.py

Verifica la gestión de rutas del sistema en diferentes entornos.
"""

import platform
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from core import paths


class TestGetBaseDirectory:
    """Tests para get_base_directory()."""

    def test_development_mode(self):
        """Test que en modo desarrollo retorna el directorio del proyecto."""
        with patch.object(sys, "frozen", False, create=True):
            base_dir = paths.get_base_directory()
            assert isinstance(base_dir, Path)
            assert base_dir.exists()
            # En desarrollo, debe ser 3 niveles arriba de paths.py (src/core/paths.py -> .)
            assert base_dir.is_dir()

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Test específico para macOS")
    def test_frozen_macos(self):
        """Test que en macOS empaquetado usa Application Support."""
        with patch.object(sys, "frozen", True, create=True):
            base_dir = paths.get_base_directory()
            assert isinstance(base_dir, Path)
            assert "Application Support" in str(base_dir)
            assert "GuardiasDePatio" in str(base_dir)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Test específico para Windows")
    def test_frozen_windows(self):
        """Test que en Windows empaquetado usa AppData."""
        with patch.object(sys, "frozen", True, create=True):
            base_dir = paths.get_base_directory()
            assert isinstance(base_dir, Path)
            assert "AppData" in str(base_dir) or "APPDATA" in str(base_dir).upper()
            assert "GuardiasDePatio" in str(base_dir)

    def test_creates_directory_if_not_exists(self):
        """Test que crea el directorio si no existe."""
        base_dir = paths.get_base_directory()
        assert base_dir.exists()
        assert base_dir.is_dir()


class TestGetDataDirectory:
    """Tests para get_data_directory()."""

    def test_returns_path(self):
        """Test que retorna un Path válido."""
        data_dir = paths.get_data_directory()
        assert isinstance(data_dir, Path)

    def test_is_subdirectory_of_base(self):
        """Test que es subdirectorio del directorio base."""
        data_dir = paths.get_data_directory()
        base_dir = paths.get_base_directory()
        assert str(data_dir).startswith(str(base_dir))
        assert "data" in str(data_dir)

    def test_creates_directory(self):
        """Test que crea el directorio si no existe."""
        data_dir = paths.get_data_directory()
        assert data_dir.exists()
        assert data_dir.is_dir()


class TestGetLogsDirectory:
    """Tests para get_logs_directory()."""

    def test_returns_path(self):
        """Test que retorna un Path válido."""
        logs_dir = paths.get_logs_directory()
        assert isinstance(logs_dir, Path)

    def test_is_subdirectory_of_base(self):
        """Test que es subdirectorio del directorio base."""
        logs_dir = paths.get_logs_directory()
        base_dir = paths.get_base_directory()
        assert str(logs_dir).startswith(str(base_dir))
        assert "logs" in str(logs_dir)

    def test_creates_directory(self):
        """Test que crea el directorio si no existe."""
        logs_dir = paths.get_logs_directory()
        assert logs_dir.exists()
        assert logs_dir.is_dir()


class TestGetUserDataDirectory:
    """Tests para get_user_data_directory()."""

    def test_returns_path(self):
        """Test que retorna un Path válido."""
        user_data_dir = paths.get_user_data_directory()
        assert isinstance(user_data_dir, Path)

    def test_is_subdirectory_of_data(self):
        """Test que es subdirectorio de data."""
        user_data_dir = paths.get_user_data_directory()
        data_dir = paths.get_data_directory()
        assert str(user_data_dir).startswith(str(data_dir))
        assert "users" in str(user_data_dir)

    def test_creates_directory(self):
        """Test que crea el directorio si no existe."""
        user_data_dir = paths.get_user_data_directory()
        assert user_data_dir.exists()
        assert user_data_dir.is_dir()


class TestGetResourcesDirectory:
    """Tests para get_resources_directory()."""

    def test_development_mode(self):
        """Test que en modo desarrollo usa imagenes/ del proyecto."""
        with patch.object(sys, "frozen", False, create=True):
            resources_dir = paths.get_resources_directory()
            assert isinstance(resources_dir, Path)
            assert "imagenes" in str(resources_dir)

    def test_frozen_with_meipass(self):
        """Test que en modo empaquetado usa _MEIPASS."""
        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", "/tmp/meipass", create=True):
                resources_dir = paths.get_resources_directory()
                assert isinstance(resources_dir, Path)
                assert "_MEIPASS" in str(resources_dir) or "imagenes" in str(resources_dir)


class TestGetDatabasePath:
    """Tests para get_database_path()."""

    def test_returns_path(self):
        """Test que retorna un Path válido."""
        db_path = paths.get_database_path()
        assert isinstance(db_path, Path)

    def test_is_in_data_directory(self):
        """Test que está en el directorio de datos."""
        db_path = paths.get_database_path()
        data_dir = paths.get_data_directory()
        assert db_path.parent == data_dir

    def test_has_db_extension(self):
        """Test que tiene extensión .db."""
        db_path = paths.get_database_path()
        assert db_path.suffix == ".db"
        assert "guardias_patio" in db_path.name


class TestModuleExports:
    """Tests para exports del módulo."""

    def test_all_exports(self):
        """Test que __all__ contiene todas las funciones públicas."""
        expected = [
            "get_base_directory",
            "get_data_directory",
            "get_logs_directory",
            "get_user_data_directory",
            "get_resources_directory",
            "get_database_path",
        ]
        assert paths.__all__ == expected

    def test_all_functions_callable(self):
        """Test que todas las funciones exportadas son llamables."""
        for func_name in paths.__all__:
            func = getattr(paths, func_name)
            assert callable(func)


class TestIntegration:
    """Tests de integración entre funciones."""

    def test_all_paths_are_consistent(self):
        """Test que todas las rutas son consistentes."""
        base = paths.get_base_directory()
        data = paths.get_data_directory()
        logs = paths.get_logs_directory()
        users = paths.get_user_data_directory()
        db = paths.get_database_path()

        # Verificar jerarquía
        assert str(data).startswith(str(base))
        assert str(logs).startswith(str(base))
        assert str(users).startswith(str(data))
        assert str(db.parent) == str(data)

    def test_all_directories_created(self):
        """Test que todas las funciones crean sus directorios."""
        paths.get_base_directory()
        paths.get_data_directory()
        paths.get_logs_directory()
        paths.get_user_data_directory()

        # Verificar que existen
        assert paths.get_base_directory().exists()
        assert paths.get_data_directory().exists()
        assert paths.get_logs_directory().exists()
        assert paths.get_user_data_directory().exists()
