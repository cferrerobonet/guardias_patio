"""UI de las guardias voluntarias y del inicio del reparto oficial.

- Ficha del profesor: «Guardias voluntarias hechas» en la fila de horas y turno, con
  una línea de ayuda que explica la cuota oficial sin cambiar la altura del recuadro.
- Listado: columna «Volunt.» detrás de «Tutor», que ordena por número.
- Ajustes: «Inicio del reparto oficial de guardias» con la casilla «Igual que el
  inicio de curso».
"""

import json
from datetime import date, time
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QApplication, QSizePolicy

from infrastructure.database.models import Configuracion, Profesor, Zona
from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.profesor_table_helpers import COL_VOLUNTARIAS, COLUMNAS_PROFESORES
from presentation.forms.profesor_widgets import HorarioWidget
from tests.ui.helpers import select_row


def _config(session, oficial=None):
    cfg = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=date(2025, 9, 1),
        fecha_fin_curso=date(2025, 10, 20),
        fecha_inicio_reparto_oficial=oficial,
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=False,
        recreos_config=json.dumps([{"id": 1, "etiqueta": "R1", "turno": "mañana", "zonas": 5}]),
    )
    session.add(cfg)
    session.add_all([Zona(nombre_zona=f"Z{i}", activa=True) for i in range(5)])
    session.commit()
    return cfg


def _profesores(session, voluntarias=(10, 10, 0, 0, 0, 0, 0, 0, 0, 0)):
    profes = [
        Profesor(
            nombre_completo=f"P{i:02d}, Nombre",
            horas_contrato=30.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            tutor=False,
            activo=True,
            guardias_voluntarias=v,
        )
        for i, v in enumerate(voluntarias)
    ]
    session.add_all(profes)
    session.commit()
    return profes


def _guardar(form):
    with patch.object(form, "mostrar_exito"):
        form.submit_btn.click()
        QApplication.processEvents()


def _fila_de(form, nombre):
    for fila in range(form.tabla_profesores.rowCount()):
        if form.tabla_profesores.item(fila, 0).text() == nombre:
            return fila
    raise AssertionError(nombre)


class TestFichaProfesor:
    def test_alta_guarda_las_voluntarias(self, qapp, session):
        form = ProfesorForm(session)
        form._abrir_formulario_nuevo()
        form.datos_basicos_widget.nombre_completo_input.setText("NUEVA, Voluntaria")
        form.horario_widget.horas_input.setText("30")
        form.horario_widget.set_turno("mañana")
        form.horario_widget.voluntarias_input.setValue(7)
        _guardar(form)
        session.expire_all()
        prof = session.query(Profesor).filter_by(nombre_completo="NUEVA, Voluntaria").one()
        assert prof.guardias_voluntarias == 7
        form.close()

    def test_editar_carga_y_guarda(self, qapp, session):
        _config(session)
        _profesores(session)
        form = ProfesorForm(session)
        form.cargar_profesores()
        select_row(form.tabla_profesores, _fila_de(form, "P00, Nombre"))
        form.editar_profesor()
        assert form.horario_widget.voluntarias_input.value() == 10
        form.horario_widget.voluntarias_input.setValue(12)
        _guardar(form)
        session.expire_all()
        prof = session.query(Profesor).filter_by(nombre_completo="P00, Nombre").one()
        assert prof.guardias_voluntarias == 12
        form.close()

    def test_limpiar_vuelve_a_cero(self, qapp, session):
        form = ProfesorForm(session)
        form.horario_widget.voluntarias_input.setValue(9)
        form._limpiar_formulario()
        assert form.horario_widget.voluntarias_input.value() == 0
        form.close()

    def test_linea_de_ayuda_en_edicion(self, qapp, qtbot, session):
        _config(session)
        _profesores(session)
        form = ProfesorForm(session)
        form.show()
        form.cargar_profesores()
        select_row(form.tabla_profesores, _fila_de(form, "P00, Nombre"))
        form.editar_profesor()
        etiqueta = form.horario_widget.ayuda_cuota_label
        assert etiqueta.isVisible()
        # 36 días × 5 zonas = 180 ranuras + 20 voluntarias → 20 cada uno
        assert etiqueta.text() == "Cuota oficial: 10 (le tocan 20 en el curso − 10 ya hechas)"

        # Cambiar el valor la recalcula tras un pequeño retardo, sin guardarlo
        form.horario_widget.voluntarias_input.setValue(30)
        qtbot.waitUntil(lambda: "30 ya hechas" in etiqueta.text(), timeout=2000)
        assert etiqueta.text().startswith("Cuota oficial: 0 ")
        assert "más de las que le tocan" in etiqueta.text()
        session.expire_all()
        assert session.query(Profesor).filter_by(nombre_completo="P00, Nombre").one(
        ).guardias_voluntarias == 10
        form.close()

    def test_sin_linea_de_ayuda_en_alta_o_sin_configuracion(self, qapp, session):
        _profesores(session)
        form = ProfesorForm(session)
        form.show()
        form._abrir_formulario_nuevo()
        form.horario_widget.voluntarias_input.setValue(5)
        form._actualizar_ayuda_cuota()
        assert not form.horario_widget.ayuda_cuota_label.isVisible()

        form.cargar_profesores()
        select_row(form.tabla_profesores, 0)
        form.editar_profesor()  # hay profesor, pero no configuración
        assert not form.horario_widget.ayuda_cuota_label.isVisible()
        form.close()


