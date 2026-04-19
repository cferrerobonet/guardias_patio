"""Tests para application/dtos/profesor_dto.py y zona_dto.py."""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from application.dtos.profesor_dto import (
    ActualizarProfesorDTO,
    CrearProfesorDTO,
    ProfesorDTO,
)
from application.dtos.zona_dto import ActualizarZonaDTO, CrearZonaDTO, ZonaDTO


# ---------------------------------------------------------------------------
# ProfesorDTO (salida)
# ---------------------------------------------------------------------------
class TestProfesorDTO:
    def test_creacion_basica(self):
        dto = ProfesorDTO(
            id=1,
            nombre_completo="García, Juan",
            horas_contrato=18.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            tutor=False,
        )
        assert dto.id == 1
        assert dto.turno == "mañana"

    def test_valores_opcionales_none(self):
        dto = ProfesorDTO(
            id=2,
            nombre_completo="López, Ana",
            horas_contrato=12.0,
            porcentaje_jornada=66.7,
            turno="tarde",
            tutor=True,
            email_corporativo=None,
            zona_preferida_id=None,
        )
        assert dto.email_corporativo is None
        assert dto.zona_preferida_id is None

    def test_campos_calculados(self):
        dto = ProfesorDTO(
            id=3,
            nombre_completo="Martínez, Pedro",
            horas_contrato=18.0,
            porcentaje_jornada=100.0,
            turno="mixto",
            tutor=False,
            ajuste_guardias=0.5,
            guardias_esperadas=10.5,
        )
        assert dto.ajuste_guardias == 0.5
        assert dto.guardias_esperadas == 10.5


# ---------------------------------------------------------------------------
# CrearProfesorDTO — validadores
# ---------------------------------------------------------------------------
class TestCrearProfesorDTO:
    def _base_data(self, **kwargs):
        data = {
            "nombre_completo": "García, Juan",
            "horas_contrato": 18.0,
            "turno": "mañana",
        }
        data.update(kwargs)
        return data

    def test_creacion_valida(self):
        dto = CrearProfesorDTO(**self._base_data())
        assert dto.nombre_completo == "García, Juan"

    def test_dias_semana_none_usa_lun_vie(self):
        dto = CrearProfesorDTO(**self._base_data(dias_semana_permitidos=None))
        assert dto.dias_semana_permitidos == list(range(5))

    def test_dias_semana_validos(self):
        dto = CrearProfesorDTO(**self._base_data(dias_semana_permitidos=[0, 1, 2, 3, 4]))
        assert dto.dias_semana_permitidos == [0, 1, 2, 3, 4]

    def test_dias_semana_invalidos_lanza(self):
        with pytest.raises(Exception):
            CrearProfesorDTO(**self._base_data(dias_semana_permitidos=[0, 7]))

    def test_recreos_none_usa_defecto(self):
        dto = CrearProfesorDTO(**self._base_data(recreos_permitidos=None))
        assert dto.recreos_permitidos == [1, 2, 3, 4]

    def test_recreos_lista_valida(self):
        dto = CrearProfesorDTO(**self._base_data(recreos_permitidos=[1, 2]))
        assert dto.recreos_permitidos == [1, 2]

    def test_recreos_dict_vacio_usa_defecto(self):
        dto = CrearProfesorDTO(**self._base_data(recreos_permitidos={}))
        assert dto.recreos_permitidos == [1, 2, 3, 4]

    def test_recreos_dict_con_string_keys(self):
        dto = CrearProfesorDTO(**self._base_data(recreos_permitidos={"0": [1, 2], "1": [2, 3]}))
        assert isinstance(dto.recreos_permitidos, dict)
        assert 0 in dto.recreos_permitidos

    def test_recreos_dict_invalido_lanza(self):
        with pytest.raises(Exception):
            CrearProfesorDTO(**self._base_data(recreos_permitidos={"0": "no_es_lista"}))

    def test_recreos_lista_invalida_lanza(self):
        with pytest.raises(Exception):
            CrearProfesorDTO(**self._base_data(recreos_permitidos=[0]))  # 0 no es >= 1

    def test_recreos_tipo_invalido_lanza(self):
        with pytest.raises(Exception):
            CrearProfesorDTO(**self._base_data(recreos_permitidos="invalido"))

    def test_horas_turno_negativas_lanza(self):
        with pytest.raises(Exception):
            CrearProfesorDTO(**self._base_data(horas_manana=-1.0))


