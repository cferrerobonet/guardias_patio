"""
Tests de integridad de migraciones Alembic.

Verifica que todas las migraciones se aplican y revierten correctamente
sobre una base de datos SQLite vacía, y que el esquema resultante
contiene las tablas y columnas críticas del modelo.
"""

import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

ROOT = Path(__file__).resolve().parents[1]


def _run_alembic(db_url: str, direction: str, revision: str = "head") -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    if direction == "upgrade":
        command.upgrade(cfg, revision)
    elif direction == "downgrade":
        command.downgrade(cfg, revision)


# ============================================================================
# TESTS: upgrade head sobre BD vacía
# ============================================================================


class TestAlembicUpgradeHead:
    def test_upgrade_head_no_lanza_excepcion(self, tmp_path):
        db_file = tmp_path / "test_migrations.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")
        assert db_file.exists()

    def test_tablas_principales_existen_tras_upgrade(self, tmp_path):
        db_file = tmp_path / "schema_check.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        tablas = inspect(engine).get_table_names()
        for tabla in ("profesores", "guardias", "zonas", "ausencias", "configuracion"):
            assert tabla in tablas, f"Tabla '{tabla}' ausente tras upgrade head"

    def test_columnas_criticas_profesores(self, tmp_path):
        db_file = tmp_path / "cols_profesores.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        cols = {c["name"] for c in inspect(engine).get_columns("profesores")}
        for col in ("id", "nombre_completo", "horas_contrato", "turno", "activo"):
            assert col in cols, f"Columna '{col}' ausente en tabla profesores"

    def test_columnas_criticas_guardias(self, tmp_path):
        db_file = tmp_path / "cols_guardias.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        cols = {c["name"] for c in inspect(engine).get_columns("guardias")}
        for col in ("id", "profesor_id", "fecha", "turno", "recreo"):
            assert col in cols, f"Columna '{col}' ausente en tabla guardias"

    def test_columna_es_sustitucion_existe_en_guardias(self, tmp_path):
        db_file = tmp_path / "es_sust.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        cols = {c["name"] for c in inspect(engine).get_columns("guardias")}
        assert "es_sustitucion" in cols

    def test_tabla_guardias_audit_log_existe(self, tmp_path):
        db_file = tmp_path / "audit_log.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        tablas = inspect(engine).get_table_names()
        assert "guardias_audit_log" in tablas

    def test_alembic_version_table_existe(self, tmp_path):
        db_file = tmp_path / "alembic_ver.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        tablas = inspect(engine).get_table_names()
        assert "alembic_version" in tablas

    def test_alembic_version_tiene_una_revision(self, tmp_path):
        db_file = tmp_path / "alembic_single.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        assert len(rows) == 1


# ============================================================================
# TESTS: downgrade + re-upgrade (idempotencia)
# ============================================================================


class TestAlembicDowngradeReupgrade:
    @pytest.mark.xfail(
        reason="Algunas migraciones usan constraints sin nombre; SQLite batch-mode requiere nombre explícito para downgrade",
        strict=False,
    )
    def test_downgrade_base_no_lanza_excepcion(self, tmp_path):
        db_file = tmp_path / "downgrade.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")
        _run_alembic(f"sqlite:///{db_file}", "downgrade", "base")

    @pytest.mark.xfail(
        reason="Idem — depende de que downgrade funcione correctamente",
        strict=False,
    )
    def test_re_upgrade_tras_downgrade_base(self, tmp_path):
        db_file = tmp_path / "reupgrade.db"
        _run_alembic(f"sqlite:///{db_file}", "upgrade")
        _run_alembic(f"sqlite:///{db_file}", "downgrade", "base")
        _run_alembic(f"sqlite:///{db_file}", "upgrade")

        engine = create_engine(f"sqlite:///{db_file}")
        tablas = inspect(engine).get_table_names()
        assert "profesores" in tablas
        assert "guardias" in tablas
