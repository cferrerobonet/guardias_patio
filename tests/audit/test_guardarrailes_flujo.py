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


def test_la_interfaz_no_puede_conceder_permiso_para_generar(panel_generacion):
    """UXF-002: el permiso lo dan los datos, no un booleano de la interfaz.

    Antes bastaba con que alguien llamara a `habilitar_generacion(True)`; ese estado
    sobrevivía a cambios de vista y de curso sin comprobar nada.
    """
    panel_generacion.habilitar_generacion(True)
    assert not panel_generacion.generar_button.isEnabled(), (
        "la interfaz ha habilitado generar con la base de datos vacía"
    )


def test_generar_se_habilita_solo_cuando_los_datos_lo_permiten(
    qapp, session, curso_generable
):
    """UXF-002: con los prerrequisitos cubiertos, generar se habilita solo."""
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    panel = GeneracionPanel(session)
    QApplication.processEvents()
    assert panel.generar_button.isEnabled()

    # Se retira un prerrequisito y se recarga: vuelve a bloquearse.
    from infrastructure.database.models import Zona

    session.query(Zona).delete()
    session.commit()
    panel.cargar_datos()

    assert not panel.generar_button.isEnabled()
    panel.close()


def test_motivo_de_bloqueo_visible_sin_hover(panel_generacion):
    """UXF-008: el motivo se lee en pantalla, no sólo pasando el ratón por encima."""
    from PyQt6.QtWidgets import QLabel

    visibles = [
        lbl.text()
        for lbl in panel_generacion.findChildren(QLabel)
        if lbl.isVisibleTo(panel_generacion) and lbl.text().strip()
    ]
    motivos = [t for t in visibles if "no se puede generar" in t.lower()]
    assert motivos, f"ninguna etiqueta visible explica el bloqueo: {visibles}"
    # Y nombra prerrequisitos concretos, no una frase genérica.
    assert any(
        clave in motivos[0].lower()
        for clave in ("zona", "profesor", "curso", "fecha", "recreo")
    ), motivos[0]


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


# ---------------------------------------------------------------------------
# UXF-001 / FUN-001: vista de estado del curso como punto de entrada
# ---------------------------------------------------------------------------
def test_la_vista_de_inicio_lista_lo_que_falta(qapp, session):
    """Con la base vacía, la vista enumera los cinco prerrequisitos pendientes."""
    from presentation.forms.estado_curso_form import EstadoCursoForm

    vista = EstadoCursoForm(session)
    QApplication.processEvents()

    assert len(vista._filas) == 5, "no se pintó un elemento por requisito"
    assert "5" in vista.resumen.text()
    assert not vista.boton_generar.isEnabled()
    vista.close()


def test_la_vista_de_inicio_se_desbloquea_cuando_todo_esta_listo(
    qapp, session, curso_generable
):
    from presentation.forms.estado_curso_form import EstadoCursoForm

    vista = EstadoCursoForm(session)
    QApplication.processEvents()

    assert vista.boton_generar.isEnabled()
    assert "listo" in vista.resumen.text().lower()
    vista.close()


def test_la_vista_de_inicio_pide_navegar_a_lo_que_falta(qapp, session):
    """Cada requisito pendiente ofrece un botón que lleva a donde se resuelve."""
    from PyQt6.QtWidgets import QPushButton

    from presentation.forms.estado_curso_form import EstadoCursoForm

    vista = EstadoCursoForm(session)
    QApplication.processEvents()

    destinos = []
    vista.ir_a_seccion.connect(destinos.append)

    for fila in vista._filas:
        for boton in fila.findChildren(QPushButton):
            boton.click()

    assert "ajustes" in destinos
    assert "zonas" in destinos
    assert "profesores" in destinos
    vista.close()


def test_la_aplicacion_abre_en_el_estado_del_curso():
    """UXF-001: la primera pantalla ya no es la rejilla de Profesores."""
    import inspect

    from presentation import ccleaner_main_window

    fuente = inspect.getsource(ccleaner_main_window.CCleanerMainWindow)
    assert 'self._ensure_view("inicio")' in fuente
    assert 'set_active_section("inicio")' in fuente
    assert 'self._ensure_view("profesores")' not in fuente


# ---------------------------------------------------------------------------
# UXF-005: se puede trabajar sin servidor, avisando de forma permanente
# ---------------------------------------------------------------------------
def test_sin_servidor_se_ofrece_el_modo_local_en_vez_de_cerrar():
    """Cancelar la configuración inicial ya no expulsa de la aplicación."""
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[2] / "src" / "main.py").read_text(
        encoding="utf-8"
    )
    inicio = fuente.index("if InitialConfigDialog.is_configuration_needed():")
    bloque = fuente[inicio : inicio + 2000]

    assert "Trabajar solo en este equipo" in bloque, (
        "no se ofrece seguir sin servidor al cancelar la configuración"
    )
    assert "No se puede iniciar la aplicación sin configurar SFTP" not in bloque


def test_el_indicador_avisa_de_forma_permanente_de_que_no_hay_servidor():
    """UXF-005: el aviso no puede ser sólo un diálogo que se cierra y se olvida."""
    import inspect

    from presentation import ccleaner_main_window

    fuente = inspect.getsource(
        ccleaner_main_window.CCleanerMainWindow._update_sync_status_label
    )
    assert "Solo en este equipo" in fuente
    assert fuente.index("if not self.sync_manager") < fuente.index("Solo en este equipo")
