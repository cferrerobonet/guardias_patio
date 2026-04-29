"""Tests de UI para SelectorCursoWidget — selector de curso activo."""

from datetime import date

import pytest
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import CursoEscolar
from presentation.widgets.selector_curso_widget import SelectorCursoWidget


@pytest.fixture
def widget_vacio(qapp, session):
    w = SelectorCursoWidget(session)
    w.show()
    QApplication.processEvents()
    yield w
    w.close()


@pytest.fixture
def widget_con_cursos(qapp, session):
    curso_activo = CursoEscolar(
        anio_inicio=2024, anio_fin=2025,
        nombre="2024/2025",
        fecha_inicio=date(2024, 9, 1),
        fecha_fin=date(2025, 6, 30),
        activo=True,
    )
    curso_inactivo = CursoEscolar(
        anio_inicio=2025, anio_fin=2026,
        nombre="2025/2026",
        fecha_inicio=date(2025, 9, 1),
        fecha_fin=date(2026, 6, 30),
        activo=False,
    )
    session.add_all([curso_activo, curso_inactivo])
    session.commit()

    w = SelectorCursoWidget(session)
    w.show()
    QApplication.processEvents()
    yield w, session, curso_activo
    w.close()


class TestSelectorCursoRenderizado:
    def test_widget_se_crea_sin_crash(self, widget_vacio):
        assert widget_vacio is not None

    def test_combo_existe(self, widget_vacio):
        assert hasattr(widget_vacio, "combo_cursos")

    def test_sin_cursos_combo_vacio(self, widget_vacio):
        assert widget_vacio.combo_cursos.count() == 0

    def test_obtener_activo_sin_cursos_retorna_none(self, widget_vacio):
        assert widget_vacio.obtener_curso_activo_id() is None


class TestSelectorCursoConDatos:
    def test_combo_cargado_con_cursos(self, widget_con_cursos):
        widget, _, _ = widget_con_cursos
        assert widget.combo_cursos.count() == 2

    def test_obtener_activo_retorna_id_correcto(self, widget_con_cursos):
        widget, _, curso_activo = widget_con_cursos
        assert widget.obtener_curso_activo_id() == curso_activo.id

    def test_refrescar_no_crashea(self, widget_con_cursos):
        widget, _, _ = widget_con_cursos
        widget.refrescar()
        QApplication.processEvents()
        assert widget.combo_cursos.count() == 2
