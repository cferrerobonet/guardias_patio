"""Tests para sync/dtos.py — capa anticorrupción ARQ-07."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sync.dtos import (
    AusenciaSyncDTO,
    ConfiguracionSyncDTO,
    CursoEscolarSyncDTO,
    GuardiaSyncDTO,
    ProfesorSyncDTO,
    ZonaSyncDTO,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_curso():
    m = MagicMock()
    m.id = 1
    m.anio_inicio = 2025
    m.anio_fin = 2026
    m.fecha_inicio = date(2025, 9, 10)
    m.fecha_fin = date(2026, 6, 20)
    m.nombre = "2025/2026"
    m.activo = True
    m.cerrado = False
    m.created_at = date(2025, 9, 1)
    return m


def _mock_profesor():
    m = MagicMock()
    m.id = 42
    m.nombre_completo = "Ana García"
    m.email_corporativo = "ana@school.es"
    m.horas_contrato = 23.0
    m.porcentaje_jornada = 100.0
    m.turno = "M"
    m.horas_manana = 23.0
    m.horas_tarde = None
    m.tutor = False
    m.activo = True
    m.fecha_inicio_guardias = None
    m.fecha_fin_guardias = None
    m.dias_semana_permitidos = None
    m.recreos_permitidos = None
    return m


def _mock_zona():
    m = MagicMock()
    m.id = 3
    m.nombre_zona = "Patio Norte"
    m.descripcion = "Zona norte del patio"
    m.fecha_inicio = None
    m.fecha_fin = None
    return m


def _mock_config():
    m = MagicMock()
    m.id = 1
    m.anio_inicio_curso = 2025
    m.fecha_inicio_curso = date(2025, 9, 10)
    m.fecha_fin_curso = date(2026, 6, 20)
    from datetime import time

    m.hora_recreo1_manana = time(10, 30)
    m.hora_recreo2_manana = None
    m.hora_recreo1_tarde = None
    m.hora_recreo2_tarde = None
    m.activar_festivos_automaticos = True
    m.dias_no_lectivos_personalizados = None
    m.recreos_config = None
    m.ajuste_tutores = 1.0
    m.ajuste_no_tutores = 1.0
    m.algoritmo_asignacion = "v2.9"
    return m


def _mock_guardia():
    m = MagicMock()
    m.id = 100
    m.curso_id = 1
    m.profesor_id = 42
    m.fecha = date(2025, 10, 14)
    m.turno = "M"
    m.recreo = 1
    m.zona_id = 3
    return m


def _mock_ausencia():
    m = MagicMock()
    m.id = 7
    m.profesor_id = 42
    m.fecha_inicio = date(2025, 11, 4)
    m.fecha_fin = date(2025, 11, 4)
    m.tipo = "ENFERMEDAD"
    m.motivo = "Baja médica"
    m.documento_path = None
    m.activa = True
    m.created_at = None
    m.updated_at = None
    return m


# ---------------------------------------------------------------------------
# CursoEscolarSyncDTO
# ---------------------------------------------------------------------------


class TestCursoEscolarSyncDTO:
    def test_from_orm_preserva_campos(self):
        dto = CursoEscolarSyncDTO.from_orm(_mock_curso())
        assert dto.id == 1
        assert dto.anio_inicio == 2025
        assert dto.nombre == "2025/2026"
        assert dto.activo is True
        assert dto.cerrado is False
        assert dto.fecha_inicio == "2025-09-10"

    def test_from_dict_round_trip(self):
        original = CursoEscolarSyncDTO.from_orm(_mock_curso())
        d = original.to_dict()
        reconstructed = CursoEscolarSyncDTO.from_dict(d)
        assert reconstructed == original

    def test_to_dict_serializable(self):
        import json

        dto = CursoEscolarSyncDTO.from_orm(_mock_curso())
        # No debe lanzar excepción
        json.dumps(dto.to_dict())

    def test_from_dict_opcionales_none(self):
        dto = CursoEscolarSyncDTO.from_dict(
            {
                "id": 2,
                "anio_inicio": 2024,
                "anio_fin": 2025,
                "nombre": "2024/2025",
                "activo": False,
                "cerrado": True,
            }
        )
        assert dto.fecha_inicio is None
        assert dto.created_at is None


# ---------------------------------------------------------------------------
# ProfesorSyncDTO
# ---------------------------------------------------------------------------


class TestProfesorSyncDTO:
    def test_from_orm_basico(self):
        dto = ProfesorSyncDTO.from_orm(_mock_profesor())
        assert dto.id == 42
        assert dto.nombre_completo == "Ana García"
        assert dto.horas_contrato == 23.0
        assert dto.horas_tarde is None

    def test_from_dict_round_trip(self):
        original = ProfesorSyncDTO.from_orm(_mock_profesor())
        reconstructed = ProfesorSyncDTO.from_dict(original.to_dict())
        assert reconstructed == original

    def test_activo_default_true(self):
        dto = ProfesorSyncDTO.from_dict(
            {
                "id": 1,
                "nombre_completo": "Test",
                "horas_contrato": 18.0,
                "porcentaje_jornada": 80.0,
                "turno": "T",
            }
        )
        assert dto.activo is True

    def test_tutor_default_false(self):
        dto = ProfesorSyncDTO.from_dict(
            {
                "id": 1,
                "nombre_completo": "Test",
                "horas_contrato": 18.0,
                "porcentaje_jornada": 80.0,
                "turno": "T",
            }
        )
        assert dto.tutor is False

    def test_horas_float_conversion(self):
        m = _mock_profesor()
        m.horas_manana = 12  # int
        dto = ProfesorSyncDTO.from_orm(m)
        assert isinstance(dto.horas_manana, float)


# ---------------------------------------------------------------------------
# ZonaSyncDTO
# ---------------------------------------------------------------------------


class TestZonaSyncDTO:
    def test_from_orm(self):
        dto = ZonaSyncDTO.from_orm(_mock_zona())
        assert dto.id == 3
        assert dto.nombre_zona == "Patio Norte"
        assert dto.fecha_inicio is None

    def test_from_dict_round_trip(self):
        original = ZonaSyncDTO.from_orm(_mock_zona())
        assert ZonaSyncDTO.from_dict(original.to_dict()) == original


# ---------------------------------------------------------------------------
# ConfiguracionSyncDTO
# ---------------------------------------------------------------------------


class TestConfiguracionSyncDTO:
    def test_from_orm(self):
        dto = ConfiguracionSyncDTO.from_orm(_mock_config())
        assert dto.id == 1
        assert dto.hora_recreo1_manana == "10:30:00"
        assert dto.hora_recreo2_manana is None
        assert dto.ajuste_tutores == 1.0
        assert dto.algoritmo_asignacion == "v2.9"

    def test_from_dict_round_trip(self):
        original = ConfiguracionSyncDTO.from_orm(_mock_config())
        assert ConfiguracionSyncDTO.from_dict(original.to_dict()) == original

    def test_ajuste_defaults(self):
        dto = ConfiguracionSyncDTO.from_dict(
            {
                "id": 1,
                "fecha_inicio_curso": "2025-09-10",
                "fecha_fin_curso": "2026-06-20",
                "activar_festivos_automaticos": True,
            }
        )
        assert dto.ajuste_tutores == 1.0
        assert dto.ajuste_no_tutores == 1.0


# ---------------------------------------------------------------------------
# GuardiaSyncDTO
# ---------------------------------------------------------------------------


class TestGuardiaSyncDTO:
    def test_from_orm(self):
        dto = GuardiaSyncDTO.from_orm(_mock_guardia())
        assert dto.id == 100
        assert dto.profesor_id == 42
        assert dto.fecha == "2025-10-14"
        assert dto.turno == "M"
        assert dto.recreo == 1
        assert dto.zona_id == 3

    def test_from_dict_round_trip(self):
        original = GuardiaSyncDTO.from_orm(_mock_guardia())
        assert GuardiaSyncDTO.from_dict(original.to_dict()) == original

    def test_curso_id_nullable(self):
        m = _mock_guardia()
        m.curso_id = None
        dto = GuardiaSyncDTO.from_orm(m)
        assert dto.curso_id is None


# ---------------------------------------------------------------------------
# AusenciaSyncDTO
# ---------------------------------------------------------------------------


class TestAusenciaSyncDTO:
    def test_from_orm(self):
        dto = AusenciaSyncDTO.from_orm(_mock_ausencia())
        assert dto.id == 7
        assert dto.tipo == "ENFERMEDAD"
        assert dto.activa is True
        assert dto.created_at is None

    def test_from_dict_round_trip(self):
        original = AusenciaSyncDTO.from_orm(_mock_ausencia())
        assert AusenciaSyncDTO.from_dict(original.to_dict()) == original

    def test_activa_default_true(self):
        dto = AusenciaSyncDTO.from_dict(
            {
                "id": 1,
                "profesor_id": 5,
                "fecha_inicio": "2025-11-01",
                "fecha_fin": "2025-11-01",
                "tipo": "PERSONAL",
            }
        )
        assert dto.activa is True

    def test_to_dict_json_serializable(self):
        import json

        dto = AusenciaSyncDTO.from_orm(_mock_ausencia())
        json.dumps(dto.to_dict())
