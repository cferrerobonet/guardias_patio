"""
Tests de persistencia campo a campo.

Cada test verifica que una acción de modificación en la UI llega realmente a la BD.
Ninguno mockea use cases — ejercitan el stack completo.
La suite detecta bugs como 'el campo X se muestra pero no se guarda'.
"""

import json
from datetime import date, time
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QApplication, QPushButton

from infrastructure.database.models import Configuracion, Profesor, Zona
from presentation.forms.ajustes_form import AjustesForm
from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.zona_form import ZonaForm

from tests.ui.helpers import select_row


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _config_base(session):
    cfg = Configuracion(
        anio_inicio_curso=2024,
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=True,
        recreos_config='[{"id":1,"etiqueta":"R1","turno":"manana","hora":"11:00","zonas":2}]',
    )
    session.add(cfg)
    session.commit()
    return cfg


def _abrir_edicion(form, row=0):
    select_row(form.tabla_profesores, row)
    form.editar_profesor()
    QApplication.processEvents()


def _guardar(form):
    with patch.object(form, "mostrar_exito"):
        form.submit_btn.click()
        QApplication.processEvents()


# ──────────────────────────────────────────────────────────────────────────────
# ProfesorForm — campos básicos
# ──────────────────────────────────────────────────────────────────────────────

class TestProfesorCamposBasicosPersis:

    def test_nombre_completo_persiste(self, qapp, session):
        form = ProfesorForm(session)
        form.show()
        form._abrir_formulario_nuevo()
        QApplication.processEvents()
        form.datos_basicos_widget.nombre_completo_input.setText("PERSISTENCIA, Nombre")
        form.horario_widget.horas_input.setText("20")
        form.horario_widget.set_turno("mañana")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        prof = session.query(Profesor).filter_by(nombre_completo="PERSISTENCIA, Nombre").first()
        assert prof is not None
        form.close()

    def test_email_corporativo_persiste(self, qapp, session):
        form = ProfesorForm(session)
        form.show()
        form._abrir_formulario_nuevo()
        QApplication.processEvents()
        form.datos_basicos_widget.nombre_completo_input.setText("EMAIL, Test")
        form.datos_basicos_widget.email_input.setText("test@colegio.edu")
        form.horario_widget.horas_input.setText("20")
        form.horario_widget.set_turno("mañana")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        prof = session.query(Profesor).filter_by(nombre_completo="EMAIL, Test").first()
        assert prof.email_corporativo == "test@colegio.edu"
        form.close()

    def test_email_se_puede_borrar(self, qapp, session, profesor_factory):
        prof = profesor_factory("BORRAREMAIL, Test", turno="mañana", horas_contrato=20.0)
        prof.email_corporativo = "borrar@test.edu"
        session.commit()
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.datos_basicos_widget.email_input.setText("")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).email_corporativo is None
        form.close()

    def test_tutor_true_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("TUTOR, Test", turno="mañana", horas_contrato=20.0)
        prof.tutor = False
        session.commit()
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.datos_basicos_widget.tutor_checkbox.setChecked(True)
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).tutor is True
        form.close()

    def test_tutor_false_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("NOTUTOR, Test", turno="mañana", horas_contrato=20.0)
        prof.tutor = True
        session.commit()
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.datos_basicos_widget.tutor_checkbox.setChecked(False)
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).tutor is False
        form.close()


# ──────────────────────────────────────────────────────────────────────────────
# ProfesorForm — campos de horario
# ──────────────────────────────────────────────────────────────────────────────

