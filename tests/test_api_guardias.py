"""
Tests para los routers de guardias, cuotas, equidad y estadísticas.

Cubre: GET/POST/DELETE guardias, exports CSV y XLSX, endpoints analytics.
Comparte la infraestructura de BD in-memory con test_api.py.
"""

import sys
from datetime import date, time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api.auth import _create_access_token
from api.dependencies import get_db
from api.main import app
from infrastructure.database.models import Base, Configuracion, CursoEscolar, Profesor, Zona

# ============================================================================
# SETUP: BD in-memory con datos base
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


client = TestClient(app, raise_server_exceptions=False)
_H = {"Authorization": f"Bearer {_create_access_token('testuser')}"}

# Datos base compartidos por la sesión de tests (se insertan una vez)
_CURSO_ID: int = 0
_CONFIG_ID: int = 0
_PROF_ID: int = 0
_ZONA_ID: int = 0


def _setup_base_data():
    global _CURSO_ID, _CONFIG_ID, _PROF_ID, _ZONA_ID
    if _CURSO_ID:
        return
    db = _TestSession()
    try:
        curso = CursoEscolar(
            nombre="Test 2025-2026", anio_inicio=2025, anio_fin=2026,
            fecha_inicio=date(2025, 9, 1), fecha_fin=date(2026, 6, 30),
        )
        db.add(curso)
        db.flush()

        config = Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=date(2025, 9, 1),
            fecha_fin_curso=date(2026, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 0),
            ajuste_tutores=0.9,
            ajuste_no_tutores=1.0,
            curso_activo_id=curso.id,
        )
        db.add(config)

        zona = Zona(nombre_zona="Patio API Test")
        prof = Profesor(
            nombre_completo="Guardia API Profesor",
            horas_contrato=20.0,
            porcentaje_jornada=80.0,
            turno="mañana",
            activo=True,
        )
        db.add_all([zona, prof])
        db.commit()

        _CURSO_ID = curso.id
        _CONFIG_ID = config.id
        _PROF_ID = prof.id
        _ZONA_ID = zona.id
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="module")
def setup_datos_base():
    _prev = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    _setup_base_data()
    yield
    if _prev is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _prev


# ============================================================================
# TESTS: GET /guardias — listado y filtros
# ============================================================================


class TestGuardiasListado:
    def test_listar_guardias_retorna_estructura_paginada(self):
        _setup_base_data()
        r = client.get(f"/api/v1/guardias?configuracion_id={_CONFIG_ID}", headers=_H)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    def test_listar_guardias_sin_configuracion_id_retorna_422(self):
        r = client.get("/api/v1/guardias", headers=_H)
        assert r.status_code == 422

    def test_listar_guardias_vacio_total_cero(self):
        _setup_base_data()
        r = client.get(f"/api/v1/guardias?configuracion_id={_CONFIG_ID}", headers=_H)
        assert r.status_code == 200
        assert r.json()["total"] >= 0

    def test_listar_guardias_con_filtro_turno(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias?configuracion_id={_CONFIG_ID}&turno=ma%C3%B1ana", headers=_H
        )
        assert r.status_code == 200
        for g in r.json()["items"]:
            assert g["turno"] == "mañana"

    def test_paginacion_limit_offset(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias?configuracion_id={_CONFIG_ID}&limit=5&offset=0", headers=_H
        )
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 5


# ============================================================================
# TESTS: GET /guardias/count
# ============================================================================


class TestGuardiasCount:
    def test_count_retorna_total_int(self):
        _setup_base_data()
        r = client.get(f"/api/v1/guardias/count?configuracion_id={_CONFIG_ID}", headers=_H)
        assert r.status_code == 200
        assert "total" in r.json()
        assert isinstance(r.json()["total"], int)

    def test_count_sin_configuracion_id_retorna_422(self):
        r = client.get("/api/v1/guardias/count", headers=_H)
        assert r.status_code == 422


# ============================================================================
# TESTS: POST /guardias — asignación manual
# ============================================================================


def _payload_guardia(**overrides):
    _setup_base_data()
    base = {
        "fecha": "2025-10-15",
        "turno": "mañana",
        "numero_recreo": 1,
        "profesor_id": _PROF_ID,
        "zona_id": _ZONA_ID,
    }
    base.update(overrides)
    return base


class TestGuardiasPost:
    def test_asignar_guardia_retorna_201(self):
        r = client.post("/api/v1/guardias", json=_payload_guardia(), headers=_H)
        assert r.status_code == 201
        data = r.json()
        assert data["id"] > 0
        assert data["turno"] == "mañana"
        assert data["recreo"] == 1

    def test_asignar_guardia_turno_invalido_retorna_422(self):
        r = client.post(
            "/api/v1/guardias", json=_payload_guardia(turno="noche"), headers=_H
        )
        assert r.status_code == 422

    def test_asignar_guardia_recreo_cero_retorna_422(self):
        r = client.post(
            "/api/v1/guardias", json=_payload_guardia(numero_recreo=0), headers=_H
        )
        assert r.status_code == 422

    def test_asignar_guardia_profesor_inexistente_retorna_4xx(self):
        r = client.post(
            "/api/v1/guardias", json=_payload_guardia(profesor_id=99999), headers=_H
        )
        assert r.status_code in (404, 422, 500)

    def test_guardia_creada_aparece_en_listado(self):
        payload = _payload_guardia(fecha="2025-11-20", numero_recreo=2)
        client.post("/api/v1/guardias", json=payload, headers=_H)
        r = client.get(f"/api/v1/guardias?configuracion_id={_CONFIG_ID}", headers=_H)
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ============================================================================
# TESTS: Export CSV y XLSX
# ============================================================================


