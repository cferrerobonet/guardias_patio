"""Tests para vinculación Profesor.curso_id y GestorCursos.copiar_profesores_curso_anterior."""

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.database.models import Base, CursoEscolar, Profesor
from services.gestor_cursos import GestorCursos


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


@pytest.fixture()
def cursos(session):
    """Crea dos cursos escolares."""
    from datetime import date

    c1 = CursoEscolar(
        anio_inicio=2024,
        anio_fin=2025,
        nombre="Curso 2024/2025",
        fecha_inicio=date(2024, 9, 1),
        fecha_fin=date(2025, 6, 30),
        activo=False,
        cerrado=True,
    )
    c2 = CursoEscolar(
        anio_inicio=2025,
        anio_fin=2026,
        nombre="Curso 2025/2026",
        fecha_inicio=date(2025, 9, 1),
        fecha_fin=date(2026, 6, 30),
        activo=True,
        cerrado=False,
    )
    session.add_all([c1, c2])
    session.commit()
    return c1, c2


@pytest.fixture()
def profesores_curso_anterior(session, cursos):
    """Crea dos profesores en el curso anterior."""
    c1, _ = cursos
    p1 = Profesor(
        nombre_completo="GARCÍA LÓPEZ, ANA",
        email_corporativo="ana.garcia@colegio.es",
        horas_contrato=18.0,
        porcentaje_jornada=100.0,
        turno="mañana",
        activo=True,
        curso_id=c1.id,
    )
    p2 = Profesor(
        nombre_completo="MARTÍNEZ RUIZ, JUAN",
        email_corporativo="juan.martinez@colegio.es",
        horas_contrato=12.0,
        porcentaje_jornada=66.6,
        turno="tarde",
        activo=True,
        curso_id=c1.id,
    )
    session.add_all([p1, p2])
    session.commit()
    return p1, p2


# ──────────────────────────────────────────────────────────────────────────────
# Tests modelo ORM — curso_id
# ──────────────────────────────────────────────────────────────────────────────


class TestProfesorCursoId:
    def test_profesor_tiene_campo_curso_id(self, session, cursos):
        c1, _ = cursos
        prof = Profesor(
            nombre_completo="TEST, PROFESOR",
            horas_contrato=18.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            activo=True,
            curso_id=c1.id,
        )
        session.add(prof)
        session.commit()
        session.refresh(prof)
        assert prof.curso_id == c1.id

    def test_profesor_sin_curso_id_es_none(self, session):
        prof = Profesor(
            nombre_completo="SIN CURSO, PROFESOR",
            horas_contrato=18.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            activo=True,
        )
        session.add(prof)
        session.commit()
        session.refresh(prof)
        assert prof.curso_id is None

    def test_profesor_relacion_curso(self, session, cursos):
        c1, _ = cursos
        prof = Profesor(
            nombre_completo="REL, PROFESOR",
            horas_contrato=18.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            activo=True,
            curso_id=c1.id,
        )
        session.add(prof)
        session.commit()
        session.refresh(prof)
        assert prof.curso is not None
        assert prof.curso.nombre == "Curso 2024/2025"

    def test_filtrar_profesores_por_curso(self, session, cursos, profesores_curso_anterior):
        c1, c2 = cursos
        # Añadir un profesor al curso nuevo
        prof_nuevo = Profesor(
            nombre_completo="NUEVO, PROFESOR",
            email_corporativo="nuevo@colegio.es",
            horas_contrato=18.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            activo=True,
            curso_id=c2.id,
        )
        session.add(prof_nuevo)
        session.commit()

        profs_c1 = session.query(Profesor).filter(Profesor.curso_id == c1.id).all()
        profs_c2 = session.query(Profesor).filter(Profesor.curso_id == c2.id).all()

        assert len(profs_c1) == 2
        assert len(profs_c2) == 1


# ──────────────────────────────────────────────────────────────────────────────
# Tests GestorCursos.copiar_profesores_curso_anterior
# ──────────────────────────────────────────────────────────────────────────────


class TestCopiarProfesoresCursoAnterior:
    def test_copia_todos_los_profesores(self, session, cursos, profesores_curso_anterior):
        _, c2 = cursos
        copiados = GestorCursos.copiar_profesores_curso_anterior(session, c2.id)
        assert copiados == 2
        profs_c2 = session.query(Profesor).filter(Profesor.curso_id == c2.id).all()
        assert len(profs_c2) == 2

    def test_copiados_tienen_curso_id_nuevo(self, session, cursos, profesores_curso_anterior):
        _, c2 = cursos
        GestorCursos.copiar_profesores_curso_anterior(session, c2.id)
        profs = session.query(Profesor).filter(Profesor.curso_id == c2.id).all()
        for p in profs:
            assert p.curso_id == c2.id

    def test_no_duplica_si_ya_existe_en_curso_nuevo(self, session, cursos, profesores_curso_anterior):
        c1, c2 = cursos
        # Añadir uno de los profesores ya al curso nuevo
        prof_dup = Profesor(
            nombre_completo="GARCÍA LÓPEZ, ANA",
            email_corporativo="ana.garcia@colegio.es",
            horas_contrato=18.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            activo=True,
            curso_id=c2.id,
        )
        session.add(prof_dup)
        session.commit()

        copiados = GestorCursos.copiar_profesores_curso_anterior(session, c2.id)
        assert copiados == 1  # Solo copia el segundo

    def test_copia_datos_basicos_correctamente(self, session, cursos, profesores_curso_anterior):
        _, c2 = cursos
        GestorCursos.copiar_profesores_curso_anterior(session, c2.id)
        prof = (
            session.query(Profesor)
            .filter(
                Profesor.curso_id == c2.id,
                Profesor.email_corporativo == "ana.garcia@colegio.es",
            )
            .first()
        )
        assert prof is not None
        assert prof.nombre_completo == "GARCÍA LÓPEZ, ANA"
        assert prof.horas_contrato == 18.0
        assert prof.turno == "mañana"

    def test_curso_sin_profesores_anteriores_devuelve_cero(self, session, cursos):
        _, c2 = cursos
        # c2 no tiene curso anterior con profesores
        copiados = GestorCursos.copiar_profesores_curso_anterior(session, c2.id)
        assert copiados == 0

    def test_error_si_curso_nuevo_no_existe(self, session):
        with pytest.raises(ValueError, match="No existe el curso"):
            GestorCursos.copiar_profesores_curso_anterior(session, 9999)
