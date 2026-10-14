"""Tests para infrastructure/mappers/configuracion_mapper.py."""
import json
import sys
from datetime import date, time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from domain.entities.configuracion_entity import ConfiguracionEntity
from infrastructure.mappers.configuracion_mapper import ConfiguracionMapper, _parse_json_list


class TestParseJsonList:
    def test_none_devuelve_default(self):
        assert _parse_json_list(None, [1]) == [1]

    def test_vacio_devuelve_default(self):
        assert _parse_json_list("", [1, 2]) == [1, 2]

    def test_json_valido_lista(self):
        assert _parse_json_list('["a", "b"]', []) == ["a", "b"]

    def test_json_valido_no_lista_default(self):
        assert _parse_json_list('{"a":1}', ["x"]) == ["x"]

    def test_literal_eval_lista(self):
        assert _parse_json_list("['x', 'y']", []) == ["x", "y"]

    def test_texto_invalido_default(self):
        assert _parse_json_list("no_es_json", [9]) == [9]


class TestConfiguracionMapper:
    def test_to_entity_defaults(self):
        model = MagicMock()
        model.id = 1
        model.anio_inicio_curso = None
        model.fecha_inicio_curso = date(2024, 9, 1)
        model.fecha_fin_curso = date(2025, 6, 30)
        model.hora_recreo1_manana = time(10, 30)
        model.hora_recreo2_manana = time(12, 0)
        model.hora_recreo1_tarde = None
        model.hora_recreo2_tarde = None
        model.activar_festivos_automaticos = True
        model.dias_no_lectivos_personalizados = None
        model.recreos_config = None
        model.ajuste_tutores = None
        model.ajuste_no_tutores = None
        model.algoritmo_asignacion = None
        model.curso_activo_id = None

        entity = ConfiguracionMapper.to_entity(model)
        assert entity.id == 1
        assert entity.anio_inicio_curso == 0
        assert entity.ajuste_tutores == 1.0
        assert entity.algoritmo_asignacion == "v2.9"

    def test_to_entity_parsea_json(self):
        model = MagicMock()
        model.id = 2
        model.anio_inicio_curso = 2024
        model.fecha_inicio_curso = date(2024, 9, 1)
        model.fecha_fin_curso = date(2025, 6, 30)
        model.hora_recreo1_manana = time(10, 30)
        model.hora_recreo2_manana = time(12, 0)
        model.hora_recreo1_tarde = None
        model.hora_recreo2_tarde = None
        model.activar_festivos_automaticos = False
        model.dias_no_lectivos_personalizados = '["2024-10-09"]'
        model.recreos_config = '[{"numero":1}]'
        model.ajuste_tutores = 1.2
        model.ajuste_no_tutores = 0.9
        model.algoritmo_asignacion = "v3"
        model.curso_activo_id = 7

        entity = ConfiguracionMapper.to_entity(model)
        assert entity.dias_no_lectivos_personalizados == ["2024-10-09"]
        assert entity.recreos_config == [{"numero": 1}]
        assert entity.algoritmo_asignacion == "v3"

    def test_to_model_nuevo(self):
        entity = ConfiguracionEntity(
            id=10,
            anio_inicio_curso=2024,
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 0),
            activar_festivos_automaticos=True,
            dias_no_lectivos_personalizados=["2024-10-09"],
            recreos_config=[{"numero": 1}],
            ajuste_tutores=1.1,
            ajuste_no_tutores=1.0,
            algoritmo_asignacion="v2.9",
            curso_activo_id=3,
        )
        model = ConfiguracionMapper.to_model(entity)
        assert model.anio_inicio_curso == 2024
        assert json.loads(model.dias_no_lectivos_personalizados) == ["2024-10-09"]
        assert json.loads(model.recreos_config) == [{"numero": 1}]
        assert model.id == 10

    def test_to_model_actualiza_existente(self):
        entity = ConfiguracionEntity(
            anio_inicio_curso=2025,
            fecha_inicio_curso=date(2025, 9, 1),
            fecha_fin_curso=date(2026, 6, 30),
        )
        existing = MagicMock()
        model = ConfiguracionMapper.to_model(entity, model=existing)
        assert model is existing
        assert model.anio_inicio_curso == 2025

    def test_to_model_serializa_listas_vacias_como_none(self):
        entity = ConfiguracionEntity(
            anio_inicio_curso=2024,
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            dias_no_lectivos_personalizados=[],
            recreos_config=[],
        )
        model = ConfiguracionMapper.to_model(entity)
        assert model.dias_no_lectivos_personalizados is None
        assert model.recreos_config is None
