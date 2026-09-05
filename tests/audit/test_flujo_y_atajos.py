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


# ---------------------------------------------------------------------------
# UXF-003: menos ceremonia para generar
# ---------------------------------------------------------------------------
def test_la_primera_generacion_no_pide_confirmar_lo_obvio():
    """Sin guardias que perder no hay nada que decidir: el resumen va en la vista."""
    import inspect

    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    fuente = inspect.getsource(GeneracionPanel._generar_guardias)
    assert "Resumen de Generación" not in fuente, "sigue el modal informativo previo"
    assert "cerrar_al_terminar=True" in fuente


def test_el_cierre_automatico_es_opcional_y_por_defecto_no_actua():
    """Sólo lo pide quien pinta el resultado en su propia vista.

    El comportamiento en marcha no se puede comprobar aquí: la guarda de diálogos
    modales de la suite anula `exec()`, y sin bucle de eventos la señal de fin no
    llega a entregarse. Lo que sí se fija es el contrato.
    """
    import inspect

    from presentation.widgets.progress_indicators import ejecutar_con_progreso

    firma = inspect.signature(ejecutar_con_progreso)
    assert firma.parameters["cerrar_al_terminar"].default is False
    assert firma.parameters["cerrar_al_terminar"].kind is inspect.Parameter.KEYWORD_ONLY


def test_un_error_no_se_cierra_solo():
    """Cerrar automáticamente un error sería esconderlo."""
    import inspect

    from presentation.widgets import progress_indicators

    fuente = inspect.getsource(progress_indicators.ejecutar_con_progreso)
    posicion_cierre = fuente.index("if cerrar_al_terminar:")
    posicion_error = fuente.index("def on_error(")
    assert posicion_cierre < posicion_error, "el cierre automático debe vivir en on_finalizado"


# ---------------------------------------------------------------------------
# UXF-009: deshacer una sustitución
# ---------------------------------------------------------------------------
def _escenario_sustitucion(session):
    import datetime

    from infrastructure.database.models import Guardia, Profesor, Zona

    session.add_all(
        [
            Profesor(
                nombre_completo="Original, A",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            ),
            Profesor(
                nombre_completo="Sustituto, B",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            ),
            Zona(nombre_zona="Patio", activa=True),
        ]
    )
    session.commit()
    original, sustituto = session.query(Profesor).all()
    zona = session.query(Zona).first()
    session.add(
        Guardia(
            profesor_id=original.id,
            zona_id=zona.id,
            fecha=datetime.date(2025, 10, 1),
            turno="mañana",
            recreo=1,
        )
    )
    session.commit()
    return session.query(Guardia).first(), original, sustituto


def test_deshacer_devuelve_la_guardia_a_su_profesor(session):
    from services.gestor_ausencias import deshacer_sustitucion, reasignar_guardia

    guardia, original, sustituto = _escenario_sustitucion(session)
    reasignar_guardia(session, guardia.id, sustituto.id)
    session.refresh(guardia)
    assert guardia.profesor_id == sustituto.id

    deshacer_sustitucion(session, guardia.id)
    session.refresh(guardia)

    assert guardia.profesor_id == original.id
    assert guardia.es_sustitucion is False
    assert guardia.profesor_sustituido_id is None


def test_deshacer_queda_registrado(session):
    from infrastructure.database.models import GuardiaAuditLog
    from services.gestor_ausencias import deshacer_sustitucion, reasignar_guardia

    guardia, _original, sustituto = _escenario_sustitucion(session)
    reasignar_guardia(session, guardia.id, sustituto.id)
    deshacer_sustitucion(session, guardia.id)

    acciones = [a.accion for a in session.query(GuardiaAuditLog).all()]
    assert "SUSTITUIDA" in acciones
    assert "SUSTITUCION_DESHECHA" in acciones


def test_no_se_puede_deshacer_lo_que_no_es_sustitucion(session):
    from services.gestor_ausencias import deshacer_sustitucion

    guardia, _o, _s = _escenario_sustitucion(session)

    with pytest.raises(ValueError, match="no es una sustitución"):
        deshacer_sustitucion(session, guardia.id)


def test_el_historial_ofrece_deshacer(qapp, session):
    from presentation.widgets.ausencias_sustituciones import AusenciasSustitucionesWidget

    widget = AusenciasSustitucionesWidget(session=session)
    try:
        assert widget.btn_deshacer.accessibleName()
        assert hasattr(widget, "deshacer_seleccion")
    finally:
        widget.close()


def test_deshacer_sin_seleccionar_nada_avisa(qapp, session, monkeypatch):
    from presentation.widgets.ausencias_sustituciones import AusenciasSustitucionesWidget

    widget = AusenciasSustitucionesWidget(session=session)
    avisos = []
    monkeypatch.setattr(type(widget), "mostrar_advertencia", lambda self, t, m: avisos.append(t))
    try:
        widget.tabla_historial.setCurrentCell(-1, -1)
        widget.deshacer_seleccion()
        assert avisos, "no avisó de que no hay nada seleccionado"
    finally:
        widget.close()