class TestFilaDeHorario:
    def test_el_campo_esta_en_la_fila_de_horas_y_turno(self, qapp):
        widget = HorarioWidget()
        widget.resize(760, widget.sizeHint().height())
        widget.show()
        QApplication.processEvents()

        def centro(campo):
            return campo.mapTo(widget, campo.rect().center())

        assert centro(widget.voluntarias_input).y() == pytest.approx(
            centro(widget.horas_input).y(), abs=4
        )
        assert centro(widget.voluntarias_input).x() > centro(widget.turno_input).x()
        widget.close()

    def test_el_campo_no_ensancha_el_recuadro(self, qapp):
        widget = HorarioWidget()
        antes = widget.sizeHint().width()
        widget.voluntarias_input.setValue(500)
        assert widget.voluntarias_input.parentWidget().sizePolicy().horizontalPolicy() == (
            QSizePolicy.Policy.Ignored
        )
        assert widget.sizeHint().width() == antes
        widget.close()

    def test_la_ayuda_no_cambia_la_altura_ni_mueve_la_segunda_fila(self, qapp):
        widget = HorarioWidget()
        widget.resize(700, widget.sizeHint().height())
        widget.show()
        widget.set_turno("mixto")
        QApplication.processEvents()
        alto = widget.sizeHint().height()
        y_mixto = widget.horas_manana_input.y()

        widget.set_ayuda_cuota("Cuota oficial: 3 (le tocan 5 en el curso − 2 ya hechas)")
        QApplication.processEvents()
        assert widget.sizeHint().height() == alto
        assert widget.horas_manana_input.y() == y_mixto

        widget.set_ayuda_cuota(None)
        QApplication.processEvents()
        assert widget.sizeHint().height() == alto
        widget.close()

    def test_get_set_datos(self, qapp):
        widget = HorarioWidget()
        widget.set_datos({"guardias_voluntarias": 4})
        assert widget.get_datos()["guardias_voluntarias"] == 4
        widget.set_datos({"guardias_voluntarias": None})
        assert widget.get_guardias_voluntarias() == 0
        assert widget.voluntarias_input.maximum() == 500
        widget.close()


