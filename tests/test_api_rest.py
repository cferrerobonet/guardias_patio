"""
Tests API REST — Fase 6 P1

Valida endpoints de profesores y guardias usando TestClient de FastAPI
con inyección de dependencias (override get_db) para no tocar la BD real.
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.auth import get_current_user
from api.dependencies import get_db
from api.main import app


def _bypass_auth():
    """Override de get_current_user para tests — devuelve usuario ficticio."""
    return "test_user"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_db_override():
    """Devuelve una función de override que inyecta una sesión mock."""
    db_mock = MagicMock()

    def _get_db_override():
        yield db_mock

    return _get_db_override, db_mock


@pytest.fixture
def client_con_db():
    """TestClient con get_db y get_current_user sobreescritos para tests."""
    override, db_mock = _make_db_override()
    app.dependency_overrides[get_db] = override
    app.dependency_overrides[get_current_user] = _bypass_auth
    c = TestClient(app, raise_server_exceptions=False)
    yield c, db_mock
    app.dependency_overrides.clear()


@pytest.fixture
def client_profesores(client_con_db):
    """TestClient con ListarProfesoresUseCase y ObtenerProfesorUseCase mockeados."""
    client, db_mock = client_con_db
    return client, db_mock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _profesor_dto(id_: int = 1, activo: bool = True, turno: str = "mañana"):
    dto = MagicMock()
    dto.id = id_
    dto.nombre_completo = f"Profesor {id_}"
    dto.horas_contrato = 18.0
    dto.porcentaje_jornada = 100.0
    dto.turno = turno
    dto.activo = activo
    dto.email_corporativo = f"p{id_}@ejemplo.es"
    return dto


def _guardia_dto(id_: int = 1):
    dto = MagicMock()
    dto.id = id_
    dto.fecha = date(2025, 9, 10)
    dto.numero_recreo = 2
    dto.turno = "mañana"
    dto.zona_id = 1
    dto.zona_nombre = "Patio central"
    dto.profesor_id = 5
    dto.profesor_nombre = "Ana García"
    dto.es_sustitucion = False
    return dto


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


def test_root_devuelve_nombre():
    """El endpoint raíz devuelve información del servicio."""
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "Guardias de Patio" in data["nombre"]
    assert "endpoints" in data


def test_health_devuelve_200_o_503():
    """El health check devuelve 200 o 503 según el estado."""
    with TestClient(app) as c:
        r = c.get("/health")
    assert r.status_code in (200, 503)
    assert "status" in r.json()


# ---------------------------------------------------------------------------
# GET /api/v1/profesores
# ---------------------------------------------------------------------------


def test_listar_profesores_vacio(client_profesores):
    """Devuelve lista vacía cuando el use case no tiene datos."""
    client, _ = client_profesores
    with patch(
        "api.routers.profesores.ListarProfesoresUseCase"
    ) as mock_uc:
        mock_uc.return_value.execute.return_value = []
        r = client.get("/api/v1/profesores")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["has_more"] is False


def test_listar_profesores_devuelve_lista(client_profesores):
    """Devuelve los profesores que proporciona el use case."""
    client, _ = client_profesores
    profesores = [_profesor_dto(1), _profesor_dto(2)]
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = profesores
        r = client.get("/api/v1/profesores")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == 1
    assert data["items"][1]["id"] == 2
    assert data["total"] == 2


def test_listar_profesores_filtro_activo(client_profesores):
    """El filtro activo=true filtra los inactivos en el router."""
    client, _ = client_profesores
    profesores = [_profesor_dto(1, activo=True), _profesor_dto(2, activo=False)]
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = profesores
        r = client.get("/api/v1/profesores?activo=true")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["activo"] is True


def test_listar_profesores_filtro_turno(client_profesores):
    """El filtro turno filtra los que no coinciden."""
    client, _ = client_profesores
    profesores = [_profesor_dto(1, turno="mañana"), _profesor_dto(2, turno="tarde")]
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = profesores
        r = client.get("/api/v1/profesores?turno=tarde")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["turno"] == "tarde"


def test_listar_profesores_error_interno(client_profesores):
    """Devuelve 500 si el use case lanza una excepción."""
    client, _ = client_profesores
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.side_effect = RuntimeError("DB caída")
        r = client.get("/api/v1/profesores")
    assert r.status_code == 500


def test_listar_profesores_error_schema_estandar(client_profesores):
    """El error 500 devuelve schema estándar {error: {code, message}}."""
    client, _ = client_profesores
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.side_effect = RuntimeError("fallo")
        r = client.get("/api/v1/profesores")
    assert r.status_code == 500
    detail = r.json()["detail"]
    assert detail["code"] == "internal_error"
    assert "message" in detail


def test_listar_profesores_paginacion_offset(client_profesores):
    """El parámetro offset pagina correctamente."""
    client, _ = client_profesores
    profesores = [_profesor_dto(i) for i in range(1, 6)]  # 5 profesores
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = profesores
        r = client.get("/api/v1/profesores?offset=2&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == 3
    assert data["total"] == 5
    assert data["offset"] == 2
    assert data["limit"] == 2
    assert data["has_more"] is True


def test_listar_profesores_paginacion_has_more_false(client_profesores):
    """has_more es False cuando no hay más páginas."""
    client, _ = client_profesores
    profesores = [_profesor_dto(i) for i in range(1, 4)]  # 3 profesores
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = profesores
        r = client.get("/api/v1/profesores?offset=0&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["has_more"] is False
    assert data["total"] == 3


def test_listar_profesores_limit_invalido(client_profesores):
    """limit=0 devuelve 422."""
    client, _ = client_profesores
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = []
        r = client.get("/api/v1/profesores?limit=0")
    assert r.status_code == 422


def test_listar_profesores_offset_negativo(client_profesores):
    """offset negativo devuelve 422."""
    client, _ = client_profesores
    with patch("api.routers.profesores.ListarProfesoresUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = []
        r = client.get("/api/v1/profesores?offset=-1")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/profesores/{id}
# ---------------------------------------------------------------------------


def test_obtener_profesor_existente(client_profesores):
    """Devuelve el profesor cuando existe."""
    client, _ = client_profesores
    dto = _profesor_dto(7)
    with patch("api.routers.profesores.ObtenerProfesorUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = dto
        r = client.get("/api/v1/profesores/7")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 7
    assert data["email"] == "p7@ejemplo.es"


def test_obtener_profesor_no_encontrado(client_profesores):
    """Devuelve 404 cuando el use case devuelve None."""
    client, _ = client_profesores
    with patch("api.routers.profesores.ObtenerProfesorUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = None
        r = client.get("/api/v1/profesores/999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/guardias
# ---------------------------------------------------------------------------


def test_listar_guardias_vacio(client_con_db):
    """Devuelve lista vacía cuando el use case no tiene datos."""
    client, _ = client_con_db
    with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = []
        r = client.get("/api/v1/guardias?configuracion_id=1")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_guardias_devuelve_datos(client_con_db):
    """Devuelve las guardias que proporciona el use case."""
    client, _ = client_con_db
    guardias = [_guardia_dto(1), _guardia_dto(2)]
    with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = guardias
        r = client.get("/api/v1/guardias?configuracion_id=1")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["zona_nombre"] == "Patio central"


def test_listar_guardias_paginacion(client_con_db):
    """El parámetro limit recorta el resultado."""
    client, _ = client_con_db
    guardias = [_guardia_dto(i) for i in range(1, 6)]
    with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = guardias
        r = client.get("/api/v1/guardias?configuracion_id=1&limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_listar_guardias_offset(client_con_db):
    """El parámetro offset salta los primeros resultados."""
    client, _ = client_con_db
    guardias = [_guardia_dto(i) for i in range(1, 6)]
    with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = guardias
        r = client.get("/api/v1/guardias?configuracion_id=1&offset=3&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["id"] == 4


def test_listar_guardias_limit_maximo(client_con_db):
    """limit > 1000 es rechazado por la validación de Query."""
    client, _ = client_con_db
    with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = []
        r = client.get("/api/v1/guardias?configuracion_id=1&limit=9999")
    assert r.status_code == 422  # Unprocessable Entity


def test_listar_guardias_error_interno(client_con_db):
    """Devuelve 500 si el use case lanza una excepción."""
    client, _ = client_con_db
    with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
        mock_uc.return_value.execute.side_effect = RuntimeError("Error")
        r = client.get("/api/v1/guardias?configuracion_id=1")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/guardias/count
# ---------------------------------------------------------------------------


def test_contar_guardias(client_con_db):
    """Devuelve el total de guardias."""
    client, _ = client_con_db
    guardias = [_guardia_dto(i) for i in range(1, 4)]
    with patch("api.routers.guardias.ObtenerGuardiasUseCase") as mock_uc:
        mock_uc.return_value.execute.return_value = guardias
        r = client.get("/api/v1/guardias/count?configuracion_id=1")
    assert r.status_code == 200
    assert r.json()["total"] == 3


# ---------------------------------------------------------------------------
# Tests SMTP mock
# ---------------------------------------------------------------------------


def test_email_send_recovery_code_ok():
    """send_recovery_code devuelve True con servidor SMTP mockeado."""
    import smtplib

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from services.email_service import EmailService

    svc = EmailService(
        smtp_server="smtp.test.local",
        smtp_port=587,
        smtp_user="user@test.local",
        smtp_password="secret",
        from_email="noreply@test.local",
    )

    mock_smtp = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp):
        mock_smtp.__enter__ = lambda s: mock_smtp
        mock_smtp.__exit__ = MagicMock(return_value=False)
        ok, msg = svc.send_recovery_code(
            to_email="dest@test.local",
            username="testuser",
            recovery_code="ABC123",
        )

    assert ok is True
    assert "dest@test.local" in msg


def test_email_send_recovery_code_auth_error():
    """send_recovery_code devuelve False con SMTPAuthenticationError."""
    import smtplib

    from services.email_service import EmailService

    svc = EmailService(
        smtp_server="smtp.test.local",
        smtp_port=587,
        smtp_user="user@test.local",
        smtp_password="wrong",
        from_email="noreply@test.local",
    )

    with patch("smtplib.SMTP") as mock_cls:
        mock_cls.return_value.__enter__ = MagicMock(
            side_effect=smtplib.SMTPAuthenticationError(535, b"Auth failed")
        )
        ok, msg = svc.send_recovery_code(
            to_email="dest@test.local",
            username="testuser",
            recovery_code="XYZ",
        )

    assert ok is False


def test_email_sin_credenciales_no_envia():
    """Si no hay credenciales, send_recovery_code devuelve False sin intentar conexión."""
    from services.email_service import EmailService

    svc = EmailService()  # sin credenciales

    ok, msg = svc.send_recovery_code("x@y.com", "user", "123456")
    assert ok is False


# ---------------------------------------------------------------------------
# Tests SFTP mock
# ---------------------------------------------------------------------------


def test_sftp_upload_llama_paramiko():
    """SFTPSyncBackend.upload_file llama a paramiko (mockeado)."""
    import tempfile

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from sync.sync_manager import SFTPSyncBackend

    mock_paramiko = MagicMock()
    mock_ssh = MagicMock()
    mock_sftp = MagicMock()
    mock_paramiko.SSHClient.return_value = mock_ssh
    mock_ssh.open_sftp.return_value = mock_sftp
    mock_paramiko.RejectPolicy = MagicMock
    mock_paramiko.RSAKey.from_private_key_file = MagicMock(return_value=MagicMock())

    with patch.dict("sys.modules", {"paramiko": mock_paramiko}):
        backend = SFTPSyncBackend(
            host="sftp.test.local",
            port=22,
            username="user",
            password="pass",
            base_dir="/remote",
        )
        # Simular conexión ya establecida
        backend.sftp = mock_sftp

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            local = Path(f.name)

        result = backend.upload_file(local, "backup.db")

    assert result is True
    mock_sftp.put.assert_called_once()
    local.unlink(missing_ok=True)


def test_local_backend_safe_path_bloquea_traversal(tmp_path):
    """LocalSyncBackend._safe_path rechaza rutas con path traversal."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from sync.sync_manager import LocalSyncBackend

    backend = LocalSyncBackend(tmp_path)

    with pytest.raises(ValueError, match="Path no permitido"):
        backend._safe_path("../../etc/passwd")
