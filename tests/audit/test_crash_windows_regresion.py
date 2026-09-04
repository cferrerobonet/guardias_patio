"""Regresión de los hallazgos CRW (cierre de la app en Windows al terminar el cálculo).

Los tests marcados xfail(strict=True) describen el comportamiento objetivo. Cuando el fix
llegue pasarán, `strict` los convertirá en fallo y habrá que retirar la marca en el mismo commit.
Ver auditoria/06_CRASH_WINDOWS_GENERACION.md.
"""

import inspect
import logging
import threading
from pathlib import Path

import pytest
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.ui


# ---------------------------------------------------------------------------
# CRW-002: el handler de logging no debe tocar widgets fuera del hilo GUI
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="CRW-002: ProgressLogHandler.emit llama a agregar_al_log en el hilo que loguea",
)
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
    logger = logging.getLogger("services.orquestador_asignacion_guardias")

    def trabajo():
        logger.info("Generando guardias desde un hilo secundario")

    t = threading.Thread(target=trabajo)
    t.start()
    t.join(timeout=5)
    qapp.processEvents()

    assert hilos_llamada, "el handler no capturó el mensaje (loggers obsoletos)"
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
    if not capturados:
        pytest.xfail("CRW-002: el handler sólo se instala en loggers de módulos inexistentes")


# ---------------------------------------------------------------------------
# CRW-001: los callbacks del solver no deben ejecutarse fuera del hilo que lanzó el solve
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=False,
    reason="CRW-001: on_solution_callback se invoca desde los hilos de OR-Tools y emite señales Qt",
)
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
@pytest.mark.xfail(
    strict=True,
    reason="CRW-004: reportar() captura OSError (InterruptedError) en las fases y sigue generando",
)
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
    if "raise InterruptedError" in fuente:
        pytest.xfail(
            "CRW-004: callback_progreso lanza InterruptedError (llega al callback C++ de CP-SAT)"
        )


# ---------------------------------------------------------------------------
# CRW-005: excepthook y SyncWorker seguros en hilos
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True, reason="CRW-005: exception_hook crea QMessageBox sin comprobar el hilo"
)
def test_excepthook_comprueba_el_hilo_antes_de_crear_widgets():
    fuente = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    inicio = fuente.index("def exception_hook")
    fin = fuente.index("sys.excepthook = exception_hook")
    cuerpo = fuente[inicio:fin]
    assert "currentThread" in cuerpo or ".thread()" in cuerpo


@pytest.mark.xfail(
    strict=True, reason="CRW-005: SyncWorker.run sólo captura ValueError/TypeError/OSError"
)
def test_syncworker_captura_cualquier_excepcion():
    from presentation.widgets.sync_progress_dialog import SyncWorker

    fuente = inspect.getsource(SyncWorker.run)
    assert "except Exception" in fuente


# ---------------------------------------------------------------------------
# CRW-006: faulthandler en builds congelados
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="CRW-006: main.py no activa faulthandler")
def test_main_activa_faulthandler():
    fuente = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    assert "faulthandler" in fuente


# ---------------------------------------------------------------------------
# CRW-009: el caso de uso de generación gestiona su transacción
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="CRW-009: GuardiaAuditLog se añade sin commit propio")
def test_generar_guardias_hace_commit_del_audit_log():
    from application.use_cases.asignacion_guardias import generar_guardias

    fuente = inspect.getsource(generar_guardias.GenerarGuardiasUseCase.execute)
    assert "self.session.commit()" in fuente