class TestListado:
    def test_columna_detras_de_tutor(self, qapp, session):
        form = ProfesorForm(session)
        cabeceras = [
            form.tabla_profesores.horizontalHeaderItem(i).text()
            for i in range(form.tabla_profesores.columnCount())
        ]
        assert cabeceras == COLUMNAS_PROFESORES
        assert cabeceras.index("Volunt.") == cabeceras.index("Tutor") + 1 == COL_VOLUNTARIAS
        form.close()

    def test_numero_o_guion_centrado(self, qapp, session):
        _profesores(session, voluntarias=(7, 0))
        form = ProfesorForm(session)
        form.cargar_profesores()
        item_7 = form.tabla_profesores.item(_fila_de(form, "P00, Nombre"), COL_VOLUNTARIAS)
        item_0 = form.tabla_profesores.item(_fila_de(form, "P01, Nombre"), COL_VOLUNTARIAS)
        assert item_7.text() == "7"
        assert item_0.text() == "-"
        assert item_7.textAlignment() & Qt.AlignmentFlag.AlignHCenter
        # Las fechas siguen en sus columnas
        assert form.tabla_profesores.item(0, COL_VOLUNTARIAS + 1).text() == "-"
        form.close()

    def test_ordena_por_numero(self, qapp, session):
        _profesores(session, voluntarias=(10, 2, 0))
        form = ProfesorForm(session)
        form.cargar_profesores()
        form.tabla_profesores.sortItems(COL_VOLUNTARIAS, Qt.SortOrder.AscendingOrder)
        textos = [
            form.tabla_profesores.item(f, COL_VOLUNTARIAS).text()
            for f in range(form.tabla_profesores.rowCount())
        ]
        assert textos == ["-", "2", "10"]
        form.close()

    def test_seleccion_multiple_sigue_funcionando(self, qapp, session):
        _profesores(session, voluntarias=(1, 2, 3))
        form = ProfesorForm(session)
        form.cargar_profesores()
        form.tabla_profesores.sortItems(COL_VOLUNTARIAS, Qt.SortOrder.DescendingOrder)
        form.seleccionar_todos()
        filas = form.tabla_profesores.selectionModel().selectedRows()
        ids = {form.tabla_profesores.item(f.row(), 0).data(Qt.ItemDataRole.UserRole) for f in filas}
        assert ids == {p.id for p in session.query(Profesor).all()}
        form.close()


class TestAjustes:
    @pytest.fixture
    def widget(self, qapp):
        from presentation.forms.config_widgets import FechasRecreosWidget

        w = FechasRecreosWidget()
        w.set_fechas(date(2025, 9, 1), date(2026, 6, 19))
        yield w
        w.close()

    def test_por_defecto_igual_que_el_inicio(self, widget):
        assert widget.reparto_igual_inicio_check.isChecked()
        assert not widget.fecha_reparto_input.isEnabled()
        assert widget.get_fecha_reparto_oficial() is None

    def test_cargar_y_leer_una_fecha(self, widget):
        widget.set_fecha_reparto_oficial(date(2025, 10, 6))
        assert not widget.reparto_igual_inicio_check.isChecked()
        assert widget.fecha_reparto_input.isEnabled()
        assert widget.get_fecha_reparto_oficial() == date(2025, 10, 6)
        widget.set_fecha_reparto_oficial(None)
        assert widget.get_fecha_reparto_oficial() is None

    def test_validacion_dentro_del_curso(self, widget):
        widget.reparto_igual_inicio_check.setChecked(False)
        widget.fecha_reparto_input.setDate(QDate(2025, 8, 31))
        valido, mensaje = widget.validar()
        assert not valido and "anterior al inicio de curso" in mensaje
        widget.fecha_reparto_input.setDate(QDate(2026, 6, 20))
        valido, mensaje = widget.validar()
        assert not valido and "posterior al fin de curso" in mensaje
        widget.fecha_reparto_input.setDate(QDate(2025, 10, 6))
        assert widget.validar() == (True, "")

    def test_el_formulario_guarda_y_carga(self, qapp, session):
        from presentation.forms.ajustes_form import AjustesForm

        _config(session)
        form = AjustesForm(session)
        form.cargar_configuracion()
        fechas = form.fechas_recreos_widget
        assert fechas.get_fecha_reparto_oficial() is None

        fechas.reparto_igual_inicio_check.setChecked(False)
        fechas.fecha_reparto_input.setDate(QDate(2025, 9, 15))
        with patch.object(form, "mostrar_exito"):
            form.guardar_configuracion()
        session.expire_all()
        assert session.query(Configuracion).one().fecha_inicio_reparto_oficial == date(2025, 9, 15)

        fechas.reparto_igual_inicio_check.setChecked(True)
        with patch.object(form, "mostrar_exito"):
            form.guardar_configuracion()
        session.expire_all()
        assert session.query(Configuracion).one().fecha_inicio_reparto_oficial is None
        form.close()
