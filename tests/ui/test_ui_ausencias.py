"""Tests de UI para GestionarAusenciasForm — CRUD completo de ausencias."""

from datetime import date, timedelta

import pytest
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Ausencia, CursoEscolar, Guardia
from presentation.widgets.gestionar_ausencias import GestionarAusenciasForm

from tests.ui.helpers import confirm_no, confirm_yes, select_row


def _crear_curso_y_guardia(session, profesor_factory, zona_factory):
    """Crea curso activo, un profesor con una guardia (requerido por cargar_profesores)."""
    curso = CursoEscolar(
        anio_inicio=2024,
        anio_fin=2025,
        nombre="2024/2025",
        fecha_inicio=date(2024, 9, 1),
        fecha_fin=date(2025, 6, 30),
        activo=True,
    )
    session.add(curso)
    session.flush()

    zona = zona_factory(nombre_zona="Patio Test")
    prof1 = profesor_factory("García López, María", turno="mañana", horas_contrato=25.0)
    prof2 = profesor_factory("Martínez Ruiz, Juan", turno="tarde", horas_contrato=18.0)
    session.flush()

    guardia1 = Guardia(
        profesor_id=prof1.id,
        zona_id=zona.id,
        fecha=date(2025, 1, 10),
        turno="mañana",
        recreo=1,
        curso_id=curso.id,
    )
    guardia2 = Guardia(
        profesor_id=prof2.id,
        zona_id=zona.id,
        fecha=date(2025, 1, 11),
        turno="tarde",
        recreo=1,
        curso_id=curso.id,
    )
    session.add_all([guardia1, guardia2])
    session.commit()
    return curso, prof1, prof2


@pytest.fixture
def form(qapp, session, profesor_factory, zona_factory):
    _crear_curso_y_guardia(session, profesor_factory, zona_factory)
    f = GestionarAusenciasForm(session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def form_con_ausencia(qapp, session, profesor_factory, zona_factory, ausencia_factory):
    curso, prof1, _ = _crear_curso_y_guardia(session, profesor_factory, zona_factory)
    ausencia_factory(
        profesor_id=prof1.id,
        fecha_inicio=date(2025, 3, 10),
        fecha_fin=date(2025, 3, 12),
        tipo="baja_medica",
    )
    session.flush()
    f = GestionarAusenciasForm(session)
    f.show()
    QApplication.processEvents()
    yield f
    f.close()


class TestAusenciasRenderizado:
    def test_tabla_existe_y_no_oculta(self, form):
        assert hasattr(form, "tabla_ausencias")
        assert not form.tabla_ausencias.isHidden()

    def test_combo_profesores_cargado(self, form):
        """El combo de profesores tiene al menos un profesor."""
        assert form.profesor_combo.count() > 0

    def test_titulo_form_nueva_ausencia(self, form):
        assert "AUSENCIA" in form.titulo_form.text().upper()


class TestAusenciasCrear:
    def test_crear_ausencia_valida(self, qtbot, form, session):
        """Seleccionar profesor + fechas + tipo y guardar crea ausencia en BD."""
        n_inicial = session.query(Ausencia).count()

        form.profesor_combo.setCurrentIndex(1)
        QApplication.processEvents()

        form.fecha_inicio_input.setDate(QDate(2025, 4, 1))
        form.fecha_fin_input.setDate(QDate(2025, 4, 3))
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_exito"):
            qtbot.mouseClick(form.guardar_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Ausencia).count() == n_inicial + 1

    def test_crear_ausencia_sin_profesor_muestra_advertencia(self, qtbot, form):
        """Guardar sin seleccionar profesor muestra advertencia."""
        form.profesor_combo.setCurrentIndex(-1)
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(form.guardar_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()

    def test_crear_ausencia_fecha_fin_anterior_inicio(self, qtbot, form):
        """Fecha fin anterior a inicio muestra error de validación."""
        form.profesor_combo.setCurrentIndex(1)
        form.fecha_inicio_input.setDate(QDate(2025, 4, 5))
        form.fecha_fin_input.setDate(QDate(2025, 4, 2))
        QApplication.processEvents()

        from unittest.mock import patch

        with patch.object(form, "mostrar_advertencia") as mock_warn:
            qtbot.mouseClick(form.guardar_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            mock_warn.assert_called_once()


class TestAusenciasEliminar:
    def test_eliminar_ausencia_confirmada(self, qtbot, form_con_ausencia, session):
        """Eliminar ausencia con confirmación la borra de BD."""
        n_inicial = session.query(Ausencia).count()
        assert n_inicial > 0
        select_row(form_con_ausencia.tabla_ausencias, 0)

        with confirm_yes(form_con_ausencia):
            qtbot.mouseClick(form_con_ausencia.delete_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Ausencia).count() == n_inicial - 1

    def test_eliminar_ausencia_cancelada(self, qtbot, form_con_ausencia, session):
        """Cancelar eliminación conserva la ausencia."""
        n_inicial = session.query(Ausencia).count()
        select_row(form_con_ausencia.tabla_ausencias, 0)

        with confirm_no(form_con_ausencia):
            qtbot.mouseClick(form_con_ausencia.delete_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Ausencia).count() == n_inicial


class TestAusenciasCargarSeleccionada:
    def test_tabla_ausencias_tiene_filas(self, form_con_ausencia):
        """La tabla de ausencias tiene al menos una fila tras cargar datos."""
        assert form_con_ausencia.tabla_ausencias.rowCount() > 0

    def test_editar_ausencia_carga_formulario(self, qtbot, form_con_ausencia):
        """Editar ausencia (click en fila) rellena el formulario."""
        select_row(form_con_ausencia.tabla_ausencias, 0)
        item = form_con_ausencia.tabla_ausencias.item(0, 0)
        if item:
            form_con_ausencia.cargar_ausencia_seleccionada()
            QApplication.processEvents()
            assert (
                form_con_ausencia.ausencia_actual is not None
                or form_con_ausencia.profesor_combo.currentIndex() > 0
            )
