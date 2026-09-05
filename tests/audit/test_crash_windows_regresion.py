"""Regresión de los hallazgos CRW (cierre de la app en Windows al terminar el cálculo).

Los tests marcados xfail(strict=True) describen el comportamiento objetivo. Cuando el fix
llegue pasarán, `strict` los convertirá en fallo y habrá que retirar la marca en el mismo commit.
Ver auditoria/06_CRASH_WINDOWS_GENERACION.md.
"""

import inspect
import logging
import re
import threading
import time
from unittest import mock
from pathlib import Path

import pytest
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.ui


# ---------------------------------------------------------------------------
# CRW-002: el handler de logging no debe tocar widgets fuera del hilo GUI
# ---------------------------------------------------------------------------
def test_log_handler_no_toca_widgets_fuera_del_hilo_gui(qapp, qtbot, monkeypatch):
    from presentation.widgets.progress_indicators import ProgressDialog

    dialog = ProgressDialog(None, "t", "m", cancelable=True, show_details=True)
    qtbot.addWidget(dialog)
    hilos_llamada = []
    original = ProgressDialog.agregar_al_log

    def espia(self, mensaje):
        hilos_llamada.append(QThread.currentThread())
        return original(self, mensaje)

    monkeypatch.setattr(ProgressDialog, "agregar_al_log", espia)
    logger = logging.getLogger("services.asignador_guardias_cpsat")

    def trabajo():
        logger.info("Generando guardias desde un hilo secundario")

    t = threading.Thread(target=trabajo)
    t.start()
    t.join(timeout=5)
    qapp.processEvents()

    assert hilos_llamada, "el handler no capturó el mensaje"
    gui = QApplication.instance().thread()
    assert all(h is gui for h in hilos_llamada), "agregar_al_log se ejecutó fuera del hilo GUI"
    dialog._cancelado = True
    dialog.close()


def test_log_handler_captura_los_loggers_de_los_algoritmos_actuales(qapp, qtbot):
    """CRW-002 (parte 2): los loggers instalados deben ser los de los algoritmos que existen."""
    from presentation.widgets.progress_indicators import ProgressDialog

    dialog = ProgressDialog(None, "t", "m", cancelable=True, show_details=True)
    qtbot.addWidget(dialog)
    handler = dialog._log_handler
    capturados = {
        name
        for name in ("services.asignador_guardias_cpsat", "services.asignador_guardias_v4_hibrido")
        if handler in logging.getLogger(name).handlers
    }
    dialog._cancelado = True
    dialog.close()
    assert capturados == {
        "services.asignador_guardias_cpsat",
        "services.asignador_guardias_v4_hibrido",
    }, f"el handler no cubre los algoritmos vivos: {capturados}"


# ---------------------------------------------------------------------------
# CRW-001: los callbacks del solver no deben ejecutarse fuera del hilo que lanzó el solve
# ---------------------------------------------------------------------------
def test_callbacks_del_solver_no_salen_del_hilo_llamante(session, configuracion_basica):
    from services.asignador_guardias_cpsat import generar_guardias_cpsat

    hilos = set()

    def cb(porcentaje, mensaje=""):
        hilos.add(threading.get_ident())

    generar_guardias_cpsat(session, cb, timeout_seconds=15)
    assert hilos, "el solver no informó de progreso"
    assert hilos == {threading.get_ident()}, (
        "el callback de progreso se ejecutó en hilos ajenos: la GUI recibe señales desde OR-Tools"
    )


def test_services_no_importa_qt():
    """Frontera solver↔Qt: ningún módulo de services/application/domain importa PyQt6."""
    ofensores = []
    for capa in ("services", "application", "domain"):
        for f in (ROOT / "src" / capa).rglob("*.py"):
            if "PyQt6" in f.read_text(encoding="utf-8", errors="ignore"):
                ofensores.append(str(f.relative_to(ROOT)))
    assert not ofensores, ofensores


# ---------------------------------------------------------------------------
# CRW-004: cancelar no debe tragarse ni lanzar a través de C++
# ---------------------------------------------------------------------------
def test_cancelacion_interrumpe_la_generacion_sin_tragarse_la_excepcion(
    session, configuracion_basica, caplog
):
    from services.asignador_guardias_cpsat import generar_guardias_cpsat

    def cb_cancela(porcentaje, mensaje=""):
        raise InterruptedError("Operación cancelada por el usuario")

    with caplog.at_level(logging.WARNING, logger="services.asignador_guardias_cpsat"):
        with pytest.raises(InterruptedError):
            generar_guardias_cpsat(session, cb_cancela, timeout_seconds=15)
    tragadas = [r for r in caplog.records if "Error en callback de progreso" in r.getMessage()]
    assert not tragadas, (
        f"la cancelación se tragó {len(tragadas)} veces antes de propagarse; "
        "debe detener la generación en la primera fase"
    )


