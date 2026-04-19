"""Tests para infrastructure/mappers — conversión ORM ↔ Domain."""
import sys
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from domain.entities import ZonaEntity
from domain.entities.ausencia_entity import AusenciaEntity
from domain.entities.curso_escolar_entity import CursoEscolarEntity
from infrastructure.mappers.ausencia_mapper import AusenciaMapper
from infrastructure.mappers.curso_escolar_mapper import CursoEscolarMapper
from infrastructure.mappers.zona_mapper import ZonaMapper


def _make_ausencia_model(**kwargs):
    m = MagicMock()
    m.id = kwargs.get("id", 1)
    m.profesor_id = kwargs.get("profesor_id", 10)
    m.fecha_inicio = kwargs.get("fecha_inicio", date(2024, 10, 1))
    m.fecha_fin = kwargs.get("fecha_fin", date(2024, 10, 5))
    m.tipo = kwargs.get("tipo", "baja_medica")
    m.motivo = kwargs.get("motivo", None)
    m.documento_path = kwargs.get("documento_path", None)
    m.activa = kwargs.get("activa", True)
    m.created_at = kwargs.get("created_at", None)
    m.updated_at = kwargs.get("updated_at", None)
    return m


def _make_zona_model(**kwargs):
    m = MagicMock()
    m.id = kwargs.get("id", 1)
    m.nombre_zona = kwargs.get("nombre_zona", "Patio A")
    m.descripcion = kwargs.get("descripcion", "Zona principal")
    m.capacidad_profesores = kwargs.get("capacidad_profesores", 3)
    m.activa = kwargs.get("activa", True)
    return m


def _make_curso_model(**kwargs):
    m = MagicMock()
    m.id = kwargs.get("id", 1)
    m.anio_inicio = kwargs.get("anio_inicio", 2024)
    m.anio_fin = kwargs.get("anio_fin", 2025)
    m.nombre = kwargs.get("nombre", "Curso 2024/2025")
    m.fecha_inicio = kwargs.get("fecha_inicio", date(2024, 9, 1))
    m.fecha_fin = kwargs.get("fecha_fin", date(2025, 6, 30))
    m.activo = kwargs.get("activo", True)
    m.cerrado = kwargs.get("cerrado", False)
    m.created_at = kwargs.get("created_at", None)
    return m


# ============================================================
# AusenciaMapper
# ============================================================
class TestAusenciaMapper:
    def test_to_entity_basico(self):
        model = _make_ausencia_model()
        entity = AusenciaMapper.to_entity(model)
        assert isinstance(entity, AusenciaEntity)
        assert entity.id == 1
        assert entity.profesor_id == 10
        assert entity.tipo == "baja_medica"
        assert entity.activa is True

    def test_to_entity_completo(self):
        now = datetime.now()
        model = _make_ausencia_model(
            id=5,
            profesor_id=20,
            tipo="vacaciones",
            motivo="Vacaciones anuales",
            documento_path="/docs/doc.pdf",
            activa=False,
            created_at=now,
        )
        entity = AusenciaMapper.to_entity(model)
        assert entity.id == 5
        assert entity.profesor_id == 20
        assert entity.tipo == "vacaciones"
        assert entity.motivo == "Vacaciones anuales"
        assert entity.activa is False

    def test_to_model_nuevo(self):
        entity = AusenciaEntity(
            profesor_id=15,
            fecha_inicio=date(2024, 11, 1),
            fecha_fin=date(2024, 11, 5),
            tipo="permiso",
        )
        model = AusenciaMapper.to_model(entity)
        assert model.profesor_id == 15
        assert model.tipo == "permiso"

    def test_to_model_actualiza_existente(self):
        entity = AusenciaEntity(
            id=3,
            profesor_id=15,
            fecha_inicio=date(2024, 11, 1),
            fecha_fin=date(2024, 11, 5),
            tipo="otros",
        )
        existing = MagicMock()
        model = AusenciaMapper.to_model(entity, model=existing)
        assert model is existing
        assert model.tipo == "otros"


# ============================================================
# ZonaMapper
# ============================================================
class TestZonaMapper:
    def test_to_entity_basico(self):
        model = _make_zona_model()
        entity = ZonaMapper.to_entity(model)
        assert isinstance(entity, ZonaEntity)
        assert entity.id == 1
        assert entity.nombre_zona == "Patio A"
        assert entity.activa is True

    def test_to_model_nuevo(self):
        entity = ZonaEntity(
            nombre_zona="Zona B",
            descripcion="Zona secundaria",
            capacidad_profesores=2,
            activa=True,
        )
        model = ZonaMapper.to_model(entity)
        assert model.nombre_zona == "Zona B"
        assert model.activa is True

    def test_to_model_actualiza_existente(self):
        entity = ZonaEntity(
            nombre_zona="Zona C",
            descripcion="Zona terciaria",
            capacidad_profesores=1,
            activa=False,
        )
        existing = MagicMock()
        model = ZonaMapper.to_model(entity, model=existing)
        assert model is existing
        assert model.activa is False

    def test_to_entities_lista(self):
        models = [_make_zona_model(id=i, nombre_zona=f"Zona {i}") for i in range(3)]
        entities = ZonaMapper.to_entities(models)
        assert len(entities) == 3
        assert all(isinstance(e, ZonaEntity) for e in entities)

    def test_to_entities_lista_vacia(self):
        assert ZonaMapper.to_entities([]) == []


# ============================================================
# CursoEscolarMapper
# ============================================================
class TestCursoEscolarMapper:
    def test_to_entity_basico(self):
        model = _make_curso_model()
        entity = CursoEscolarMapper.to_entity(model)
        assert isinstance(entity, CursoEscolarEntity)
        assert entity.id == 1
        assert entity.anio_inicio == 2024
        assert entity.nombre == "Curso 2024/2025"
        assert entity.activo is True
        assert entity.cerrado is False

    def test_to_model_nuevo(self):
        entity = CursoEscolarEntity(
            anio_inicio=2025,
            anio_fin=2026,
            nombre="Curso 2025/2026",
            fecha_inicio=date(2025, 9, 1),
            fecha_fin=date(2026, 6, 30),
            activo=True,
            cerrado=False,
        )
        model = CursoEscolarMapper.to_model(entity)
        assert model.anio_inicio == 2025
        assert model.nombre == "Curso 2025/2026"

    def test_to_model_actualiza_existente(self):
        entity = CursoEscolarEntity(
            id=5,
            anio_inicio=2023,
            anio_fin=2024,
            nombre="Curso 2023/2024",
            fecha_inicio=date(2023, 9, 1),
            fecha_fin=date(2024, 6, 30),
            activo=False,
            cerrado=True,
        )
        existing = MagicMock()
        model = CursoEscolarMapper.to_model(entity, model=existing)
        assert model is existing
        assert model.cerrado is True
        assert model.id == 5
