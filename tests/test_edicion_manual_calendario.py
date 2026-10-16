"""GUA-CON-001: mover o asignar una guardia a mano con las restricciones del reparto.

Lo que el reparto nunca haría tampoco se puede hacer a mano: día fuera del reparto,
zona inactiva, hueco ya cubierto, turno equivocado, ausencia, fuera de las fechas del
profesor, día de la semana vetado, recreo no permitido o dos guardias el mismo día.
Cada cambio se confirma antes y se puede deshacer después.
"""

import json
from datetime import date, time, timedelta

import pytest

from infrastructure.database.models import (
    Ausencia,
    Configuracion,
    CursoEscolar,
    Guardia,
    GuardiaAuditLog,
    Profesor,
    Zona,
)
from services import edicion_manual_calendario as edicion
from services._asignador_cpsat_helpers import _es_elegible_basico
from services.edicion_manual_calendario import Hueco

LUNES = date(2026, 9, 7)
MARTES = LUNES + timedelta(days=1)
SABADO = LUNES + timedelta(days=5)
FIN = date(2026, 10, 2)


@pytest.fixture
def escenario(session):
    session.add(CursoEscolar(anio_inicio=2026, anio_fin=2027, fecha_inicio=LUNES,
                             fecha_fin=date(2027, 6, 30), nombre="Curso 2026/2027",
                             activo=True, cerrado=False))
    session.add(Configuracion(
        anio_inicio_curso=2026, fecha_inicio_curso=LUNES, fecha_fin_curso=FIN,
        hora_recreo1_manana=time(10, 45), hora_recreo2_manana=time(12, 35),
        activar_festivos_automaticos=False,
        recreos_config=(
            '[{"id": 1, "etiqueta": "R1", "turno": "mañana", "hora": "10:45", "zonas": 2},'
            ' {"id": 2, "etiqueta": "R2", "turno": "mañana", "hora": "12:35", "zonas": 2}]'
        ),
    ))
    zonas = [Zona(nombre_zona="Cerrada", activa=False), Zona(nombre_zona="A"), Zona(nombre_zona="B")]
    session.add_all(zonas)

    def profe(nombre, **kw):
        datos = dict(horas_contrato=30, porcentaje_jornada=100, turno="mañana")
        datos.update(kw)
        return Profesor(nombre_completo=nombre, **datos)

    profes = {
        "ana": profe("Ana, Libre"),
        "bea": profe("Bea, Libre"),
        "tarde": profe("Teo, Tarde", turno="tarde"),
        "inactivo": profe("Iñigo, Inactivo", activo=False),
        "solo_martes": profe("Marta, Martes", dias_semana_permitidos="[1]"),
        "desde_martes": profe("Dani, Desde", fecha_inicio_guardias=MARTES),
        "solo_r2": profe("Rosa, Recreo dos", recreos_permitidos="[2]"),
        "ausente": profe("Áurea, Ausente"),
    }
    session.add_all(profes.values())
    session.commit()
    session.add(Ausencia(profesor_id=profes["ausente"].id, fecha_inicio=LUNES, fecha_fin=LUNES,
                         tipo="permiso", activa=True))
    session.commit()
    _, a, b = zonas
    return {"zonas": zonas, "a": a, "b": b, **profes}


def _hueco(escenario, fecha=LUNES, recreo=1, zona="a"):
    return Hueco(fecha, "mañana", recreo, escenario[zona].id)


# --- Huecos -----------------------------------------------------------------


def test_los_huecos_del_dia_son_los_del_reparto(session, escenario):
    huecos = edicion.huecos_del_dia(session, LUNES)
    assert {(h.recreo, h.zona_id) for h in huecos} == {
        (r, escenario[z].id) for r in (1, 2) for z in ("a", "b")
    }
    assert edicion.huecos_del_dia(session, SABADO) == []


def test_ni_dia_fuera_del_reparto_ni_zona_inactiva(session, escenario):
    cerrada = escenario["zonas"][0]
    with pytest.raises(ValueError, match="no tiene ese recreo y esa zona"):
        edicion.asignar_guardia(session, Hueco(LUNES, "mañana", 1, cerrada.id), escenario["ana"].id)
    with pytest.raises(ValueError, match="no tiene ese recreo y esa zona"):
        edicion.asignar_guardia(session, _hueco(escenario, fecha=SABADO), escenario["ana"].id)
    with pytest.raises(ValueError, match="no tiene ese recreo y esa zona"):
        edicion.asignar_guardia(session, _hueco(escenario, recreo=3), escenario["ana"].id)


# --- Asignar ----------------------------------------------------------------


def test_asignar_un_hueco_libre(session, escenario):
    entrada = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)

    guardia = session.get(Guardia, entrada.guardia_id)
    assert guardia.profesor_id == escenario["ana"].id
    assert guardia.curso_id == session.query(CursoEscolar).one().id
    assert entrada.accion == "ASIGNADA_A_MANO"


