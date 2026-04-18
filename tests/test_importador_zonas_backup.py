"""Tests para importador_zonas y backup/restore de BD."""

import csv
import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.database.models import Base, Zona
from services.importador_zonas import (
    _parse_bool,
    _parse_int_or_none,
    importar_zonas,
    importar_zonas_desde_csv,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


@pytest.fixture()
def csv_basico(tmp_path):
    """CSV con 3 zonas válidas."""
    archivo = tmp_path / "zonas.csv"
    archivo.write_text(
        "nombre_zona,descripcion,activa,capacidad_profesores\n"
        "Patio Central,Zona principal,1,3\n"
        "Entrada Principal,,true,\n"
        "Gimnasio,Zona deportiva,si,2\n",
        encoding="utf-8",
    )
    return str(archivo)


@pytest.fixture()
def csv_con_duplicado(tmp_path, session):
    """CSV con una zona que ya existe en BD."""
    session.add(Zona(nombre_zona="Patio Central", activa=True))
    session.commit()

    archivo = tmp_path / "zonas_dup.csv"
    archivo.write_text(
        "nombre_zona,activa\n"
        "Patio Central,1\n"
        "Entrada Secundaria,1\n",
        encoding="utf-8",
    )
    return str(archivo)


@pytest.fixture()
def csv_con_errores(tmp_path):
    """CSV con filas con nombre vacío."""
    archivo = tmp_path / "zonas_err.csv"
    archivo.write_text(
        "nombre_zona,activa\n"
        ",1\n"
        "Zona Válida,1\n"
        "   ,0\n",
        encoding="utf-8",
    )
    return str(archivo)


# ──────────────────────────────────────────────────────────────────────────────
# Tests helpers privados
# ──────────────────────────────────────────────────────────────────────────────


class TestParseBool:
    def test_true_values(self):
        for v in ("1", "true", "True", "si", "sí", "yes", "verdadero"):
            assert _parse_bool(v) is True

    def test_false_values(self):
        for v in ("0", "false", "False", "no", "falso"):
            assert _parse_bool(v) is False

    def test_default_on_unknown(self):
        assert _parse_bool("x", default=True) is True
        assert _parse_bool("x", default=False) is False


class TestParseIntOrNone:
    def test_entero_valido(self):
        assert _parse_int_or_none("3") == 3

    def test_vacio(self):
        assert _parse_int_or_none("") is None

    def test_texto(self):
        assert _parse_int_or_none("abc") is None

    def test_nan(self):
        assert _parse_int_or_none("nan") is None


# ──────────────────────────────────────────────────────────────────────────────
# Tests importar_zonas_desde_csv
# ──────────────────────────────────────────────────────────────────────────────


class TestImportarZonasCsv:
    def test_importa_tres_zonas(self, session, csv_basico):
        res = importar_zonas_desde_csv(session, csv_basico)
        assert res["leidos"] == 3
        assert res["importadas"] == 3
        assert res["existentes"] == 0
        assert res["errores"] == 0
        assert session.query(Zona).count() == 3

    def test_zona_con_capacidad(self, session, csv_basico):
        importar_zonas_desde_csv(session, csv_basico)
        zona = session.query(Zona).filter(Zona.nombre_zona == "Patio Central").first()
        assert zona is not None
        assert zona.capacidad_profesores == 3
        assert zona.activa is True

    def test_zona_sin_capacidad_es_none(self, session, csv_basico):
        importar_zonas_desde_csv(session, csv_basico)
        zona = session.query(Zona).filter(Zona.nombre_zona == "Entrada Principal").first()
        assert zona.capacidad_profesores is None

    def test_duplicado_omitido(self, session, csv_con_duplicado):
        res = importar_zonas_desde_csv(session, csv_con_duplicado)
        assert res["existentes"] == 1
        assert res["importadas"] == 1
        assert session.query(Zona).count() == 2

    def test_filas_nombre_vacio_son_errores(self, session, csv_con_errores):
        res = importar_zonas_desde_csv(session, csv_con_errores)
        assert res["errores"] == 2
        assert res["importadas"] == 1

    def test_progress_callback_llamado(self, session, csv_basico):
        llamadas = []
        importar_zonas_desde_csv(session, csv_basico, progress_callback=lambda p, m: llamadas.append(p))
        assert len(llamadas) > 0

    def test_archivo_inexistente(self, session):
        res = importar_zonas_desde_csv(session, "/no/existe.csv")
        assert res["errores"] == 1

    def test_nombre_archivo_en_resultado(self, session, csv_basico):
        res = importar_zonas_desde_csv(session, csv_basico)
        assert res["archivo"] == "zonas.csv"


# ──────────────────────────────────────────────────────────────────────────────
# Tests importar_zonas (entrada unificada)
# ──────────────────────────────────────────────────────────────────────────────


class TestImportarZonasUnificado:
    def test_csv_detectado(self, session, csv_basico):
        res = importar_zonas(session, csv_basico)
        assert res["importadas"] == 3

    def test_formato_no_soportado(self, session, tmp_path):
        archivo = tmp_path / "zonas.json"
        archivo.write_text("{}")
        res = importar_zonas(session, str(archivo))
        assert res["errores"] == 1
        assert ".json" in res["detalles"][0]


# ──────────────────────────────────────────────────────────────────────────────
# Tests backup_database / restore_database
# ──────────────────────────────────────────────────────────────────────────────


class TestBackupRestore:
    """Tests para backup_database() y restore_database() de db_manager."""

    def _make_temp_db(self, tmp_path: Path) -> Path:
        """Crea una BD SQLite temporal con estructura básica."""
        from sqlalchemy import create_engine

        db_path = tmp_path / "test_user" / "guardias_patio.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        engine.dispose()
        return db_path

    def test_backup_genera_archivo(self, tmp_path, monkeypatch):
        from database import db_manager

        db_path = self._make_temp_db(tmp_path)
        monkeypatch.setattr(db_manager, "USER_DATA_DIR", tmp_path)

        username = "test_user"
        # Simular hash correcto apuntando al directorio creado
        import hashlib
        user_hash = hashlib.sha256(username.encode()).hexdigest()[:16]
        user_dir = tmp_path / user_hash
        user_dir.mkdir(parents=True, exist_ok=True)
        real_db = user_dir / "guardias_patio.db"
        import shutil
        shutil.copy2(db_path, real_db)

        backup_path = db_manager.backup_database(username)
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.suffix == ".db"

    def test_backup_permisos_600(self, tmp_path, monkeypatch):
        from database import db_manager
        import hashlib
        import shutil

        username = "test_perms"
        user_hash = hashlib.sha256(username.encode()).hexdigest()[:16]
        user_dir = tmp_path / user_hash
        user_dir.mkdir(parents=True, exist_ok=True)
        src_db = self._make_temp_db(tmp_path)
        shutil.copy2(src_db, user_dir / "guardias_patio.db")
        monkeypatch.setattr(db_manager, "USER_DATA_DIR", tmp_path)

        backup_path = db_manager.backup_database(username)
        assert backup_path is not None
        stat = os.stat(backup_path)
        assert oct(stat.st_mode)[-3:] == "600"

    def test_backup_usuario_sin_bd_retorna_none(self, tmp_path, monkeypatch):
        from database import db_manager

        monkeypatch.setattr(db_manager, "USER_DATA_DIR", tmp_path)
        result = db_manager.backup_database("usuario_inexistente")
        assert result is None

    def test_restore_desde_backup(self, tmp_path, monkeypatch):
        from database import db_manager
        import hashlib
        import shutil

        username = "test_restore"
        user_hash = hashlib.sha256(username.encode()).hexdigest()[:16]
        user_dir = tmp_path / user_hash
        user_dir.mkdir(parents=True, exist_ok=True)

        src_db = self._make_temp_db(tmp_path)
        shutil.copy2(src_db, user_dir / "guardias_patio.db")
        monkeypatch.setattr(db_manager, "USER_DATA_DIR", tmp_path)

        # Crear backup y restaurar
        backup_path = db_manager.backup_database(username)
        assert backup_path is not None

        ok = db_manager.restore_database(username, backup_path)
        assert ok is True

    def test_restore_archivo_inexistente(self, tmp_path, monkeypatch):
        from database import db_manager

        monkeypatch.setattr(db_manager, "USER_DATA_DIR", tmp_path)
        ok = db_manager.restore_database("cualquier_usuario", "/no/existe.db")
        assert ok is False

    def test_restore_archivo_invalido(self, tmp_path, monkeypatch):
        from database import db_manager

        monkeypatch.setattr(db_manager, "USER_DATA_DIR", tmp_path)
        archivo_malo = tmp_path / "not_a_db.db"
        archivo_malo.write_bytes(b"esto no es sqlite")

        ok = db_manager.restore_database("cualquier_usuario", archivo_malo)
        assert ok is False
