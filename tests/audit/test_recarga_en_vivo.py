"""La recarga de datos debe verse sin cerrar y volver a abrir la aplicación.

Una importación o una descarga sustituyen los datos por debajo. Antes las vistas
seguían mostrando lo anterior porque el envoltorio de cada vista no guardaba el
widget y las señales de importación no las escuchaba nadie.
"""

import pytest
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QLabel

from presentation.ventana_principal import VentanaPrincipal, ContentWrapper

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
    monkeypatch.setattr(VentanaPrincipal, "setup_ui", lambda self: None)
    v = VentanaPrincipal(session)
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


class _VistaQueCambia(_VistaFalsa):
    datos_modificados = pyqtSignal()

    def __init__(self, con_cambios=False):
        super().__init__()
        self._con_cambios = con_cambios

    def tiene_cambios(self):
        return self._con_cambios


def test_un_cambio_recarga_las_demas_vistas_al_volver_a_ellas(ventana):
    """Un profesor dado de alta no aparecía en Ausencias ni en Reportes (2026-10-03)."""
    origen, otra = _VistaQueCambia(), _VistaFalsa()
    ventana.widgets = {
        "profesores": ContentWrapper("Profesores", QLabel()),
        "ausencias": ContentWrapper("Ausencias", QLabel()),
    }
    ventana.widgets["profesores"].content_widget = origen
    ventana.widgets["ausencias"].content_widget = otra
    ventana._conectar_senales_de_recarga(origen, "profesores")

    origen.datos_modificados.emit()
    assert ventana._vistas_desfasadas == {"ausencias"}
    assert otra.recargas == 0, "no se recarga todo al momento, sino al volver"

    ventana._refrescar_vista("ausencias")
    assert otra.recargas == 1
    assert not ventana._vistas_desfasadas


def test_no_se_recarga_una_vista_con_cambios_sin_guardar(ventana):
    vista = _VistaQueCambia(con_cambios=True)
    ventana.widgets = {"ajustes": ContentWrapper("Ajustes", QLabel())}
    ventana.widgets["ajustes"].content_widget = vista
    ventana._vistas_desfasadas = {"ajustes"}

    ventana._refrescar_vista("ajustes")
    assert vista.recargas == 0
    assert ventana._vistas_desfasadas == {"ajustes"}


def test_se_prefiere_refrescar_a_las_cargas_parciales(ventana):
    class _Ausencias:
        def __init__(self):
            self.llamadas = []

        def cargar_profesores(self):
            self.llamadas.append("cargar_profesores")

        def refrescar(self):
            self.llamadas.append("refrescar")

    vista = _Ausencias()
    ventana._refresh_widget(vista)
    assert vista.llamadas == ["refrescar"]


def test_las_vistas_que_cambian_datos_lo_anuncian():
    from presentation.forms.ajustes_form import AjustesForm
    from presentation.forms.asignacion_calculo_form import AsignacionCalculoForm
    from presentation.forms.import_export_form import ImportExportForm

    assert hasattr(AjustesForm, "configuracion_guardada")
    assert hasattr(AjustesForm, "cursos_modificados")
    assert hasattr(AsignacionCalculoForm, "guardias_generadas")
    assert hasattr(AsignacionCalculoForm, "guardias_limpiadas")
    assert hasattr(ImportExportForm, "datos_recargados")
