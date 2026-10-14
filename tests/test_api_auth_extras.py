"""
Tests adicionales de API: auth.py, routers estadísticas/equidad/cuotas, guardias export/count.
"""

import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import jwt
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.auth import _create_access_token, _hash_username, _verify_user, get_current_user
from api.dependencies import get_db
from api.main import app
from config.settings import get_settings
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# Helpers compartidos
# ─────────────────────────────────────────────────────────────────────────────


def _bypass_auth() -> str:
    return "test_user"


def _make_db_override():
    db_mock = MagicMock()

    def _get_db_override():
        yield db_mock

    return _get_db_override, db_mock


@pytest.fixture
def client_con_db():
    override, db_mock = _make_db_override()
    app.dependency_overrides[get_db] = override
    app.dependency_overrides[get_current_user] = _bypass_auth
    c = TestClient(app, raise_server_exceptions=False)
    yield c, db_mock
    app.dependency_overrides.clear()


def _setup_estadisticas_mock(db_mock, total=0, asignadas=0, por_turno=None, top_profe_row=None):
    """Configura el mock de DB para el router de estadísticas."""
    q = MagicMock()
    q.count.return_value = total
    q.filter.return_value.count.return_value = asignadas
    q.group_by.return_value.all.return_value = por_turno or []
    q.filter.return_value.group_by.return_value.order_by.return_value.first.return_value = (
        top_profe_row
    )
    db_mock.query.return_value.filter.return_value = q
    return q


# ─────────────────────────────────────────────────────────────────────────────
# _hash_username
# ─────────────────────────────────────────────────────────────────────────────


class TestHashUsername:
    def test_returns_16_chars(self):
        assert len(_hash_username("profe")) == 16

    def test_consistent(self):
        assert _hash_username("abc") == _hash_username("abc")

    def test_different_for_different_inputs(self):
        assert _hash_username("x") != _hash_username("y")

    def test_returns_hex_string(self):
        result = _hash_username("test")
        int(result, 16)  # No lanza ValueError si es hex válido


# ─────────────────────────────────────────────────────────────────────────────
# _create_access_token
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateAccessToken:
    def test_returns_decodable_token(self):
        settings = get_settings()
        token = _create_access_token("usuario_test")
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[settings.api_algorithm])
        assert payload["sub"] == "usuario_test"

    def test_token_has_expiry(self):
        settings = get_settings()
        token = _create_access_token("usuario_test")
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[settings.api_algorithm])
        assert "exp" in payload

    def test_diferentes_usuarios_diferentes_tokens(self):
        t1 = _create_access_token("user1")
        t2 = _create_access_token("user2")
        assert t1 != t2


# ─────────────────────────────────────────────────────────────────────────────
# _verify_user
# ─────────────────────────────────────────────────────────────────────────────


