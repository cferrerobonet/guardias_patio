"""
Tests para importadores CSV/Excel y DataExporter (métodos estáticos).
"""

import csv
import sys
import tempfile
from datetime import date, datetime, time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infrastructure.database.models import Base, Zona, Profesor
from services.importador_zonas import (
    _parse_bool,
    _parse_int_or_none,
    importar_zonas_desde_csv,
    importar_zonas,
)
from services.importador_profesores import normalizar_nombre, importar_profesores_desde_csv
from sync.data_exporter import DataExporter


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures BD
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine_imp():
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session_imp(engine_imp) -> Session:
    conn = engine_imp.connect()
    txn = conn.begin()
    sess = sessionmaker(bind=conn)()
    yield sess
    sess.rollback()
    sess.close()
    if txn.is_active:
        txn.rollback()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — funciones puras de importador_zonas
# ─────────────────────────────────────────────────────────────────────────────


class TestParseBool:
    def test_true_variants(self):
        for val in ["1", "true", "si", "sí", "yes", "verdadero", "TRUE", "SI"]:
            assert _parse_bool(val) is True

    def test_false_variants(self):
        for val in ["0", "false", "no", "falso", "FALSE", "NO"]:
            assert _parse_bool(val) is False

    def test_default_true_on_unknown(self):
        assert _parse_bool("desconocido", default=True) is True

    def test_default_false_on_unknown(self):
        assert _parse_bool("desconocido", default=False) is False


class TestParseIntOrNone:
    def test_entero_valido(self):
        assert _parse_int_or_none("5") == 5

    def test_string_invalido(self):
        assert _parse_int_or_none("abc") is None

    def test_none_devuelve_none(self):
        assert _parse_int_or_none(None) is None

    def test_float_string(self):
        assert _parse_int_or_none("3.5") is None


# ─────────────────────────────────────────────────────────────────────────────
# importar_zonas_desde_csv
# ─────────────────────────────────────────────────────────────────────────────