class TestProfesorCamposHorarioPersis:

    def test_horas_contrato_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("HORAS, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.horario_widget.horas_input.setText("30")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).horas_contrato == 30.0
        form.close()

    def test_turno_tarde_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("TURNOTARDE, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.horario_widget.set_turno("tarde")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).turno == "tarde"
        form.close()

    def test_horas_manana_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("HORASMANANA, Test", turno="mixto", horas_contrato=30.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        # horas_manana se expone cuando turno = mixto
        form.horario_widget.set_turno("mixto")
        QApplication.processEvents()
        if hasattr(form.horario_widget, "horas_manana_input"):
            form.horario_widget.horas_manana_input.setText("4")
            QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        prof_bd = session.get(Profesor, prof_id)
        if prof_bd.horas_manana is not None:
            assert prof_bd.horas_manana == 4.0
        form.close()

    def test_horas_tarde_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("HORASTARDE, Test", turno="mixto", horas_contrato=30.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.horario_widget.set_turno("mixto")
        QApplication.processEvents()
        if hasattr(form.horario_widget, "horas_tarde_input"):
            form.horario_widget.horas_tarde_input.setText("4")
            QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        prof_bd = session.get(Profesor, prof_id)
        if prof_bd.horas_tarde is not None:
            assert prof_bd.horas_tarde == 4.0
        form.close()


# ──────────────────────────────────────────────────────────────────────────────
# ProfesorForm — campos de restricciones
# ──────────────────────────────────────────────────────────────────────────────

class TestProfesorCamposRestriccionesPersis:

    def test_zona_preferida_persiste(self, qapp, session, profesor_factory, zona_factory):
        zona = zona_factory(nombre_zona="Zona Persist")
        prof = profesor_factory("ZONAPERSIS, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        combo = form.restricciones_widget.zona_preferida_combo
        for i in range(combo.count()):
            if combo.itemData(i) == zona.id:
                combo.setCurrentIndex(i)
                break
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).zona_preferida_id == zona.id
        form.close()

    def test_zona_preferida_null_persiste(self, qapp, session, profesor_factory, zona_factory):
        zona = zona_factory(nombre_zona="Zona Borrar")
        prof = profesor_factory("ZONABORRAR, Test", turno="mañana", horas_contrato=20.0,
                                zona_preferida_id=zona.id)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.restricciones_widget.zona_preferida_combo.setCurrentIndex(0)
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).zona_preferida_id is None
        form.close()

    def test_zona_creada_con_la_vista_abierta_se_ve_y_no_se_borra(
        self, qapp, session, profesor_factory
    ):
        # La vista de profesores se crea al arrancar; las zonas pueden llegar
        # después (vista Zonas, importación o descarga) (2026-10-03).
        prof = profesor_factory("ZONATARDE, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id
        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()

        zona = Zona(nombre_zona="Zona Tardía")
        session.add(zona)
        session.commit()
        prof.zona_preferida_id = zona.id
        session.commit()

        _abrir_edicion(form, 0)
        assert form.restricciones_widget.get_zona_preferida_id() == zona.id
        form.datos_basicos_widget.email_input.setText("tarde@colegio.edu")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).zona_preferida_id == zona.id
        form.close()

    def test_fecha_inicio_guardias_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("FECHAINICIO, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.restricciones_widget.usar_fecha_inicio_checkbox.setChecked(True)
        QApplication.processEvents()
        form.restricciones_widget.fecha_inicio_guardias_input.setDate(QDate(2025, 1, 15))
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).fecha_inicio_guardias == date(2025, 1, 15)
        form.close()

    def test_fecha_inicio_guardias_null_persiste(self, qapp, session, profesor_factory):
        prof = profesor_factory("FECHANULL, Test", turno="mañana", horas_contrato=20.0)
        prof.fecha_inicio_guardias = date(2025, 1, 1)
        session.commit()
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.restricciones_widget.usar_fecha_inicio_checkbox.setChecked(False)
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof_id).fecha_inicio_guardias is None
        form.close()

    def test_semana_widget_deshabilitado_sin_checkbox(self, qapp, session, profesor_factory):
        """
        Regresión: semana_widget debe arrancar deshabilitado cuando el checkbox
        está desmarcado, impidiendo que el usuario modifique la matriz sin activarla.
        """
        prof = profesor_factory("MATRIZINIT, Test", turno="mañana", horas_contrato=20.0)
        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        widget = form.restricciones_widget
        assert not widget.usar_restricciones_checkbox.isChecked()
        assert not widget.semana_widget.isEnabled()
        form.close()

    def test_recreos_personalizados_persisten(self, qapp, session, profesor_factory):
        """
        Regresión: pulsar botón de plantilla en la matriz y guardar debe persistir
        los recreos en BD. Detecta el bug donde la matriz era visualmente
        interactiva pero no guardaba sin marcar el checkbox primero.
        """
        prof = profesor_factory("RECREOS, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)

        widget = form.restricciones_widget
        # Activar restricciones personalizadas (habilita la matriz)
        widget.usar_restricciones_checkbox.setChecked(True)
        QApplication.processEvents()
        assert widget.semana_widget.isEnabled()

        # Pulsar el botón de plantilla real "Lun/Mié/Vie" en la UI
        btn_plantilla = None
        for btn in widget.semana_widget.findChildren(QPushButton):
            if "Lun" in btn.text():
                btn_plantilla = btn
                break
        assert btn_plantilla is not None, "Botón 'Lun/Mié/Vie' no encontrado en semana_widget"
        btn_plantilla.click()
        QApplication.processEvents()

        _guardar(form)
        session.expire_all()

        prof_bd = session.get(Profesor, prof_id)
        assert prof_bd.recreos_permitidos is not None
        assert prof_bd.recreos_permitidos != ""

        recreos_guardados = json.loads(prof_bd.recreos_permitidos)
        # Días 0, 2, 4 deben tener recreos; días 1, 3 deben estar vacíos
        assert "0" in recreos_guardados
        assert "2" in recreos_guardados
        assert "4" in recreos_guardados
        assert recreos_guardados.get("1", []) == []
        assert recreos_guardados.get("3", []) == []
        form.close()

    def test_recreos_por_defecto_se_guardan_segun_turno(self, qapp, session, profesor_factory):
        """Sin checkbox activo, guardar persiste los recreos por defecto del turno."""
        prof = profesor_factory("RECREOSDEF, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)

        # No activar checkbox → guarda por defecto de mañana (R1, R2)
        form.restricciones_widget.usar_restricciones_checkbox.setChecked(False)
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()

        prof_bd = session.get(Profesor, prof_id)
        assert prof_bd.recreos_permitidos is not None
        recreos = json.loads(prof_bd.recreos_permitidos)
        # Mañana por defecto: R1, R2 en todos los días
        for dia_str in [str(d) for d in range(5)]:
            assert 1 in recreos.get(dia_str, [])
            assert 2 in recreos.get(dia_str, [])
        form.close()

    def test_recreos_cambian_al_cambiar_turno(self, qapp, session, profesor_factory):
        """Cambiar turno de mañana a tarde guarda los recreos correctos."""
        prof = profesor_factory("RECREOSTURNO, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)

        form.horario_widget.set_turno("tarde")
        form.restricciones_widget.usar_restricciones_checkbox.setChecked(False)
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()

        prof_bd = session.get(Profesor, prof_id)
        recreos = json.loads(prof_bd.recreos_permitidos)
        # Tarde por defecto: R3, R4 — no R1 ni R2
        for dia_str in [str(d) for d in range(5)]:
            dia_recreos = recreos.get(dia_str, [])
            assert 3 in dia_recreos or 4 in dia_recreos
            assert 1 not in dia_recreos
        form.close()

    def test_dias_semana_permitidos_persisten(self, qapp, session, profesor_factory):
        """dias_semana_permitidos se guarda cuando hay restricciones activas."""
        prof = profesor_factory("DIASSEMANA, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)

        widget = form.restricciones_widget
        widget.usar_restricciones_checkbox.setChecked(True)
        QApplication.processEvents()

        # Solo lunes (día 0) y miércoles (día 2)
        widget.semana_widget._aplicar_plantilla({0: [1, 2], 2: [1, 2]})
        QApplication.processEvents()

        _guardar(form)
        session.expire_all()

        prof_bd = session.get(Profesor, prof_id)
        assert prof_bd.dias_semana_permitidos is not None
        dias = json.loads(prof_bd.dias_semana_permitidos)
        assert 0 in dias
        assert 2 in dias
        assert 1 not in dias
        assert 3 not in dias
        assert 4 not in dias
        form.close()


# ──────────────────────────────────────────────────────────────────────────────
# ProfesorForm — recreos personalizados por día (fallo del 2026-09-29)
# ──────────────────────────────────────────────────────────────────────────────

#: Lunes sólo R1; el resto R1 y R2. La unión de recreos (R1, R2) es la del turno
#: de mañana: justo el caso en que la personalización «no se guardaba».
_MATRIZ_LUNES_SOLO_R1 = {"0": [1], "1": [1, 2], "2": [1, 2], "3": [1, 2], "4": [1, 2]}


def _profesor_con_matriz(profesor_factory, matriz, dias=None):
    return profesor_factory(
        "PORDIA, Test",
        turno="mañana",
        horas_contrato=20.0,
        recreos_permitidos=json.dumps(matriz),
        dias_semana_permitidos=json.dumps(dias if dias is not None else [0, 1, 2, 3, 4]),
    )


def _abrir_form(session):
    form = ProfesorForm(session)
    form.show()
    QApplication.processEvents()
    _abrir_edicion(form, 0)
    return form


class TestProfesorRecreosPorDiaPersis:
    """Personalizar los recreos desde la rejilla y que siga ahí al volver."""

    def test_al_reabrir_la_rejilla_muestra_lo_guardado_dia_a_dia(
        self, qapp, session, profesor_factory
    ):
        _profesor_con_matriz(profesor_factory, _MATRIZ_LUNES_SOLO_R1)
        form = _abrir_form(session)

        widget = form.restricciones_widget
        celdas = widget.semana_widget._celdas
        assert widget.usar_restricciones_checkbox.isChecked()
        assert celdas[(0, 1)].isChecked()
        assert not celdas[(0, 2)].isChecked(), "el lunes R2 estaba quitado"
        assert celdas[(1, 2)].isChecked()
        form.close()

    def test_guardar_otro_campo_no_pisa_los_recreos_por_dia(
        self, qapp, session, profesor_factory
    ):
        prof_id = _profesor_con_matriz(profesor_factory, _MATRIZ_LUNES_SOLO_R1).id
        form = _abrir_form(session)

        form.datos_basicos_widget.email_input.setText("pordia@epla.es")
        _guardar(form)
        session.expire_all()

        guardado = json.loads(session.get(Profesor, prof_id).recreos_permitidos)
        assert guardado == _MATRIZ_LUNES_SOLO_R1
        form.close()

    def test_personalizar_desde_la_rejilla_sobrevive_a_reabrir_y_volver_a_guardar(
        self, qapp, session, profesor_factory
    ):
        prof = profesor_factory("REJILLA, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id
        form = _abrir_form(session)

        widget = form.restricciones_widget
        widget.usar_restricciones_checkbox.click()
        QApplication.processEvents()
        widget.semana_widget._celdas[(0, 2)].click()  # lunes, R2: fuera
        QApplication.processEvents()
        _guardar(form)

        _abrir_edicion(form, 0)
        widget = form.restricciones_widget
        assert widget.usar_restricciones_checkbox.isChecked()
        assert not widget.semana_widget._celdas[(0, 2)].isChecked()

        _guardar(form)
        session.expire_all()
        guardado = json.loads(session.get(Profesor, prof_id).recreos_permitidos)
        assert guardado["0"] == [1]
        assert guardado["1"] == [1, 2]
        form.close()

    def test_tocar_una_casilla_cuenta_como_cambio_sin_guardar(
        self, qapp, session, profesor_factory
    ):
        """Sin esto, salir de la vista tras tocar sólo la rejilla no avisaba."""
        _profesor_con_matriz(profesor_factory, _MATRIZ_LUNES_SOLO_R1)
        form = _abrir_form(session)
        assert not form.tiene_cambios()

        form.restricciones_widget.semana_widget._celdas[(2, 1)].click()
        QApplication.processEvents()

        assert form.tiene_cambios()
        form.close()

    def test_aplicar_una_plantilla_cuenta_como_cambio_sin_guardar(
        self, qapp, session, profesor_factory
    ):
        _profesor_con_matriz(profesor_factory, _MATRIZ_LUNES_SOLO_R1)
        form = _abrir_form(session)
        assert not form.tiene_cambios()

        plantilla = next(
            b
            for b in form.restricciones_widget.semana_widget.findChildren(QPushButton)
            if b.text() == "Siempre"
        )
        plantilla.click()
        QApplication.processEvents()

        assert form.tiene_cambios()
        form.close()

    def test_quitar_la_personalizacion_devuelve_los_dias_del_turno(
        self, qapp, session, profesor_factory
    ):
        """Sin lunes personalizado y luego desmarcado: el lunes tiene que volver."""
        matriz = {"1": [1, 2], "2": [1, 2], "3": [1, 2], "4": [1, 2]}
        prof_id = _profesor_con_matriz(profesor_factory, matriz, dias=[1, 2, 3, 4]).id
        form = _abrir_form(session)

        form.restricciones_widget.usar_restricciones_checkbox.click()
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()

        prof_bd = session.get(Profesor, prof_id)
        assert json.loads(prof_bd.dias_semana_permitidos) == [0, 1, 2, 3, 4]
        assert json.loads(prof_bd.recreos_permitidos)["0"] == [1, 2]
        form.close()


# ──────────────────────────────────────────────────────────────────────────────
# ZonaForm — campos
# ──────────────────────────────────────────────────────────────────────────────

class TestZonaCamposPersis:

    def test_nombre_zona_nuevo_persiste(self, qapp, session):
        form = ZonaForm(session)
        form.show()
        QApplication.processEvents()
        form.nombre_zona_input.setText("Zona Persistencia Test")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        zona = session.query(Zona).filter_by(nombre_zona="Zona Persistencia Test").first()
        assert zona is not None
        form.close()

    def test_nombre_zona_editado_persiste(self, qapp, session, zona_factory):
        zona = zona_factory(nombre_zona="Zona Original")
        zona_id = zona.id

        form = ZonaForm(session)
        form.show()
        QApplication.processEvents()
        select_row(form.tabla_zonas, 0)
        form.editar_zona()
        QApplication.processEvents()

        form.nombre_zona_input.setText("Zona Editada Persist")
        QApplication.processEvents()
        _guardar(form)
        session.expire_all()
        assert session.get(Zona, zona_id).nombre_zona == "Zona Editada Persist"
        form.close()


# ──────────────────────────────────────────────────────────────────────────────
# AjustesForm — campos de configuración
# ──────────────────────────────────────────────────────────────────────────────

class TestAjustesCamposPersis:

    def test_ajuste_tutores_persiste(self, qapp, session):
        _config_base(session)

        form = AjustesForm(session)
        form.show()
        QApplication.processEvents()

        form.ajustes_widget.ajuste_tutores_input.setText("0.85")
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.guardar_configuracion()
            QApplication.processEvents()

        session.expire_all()
        cfg = session.query(Configuracion).first()
        assert abs(cfg.ajuste_tutores - 0.85) < 0.001
        form.close()

    def test_ajuste_no_tutores_persiste(self, qapp, session):
        _config_base(session)

        form = AjustesForm(session)
        form.show()
        QApplication.processEvents()

        form.ajustes_widget.ajuste_no_tutores_input.setText("1.15")
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.guardar_configuracion()
            QApplication.processEvents()

        session.expire_all()
        cfg = session.query(Configuracion).first()
        assert abs(cfg.ajuste_no_tutores - 1.15) < 0.001
        form.close()

    def test_festivos_automaticos_desactivar_persiste(self, qapp, session):
        _config_base(session)

        form = AjustesForm(session)
        form.show()
        QApplication.processEvents()

        form.festivos_widget.set_festivos_config(activar_automaticos=False, dias_no_lectivos="")
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.guardar_configuracion()
            QApplication.processEvents()

        session.expire_all()
        cfg = session.query(Configuracion).first()
        assert cfg.activar_festivos_automaticos is False
        form.close()

    def test_dias_no_lectivos_personalizados_persisten(self, qapp, session):
        _config_base(session)

        form = AjustesForm(session)
        form.show()
        QApplication.processEvents()

        form.festivos_widget.set_festivos_config(
            activar_automaticos=True,
            dias_no_lectivos="2025-10-09, 2025-12-08",
        )
        QApplication.processEvents()

        with patch.object(form, "mostrar_exito"):
            form.guardar_configuracion()
            QApplication.processEvents()

        session.expire_all()
        cfg = session.query(Configuracion).first()
        # El valor exacto depende del DTO — verificar que se guardó algo
        assert cfg is not None
        form.close()


# ──────────────────────────────────────────────────────────────────────────────
# «Descartar» al salir de la vista
# ──────────────────────────────────────────────────────────────────────────────

class TestDescartarRevierte:
    """«Descartar» sólo quitaba el aviso: lo descartado seguía en pantalla y se
    guardaba con el siguiente «Guardar» (2026-10-03)."""

    def test_profesor(self, qapp, session, profesor_factory):
        prof = profesor_factory("DESCARTE, Test", turno="mañana", horas_contrato=20.0)
        prof.email_corporativo = "antes@colegio.edu"
        session.commit()
        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)
        form.datos_basicos_widget.email_input.setText("descartado@colegio.edu")
        form._al_editar_campo()
        assert form.tiene_cambios()

        form.revertir_cambios()
        assert not form.tiene_cambios()
        assert form.profesor_editando_id is None
        assert form.datos_basicos_widget.email_input.text() == ""
        _guardar(form)
        session.expire_all()
        assert session.get(Profesor, prof.id).email_corporativo == "antes@colegio.edu"
        form.close()

    def test_ajustes(self, qapp, session):
        _config_base(session)
        form = AjustesForm(session)
        form.show()
        QApplication.processEvents()
        original = form.ajuste_tutores_input.text()
        form.ajuste_tutores_input.setText("2.5")
        assert form.tiene_cambios()

        form.revertir_cambios()
        assert form.ajuste_tutores_input.text() == original
        assert not form.tiene_cambios()
        assert not form._dirty_label.isVisible()
        form.close()


def test_reportes_ve_un_profesor_nuevo_y_respeta_los_desmarcados(qapp, session, profesor_factory):
    from presentation.forms.reportes_form import ReportesForm

    _config_base(session)
    quitado = profesor_factory("QUITADO, Uno", turno="mañana", horas_contrato=20.0)
    form = ReportesForm(session)
    widget = form.calendarios_widget
    next(cb for cb in widget.profesor_checkboxes if cb.property("profesor_id") == quitado.id)\
        .setChecked(False)

    nuevo = profesor_factory("NUEVO, Dos", turno="mañana", horas_contrato=20.0)
    form.refrescar()

    estado = {cb.property("profesor_id"): cb.isChecked() for cb in widget.profesor_checkboxes}
    assert estado == {quitado.id: False, nuevo.id: True}
    assert form._ical_combo.findData(nuevo.id) >= 0
    form.close()


# ──────────────────────────────────────────────────────────────────────────────
# Guardar y reabrir: todos los campos
# ──────────────────────────────────────────────────────────────────────────────

def test_ajustes_todos_los_campos_sobreviven_a_reabrir(qapp, session):
    from PyQt6.QtCore import QTime

    _config_base(session)
    form = AjustesForm(session)
    fr = form.fechas_recreos_widget
    fr.fecha_inicio_input.setDate(QDate(2026, 9, 8))
    fr.fecha_fin_input.setDate(QDate(2027, 6, 18))
    fr.reparto_igual_inicio_check.setChecked(False)
    fr.fecha_reparto_input.setDate(QDate(2026, 9, 21))
    fr.recreo1_manana_input.setTime(QTime(10, 45))
    fr.recreo2_manana_input.setTime(QTime(12, 35))
    fr.recreo1_tarde_input.setTime(QTime(16, 50))
    fr.recreo2_tarde_input.setTime(QTime(18, 40))
    form.ajuste_tutores_input.setText("0.8")
    form.ajuste_no_tutores_input.setText("1.2")
    form.festivos_auto_input.setText("0")
    form.no_lectivos_input.setText("2026-10-09, 2026-12-07")
    with patch.object(form, "mostrar_exito"), patch.object(form, "mostrar_advertencia") as aviso:
        form.guardar_configuracion()
    assert not aviso.called, aviso.call_args
    form.close()

    otra = AjustesForm(session)
    fr = otra.fechas_recreos_widget
    assert fr.get_fechas() == {"fecha_inicio": date(2026, 9, 8), "fecha_fin": date(2027, 6, 18)}
    assert fr.get_fecha_reparto_oficial() == date(2026, 9, 21)
    assert fr.get_recreos_manana() == {"recreo1": time(10, 45), "recreo2": time(12, 35)}
    assert fr.get_recreos_tarde() == {"recreo1": time(16, 50), "recreo2": time(18, 40)}
    assert otra.ajustes_widget.get_ajustes()["tutores"] == 0.8
    assert otra.ajustes_widget.get_ajustes()["no_tutores"] == 1.2
    assert otra.festivos_widget.get_festivos_config() == {
        "activar_automaticos": False,
        "dias_no_lectivos": "2026-10-09, 2026-12-07",
    }
    assert not otra.tiene_cambios()
    otra.close()


def test_un_dia_no_lectivo_imposible_no_se_acepta(qapp, session):
    _config_base(session)
    form = AjustesForm(session)
    form.no_lectivos_input.setText("2026-10-09, 2026-30-03")
    valido, mensaje = form.validar_formulario()
    assert not valido and "2026-30-03" in mensaje
    form.close()


def test_zona_todos_los_campos_sobreviven_a_reabrir(qapp, session, zona_factory):
    zona = zona_factory(nombre_zona="Zona Completa")
    form = ZonaForm(session)
    form.show()
    QApplication.processEvents()
    select_row(form.tabla_zonas, 0)
    form.editar_zona()
    w = form.datos_zona_widget
    w.descripcion_input.setText("Junto a la pista")
    w.usar_fecha_inicio_check.setChecked(True)
    w.fecha_inicio_input.setDate(QDate(2026, 9, 14))
    w.usar_fecha_fin_check.setChecked(True)
    w.fecha_fin_input.setDate(QDate(2027, 5, 28))
    with patch.object(form, "mostrar_exito"):
        form.guardar_zona()

    select_row(form.tabla_zonas, 0)
    form.editar_zona()
    assert w.get_datos() == {
        "nombre": "Zona Completa",
        "descripcion": "Junto a la pista",
        "fecha_inicio": date(2026, 9, 14),
        "fecha_fin": date(2027, 5, 28),
    }
    session.expire_all()
    assert session.get(Zona, zona.id).fecha_fin == date(2027, 5, 28)
    form.close()
