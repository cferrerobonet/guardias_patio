"""Centros sin guardias de mañana o sin guardias de tarde (2026-10-06).

Un usuario con todo el profesorado de tarde tenía configurados recreos de
mañana: la generación dejaba el 50 % de los huecos sin nadie elegible y no
había forma de quitar esos recreos (la validación exigía sus horas). Ahora cada
turno se quita con una casilla en Ajustes, la rejilla del profesor solo enseña
los recreos de los turnos con guardias y, si un turno no tiene profesorado
suficiente, se avisa antes de generar sin bloquear: se reparte lo posible.
"""

import json

import pytest
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Configuracion, Guardia, Profesor

pytestmark = pytest.mark.ui

SOLO_TARDE = json.dumps(
    [
        {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:00", "zonas": 2},
        {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "17:00", "zonas": 2},
    ]
)


def _todos_de_tarde(session):
    for p in session.query(Profesor).all():
        p.turno = "tarde"
        p.recreos_permitidos = None
    session.commit()


def _preflight(session):
    from application.use_cases.preflight_generacion import PreflightGeneracionUseCase

    return PreflightGeneracionUseCase(session).execute()


# ── Aviso de turnos sin profesorado ─────────────────────────────────────────


def test_sin_profesorado_de_manana_avisa_pero_deja_generar(session, curso_generable):
    _todos_de_tarde(session)
    estado = _preflight(session)
    assert estado.listo, "se reparte lo posible: no bloquea"
    detalle = " ".join(r.detalle for r in estado.avisos)
    assert "ningún profesor de mañana" in detalle
    assert "desmarca «Hay guardias de mañana»" in detalle


def test_con_pocos_mixtos_avisa_de_huecos_todos_los_dias(session, curso_generable):
    _todos_de_tarde(session)
    session.query(Profesor).first().turno = "mixto"
    session.commit()
    detalle = " ".join(r.detalle for r in _preflight(session).avisos)
    assert "solo 1 profesores pueden hacerlas" in detalle, (
        "con un mixto para 2 recreos × 2 zonas de mañana quedan huecos cada día"
    )


def test_sin_recreos_de_manana_no_hay_aviso(session, curso_generable):
    from services.calculador_guardias import turnos_con_recreos

    _todos_de_tarde(session)
    config = session.query(Configuracion).first()
    config.recreos_config = SOLO_TARDE
    session.commit()
    assert turnos_con_recreos(config) == (False, True)
    assert _preflight(session).avisos == []


def test_con_huecos_se_reparte_lo_demas(session, curso_generable):
    """La generación no se cancela: guarda lo de tarde aunque la mañana no tenga a nadie."""
    from application.use_cases.asignacion_guardias.generar_guardias import (
        GenerarGuardiasUseCase,
    )

    _todos_de_tarde(session)
    resumen = GenerarGuardiasUseCase(session).execute()
    assert resumen.slots_sin_cubrir > 0
    assert resumen.guardias_generadas > 0
    assert session.query(Guardia).filter_by(turno="tarde").count() == resumen.guardias_generadas


# ── Ajustes ─────────────────────────────────────────────────────────────────


@pytest.fixture
def ajustes(qapp, session, curso_generable):
    from presentation.forms.ajustes_form import AjustesForm

    form = AjustesForm(session)
    QApplication.processEvents()
    yield form
    form.close()


def test_desmarcar_la_manana_deja_solo_los_recreos_de_tarde(ajustes):
    from PyQt6.QtCore import QTime

    w = ajustes.fechas_recreos_widget
    w.grupo_manana.setChecked(False)
    # Sin guardias de mañana, sus horas no se validan: antes «00:00 y 00:00» no se podía guardar.
    w.recreo1_manana_input.setTime(QTime(0, 0))
    w.recreo2_manana_input.setTime(QTime(0, 0))
    assert w.validar() == (True, "")
    recreos = json.loads(ajustes._generar_recreos_config_json())
    assert [r["id"] for r in recreos] == [3, 4], "los ids de tarde no cambian (rejillas guardadas)"
    assert {r["turno"] for r in recreos} == {"tarde"}


def test_sin_ningun_turno_no_se_puede_guardar(ajustes):
    w = ajustes.fechas_recreos_widget
    w.grupo_manana.setChecked(False)
    w.grupo_tarde.setChecked(False)
    valido, mensaje = w.validar()
    assert not valido and "al menos un turno" in mensaje


def test_al_cargar_las_casillas_reflejan_lo_guardado(qapp, session, curso_generable):
    from presentation.forms.ajustes_form import AjustesForm

    session.query(Configuracion).first().recreos_config = SOLO_TARDE
    session.commit()
    form = AjustesForm(session)
    w = form.fechas_recreos_widget
    assert not w.hay_recreos_manana() and w.hay_recreos_tarde()
    form.close()


# ── Rejilla de recreos del profesor ─────────────────────────────────────────


def test_la_rejilla_solo_ensena_los_recreos_de_los_turnos_con_guardias(qapp):
    from presentation.forms.profesor_widgets.restricciones_widget import (
        SemanaRestriccionesWidget,
    )

    rejilla = SemanaRestriccionesWidget([1, 2, 3, 4])
    rejilla.set_restricciones_dias({d: [1, 2, 3, 4] for d in range(5)})
    rejilla.set_turnos_con_recreos(False, True)

    assert rejilla._celdas[(0, 1)].isHidden() and rejilla._etiquetas[2].isHidden()
    assert not rejilla._celdas[(0, 3)].isHidden()
    assert rejilla._plantillas["Solo mañanas"].isHidden()
    assert rejilla._plantillas["Solo tardes"].isHidden()

    rejilla._aplicar_plantilla({})  # «Ninguno»
    assert rejilla.get_restricciones_dias() == {d: [1, 2] for d in range(5)}, (
        "las filas ocultas conservan su valor por si el turno vuelve a tener guardias"
    )

    rejilla.set_turnos_con_recreos(True, True)
    assert not rejilla._celdas[(0, 1)].isHidden()
    assert not rejilla._plantillas["Solo mañanas"].isHidden()
    rejilla.close()


# ── Panel de generación ─────────────────────────────────────────────────────


def test_el_panel_deja_generar_y_avisa_antes_de_los_huecos(qapp, session, curso_generable):
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    _todos_de_tarde(session)
    panel = GeneracionPanel(session)
    QApplication.processEvents()
    assert panel.generar_button.isEnabled()
    assert not panel.label_bloqueo.isHidden()
    assert "quedarán huecos" in panel.label_bloqueo.text()
    assert "ningún profesor de mañana" in panel.label_bloqueo.text()
    panel.close()


# ── Calendario ──────────────────────────────────────────────────────────────


def test_el_calendario_solo_pinta_los_recreos_guardados(session, curso_generable):
    """Leía la configuración como entidad (recreos en lista), `json.loads` fallaba en
    silencio y se inventaba los recreos a partir de las cuatro horas de Ajustes: los de
    mañana salían «sin guardia asignada» y tapaban las guardias de tarde (2026-10-06)."""
    from datetime import date

    from presentation.widgets.vista_calendario_helpers import (
        obtener_zonas_esperadas_por_recreo,
    )

    session.query(Configuracion).first().recreos_config = SOLO_TARDE
    session.commit()
    claves = sorted(obtener_zonas_esperadas_por_recreo(session, date(2025, 9, 16)))
    assert claves == [("tarde", 3), ("tarde", 4)]
