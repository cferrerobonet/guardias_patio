"""Tests de ramas de configuración y esquema para DataExporter."""

import base64
import json
import sys
from datetime import date, time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infrastructure.database.models import Configuracion
from sync.data_exporter import DataExporter


class TestDataExporterSMTPConfig:
    def test_export_smtp_config_complete(self):
        env = {
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "secret",
            "SMTP_FROM_NAME": "Guardias",
        }
        with (
            patch.dict("os.environ", env, clear=True),
            patch("dotenv.load_dotenv", return_value=True),
        ):
            data = DataExporter._export_smtp_config()
        assert data is not None
        assert data["smtp_server"] == "smtp.example.com"
        assert data["smtp_password"] != "secret"

    def test_export_smtp_config_incomplete(self):
        env = {"SMTP_SERVER": "smtp.example.com", "SMTP_PORT": "587"}
        with (
            patch.dict("os.environ", env, clear=True),
            patch("dotenv.load_dotenv", return_value=True),
        ):
            assert DataExporter._export_smtp_config() is None

    def test_import_smtp_config_incomplete(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ok = DataExporter._import_smtp_config({"smtp_server": "x"})
        assert ok is False

    def test_import_smtp_config_creates_env(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        payload = {
            "smtp_server": "smtp.example.com",
            "smtp_port": "587",
            "smtp_user": "user@example.com",
            "smtp_password": DataExporter._encriptar_password("secret"),
            "smtp_from_name": "Centro",
        }
        ok = DataExporter._import_smtp_config(payload)
        assert ok is True
        content = (tmp_path / ".env").read_text(encoding="utf-8")
        assert "SMTP_SERVER=smtp.example.com" in content
        assert "SMTP_PASSWORD=secret" in content

    def test_import_smtp_config_updates_existing_env(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        env_file = tmp_path / ".env"
        env_file.write_text("SMTP_SERVER=old\nSMTP_PORT=25\nOTHER_VAR=1\n", encoding="utf-8")

        payload = {
            "smtp_server": "new.smtp",
            "smtp_port": "465",
            "smtp_user": "u@x.com",
            "smtp_password": DataExporter._encriptar_password("newpass"),
            "smtp_from_name": "Nuevo",
        }
        ok = DataExporter._import_smtp_config(payload)
        assert ok is True
        content = env_file.read_text(encoding="utf-8")
        assert "SMTP_SERVER=new.smtp" in content
        assert "SMTP_PORT=465" in content
        assert "OTHER_VAR=1" in content


class TestDataExporterSFTPConfig:
    def test_export_sftp_config_complete(self):
        env = {
            "SFTP_HOST": "sftp.example.com",
            "SFTP_PORT": "22",
            "SFTP_BASE_DIR": "/guardias",
            "SFTP_USERNAME": "user",
            "SFTP_PASSWORD": "pwd",
        }
        with (
            patch.dict("os.environ", env, clear=True),
            patch("dotenv.load_dotenv", return_value=True),
        ):
            data = DataExporter._export_sftp_config()
        assert data is not None
        assert data["sftp_host"] == "sftp.example.com"
        assert data["sftp_password"] != "pwd"

    def test_export_sftp_config_incomplete(self):
        env = {"SFTP_HOST": "sftp.example.com"}
        with (
            patch.dict("os.environ", env, clear=True),
            patch("dotenv.load_dotenv", return_value=True),
        ):
            assert DataExporter._export_sftp_config() is None

    def test_import_sftp_config_incomplete(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ok = DataExporter._import_sftp_config({"sftp_host": "x"})
        assert ok is False

    def test_import_sftp_config_creates_env(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        payload = {
            "sftp_host": "sftp.example.com",
            "sftp_port": "22",
            "sftp_base_dir": "/guardias",
            "sftp_username": "user",
            "sftp_password": DataExporter._encriptar_password("secret"),
        }
        ok = DataExporter._import_sftp_config(payload)
        assert ok is True
        content = (tmp_path / ".env").read_text(encoding="utf-8")
        assert "SFTP_HOST=sftp.example.com" in content
        assert "SFTP_PASSWORD=secret" in content


class TestDataExporterDecryptFallbacks:
    def test_decrypt_base64_fallback(self):
        encoded = base64.b64encode("texto".encode("utf-8")).decode("utf-8")
        assert DataExporter._desencriptar_password(encoded) == "texto"

    def test_decrypt_returns_original_if_invalid(self):
        assert DataExporter._desencriptar_password("@@no-valido@@") == "@@no-valido@@"


class TestDataExporterSchemaGuards:
    def _make_session(self):
        session = MagicMock()
        session.bind = MagicMock()
        session.rollback = MagicMock()
        return session

    def test_import_fails_if_profesor_columns_missing(self, tmp_path):
        payload = {"version": "1.0", "export_date": "now"}
        p = tmp_path / "data.json"
        p.write_text(json.dumps(payload), encoding="utf-8")

        session = self._make_session()
        fake_inspector = MagicMock()
        fake_inspector.get_columns.side_effect = [
            [{"name": "id"}, {"name": "nombre_completo"}],  # profesores incompleto
        ]

        with patch("sqlalchemy.inspect", return_value=fake_inspector):
            ok = DataExporter.import_from_json(session, p)

        assert ok is False

    def test_import_fails_if_config_algoritmo_missing(self, tmp_path):
        payload = {"version": "1.0", "export_date": "now"}
        p = tmp_path / "data.json"
        p.write_text(json.dumps(payload), encoding="utf-8")

        session = self._make_session()
        fake_inspector = MagicMock()
        fake_inspector.get_columns.side_effect = [
            [
                {"name": "activo"},
                {"name": "zona_preferida_id"},
                {"name": "dias_semana_permitidos"},
                {"name": "recreos_permitidos"},
                {"name": "fecha_inicio_guardias"},
                {"name": "fecha_fin_guardias"},
            ],
            [{"name": "id"}],  # configuracion sin algoritmo_asignacion
        ]

        with patch("sqlalchemy.inspect", return_value=fake_inspector):
            ok = DataExporter.import_from_json(session, p)

        assert ok is False


class TestDataExporterImportHappyPath:
    def test_import_minimal_json_ok(self, session, tmp_path):
        """Esquema correcto + listas vacías debe completar importación."""
        data = {
            "version": "1.0",
            "export_date": "2026-01-01T10:00:00",
            "cursos_escolares": [],
            "profesores": [],
            "zonas": [],
            "configuracion": [],
            "guardias": [],
            "ausencias": [],
        }
        p = tmp_path / "min.json"
        p.write_text(json.dumps(data), encoding="utf-8")

        assert DataExporter.import_from_json(session, p, clear_existing=True) is True

    def test_export_with_real_config_and_reimport_returns_false(self, session, tmp_path):
        """El export incluye anio_inicio_curso y el reimport debe ser exitoso."""
        config = Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=date(2025, 9, 1),
            fecha_fin_curso=date(2026, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 0),
            hora_recreo1_tarde=time(16, 30),
            hora_recreo2_tarde=time(18, 0),
        )
        session.add(config)
        session.commit()

        out = tmp_path / "exp.json"
        assert DataExporter.export_to_json(session, out) is True
        assert out.exists()
        assert DataExporter.import_from_json(session, out, clear_existing=True) is True
