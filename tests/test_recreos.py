"""Turno, número dentro del turno, etiqueta y hora de cada recreo (`services.recreos`).

Las guardias guardan el id global del recreo: con la lista de Ajustes, 1 y 2 de
mañana y 3 y 4 de tarde; sin ella, la numeración compacta del reparto. Hasta la
7.5.1 los PDF y el .ics leían el id como si fuera 1 o 2 de cada turno: la tarde
salía como «Recreo 3» sin hora y el .ics la dejaba fuera.
"""

import json
from datetime import date, time
from types import SimpleNamespace

import pytest

from infrastructure.database.models import Configuracion, CursoEscolar, Guardia, Profesor, Zona
from services import recreos
from services.icalendar_service import ICalendarService
from services.pdf_styles import abreviatura_zona, abreviaturas_de_zonas

HORAS = dict(
    hora_recreo1_manana=time(10, 30), hora_recreo2_manana=time(12, 20),
    hora_recreo1_tarde=time(16, 30), hora_recreo2_tarde=time(18, 30),
)
LISTA_DE_AJUSTES = [
    {"id": 1, "etiqueta": "Recreo 1 Mañana", "turno": "mañana", "hora": "10:30"},
    {"id": 2, "etiqueta": "Recreo 2 Mañana", "turno": "mañana", "hora": "12:20"},
    {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:30"},
    {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "18:30"},
]


def _config(lista=None, **horas):
    valores = {k: None for k in HORAS}
    valores.update(horas)
    return SimpleNamespace(recreos_config=json.dumps(lista) if lista else None, **valores)


# --- La función ------------------------------------------------------------------


class TestConListaDeAjustes:
    def test_los_recreos_de_tarde_son_el_3_y_el_4(self):
        config = _config(LISTA_DE_AJUSTES)

        r3 = recreos.resolver(config, 3, "tarde")
        r4 = recreos.resolver(config, 4, "tarde")

        assert (r3.turno, r3.ordinal, r3.hora_texto) == ("tarde", 1, "16:30")
        assert (r4.turno, r4.ordinal, r4.hora_texto) == ("tarde", 2, "18:30")
        assert r3.etiqueta_con_hora == "Recreo 1 de tarde · 16:30"
        assert (r3.corta, r3.codigo) == ("R1", "T1")

    def test_la_manana_sigue_igual(self):
        r = recreos.resolver(_config(LISTA_DE_AJUSTES), 2, "mañana")
        assert (r.turno, r.ordinal, r.hora_texto) == ("mañana", 2, "12:20")

    def test_sin_hora_en_la_lista_se_toma_la_del_campo(self):
        lista = [{"id": 3, "turno": "tarde"}]
        r = recreos.resolver(_config(lista, hora_recreo1_tarde=time(17, 0)), 3, "tarde")
        assert r.hora_texto == "17:00"

    def test_solo_tarde_conserva_los_ids_y_los_numeros(self):
        """Ajustes no renumera: sin recreos de mañana la tarde sigue siendo 3 y 4."""
        config = _config(LISTA_DE_AJUSTES[2:])
        assert [(r.id, r.ordinal) for r in recreos.recreos_de(config)] == [(3, 1), (4, 2)]


class TestSinLista:
    def test_numeracion_compacta_como_el_reparto(self):
        config = _config(**HORAS)

        lista = recreos.recreos_de(config)

        assert [(r.id, r.turno, r.ordinal) for r in lista] == [
            (1, "mañana", 1), (2, "mañana", 2), (3, "tarde", 1), (4, "tarde", 2),
        ]
        assert recreos.resolver(config, 4, "tarde").hora_texto == "18:30"

    def test_centro_solo_de_tarde_numera_desde_el_1(self):
        config = _config(hora_recreo1_tarde=time(16, 30), hora_recreo2_tarde=time(18, 30))

        r = recreos.resolver(config, 1, "tarde")

        assert (r.turno, r.ordinal, r.hora_texto) == ("tarde", 1, "16:30")

    def test_sin_configuracion_no_falla(self):
        r = recreos.resolver(None, 3, "tarde")
        assert (r.turno, r.ordinal, r.hora) == ("tarde", 1, None)
        assert r.etiqueta_con_hora == "Recreo 1 de tarde"


def test_datos_antiguos_numerados_dentro_del_turno():
    """Una guardia de tarde con recreo 1 (numeración antigua) sigue saliendo bien."""
    r = recreos.resolver(_config(LISTA_DE_AJUSTES), 1, "tarde")
    assert (r.turno, r.ordinal, r.hora_texto) == ("tarde", 1, "16:30")


# --- Zonas -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre, abreviatura",
    [("Z2", "Z2"), ("Gim", "Gim"), ("Patio Norte", "PN"), ("Patio 2", "P2"),
     ("Gimnasio", "GIM"), ("Porche y cafetería", "PC"), ("Jardín de atrás", "JA")],
)
def test_abreviatura_de_la_zona(nombre, abreviatura):
    assert abreviatura_zona(nombre) == abreviatura


