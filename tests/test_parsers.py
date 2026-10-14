"""Tests para application/use_cases/profesor/parsers.py."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from application.use_cases.profesor.parsers import (
    parse_dias_semana,
    parse_json_field,
    parse_recreos,
)


class TestParseJsonField:
    def test_none_devuelve_default(self):
        assert parse_json_field(None, []) == []

    def test_cadena_vacia_devuelve_default(self):
        assert parse_json_field("", "default") == "default"

    def test_lista_directa(self):
        assert parse_json_field([1, 2, 3], []) == [1, 2, 3]

    def test_dict_directo(self):
        d = {"key": "val"}
        assert parse_json_field(d, {}) == d

    def test_json_string_lista(self):
        assert parse_json_field("[1, 2, 3]", []) == [1, 2, 3]

    def test_json_string_dict(self):
        assert parse_json_field('{"a": 1}', {}) == {"a": 1}

    def test_python_literal_string(self):
        assert parse_json_field("[0, 1, 2]", []) == [0, 1, 2]

    def test_cadena_invalida_devuelve_default(self):
        assert parse_json_field("esto no es json ni literal", "default") == "default"

    def test_numero_devuelve_default(self):
        assert parse_json_field(42, "default") == "default"

    def test_lista_con_python_literal_tuple(self):
        # ast.literal_eval soporta tuplas
        result = parse_json_field("(1, 2)", "default")
        assert result == (1, 2)


class TestParseDiasSemana:
    def test_none_devuelve_todos_los_dias(self):
        assert parse_dias_semana(None) == list(range(7))

    def test_lista_valida(self):
        assert parse_dias_semana([0, 1, 2]) == [0, 1, 2]

    def test_json_string(self):
        assert parse_dias_semana("[0, 1, 2, 3, 4]") == [0, 1, 2, 3, 4]

    def test_no_lista_devuelve_default(self):
        # Si el resultado parseado no es lista, debe devolver default
        assert parse_dias_semana('{"key": "val"}') == list(range(7))

    def test_cadena_invalida_devuelve_default(self):
        assert parse_dias_semana("invalido") == list(range(7))


class TestParseRecreos:
    def test_none_devuelve_default(self):
        assert parse_recreos(None) == [1, 2]

    def test_lista_valida(self):
        assert parse_recreos([1]) == [1]

    def test_json_string(self):
        assert parse_recreos("[1, 2]") == [1, 2]

    def test_dict_formato_antiguo_extrae_recreos(self):
        # dict con listas de recreos
        result = parse_recreos({"lunes": [1, 2], "martes": [2, 3]})
        assert sorted(result) == [1, 2, 3]

    def test_dict_vacio_devuelve_default(self):
        result = parse_recreos({})
        assert result == [1, 2]

    def test_cadena_invalida_devuelve_default(self):
        assert parse_recreos("invalido") == [1, 2]

    def test_dict_string_formato_antiguo(self):
        # dict como string JSON
        import json
        d = {"lunes": [1], "martes": [1, 2]}
        result = parse_recreos(json.dumps(d))
        assert sorted(result) == [1, 2]
