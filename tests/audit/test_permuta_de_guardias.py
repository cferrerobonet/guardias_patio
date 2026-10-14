"""Permutar una guardia entre dos profesores.

Petición de CarlosFB (2026-09-06): que dos profesores puedan intercambiarse una
guardia sin que nadie falte. No es una sustitución —eso parte de una baja— ni
edición libre del calendario: es un trato entre dos personas.

Decisión de producto: **intercambio 1 a 1**. Cada uno cede una y coge otra, así
que los totales del curso no cambian y el reparto sigue siendo equitativo.
"""

import datetime
from collections import Counter

import pytest

from infrastructure.database.models import Ausencia, Guardia, GuardiaAuditLog, Profesor, Zona
from services.gestor_ausencias import permutar_guardias

MARTES = datetime.date(2025, 10, 7)
JUEVES = datetime.date(2025, 10, 9)


@pytest.fixture
def escenario(session):
    """Dos profesores con una guardia cada uno, en días distintos."""
    session.add_all(
        [
            Profesor(
                nombre_completo=f"Profesor{i}, Nombre",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            )
            for i in range(3)
        ]
    )
    session.add(Zona(nombre_zona="Patio A", activa=True))
    session.commit()

    a, b, c = session.query(Profesor).order_by(Profesor.id).all()
    zona = session.query(Zona).first()
    guardia_a = Guardia(
        profesor_id=a.id, zona_id=zona.id, fecha=MARTES, turno="mañana", recreo=1
    )
    guardia_b = Guardia(
        profesor_id=b.id, zona_id=zona.id, fecha=JUEVES, turno="mañana", recreo=1
    )
    session.add_all([guardia_a, guardia_b])
    session.commit()
    return session, a, b, c, zona, guardia_a, guardia_b


def test_las_guardias_cambian_de_profesor(escenario):
    session, a, b, _c, _z, guardia_a, guardia_b = escenario

    permutar_guardias(session, guardia_a.id, guardia_b.id)
    session.refresh(guardia_a)
    session.refresh(guardia_b)

    assert guardia_a.profesor_id == b.id
    assert guardia_b.profesor_id == a.id


def test_los_totales_no_cambian(escenario):
    """Es la razón de ser del intercambio 1 a 1: el reparto sigue siendo justo."""
    session, _a, _b, _c, _z, guardia_a, guardia_b = escenario
    antes = Counter(g.profesor_id for g in session.query(Guardia).all())

    permutar_guardias(session, guardia_a.id, guardia_b.id)

    despues = Counter(g.profesor_id for g in session.query(Guardia).all())
    assert antes == despues


def test_no_se_marca_como_sustitucion(escenario):
    """Nadie ha faltado: marcarlo falsearía el historial de ausencias."""
    session, _a, _b, _c, _z, guardia_a, guardia_b = escenario

    permutar_guardias(session, guardia_a.id, guardia_b.id)
    session.refresh(guardia_a)

    assert guardia_a.es_sustitucion is False
    assert guardia_a.profesor_sustituido_id is None


def test_queda_registrado_en_las_dos_guardias(escenario):
    session, _a, _b, _c, _z, guardia_a, guardia_b = escenario

    permutar_guardias(session, guardia_a.id, guardia_b.id)

    acciones = [
        a for a in session.query(GuardiaAuditLog).all() if a.accion == "PERMUTADA"
    ]
    assert len(acciones) == 2
    assert {a.guardia_id for a in acciones} == {guardia_a.id, guardia_b.id}


# ---------------------------------------------------------------------------
# Lo que tiene que rechazar
# ---------------------------------------------------------------------------
def test_no_se_permuta_una_guardia_consigo_misma(escenario):
    session, _a, _b, _c, _z, guardia_a, _gb = escenario

    with pytest.raises(ValueError, match="distintas"):
        permutar_guardias(session, guardia_a.id, guardia_a.id)


def test_no_se_permuta_entre_guardias_del_mismo_profesor(escenario):
    session, a, _b, _c, zona, guardia_a, _gb = escenario
    otra = Guardia(
        profesor_id=a.id, zona_id=zona.id, fecha=JUEVES, turno="mañana", recreo=1
    )
    session.add(otra)
    session.commit()

    with pytest.raises(ValueError, match="mismo profesor"):
        permutar_guardias(session, guardia_a.id, otra.id)


def test_nadie_acaba_con_dos_guardias_el_mismo_dia(escenario):
    """Es la restricción de la que partía la petición: que el otro esté libre ese día."""
    session, _a, _b, c, zona, guardia_a, _gb = escenario
    # C ya tiene guardia el martes, y otra el jueves que ofrecería a cambio
    session.add_all(
        [
            Guardia(profesor_id=c.id, zona_id=zona.id, fecha=MARTES, turno="mañana", recreo=2),
            Guardia(profesor_id=c.id, zona_id=zona.id, fecha=JUEVES, turno="mañana", recreo=2),
        ]
    )
    session.commit()
    suya_del_jueves = (
        session.query(Guardia)
        .filter(Guardia.profesor_id == c.id, Guardia.fecha == JUEVES)
        .first()
    )

    with pytest.raises(ValueError, match="ya tiene otra guardia"):
        permutar_guardias(session, guardia_a.id, suya_del_jueves.id)