def test_un_hueco_cubierto_no_se_vuelve_a_cubrir(session, escenario):
    edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    with pytest.raises(ValueError, match="ya tiene guardia en ese recreo: la hace Ana"):
        edicion.asignar_guardia(session, _hueco(escenario), escenario["bea"].id)


@pytest.mark.parametrize(
    ("quien", "motivo"),
    [
        ("tarde", "es de turno de tarde"),
        ("inactivo", "no está activo"),
        ("solo_martes", "no hace guardias los lunes"),
        ("desde_martes", "empieza a hacer guardias el 08/09/2026"),
        ("ausente", "está ausente ese día"),
    ],
)
def test_lo_que_el_reparto_no_haria_tampoco_a_mano(session, escenario, quien, motivo):
    with pytest.raises(ValueError, match=motivo):
        edicion.asignar_guardia(session, _hueco(escenario), escenario[quien].id)
    assert session.query(Guardia).count() == 0


def test_el_recreo_no_permitido_tampoco(session, escenario):
    with pytest.raises(ValueError, match="no puede hacer guardia en ese recreo"):
        edicion.asignar_guardia(session, _hueco(escenario, recreo=1), escenario["solo_r2"].id)
    edicion.asignar_guardia(session, _hueco(escenario, recreo=2), escenario["solo_r2"].id)


def test_como_mucho_una_guardia_al_dia(session, escenario):
    edicion.asignar_guardia(session, _hueco(escenario, recreo=1), escenario["ana"].id)
    with pytest.raises(ValueError, match="ya tiene otra guardia ese día"):
        edicion.asignar_guardia(session, _hueco(escenario, recreo=2, zona="b"), escenario["ana"].id)


def test_las_mismas_reglas_que_el_reparto_para_cada_profesor_y_hueco(session, escenario):
    """La lista de motivos y la elegibilidad del reparto dicen lo mismo, siempre."""
    for fecha in (LUNES, MARTES):
        for hueco in edicion.huecos_del_dia(session, fecha):
            for profesor in session.query(Profesor).all():
                puede = profesor.activo and _es_elegible_basico(profesor, hueco.slot, session)
                assert (not edicion.motivos_del_profesor(session, profesor, hueco)) == puede, (
                    profesor.nombre_completo, hueco,
                )


def test_los_candidatos_dicen_por_que_no(session, escenario):
    lista = dict((p.nombre_completo, m) for p, m in edicion.candidatos(session, _hueco(escenario)))
    assert lista["Ana, Libre"] == []
    assert any("turno" in m for m in lista["Teo, Tarde"])
    assert "Iñigo, Inactivo" not in lista


# --- Mover ------------------------------------------------------------------


def test_mover_a_otro_dia_zona_y_profesor(session, escenario):
    origen = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    destino = _hueco(escenario, fecha=MARTES, recreo=2, zona="b")

    edicion.mover_guardia(session, origen.guardia_id, destino, escenario["solo_martes"].id)

    guardia = session.get(Guardia, origen.guardia_id)
    assert Hueco.de_guardia(guardia) == destino
    assert guardia.profesor_id == escenario["solo_martes"].id


def test_mover_respeta_las_reglas_y_no_toca_nada_si_falla(session, escenario):
    entrada = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    with pytest.raises(ValueError, match="no hace guardias los lunes"):
        edicion.mover_guardia(
            session, entrada.guardia_id, _hueco(escenario, zona="b"), escenario["solo_martes"].id
        )
    guardia = session.get(Guardia, entrada.guardia_id)
    assert Hueco.de_guardia(guardia) == _hueco(escenario)
    assert guardia.profesor_id == escenario["ana"].id


def test_mover_dentro_del_mismo_dia_no_cuenta_la_propia_guardia(session, escenario):
    entrada = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    edicion.mover_guardia(session, entrada.guardia_id, _hueco(escenario, recreo=2), escenario["ana"].id)
    assert session.get(Guardia, entrada.guardia_id).recreo == 2


def test_mover_sin_cambiar_nada_se_avisa(session, escenario):
    entrada = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    with pytest.raises(ValueError, match="No has cambiado nada"):
        edicion.mover_guardia(session, entrada.guardia_id, _hueco(escenario), escenario["ana"].id)


# --- Deshacer ---------------------------------------------------------------


def test_deshacer_una_asignacion_la_quita(session, escenario):
    entrada = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    edicion.deshacer_edicion_manual(session, entrada.id)
    assert session.query(Guardia).count() == 0


