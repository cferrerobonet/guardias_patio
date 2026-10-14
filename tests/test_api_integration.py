"""
Tests de integración API REST con SQLite in-memory.

Valida endpoints reales (profesores, zonas, guardias) con BD en memoria.
No se usan mocks de sesión — los use cases operan sobre datos reales.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.auth import get_current_user
from api.dependencies import get_db
from api.main import app
from infrastructure.database.models import Base, CursoEscolar


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def engine():
    """Motor SQLite in-memory compartido (StaticPool) para toda la suite."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture(scope="module")
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture(scope="module")
def curso_activo_db(session_factory):
    """Crea un CursoEscolar activo en la BD de test."""
    from datetime import date

    session = session_factory()
    curso = CursoEscolar(
        nombre="2024/2025",
        activo=True,
        anio_inicio=2024,
        anio_fin=2025,
        fecha_inicio=date(2024, 9, 1),
        fecha_fin=date(2025, 6, 30),
    )
    session.add(curso)
    session.commit()
    curso_id = curso.id
    session.close()
    return curso_id


@pytest.fixture(scope="module")
def client(engine, session_factory, curso_activo_db):
    """TestClient con BD SQLite in-memory real inyectada vía dependency override."""
    TestSession = session_factory

    def _get_db_real():
        db = TestSession()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_real
    app.dependency_overrides[get_current_user] = lambda: "test_user"
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests: Profesores
# ---------------------------------------------------------------------------


class TestProfesoresIntegracion:
    """Tests de integración del endpoint /api/v1/profesores."""

    def test_listar_profesores_vacio(self, client):
        """Lista vacía cuando no hay profesores en la BD."""
        resp = client.get("/api/v1/profesores/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_crear_profesor(self, client):
        """Crear un profesor y verificar que aparece en el listado."""
        payload = {
            "nombre_completo": "Ana García López",
            "horas_contrato": 18.0,
            "porcentaje_jornada": 100.0,
            "turno": "mañana",
            "activo": True,
            "email_corporativo": "ana.garcia@centro.es",
        }
        resp = client.post("/api/v1/profesores/", json=payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["nombre_completo"] == "Ana García López"
        assert data["turno"] == "mañana"

    def test_listar_profesores_con_datos(self, client):
        """Tras crear un profesor, el listado devuelve al menos 1."""
        resp = client.get("/api/v1/profesores/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_obtener_profesor_por_id(self, client):
        """Obtener un profesor por su ID."""
        # Primero creamos uno determinista
        payload = {
            "nombre_completo": "Carlos Ruiz Martínez",
            "horas_contrato": 12.0,
            "porcentaje_jornada": 66.0,
            "turno": "tarde",
            "activo": True,
        }
        resp_crear = client.post("/api/v1/profesores/", json=payload)
        assert resp_crear.status_code in (200, 201)
        profesor_id = resp_crear.json()["id"]

        resp = client.get(f"/api/v1/profesores/{profesor_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == profesor_id
        assert resp.json()["nombre_completo"] == "Carlos Ruiz Martínez"

    def test_obtener_profesor_inexistente(self, client):
        """Solicitar un ID inexistente devuelve 404."""
        resp = client.get("/api/v1/profesores/999999")
        assert resp.status_code == 404

    def test_crear_profesor_turno_invalido(self, client):
        """Turno inválido debe devolver error de validación."""
        payload = {
            "nombre_completo": "Test Turno Inválido",
            "horas_contrato": 18.0,
            "porcentaje_jornada": 100.0,
            "turno": "turno_invalido",
            "activo": True,
        }
        resp = client.post("/api/v1/profesores/", json=payload)
        assert resp.status_code in (400, 422)

    def test_filtrar_profesores_por_turno(self, client):
        """Filtrar por turno devuelve solo profesores del turno indicado."""
        resp = client.get("/api/v1/profesores/?turno=mañana")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["turno"] == "mañana"


# ---------------------------------------------------------------------------
# Tests: Zonas
# ---------------------------------------------------------------------------


class TestZonasIntegracion:
    """Tests de integración del endpoint /api/v1/zonas."""

    def test_listar_zonas_vacio(self, client):
        """Lista vacía cuando no hay zonas."""
        resp = client.get("/api/v1/zonas/")
        assert resp.status_code == 200

    def test_crear_zona(self, client):
        """Crear una zona y verificar respuesta."""
        payload = {"nombre_zona": "Patio Norte", "capacidad_profesores": 3}
        resp = client.post("/api/v1/zonas", json=payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["nombre_zona"] == "Patio Norte"

    def test_zona_duplicada(self, client):
        """Crear zona con nombre duplicado debe fallar."""
        payload = {"nombre_zona": "Zona Única Duplicada"}
        resp1 = client.post("/api/v1/zonas", json=payload)
        assert resp1.status_code in (200, 201)
        resp2 = client.post("/api/v1/zonas", json=payload)
        # Debe devolver error (400 o 409)
        assert resp2.status_code >= 400


# ---------------------------------------------------------------------------
# Tests: Guardias
# ---------------------------------------------------------------------------


class TestGuardiasIntegracion:
    """Tests de integración del endpoint /api/v1/guardias."""

    def test_listar_guardias(self, client, curso_activo_db):
        """El endpoint de guardias responde correctamente con configuracion_id requerido."""
        resp = client.get("/api/v1/guardias", params={"configuracion_id": curso_activo_db})
        assert resp.status_code == 200
