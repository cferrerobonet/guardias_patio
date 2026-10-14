"""UXA-004: los cambios sin guardar no se pierden en silencio.

La infraestructura existía en `BaseForm` (`_mark_dirty`, `tiene_cambios`…) pero
no la llamaba nadie: cambiar de sección o cerrar la aplicación descartaba el
trabajo sin avisar. Estos tests fijan la matriz de estado sucio × salida.
"""

import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit, QMessageBox, QVBoxLayout

pytestmark = pytest.mark.ui


@pytest.fixture
def formulario(qapp):
    from presentation.forms.base_form import BaseForm

    f = BaseForm(None)
    caja = QVBoxLayout(f)
    campo = QLineEdit()
    caja.addWidget(campo)
    f.vigilar_cambios()
    yield f, campo
    f.close()


# ---------------------------------------------------------------------------
# Detección
# ---------------------------------------------------------------------------
def test_un_formulario_recien_abierto_no_tiene_cambios(formulario):
    f, _ = formulario
    assert not f.tiene_cambios()


def test_rellenar_por_codigo_no_cuenta_como_edicion(formulario):
    f, campo = formulario
    campo.setText("cargado desde la base de datos")
    assert not f.tiene_cambios()


def test_editar_a_mano_si_cuenta(formulario):
    f, campo = formulario
    campo.textEdited.emit("escrito por el usuario")
    assert f.tiene_cambios()


def test_cargando_suspende_la_deteccion(formulario):
    f, campo = formulario
    with f.cargando():
        campo.textEdited.emit("volcado de un registro")
    assert not f.tiene_cambios()


def test_descartar_deja_el_formulario_limpio(formulario):
    f, campo = formulario
    campo.textEdited.emit("algo")
    f.descartar_cambios()
    assert not f.tiene_cambios()


def test_la_senal_avisa_del_cambio_de_estado(formulario):
    f, campo = formulario
    estados = []
    f.cambios_sin_guardar.connect(estados.append)

    campo.textEdited.emit("uno")
    campo.textEdited.emit("dos")  # ya estaba sucio: no repite señal
    f.descartar_cambios()

    assert estados == [True, False]


# ---------------------------------------------------------------------------
# Matriz sucio × salida × decisión
# ---------------------------------------------------------------------------
@pytest.fixture
def ventana(qapp, session):
    from presentation.ventana_principal import VentanaPrincipal

    w = VentanaPrincipal(session, sync_manager=None)
    QApplication.processEvents()
    yield w
    w.close()


def _ensuciar_la_vista_actual(ventana):
    vista = ventana.vista_actual()
    vista._mark_dirty()
    return vista


def test_sin_cambios_se_navega_sin_preguntar(ventana, monkeypatch):
    titulos = []  # texto del diálogo: macOS ignora el título de QMessageBox
    monkeypatch.setattr(
        QMessageBox, "exec", lambda self: titulos.append(self.text()) or 0
    )

    ventana.on_section_changed("zonas")
    QApplication.processEvents()

    # Otras pantallas pueden avisar de sus propias cosas al abrirse; lo que no
    # puede aparecer es el guard de cambios sin guardar.
    assert "cambios sin guardar" not in " ".join(titulos).lower(), titulos
    assert ventana._seccion_actual == "zonas"


def test_con_cambios_seguir_editando_no_navega(ventana, monkeypatch):
    _ensuciar_la_vista_actual(ventana)

    def responder(caja):
        # "Seguir editando" es el botón por defecto
        caja.setResult(0)
        caja._pulsado = caja.defaultButton()
        return 0

    monkeypatch.setattr(QMessageBox, "exec", responder)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self.defaultButton())

    ventana.on_section_changed("zonas")
    QApplication.processEvents()

    assert ventana._seccion_actual == "profesores", "navegó pese a pedir seguir editando"


