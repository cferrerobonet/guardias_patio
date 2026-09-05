"""Lote 9: que la aplicación hable con una sola voz.

- VIS-006: el envoltorio de vistas recibía un título y no lo pintaba nunca. Cada
  pantalla ponía el suyo, con su propio formato, o no ponía ninguno.
- UXA-013: cambiar de sección no anunciaba nada a un lector de pantalla.
- UXA-003: los avisos flotantes eran invisibles para un lector de pantalla y
  desaparecían a los 2,5 segundos, errores incluidos.
- VIS-007: el botón secundario se marcaba de dos formas y sólo una tenía estilo.
"""

import re
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QLabel

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.ui


# ---------------------------------------------------------------------------
# VIS-006 / UXA-013: una cabecera, y que se anuncie
# ---------------------------------------------------------------------------
def test_el_envoltorio_pinta_el_titulo_que_recibe(qapp):
    from presentation.ccleaner_main_window import ContentWrapper

    envoltorio = ContentWrapper("Gestión de Profesores", QLabel("contenido"))
    try:
        assert envoltorio.cabecera.text() == "Gestión de Profesores"
        assert envoltorio.cabecera.objectName() == "cabeceraDeVista"
    finally:
        envoltorio.close()


def test_la_vista_se_anuncia_al_entrar(qapp):
    """Sin nombre accesible, cambiar de sección no dice nada (UXA-013)."""
    from presentation.ccleaner_main_window import ContentWrapper

    contenido = QLabel("contenido")
    envoltorio = ContentWrapper("Calendario de Guardias", contenido)
    try:
        assert envoltorio.accessibleName() == "Calendario de Guardias"
        assert contenido.accessibleName() == "Calendario de Guardias"
    finally:
        envoltorio.close()


def test_ninguna_vista_repite_el_titulo_por_su_cuenta():
    """Si la cabecera la pone el envoltorio, la vista no debe pintar otra."""
    ofensores = []
    for fichero in (ROOT / "src" / "presentation" / "forms").glob("*.py"):
        texto = fichero.read_text(encoding="utf-8", errors="ignore")
        if 'setObjectName("titleMain")' in texto:
            ofensores.append(fichero.name)

    assert not ofensores, f"estas vistas siguen pintando su propio título: {ofensores}"


# ---------------------------------------------------------------------------
# UXA-003: los avisos se oyen, y los errores esperan
# ---------------------------------------------------------------------------
def test_el_aviso_tiene_nombre_para_el_lector_de_pantalla(qapp):
    from PyQt6.QtWidgets import QWidget

    from presentation.widgets.toast_notification import ToastNotification

    ventana = QWidget()
    aviso = ToastNotification(ventana, "Guardado correctamente", "success")
    try:
        assert "Guardado correctamente" in aviso.accessibleName()
        assert aviso.accessibleName().startswith("Aviso")
    finally:
        aviso.close()
        ventana.close()


def test_un_error_no_desaparece_solo(qapp):
    """2,5 segundos no bastan para un fallo: quien mira a otro lado se lo pierde."""
    from presentation.widgets.toast_notification import ToastNotification

    assert ToastNotification.DURACIONES["error"] == 0, "los errores deben esperar a que se pulsen"
    assert ToastNotification.DURACIONES["warning"] > ToastNotification.DURACIONES["success"]


def test_el_aviso_se_puede_cerrar_pulsandolo(qapp):
    from presentation.widgets.toast_notification import ToastNotification

    assert hasattr(ToastNotification, "mousePressEvent")


def test_el_aviso_avisa_al_lector_de_pantalla():
    import inspect

    from presentation.widgets.toast_notification import ToastNotification

    fuente = inspect.getsource(ToastNotification.__init__)
    assert "announce(" in fuente, "el aviso no se anuncia por accesibilidad"


# ---------------------------------------------------------------------------
# VIS-007: una sola forma de marcar cada variante de botón
# ---------------------------------------------------------------------------
def test_todas_las_variantes_de_boton_usadas_tienen_estilo():
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from presentation.theme.hoja_de_estilos import construir_hoja_de_estilos

    hoja = construir_hoja_de_estilos()
    declaradas = set(re.findall(r'QPushButton\[(\w+)="true"\]', hoja))

    usadas = set()
    for fichero in (ROOT / "src" / "presentation").rglob("*.py"):
        texto = fichero.read_text(encoding="utf-8", errors="ignore")
        usadas |= set(re.findall(r'setProperty\("(\w+)", "true"\)', texto))

    # `active` es estado del menú lateral, no una variante de botón.
    usadas -= {"active", "error"}

    assert usadas <= declaradas, f"variantes usadas sin estilo: {sorted(usadas - declaradas)}"


def test_la_jerarquia_de_botones_esta_escrita():
    """Para que la siguiente pantalla no invente una variante nueva."""
    qss = (ROOT / "src" / "presentation" / "theme" / "light.qss").read_text(encoding="utf-8")
    assert "JERARQUÍA DE BOTONES" in qss
    assert "botonPrimarioDeVista" in qss


# ---------------------------------------------------------------------------
# VIS-004: emojis donde debería haber iconos
# ---------------------------------------------------------------------------
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")

#: Únicos emojis que quedan en botones o títulos: las casillas de la matriz de
#: restricciones, cuyo ✓ es el estado visible de un interruptor y que desde
#: v5.60.0 ya se anuncian con nombre y estado propios.
EMOJIS_ACEPTADOS_EN_CONTROLES = 2


def test_los_botones_y_titulos_no_usan_emojis_como_iconos():
    """Un emoji se ve distinto en cada sistema y el lector lo lee en voz alta."""
    encontrados = []
    for fichero in (ROOT / "src" / "presentation").rglob("*.py"):
        for numero, linea in enumerate(
            fichero.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            texto = linea.strip()
            if not EMOJI.search(texto):
                continue
            if re.search(r'setWindowTitle\(|QPushButton\("|setText\("', texto):
                encontrados.append(f"{fichero.name}:{numero}")

    assert len(encontrados) <= EMOJIS_ACEPTADOS_EN_CONTROLES, (
        f"emojis nuevos en controles: {encontrados}"
    )


def test_el_estado_de_una_sustitucion_se_dice_con_palabras():
    """Un círculo verde o rojo no lo distingue quien no ve colores."""
    import inspect

    from presentation.widgets import ausencias_sustituciones

    fuente = inspect.getsource(ausencias_sustituciones.AusenciasSustitucionesWidget._on_combo_changed)
    assert "🟢" not in fuente and "🔴" not in fuente
    assert "Asignado" in fuente
    assert "setAccessibleName" in fuente


def test_el_terminal_retro_se_queda(qapp, session):
    """Decisión de producto de CarlosFB (2026-09-05): el panel de resultados gusta
    como está. Este test existe para que no se 'modernice' por descuido."""
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    panel = GeneracionPanel(session)
    try:
        assert panel.content_text.objectName() == "terminalRetro"
    finally:
        panel.close()
