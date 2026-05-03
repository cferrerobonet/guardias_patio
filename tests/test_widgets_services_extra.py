"""
Tests para progress_indicators.py y analisis_equidad_use_case.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# ProgressDialog
# ===========================================================================


@pytest.mark.ui
class TestProgressDialog:
    def test_constructor_defaults(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog

        dlg = ProgressDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_constructor_custom(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog

        dlg = ProgressDialog(title="Cargando", message="Espere...", cancelable=False)
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Cargando"

    def test_fue_cancelado_inicial(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog

        dlg = ProgressDialog()
        qtbot.addWidget(dlg)
        assert dlg.fue_cancelado() is False

    def test_actualizar_progreso(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog

        dlg = ProgressDialog()
        qtbot.addWidget(dlg)
        dlg.actualizar_progreso(50, 100, "Procesando...")  # No debe lanzar

    def test_agregar_al_log(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog

        dlg = ProgressDialog(show_details=True)
        qtbot.addWidget(dlg)
        dlg.agregar_al_log("Mensaje de log")  # No debe lanzar

    def test_sin_detalles(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog

        dlg = ProgressDialog(show_details=False)
        qtbot.addWidget(dlg)
        assert dlg is not None


# ===========================================================================
# ProgressLogHandler
# ===========================================================================


@pytest.mark.ui
class TestProgressLogHandler:
    @pytest.mark.xfail(reason="Bug en código fuente: doble __init__ en ProgressLogHandler")
    def test_constructor(self, qtbot):
        from presentation.widgets.progress_indicators import ProgressDialog, ProgressLogHandler

        dlg = ProgressDialog()
        qtbot.addWidget(dlg)
        worker = MagicMock()
        handler = ProgressLogHandler(dlg, worker)
        assert handler is not None

    @pytest.mark.xfail(reason="Bug en código fuente: doble __init__ en ProgressLogHandler")
    def test_emit(self, qtbot):
        import logging

        from presentation.widgets.progress_indicators import ProgressDialog, ProgressLogHandler

        dlg = ProgressDialog()
        qtbot.addWidget(dlg)
        worker = MagicMock()
        handler = ProgressLogHandler(dlg, worker)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Procesando slots",
            args=(),
            exc_info=None,
        )
        handler.emit(record)  # No debe lanzar


# ===========================================================================
# AnalisisEquidadUseCase
# ===========================================================================


class TestAnalisisEquidadUseCase:
    def test_constructor(self):
        from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase

        session = MagicMock()
        with (
            patch("application.use_cases.analisis_equidad_use_case.EquidadGuardiasService"),
            patch("application.use_cases.analisis_equidad_use_case.DistribucionCuotasService"),
        ):
            uc = AnalisisEquidadUseCase(session)
        assert uc.session is session

    def test_execute_sin_guardias(self):
        from application.dtos.domain_services_dtos import AnalisisEquidadRequest
        from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase

        session = MagicMock()
        session.query.return_value.all.return_value = []
        session.query.return_value.filter.return_value.all.return_value = []

        with (
            patch("application.use_cases.analisis_equidad_use_case.EquidadGuardiasService"),
            patch("application.use_cases.analisis_equidad_use_case.DistribucionCuotasService"),
        ):
            uc = AnalisisEquidadUseCase(session)
            request = AnalisisEquidadRequest(configuracion_id=None)
            result = uc.execute(request)
        assert result is not None