def test_no_se_permuta_con_alguien_ausente_ese_dia(escenario):
    session, _a, _b, c, zona, guardia_a, _gb = escenario
    session.add(
        Guardia(profesor_id=c.id, zona_id=zona.id, fecha=JUEVES, turno="mañana", recreo=2)
    )
    session.add(
        Ausencia(
            profesor_id=c.id,
            fecha_inicio=MARTES,
            fecha_fin=MARTES,
            tipo="baja_medica",
            activa=True,
        )
    )
    session.commit()
    suya = (
        session.query(Guardia)
        .filter(Guardia.profesor_id == c.id, Guardia.fecha == JUEVES)
        .first()
    )

    with pytest.raises(ValueError, match="ausente"):
        permutar_guardias(session, guardia_a.id, suya.id)


def test_una_permuta_rechazada_no_cambia_nada(escenario):
    """Si se valida a medias, el calendario quedaría inconsistente."""
    session, _a, _b, c, zona, guardia_a, _gb = escenario
    session.add_all(
        [
            Guardia(profesor_id=c.id, zona_id=zona.id, fecha=MARTES, turno="mañana", recreo=2),
            Guardia(profesor_id=c.id, zona_id=zona.id, fecha=JUEVES, turno="mañana", recreo=2),
        ]
    )
    session.commit()
    antes = {(g.id, g.profesor_id) for g in session.query(Guardia).all()}
    suya = (
        session.query(Guardia)
        .filter(Guardia.profesor_id == c.id, Guardia.fecha == JUEVES)
        .first()
    )

    with pytest.raises(ValueError):
        permutar_guardias(session, guardia_a.id, suya.id)

    session.expire_all()
    assert {(g.id, g.profesor_id) for g in session.query(Guardia).all()} == antes


# ---------------------------------------------------------------------------
# La vía desde el calendario
# ---------------------------------------------------------------------------
def test_el_dialogo_propone_solo_guardias_futuras_de_otro_profesor(qapp, escenario):
    from presentation.dialogs.permutar_guardia_dialog import PermutarGuardiaDialog

    session, a, b, _c, zona, _ga, _gb = escenario
    manana = datetime.date.today() + datetime.timedelta(days=1)
    ayer = datetime.date.today() - datetime.timedelta(days=1)
    mia = Guardia(profesor_id=a.id, zona_id=zona.id, fecha=manana, turno="mañana", recreo=1)
    suya_futura = Guardia(
        profesor_id=b.id,
        zona_id=zona.id,
        fecha=manana + datetime.timedelta(days=2),
        turno="mañana",
        recreo=1,
    )
    suya_pasada = Guardia(
        profesor_id=b.id, zona_id=zona.id, fecha=ayer, turno="mañana", recreo=2
    )
    session.add_all([mia, suya_futura, suya_pasada])
    session.commit()

    dialogo = PermutarGuardiaDialog(session, mia)
    try:
        profesores = [
            dialogo.combo_profesor.itemData(i) for i in range(dialogo.combo_profesor.count())
        ]
        assert a.id not in profesores, "se ofrece permutar con uno mismo"

        dialogo.combo_profesor.setCurrentIndex(profesores.index(b.id))
        ofrecidas = [
            dialogo.combo_guardia.itemData(i) for i in range(dialogo.combo_guardia.count())
        ]
        assert suya_futura.id in ofrecidas
        assert suya_pasada.id not in ofrecidas, "ofrece una guardia ya pasada"
    finally:
        dialogo.close()


def test_el_detalle_del_dia_ofrece_permutar(qapp, escenario):
    from presentation.dialogs.dia_detalle_dialog import DiaDetalleDialog

    session, _a, _b, _c, _z, guardia_a, _gb = escenario
    dialogo = DiaDetalleDialog(
        fecha=MARTES,
        guardias=[guardia_a],
        ausencias=[],
        sustituciones=[],
        session=session,
    )
    try:
        from PyQt6.QtWidgets import QPushButton

        botones = [
            b for b in dialogo.findChildren(QPushButton) if "Permutar" in b.text()
        ]
        assert botones, "el detalle del día no ofrece permutar"
        assert botones[0].accessibleName()
    finally:
        dialogo.close()


def test_sin_sesion_el_detalle_no_ofrece_permutar(qapp, escenario):
    """El diálogo se usa también en contextos de sólo lectura."""
    from presentation.dialogs.dia_detalle_dialog import DiaDetalleDialog
    from PyQt6.QtWidgets import QPushButton

    _session, _a, _b, _c, _z, guardia_a, _gb = escenario
    dialogo = DiaDetalleDialog(
        fecha=MARTES, guardias=[guardia_a], ausencias=[], sustituciones=[]
    )
    try:
        assert not [b for b in dialogo.findChildren(QPushButton) if "Permutar" in b.text()]
    finally:
        dialogo.close()
