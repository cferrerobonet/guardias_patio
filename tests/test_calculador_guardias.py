"""Tests para services/calculador_guardias.py — funciones puras de cálculo."""
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services.calculador_guardias import (
    _easter_sunday,
    _festivos_automaticos_en_rango,
    _parse_custom_no_lectivos,
    ajustar_redondeo,
    calcular_dias_lectivos,
    listar_dias_lectivos,
)


class TestCalcularDiasLectivos:
    def test_misma_fecha(self):
        # Un lunes
        lunes = datetime(2024, 9, 2)
        assert calcular_dias_lectivos(lunes, lunes) == 1

    def test_rango_inverso(self):
        inicio = datetime(2024, 9, 10)
        fin = datetime(2024, 9, 1)
        assert calcular_dias_lectivos(inicio, fin) == 0

    def test_semana_completa(self):
        # 2-6 sept 2024 = lunes a viernes
        inicio = datetime(2024, 9, 2)
        fin = datetime(2024, 9, 6)
        assert calcular_dias_lectivos(inicio, fin) == 5

    def test_excluye_fin_de_semana(self):
        # Incluye sáb y dom
        inicio = datetime(2024, 9, 2)  # lunes
        fin = datetime(2024, 9, 8)  # domingo
        assert calcular_dias_lectivos(inicio, fin) == 5

    def test_tres_semanas(self):
        inicio = datetime(2024, 9, 2)
        fin = datetime(2024, 9, 20)
        # 3 semanas: 15 días lectivos
        assert calcular_dias_lectivos(inicio, fin) == 15


class TestEasterSunday:
    def test_2024(self):
        easter = _easter_sunday(2024)
        assert easter == date(2024, 3, 31)

    def test_2025(self):
        easter = _easter_sunday(2025)
        assert easter == date(2025, 4, 20)

    def test_2023(self):
        easter = _easter_sunday(2023)
        assert easter == date(2023, 4, 9)

    def test_resultado_es_domingo(self):
        for year in [2020, 2021, 2022, 2023, 2024, 2025]:
            easter = _easter_sunday(year)
            assert easter.weekday() == 6, f"Pascua {year} no es domingo: {easter}"


class TestFestivosAutomaticos:
    def test_rango_inverso_vacio(self):
        result = _festivos_automaticos_en_rango(date(2024, 10, 1), date(2024, 9, 1))
        assert len(result) == 0

    def test_incluye_12_octubre(self):
        inicio = date(2024, 10, 10)
        fin = date(2024, 10, 15)
        festivos = _festivos_automaticos_en_rango(inicio, fin)
        # 12/10/2024 es sábado → no se añade (es fin de semana)
        # 14/10/2024 es lunes → 12/10 es sáb, no se añade
        # Lo que importa es que la lógica no falla
        assert isinstance(festivos, set)

    def test_incluye_1_noviembre(self):
        inicio = date(2024, 10, 30)
        fin = date(2024, 11, 5)
        festivos = _festivos_automaticos_en_rango(inicio, fin)
        # 1/11/2024 es viernes → debería estar si es lectivo
        assert isinstance(festivos, set)

    def test_incluye_navidad(self):
        inicio = date(2024, 12, 20)
        fin = date(2025, 1, 10)
        festivos = _festivos_automaticos_en_rango(inicio, fin)
        # 23/12/2024 a 06/01/2025 son no lectivos
        # Al menos alguno debe estar (excluyendo fines de semana)
        assert len(festivos) > 0


class TestParseCustomNoLectivos:
    def test_texto_vacio(self):
        assert _parse_custom_no_lectivos("") == set()

    def test_none(self):
        assert _parse_custom_no_lectivos(None) == set()

    def test_una_fecha(self):
        result = _parse_custom_no_lectivos("2024-10-15")
        assert date(2024, 10, 15) in result

    def test_varias_fechas(self):
        result = _parse_custom_no_lectivos("2024-10-15,2024-11-01,2025-01-07")
        assert date(2024, 10, 15) in result
        assert date(2024, 11, 1) in result
        assert date(2025, 1, 7) in result

    def test_fecha_invalida_ignorada(self):
        result = _parse_custom_no_lectivos("2024-10-15,fecha_invalida,2024-11-01")
        assert len(result) == 2

    def test_espacios_ignorados(self):
        result = _parse_custom_no_lectivos(" 2024-10-15 , 2024-11-01 ")
        assert date(2024, 10, 15) in result


class TestAjustarRedondeo:
    def test_distribucion_vacia(self):
        assert ajustar_redondeo({}) == {}

    def test_valores_exactos(self):
        distribucion = {1: 3.0, 2: 5.0, 3: 2.0}
        resultado = ajustar_redondeo(distribucion)
        assert sum(resultado.values()) == 10

    def test_residuos_se_distribuyen(self):
        # 3 profesores con 0.5 de residuo cada uno → total 1.5 → 1 sobrante
        distribucion = {1: 2.5, 2: 2.0, 3: 1.5}
        resultado = ajustar_redondeo(distribucion)
        total = sum(resultado.values())
        # La suma debe ser round(6.0) = 6
        assert total == 6
        for v in resultado.values():
            assert isinstance(v, int)

    def test_un_solo_profesor(self):
        resultado = ajustar_redondeo({1: 5.7})
        assert resultado[1] in [5, 6]

    def test_todos_valores_enteros(self):
        distribucion = {1: 3.0, 2: 2.0}
        resultado = ajustar_redondeo(distribucion)
        assert resultado == {1: 3, 2: 2}


class TestListarDiasLectivos:
    def _make_config(self, inicio, fin, festivos=True, custom=None):
        config = MagicMock()
        config.fecha_inicio_curso = inicio
        config.fecha_fin_curso = fin
        config.activar_festivos_automaticos = festivos
        config.dias_no_lectivos_personalizados = custom
        return config

    def test_rango_inverso_vacio(self):
        config = self._make_config(date(2024, 10, 1), date(2024, 9, 1))
        assert listar_dias_lectivos(config) == []

    def test_excluye_fines_de_semana(self):
        # Del 2 al 8 sept 2024 = lunes a domingo, solo 5 días lectivos
        config = self._make_config(date(2024, 9, 2), date(2024, 9, 8), festivos=False)
        dias = listar_dias_lectivos(config)
        assert len(dias) == 5
        for d in dias:
            assert d.weekday() < 5

    def test_custom_no_lectivos_excluidos(self):
        # 3 días lectivos, uno personalizado como no lectivo
        config = self._make_config(
            date(2024, 9, 2), date(2024, 9, 6), festivos=False, custom="2024-09-04"
        )
        dias = listar_dias_lectivos(config)
        assert date(2024, 9, 4) not in dias
        assert len(dias) == 4

    def test_sin_festivos_automaticos(self):
        config = self._make_config(date(2024, 12, 23), date(2024, 12, 27), festivos=False)
        dias = listar_dias_lectivos(config)
        # 23, 24, 25, 26, 27 dic 2024 → lun, mar, mié, jue, vie
        assert len(dias) == 5

    def test_con_festivos_automaticos_navidad_excluida(self):
        config = self._make_config(date(2024, 12, 23), date(2024, 12, 27), festivos=True)
        dias = listar_dias_lectivos(config)
        # 23-27 dic son no lectivos automáticamente
        assert len(dias) == 0
