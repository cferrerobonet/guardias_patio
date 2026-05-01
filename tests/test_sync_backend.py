"""
Tests para el sistema de sincronización (sync/).

Cubre: LocalSyncBackend (upload, download, exists, path traversal),
DataExporter (export/import JSON), backend_factory.
No requiere servidor SFTP real — usa mocks y backend local.
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infrastructure.database.models import Base, Configuracion, CursoEscolar, Profesor, Zona
from sync.sync_manager import LocalSyncBackend


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def base_dir(tmp_path):
    return tmp_path / "sync_base"


@pytest.fixture
def backend(base_dir):
    return LocalSyncBackend(base_dir)


@pytest.fixture
def session_vacia():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()


@pytest.fixture
def session_con_datos(session_vacia):
    db = session_vacia
    curso = CursoEscolar(
        nombre="2025-2026",
        anio_inicio=2025,
        anio_fin=2026,
        fecha_inicio=datetime(2025, 9, 1).date(),
        fecha_fin=datetime(2026, 6, 30).date(),
    )
    db.add(curso)
    db.flush()
    zona = Zona(nombre_zona="Patio Export")
    prof = Profesor(nombre_completo="Export Profesor", horas_contrato=20.0, porcentaje_jornada=80.0, turno="mañana")
    db.add_all([zona, prof])
    db.commit()
    return db


# ============================================================================
# TESTS: LocalSyncBackend — upload
# ============================================================================


class TestLocalSyncBackendUpload:
    def test_upload_archivo_existente(self, backend, tmp_path):
        src = tmp_path / "file.json"
        src.write_text('{"ok": true}')
        result = backend.upload_file(src, "subdir/file.json")
        assert result is True
        assert (backend.base_path / "subdir" / "file.json").exists()

    def test_upload_crea_directorios_intermedios(self, backend, tmp_path):
        src = tmp_path / "data.txt"
        src.write_text("data")
        backend.upload_file(src, "a/b/c/data.txt")
        assert (backend.base_path / "a" / "b" / "c" / "data.txt").exists()

    def test_upload_path_traversal_retorna_false(self, backend, tmp_path):
        src = tmp_path / "evil.txt"
        src.write_text("evil")
        result = backend.upload_file(src, "../outside.txt")
        assert result is False

    def test_upload_path_traversal_doble_retorna_false(self, backend, tmp_path):
        src = tmp_path / "evil.txt"
        src.write_text("evil")
        result = backend.upload_file(src, "../../etc/passwd")
        assert result is False

    def test_upload_sobreescribe_archivo_existente(self, backend, tmp_path):
        src = tmp_path / "update.json"
        src.write_text("original")
        backend.upload_file(src, "update.json")
        src.write_text("updated")
        backend.upload_file(src, "update.json")
        assert (backend.base_path / "update.json").read_text() == "updated"


# ============================================================================
# TESTS: LocalSyncBackend — download
# ============================================================================


class TestLocalSyncBackendDownload:
    def test_download_archivo_existente(self, backend, tmp_path):
        (backend.base_path / "remote.json").write_text('{"x": 1}')
        dest = tmp_path / "local.json"
        result = backend.download_file("remote.json", dest)
        assert result is True
        assert dest.read_text() == '{"x": 1}'

    def test_download_archivo_inexistente_retorna_false(self, backend, tmp_path):
        dest = tmp_path / "nope.json"
        result = backend.download_file("no_existe.json", dest)
        assert result is False
        assert not dest.exists()

    def test_download_path_traversal_retorna_false(self, backend, tmp_path):
        dest = tmp_path / "dest.txt"
        result = backend.download_file("../../etc/shadow", dest)
        assert result is False

    def test_download_crea_directorio_destino(self, backend, tmp_path):
        (backend.base_path / "data.json").write_text("{}")
        dest = tmp_path / "deep" / "nested" / "out.json"
        result = backend.download_file("data.json", dest)
        assert result is True
        assert dest.exists()


# ============================================================================
# TESTS: LocalSyncBackend — file_exists y get_last_modified
# ============================================================================


class TestLocalSyncBackendFileOps:
    def test_file_exists_verdadero(self, backend):
        (backend.base_path / "presente.json").write_text("{}")
        assert backend.file_exists("presente.json") is True

    def test_file_exists_falso(self, backend):
        assert backend.file_exists("no_existe.json") is False

    def test_get_last_modified_retorna_datetime(self, backend):
        (backend.base_path / "ts.json").write_text("{}")
        result = backend.get_last_modified("ts.json")
        assert isinstance(result, datetime)

    def test_get_last_modified_archivo_inexistente_retorna_none(self, backend):
        result = backend.get_last_modified("fantasma.json")
        assert result is None


# ============================================================================
# TESTS: LocalSyncBackend — _safe_path directamente
# ============================================================================


class TestSafePath:
    def test_safe_path_ruta_normal(self, backend):
        path = backend._safe_path("folder/file.json")
        assert str(path).startswith(str(backend.base_path))

    def test_safe_path_traversal_raises_value_error(self, backend):
        with pytest.raises(ValueError):
            backend._safe_path("../outside")

    def test_safe_path_traversal_profundo_raises(self, backend):
        with pytest.raises(ValueError):
            backend._safe_path("a/b/../../../escape")

    def test_safe_path_solo_nombre_de_fichero(self, backend):
        path = backend._safe_path("archivo.db")
        assert path.name == "archivo.db"


# ============================================================================
# TESTS: DataExporter — export_to_json
# ============================================================================


class TestDataExporterExport:
    def test_export_crea_fichero_json(self, session_con_datos, tmp_path):
        from sync.data_exporter import DataExporter

        output = tmp_path / "export.json"
        result = DataExporter.export_to_json(session_con_datos, output)
        assert result is True
        assert output.exists()

    def test_export_json_tiene_claves_obligatorias(self, session_con_datos, tmp_path):
        from sync.data_exporter import DataExporter

        output = tmp_path / "export.json"
        DataExporter.export_to_json(session_con_datos, output)
        data = json.loads(output.read_text())
        for key in ("profesores", "zonas", "guardias", "ausencias", "export_date"):
            assert key in data, f"Clave '{key}' ausente en el JSON exportado"

    def test_export_incluye_profesores(self, session_con_datos, tmp_path):
        from sync.data_exporter import DataExporter

        output = tmp_path / "export.json"
        DataExporter.export_to_json(session_con_datos, output)
        data = json.loads(output.read_text())
        assert len(data["profesores"]) >= 1

    def test_export_incluye_zonas(self, session_con_datos, tmp_path):
        from sync.data_exporter import DataExporter

        output = tmp_path / "export.json"
        DataExporter.export_to_json(session_con_datos, output)
        data = json.loads(output.read_text())
        assert len(data["zonas"]) >= 1

    def test_export_sesion_vacia_retorna_true(self, session_vacia, tmp_path):
        from sync.data_exporter import DataExporter

        output = tmp_path / "empty.json"
        result = DataExporter.export_to_json(session_vacia, output)
        assert result is True


# ============================================================================
# TESTS: backend_factory
# ============================================================================


class TestBackendFactory:
    def test_crear_backend_local_retorna_local_backend(self):
        from sync.backend_factory import create_sync_backend

        backend = create_sync_backend("local")
        assert isinstance(backend, LocalSyncBackend)

    def test_crear_backend_tipo_desconocido_lanza_value_error(self):
        from sync.backend_factory import create_sync_backend

        with pytest.raises(ValueError, match="Backend desconocido"):
            create_sync_backend("unknown_type")