# ---------------------------------------------------------------------------
# ActualizarProfesorDTO — validadores
# ---------------------------------------------------------------------------
class TestActualizarProfesorDTO:
    def test_todos_campos_none(self):
        dto = ActualizarProfesorDTO()
        assert dto.nombre_completo is None
        assert dto.turno is None

    def test_email_valido(self):
        dto = ActualizarProfesorDTO(email_corporativo="profe@example.com")
        assert dto.email_corporativo == "profe@example.com"

    def test_email_invalido_lanza(self):
        with pytest.raises(Exception):
            ActualizarProfesorDTO(email_corporativo="no_es_email")

    def test_dias_semana_validos(self):
        dto = ActualizarProfesorDTO(dias_semana_permitidos=[0, 1, 2])
        assert dto.dias_semana_permitidos == [0, 1, 2]

    def test_dias_semana_invalidos_lanza(self):
        with pytest.raises(Exception):
            ActualizarProfesorDTO(dias_semana_permitidos=[7])

    def test_recreos_none_permitido(self):
        dto = ActualizarProfesorDTO(recreos_permitidos=None)
        assert dto.recreos_permitidos is None

    def test_recreos_dict_vacio_devuelve_none(self):
        dto = ActualizarProfesorDTO(recreos_permitidos={})
        assert dto.recreos_permitidos is None

    def test_recreos_lista_valida(self):
        dto = ActualizarProfesorDTO(recreos_permitidos=[1, 3])
        assert dto.recreos_permitidos == [1, 3]

    def test_recreos_dict_valido(self):
        dto = ActualizarProfesorDTO(recreos_permitidos={"0": [1, 2]})
        assert isinstance(dto.recreos_permitidos, dict)

    def test_recreos_dict_invalido_lanza(self):
        with pytest.raises(Exception):
            ActualizarProfesorDTO(recreos_permitidos={"0": "no_lista"})

    def test_recreos_lista_invalida_lanza(self):
        with pytest.raises(Exception):
            ActualizarProfesorDTO(recreos_permitidos=[0])

    def test_recreos_tipo_invalido_lanza(self):
        with pytest.raises(Exception):
            ActualizarProfesorDTO(recreos_permitidos=123)


# ---------------------------------------------------------------------------
# ZonaDTO
# ---------------------------------------------------------------------------
class TestZonaDTO:
    def test_creacion_basica(self):
        dto = ZonaDTO(id=1, nombre_zona="Patio Central")
        assert dto.id == 1
        assert dto.descripcion is None


# ---------------------------------------------------------------------------
# CrearZonaDTO
# ---------------------------------------------------------------------------
class TestCrearZonaDTO:
    def test_valido(self):
        dto = CrearZonaDTO(nombre_zona="  Patio  ")
        assert dto.nombre_zona == "Patio"  # strip aplicado

    def test_nombre_vacio_lanza(self):
        with pytest.raises(Exception):
            CrearZonaDTO(nombre_zona="   ")

    def test_nombre_muy_corto_lanza(self):
        with pytest.raises(Exception):
            CrearZonaDTO(nombre_zona="A")

    def test_fechas_validas(self):
        dto = CrearZonaDTO(
            nombre_zona="Patio",
            fecha_inicio=date(2024, 9, 1),
            fecha_fin=date(2025, 6, 30),
        )
        assert dto.fecha_fin > dto.fecha_inicio

    def test_fecha_fin_anterior_lanza(self):
        with pytest.raises(Exception):
            CrearZonaDTO(
                nombre_zona="Patio",
                fecha_inicio=date(2025, 1, 1),
                fecha_fin=date(2024, 1, 1),
            )


# ---------------------------------------------------------------------------
# ActualizarZonaDTO
# ---------------------------------------------------------------------------
class TestActualizarZonaDTO:
    def test_todos_none(self):
        dto = ActualizarZonaDTO()
        assert dto.nombre_zona is None

    def test_nombre_valido(self):
        dto = ActualizarZonaDTO(nombre_zona="Patio Sur")
        assert dto.nombre_zona == "Patio Sur"

    def test_nombre_none_permitido(self):
        dto = ActualizarZonaDTO(nombre_zona=None)
        assert dto.nombre_zona is None

    def test_nombre_invalido_lanza(self):
        with pytest.raises(Exception):
            ActualizarZonaDTO(nombre_zona="  ")

    def test_nombre_demasiado_corto_lanza(self):
        with pytest.raises(Exception):
            ActualizarZonaDTO(nombre_zona="X")

    def test_fecha_fin_anterior_lanza(self):
        with pytest.raises(Exception):
            ActualizarZonaDTO(
                fecha_inicio=date(2025, 6, 1),
                fecha_fin=date(2024, 1, 1),
            )