def test_abreviaturas_repetidas_llevan_su_id():
    zonas = [SimpleNamespace(id=1, nombre_zona="Patio Norte"),
             SimpleNamespace(id=2, nombre_zona="Pista Nueva"),
             SimpleNamespace(id=3, nombre_zona="Z3")]
    assert abreviaturas_de_zonas(zonas) == {1: "PN1", 2: "PN2", 3: "Z3"}


# --- El .ics ---------------------------------------------------------------------


@pytest.fixture
def centro(session):
    curso = CursoEscolar(anio_inicio=2026, anio_fin=2027, fecha_inicio=date(2026, 9, 1),
                         fecha_fin=date(2027, 6, 30), nombre="Curso 2026/2027", activo=True)
    session.add(curso)
    session.flush()
    session.add(Configuracion(
        anio_inicio_curso=2026, fecha_inicio_curso=date(2026, 9, 1),
        fecha_fin_curso=date(2027, 6, 30), curso_activo_id=curso.id,
        recreos_config=json.dumps(LISTA_DE_AJUSTES), **HORAS,
    ))
    zona = Zona(nombre_zona="Z2", descripcion="Patio de prueba")
    profesor = Profesor(nombre_completo="Ficticio, Tarde", email_corporativo="tarde@example.com",
                        horas_contrato=25, porcentaje_jornada=100, turno="tarde",
                        activo=True, curso_id=curso.id)
    session.add_all([zona, profesor])
    session.flush()
    session.add_all([
        Guardia(curso_id=curso.id, profesor_id=profesor.id, fecha=date(2026, 10, 20),
                turno="tarde", recreo=3, zona_id=zona.id),
        Guardia(curso_id=curso.id, profesor_id=profesor.id, fecha=date(2026, 10, 22),
                turno="tarde", recreo=4, zona_id=zona.id),
    ])
    session.flush()
    return profesor


def test_el_ics_lleva_las_guardias_de_tarde_con_su_hora(session, centro, tmp_path):
    ruta = tmp_path / "tarde.ics"

    assert ICalendarService.generar_icalendar_profesor(session, centro.id, str(ruta))

    ics = ruta.read_text(encoding="utf-8")
    assert ics.count("BEGIN:VEVENT") == 2
    assert "DTSTART:20261020T163000" in ics
    assert "DTSTART:20261022T183000" in ics
    assert "Recreo 1 de tarde · 16:30" in ics


def test_el_correo_dice_el_recreo_de_tarde_con_su_hora(session, centro):
    from services.notificador_guardias import preparar_envios

    envio = next(e for e in preparar_envios(session, "Octubre 2026").envios
                 if e.profesor_id == centro.id)

    assert "Recreo 1 de tarde · 16:30" in envio.texto
    assert "Recreo 2 de tarde · 18:30" in envio.html
    assert "Recreo 3" not in envio.texto + envio.html


def test_la_rejilla_del_profesor_rotula_la_tarde_con_su_numero_y_su_hora(qapp):
    """La rejilla de restricciones ponía «R3» y «R4» para la tarde; el valor que
    guarda sigue siendo el id global."""
    from presentation.forms.profesor_widgets.restricciones_widget import RestriccionesWidget

    widget = RestriccionesWidget()
    rejilla = widget.semana_widget
    etiquetas = {r: lbl.text() for r, lbl in rejilla._etiquetas.items()}
    assert etiquetas == {1: "R1 mañana", 2: "R2 mañana", 3: "R1 tarde", 4: "R2 tarde"}

    widget.set_configuracion_recreos(SimpleNamespace(recreos_config=None, **HORAS))
    assert rejilla._etiquetas[3].toolTip() == "Recreo 1 de tarde · 16:30"
    assert "18:30" in rejilla._celdas[(0, 4)].toolTip()
    assert rejilla._celdas[(0, 4)].accessibleName() == "Recreo 2 de tarde del lunes"

    rejilla.set_restricciones_dias({0: [3]})
    assert rejilla.get_restricciones_dias() == {0: [3]}
    widget.deleteLater()