class TestImportarZonasDesdeCSV:
    def _crear_csv(self, filas: list[dict], path: str):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=filas[0].keys())
            writer.writeheader()
            writer.writerows(filas)

    def test_importa_zonas_correctamente(self, session_imp):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            ruta = f.name
        self._crear_csv([{"nombre_zona": "Patio Norte", "activa": "1", "capacidad_profesores": "3"}], ruta)
        result = importar_zonas_desde_csv(session_imp, ruta)
        assert result["importadas"] == 1
        assert result["errores"] == 0
        Path(ruta).unlink(missing_ok=True)

    def test_fila_sin_nombre_zona(self, session_imp):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            ruta = f.name
        self._crear_csv([{"nombre_zona": ""}], ruta)
        result = importar_zonas_desde_csv(session_imp, ruta)
        assert result["errores"] == 1
        Path(ruta).unlink(missing_ok=True)

    def test_zona_ya_existente(self, session_imp):
        """Segunda importación de la misma zona → cuenta como existente."""
        zona = Zona(nombre_zona="Patio Sur")
        session_imp.add(zona)
        session_imp.flush()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            ruta = f.name
        self._crear_csv([{"nombre_zona": "Patio Sur"}], ruta)
        result = importar_zonas_desde_csv(session_imp, ruta)
        assert result["existentes"] == 1
        assert result["importadas"] == 0
        Path(ruta).unlink(missing_ok=True)

    def test_archivo_no_existe(self, session_imp):
        result = importar_zonas_desde_csv(session_imp, "/tmp/no_existe_jamás.csv")
        assert result["errores"] >= 1

    def test_progress_callback_llamado(self, session_imp):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            ruta = f.name
        self._crear_csv([{"nombre_zona": "Test Callback"}], ruta)
        llamadas = []
        importar_zonas_desde_csv(session_imp, ruta, progress_callback=lambda p, m: llamadas.append(p))
        assert len(llamadas) > 0
        Path(ruta).unlink(missing_ok=True)

    def test_importar_zonas_delega_a_csv(self, session_imp):
        """importar_zonas() con archivo .csv delega correctamente."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            ruta = f.name
        self._crear_csv([{"nombre_zona": "Delega CSV"}], ruta)
        result = importar_zonas(session_imp, ruta)
        assert "importadas" in result
        Path(ruta).unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# importador_profesores — funciones puras
# ─────────────────────────────────────────────────────────────────────────────


class TestNormalizarNombre:
    def test_normaliza_mayusculas(self):
        assert normalizar_nombre("juan garcía") == "JUAN GARCÍA"

    def test_elimina_espacios_extra(self):
        assert normalizar_nombre("  JUAN   GARCÍA  ") == "JUAN GARCÍA"

    def test_nombre_vacio(self):
        assert normalizar_nombre("") == ""


class TestImportarProfesoresDesdeCSV:
    def _crear_csv_prof(self, filas: list[dict], path: str):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=filas[0].keys())
            writer.writeheader()
            writer.writerows(filas)

    def test_importa_profesor_correctamente(self, session_imp):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            ruta = f.name
        self._crear_csv_prof(
            [{"nombre_completo": "NUEVO, PROFESOR", "turno": "mañana", "horas_contrato": "25", "porcentaje_jornada": "100", "activo": "1"}],
            ruta,
        )
        result = importar_profesores_desde_csv(session_imp, ruta)
        assert result["importados"] >= 1 or result["errores"] == 0
        Path(ruta).unlink(missing_ok=True)

    def test_archivo_no_existe(self, session_imp):
        result = importar_profesores_desde_csv(session_imp, "/tmp/no_existe_jamás.csv")
        assert result["errores"] >= 1


# ─────────────────────────────────────────────────────────────────────────────
# DataExporter — métodos estáticos (sin BD)
# ─────────────────────────────────────────────────────────────────────────────


class TestDataExporterEstaticos:
    def test_serialize_date(self):
        d = date(2025, 10, 15)
        assert DataExporter._serialize_date(d) == "2025-10-15"

    def test_serialize_datetime(self):
        dt = datetime(2025, 10, 15, 10, 30)
        result = DataExporter._serialize_date(dt)
        assert "2025-10-15" in result

    def test_serialize_string_fallback(self):
        assert DataExporter._serialize_date("texto") == "texto"

    def test_parse_date_valida(self):
        result = DataExporter._parse_date("2025-10-15")
        assert result == date(2025, 10, 15)

    def test_parse_date_none(self):
        assert DataExporter._parse_date(None) is None

    def test_parse_date_invalida(self):
        assert DataExporter._parse_date("no-es-fecha") is None

    def test_parse_date_ya_es_date(self):
        d = date(2025, 10, 15)
        assert DataExporter._parse_date(d) == d

    def test_parse_time_valida(self):
        result = DataExporter._parse_time("10:30:00")
        assert result == time(10, 30, 0)

    def test_parse_time_none(self):
        assert DataExporter._parse_time(None) is None

    def test_parse_time_invalida(self):
        assert DataExporter._parse_time("no-es-hora") is None

    def test_parse_time_ya_es_time(self):
        t = time(10, 30)
        assert DataExporter._parse_time(t) == t

    def test_encriptar_desencriptar(self):
        original = "mi_password_segura"
        encriptado = DataExporter._encriptar_password(original)
        assert encriptado != original
        desencriptado = DataExporter._desencriptar_password(encriptado)
        assert desencriptado == original

    def test_encriptar_vacio(self):
        assert DataExporter._encriptar_password("") == ""

    def test_desencriptar_vacio(self):
        assert DataExporter._desencriptar_password("") == ""


# ─────────────────────────────────────────────────────────────────────────────
# DataExporter — export/import con BD en memoria
# ─────────────────────────────────────────────────────────────────────────────


class TestDataExporterBD:
    @pytest.fixture
    def session_export(self, engine_imp) -> Session:
        conn = engine_imp.connect()
        txn = conn.begin()
        sess = sessionmaker(bind=conn)()
        yield sess
        sess.rollback()
        sess.close()
        if txn.is_active:
            txn.rollback()
        conn.close()

    def test_export_to_json(self, session_export):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            ruta = Path(f.name)
        result = DataExporter.export_to_json(session_export, ruta)
        assert result is True
        contenido = ruta.read_text(encoding="utf-8")
        import json
        data = json.loads(contenido)
        assert "profesores" in data
        assert "zonas" in data
        ruta.unlink(missing_ok=True)

    def test_import_from_json_archivo_no_existe(self, session_export):
        result = DataExporter.import_from_json(session_export, Path("/tmp/no_existe.json"))
        assert result is False

    def test_roundtrip_export_import(self, session_export):
        """Exporta a JSON e importa de vuelta sin error."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            ruta = Path(f.name)
        DataExporter.export_to_json(session_export, ruta)
        result = DataExporter.import_from_json(session_export, ruta, clear_existing=True)
        assert result is True
        ruta.unlink(missing_ok=True)
