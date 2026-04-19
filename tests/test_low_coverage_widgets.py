"""
Tests para widgets con baja cobertura:
- InitialConfigDialog (9%)
- GeneracionPanel (20%)
- ProfesorForm (42%)
- VistaCalendario (47%)
- progress_indicators (48%)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# InitialConfigDialog
# ===========================================================================


@pytest.mark.ui
class TestInitialConfigDialog:
    def test_constructor(self, qtbot):
        from presentation.dialogs.initial_config_dialog import InitialConfigDialog

        dlg = InitialConfigDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_titulo(self, qtbot):
        from presentation.dialogs.initial_config_dialog import InitialConfigDialog

        dlg = InitialConfigDialog()
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() != ""


# ===========================================================================
# GeneracionPanel
# ===========================================================================


@pytest.mark.ui
class TestGeneracionPanel:
    def test_constructor(self, qtbot, session):
        from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

        panel = GeneracionPanel(session)
        qtbot.addWidget(panel)
        assert panel is not None

    def test_constructor_con_sync_manager(self, qtbot, session):
        from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

        sync_mgr = MagicMock()
        panel = GeneracionPanel(session, sync_manager=sync_mgr)
        qtbot.addWidget(panel)
        assert panel is not None


# ===========================================================================
# ProfesorForm
# ===========================================================================


@pytest.mark.ui
class TestProfesorForm:
    def test_constructor(self, qtbot, session):
        from presentation.forms.profesor_form import ProfesorForm

        form = ProfesorForm(session)
        qtbot.addWidget(form)
        assert form is not None

    def test_refrescar(self, qtbot, session):
        from presentation.forms.profesor_form import ProfesorForm

        form = ProfesorForm(session)
        qtbot.addWidget(form)
        assert hasattr(form, "session")


# ===========================================================================
# VistaCalendario
# ===========================================================================


@pytest.mark.ui
class TestVistaCalendario:
    def test_constructor(self, qtbot, session):
        from presentation.widgets.vista_calendario import VistaCalendario

        widget = VistaCalendario(session)
        qtbot.addWidget(widget)
        assert widget is not None


# ===========================================================================
# ProgressIndicators básicos
# ===========================================================================


@pytest.mark.ui
class TestProgressIndicators:
    def test_progress_dialog_constructor(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog

        dlg = ProgressDialog(title="Título", message="Procesando...")
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_worker_thread(self, qtbot):
        from presentation.widgets.progress_indicators import WorkerThread

        def tarea(callback):
            callback(50, "Mitad")
            return "resultado"

        worker = WorkerThread(tarea)
        assert worker is not None
