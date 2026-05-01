"""
Tests para la API REST (FastAPI).

Cubre: autenticación JWT, CRUD profesores, CRUD zonas, security headers.
Usa TestClient con base de datos in-memory y dependency override de get_db.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api.auth import _create_access_token, get_current_user
from api.dependencies import get_db
from api.main import app
from infrastructure.database.models import Base

# ============================================================================
# SETUP: BD in-memory + override de get_db
# ============================================================================

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_engine)
_TestSession = sessionmaker(bind=_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app, raise_server_exceptions=False)

_VALID_HEADERS = {"Authorization": f"Bearer {_create_access_token('testuser')}"}


# ============================================================================
# TESTS: Tokens y autenticación
# ============================================================================


class TestAuthToken:
    def test_token_invalido_retorna_401(self):
        r = client.get("/api/v1/profesores", headers={"Authorization": "Bearer invalid.token"})
        assert r.status_code == 401

    def test_sin_token_retorna_401(self):
        r = client.get("/api/v1/profesores")
        assert r.status_code == 401

    def test_login_credenciales_invalidas_retorna_401(self):
        with patch("api.auth._verify_user", return_value=(False, "Credenciales incorrectas")):
            r = client.post("/api/v1/auth/token", data={"username": "x", "password": "y"})
        assert r.status_code == 401

    def test_login_credenciales_validas_retorna_token(self):
        with patch("api.auth._verify_user", return_value=(True, None)):
            r = client.post("/api/v1/auth/token", data={"username": "admin", "password": "pass"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_token_valido_decodifica_username(self):
        token = _create_access_token("usuario_test")
        username = get_current_user(token)
        assert username == "usuario_test"

    def test_token_contiene_sub_correcto(self):
        import jwt
        from config.settings import get_settings

        settings = get_settings()
        token = _create_access_token("carlos")
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[settings.api_algorithm])
        assert payload["sub"] == "carlos"


# ============================================================================
# TESTS: Security headers
# ============================================================================


class TestSecurityHeaders:
    def test_health_retorna_x_content_type_options(self):
        r = client.get("/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"

    def test_health_retorna_x_frame_options(self):
        r = client.get("/health")
        assert r.headers.get("X-Frame-Options") == "DENY"

    def test_endpoint_autenticado_tiene_security_headers(self):
        r = client.get("/api/v1/profesores", headers=_VALID_HEADERS)
        assert r.headers.get("X-Content-Type-Options") == "nosniff"


# ============================================================================
# TESTS: Profesores — listado y paginación
# ============================================================================


class TestProfesoresListado:
    def test_listar_retorna_estructura_paginada(self):
        r = client.get("/api/v1/profesores", headers=_VALID_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "has_more" in data

    def test_limit_acota_resultados(self):
        r = client.get("/api/v1/profesores?limit=2", headers=_VALID_HEADERS)
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 2

    def test_offset_fuera_de_rango_retorna_lista_vacia(self):
        r = client.get("/api/v1/profesores?offset=99999&limit=10", headers=_VALID_HEADERS)
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_filtro_activo_true_solo_devuelve_activos(self):
        _crear_profesor("Activo Test Listado", activo=True)
        r = client.get("/api/v1/profesores?activo=true", headers=_VALID_HEADERS)
        assert r.status_code == 200
        for prof in r.json()["items"]:
            assert prof["activo"] is True

    def test_filtro_turno_manana_solo_devuelve_manana(self):
        _crear_profesor("Turno Mañana Filter", turno="mañana")
        r = client.get("/api/v1/profesores?turno=ma%C3%B1ana", headers=_VALID_HEADERS)
        assert r.status_code == 200
        for prof in r.json()["items"]:
            assert prof["turno"] == "mañana"


# ============================================================================
# TESTS: Profesores — CRUD
# ============================================================================


def _crear_profesor(nombre: str, turno: str = "mañana", activo: bool = True) -> dict:
    payload = {
        "nombre_completo": nombre,
        "horas_contrato": 20.0,
        "turno": turno,
    }
    r = client.post("/api/v1/profesores", json=payload, headers=_VALID_HEADERS)
    assert r.status_code == 201, r.text
    return r.json()


class TestProfesoresCRUD:
    def test_crear_profesor_retorna_201_y_datos(self):
        data = _crear_profesor("API Crear Test")
        assert data["nombre_completo"] == "API Crear Test"
        assert data["id"] > 0
        assert data["horas_contrato"] == 20.0

    def test_obtener_profesor_existente(self):
        prof = _crear_profesor("API Get Test")
        r = client.get(f"/api/v1/profesores/{prof['id']}", headers=_VALID_HEADERS)
        assert r.status_code == 200
        assert r.json()["id"] == prof["id"]

    def test_obtener_profesor_inexistente_retorna_404(self):
        r = client.get("/api/v1/profesores/99999", headers=_VALID_HEADERS)
        assert r.status_code == 404

    def test_actualizar_nombre_profesor(self):
        prof = _crear_profesor("API Update Antes")
        r = client.put(
            f"/api/v1/profesores/{prof['id']}",
            json={"nombre_completo": "API Update Despues"},
            headers=_VALID_HEADERS,
        )
        assert r.status_code == 200
        assert r.json()["nombre_completo"] == "API Update Despues"

    def test_actualizar_profesor_inexistente_retorna_404(self):
        r = client.put(
            "/api/v1/profesores/99999",
            json={"nombre_completo": "No existe"},
            headers=_VALID_HEADERS,
        )
        assert r.status_code == 404

    def test_eliminar_profesor_retorna_204(self):
        prof = _crear_profesor("API Delete Test")
        r = client.delete(f"/api/v1/profesores/{prof['id']}", headers=_VALID_HEADERS)
        assert r.status_code == 204

    def test_eliminar_profesor_no_aparece_en_listado(self):
        prof = _crear_profesor("API Delete Verificar")
        prof_id = prof["id"]
        client.delete(f"/api/v1/profesores/{prof_id}", headers=_VALID_HEADERS)
        r = client.get(f"/api/v1/profesores/{prof_id}", headers=_VALID_HEADERS)
        assert r.status_code == 404

    def test_crear_profesor_turno_invalido_retorna_422(self):
        payload = {"nombre_completo": "Turno Raro", "horas_contrato": 20.0, "turno": "noche"}
        r = client.post("/api/v1/profesores", json=payload, headers=_VALID_HEADERS)
        assert r.status_code == 422

    def test_crear_profesor_horas_negativas_retorna_422(self):
        payload = {"nombre_completo": "Horas Mal", "horas_contrato": -5.0, "turno": "mañana"}
        r = client.post("/api/v1/profesores", json=payload, headers=_VALID_HEADERS)
        assert r.status_code == 422

    def test_crear_profesor_nombre_demasiado_corto_retorna_422(self):
        payload = {"nombre_completo": "AB", "horas_contrato": 20.0, "turno": "mañana"}
        r = client.post("/api/v1/profesores", json=payload, headers=_VALID_HEADERS)
        assert r.status_code == 422


# ============================================================================
# TESTS: Zonas — CRUD
# ============================================================================


def _crear_zona(nombre: str) -> dict:
    r = client.post("/api/v1/zonas", json={"nombre_zona": nombre}, headers=_VALID_HEADERS)
    assert r.status_code == 201, r.text
    return r.json()


class TestZonasCRUD:
    def test_listar_zonas_retorna_lista(self):
        r = client.get("/api/v1/zonas", headers=_VALID_HEADERS)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_crear_zona_retorna_201_y_datos(self):
        data = _crear_zona("Patio Norte API")
        assert data["nombre_zona"] == "Patio Norte API"
        assert data["id"] > 0

    def test_obtener_zona_existente(self):
        zona = _crear_zona("Zona Get Test")
        r = client.get(f"/api/v1/zonas/{zona['id']}", headers=_VALID_HEADERS)
        assert r.status_code == 200
        assert r.json()["id"] == zona["id"]

    def test_obtener_zona_inexistente_retorna_404(self):
        r = client.get("/api/v1/zonas/99999", headers=_VALID_HEADERS)
        assert r.status_code == 404

    def test_actualizar_zona(self):
        zona = _crear_zona("Zona Original")
        r = client.put(
            f"/api/v1/zonas/{zona['id']}",
            json={"nombre_zona": "Zona Modificada"},
            headers=_VALID_HEADERS,
        )
        assert r.status_code == 200
        assert r.json()["nombre_zona"] == "Zona Modificada"

    def test_actualizar_zona_inexistente_retorna_404(self):
        r = client.put(
            "/api/v1/zonas/99999",
            json={"nombre_zona": "No existe"},
            headers=_VALID_HEADERS,
        )
        assert r.status_code == 404

    def test_eliminar_zona_retorna_204(self):
        zona = _crear_zona("Zona Eliminar")
        r = client.delete(f"/api/v1/zonas/{zona['id']}", headers=_VALID_HEADERS)
        assert r.status_code == 204

    def test_eliminar_zona_no_aparece_despues(self):
        zona = _crear_zona("Zona Eliminar Verificar")
        zona_id = zona["id"]
        client.delete(f"/api/v1/zonas/{zona_id}", headers=_VALID_HEADERS)
        r = client.get(f"/api/v1/zonas/{zona_id}", headers=_VALID_HEADERS)
        assert r.status_code == 404

    def test_crear_zona_nombre_demasiado_corto_retorna_422(self):
        r = client.post("/api/v1/zonas", json={"nombre_zona": "A"}, headers=_VALID_HEADERS)
        assert r.status_code == 422

    def test_crear_zona_con_descripcion(self):
        data = _crear_zona("Zona Con Descripcion")
        r = client.put(
            f"/api/v1/zonas/{data['id']}",
            json={"nombre_zona": "Zona Con Descripcion", "descripcion": "Una descripción"},
            headers=_VALID_HEADERS,
        )
        assert r.status_code == 200
        assert r.json()["descripcion"] == "Una descripción"
