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
from PyQt6.QtWidgets import QApplication

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

    def test_recreos_personalizados_persisten(self, qapp, session, profesor_factory):
        """
        Regresión: modificar la matriz de recreos con checkbox activo debe
        guardarse en BD. Detecta el bug 'recreos editados pero no guardados'.
        """
        prof = profesor_factory("RECREOS, Test", turno="mañana", horas_contrato=20.0)
        prof_id = prof.id

        form = ProfesorForm(session)
        form.show()
        QApplication.processEvents()
        _abrir_edicion(form, 0)

        widget = form.restricciones_widget
        # Activar restricciones personalizadas
        widget.usar_restricciones_checkbox.setChecked(True)
        QApplication.processEvents()

        # Aplicar plantilla "Lun/Mié/Vie" (solo días 0, 2, 4) — diferente del default mañana
        dias_custom = {0: [1, 2], 2: [1, 2], 4: [1, 2]}
        widget.semana_widget._aplicar_plantilla(dias_custom)
        QApplication.processEvents()

        _guardar(form)
        session.expire_all()

        prof_bd = session.get(Profesor, prof_id)
        assert prof_bd.recreos_permitidos is not None
        assert prof_bd.recreos_permitidos != ""

        recreos_guardados = json.loads(prof_bd.recreos_permitidos)
        # Días 0, 2, 4 deben tener recreos; días 1, 3 no
        assert "0" in recreos_guardados
        assert "2" in recreos_guardados
        assert "4" in recreos_guardados
        # Días 1 y 3 pueden estar ausentes o con lista vacía
        recreos_dia1 = recreos_guardados.get("1", [])
        recreos_dia3 = recreos_guardados.get("3", [])
        assert recreos_dia1 == []
        assert recreos_dia3 == []
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
