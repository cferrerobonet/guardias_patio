"""GUA-GIT-005: tras un rechazo o un fallo, la app no reintenta la conexión SFTP en bucle.

El servidor corta el puerto 22 a quien encadena conexiones. Antes, cada latido de la
sesión (30 s) y cada fichero de una sincronización abría una conexión nueva si la
anterior había fallado. Todo sin red: paramiko se sustituye por dobles.
"""

from unittest.mock import MagicMock, patch

import paramiko
import pytest

from sync import limite_conexiones
from sync.backends import SFTPSyncBackend
from sync.limite_conexiones import (
    ESPERA_MAXIMA,
    TOPE_AUTOMATICO,
    LimiteDeConexiones,
    espera_tras,
)


class _Reloj:
    def __init__(self, ahora: float = 1_000_000.0):
        self.ahora = ahora

    def __call__(self) -> float:
        return self.ahora

    def avanzar(self, segundos: float) -> None:
        self.ahora += segundos


@pytest.fixture
def reloj():
    return _Reloj()


@pytest.fixture
def limite(tmp_path, reloj):
    nuevo = LimiteDeConexiones(ruta=tmp_path / "limite.json", reloj=reloj)
    limite_conexiones.usar_limite(nuevo)
    return nuevo


def _backend_sin_conectar() -> SFTPSyncBackend:
    backend = SFTPSyncBackend.__new__(SFTPSyncBackend)
    backend._host, backend._port = "sftp.example.com", 22
    backend._username, backend._password = "usuario", "contrasena-de-pruebas"
    backend.base_dir = "/guardias_patio"
    backend.sftp = None
    backend.client = None
    return backend


def _cliente_que_falla(error: Exception) -> MagicMock:
    cliente = MagicMock()
    cliente.return_value.connect.side_effect = error
    return cliente


# --- La regla ---------------------------------------------------------------


def test_la_espera_se_dobla_con_cada_fallo_y_tiene_tope():
    assert [espera_tras(n) for n in range(0, 8)] == [0, 30, 60, 120, 240, 480, 900, 900]
    assert espera_tras(50) == ESPERA_MAXIMA


def test_tras_un_fallo_no_se_vuelve_a_intentar_hasta_que_pasa_la_espera(limite, reloj):
    assert limite.puede_intentar()
    limite.registrar_fallo()
    assert not limite.puede_intentar()
    assert "30 s" in limite.motivo()
    reloj.avanzar(29)
    assert not limite.puede_intentar()
    reloj.avanzar(1)
    assert limite.puede_intentar()

    limite.registrar_fallo()
    reloj.avanzar(59)
    assert not limite.puede_intentar(), "la segunda espera tiene que ser el doble"
    reloj.avanzar(1)
    assert limite.puede_intentar()


def test_tras_el_tope_la_app_deja_de_intentarlo_sola(limite, reloj):
    for _ in range(TOPE_AUTOMATICO):
        assert limite.puede_intentar()
        limite.registrar_fallo()
        reloj.avanzar(ESPERA_MAXIMA)

    assert not limite.puede_intentar(automatico=True)
    assert "no se volverá a intentar sola" in limite.motivo(automatico=True)
    assert limite.puede_intentar(automatico=False), "quien lo pide puede probar tras la espera"


def test_una_conexion_buena_pone_la_cuenta_a_cero(limite, reloj):
    limite.registrar_fallo()
    reloj.avanzar(30)
    limite.registrar_exito()
    assert limite.fallos_seguidos == 0
    limite.registrar_fallo()
    reloj.avanzar(30)
    assert limite.puede_intentar(), "tras el éxito la espera vuelve a empezar en 30 s"


def test_cerrar_y_abrir_la_app_no_reinicia_la_espera(tmp_path, reloj):
    ruta = tmp_path / "limite.json"
    primera = LimiteDeConexiones(ruta=ruta, reloj=reloj)
    primera.registrar_fallo()
    primera.registrar_fallo()

    reloj.avanzar(10)
    reabierta = LimiteDeConexiones(ruta=ruta, reloj=reloj)
    assert reabierta.fallos_seguidos == 2
    assert not reabierta.puede_intentar(automatico=False)
    reloj.avanzar(50)
    assert reabierta.puede_intentar(automatico=False)


def test_un_estado_ilegible_no_impide_conectar(tmp_path, reloj):
    ruta = tmp_path / "limite.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    assert LimiteDeConexiones(ruta=ruta, reloj=reloj).puede_intentar()


# --- La app la respeta ------------------------------------------------------


