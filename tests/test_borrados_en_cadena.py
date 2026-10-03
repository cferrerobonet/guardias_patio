"""Borrar profesores, zonas y cursos con las claves foráneas activas, como en la app.

Un profesor con ausencias, una zona que era la preferida de alguien o un curso
referenciado por la configuración no se podían borrar: el error que veía el
usuario era el de SQLite (2026-10-03).
"""

from datetime import date, time

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from application.use_cases.profesor.eliminar_profesor import EliminarProfesorUseCase
from application.use_cases.zona.eliminar_zona import EliminarZonaUseCase
from infrastructure.database.models import (
    Ausencia,
    Base,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)
from services.gestor_cursos import GestorCursos


@pytest.fixture
def bd():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _claves_foraneas(conexion, _):
        conexion.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine)()
    yield sesion
    sesion.close()


def _profesor(bd, nombre, **campos):
    profesor = Profesor(
        nombre_completo=nombre, horas_contrato=20, porcentaje_jornada=66, turno="mañana",
        **campos,
    )
    bd.add(profesor)
    bd.commit()
    return profesor


def test_un_profesor_con_ausencias_se_borra_con_ellas(bd):
    x = _profesor(bd, "X, A")
    bd.add(Ausencia(profesor_id=x.id, fecha_inicio=date(2026, 10, 5),
                    fecha_fin=date(2026, 10, 5), tipo="otros"))
    bd.commit()
    EliminarProfesorUseCase(bd).execute(x.id)
    assert bd.query(Profesor).count() == 0
    assert bd.query(Ausencia).count() == 0


def test_un_profesor_sustituido_se_borra_y_la_guardia_se_queda(bd):
    zona = Zona(nombre_zona="A")
    bd.add(zona)
    bd.commit()
    x, y = _profesor(bd, "X, A"), _profesor(bd, "Y, B")
    guardia = Guardia(profesor_id=y.id, fecha=date(2026, 10, 5), turno="mañana", recreo=1,
                      zona_id=zona.id, es_sustitucion=True, profesor_sustituido_id=x.id)
    bd.add(guardia)
    bd.commit()
    EliminarProfesorUseCase(bd).execute(x.id)
    bd.expire_all()
    assert bd.get(Guardia, guardia.id).profesor_id == y.id


def test_una_zona_preferida_se_borra_y_el_profesor_queda_sin_preferencia(bd):
    zona = Zona(nombre_zona="A")
    bd.add(zona)
    bd.commit()
    x = _profesor(bd, "X, A", zona_preferida_id=zona.id)
    EliminarZonaUseCase(bd).execute(zona.id)
    bd.expire_all()
    assert bd.query(Zona).count() == 0
    assert bd.get(Profesor, x.id).zona_preferida_id is None


def test_un_curso_referenciado_se_borra_y_se_sueltan_las_referencias(bd):
    curso = CursoEscolar(anio_inicio=2024, anio_fin=2025, fecha_inicio=date(2024, 9, 1),
                         fecha_fin=date(2025, 6, 30), nombre="Curso 2024/2025", activo=True,
                         cerrado=False)
    bd.add(curso)
    bd.commit()
    config = Configuracion(anio_inicio_curso=2024, fecha_inicio_curso=date(2024, 9, 1),
                           fecha_fin_curso=date(2025, 6, 30), hora_recreo1_manana=time(11),
                           hora_recreo2_manana=time(12), curso_activo_id=curso.id)
    bd.add(config)
    bd.commit()
    x = _profesor(bd, "X, A", curso_id=curso.id)

    assert GestorCursos.from_session(bd).eliminar_curso(curso.id)
    bd.expire_all()
    assert bd.query(CursoEscolar).count() == 0
    assert bd.get(Configuracion, config.id).curso_activo_id is None
    assert bd.get(Profesor, x.id).curso_id is None
