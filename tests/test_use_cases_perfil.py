"""
Tests para use cases de gestión de perfiles de usuario.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from application.dtos.perfil_dto import (
    ActualizarPerfilDTO,
    CambiarPasswordDTO,
    CrearPerfilDTO,
)
from application.use_cases.perfil.actualizar_perfil import ActualizarPerfilUseCase
from application.use_cases.perfil.cambiar_password import CambiarPasswordUseCase
from application.use_cases.perfil.crear_perfil import CrearPerfilUseCase
from application.use_cases.perfil.eliminar_perfil import EliminarPerfilUseCase
from application.use_cases.perfil.listar_perfiles import ListarPerfilesUseCase
from core.exceptions import NotFoundError, ValidationError


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: UserAuth mockeado
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_user_auth():
    """UserAuth mock con datos de prueba."""
    auth = MagicMock()
    auth.users = {
        "admin": {"email": "admin@test.com", "password_hash": "hash1"},
    }
    auth.validate_password_policy.return_value = (True, "OK")
    auth.register_user.return_value = True
    auth.unregister_user.return_value = True
    auth.authenticate.return_value = (True, "OK")
    auth._save_users = MagicMock()
    return auth


# ─────────────────────────────────────────────────────────────────────────────
# CrearPerfilUseCase
# ─────────────────────────────────────────────────────────────────────────────


class TestCrearPerfilUseCase:
    def test_crea_perfil_correctamente(self, mock_user_auth):
        mock_user_auth.users = {}
        with (
            patch("application.use_cases.perfil.crear_perfil.create_user_database", return_value=True),
            patch("application.use_cases.perfil.crear_perfil.get_current_user_id", return_value=None),
        ):
            uc = CrearPerfilUseCase(mock_user_auth)
            dto = CrearPerfilDTO(username="nuevo", email="nuevo@test.com", password="Abc1234!")
            result = uc.execute(dto)
        assert result.username == "nuevo"
        assert result.email == "nuevo@test.com"
        assert result.tiene_bd is True

    def test_falla_si_username_vacio(self, mock_user_auth):
        uc = CrearPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="obligatorio"):
            uc.execute(CrearPerfilDTO(username="  ", email="a@b.com", password="Abc1234!"))

    def test_falla_si_email_invalido(self, mock_user_auth):
        mock_user_auth.users = {}
        uc = CrearPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="email"):
            uc.execute(CrearPerfilDTO(username="usr", email="no-email", password="Abc1234!"))

    def test_falla_si_email_vacio(self, mock_user_auth):
        mock_user_auth.users = {}
        uc = CrearPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="obligatorio"):
            uc.execute(CrearPerfilDTO(username="usr", email="", password="Abc1234!"))

    def test_falla_si_password_vacio(self, mock_user_auth):
        mock_user_auth.users = {}
        uc = CrearPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError):
            uc.execute(CrearPerfilDTO(username="usr", email="a@b.com", password=""))

    def test_falla_si_password_no_cumple_politica(self, mock_user_auth):
        mock_user_auth.users = {}
        mock_user_auth.validate_password_policy.return_value = (False, "Demasiado corta")
        uc = CrearPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="Demasiado corta"):
            uc.execute(CrearPerfilDTO(username="usr", email="a@b.com", password="123"))

    def test_falla_si_usuario_ya_existe(self, mock_user_auth):
        uc = CrearPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="Ya existe"):
            uc.execute(CrearPerfilDTO(username="admin", email="a@b.com", password="Abc1234!"))

    def test_falla_si_register_user_falla(self, mock_user_auth):
        mock_user_auth.users = {}
        mock_user_auth.register_user.return_value = False
        uc = CrearPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="No se pudo crear"):
            uc.execute(CrearPerfilDTO(username="usr", email="a@b.com", password="Abc1234!"))

    def test_falla_y_revierte_si_bd_falla(self, mock_user_auth):
        mock_user_auth.users = {}
        with (
            patch("application.use_cases.perfil.crear_perfil.create_user_database", return_value=False),
        ):
            uc = CrearPerfilUseCase(mock_user_auth)
            with pytest.raises(ValidationError, match="base de datos"):
                uc.execute(CrearPerfilDTO(username="usr", email="a@b.com", password="Abc1234!"))
        mock_user_auth.unregister_user.assert_called_once_with("usr")


# ─────────────────────────────────────────────────────────────────────────────
# ListarPerfilesUseCase
# ─────────────────────────────────────────────────────────────────────────────


class TestListarPerfilesUseCase:
    def test_lista_perfiles(self, mock_user_auth):
        with (
            patch("application.use_cases.perfil.listar_perfiles.user_has_database", return_value=True),
            patch("application.use_cases.perfil.listar_perfiles.get_current_user_id", return_value="admin"),
        ):
            uc = ListarPerfilesUseCase(mock_user_auth)
            result = uc.execute()
        assert len(result) == 1
        assert result[0].username == "admin"
        assert result[0].es_actual is True

    def test_lista_vacia_sin_usuarios(self, mock_user_auth):
        mock_user_auth.users = {}
        with (
            patch("application.use_cases.perfil.listar_perfiles.user_has_database", return_value=False),
            patch("application.use_cases.perfil.listar_perfiles.get_current_user_id", return_value=None),
        ):
            uc = ListarPerfilesUseCase(mock_user_auth)
            result = uc.execute()
        assert result == []

    def test_usuario_actual_aparece_primero(self, mock_user_auth):
        mock_user_auth.users = {
            "zzz": {"email": "z@z.com"},
            "aaa": {"email": "a@a.com"},
        }
        with (
            patch("application.use_cases.perfil.listar_perfiles.user_has_database", return_value=True),
            patch("application.use_cases.perfil.listar_perfiles.get_current_user_id", return_value="zzz"),
        ):
            uc = ListarPerfilesUseCase(mock_user_auth)
            result = uc.execute()
        assert result[0].username == "zzz"
        assert result[0].es_actual is True


# ─────────────────────────────────────────────────────────────────────────────
# ActualizarPerfilUseCase
# ─────────────────────────────────────────────────────────────────────────────


class TestActualizarPerfilUseCase:
    def test_actualiza_email_correctamente(self, mock_user_auth):
        with (
            patch("application.use_cases.perfil.actualizar_perfil.user_has_database", return_value=True),
            patch("application.use_cases.perfil.actualizar_perfil.get_current_user_id", return_value="admin"),
        ):
            uc = ActualizarPerfilUseCase(mock_user_auth)
            result = uc.execute(ActualizarPerfilDTO(username="admin", email="nuevo@test.com"))
        assert result.email == "nuevo@test.com"
        assert mock_user_auth._save_users.called

    def test_falla_si_usuario_no_existe(self, mock_user_auth):
        uc = ActualizarPerfilUseCase(mock_user_auth)
        with pytest.raises(NotFoundError):
            uc.execute(ActualizarPerfilDTO(username="noexiste", email="x@x.com"))

    def test_falla_si_email_invalido(self, mock_user_auth):
        uc = ActualizarPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="email"):
            uc.execute(ActualizarPerfilDTO(username="admin", email="invalido"))

    def test_falla_si_email_vacio(self, mock_user_auth):
        uc = ActualizarPerfilUseCase(mock_user_auth)
        with pytest.raises(ValidationError, match="obligatorio"):
            uc.execute(ActualizarPerfilDTO(username="admin", email="  "))


# ─────────────────────────────────────────────────────────────────────────────
# EliminarPerfilUseCase
# ─────────────────────────────────────────────────────────────────────────────


class TestEliminarPerfilUseCase:
    def test_elimina_perfil_correctamente(self, mock_user_auth):
        with (
            patch("application.use_cases.perfil.eliminar_perfil.delete_user_database", return_value=True),
            patch("application.use_cases.perfil.eliminar_perfil.get_current_user_id", return_value="otro"),
        ):
            uc = EliminarPerfilUseCase(mock_user_auth)
            result = uc.execute("admin")
        assert result is True
        mock_user_auth.unregister_user.assert_called_once_with("admin")

    def test_falla_si_usuario_no_existe(self, mock_user_auth):
        uc = EliminarPerfilUseCase(mock_user_auth)
        with pytest.raises(NotFoundError):
            uc.execute("noexiste")

    def test_falla_si_intenta_eliminar_usuario_actual(self, mock_user_auth):
        with (
            patch("application.use_cases.perfil.eliminar_perfil.get_current_user_id", return_value="admin"),
        ):
            uc = EliminarPerfilUseCase(mock_user_auth)
            with pytest.raises(ValidationError, match="logueado"):
                uc.execute("admin")


# ─────────────────────────────────────────────────────────────────────────────
# CambiarPasswordUseCase
# ─────────────────────────────────────────────────────────────────────────────


class TestCambiarPasswordUseCase:
    def test_cambia_password_correctamente(self, mock_user_auth):
        with patch("application.use_cases.perfil.cambiar_password.get_current_user_id", return_value="admin"):
            uc = CambiarPasswordUseCase(mock_user_auth)
            result = uc.execute(
                CambiarPasswordDTO(
                    username="admin",
                    password_actual="Abc1234!",
                    password_nueva="Xyz9876@",
                    password_confirmacion="Xyz9876@",
                )
            )
        assert result is True
        assert mock_user_auth._save_users.called

    def test_falla_si_no_es_usuario_actual(self, mock_user_auth):
        with patch("application.use_cases.perfil.cambiar_password.get_current_user_id", return_value="otro"):
            uc = CambiarPasswordUseCase(mock_user_auth)
            with pytest.raises(ValidationError, match="propia"):
                uc.execute(
                    CambiarPasswordDTO(
                        username="admin",
                        password_actual="Abc1234!",
                        password_nueva="Xyz9876@",
                        password_confirmacion="Xyz9876@",
                    )
                )

    def test_falla_si_passwords_no_coinciden(self, mock_user_auth):
        with patch("application.use_cases.perfil.cambiar_password.get_current_user_id", return_value="admin"):
            uc = CambiarPasswordUseCase(mock_user_auth)
            with pytest.raises(ValidationError, match="coinciden"):
                uc.execute(
                    CambiarPasswordDTO(
                        username="admin",
                        password_actual="Abc1234!",
                        password_nueva="Xyz9876@",
                        password_confirmacion="DISTINTA",
                    )
                )

    def test_falla_si_policy_no_cumplida(self, mock_user_auth):
        mock_user_auth.validate_password_policy.return_value = (False, "Muy corta")
        with patch("application.use_cases.perfil.cambiar_password.get_current_user_id", return_value="admin"):
            uc = CambiarPasswordUseCase(mock_user_auth)
            with pytest.raises(ValidationError, match="Muy corta"):
                uc.execute(
                    CambiarPasswordDTO(
                        username="admin",
                        password_actual="Abc1234!",
                        password_nueva="123",
                        password_confirmacion="123",
                    )
                )

    def test_falla_si_password_actual_incorrecta(self, mock_user_auth):
        mock_user_auth.authenticate.return_value = (False, "Incorrecta")
        with patch("application.use_cases.perfil.cambiar_password.get_current_user_id", return_value="admin"):
            uc = CambiarPasswordUseCase(mock_user_auth)
            with pytest.raises(ValidationError, match="incorrecta"):
                uc.execute(
                    CambiarPasswordDTO(
                        username="admin",
                        password_actual="mala",
                        password_nueva="Xyz9876@",
                        password_confirmacion="Xyz9876@",
                    )
                )
