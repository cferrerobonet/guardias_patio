"""Dos fallos vistos por CarlosFB al arrancar tras la v5.95.0 (2026-09-06).

1. La aplicación volvía a pedir la configuración de servidor en cada arranque.
   Al llevar las contraseñas al llavero, el `.env` se queda con la línea vacía,
   y la comprobación de arranque seguía mirando sólo el fichero.

2. Y el diálogo que salía estaba roto: los campos del servidor unos encima de
   otros y los botones pisándose. Estaba fijado a 720 px de alto con un
   contenido que, con la hoja de estilos aplicada, necesita más de 900. Sin área
   de desplazamiento, Qt no recorta: superpone. Roto desde que el diálogo recibe
   la hoja de estilos (v5.74.0); nadie lo veía porque no volvía a salir.
"""

import pytest
from PyQt6.QtWidgets import QLineEdit, QScrollArea

from presentation.dialogs.initial_config_dialog import InitialConfigDialog


def _entorno_sftp_sin_contrasena(monkeypatch):
    for clave in ("SFTP_HOST", "SFTP_PORT", "SFTP_USERNAME", "SFTP_USER", "SFTP_PASSWORD"):
        monkeypatch.delenv(clave, raising=False)
    monkeypatch.setenv("SFTP_HOST", "sftp.ejemplo.test")
    monkeypatch.setenv("SFTP_PORT", "22")
    monkeypatch.setenv("SFTP_USERNAME", "alguien")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)


def test_con_la_contrasena_en_el_llavero_no_se_pide_configuracion(monkeypatch):
    from core import credenciales

    _entorno_sftp_sin_contrasena(monkeypatch)
    credenciales.guardar("SFTP_PASSWORD", "secreta")

    assert InitialConfigDialog.is_configuration_needed() is False


def test_sin_contrasena_en_ningun_sitio_si_se_pide(monkeypatch):
    from core import credenciales

    _entorno_sftp_sin_contrasena(monkeypatch)
    credenciales.borrar("SFTP_PASSWORD")

    assert InitialConfigDialog.is_configuration_needed() is True


def test_el_nombre_antiguo_del_usuario_tambien_vale(monkeypatch):
    """Hay equipos con `SFTP_USER` en vez de `SFTP_USERNAME`."""
    from core import credenciales

    _entorno_sftp_sin_contrasena(monkeypatch)
    monkeypatch.delenv("SFTP_USERNAME")
    monkeypatch.setenv("SFTP_USER", "alguien")
    credenciales.guardar("SFTP_PASSWORD", "secreta")

    assert InitialConfigDialog.is_configuration_needed() is False


@pytest.fixture
def dialogo(qapp):
    from presentation.theme.hoja_de_estilos import construir_hoja_de_estilos

    qapp.setStyleSheet(construir_hoja_de_estilos())
    d = InitialConfigDialog()
    d.resize(700, 600)  # la pantalla mínima que promete la aplicación
    d.show()
    qapp.processEvents()
    yield d
    d.close()
    qapp.setStyleSheet("")


def test_los_campos_del_servidor_no_se_pisan(dialogo):
    campos = [w for w in dialogo.findChildren(QLineEdit) if w.isVisible()]
    rects = sorted(
        (w.mapTo(dialogo, w.rect().topLeft()).y(), w.height(), w.accessibleName())
        for w in campos
    )
    solapes = [
        (a[2], b[2]) for a, b in zip(rects, rects[1:]) if b[0] < a[0] + a[1]
    ]
    assert solapes == [], f"campos superpuestos: {solapes}"


def test_cada_pestana_se_desplaza_si_no_cabe(dialogo):
    areas = dialogo.findChildren(QScrollArea)
    assert len(areas) >= 2
    assert all(a.widgetResizable() for a in areas)


def test_el_dialogo_cabe_en_la_pantalla_minima(dialogo):
    """La aplicación promete 1024×700: el diálogo no puede exigir más alto."""
    assert dialogo.minimumHeight() <= 700
