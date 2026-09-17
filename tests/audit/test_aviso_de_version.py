"""FUN-011 — avisar de una versión nueva y poder instalarla.

El aviso ya existía, pero fallaba en las dos puntas: pulsarlo empezaba la
descarga sin decir qué cambiaba, y al terminar abría el instalador con `open`,
que sólo existe en macOS —en Windows la descarga acababa y no pasaba nada—.
"""

import importlib
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
    from presentation.dialogs import actualizacion

    fuente = inspect.getsource(actualizacion.descargar_e_instalar)
    assert '["open"' not in fuente
    assert "instalar_y_salir" in fuente

    lanzamiento = inspect.getsource(actualizacion.instalar_y_salir)
    assert "abrir_instalador" in lanzamiento


def test_la_aplicacion_se_cierra_antes_de_instalar():
    """El instalador no puede reemplazar el ejecutable mientras la app corre:
    en Windows terminaba en «DeleteFile falló; código 5»."""
    from presentation.dialogs import actualizacion

    fuente = inspect.getsource(actualizacion.instalar_y_salir)
    assert fuente.index("closeAllWindows") < fuente.index("abrir_instalador(")
    assert "quit()" in fuente


def test_si_algo_se_niega_a_cerrarse_no_se_instala():
    """Con una ventana abierta la copia fallaría igual y dejaría la instalación
    a medias: mejor no lanzar el instalador."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QWidget

    from presentation.dialogs import actualizacion

    class _VentanaTerca(QWidget):
        def closeEvent(self, evento):  # noqa: N802 - firma de Qt
            evento.ignore()

    app = QApplication.instance() or QApplication([])
    testigo = _VentanaTerca()
    testigo.show()

    lanzados = []
    actualizacion.abrir_instalador = lambda ruta: lanzados.append(ruta)
    try:
        actualizacion.instalar_y_salir(None, "C:/temp/instalador.exe")
    finally:
        testigo.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        testigo.hide()
        importlib.reload(actualizacion)

    assert lanzados == [], "no se puede instalar con la aplicación aún abierta"
    assert app is not None


def test_pulsar_el_aviso_pregunta_antes_de_descargar():
    from presentation.dialogs import actualizacion

    fuente = inspect.getsource(actualizacion.ofrecer)
    assert fuente.index("confirmar(") < fuente.index("descargar_e_instalar(")


def test_el_menu_lateral_y_el_login_ofrecen_lo_mismo():
    """Una sola copia del flujo: el menú lateral tenía la suya y el login habría
    acabado con otra."""
    from presentation.components import menu_lateral
    from presentation.forms import login_dialog

    for fuente in (
        inspect.getsource(menu_lateral.SidebarMenu._on_update_banner_clicked),
        inspect.getsource(login_dialog.LoginDialog._ofrecer_actualizacion),
    ):
        assert "actualizacion.ofrecer(" in fuente


def test_el_login_avisa_de_la_version_nueva_junto_a_la_version(qtbot):
    """Quien no puede entrar porque su versión falla es quien más necesita
    actualizarse, y sólo se avisaba con la sesión ya abierta (SYNC-024)."""
    from presentation.forms.login_dialog import LoginDialog

    dlg = LoginDialog()
    qtbot.addWidget(dlg)

    assert dlg.boton_actualizar.isHidden()

    dlg._mostrar_aviso_de_version("9.9.9", "https://github.com/x/y/z.dmg", "notas")

    assert not dlg.boton_actualizar.isHidden()
    assert "9.9.9" in dlg.boton_actualizar.text()
    assert dlg._url_de_descarga.endswith(".dmg")


def test_el_login_pregunta_por_la_version_sin_bloquear_la_pantalla():
    from presentation.forms import login_dialog

    fuente = inspect.getsource(login_dialog.LoginDialog._comprobar_si_hay_version_nueva)
    # El callback llega desde un hilo suelto: tiene que entrar por una señal,
    # nunca tocar el widget directamente (CRW-005).
    assert "nueva_version_detectada.emit" in fuente


# ---------------------------------------------------------------------------
# BLD-018 — el aviso no llegaba desde la app instalada en macOS
# ---------------------------------------------------------------------------
# El OpenSSL empaquetado busca los certificados raíz en la carpeta del Python
# de compilación (`/Library/Frameworks/Python.framework/…/etc/openssl`), que no
# existe en el Mac del usuario: «CERTIFICATE_VERIFY_FAILED», tragado en
# silencio. La verificación tiene que hacerse con el `cacert.pem` de certifi,
# que ya viaja dentro del paquete.


def test_la_comprobacion_verifica_con_los_certificados_de_certifi(monkeypatch):
    import ssl

    recibido = {}
    monkeypatch.setattr(
        ssl, "create_default_context", lambda cafile=None: recibido.setdefault("cafile", cafile)
    )

    update_checker.contexto_ssl()

    import certifi

    assert recibido["cafile"] == certifi.where()


def test_la_peticion_a_github_lleva_ese_contexto(monkeypatch):
    centinela = object()
    monkeypatch.setattr(update_checker, "contexto_ssl", lambda: centinela)
    llamadas = []

    def _urlopen(*a, **k):
        llamadas.append(k)
        return _RespuestaFalsa(RELEASE)

    monkeypatch.setattr(update_checker.urllib.request, "urlopen", _urlopen)
    monkeypatch.setattr(update_checker, "Thread", _HiloInmediato)

    update_checker.check_for_updates("1.0.0", lambda *args: None)

    assert llamadas[0]["context"] is centinela


def test_un_fallo_al_comprobar_queda_en_el_log(monkeypatch, caplog):
    def _urlopen(*a, **k):
        raise OSError("CERTIFICATE_VERIFY_FAILED")

    monkeypatch.setattr(update_checker.urllib.request, "urlopen", _urlopen)
    monkeypatch.setattr(update_checker, "Thread", _HiloInmediato)

    with caplog.at_level("WARNING", logger=update_checker.__name__):
        update_checker.check_for_updates("1.0.0", lambda *args: None)

    assert "CERTIFICATE_VERIFY_FAILED" in caplog.text


def test_la_descarga_del_instalador_usa_el_mismo_contexto():
    from presentation.dialogs import actualizacion

    fuente = inspect.getsource(actualizacion._Descargador.run)
    assert "contexto_ssl()" in fuente
    # `urlretrieve` no admite contexto: fallaría igual que la comprobación.
    assert "urlretrieve(" not in fuente