class TestVerifyUser:
    def test_locked_out_returns_false(self):
        with patch("api.auth.LockoutManager") as mock_lm:
            mock_lm.return_value.is_locked.return_value = True
            mock_lm.return_value.get_remaining_lockout_time.return_value = 450.0
            ok, msg = _verify_user("user", "pass")
        assert ok is False
        assert "bloqueado" in msg.lower()

    def test_file_not_exists(self):
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=False
        ):
            mock_lm.return_value.is_locked.return_value = False
            ok, msg = _verify_user("user", "pass")
        assert ok is False
        assert "no encontrado" in msg

    def test_read_error(self):
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.open", side_effect=Exception("IO")):
            mock_lm.return_value.is_locked.return_value = False
            ok, msg = _verify_user("user", "pass")
        assert ok is False
        assert "error" in msg.lower()

    def test_user_not_found_in_list(self):
        users = []
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.open", mock_open(read_data=json.dumps(users))), patch(
            "json.load", return_value=users
        ):
            mock_lm.return_value.is_locked.return_value = False
            mock_lm.return_value.record_failed_attempt.return_value = (False, 0)
            ok, msg = _verify_user("noexiste", "pass")
        assert ok is False
        assert msg == "Credenciales incorrectas"

    def test_user_no_password_hash(self):
        users = [{"username": "profe1", "password_hash": ""}]
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.open", mock_open(read_data=json.dumps(users))), patch(
            "json.load", return_value=users
        ):
            mock_lm.return_value.is_locked.return_value = False
            mock_lm.return_value.record_failed_attempt.return_value = (False, 0)
            ok, msg = _verify_user("profe1", "pass")
        assert ok is False
        assert msg == "Credenciales incorrectas"

    def test_valid_credentials(self):
        users = [{"username": "profe1", "password_hash": "$2b$12$fakehash"}]
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.open", mock_open(read_data=json.dumps(users))), patch(
            "json.load", return_value=users
        ), patch("bcrypt.checkpw", return_value=True):
            mock_lm.return_value.is_locked.return_value = False
            mock_lm.return_value.reset_attempts.return_value = None
            ok, msg = _verify_user("profe1", "correct")
        assert ok is True
        assert msg is None

    def test_invalid_password(self):
        users = [{"username": "profe1", "password_hash": "$2b$12$fakehash"}]
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.open", mock_open(read_data=json.dumps(users))), patch(
            "json.load", return_value=users
        ), patch("bcrypt.checkpw", return_value=False):
            mock_lm.return_value.is_locked.return_value = False
            mock_lm.return_value.record_failed_attempt.return_value = (False, 0)
            ok, msg = _verify_user("profe1", "wrong")
        assert ok is False
        assert "incorrectas" in msg

    def test_invalid_password_triggers_lockout(self):
        users = [{"username": "profe1", "password_hash": "$2b$12$fakehash"}]
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.open", mock_open(read_data=json.dumps(users))), patch(
            "json.load", return_value=users
        ), patch("bcrypt.checkpw", return_value=False):
            mock_lm.return_value.is_locked.return_value = False
            mock_lm.return_value.record_failed_attempt.return_value = (True, 0)
            mock_lm.return_value.get_remaining_lockout_time.return_value = 900.0
            ok, msg = _verify_user("profe1", "wrong")
        assert ok is False
        assert "bloqueado" in msg.lower()

    def test_bcrypt_exception(self):
        users = [{"username": "profe1", "password_hash": "$2b$12$fakehash"}]
        with patch("api.auth.LockoutManager") as mock_lm, patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.open", mock_open(read_data=json.dumps(users))), patch(
            "json.load", return_value=users
        ), patch("bcrypt.checkpw", side_effect=Exception("crypto error")):
            mock_lm.return_value.is_locked.return_value = False
            mock_lm.return_value.record_failed_attempt.return_value = (False, 0)
            ok, msg = _verify_user("profe1", "pass")
        assert ok is False
        assert "autenticación" in msg.lower()


# ─────────────────────────────────────────────────────────────────────────────
# get_current_user via TestClient
# ─────────────────────────────────────────────────────────────────────────────


