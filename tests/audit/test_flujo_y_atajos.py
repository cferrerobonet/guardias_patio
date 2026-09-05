"""Lote 10: lo que se nota al usar la aplicación a diario.

- UXF-010: cinco exportaciones de PDF, cada una abriendo el diálogo en el
  directorio por omisión. En septiembre, exportando calendarios seguidos, había
  que rebuscar la misma carpeta cada vez.
- UXF-006: «Limpiar Guardias» tenía el mismo tamaño y peso que «Generar», siendo
  una acción destructiva.
- UXF-011: el único atajo global era Ctrl+B, para plegar el menú.
"""

import pytest
from PyQt6.QtWidgets import QPushButton

pytestmark = pytest.mark.ui


# ---------------------------------------------------------------------------
# UXF-010: recordar la carpeta
# ---------------------------------------------------------------------------
@pytest.fixture
def ajustes_limpios(monkeypatch, tmp_path):
    """QSettings en un fichero temporal, para no tocar los del equipo."""
    from PyQt6.QtCore import QSettings

    fichero = tmp_path / "ajustes.ini"
    monkeypatch.setattr(
        "utils.ui_helpers.QSettings",
        lambda *_a, **_k: QSettings(str(fichero), QSettings.Format.IniFormat),
        raising=False,
    )
    return fichero


def test_al_principio_no_hay_carpeta_recordada(qapp, monkeypatch, tmp_path):
    from PyQt6.QtCore import QSettings

    import utils.ui_helpers as helpers

    monkeypatch.setattr(
        helpers, "QSettings", lambda *_a, **_k: QSettings(str(tmp_path / "x.ini"), QSettings.Format.IniFormat), raising=False
    )
    assert helpers.ultima_carpeta("prueba-sin-usar") == ""


def test_se_recuerda_la_carpeta_elegida(qapp, tmp_path):
    from utils.ui_helpers import recordar_carpeta, ultima_carpeta

    destino = tmp_path / "PDFs"
    destino.mkdir()

    recordar_carpeta(str(destino), clave="prueba-carpetas")

    assert ultima_carpeta("prueba-carpetas") == str(destino)


def test_de_un_fichero_se_recuerda_su_carpeta(qapp, tmp_path):
    """Los diálogos de guardar devuelven la ruta del fichero, no la carpeta."""
    from utils.ui_helpers import recordar_carpeta, ultima_carpeta

    fichero = tmp_path / "calendario.ics"
    fichero.write_text("x")

    recordar_carpeta(str(fichero), clave="prueba-fichero")

    assert ultima_carpeta("prueba-fichero") == str(tmp_path)


def test_una_carpeta_que_ya_no_existe_no_se_propone(qapp, tmp_path):
    """Un pendrive desconectado no puede dejar el diálogo apuntando a la nada."""
    from utils.ui_helpers import recordar_carpeta, ultima_carpeta

    desaparecida = tmp_path / "usb"
    desaparecida.mkdir()
    recordar_carpeta(str(desaparecida), clave="prueba-borrada")
    desaparecida.rmdir()

    assert ultima_carpeta("prueba-borrada") == ""


def test_las_exportaciones_usan_la_carpeta_recordada():
    """Ningún diálogo de exportación puede volver a abrir en el directorio por omisión."""
    import inspect

    from presentation.forms import reportes_form
    from presentation.forms.reportes_widgets import informes_estadisticos_widget

    for modulo in (reportes_form, informes_estadisticos_widget):
        fuente = inspect.getsource(modulo)
        assert 'getExistingDirectory(\n            self, "Seleccionar' not in fuente
        assert "pedir_carpeta" in fuente, f"{modulo.__name__} no recuerda la carpeta"


# ---------------------------------------------------------------------------
# UXF-006: la acción destructiva no puede pesar lo mismo que la principal
# ---------------------------------------------------------------------------
def test_generar_pesa_mas_que_limpiar(qapp, session):
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    panel = GeneracionPanel(session)
    try:
        assert panel.generar_button.objectName() == "botonPrimarioDeVista"
        assert panel.limpiar_button.property("danger") == "true"
        assert panel.limpiar_button.minimumHeight() < panel.generar_button.minimumHeight()
        assert panel.limpiar_button.toolTip(), "la acción destructiva no avisa de lo que hace"
    finally:
        panel.close()


# ---------------------------------------------------------------------------
# UXF-011: moverse sin ratón
# ---------------------------------------------------------------------------
def test_cada_seccion_tiene_su_atajo(qapp, session):
    from presentation.ccleaner_main_window import CCleanerMainWindow

    ventana = CCleanerMainWindow(session, sync_manager=None)
    try:
        secciones_con_atajo = {s for _, s in ventana.ATAJOS_DE_SECCION}
        secciones_del_menu = {
            b.property("section")
            for b in ventana.sidebar.findChildren(QPushButton)
            if b.property("section")
        }
        assert secciones_del_menu <= secciones_con_atajo, (
            f"sin atajo: {secciones_del_menu - secciones_con_atajo}"
        )
    finally:
        ventana.close()


def test_el_atajo_navega_de_verdad(qapp, session):
    from presentation.ccleaner_main_window import CCleanerMainWindow

    ventana = CCleanerMainWindow(session, sync_manager=None)
    try:
        ventana._navegar_con_atajo("zonas")
        assert ventana._seccion_actual == "zonas"
    finally:
        ventana.close()


def test_el_atajo_se_anuncia_en_el_boton(qapp, session):
    """Un atajo que no se ve no lo usa nadie."""
    from presentation.ccleaner_main_window import CCleanerMainWindow

    ventana = CCleanerMainWindow(session, sync_manager=None)
    try:
        botones = {
            b.property("section"): b
            for b in ventana.sidebar.findChildren(QPushButton)
            if b.property("section")
        }
        for combinacion, seccion in ventana.ATAJOS_DE_SECCION:
            boton = botones.get(seccion)
            if boton is None:
                continue
            assert combinacion in boton.toolTip(), f"{seccion} no anuncia su atajo"
            assert boton.accessibleName(), f"{seccion} sin nombre accesible"
    finally:
        ventana.close()