def test_worker_no_lanza_dentro_del_callback_del_solver():
    """CRW-004: la cancelación debe propagarse por bandera, no por excepción en el callback."""
    from presentation.widgets import progress_worker

    fuente = inspect.getsource(progress_worker.WorkerThread.run)
    assert "raise InterruptedError" not in fuente, (
        "CRW-004: callback_progreso no debe lanzar (llegaría al callback C++ de CP-SAT); "
        "la cancelación viaja por el evento WorkerThread.cancelacion"
    )


def test_resolver_con_progreso_para_el_solver_al_cancelar():
    """CRW-004: cancelar llama a stop_search() y corta el solve en menos de 2 s."""
    from services._asignador_cpsat_helpers import ProgresoSolver, resolver_con_progreso

    cancelacion = threading.Event()
    parado = threading.Event()

    class SolverFalso:
        def Solve(self, model, callback):  # noqa: N802 - imita la API de OR-Tools
            for _ in range(400):  # ~8 s si nadie lo detiene
                if parado.is_set():
                    return "PARADO"
                time.sleep(0.02)
            return "COMPLETO"

        def stop_search(self):
            parado.set()

    progreso = ProgresoSolver()
    hilos_reportar = []

    def reportar(porcentaje, mensaje=""):
        hilos_reportar.append(threading.get_ident())

    threading.Timer(0.2, cancelacion.set).start()
    inicio = time.monotonic()
    status = resolver_con_progreso(SolverFalso(), None, None, progreso, reportar, cancelacion)
    tardanza = time.monotonic() - inicio

    assert status == "PARADO", "el solver siguió trabajando tras la cancelación"
    assert tardanza < 2, f"la cancelación tardó {tardanza:.1f} s en detener el solve"
    assert all(h == threading.get_ident() for h in hilos_reportar), (
        "reportar se ejecutó fuera del hilo llamante"
    )


def test_progreso_publicado_por_el_solver_lo_reporta_el_hilo_llamante():
    """CRW-001: lo que publican los hilos de OR-Tools sale por el hilo llamante."""
    from services._asignador_cpsat_helpers import ProgresoSolver, resolver_con_progreso

    progreso = ProgresoSolver()
    avisos = []

    class SolverFalso:
        def Solve(self, model, callback):  # noqa: N802
            # Publica desde un hilo ajeno, como hacen los workers del solver.
            hilo = threading.Thread(target=lambda: progreso.publicar(42, "Solución 1"))
            hilo.start()
            hilo.join()
            time.sleep(0.4)
            return "COMPLETO"

        def stop_search(self):
            pass

    def reportar(porcentaje, mensaje=""):
        avisos.append((porcentaje, mensaje, threading.get_ident()))

    resolver_con_progreso(SolverFalso(), None, None, progreso, reportar)

    assert avisos, "el progreso publicado por el solver no llegó a reportarse"
    assert all(a[2] == threading.get_ident() for a in avisos)


def test_worker_pasa_el_evento_de_cancelacion_a_la_tarea(qapp, qtbot):
    """CRW-004: la tarea que declara `cancelacion` recibe el evento del worker."""
    from presentation.widgets.progress_worker import WorkerThread

    recibido = {}

    def tarea(progress_callback, cancelacion=None):
        recibido["evento"] = cancelacion
        return "ok"

    worker = WorkerThread(tarea)
    with qtbot.waitSignal(worker.finalizado, timeout=5000):
        worker.start()
    worker.wait()

    assert recibido["evento"] is worker.cancelacion


def test_worker_cancelado_avisa_con_interrupted_error(qapp, qtbot):
    """CRW-004: cancelar sigue terminando en InterruptedError, pero sin lanzar en el callback."""
    from presentation.widgets.progress_worker import WorkerThread

    def tarea(progress_callback, cancelacion=None):
        cancelacion.wait(timeout=5)
        return "ok"

    worker = WorkerThread(tarea)
    with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
        worker.start()
        worker.cancelar()
    worker.wait()

    assert isinstance(blocker.args[0], InterruptedError)


