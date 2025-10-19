"""
Tests unitarios para los mappers de infraestructura:
- ProfesorMapper
- ZonaMapper
- GuardiaMapper
Valida conversiones bidireccionales y edge cases.
"""
from datetime import date

from src.domain.entities import ProfesorEntity
from src.domain.value_objects import Email, HorasContrato, Turno, TurnoEnum, ZonaPreferida
from src.infrastructure.mappers.guardia_mapper import GuardiaMapper
from src.infrastructure.mappers.profesor_mapper import ProfesorMapper
from src.infrastructure.mappers.zona_mapper import ZonaMapper
from src.models.models import Guardia, Profesor, Zona


class TestProfesorMapper:
    def test_to_entity_and_to_model(self):
        # Crear modelo
        model = Profesor(
            nombre_completo="Test Mapper",
            email_corporativo="test@correo.com",
            horas_contrato=20.0,
            porcentaje_jornada=80.0,
            turno="mañana",
            horas_manana=None,
            horas_tarde=None,
            tutor=False,
        )
        # Model → Entity
        entity = ProfesorMapper.to_entity(model)
        assert entity.nombre_completo == "Test Mapper"
        assert entity.email_corporativo.value == "test@correo.com"
        assert entity.horas_contrato.value == 20.0
        assert entity.turno.value == TurnoEnum.MANANA
        # Entity → Model
        model2 = ProfesorMapper.to_model(entity)
        assert model2.nombre_completo == "Test Mapper"
        assert model2.email_corporativo == "test@correo.com"
        assert model2.horas_contrato == 20.0
        assert model2.turno == "mañana"

    def test_turno_mixto_bidireccional(self):
        # Entity con turno mixto
        entity = ProfesorEntity(
            id=1,
            nombre_completo="Mixto",
            email_corporativo=Email("mixto@correo.com"),
            horas_contrato=HorasContrato(30.0),
            porcentaje_jornada=100.0,
            turno=Turno(TurnoEnum.MIXTO, horas_manana=15.0, horas_tarde=15.0),
            zona_preferida=ZonaPreferida.sin_preferencia(),
        )
        # Entity → Model
        model = ProfesorMapper.to_model(entity)
        assert model.turno == "mixto"
        assert model.horas_manana == 15.0
        assert model.horas_tarde == 15.0
        # Model → Entity
        entity2 = ProfesorMapper.to_entity(model)
        assert entity2.turno.value == TurnoEnum.MIXTO
        assert entity2.turno.horas_manana == 15.0
        assert entity2.turno.horas_tarde == 15.0

class TestZonaMapper:
    def test_to_entity_and_to_model(self):
        # Crear modelo
        model = Zona(
            nombre_zona="Patio Central",
            descripcion="Zona principal",
        )
        # Model → Entity
        entity = ZonaMapper.to_entity(model)
        assert entity.nombre_zona == "Patio Central"
        assert entity.descripcion == "Zona principal"
        # Entity → Model
        model2 = ZonaMapper.to_model(entity)
        assert model2.nombre_zona == "Patio Central"
        assert model2.descripcion == "Zona principal"

class TestGuardiaMapper:
    def test_to_entity_and_to_model(self):
        # Crear modelo
        model = Guardia(
            fecha=date(2025, 10, 20),
            turno="mañana",
            recreo=1,
            profesor_id=1,
            zona_id=2,
        )
        # Model → Entity
        entity = GuardiaMapper.to_entity(model)
        assert entity.fecha == date(2025, 10, 20)
        assert entity.turno == "mañana"
        assert entity.recreo == 1
        assert entity.profesor_id == 1
        assert entity.zona_id == 2
        # Entity → Model
        model2 = GuardiaMapper.to_model(entity)
        assert model2.fecha == date(2025, 10, 20)
        assert model2.turno == "mañana"
        assert model2.recreo == 1
        assert model2.profesor_id == 1
        assert model2.zona_id == 2

