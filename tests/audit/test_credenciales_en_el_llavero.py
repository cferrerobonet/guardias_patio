"""SEC-001 — las contraseñas dejan el fichero de texto y van al llavero.

El `.env` guardaba en claro las contraseñas de SFTP y de correo, sobrevivía a
desinstalar la aplicación y en Windows no tenía más protección que el perfil de
usuario, porque `os.chmod` no aplica permisos POSIX allí.

Ahora van al llavero del sistema y el `.env` se queda con lo que no es secreto.
Si el equipo no tiene llavero se sigue escribiendo el fichero: quedarse sin
poder sincronizar sería peor, pero queda avisado en el registro.
"""

import re
from pathlib import Path

import pytest

from core import credenciales

RAIZ = Path(__file__).resolve().parents[2]


class _LlaveroFalso:
    """Sustituye al llavero del sistema: nada sale del proceso."""

    def __init__(self):
        self.almacen: dict = {}

    def set_password(self, servicio, nombre, valor):
        self.almacen[(servicio, nombre)] = valor

    def get_password(self, servicio, nombre):
        return self.almacen.get((servicio, nombre))

    def delete_password(self, servicio, nombre):
        self.almacen.pop((servicio, nombre), None)


@pytest.fixture
def llavero(monkeypatch):
    falso = _LlaveroFalso()
    monkeypatch.setattr(credenciales, "_llavero", lambda: falso)
    return falso


@pytest.fixture
def sin_llavero(monkeypatch):
    monkeypatch.setattr(credenciales, "_llavero", lambda: None)


def test_lo_guardado_se_recupera(llavero):
    credenciales.guardar("SFTP_PASSWORD", "secreta")

    assert credenciales.leer("SFTP_PASSWORD") == "secreta"


def test_el_llavero_manda_sobre_el_entorno(llavero, monkeypatch):
    """Un `.env` viejo puede traer la contraseña anterior a cambiarla."""
    monkeypatch.setenv("SFTP_PASSWORD", "la_vieja_del_fichero")
    credenciales.guardar("SFTP_PASSWORD", "la_nueva")

    assert credenciales.obtener("SFTP_PASSWORD") == "la_nueva"


def test_sin_llavero_se_usa_el_entorno(sin_llavero, monkeypatch):
    monkeypatch.setenv("SMTP_PASSWORD", "del_fichero")

    assert credenciales.obtener("SMTP_PASSWORD") == "del_fichero"


def test_guardar_la_configuracion_no_escribe_la_contrasena(llavero, tmp_path, monkeypatch):
    monkeypatch.setattr("core.paths.get_base_directory", lambda: tmp_path)

    credenciales.guardar_configuracion(
        {"SFTP_HOST": "sftp.ejemplo.test", "SFTP_PASSWORD": "secreta"}
    )

    escrito = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "sftp.ejemplo.test" in escrito
    assert "secreta" not in escrito
    assert credenciales.leer("SFTP_PASSWORD") == "secreta"


def test_sin_llavero_la_contrasena_sigue_yendo_al_fichero(sin_llavero, tmp_path, monkeypatch):
    """Perder la sincronización sería peor que el riesgo que ya se asumía."""
    monkeypatch.setattr("core.paths.get_base_directory", lambda: tmp_path)

    credenciales.guardar_configuracion({"SFTP_PASSWORD": "secreta"})

    assert "secreta" in (tmp_path / ".env").read_text(encoding="utf-8")


def test_migrar_saca_las_contrasenas_del_fichero(llavero, tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "SFTP_HOST=sftp.ejemplo.test\nSFTP_PASSWORD=secreta\nSMTP_PASSWORD=otra\n",
        encoding="utf-8",
    )

    migradas = credenciales.migrar_desde_env(env)

    assert set(migradas) == {"SFTP_PASSWORD", "SMTP_PASSWORD"}
    texto = env.read_text(encoding="utf-8")
    assert "secreta" not in texto and "otra" not in texto
    assert "SFTP_HOST=sftp.ejemplo.test" in texto
    assert credenciales.leer("SMTP_PASSWORD") == "otra"


def test_migrar_dos_veces_no_hace_nada_la_segunda(llavero, tmp_path):
    env = tmp_path / ".env"
    env.write_text("SFTP_PASSWORD=secreta\n", encoding="utf-8")
    credenciales.migrar_desde_env(env)

    assert credenciales.migrar_desde_env(env) == []


def test_sin_llavero_no_se_toca_el_fichero(sin_llavero, tmp_path):
    """Vaciar la línea sin poder guardar en el llavero perdería la contraseña."""
    env = tmp_path / ".env"
    env.write_text("SFTP_PASSWORD=secreta\n", encoding="utf-8")

    assert credenciales.migrar_desde_env(env) == []
    assert "secreta" in env.read_text(encoding="utf-8")


def test_el_arranque_migra():
    import inspect

    import main

    fuente = inspect.getsource(main)
    assert "migrar_desde_env" in fuente


@pytest.mark.parametrize(
    "modulo,funcion",
    [("config.sftp_config", "_contrasena_sftp"), ("services.email_service", "get_email_service")],
)
def test_los_lectores_preguntan_al_llavero(modulo, funcion):
    import importlib
    import inspect

    fuente = inspect.getsource(getattr(importlib.import_module(modulo), funcion))
    assert "obtener" in fuente


def test_nadie_escribe_ya_en_un_env_relativo():
    """Escribían en el directorio de trabajo, que no es donde se lee."""
    culpables = []
    for ruta in (RAIZ / "src").rglob("*.py"):
        if "__pycache__" in ruta.parts or "egg-info" in str(ruta):
            continue
        if re.search(r'env_path\s*=\s*["\']\.env["\']', ruta.read_text(encoding="utf-8")):
            culpables.append(ruta.name)
    assert culpables == [], f"escriben en un .env relativo: {culpables}"


def test_el_empaquetado_se_lleva_los_almacenes_del_llavero():
    """El llavero elige su almacén al arrancar: PyInstaller no lo ve solo."""
    spec = (RAIZ / "GuardiasDePatio.spec").read_text(encoding="utf-8")
    windows = (RAIZ / "scripts" / "build_windows.ps1").read_text(encoding="utf-8")
    assert "keyring.backends" in spec
    assert "keyring" in windows