def test_con_cambios_descartar_navega_y_limpia(ventana, monkeypatch):
    vista = _ensuciar_la_vista_actual(ventana)

    def pulsar_descartar(self):
        botones = [b for b in self.buttons() if "Descartar" in b.text()]
        self._elegido = botones[0]
        return 0

    monkeypatch.setattr(QMessageBox, "exec", pulsar_descartar)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._elegido)

    ventana.on_section_changed("zonas")
    QApplication.processEvents()

    assert ventana._seccion_actual == "zonas"
    assert not vista.tiene_cambios()


def test_cerrar_la_ventana_tambien_pregunta(ventana, monkeypatch):
    _ensuciar_la_vista_actual(ventana)
    preguntado = []

    def pulsar_seguir(self):
        preguntado.append(True)
        self._elegido = [b for b in self.buttons() if "Seguir" in b.text()][0]
        return 0

    monkeypatch.setattr(QMessageBox, "exec", pulsar_seguir)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._elegido)

    from PyQt6.QtGui import QCloseEvent

    evento = QCloseEvent()
    ventana.closeEvent(evento)

    assert preguntado, "cerrar con cambios pendientes no preguntó"
    assert not evento.isAccepted(), "se cerró pese a pedir seguir editando"


def test_los_formularios_editables_ofrecen_guardar_desde_el_guard(qapp, session):
    """Guardar sólo se ofrece si el formulario sabe guardarse solo."""
    from presentation.forms.base_form import BaseForm
    from presentation.forms.profesor_form import ProfesorForm
    from presentation.forms.zona_form import ZonaForm

    assert not BaseForm(session).puede_guardar_desde_el_guard()

    for clase in (ProfesorForm, ZonaForm):
        vista = clase(session)
        assert vista.puede_guardar_desde_el_guard(), clase.__name__
        vista.close()


# ---------------------------------------------------------------------------
# UXF-004: cambiar de curso con cambios pendientes
# ---------------------------------------------------------------------------
def test_cambiar_de_curso_avisa_antes_de_descartar(ventana, monkeypatch):
    """Los cambios pendientes son del curso anterior: se avisa, no se pierden mudos."""
    vista = _ensuciar_la_vista_actual(ventana)
    titulos = []  # texto del diálogo: macOS ignora el título de QMessageBox

    def pulsar_descartar(self):
        titulos.append(self.text())
        self._elegido = [b for b in self.buttons() if "Descartar" in b.text()][0]
        return 0

    monkeypatch.setattr(QMessageBox, "exec", pulsar_descartar)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._elegido)

    ventana._on_curso_cambiado(7)
    QApplication.processEvents()

    assert any("cambios sin guardar" in t.lower() for t in titulos), titulos
    assert not vista.tiene_cambios()


def test_cambiar_de_curso_sin_cambios_no_molesta(ventana, monkeypatch):
    titulos = []  # texto del diálogo: macOS ignora el título de QMessageBox
    monkeypatch.setattr(
        QMessageBox, "exec", lambda self: titulos.append(self.text()) or 0
    )

    ventana._on_curso_cambiado(7)
    QApplication.processEvents()

    assert "cambios sin guardar" not in " ".join(titulos).lower()


@pytest.mark.parametrize("nombre", ["ProfesorForm", "ZonaForm", "AjustesForm"])
def test_ningun_formulario_nace_con_cambios_pendientes(qapp, session, nombre):
    """Rellenar los campos al abrir no puede contar como edición del usuario.

    Es el falso positivo que hace inservible cualquier guard: si el formulario
    nace sucio, el aviso salta siempre y la gente aprende a ignorarlo.
    """
    from presentation.forms.ajustes_form import AjustesForm
    from presentation.forms.profesor_form import ProfesorForm
    from presentation.forms.zona_form import ZonaForm

    clase = {"ProfesorForm": ProfesorForm, "ZonaForm": ZonaForm, "AjustesForm": AjustesForm}[nombre]
    vista = clase(session)
    QApplication.processEvents()
    try:
        assert not vista.tiene_cambios()
    finally:
        vista.close()