def test_el_latido_y_las_subidas_no_abren_una_conexion_tras_otra(limite, reloj, tmp_path):
    """Sin el límite, diez operaciones seguidas eran diez conexiones fallidas."""
    fichero = tmp_path / "marca.json"
    fichero.write_text("{}", encoding="utf-8")
    backend = _backend_sin_conectar()
    cliente = _cliente_que_falla(OSError("conexión rechazada"))

    with patch.object(paramiko, "SSHClient", cliente):
        for _ in range(10):
            assert backend.upload_file(fichero, "sesion.lock") is False
        assert cliente.return_value.connect.call_count == 1

        reloj.avanzar(30)
        backend.upload_file(fichero, "sesion.lock")
        assert cliente.return_value.connect.call_count == 2


def test_un_rechazo_de_contrasena_tambien_cuenta(limite):
    backend = _backend_sin_conectar()
    cliente = _cliente_que_falla(paramiko.AuthenticationException("Authentication failed."))

    with patch.object(paramiko, "SSHClient", cliente):
        assert backend._connect_once() is False
        assert backend._connect_once() is False
    assert cliente.return_value.connect.call_count == 1
    assert limite.fallos_seguidos == 1


def test_un_servidor_sin_confirmar_no_cuenta_como_fallo(limite):
    """Lo rechaza este equipo y a continuación se pregunta por la huella: tras
    confirmarla hay que poder conectar en el acto."""
    backend = _backend_sin_conectar()
    error = paramiko.SSHException("Server '[sftp.example.com]:22' not found in known_hosts")

    with patch.object(paramiko, "SSHClient", _cliente_que_falla(error)):
        assert backend._connect_once() is False
    assert limite.fallos_seguidos == 0
    assert limite.puede_intentar()


def test_una_conexion_buena_desde_la_app_pone_la_cuenta_a_cero(limite, reloj):
    limite.registrar_fallo()
    reloj.avanzar(30)
    backend = _backend_sin_conectar()

    with patch.object(paramiko, "SSHClient", MagicMock()):
        assert backend._connect_once() is True
    assert limite.fallos_seguidos == 0


def test_al_arrancar_en_espera_se_dice_por_que_y_no_se_conecta(limite):
    limite.registrar_fallo()
    cliente = MagicMock()

    with patch.object(paramiko, "SSHClient", cliente):
        with pytest.raises(ConnectionError, match="no se volverá a intentar hasta dentro de"):
            SFTPSyncBackend(host="sftp.example.com", port=22, username="u", password="p")
    cliente.assert_not_called()


def test_pedir_la_huella_en_espera_no_conecta(limite):
    from sync import huella_servidor

    limite.registrar_fallo()
    transporte = MagicMock()

    with patch.object(paramiko, "Transport", transporte):
        with pytest.raises(ConnectionError):
            huella_servidor.clave_del_servidor("sftp.example.com", 22)
    transporte.assert_not_called()


def test_probar_la_conexion_varias_veces_seguidas_no_martillea(limite):
    """«Probar» en la configuración inicial: el segundo clic tras un fallo espera."""
    from presentation.dialogs import initial_config_dialog as modulo

    dialogo = modulo.InitialConfigDialog.__new__(modulo.InitialConfigDialog)
    for campo, valor in {
        "sftp_host_input": "sftp.example.com",
        "sftp_port_input": "22",
        "sftp_user_input": "usuario",
        "sftp_password_input": "contrasena-de-pruebas",
        "sftp_basedir_input": "/guardias_patio",
    }.items():
        entrada = MagicMock()
        entrada.text.return_value = valor
        setattr(dialogo, campo, entrada)
    dialogo._sftp_password = ""

    transporte = MagicMock()
    transporte.return_value.connect.side_effect = paramiko.AuthenticationException("no")

    with patch.object(modulo.paramiko, "Transport", transporte):
        ok, mensaje = dialogo._probar_conexion_sftp()
        assert not ok and "rechazó" in mensaje
        ok, mensaje = dialogo._probar_conexion_sftp()
    assert not ok and "30 s" in mensaje
    assert transporte.call_count == 1


def test_toda_conexion_sftp_del_codigo_pasa_por_el_limite():
    """Una conexión nueva que no consulte el límite vuelve a abrir la puerta al bucle."""
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src"
    sin_limite = [
        str(fichero.relative_to(src))
        for fichero in src.rglob("*.py")
        if "egg-info" not in str(fichero)
        and any(
            señal in (texto := fichero.read_text(encoding="utf-8"))
            for señal in ("paramiko.Transport(", "paramiko.SSHClient(")
        )
        and "limite_sftp()" not in texto
    ]
    assert not sin_limite, f"abren conexión SFTP sin consultar el límite: {sin_limite}"