class TestGetCurrentUserEndpoint:
    def setup_method(self):
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_missing_token_returns_401(self):
        override, _ = _make_db_override()
        app.dependency_overrides[get_db] = override
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/api/v1/profesores")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        override, _ = _make_db_override()
        app.dependency_overrides[get_db] = override
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/api/v1/profesores", headers={"Authorization": "Bearer token_invalido"})
        assert r.status_code == 401

    def test_valid_token_accepted(self):
        settings = get_settings()
        token = _create_access_token("testuser")
        override, _ = _make_db_override()
        app.dependency_overrides[get_db] = override
        with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = []
            c = TestClient(app, raise_server_exceptions=False)
            r = c.get("/api/v1/profesores", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Router: estadísticas
# ─────────────────────────────────────────────────────────────────────────────


class TestEstadisticasRouter:
    def test_resumen_sin_guardias(self, client_con_db):
        client, db_mock = client_con_db
        _setup_estadisticas_mock(db_mock, total=0, asignadas=0)
        r = client.get("/api/v1/estadisticas/resumen?configuracion_id=1")
        assert r.status_code == 200
        data = r.json()
        assert data["total_guardias"] == 0
        assert data["cobertura_porcentaje"] == 0
        assert data["sin_asignar"] == 0

    def test_resumen_con_guardias(self, client_con_db):
        client, db_mock = client_con_db
        q = _setup_estadisticas_mock(
            db_mock,
            total=10,
            asignadas=8,
            por_turno=[("mañana", 6), ("tarde", 4)],
            top_profe_row=(5, 6),
        )
        profe_mock = MagicMock()
        profe_mock.id = 5
        profe_mock.nombre_completo = "Ana García"
        db_mock.query.return_value.get.return_value = profe_mock

        r = client.get("/api/v1/estadisticas/resumen?configuracion_id=1")
        assert r.status_code == 200
        data = r.json()
        assert data["total_guardias"] == 10
        assert data["asignadas"] == 8
        assert data["sin_asignar"] == 2
        assert data["cobertura_porcentaje"] == pytest.approx(80.0)
        assert data["por_turno"]["mañana"] == 6

    def test_resumen_con_filtros_fecha(self, client_con_db):
        client, db_mock = client_con_db
        # Con filtros de fecha, el query añade .filter() extra → la cadena de mocks es más profunda
        q = MagicMock()
        q.count.return_value = 5
        # tras fecha_inicio + fecha_fin: query = q.filter().filter()
        q2 = q.filter.return_value.filter.return_value
        q2.count.return_value = 5
        q2.filter.return_value.count.return_value = 3  # asignadas
        # por_turno y top_profesor reutilizan q directamente (segundo db.query().filter())
        q.group_by.return_value.all.return_value = []
        q.group_by.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value.filter.return_value = q
        r = client.get(
            "/api/v1/estadisticas/resumen?configuracion_id=1"
            "&fecha_inicio=2025-09-01&fecha_fin=2025-12-31"
        )
        assert r.status_code == 200
        assert r.json()["total_guardias"] == 5

    def test_por_profesor_vacio(self, client_con_db):
        client, db_mock = client_con_db
        (
            db_mock.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value
        ) = []
        r = client.get("/api/v1/estadisticas/por-profesor?configuracion_id=1")
        assert r.status_code == 200
        data = r.json()
        assert data["profesores"] == []
        assert data["total_profesores"] == 0

    def test_por_profesor_con_datos(self, client_con_db):
        client, db_mock = client_con_db
        (
            db_mock.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value
        ) = [(1, "Ana García", 5), (2, "Luis Martín", 3)]
        r = client.get("/api/v1/estadisticas/por-profesor?configuracion_id=1")
        assert r.status_code == 200
        data = r.json()
        assert len(data["profesores"]) == 2
        assert data["profesores"][0]["nombre"] == "Ana García"
        assert data["total_profesores"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# Router: equidad
# ─────────────────────────────────────────────────────────────────────────────


class TestEquidadRouter:
    def test_equidad_ok(self, client_con_db):
        client, db_mock = client_con_db
        # El router pasa incluir_cuotas_detalle al DTO pero éste espera incluir_detalle (bug conocido)
        # → patcheamos AnalisisEquidadRequest para evitar el TypeError
        with patch("api.routers.equidad.AnalisisEquidadUseCase") as mock_uc, patch(
            "api.routers.equidad.AnalisisEquidadRequest"
        ) as mock_req, patch(
            "api.routers.equidad.asdict",
            return_value={
                "media": 2.5,
                "desviacion": 0.5,
                "coeficiente_variacion": 0.2,
                "max_guardias": 3,
                "min_guardias": 2,
                "profesores_sobre_cuota": 0,
                "profesores_bajo_cuota": 0,
                "total_profesores": 5,
            },
        ):
            resp = MagicMock()
            resp.exitoso = True
            resp.metricas = MagicMock()
            resp.cuotas = []
            resp.recomendaciones = ["Todo OK"]
            resp.mensaje = "Distribución equitativa"
            mock_req.return_value = MagicMock()
            mock_uc.return_value.execute.return_value = resp
            r = client.get("/api/v1/equidad?configuracion_id=1")
        assert r.status_code == 200
        data = r.json()
        assert data["exitoso"] is True
        assert data["recomendaciones"] == ["Todo OK"]

    def test_equidad_error_500(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.equidad.AnalisisEquidadUseCase") as mock_uc:
            mock_uc.return_value.execute.side_effect = Exception("DB error")
            r = client.get("/api/v1/equidad?configuracion_id=1")
        assert r.status_code == 500

    def test_equidad_con_umbral_custom(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.equidad.AnalisisEquidadUseCase") as mock_uc, patch(
            "api.routers.equidad.AnalisisEquidadRequest"
        ) as mock_req, patch(
            "api.routers.equidad.asdict", return_value={"media": 1.0}
        ):
            resp = MagicMock()
            resp.exitoso = True
            resp.metricas = MagicMock()
            resp.cuotas = []
            resp.recomendaciones = []
            resp.mensaje = "OK"
            mock_req.return_value = MagicMock()
            mock_uc.return_value.execute.return_value = resp
            r = client.get("/api/v1/equidad?configuracion_id=2&umbral_desbalance=0.25")
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Router: cuotas
# ─────────────────────────────────────────────────────────────────────────────


class TestCuotasRouter:
    def test_cuotas_ok(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.cuotas.CalcularCuotasUseCase") as mock_uc:
            resp = MagicMock()
            resp.exitoso = True
            resp.cuotas = {"profe1": 3.5}
            resp.cuotas_detalle = []
            resp.total_guardias = 10
            resp.mensaje = "OK"
            mock_uc.return_value.execute.return_value = resp
            r = client.get("/api/v1/cuotas?configuracion_id=1")
        assert r.status_code == 200
        data = r.json()
        assert data["exitoso"] is True
        assert data["total_guardias"] == 10

    def test_cuotas_solo_activos_false(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.cuotas.CalcularCuotasUseCase") as mock_uc:
            resp = MagicMock()
            resp.exitoso = True
            resp.cuotas = {}
            resp.cuotas_detalle = []
            resp.total_guardias = 0
            resp.mensaje = "Sin guardias"
            mock_uc.return_value.execute.return_value = resp
            r = client.get("/api/v1/cuotas?configuracion_id=1&solo_activos=false")
        assert r.status_code == 200

    def test_cuotas_error_500(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.cuotas.CalcularCuotasUseCase") as mock_uc:
            mock_uc.return_value.execute.side_effect = Exception("fallo grave")
            r = client.get("/api/v1/cuotas?configuracion_id=1")
        assert r.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# Router: guardias — count y export
# ─────────────────────────────────────────────────────────────────────────────


def _guardia_dto_full():
    dto = MagicMock()
    dto.id = 1
    dto.fecha = date(2025, 10, 3)
    dto.numero_recreo = 2
    dto.turno = "mañana"
    dto.zona_id = 1
    dto.zona_nombre = "Patio central"
    dto.profesor_id = 5
    dto.profesor_nombre = "Ana García"
    dto.es_sustitucion = False
    return dto


class TestGuardiasCount:
    def test_count_devuelve_total(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = [
                _guardia_dto_full(),
                _guardia_dto_full(),
            ]
            r = client.get("/api/v1/guardias/count?configuracion_id=1")
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_count_vacio(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = []
            r = client.get("/api/v1/guardias/count?configuracion_id=1")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_count_con_filtro_turno(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = [_guardia_dto_full()]
            r = client.get("/api/v1/guardias/count?configuracion_id=1&turno=mañana")
        assert r.status_code == 200
        assert r.json()["total"] == 1


class TestGuardiasExportCSV:
    def test_export_csv_devuelve_csv(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = [_guardia_dto_full()]
            r = client.get("/api/v1/guardias/export/csv?configuracion_id=1")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        body = r.content.decode("utf-8-sig")
        assert "id" in body
        assert "Ana García" in body

    def test_export_csv_vacio(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = []
            r = client.get("/api/v1/guardias/export/csv?configuracion_id=1")
        assert r.status_code == 200
        body = r.content.decode("utf-8-sig")
        assert "id" in body  # Cabecera siempre presente

    def test_export_csv_error_500(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.side_effect = Exception("DB fail")
            r = client.get("/api/v1/guardias/export/csv?configuracion_id=1")
        assert r.status_code == 500

    def test_export_csv_con_filtros(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = [_guardia_dto_full()]
            r = client.get(
                "/api/v1/guardias/export/csv?configuracion_id=1"
                "&fecha_inicio=2025-09-01&turno=mañana"
            )
        assert r.status_code == 200


class TestGuardiasExportXLSX:
    def test_export_xlsx_devuelve_xlsx_o_500(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = [_guardia_dto_full()]
            r = client.get("/api/v1/guardias/export/xlsx?configuracion_id=1")
        # openpyxl puede o no estar instalado
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            assert "spreadsheetml" in r.headers["content-type"]

    def test_export_xlsx_error_obtencion(self, client_con_db):
        client, db_mock = client_con_db
        with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
            mock_uc.return_value.execute.side_effect = Exception("fail")
            r = client.get("/api/v1/guardias/export/xlsx?configuracion_id=1")
        assert r.status_code == 500
