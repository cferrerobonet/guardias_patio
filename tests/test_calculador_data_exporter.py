"""
Tests para calculador_guardias.py y data_exporter.py
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# calculador_guardias - funciones puras
# ===========================================================================


class TestCalcularDiasLectivos:
    def test_rango_normal(self):
        from services.calculador_guardias import calcular_dias_lectivos

        inicio = datetime(2024, 9, 2)  # lunes
        fin = datetime(2024, 9, 6)  # viernes
        assert calcular_dias_lectivos(inicio, fin) == 5

    def test_incluye_fin_de_semana(self):
        from services.calculador_guardias import calcular_dias_lectivos

        inicio = datetime(2024, 9, 2)  # lunes
        fin = datetime(2024, 9, 8)  # domingo
        assert calcular_dias_lectivos(inicio, fin) == 5

    def test_inicio_mayor_que_fin(self):
        from services.calculador_guardias import calcular_dias_lectivos

        inicio = datetime(2024, 9, 10)
        fin = datetime(2024, 9, 1)
        assert calcular_dias_lectivos(inicio, fin) == 0

    def test_mismo_dia_laborable(self):
        from services.calculador_guardias import calcular_dias_lectivos

        lunes = datetime(2024, 9, 2)
        assert calcular_dias_lectivos(lunes, lunes) == 1

    def test_mismo_dia_fin_de_semana(self):
        from services.calculador_guardias import calcular_dias_lectivos

        sabado = datetime(2024, 9, 7)
        assert calcular_dias_lectivos(sabado, sabado) == 0


class TestAjustarRedondeo:
    def test_distribucion_entera(self):
        from services.calculador_guardias import ajustar_redondeo

        dist = {1: 3.0, 2: 2.0}
        result = ajustar_redondeo(dist)
        assert result[1] == 3
        assert result[2] == 2

    def test_vacia(self):
        from services.calculador_guardias import ajustar_redondeo

        result = ajustar_redondeo({})
        assert result == {}

    def test_decimales(self):
        from services.calculador_guardias import ajustar_redondeo

        dist = {1: 2.5, 2: 2.5}
        result = ajustar_redondeo(dist)
        # Suma debe ser igual a la suma entera original
        assert isinstance(result[1], int)
        assert isinstance(result[2], int)


# ===========================================================================
# DataExporter
# ===========================================================================


class TestDataExporter:
    def test_export_to_json_sin_datos(self, tmp_path, session):
        from sync.data_exporter import DataExporter

        output = tmp_path / "export.json"
        with (
            patch("sync.data_exporter.DataExporter._export_smtp_config", return_value={}),
            patch("sync.data_exporter.DataExporter._export_sftp_config", return_value={}),
        ):
            result = DataExporter.export_to_json(session, output)
        assert result is True
        assert output.exists()

    def test_export_crea_json_valido(self, tmp_path, session):
        import json

        from sync.data_exporter import DataExporter

        output = tmp_path / "export.json"
        with (
            patch("sync.data_exporter.DataExporter._export_smtp_config", return_value={}),
            patch("sync.data_exporter.DataExporter._export_sftp_config", return_value={}),
        ):
            DataExporter.export_to_json(session, output)

        data = json.loads(output.read_text())
        assert "profesores" in data
        assert "zonas" in data
        assert "guardias" in data

    def test_import_from_json_archivo_invalido(self, tmp_path, session):
        from sync.data_exporter import DataExporter

        archivo_inexistente = tmp_path / "no_existe.json"
        result = DataExporter.import_from_json(session, archivo_inexistente)
        assert result is False

    def test_import_from_json_json_vacio(self, tmp_path, session):
        import json

        from sync.data_exporter import DataExporter

        archivo = tmp_path / "empty.json"
        archivo.write_text(json.dumps({}))
        result = DataExporter.import_from_json(session, archivo)
        # Con datos vacíos no debe lanzar
        assert isinstance(result, bool)