# ---------------------------------------------------------------------------
# CRW-005: excepthook y SyncWorker seguros en hilos
# ---------------------------------------------------------------------------
def test_excepthook_comprueba_el_hilo_antes_de_crear_widgets():
    fuente = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    inicio = fuente.index("def exception_hook")
    fin = fuente.index("sys.excepthook = exception_hook")
    cuerpo = fuente[inicio:fin]
    assert "currentThread" in cuerpo or ".thread()" in cuerpo
    # Y la comprobación debe ir ANTES de construir el widget, no después.
    assert cuerpo.index("currentThread") < cuerpo.index("QMessageBox()"), (
        "el QMessageBox se construye antes de comprobar el hilo"
    )


def test_syncworker_captura_cualquier_excepcion():
    from presentation.widgets.sync_progress_dialog import SyncWorker

    fuente = inspect.getsource(SyncWorker.run)
    assert "except Exception" in fuente


# ---------------------------------------------------------------------------
# CRW-006: faulthandler en builds congelados
# ---------------------------------------------------------------------------
def test_main_activa_faulthandler():
    """CRW-006 resuelto en v5.44.0: sin esto un fallo nativo no deja ninguna traza."""
    fuente = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    assert "faulthandler.enable(" in fuente
    assert "sys.stdout is not None" in fuente, (
        "en un build windowed sys.stdout es None: no debe crearse StreamHandler"
    )


# ---------------------------------------------------------------------------
# CRW-009: el caso de uso de generación gestiona su transacción
# ---------------------------------------------------------------------------
def test_generar_guardias_hace_commit_del_audit_log():
    from application.use_cases.asignacion_guardias import generar_guardias

    fuente = inspect.getsource(generar_guardias.GenerarGuardiasUseCase.execute)
    assert "self.session.commit()" in fuente


def test_sincronizar_del_panel_no_bloquea_el_hilo_gui():
    """CRW-007: la sync posterior a generar corre en SyncWorker, no en el hilo GUI."""
    from presentation.forms.asignacion_widgets import generacion_panel

    fuente = inspect.getsource(generacion_panel.GeneracionPanel._sincronizar)
    assert "SyncWorker" in fuente, "la sincronización sigue ejecutándose en el hilo GUI"
    assert "sync_on_shutdown" not in fuente, (
        "sync_on_shutdown llamado directamente: vuelve a bloquear la interfaz"
    )
    assert "except Exception" in fuente, (
        "sólo captura ValueError/TypeError/OSError: un fallo de paramiko escaparía del slot"
    )


def test_generar_guardias_deja_pasar_la_cancelacion():
    """La cancelación no debe disfrazarse de BusinessLogicError (si no, sale un error feo)."""
    from application.use_cases.asignacion_guardias import generar_guardias

    fuente = inspect.getsource(generar_guardias.GenerarGuardiasUseCase.execute)
    assert "except InterruptedError" in fuente
    assert fuente.index("except InterruptedError") < fuente.index("except Exception"), (
        "InterruptedError debe capturarse antes que Exception"
    )


# ---------------------------------------------------------------------------
# CRW-003: cada hilo con su propia sesión de base de datos
# ---------------------------------------------------------------------------
def test_worker_no_reutiliza_sesion_gui(qapp, session, configuracion_basica):
    """El worker de generación trabaja sobre una sesión propia, no la de la GUI."""
    from contextlib import contextmanager

    from presentation.forms.asignacion_calculo_form import AsignacionCalculoForm

    sesion_del_worker = object()

    @contextmanager
    def factory():
        yield sesion_del_worker

    form = AsignacionCalculoForm(session, session_factory=factory)
    panel = form.generacion_panel
    sesiones_recibidas = []

    def ejecutar_sincrono(parent, funcion, *args, **kwargs):
        return funcion(lambda *a, **k: None)

    class UseCaseEspia:
        def __init__(self, sesion):
            sesiones_recibidas.append(sesion)

        def execute(self, **kwargs):
            return None

    with mock.patch(
        "presentation.forms.asignacion_widgets.generacion_panel.GenerarGuardiasUseCase",
        UseCaseEspia,
    ):
        with mock.patch(
            "presentation.widgets.progress_indicators.ejecutar_con_progreso",
            ejecutar_sincrono,
        ):
            panel._generar_guardias()

    form.close()

    assert sesiones_recibidas, "la tarea de generación no llegó a ejecutarse"
    assert sesiones_recibidas[0] is sesion_del_worker
    assert sesiones_recibidas[0] is not session, (
        "el worker de generación está usando la sesión del hilo GUI"
    )


