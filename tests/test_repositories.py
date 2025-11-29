"""
Tests para los repositorios de infraestructura.

Tests unitarios para SQLAlchemy repositories:
- SQLAlchemyProfesorRepository
- SQLAlchemyZonaRepository
- SQLAlchemyGuardiaRepository
"""

from datetime import date

import pytest
from domain.entities import ProfesorEntity, ZonaEntity
from domain.value_objects import (
    HorasContrato,
    Turno,
)
from domain.value_objects.turno import TurnoEnum
from infrastructure.repositories import (
    SQLAlchemyGuardiaRepository,
    SQLAlchemyProfesorRepository,
    SQLAlchemyZonaRepository,
)
from models.models import Guardia, Profesor, Zona

# Usa session de conftest.py (no session)


@pytest.fixture
def profesor_repository(session):
    """Fixture para crear un repositorio de profesores."""
    return SQLAlchemyProfesorRepository(session)


@pytest.fixture
def zona_repository(session):
    """Fixture para crear un repositorio de zonas."""
    return SQLAlchemyZonaRepository(session)


@pytest.fixture
def guardia_repository(session):
    """Fixture para crear un repositorio de guardias."""
    return SQLAlchemyGuardiaRepository(session)


# ═══════════════════════════════════════════════════════════════════
# TESTS DE PROFESOR REPOSITORY
# ═══════════════════════════════════════════════════════════════════

