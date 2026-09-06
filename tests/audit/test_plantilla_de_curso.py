"""FUN-005 — arrancar un curso a partir del anterior.

Cada septiembre había que teclear otra vez el claustro entero y volver a marcar
las fechas no lectivas: la casilla de copiar profesores llevaba deshabilitada
desde que se creó. Aquí se fija qué se hereda y qué no.

Zonas, recreos y ajustes de reparto no aparecen: son únicos para toda la
aplicación, así que el curso nuevo ya los tiene.
"""

import datetime

import pytest

from infrastructure.database.models import Configuracion, CursoEscolar, Profesor
from services.gestor_cursos import GestorCursos


def _curso(anio, **kwargs):
    return CursoEscolar(
        anio_inicio=anio,
        anio_fin=anio + 1,
        fecha_inicio=datetime.date(anio, 9, 1),
        fecha_fin=datetime.date(anio + 1, 6, 30),
        nombre=f"{anio}/{anio + 1}",
        activo=kwargs.get("activo", False),
        cerrado=False,
    )


@pytest.fixture
def curso_anterior(session):
    """Curso 2025/2026 activo, con tres profesores y días no lectivos a mano."""
    curso = _curso(2025, activo=True)
    session.add(curso)
    session.commit()
    session.add_all(
        [
            Profesor(
                nombre_completo=f"Apellido{i}, Nombre",
                email_corporativo=f"p{i}@epla.es" if i < 2 else None,
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=i == 0,
                activo=True,
                curso_id=curso.id,
            )
            for i in range(3)
        ]
    )
    session.add(
        Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=datetime.date(2025, 9, 1),
            fecha_fin_curso=datetime.date(2026, 6, 30),
            hora_recreo1_manana=datetime.time(11, 0),
            hora_recreo2_manana=datetime.time(12, 0),
            dias_no_lectivos_personalizados="2025-12-24,2026-03-19,2026-08-15",
            curso_activo_id=curso.id,
        )
    )
    session.commit()
    return curso


def test_el_claustro_pasa_al_curso_nuevo(session, curso_anterior):
    gestor = GestorCursos.from_session(session)
    nuevo = gestor.crear_nuevo_curso(anio_inicio=2026)

    resumen = gestor.preparar_curso_nuevo(nuevo.id, trasladar_no_lectivos=False)

    assert resumen["profesores"] == 3
    copiados = session.query(Profesor).filter_by(curso_id=nuevo.id).all()
    assert {p.nombre_completo for p in copiados} == {
        "Apellido0, Nombre",
        "Apellido1, Nombre",
        "Apellido2, Nombre",
    }


def test_los_profesores_sin_correo_se_copian_todos(session, curso_anterior):
    """Filtrar por un correo vacío los agrupaba a todos en uno y perdía el resto."""
    session.query(Profesor).filter(Profesor.email_corporativo.isnot(None)).delete(
        synchronize_session=False
    )
    session.commit()

    gestor = GestorCursos.from_session(session)
    nuevo = gestor.crear_nuevo_curso(anio_inicio=2026)
    gestor.preparar_curso_nuevo(nuevo.id, trasladar_no_lectivos=False)

    assert session.query(Profesor).filter_by(curso_id=nuevo.id).count() == 1

    otro = Profesor(
        nombre_completo="Sincorreo, Segundo",
        horas_contrato=25.0,
        porcentaje_jornada=100.0,
        turno="mañana",
        tutor=False,
        activo=True,
        curso_id=curso_anterior.id,
    )
    session.add(otro)
    session.commit()

    tercero = gestor.crear_nuevo_curso(anio_inicio=2027)
    gestor.preparar_curso_nuevo(
        tercero.id, curso_anterior_id=curso_anterior.id, trasladar_no_lectivos=False
    )
    assert session.query(Profesor).filter_by(curso_id=tercero.id).count() == 2


def test_copiar_dos_veces_no_duplica(session, curso_anterior):
    gestor = GestorCursos.from_session(session)
    nuevo = gestor.crear_nuevo_curso(anio_inicio=2026)

    gestor.preparar_curso_nuevo(nuevo.id, trasladar_no_lectivos=False)
    segundo = gestor.preparar_curso_nuevo(nuevo.id, trasladar_no_lectivos=False)

    assert segundo["profesores"] == 0
    assert session.query(Profesor).filter_by(curso_id=nuevo.id).count() == 3


def test_los_dias_no_lectivos_se_desplazan_un_anio(session, curso_anterior):
    gestor = GestorCursos.from_session(session)
    nuevo = gestor.crear_nuevo_curso(anio_inicio=2026)

    resumen = gestor.preparar_curso_nuevo(nuevo.id, copiar_profesores=False)

    config = session.query(Configuracion).first()
    assert config.dias_no_lectivos_personalizados == "2026-12-24,2027-03-19"
    assert resumen["trasladados"] == 2
    assert resumen["descartados"] == 1  # 2027-08-15 cae en verano, fuera del curso


def test_sin_curso_anterior_no_hereda_nada(session):
    gestor = GestorCursos.from_session(session)
    primero = gestor.crear_nuevo_curso(anio_inicio=2025)

    resumen = gestor.preparar_curso_nuevo(primero.id)

    assert resumen["hubo_anterior"] is False
    assert resumen["profesores"] == 0


def test_activar_un_curso_mueve_las_fechas_de_la_configuracion(session, curso_anterior):
    """Sin esto la generación seguía usando el rango del curso viejo."""
    gestor = GestorCursos.from_session(session)
    nuevo = gestor.crear_nuevo_curso(anio_inicio=2026)

    gestor.activar_curso(nuevo.id)

    config = session.query(Configuracion).first()
    assert config.curso_activo_id == nuevo.id
    assert config.anio_inicio_curso == 2026
    assert config.fecha_inicio_curso == datetime.date(2026, 9, 1)
    assert config.fecha_fin_curso == datetime.date(2027, 6, 30)


def test_el_29_de_febrero_no_rompe_el_traslado(session, curso_anterior):
    config = session.query(Configuracion).first()
    config.dias_no_lectivos_personalizados = "2024-02-29"
    session.commit()

    gestor = GestorCursos.from_session(session)
    nuevo = gestor.crear_nuevo_curso(anio_inicio=2026)
    resumen = gestor.preparar_curso_nuevo(nuevo.id, copiar_profesores=False)

    assert resumen["descartados"] == 1
    assert session.query(Configuracion).first().dias_no_lectivos_personalizados == ""