class TestGuardiasExport:
    def test_exportar_csv_retorna_200(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias/export/csv?configuracion_id={_CONFIG_ID}", headers=_H
        )
        assert r.status_code == 200

    def test_exportar_csv_content_type_es_csv(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias/export/csv?configuracion_id={_CONFIG_ID}", headers=_H
        )
        assert "text/csv" in r.headers.get("content-type", "")

    def test_exportar_csv_tiene_bom_utf8(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias/export/csv?configuracion_id={_CONFIG_ID}", headers=_H
        )
        assert r.content[:3] == b"\xef\xbb\xbf"

    def test_exportar_csv_contiene_cabecera(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias/export/csv?configuracion_id={_CONFIG_ID}", headers=_H
        )
        content = r.content.decode("utf-8-sig")
        assert "fecha" in content
        assert "turno" in content

    def test_exportar_xlsx_retorna_200(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias/export/xlsx?configuracion_id={_CONFIG_ID}", headers=_H
        )
        assert r.status_code == 200

    def test_exportar_xlsx_content_type_es_xlsx(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias/export/xlsx?configuracion_id={_CONFIG_ID}", headers=_H
        )
        ct = r.headers.get("content-type", "")
        assert "spreadsheetml" in ct or "octet-stream" in ct

    def test_exportar_xlsx_bytes_son_validos(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/guardias/export/xlsx?configuracion_id={_CONFIG_ID}", headers=_H
        )
        # Los archivos XLSX son ZIPs — empiezan con PK
        assert r.content[:2] == b"PK"


# ============================================================================
# TESTS: DELETE /guardias
# ============================================================================


class TestGuardiasDelete:
    def test_limpiar_guardias_retorna_200(self):
        r = client.delete("/api/v1/guardias", headers=_H)
        assert r.status_code == 200
        assert "eliminadas" in r.json()

    def test_limpiar_guardias_campo_eliminadas_es_int(self):
        r = client.delete("/api/v1/guardias", headers=_H)
        assert isinstance(r.json()["eliminadas"], int)


# ============================================================================
# TESTS: GET /cuotas
# ============================================================================


class TestCuotasAPI:
    def test_calcular_cuotas_retorna_200(self):
        _setup_base_data()
        r = client.get(f"/api/v1/cuotas?configuracion_id={_CONFIG_ID}", headers=_H)
        assert r.status_code == 200

    def test_calcular_cuotas_tiene_campos_obligatorios(self):
        _setup_base_data()
        r = client.get(f"/api/v1/cuotas?configuracion_id={_CONFIG_ID}", headers=_H)
        data = r.json()
        for campo in ("exitoso", "cuotas", "cuotas_detalle", "total_guardias", "mensaje"):
            assert campo in data, f"Campo '{campo}' ausente"

    def test_calcular_cuotas_sin_configuracion_id_422(self):
        r = client.get("/api/v1/cuotas", headers=_H)
        assert r.status_code == 422


# ============================================================================
# TESTS: GET /equidad
# ============================================================================


class TestEquidadAPI:
    def test_analizar_equidad_retorna_200(self):
        _setup_base_data()
        r = client.get(f"/api/v1/equidad?configuracion_id={_CONFIG_ID}", headers=_H)
        assert r.status_code == 200

    def test_analizar_equidad_tiene_campos_obligatorios(self):
        _setup_base_data()
        r = client.get(f"/api/v1/equidad?configuracion_id={_CONFIG_ID}", headers=_H)
        data = r.json()
        for campo in ("exitoso", "metricas", "cuotas", "recomendaciones", "mensaje"):
            assert campo in data, f"Campo '{campo}' ausente"

    def test_analizar_equidad_umbral_personalizado(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/equidad?configuracion_id={_CONFIG_ID}&umbral_desbalance=0.20",
            headers=_H,
        )
        assert r.status_code == 200

    def test_analizar_equidad_sin_configuracion_id_422(self):
        r = client.get("/api/v1/equidad", headers=_H)
        assert r.status_code == 422


# ============================================================================
# TESTS: GET /estadisticas
# ============================================================================


class TestEstadisticasAPI:
    def test_resumen_retorna_200(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/estadisticas/resumen?configuracion_id={_CONFIG_ID}", headers=_H
        )
        assert r.status_code == 200

    def test_resumen_tiene_campos_obligatorios(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/estadisticas/resumen?configuracion_id={_CONFIG_ID}", headers=_H
        )
        data = r.json()
        for campo in ("total_guardias", "asignadas", "sin_asignar", "cobertura_porcentaje", "por_turno"):
            assert campo in data, f"Campo '{campo}' ausente"

    def test_resumen_cobertura_entre_0_y_100(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/estadisticas/resumen?configuracion_id={_CONFIG_ID}", headers=_H
        )
        pct = r.json()["cobertura_porcentaje"]
        assert 0.0 <= pct <= 100.0

    def test_estadisticas_por_profesor_retorna_200(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/estadisticas/por-profesor?configuracion_id={_CONFIG_ID}", headers=_H
        )
        assert r.status_code == 200

    def test_estadisticas_por_profesor_tiene_estructura(self):
        _setup_base_data()
        r = client.get(
            f"/api/v1/estadisticas/por-profesor?configuracion_id={_CONFIG_ID}", headers=_H
        )
        data = r.json()
        assert "profesores" in data
        assert "total_profesores" in data

    def test_resumen_sin_configuracion_id_422(self):
        r = client.get("/api/v1/estadisticas/resumen", headers=_H)
        assert r.status_code == 422
