"""SYNC-014: la sincronización automática sólo sube, y cuando no puede, se nota.

Cada 30 minutos la aplicación sube los datos. Si otro equipo ha publicado algo
entretanto, la subida se rechaza —correctamente, para no pisar su trabajo— pero
hasta v5.69.0 eso sólo quedaba en el registro y en un «✕ Error de sync» diminuto
del menú lateral: se podía seguir trabajando horas sin saber que nada salía del
equipo.

La descarga en mitad de la sesión sigue descartada a propósito: cambiaría los
datos bajo las vistas abiertas. El modelo acordado es «uno cada vez», y la copia
buena se trae al arrancar.
"""

import pytest
from PyQt6.QtWidgets import QMessageBox

pytestmark = pytest.mark.ui


class _SyncFalso:
    def __init__(self, motivo=None):
        self.motivo_ultimo_fallo = motivo

    def get_last_sync_time(self):
        return None


@pytest.fixture
def ventana(qapp, session):
    from presentation.ventana_principal import VentanaPrincipal

    v = VentanaPrincipal(session, sync_manager=None)
    yield v
    v.close()


def _capturar_avisos(monkeypatch):
    avisos = []
    monkeypatch.setattr(QMessageBox, "exec", lambda self: avisos.append(self.text()) or 0)
    return avisos


def test_si_la_nube_cambio_se_explica_al_usuario(ventana, monkeypatch):
    avisos = _capturar_avisos(monkeypatch)
    ventana.sync_manager = _SyncFalso("El servidor tiene la versión 7 y esta sesión partió de la 5.")

    ventana._on_auto_sync_finished(False)

    assert avisos, "no se avisó de que los cambios no se están subiendo"
    assert "nube ha cambiado" in avisos[0].lower()


def test_el_aviso_no_se_repite_cada_media_hora(ventana, monkeypatch):
    """Un aviso cada 30 minutos se convierte en ruido que se cierra sin leer."""
    avisos = _capturar_avisos(monkeypatch)
    ventana.sync_manager = _SyncFalso("conflicto de versiones")

    ventana._on_auto_sync_finished(False)
    ventana._on_auto_sync_finished(False)
    ventana._on_auto_sync_finished(False)

    assert len(avisos) == 1


def test_un_fallo_puntual_de_red_no_interrumpe(ventana, monkeypatch):
    """Sin motivo registrado es un corte pasajero: basta el indicador lateral."""
    avisos = _capturar_avisos(monkeypatch)
    ventana.sync_manager = _SyncFalso(None)

    ventana._on_auto_sync_finished(False)

    assert not avisos


def test_el_indicador_lateral_distingue_los_dos_casos(ventana):
    ventana.sync_manager = _SyncFalso("conflicto de versiones")
    ventana._update_sync_status_label(error=True)
    assert "nube cambió" in ventana.sidebar.sync_status_label.text()

    ventana.sync_manager = _SyncFalso(None)
    ventana._update_sync_status_label(error=True)
    assert ventana.sidebar.sync_status_label.text() == "✕ Error de sync"


def test_el_gestor_recuerda_por_que_no_pudo_subir():
    """El motivo tiene que salir del gestor, no reconstruirse en la interfaz."""
    import inspect

    from sync import sync_manager

    fuente = inspect.getsource(sync_manager.SyncManager.sync_on_shutdown)
    assert "self.motivo_ultimo_fallo = motivo" in fuente
    # Y se limpia cuando la subida sí funciona, o el aviso se quedaría pegado.
    assert "self.motivo_ultimo_fallo = None" in fuente