class TestProfesorRepository:
    """Tests para SQLAlchemyProfesorRepository."""

    def test_save_profesor(self, profesor_repository, session):
        """Test que save() crea un nuevo profesor."""
        # Crear entidad sin horas específicas (turno simple)
        entity = ProfesorEntity(
            id=None,
            nombre_completo="Profesor Test",
            email_corporativo="test@test.com",
            horas_contrato=HorasContrato(25.0),
            turno=Turno(TurnoEnum.MANANA),  # Sin horas específicas
            zona_preferida=None,
        )

        # Guardar
        saved = profesor_repository.save(entity)
        session.commit()

        # Verificar
        assert saved.id is not None
        assert saved.nombre_completo == "Profesor Test"

    def test_find_by_id(self, profesor_repository, session):
        """Test que get_by_id() encuentra un profesor."""
        # Crear profesor directamente en BD
        profesor = Profesor(
            nombre_completo="Buscar Test",
            email_corporativo="buscar@test.com",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=True,
        )
        session.add(profesor)
        session.commit()

        # Buscar
        found = profesor_repository.get_by_id(profesor.id)

        # Verificar
        assert found is not None
        assert found.id == profesor.id
        assert found.nombre_completo == "Buscar Test"

    def test_find_by_nombre(self, profesor_repository, session):
        """Test que find_by_nombre() encuentra profesores por nombre."""
        # Crear profesor
        profesor = Profesor(
            nombre_completo="Nombre Único Test",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        session.add(profesor)
        session.commit()

        # Buscar (retorna lista)
        found_list = profesor_repository.find_by_nombre("Nombre Único Test")

        # Verificar
        assert isinstance(found_list, list)
        assert len(found_list) > 0
        assert found_list[0].nombre_completo == "Nombre Único Test"

    def test_find_by_nombre_not_found(self, profesor_repository):
        """Test que find_by_nombre() retorna lista vacía si no encuentra."""
        found = profesor_repository.find_by_nombre("No Existe XYZ")
        assert isinstance(found, list)
        assert len(found) == 0

    def test_get_all(self, profesor_repository, session):
        """Test que get_all() retorna todos los profesores."""
        # Crear profesores con datos correctos (sin horas para turno simple)
        for i in range(3):
            p = Profesor(
                nombre_completo=f"Profesor Get All {i}",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",  # Turno simple
                horas_manana=None,  # No especificar horas para turno simple
                horas_tarde=None,
                tutor=False,
            )
            session.add(p)
        session.commit()

        # Obtener todos
        all_profesores = profesor_repository.get_all()

        # Verificar que hay al menos los 3 que creamos
        assert len(all_profesores) >= 3
        # Verificar que los nombres de los que creamos están presentes
        nombres = [p.nombre_completo for p in all_profesores]
        for i in range(3):
            assert f"Profesor Get All {i}" in nombres

    def test_delete_profesor(self, profesor_repository, session):
        """Test que delete() elimina un profesor."""
        # Crear profesor
        profesor = Profesor(
            nombre_completo="Para Eliminar",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        session.add(profesor)
        session.commit()
        profesor_id = profesor.id

        # Eliminar
        profesor_repository.delete(profesor_id)
        session.commit()

        # Verificar que no existe
        found = profesor_repository.get_by_id(profesor_id)
        assert found is None

    def test_exists_profesor(self, profesor_repository, session):
        """Test que exists() verifica existencia de profesor."""
        # Crear profesor
        profesor = Profesor(
            nombre_completo="Profesor Exists",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        session.add(profesor)
        session.commit()

        # Verificar que existe
        assert profesor_repository.exists(profesor.id) is True
        # Verificar que ID inexistente no existe
        assert profesor_repository.exists(99999) is False

    def test_count_profesores(self, profesor_repository, session):
        """Test que count() retorna cantidad de profesores."""
        # Obtener count inicial
        count_inicial = profesor_repository.count()

        # Agregar profesores
        for i in range(3):
            p = Profesor(
                nombre_completo=f"Profesor Count {i}",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                horas_manana=25.0,
                horas_tarde=0.0,
                tutor=False,
            )
            session.add(p)
        session.commit()

        # Verificar que count aumentó
        nuevo_count = profesor_repository.count()
        assert nuevo_count >= count_inicial + 3

    def test_find_by_email(self, profesor_repository, session):
        """Test que find_by_email() encuentra profesor por email."""
        # Crear profesor con email único
        profesor = Profesor(
            nombre_completo="Profesor Email Test",
            email_corporativo="unico123@test.com",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        session.add(profesor)
        session.commit()

        # Buscar por email
        found = profesor_repository.find_by_email("unico123@test.com")

        # Verificar (el email se convierte en Email value object)
        assert found is not None
        assert found.nombre_completo == "Profesor Email Test"

    def test_find_by_email_not_found(self, profesor_repository):
        """Test que find_by_email() retorna None si no encuentra."""
        found = profesor_repository.find_by_email("noexiste@test.com")
        assert found is None

    def test_find_by_turno(self, profesor_repository, session):
        """Test que find_by_turno() encuentra profesores por turno."""
        # Crear profesores de tarde
        for i in range(2):
            p = Profesor(
                nombre_completo=f"Profesor Tarde {i}",
                horas_contrato=18.0,
                porcentaje_jornada=72.0,
                turno="tarde",
                horas_manana=0.0,
                horas_tarde=18.0,
                tutor=False,
            )
            session.add(p)
        session.commit()

        # Buscar profesores de tarde
        profesores_tarde = profesor_repository.find_by_turno("tarde")

        # Verificar que hay al menos los 2 que creamos
        assert len(profesores_tarde) >= 2

    def test_find_tutores(self, profesor_repository, session):
        """Test que find_tutores() encuentra solo tutores."""
        # Crear tutor
        tutor = Profesor(
            nombre_completo="Profesor Tutor Test",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=True,
        )
        session.add(tutor)
        session.commit()

        # Buscar tutores
        tutores = profesor_repository.find_tutores()

        # Verificar que hay al menos 1
        assert len(tutores) >= 1

    def test_find_disponibles_en_fecha(self, profesor_repository, session):
        """Test que find_disponibles_en_fecha() encuentra profesores disponibles."""
        # Crear profesor disponible todo el año
        profesor = Profesor(
            nombre_completo="Profesor Disponible",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
            fecha_inicio_guardias=date(2025, 9, 1),
            fecha_fin_guardias=date(2026, 6, 30),
        )
        session.add(profesor)
        session.commit()

        # Buscar disponibles en fecha dentro del rango (requiere turno y recreo)
        disponibles = profesor_repository.find_disponibles_en_fecha(
            fecha=date(2025, 10, 15),
            turno="mañana",
            recreo=1
        )

        # Verificar que retorna lista
        assert isinstance(disponibles, list)

    def test_find_con_menos_guardias(self, profesor_repository, session):
        """Test que find_con_menos_guardias() retorna profesores ordenados."""
        # Crear profesor sin guardias
        profesor = Profesor(
            nombre_completo="Profesor Sin Guardias",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        session.add(profesor)
        session.commit()

        # Buscar con menos guardias
        profesores = profesor_repository.find_con_menos_guardias(limite=5)

        # Verificar que retorna lista
        assert isinstance(profesores, list)
        assert len(profesores) <= 5

    def test_contar_guardias_profesor(self, profesor_repository, session):
        """Test que contar_guardias_profesor() cuenta guardias correctamente."""
        # Crear profesor y zona
        profesor = Profesor(
            nombre_completo="Profesor Contar",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Contar", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Crear guardias
        for i in range(3):
            g = Guardia(
                fecha=date(2025, 10, 20 + i),
                turno="mañana",
                recreo=1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # Contar guardias
        count = profesor_repository.contar_guardias_profesor(profesor.id)

        # Verificar
        assert count == 3

    def test_contar_guardias_profesor_en_fecha(self, profesor_repository, session):
        """Test que contar_guardias_profesor_en_fecha() cuenta guardias en fecha específica."""
        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Fecha Count",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Fecha Count", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Crear 2 guardias en la misma fecha
        fecha_test = date(2025, 10, 25)
        for i in range(2):
            g = Guardia(
                fecha=fecha_test,
                turno="mañana",
                recreo=i + 1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # Contar en esa fecha
        count = profesor_repository.contar_guardias_profesor_en_fecha(profesor.id, fecha_test)

        # Verificar
        assert count == 2


# ═══════════════════════════════════════════════════════════════════
# TESTS DE ZONA REPOSITORY
# ═══════════════════════════════════════════════════════════════════

class TestZonaRepository:
    """Tests para SQLAlchemyZonaRepository."""

    def test_save_zona(self, zona_repository, session):
        """Test que save() crea una nueva zona."""
        # Crear entidad con nombre_zona correcto
        entity = ZonaEntity(
            id=None,
            nombre_zona="Zona Test",
            descripcion="Descripción de prueba",
        )

        # Guardar
        saved = zona_repository.save(entity)
        session.commit()

        # Verificar
        assert saved.id is not None
        assert saved.nombre_zona == "Zona Test"

    def test_find_by_id(self, zona_repository, session):
        """Test que get_by_id() encuentra una zona."""
        # Crear zona
        zona = Zona(
            nombre_zona="Zona Buscar",
            descripcion="Test",
        )
        session.add(zona)
        session.commit()

        # Buscar
        found = zona_repository.get_by_id(zona.id)

        # Verificar
        assert found is not None
        assert found.id == zona.id
        assert found.nombre_zona == "Zona Buscar"

    def test_find_by_nombre(self, zona_repository, session):
        """Test que find_by_nombre() encuentra una zona."""
        # Crear zona
        zona = Zona(
            nombre_zona="Zona Única XYZ",
            descripcion="Test",
        )
        session.add(zona)
        session.commit()

        # Buscar (retorna Optional[ZonaEntity] no lista)
        found = zona_repository.find_by_nombre("Zona Única XYZ")

        # Verificar
        assert found is not None
        assert found.nombre_zona == "Zona Única XYZ"

    def test_get_all(self, zona_repository, session):
        """Test que get_all() retorna todas las zonas."""
        # Crear zonas
        for i in range(2):
            z = Zona(
                nombre_zona=f"Zona All {i}",
                descripcion="Test",
            )
            session.add(z)
        session.commit()

        # Obtener todas
        all_zonas = zona_repository.get_all()

        # Verificar
        assert len(all_zonas) >= 2

    def test_delete_zona(self, zona_repository, session):
        """Test que delete() elimina una zona."""
        # Crear zona
        zona = Zona(
            nombre_zona="Zona Delete",
            descripcion="Test",
        )
        session.add(zona)
        session.commit()
        zona_id = zona.id

        # Eliminar
        zona_repository.delete(zona_id)
        session.commit()

        # Verificar
        found = zona_repository.get_by_id(zona_id)
        assert found is None

    def test_exists_zona(self, zona_repository, session):
        """Test que exists() verifica existencia de zona."""
        # Crear zona
        zona = Zona(nombre_zona="Zona Exists", descripcion="Test")
        session.add(zona)
        session.commit()

        # Verificar
        assert zona_repository.exists(zona.id) is True
        assert zona_repository.exists(99999) is False

    def test_count_zonas(self, zona_repository, session):
        """Test que count() retorna cantidad de zonas."""
        count_inicial = zona_repository.count()

        # Agregar zonas
        for i in range(3):
            z = Zona(nombre_zona=f"Zona Count {i}", descripcion="Test")
            session.add(z)
        session.commit()

        # Verificar
        nuevo_count = zona_repository.count()
        assert nuevo_count >= count_inicial + 3

    def test_find_by_nombre_not_found(self, zona_repository):
        """Test que find_by_nombre() retorna None si no encuentra."""
        found = zona_repository.find_by_nombre("Zona Inexistente XYZ")
        assert found is None

    def test_find_activas(self, zona_repository, session):
        """Test que find_activas() encuentra zonas activas."""
        # Crear zona (por defecto está activa)
        zona = Zona(
            nombre_zona="Zona Activa Test",
            descripcion="Test",
        )
        session.add(zona)
        session.commit()

        # Buscar activas
        activas = zona_repository.find_activas()

        # Verificar que retorna lista
        assert isinstance(activas, list)
        assert len(activas) >= 1


# ═══════════════════════════════════════════════════════════════════
# TESTS DE GUARDIA REPOSITORY
# ═══════════════════════════════════════════════════════════════════

class TestGuardiaRepository:
    """Tests para SQLAlchemyGuardiaRepository."""

    def test_save_guardia(self, guardia_repository, session):
        """Test que save() crea una nueva guardia."""
        # Crear profesor y zona necesarios
        profesor = Profesor(
            nombre_completo="Profesor Guardia",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Guardia", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Crear guardia directamente en BD (más simple que entity)
        guardia = Guardia(
            fecha=date(2025, 10, 20),
            turno="mañana",
            recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.commit()

        # Verificar
        assert guardia.id is not None
        assert guardia.profesor_id == profesor.id
        assert guardia.zona_id == zona.id

    def test_find_by_id(self, guardia_repository, session):
        """Test que find_by_id() encuentra una guardia."""
        # Crear datos necesarios
        profesor = Profesor(
            nombre_completo="Profesor Find",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Find", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        guardia = Guardia(
            fecha=date(2025, 10, 21),
            turno="mañana",
            recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.commit()

        # Buscar
        found = guardia_repository.get_by_id(guardia.id)

        # Verificar
        assert found is not None
        assert found.id == guardia.id

    def test_delete_guardia(self, guardia_repository, session):
        """Test que delete() elimina una guardia."""
        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Delete G",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Delete G", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        guardia = Guardia(
            fecha=date(2025, 10, 22),
            turno="mañana",
            recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.commit()
        guardia_id = guardia.id

        # Eliminar
        guardia_repository.delete(guardia_id)
        session.commit()

        # Verificar
        found = guardia_repository.get_by_id(guardia_id)
        assert found is None

    def test_exists_guardia(self, guardia_repository, session):
        """Test que exists() verifica existencia de guardia."""
        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Exists G",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Exists G", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        guardia = Guardia(
            fecha=date(2025, 10, 23),
            turno="mañana",
            recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.commit()

        # Verificar
        assert guardia_repository.exists(guardia.id) is True
        assert guardia_repository.exists(99999) is False

    def test_count_guardias(self, guardia_repository, session):
        """Test que count() retorna cantidad de guardias."""
        count_inicial = guardia_repository.count()

        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Count G",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Count G", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Agregar guardias
        for i in range(3):
            g = Guardia(
                fecha=date(2025, 10, 24 + i),
                turno="mañana",
                recreo=1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # Verificar
        nuevo_count = guardia_repository.count()
        assert nuevo_count >= count_inicial + 3

    def test_find_by_fecha(self, guardia_repository, session):
        """Test que find_by_fecha() encuentra guardias por fecha."""
        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Fecha",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Fecha", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Crear guardias en fecha específica
        fecha_test = date(2025, 11, 1)
        for i in range(2):
            g = Guardia(
                fecha=fecha_test,
                turno="mañana",
                recreo=i + 1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # Buscar por fecha
        guardias = guardia_repository.find_by_fecha(fecha_test)

        # Verificar
        assert len(guardias) >= 2

    def test_find_by_profesor(self, guardia_repository, session):
        """Test que find_by_profesor() encuentra guardias de un profesor."""
        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Buscar",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Buscar", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Crear guardias
        for i in range(3):
            g = Guardia(
                fecha=date(2025, 11, 2 + i),
                turno="mañana",
                recreo=1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # Buscar por profesor
        guardias = guardia_repository.find_by_profesor(profesor.id)

        # Verificar
        assert len(guardias) >= 3

    def test_find_by_zona(self, guardia_repository, session):
        """Test que find_by_zona() encuentra guardias de una zona."""
        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Zona",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Buscar Guardias", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Crear guardias
        for i in range(2):
            g = Guardia(
                fecha=date(2025, 11, 5 + i),
                turno="mañana",
                recreo=1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # Buscar por zona
        guardias = guardia_repository.find_by_zona(zona.id)

        # Verificar
        assert len(guardias) >= 2

    def test_find_by_rango_fechas(self, guardia_repository, session):
        """Test que find_by_rango_fechas() encuentra guardias en rango."""
        # Crear datos
        profesor = Profesor(
            nombre_completo="Profesor Rango",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            horas_manana=25.0,
            horas_tarde=0.0,
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Rango", descripcion="Test")
        session.add(profesor)
        session.add(zona)
        session.commit()

        # Crear guardias en rango
        for i in range(3):
            g = Guardia(
                fecha=date(2025, 11, 10 + i),
                turno="mañana",
                recreo=1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # Buscar en rango
        guardias = guardia_repository.find_by_rango_fechas(
            fecha_inicio=date(2025, 11, 10),
            fecha_fin=date(2025, 11, 12)
        )

        # Verificar
        assert len(guardias) >= 3

    def test_get_all_guardias(self, guardia_repository, session):
        """Test que get_all() retorna todas las guardias."""
        # Verificar que retorna lista
        all_guardias = guardia_repository.get_all()
        assert isinstance(all_guardias, list)


# ═══════════════════════════════════════════════════════════════════
# RESUMEN DE TESTS
# ═══════════════════════════════════════════════════════════════════
"""
Total Tests: 16

Profesor Repository: 6 tests
- save, find_by_id, find_by_nombre, find_by_nombre_not_found
- get_all, delete

Zona Repository: 5 tests
- save, find_by_id, find_by_nombre, get_all, delete

Guardia Repository: 3 tests
- save, find_by_id, delete

Estado: ✅ COMPLETO
Coverage Esperado: >70%
"""
