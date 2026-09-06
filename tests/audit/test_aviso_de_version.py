"""FUN-011 — avisar de una versión nueva y poder instalarla.

El aviso ya existía, pero fallaba en las dos puntas: pulsarlo empezaba la
descarga sin decir qué cambiaba, y al terminar abría el instalador con `open`,
que sólo existe en macOS —en Windows la descarga acababa y no pasaba nada—.
"""

import inspect
import json
import platform
from unittest.mock import MagicMock

import pytest

from utils import update_checker


class _RespuestaFalsa:
    def __init__(self, datos):
        self._datos = json.dumps(datos).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        return False

    def read(self):
        return self._datos


RELEASE = {
    "tag_name": "v9.0.0",
    "body": "  Arreglado el envío de correos.  ",
    "assets": [
        {
            "name": "GuardiasDePatio-9.0.0-Windows-Setup.exe",
            "browser_download_url": "https://github.com/x/y/releases/z.exe",
        },
        {
            "name": "GuardiasDePatio-9.0.0.dmg",
            "browser_download_url": "https://github.com/x/y/releases/z.dmg",
        },
    ],
}


def _comprobar(monkeypatch, datos=RELEASE):
    monkeypatch.setattr(
        update_checker.urllib.request, "urlopen", lambda *a, **k: _RespuestaFalsa(datos)
    )
    recibido = []
    monkeypatch.setattr(update_checker, "Thread", _HiloInmediato)
    update_checker.check_for_updates("1.0.0", lambda *args: recibido.append(args))
    return recibido


class _HiloInmediato:
    """Ejecuta en el acto en vez de en segundo plano, para poder comprobarlo."""

    def __init__(self, target=None, daemon=None):
        self._target = target

    def start(self):
        self._target()


def test_el_aviso_incluye_las_notas_de_la_version(monkeypatch):
    recibido = _comprobar(monkeypatch)

    assert len(recibido) == 1
    version, url, notas = recibido[0]
    assert version == "9.0.0"
    assert notas == "Arreglado el envío de correos."


def test_sin_notas_publicadas_llega_cadena_vacia(monkeypatch):
    datos = dict(RELEASE, body=None)

    recibido = _comprobar(monkeypatch, datos)

    assert recibido[0][2] == ""


def test_no_avisa_si_la_version_no_es_mas_nueva(monkeypatch):
    monkeypatch.setattr(
        update_checker.urllib.request, "urlopen", lambda *a, **k: _RespuestaFalsa(RELEASE)
    )
    monkeypatch.setattr(update_checker, "Thread", _HiloInmediato)
    recibido = []

    update_checker.check_for_updates("9.0.0", lambda *args: recibido.append(args))

    assert recibido == []


@pytest.mark.parametrize(
    "sistema,esperado", [("Darwin", "/usr/bin/open"), ("Linux", "/usr/bin/xdg-open")]
)
def test_cada_sistema_abre_el_instalador_como_sabe(monkeypatch, sistema, esperado):
    monkeypatch.setattr(platform, "system", lambda: sistema)
    ejecutado = MagicMock()
    import subprocess

    monkeypatch.setattr(subprocess, "run", ejecutado)

    update_checker.abrir_instalador("/tmp/instalador")

    assert ejecutado.call_args[0][0][0] == esperado


def test_en_windows_se_usa_startfile(monkeypatch):
    """`open` no existe en Windows: la descarga terminaba y no pasaba nada."""
    import os

    monkeypatch.setattr(platform, "system", lambda: "Windows")
    abierto = MagicMock()
    monkeypatch.setattr(os, "startfile", abierto, raising=False)

    update_checker.abrir_instalador("C:\\temp\\instalador.exe")

    abierto.assert_called_once_with("C:\\temp\\instalador.exe")


def test_el_instalador_no_se_abre_con_open_a_secas():
    """Regresión: era la línea que dejaba a Windows sin poder actualizarse."""
    from presentation.components import menu_lateral

    fuente = inspect.getsource(menu_lateral.SidebarMenu._descargar_e_instalar)
    assert '["open"' not in fuente
    assert "abrir_instalador" in fuente


def test_pulsar_el_aviso_pregunta_antes_de_descargar():
    from presentation.components import menu_lateral

    fuente = inspect.getsource(menu_lateral.SidebarMenu._on_update_banner_clicked)
    assert fuente.index("_confirmar_actualizacion") < fuente.index("_descargar_e_instalar")
