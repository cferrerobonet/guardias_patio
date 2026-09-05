"""La recarga de datos debe verse sin cerrar y volver a abrir la aplicación.

Una importación o una descarga sustituyen los datos por debajo. Antes las vistas
seguían mostrando lo anterior porque el envoltorio de cada vista no guardaba el
widget y las señales de importación no las escuchaba nadie.
"""

import pytest
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QLabel

from presentation.ccleaner_main_window import CCleanerMainWindow, ContentWrapper

pytestmark = pytest.mark.ui


def test_el_envoltorio_conserva_la_vista(qapp):
    """Sin esto ningún refresco llega a su destino."""
    etiqueta = QLabel("contenido")
    envoltorio = ContentWrapper("Título", etiqueta)
    assert envoltorio.content_widget is etiqueta


class _VistaFalsa(QObject):
    """Una vista que sabe recargarse y que avisa cuando importa datos."""

    profesores_importados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.recargas = 0

    def cargar_datos(self):
        self.recargas += 1


@pytest.fixture
def ventana(qapp, session, monkeypatch):
    monkeypatch.setattr(CCleanerMainWindow, "setup_ui", lambda self: None)
    v = CCleanerMainWindow(session)
    v.widgets = {}
    v._view_factories = {}
    yield v


def test_recargar_repinta_todas_las_vistas_abiertas(ventana):
    primera, segunda = _VistaFalsa(), _VistaFalsa()
    ventana.widgets = {
        "profesores": ContentWrapper("Profesores", QLabel()),
        "zonas": ContentWrapper("Zonas", QLabel()),
    }
    ventana.widgets["profesores"].content_widget = primera
    ventana.widgets["zonas"].content_widget = segunda

    ventana.recargar_todas_las_vistas("prueba")

    assert primera.recargas == 1
    assert segunda.recargas == 1


def test_una_importacion_dispara_la_recarga(ventana):
    importador = _VistaFalsa()
    otra = _VistaFalsa()
    ventana.widgets = {"otra": ContentWrapper("Otra", QLabel())}
    ventana.widgets["otra"].content_widget = otra

    ventana._conectar_senales_de_recarga(importador)
    importador.profesores_importados.emit()

    assert otra.recargas == 1, "importar debe repintar las demás vistas, sin reiniciar"


def test_una_vista_rota_no_impide_recargar_el_resto(ventana):
    class _Rota:
        def cargar_datos(self):
            raise RuntimeError("vista defectuosa")

    sana = _VistaFalsa()
    ventana.widgets = {
        "rota": ContentWrapper("Rota", QLabel()),
        "sana": ContentWrapper("Sana", QLabel()),
    }
    ventana.widgets["rota"].content_widget = _Rota()
    ventana.widgets["sana"].content_widget = sana

    ventana.recargar_todas_las_vistas("prueba")

    assert sana.recargas == 1
