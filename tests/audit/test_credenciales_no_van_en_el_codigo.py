"""SEC-001 — que el servidor del centro no viaje dentro del programa.

`config/sftp_config.py` traía como valores por defecto el servidor y el usuario
reales del centro. Este repositorio es público y esos valores se compilan dentro
de cada instalador, así que quedaban a la vista de cualquiera: no es la
contraseña, pero es la mitad del par y ahorra tener que adivinar nada.

Encima había un fallo que hacía que ese valor fijo se usara de verdad: el módulo
leía `SFTP_USER` mientras que el diálogo de configuración y Ajustes escriben
`SFTP_USERNAME`. En un equipo configurado desde la propia aplicación, el usuario
tecleado se ignoraba y se conectaba con el que estaba escrito en el código.
"""

import importlib
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]

#: Rastros de la instalación real del centro. Si vuelven a aparecer, es que
#: alguien ha vuelto a escribir credenciales en el código.
RASTROS = (
    re.compile(r"\b[a-z]*\d{6,}\.1and1-data\.host\b", re.I),
    re.compile(r"\bu\d{8}\b"),
)

CARPETAS = (RAIZ / "src", RAIZ / "tests")


def _recargar_configuracion(monkeypatch, **entorno):
    """Recarga el módulo con el entorno controlado y sin leer ningún `.env`.

    Al importarse llama a `load_dotenv`, que rellenaría desde el `.env` del
    equipo justo las claves que este test quiere ver vacías.
    """
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for clave in ("SFTP_HOST", "SFTP_PORT", "SFTP_USER", "SFTP_USERNAME", "SFTP_PASSWORD"):
        monkeypatch.delenv(clave, raising=False)
    for clave, valor in entorno.items():
        monkeypatch.setenv(clave, valor)
    import config.sftp_config as modulo

    return importlib.reload(modulo)


def test_no_hay_servidor_ni_usuario_del_centro_en_el_codigo():
    culpables = []
    for carpeta in CARPETAS:
        for ruta in carpeta.rglob("*.py"):
            if "__pycache__" in ruta.parts or ruta.name == Path(__file__).name:
                continue
            texto = ruta.read_text(encoding="utf-8", errors="ignore")
            if any(rastro.search(texto) for rastro in RASTROS):
                culpables.append(str(ruta.relative_to(RAIZ)))
    assert culpables == [], f"credenciales del centro escritas en: {culpables}"


def test_sin_configuracion_no_se_inventa_un_servidor(monkeypatch):
    """Antes caía en el servidor del centro; ahora se queda vacío y se pide."""
    modulo = _recargar_configuracion(monkeypatch)

    assert modulo.SFTP_CONFIG["host"] == ""
    assert modulo.SFTP_CONFIG["username"] == ""
    assert modulo.validate_sftp_config() is False


def test_se_usa_el_usuario_que_escribe_la_aplicacion(monkeypatch):
    """El diálogo guarda `SFTP_USERNAME`; el módulo leía `SFTP_USER`."""
    modulo = _recargar_configuracion(
        monkeypatch,
        SFTP_HOST="sftp.ejemplo.test",
        SFTP_USERNAME="usuario_tecleado",
        SFTP_PASSWORD="x",
    )

    assert modulo.SFTP_CONFIG["username"] == "usuario_tecleado"


def test_el_nombre_antiguo_sigue_valiendo(monkeypatch):
    """Hay equipos con las dos claves en su `.env`: no se les puede romper."""
    modulo = _recargar_configuracion(
        monkeypatch,
        SFTP_HOST="sftp.ejemplo.test",
        SFTP_USER="usuario_antiguo",
        SFTP_PASSWORD="x",
    )

    assert modulo.SFTP_CONFIG["username"] == "usuario_antiguo"


def test_el_nombre_nuevo_manda_sobre_el_antiguo(monkeypatch):
    modulo = _recargar_configuracion(
        monkeypatch,
        SFTP_HOST="sftp.ejemplo.test",
        SFTP_USER="antiguo",
        SFTP_USERNAME="nuevo",
        SFTP_PASSWORD="x",
    )

    assert modulo.SFTP_CONFIG["username"] == "nuevo"


@pytest.mark.parametrize("falta", ["SFTP_HOST", "SFTP_USERNAME", "SFTP_PASSWORD"])
def test_falta_cualquier_dato_y_se_dice_cuál(monkeypatch, falta):
    entorno = {
        "SFTP_HOST": "sftp.ejemplo.test",
        "SFTP_USERNAME": "alguien",
        "SFTP_PASSWORD": "x",
    }
    entorno.pop(falta)
    modulo = _recargar_configuracion(monkeypatch, **entorno)

    with pytest.raises(ValueError, match="Falta configuración SFTP"):
        modulo.get_sftp_config()


def test_el_instalador_no_empaqueta_credenciales():
    """Ni `.env` ni los JSON de configuración pueden acabar dentro del ejecutable."""
    for fichero in ("GuardiasDePatio.spec", "scripts/build_windows.ps1"):
        texto = (RAIZ / fichero).read_text(encoding="utf-8", errors="ignore")
        for prohibido in (".env", "sftp_config.json", "smtp_config.json"):
            assert prohibido not in texto, f"{fichero} empaqueta {prohibido}"
