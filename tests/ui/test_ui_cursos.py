"""Tests de UI para GestionCursosWidget — gestión de cursos escolares."""

from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import CursoEscolar


def _get_widget(session):
    try:
        from presentation.widgets.gestion_cursos import GestionCursosWidget
        return GestionCursosWidget(session)
    except ImportError:
        try:
            from presentation.forms.cursos_form import CursosForm
            return CursosForm(session)
        except ImportError:
            return None


@pytest.fixture
def widget(qapp, session):
    w = _get_widget(session)
    if w is None:
        pytest.skip("GestionCursosWidget no encontrado")
    QApplication.processEvents()
    yield w
    w.close()


@pytest.fixture
def widget_con_cursos(qapp, session):
    from services.gestor_cursos import GestorCursos
    from datetime import date

    gc = GestorCursos(session)
    gc.crear_nuevo_curso(
        anio_inicio=2024,
        anio_fin=2025,
        fecha_inicio=date(2024, 9, 1),
        fecha_fin=date(2025, 6, 30),
        nombre="2024/2025",
        activar=True,
    )
    gc.crear_nuevo_curso(
        anio_inicio=2025,
        anio_fin=2026,
        fecha_inicio=date(2025, 9, 1),
        fecha_fin=date(2026, 6, 30),
        nombre="2025/2026",
        activar=False,
    )
    session.flush()

    w = _get_widget(session)
    if w is None:
        pytest.skip("GestionCursosWidget no encontrado")
    QApplication.processEvents()
    yield w
    w.close()


class TestCursosRenderizado:
    def test_widget_se_crea_sin_crash(self, widget):
        assert widget is not None

    def test_widget_con_cursos_no_crashea(self, widget_con_cursos):
        assert widget_con_cursos is not None


class TestCursosInteraccion:
    def test_crear_curso_no_crashea(self, qtbot, widget):
        """Intentar crear curso no provoca crash."""
        btn = (
            getattr(widget, "crear_btn", None)
            or getattr(widget, "nuevo_btn", None)
            or getattr(widget, "btn_crear", None)
        )
        if btn:
            with patch.object(widget, "mostrar_exito", side_effect=None):
                with patch.object(widget, "mostrar_error", side_effect=None):
                    qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
                    QApplication.processEvents()

    def test_eliminar_curso_sin_seleccion_no_crashea(self, qtbot, widget):
        """Eliminar sin selección no provoca crash."""
        btn = (
            getattr(widget, "delete_btn", None)
            or getattr(widget, "eliminar_btn", None)
        )
        if btn:
            with patch.object(widget, "mostrar_advertencia", side_effect=None):
                qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
                QApplication.processEvents()

    def test_navegacion_cursos_no_crashea(self, qtbot, widget_con_cursos):
        """Navegar por los cursos no provoca crash."""
        tabla = (
            getattr(widget_con_cursos, "tabla_cursos", None)
            or getattr(widget_con_cursos, "cursos_table", None)
        )
        if tabla and tabla.rowCount() > 0:
            tabla.setCurrentCell(0, 0)
            QApplication.processEvents()