def test_deshacer_un_movimiento_la_devuelve_a_su_sitio(session, escenario):
    alta = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    movida = edicion.mover_guardia(
        session, alta.guardia_id, _hueco(escenario, fecha=MARTES, zona="b"), escenario["bea"].id
    )

    edicion.deshacer_edicion_manual(session, movida.id)

    guardia = session.get(Guardia, alta.guardia_id)
    assert Hueco.de_guardia(guardia) == _hueco(escenario)
    assert guardia.profesor_id == escenario["ana"].id
    ultima = session.query(GuardiaAuditLog).order_by(GuardiaAuditLog.id.desc()).first()
    assert ultima.accion == "EDICION_DESHECHA"
    assert json.loads(ultima.detalle) == {"deshace": movida.id}


def test_no_se_deshace_dos_veces(session, escenario):
    alta = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    movida = edicion.mover_guardia(session, alta.guardia_id, _hueco(escenario, zona="b"), escenario["ana"].id)
    edicion.deshacer_edicion_manual(session, movida.id)
    with pytest.raises(ValueError, match="ya se deshizo"):
        edicion.deshacer_edicion_manual(session, movida.id)


def test_no_se_deshace_encima_de_un_cambio_posterior(session, escenario):
    alta = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    primera = edicion.mover_guardia(session, alta.guardia_id, _hueco(escenario, zona="b"), escenario["ana"].id)
    edicion.mover_guardia(session, alta.guardia_id, _hueco(escenario, recreo=2), escenario["bea"].id)

    with pytest.raises(ValueError, match="ha cambiado después"):
        edicion.deshacer_edicion_manual(session, primera.id)


# --- Interfaz ---------------------------------------------------------------


@pytest.mark.ui
def test_el_dialogo_desactiva_a_quien_no_puede_y_no_deja_guardar_un_hueco_ocupado(
    qapp, session, escenario
):
    from presentation.dialogs.editar_guardia_dialog import EditarGuardiaDialog

    edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    dialogo = EditarGuardiaDialog(session, LUNES, hueco=_hueco(escenario))

    modelo = dialogo.combo_profesor.model()
    estados = {
        dialogo.combo_profesor.itemText(i): modelo.item(i).isEnabled()
        for i in range(dialogo.combo_profesor.count())
    }
    assert estados["Teo, Tarde — no puede"] is False
    assert estados["Bea, Libre"] is True
    assert "ya tiene guardia en ese recreo" in dialogo.aviso.text()
    assert not dialogo.boton_ok.isEnabled()

    dialogo.combo_zona.setCurrentIndex(1)  # zona B, libre
    assert dialogo.boton_ok.isEnabled()
    assert "pasará de 0 a 1 guardias" in dialogo.aviso.text()
    dialogo.close()


@pytest.mark.ui
def test_el_dialogo_pide_confirmacion_y_sin_ella_no_guarda(qapp, session, escenario, dialogos_modales):
    from presentation.dialogs.editar_guardia_dialog import EditarGuardiaDialog

    dialogo = EditarGuardiaDialog(session, LUNES, hueco=_hueco(escenario))
    dialogo._aceptar()  # la barrera de modales responde «No», el botón por defecto

    assert any("¿Asignar" in d.texto for d in dialogos_modales)
    assert session.query(Guardia).count() == 0
    dialogo.close()


@pytest.mark.ui
def test_el_dialogo_con_confirmacion_guarda_y_deja_la_entrada_para_deshacer(
    qapp, session, escenario, monkeypatch
):
    from PyQt6.QtWidgets import QMessageBox

    from presentation.dialogs.editar_guardia_dialog import EditarGuardiaDialog

    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.StandardButton.Yes)
    dialogo = EditarGuardiaDialog(session, LUNES, hueco=_hueco(escenario))
    dialogo._aceptar()

    assert dialogo.entrada is not None
    guardia = session.get(Guardia, dialogo.entrada.guardia_id)
    assert guardia.profesor_id == dialogo.combo_profesor.currentData()
    dialogo.close()


@pytest.mark.ui
def test_el_detalle_del_dia_ofrece_mover_y_asignar(qapp, session, escenario):
    from PyQt6.QtWidgets import QPushButton

    from presentation.dialogs.dia_detalle_dialog import DiaDetalleDialog

    entrada = edicion.asignar_guardia(session, _hueco(escenario), escenario["ana"].id)
    guardia = session.get(Guardia, entrada.guardia_id)
    dialogo = DiaDetalleDialog(
        fecha=LUNES, guardias=[guardia], ausencias=[], sustituciones=[],
        zonas_esperadas_por_recreo={("mañana", 1): [escenario["a"], escenario["b"]]},
        session=session,
    )
    textos = [b.text() for b in dialogo.findChildren(QPushButton)]
    assert "Mover…" in textos
    assert "Asignar…" in textos  # la zona B de ese recreo, sin cubrir
    assert "Asignar guardia…" in textos
    dialogo.close()
