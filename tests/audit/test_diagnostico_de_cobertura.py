"""FUN-013 — decir por qué un hueco de guardia se queda sin nadie.

Antes el registro sólo contaba cuántos slots no tenían profesor elegible, lo que
no da ninguna pista para arreglarlo. Ahora se dice qué regla dura dejó fuera a
cada profesor y qué cambio mínimo desbloquea el hueco.
"""

import datetime
import json

import pytest

from infrastructure.database.models import Ausencia, Profesor, Zona
from services._asignador_cpsat_helpers import Slot, _es_elegible_basico
from services.diagnostico_cobertura import (
    AUSENTE,
    FUERA_DE_RANGO,
    RECREO,
    TURNO,
    diagnosticar,
    motivos_de_exclusion,
)

LUNES = datetime.date(2025, 10, 6)


def _slot(recreo=1, turno="mañana", zona_id=1):
    return Slot(fecha=LUNES, turno=turno, recreo_id=recreo, zona_id=zona_id)


def _profesor(session, **kwargs):
    datos = {
        "nombre_completo": kwargs.pop("nombre", "Profesor, Uno"),
        "horas_contrato": 25.0,
        "porcentaje_jornada": 100.0,
        "turno": "mañana",
        "tutor": False,
        "activo": True,
    }
    datos.update(kwargs)
    profesor = Profesor(**datos)
    session.add(profesor)
    session.commit()
    return profesor


@pytest.fixture
def zona(session):
    z = Zona(nombre_zona="Patio A", activa=True)
    session.add(z)
    session.commit()
    return z


def test_sin_impedimento_no_hay_motivos(session, zona):
    profesor = _profesor(session)

    assert motivos_de_exclusion(profesor, _slot(zona_id=zona.id), session) == []


def test_el_turno_incompatible_se_nombra(session, zona):
    profesor = _profesor(session, turno="tarde")

    motivos = motivos_de_exclusion(profesor, _slot(zona_id=zona.id), session)
    assert TURNO in motivos


def test_una_ausencia_se_nombra(session, zona):
    profesor = _profesor(session)
    session.add(
        Ausencia(
            profesor_id=profesor.id,
            fecha_inicio=LUNES,
            fecha_fin=LUNES,
            tipo="permiso",
            activa=True,
        )
    )
    session.commit()

    assert AUSENTE in motivos_de_exclusion(profesor, _slot(zona_id=zona.id), session)


def test_el_periodo_de_guardias_se_nombra(session, zona):
    profesor = _profesor(session, fecha_inicio_guardias=LUNES + datetime.timedelta(days=30))

    assert FUERA_DE_RANGO in motivos_de_exclusion(profesor, _slot(zona_id=zona.id), session)


def test_un_recreo_no_permitido_se_nombra(session, zona):
    profesor = _profesor(session, recreos_permitidos=json.dumps([2]))

    assert RECREO in motivos_de_exclusion(profesor, _slot(recreo=1, zona_id=zona.id), session)


def test_se_recogen_todos_los_motivos_a_la_vez(session, zona):
    """`_es_elegible_basico` para en el primero; aquí interesan todos."""
    profesor = _profesor(session, turno="tarde", recreos_permitidos=json.dumps([2]))

    motivos = motivos_de_exclusion(profesor, _slot(recreo=1, zona_id=zona.id), session)
    assert TURNO in motivos and RECREO in motivos


def test_coincide_con_la_elegibilidad_real(session, zona):
    """Si el diagnóstico no da motivos, el solver debe considerarlo elegible."""
    permitido = _profesor(session, nombre="Puede, Uno")
    bloqueado = _profesor(session, nombre="No Puede, Dos", turno="tarde")
    slot = _slot(zona_id=zona.id)

    assert bool(motivos_de_exclusion(permitido, slot, session)) is not _es_elegible_basico(
        permitido, slot, session
    )
    assert bool(motivos_de_exclusion(bloqueado, slot, session)) is not _es_elegible_basico(
        bloqueado, slot, session
    )


def test_el_informe_cuenta_a_cuanta_gente_afecta_cada_regla(session, zona):
    for i in range(3):
        _profesor(session, nombre=f"Tarde{i}, Nombre", turno="tarde")
    _profesor(session, nombre="Recreo, Unico", recreos_permitidos=json.dumps([2]))
    profesores = session.query(Profesor).all()

    informe = diagnosticar(profesores, [_slot(recreo=1, zona_id=zona.id)], session)

    assert informe[0].motivos[TURNO] == 3
    assert informe[0].motivos[RECREO] == 1


def test_la_sugerencia_apunta_a_lo_que_bloquea_a_mas_gente(session, zona):
    for i in range(3):
        _profesor(session, nombre=f"Tarde{i}, Nombre", turno="tarde")
    profesores = session.query(Profesor).all()

    informe = diagnosticar(profesores, [_slot(zona_id=zona.id)], session)

    assert "turno" in informe[0].sugerencia


def test_sin_claustro_lo_dice_claramente(session, zona):
    informe = diagnosticar([], [_slot(zona_id=zona.id)], session)

    assert "claustro" in informe[0].sugerencia


def test_la_descripcion_incluye_el_hueco_y_el_remedio(session, zona):
    _profesor(session, turno="tarde")
    profesores = session.query(Profesor).all()

    texto = diagnosticar(profesores, [_slot(zona_id=zona.id)], session)[0].describir()

    assert "2025-10-06" in texto
    assert "recreo 1" in texto
    assert TURNO in texto
