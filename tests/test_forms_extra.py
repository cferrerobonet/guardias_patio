"""
Tests para módulos con cobertura 38-46%:
- restricciones_widget.py
- zona_form.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# RestriccionesWidget
# ===========================================================================


@pytest.mark.ui
class TestRestriccionesWidget:
    def test_constructor(self, qtbot):
        from presentation.forms.profesor_widgets.restricciones_widget import (
            RestriccionesWidget,
        )

        w = RestriccionesWidget()
        qtbot.addWidget(w)
        assert w is not None

    def test_titulo(self, qtbot):
        from presentation.forms.profesor_widgets.restricciones_widget import (
            RestriccionesWidget,
        )

        w = RestriccionesWidget()
        qtbot.addWidget(w)
        assert w.title() != ""

    def test_poblar_tabla(self, qtbot):
        from presentation.forms.profesor_widgets.restricciones_widget import (
            RestriccionesWidget,
        )

        w = RestriccionesWidget()
        qtbot.addWidget(w)
        w._poblar_tabla()  # No debe lanzar

    def test_toggle_panel(self, qtbot):
        from presentation.forms.profesor_widgets.restricciones_widget import (
            RestriccionesWidget,
        )

        w = RestriccionesWidget()
        qtbot.addWidget(w)
        w._toggle_panel_restricciones()  # No debe lanzar


# ===========================================================================
# ZonaForm
# ===========================================================================


@pytest.mark.ui
class TestZonaForm:
    def test_constructor(self, qtbot, session):
        from presentation.forms.zona_form import ZonaForm

        form = ZonaForm(session)
        qtbot.addWidget(form)
        assert form is not None

    def test_setup_ui(self, qtbot, session):
        from presentation.forms.zona_form import ZonaForm

        form = ZonaForm(session)
        qtbot.addWidget(form)
        assert hasattr(form, "session")