def test_ningun_syncworker_recibe_la_sesion_de_la_gui():
    """CRW-003: ninguna llamada a SyncWorker le pasa la sesión de la GUI."""
    ofensores = []
    for f in (ROOT / "src").rglob("*.py"):
        texto = f.read_text(encoding="utf-8", errors="ignore")
        for llamada in re.finditer(r"SyncWorker\(([^)]*)\)", texto):
            if "session" in llamada.group(1):
                ofensores.append(f"{f.relative_to(ROOT)}: {llamada.group(0)}")
    assert not ofensores, ofensores


def test_syncworker_abre_su_propia_sesion(qapp):
    """SyncWorker usa la sesión que abre él, no una recibida desde fuera."""
    from contextlib import contextmanager

    from presentation.widgets.sync_progress_dialog import SyncWorker

    sesion_propia = object()
    recibidas = []

    @contextmanager
    def factory():
        yield sesion_propia

    class SyncManagerFalso:
        def sync_on_shutdown(self, session=None, progress_callback=None):
            recibidas.append(session)
            return True

    worker = SyncWorker(SyncManagerFalso(), session_factory=factory)
    worker.run()  # sin start(): interesa el cuerpo, no el hilo

    assert recibidas == [sesion_propia]


def test_dos_sesiones_sobre_la_misma_bd_en_fichero(db_fichero):
    """La sesión de la GUI y la del worker conviven sobre el mismo fichero SQLite.

    Es el escenario real de CRW-003 al revés: ya no comparten sesión, así que lo
    que hay que demostrar es que dos conexiones simultáneas al mismo fichero (con
    journal DELETE, como en producción) no se bloquean entre sí.
    """
    from sqlalchemy.orm import sessionmaker

    from infrastructure.database.models import Profesor

    factory = sessionmaker(bind=db_fichero, autoflush=False, expire_on_commit=False)

    sesion_gui = factory()
    sesion_gui.query(Profesor).all()  # la GUI deja su conexión viva, como en la app

    errores = []

    def escribe_desde_otro_hilo():
        try:
            sesion_worker = factory()
            try:
                sesion_worker.add(
                    Profesor(
                        nombre_completo="Worker, Test",
                        horas_contrato=25.0,
                        porcentaje_jornada=100.0,
                        turno="mañana",
                        tutor=False,
                        activo=True,
                    )
                )
                sesion_worker.commit()
            finally:
                sesion_worker.close()
        except Exception as e:  # noqa: BLE001
            errores.append(e)

    hilo = threading.Thread(target=escribe_desde_otro_hilo)
    hilo.start()
    hilo.join(timeout=40)

    assert not hilo.is_alive(), "el worker se quedó esperando el bloqueo de SQLite"
    assert not errores, f"escribir desde otro hilo falló: {errores}"

    # Y la GUI ve lo escrito en cuanto caduca su mapa de identidad.
    sesion_gui.expire_all()
    assert sesion_gui.query(Profesor).count() == 1
    sesion_gui.close()


def test_ninguna_tarea_en_hilo_usa_la_sesion_de_la_gui():
    """CRW-003: las funciones que `ejecutar_con_progreso` corre en el WorkerThread
    no pueden tocar `self.session`, que pertenece al hilo GUI.

    Es el guardarraíl del hallazgo: sin él vuelve a colarse en la próxima vista que
    exporte o importe algo con barra de progreso.
    """
    import ast

    ofensores = []
    for fichero in (ROOT / "src" / "presentation").rglob("*.py"):
        arbol = ast.parse(fichero.read_text(encoding="utf-8", errors="ignore"))

        # Nombres de las funciones que se pasan a ejecutar_con_progreso
        lanzadas = set()
        for nodo in ast.walk(arbol):
            if (
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Name)
                and nodo.func.id == "ejecutar_con_progreso"
                and len(nodo.args) >= 2
                and isinstance(nodo.args[1], ast.Name)
            ):
                lanzadas.add(nodo.args[1].id)

        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.FunctionDef) or nodo.name not in lanzadas:
                continue
            for hijo in ast.walk(nodo):
                if (
                    isinstance(hijo, ast.Attribute)
                    and hijo.attr == "session"
                    and isinstance(hijo.value, ast.Name)
                    and hijo.value.id == "self"
                ):
                    ofensores.append(
                        f"{fichero.relative_to(ROOT)}:{hijo.lineno} en {nodo.name}()"
                    )

    assert not ofensores, (
        "estas tareas corren en otro hilo y usan la sesión de la GUI: " + str(ofensores)
    )
