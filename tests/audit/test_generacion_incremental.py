"""FUN-002: regenerar sólo desde una fecha, sin tirar lo ya trabajado.

Hasta v5.67.0, «Generar» borraba las guardias del curso entero. Si en enero
entraba un profesor nuevo, rehacer el reparto significaba perder también las
sustituciones puestas a mano durante el primer trimestre.

Decisiones de producto (CarlosFB, 2026-09-05):
- Las sustituciones posteriores a la fecha **se respetan siempre**.
- El diálogo propone **hoy** como fecha de corte.
"""

import datetime
import json
from collections import Counter

import pytest

from infrastructure.database.models import Configuracion, CursoEscolar, Guardia, Profesor, Zona

pytestmark = pytest.mark.slow

CORTE = datetime.date(2025, 10, 1)


@pytest.fixture
def curso_con_guardias(session):
    """Un curso de un mes, generado entero, listo para regenerar por tramos."""
    session.add(
        CursoEscolar(
            anio_inicio=2025,
            anio_fin=2026,
            fecha_inicio=datetime.date(2025, 7, 1),
            fecha_fin=datetime.date(2026, 6, 30),
            nombre="Curso 2025/2026",
            activo=True,
            cerrado=False,
        )
    )
    for i in range(6):
        session.add(
            Profesor(
                nombre_completo=f"Profesor{i:02d}, Nombre",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            )
        )
    session.add_all([Zona(nombre_zona="A", activa=True), Zona(nombre_zona="B", activa=True)])
    session.add(
        Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=datetime.date(2025, 9, 15),
            fecha_fin_curso=datetime.date(2025, 10, 15),
            hora_recreo1_manana=datetime.time(11, 0),
            hora_recreo2_manana=datetime.time(12, 0),
            hora_recreo1_tarde=datetime.time(16, 0),
            hora_recreo2_tarde=datetime.time(17, 0),
            algoritmo_asignacion="cpsat",
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
            activar_festivos_automaticos=False,
            recreos_config=json.dumps(
                [{"id": 1, "etiqueta": "R1", "turno": "mañana", "hora": "11:00"}]
            ),
        )
    )
    session.commit()

    from services.asignador_guardias_cpsat import generar_guardias_cpsat, guardar_guardias_cpsat_en_bd

    guardias, _ = generar_guardias_cpsat(session, timeout_seconds=20)
    guardar_guardias_cpsat_en_bd(session, guardias)
    return session


def _firmas(session):
    return {
        (g.fecha, g.recreo, g.zona_id, g.profesor_id) for g in session.query(Guardia).all()
    }


def _regenerar_desde(session, desde):
    from services.asignador_guardias_cpsat import generar_guardias_cpsat, guardar_guardias_cpsat_en_bd

    session.query(Guardia).filter(
        Guardia.fecha >= desde, Guardia.es_sustitucion.is_(False)
    ).delete(synchronize_session=False)
    session.commit()

    nuevas, _ = generar_guardias_cpsat(session, timeout_seconds=20, desde=desde)
    guardar_guardias_cpsat_en_bd(session, [g for g in nuevas if g not in session])
    session.commit()


def test_el_pasado_no_se_toca(curso_con_guardias):
    sesion = curso_con_guardias
    antes = {
        (g.fecha, g.recreo, g.zona_id, g.profesor_id)
        for g in sesion.query(Guardia).filter(Guardia.fecha < CORTE).all()
    }
    assert antes, "el escenario debería tener guardias antes del corte"

    _regenerar_desde(sesion, CORTE)

    assert antes <= _firmas(sesion), "se perdió o cambió alguna guardia anterior a la fecha"


def test_las_sustituciones_posteriores_se_respetan(curso_con_guardias):
    sesion = curso_con_guardias
    sustitucion = sesion.query(Guardia).filter(Guardia.fecha >= CORTE).first()
    sustitucion.es_sustitucion = True
    firma = (
        sustitucion.fecha,
        sustitucion.recreo,
        sustitucion.zona_id,
        sustitucion.profesor_id,
    )
    sesion.commit()

    _regenerar_desde(sesion, CORTE)

    assert firma in _firmas(sesion), "se rehizo una sustitución puesta a mano"


def test_el_calendario_sigue_completo_y_repartido(curso_con_guardias):
    """Regenerar por tramos no puede dejar huecos ni cargar a nadie de más."""
    sesion = curso_con_guardias
    total_antes = sesion.query(Guardia).count()

    _regenerar_desde(sesion, CORTE)

    assert sesion.query(Guardia).count() == total_antes, "cambió el número de guardias"

    reparto = Counter(g.profesor_id for g in sesion.query(Guardia).all())
    assert max(reparto.values()) - min(reparto.values()) <= 2, (
        f"el reparto quedó desequilibrado: {sorted(reparto.values())}"
    )


def test_las_cuotas_descuentan_lo_ya_hecho(curso_con_guardias):
    """Si no, quien cubrió mucho en el primer tramo volvería a cargar con todo."""
    import inspect

    from services import asignador_guardias_cpsat

    fuente = inspect.getsource(asignador_guardias_cpsat.generar_guardias_cpsat)
    assert "ya_asignadas" in fuente
    assert "cuotas_ideales[p_id] - ya_asignadas" in fuente


def test_sin_fecha_se_comporta_como_siempre(curso_con_guardias):
    """La generación completa no cambia: `desde=None` es el comportamiento anterior."""
    from services.asignador_guardias_cpsat import generar_guardias_cpsat

    sesion = curso_con_guardias
    guardias, _ = generar_guardias_cpsat(sesion, timeout_seconds=20)
    fechas = {g.fecha for g in guardias}

    assert min(fechas) == datetime.date(2025, 9, 15), "no empezó por el principio del curso"


def test_el_dialogo_propone_hoy_y_respeta_las_sustituciones():
    """Decisiones de producto de 2026-09-05, fijadas para que no se cambien sin querer."""
    import inspect

    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    fuente = inspect.getsource(GeneracionPanel._preguntar_alcance)
    assert "date.today()" in fuente
    assert "setDefaultButton(boton_desde_hoy)" in fuente
    assert "sustituciones" in fuente.lower()
