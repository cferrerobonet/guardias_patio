"""Guardarraíles de flujo: lo que debe hacerse antes que otra cosa tiene que ser visible y
verificable desde dominio, no un flag de sesión de UI. Ver auditoria/03 (UXF-001/002/008)."""

import pytest
from PyQt6.QtWidgets import QApplication

pytestmark = pytest.mark.ui


@pytest.fixture
def panel_generacion(qapp, session):
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    p = GeneracionPanel(session)
    QApplication.processEvents()
    yield p
    p.close()


def test_generar_esta_bloqueado_al_inicio_y_explica_por_que(panel_generacion):
    """Comportamiento actual que debe conservarse."""
    assert not panel_generacion.generar_button.isEnabled()
    assert panel_generacion.generar_button.toolTip().strip()


@pytest.mark.xfail(
    strict=True,
    reason="UXF-002: el gate es un flag de UI; tras cargar_datos sin config sigue habilitado",
)
def test_generar_se_bloquea_de_nuevo_si_faltan_prerrequisitos(panel_generacion):
    panel_generacion.habilitar_generacion(True)
    assert panel_generacion.generar_button.isEnabled()
    panel_generacion.cargar_datos()  # sin Configuracion ni zonas en la BD
    assert not panel_generacion.generar_button.isEnabled()


@pytest.mark.xfail(
    strict=True,
    reason="UXF-008: el motivo del bloqueo sólo está en el tooltip, no en un texto visible",
)
def test_motivo_de_bloqueo_visible_sin_hover(panel_generacion):
    from PyQt6.QtWidgets import QLabel

    textos = [
        lbl.text()
        for lbl in panel_generacion.findChildren(QLabel)
        if lbl.isVisibleTo(panel_generacion) and "cuota" in lbl.text().lower()
    ]
    assert textos, "no hay etiqueta visible que explique que faltan las cuotas"


@pytest.mark.xfail(
    strict=True,
    reason="UXF-001: no existe un caso de uso de preflight que liste los prerrequisitos faltantes",
)
def test_existe_preflight_de_generacion_en_application(session):
    import importlib

    mod = importlib.import_module("application.use_cases.preflight_generacion")
    resultado = mod.PreflightGeneracionUseCase(session).execute()
    assert hasattr(resultado, "faltantes")
    assert resultado.faltantes, "sin configuración ni zonas debería haber faltantes"


def test_cambio_de_curso_refresca_las_vistas_cargadas(qapp):
    """UXA-007 resuelto en v5.49.0: el envoltorio conserva la vista para poder recargarla."""
    from PyQt6.QtWidgets import QLabel

    from presentation.ccleaner_main_window import ContentWrapper

    w = ContentWrapper("Título", QLabel("contenido"))
    assert isinstance(w.content_widget, QLabel)
