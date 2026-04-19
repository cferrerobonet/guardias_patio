"""
Tests para services/migrar_a_multi_curso.py — migración automática al sistema Multi-Curso.
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.database.models import CursoEscolar, Guardia, Profesor, Zona
from services.migrar_a_multi_curso import (
    MigradorMultiCurso,
    ejecutar_migracion_si_necesario,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_profesor(session):
    p = Profesor(
        nombre_completo="Profe Migracion",
        horas_contrato=18.0,
        porcentaje_jornada=100.0,
        turno="mañana",
        activo=True,
    )
    session.add(p)
    session.flush()
    return p


def _make_zona(session):
    z = Zona(nombre_zona="Patio")
    session.add(z)
    session.flush()
    return z


def _make_guardia_huerfana(session, profesor_id, zona_id, fecha):
    """Crea una guardia sin curso_id (huérfana)."""
    g = Guardia(
        profesor_id=profesor_id,
        fecha=fecha,
        turno="mañana",
        recreo=1,
        zona_id=zona_id,
        curso_id=None,
    )
    session.add(g)
    session.flush()
    return g


# ─────────────────────────────────────────────────────────────────────────────
# necesita_migracion
# ─────────────────────────────────────────────────────────────────────────────


class TestNecesitaMigracion:
    def test_false_sin_guardias_huerfanas(self, session):
        assert MigradorMultiCurso.necesita_migracion(session) is False

    def test_true_con_guardias_huerfanas(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        _make_guardia_huerfana(session, p.id, z.id, date(2025, 10, 1))
        assert MigradorMultiCurso.necesita_migracion(session) is True


# ─────────────────────────────────────────────────────────────────────────────
# detectar_anio_curso_desde_guardias
# ─────────────────────────────────────────────────────────────────────────────


class TestDetectarAnioCurso:
    def test_none_sin_guardias(self, session):
        result = MigradorMultiCurso.detectar_anio_curso_desde_guardias(session)
        assert result is None

    def test_detecta_anio_inicio_desde_guardias_sep_dic(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        # Guardias en Sep-Nov 2025 → curso 2025
        for d in [date(2025, 9, 10), date(2025, 10, 5), date(2025, 11, 20)]:
            _make_guardia_huerfana(session, p.id, z.id, d)
        anio = MigradorMultiCurso.detectar_anio_curso_desde_guardias(session)
        assert anio == 2025

    def test_detecta_anio_inicio_desde_guardias_ene_ago(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        # Guardias en Jan-Jun 2026 → curso empezó en 2025
        for d in [date(2026, 1, 10), date(2026, 2, 5), date(2026, 3, 20)]:
            _make_guardia_huerfana(session, p.id, z.id, d)
        anio = MigradorMultiCurso.detectar_anio_curso_desde_guardias(session)
        assert anio == 2025


# ─────────────────────────────────────────────────────────────────────────────
# crear_curso_desde_guardias
# ─────────────────────────────────────────────────────────────────────────────


class TestCrearCursoDesdeGuardias:
    def test_crea_curso_con_anio_especificado(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        _make_guardia_huerfana(session, p.id, z.id, date(2025, 9, 10))
        curso = MigradorMultiCurso.crear_curso_desde_guardias(session, anio_inicio=2025)
        assert curso is not None
        assert curso.anio_inicio == 2025

    def test_crea_curso_detectando_anio_automaticamente(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        for d in [date(2024, 10, 5), date(2024, 11, 10)]:
            _make_guardia_huerfana(session, p.id, z.id, d)
        curso = MigradorMultiCurso.crear_curso_desde_guardias(session)
        assert curso.anio_inicio == 2024

    def test_reutiliza_curso_existente(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        _make_guardia_huerfana(session, p.id, z.id, date(2025, 9, 10))
        # Crear curso previamente
        from services.gestor_cursos import GestorCursos

        curso_existente = GestorCursos.crear_nuevo_curso(
            session, anio_inicio=2025, activar=False, copiar_profesores=False
        )
        session.flush()
        # crear_curso_desde_guardias debe devolver el existente
        curso = MigradorMultiCurso.crear_curso_desde_guardias(session, anio_inicio=2025)
        assert curso.id == curso_existente.id

    def test_error_si_no_hay_guardias_y_sin_anio(self, session):
        with pytest.raises(ValueError, match="No se pudo determinar"):
            MigradorMultiCurso.crear_curso_desde_guardias(session)


# ─────────────────────────────────────────────────────────────────────────────
# asignar_guardias_a_curso
# ─────────────────────────────────────────────────────────────────────────────


class TestAsignarGuardiasACurso:
    def test_asigna_todas_las_guardias_huerfanas(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        from services.gestor_cursos import GestorCursos

        curso = GestorCursos.crear_nuevo_curso(
            session, anio_inicio=2025, activar=False, copiar_profesores=False
        )
        session.flush()
        _make_guardia_huerfana(session, p.id, z.id, date(2025, 10, 1))
        _make_guardia_huerfana(session, p.id, z.id, date(2025, 11, 1))
        n = MigradorMultiCurso.asignar_guardias_a_curso(session, curso.id)
        assert n == 2

    def test_asigna_solo_guardias_del_anio_indicado(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        from services.gestor_cursos import GestorCursos

        curso = GestorCursos.crear_nuevo_curso(
            session, anio_inicio=2025, activar=False, copiar_profesores=False
        )
        session.flush()
        _make_guardia_huerfana(session, p.id, z.id, date(2025, 10, 1))  # 2025/26
        _make_guardia_huerfana(session, p.id, z.id, date(2024, 10, 1))  # 2024/25
        n = MigradorMultiCurso.asignar_guardias_a_curso(session, curso.id, anio_inicio=2025)
        assert n == 1


# ─────────────────────────────────────────────────────────────────────────────
# migrar_automaticamente
# ─────────────────────────────────────────────────────────────────────────────


class TestMigrarAutomaticamente:
    def test_no_migracion_sin_huerfanas(self, session):
        resultado = MigradorMultiCurso.migrar_automaticamente(session)
        assert resultado["necesitaba_migracion"] is False
        assert resultado["guardias_migradas"] == 0

    def test_migracion_completa(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        for d in [date(2025, 9, 10), date(2025, 10, 5), date(2025, 11, 1)]:
            _make_guardia_huerfana(session, p.id, z.id, d)
        resultado = MigradorMultiCurso.migrar_automaticamente(session)
        assert resultado["necesitaba_migracion"] is True
        assert resultado["guardias_migradas"] == 3
        assert resultado["curso_id"] is not None

    def test_migracion_con_curso_existente(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        from services.gestor_cursos import GestorCursos

        curso = GestorCursos.crear_nuevo_curso(
            session, anio_inicio=2025, activar=False, copiar_profesores=False
        )
        session.flush()
        _make_guardia_huerfana(session, p.id, z.id, date(2025, 9, 10))
        resultado = MigradorMultiCurso.migrar_automaticamente(session)
        assert resultado["necesitaba_migracion"] is True
        assert resultado["curso_creado"] is False
        assert resultado["curso_id"] == curso.id


# ─────────────────────────────────────────────────────────────────────────────
# migrar_interactivo
# ─────────────────────────────────────────────────────────────────────────────


class TestMigrarInteractivo:
    def test_crea_curso_si_no_existe(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        _make_guardia_huerfana(session, p.id, z.id, date(2023, 10, 1))
        resultado = MigradorMultiCurso.migrar_interactivo(session, anio_inicio=2023)
        assert resultado["curso_creado"] is True
        assert resultado["guardias_migradas"] == 1

    def test_usa_curso_existente(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        from services.gestor_cursos import GestorCursos

        curso = GestorCursos.crear_nuevo_curso(
            session, anio_inicio=2022, activar=False, copiar_profesores=False
        )
        session.flush()
        _make_guardia_huerfana(session, p.id, z.id, date(2022, 10, 1))
        resultado = MigradorMultiCurso.migrar_interactivo(session, anio_inicio=2022)
        assert resultado["curso_creado"] is False
        assert resultado["curso_id"] == curso.id

    def test_error_si_no_existe_y_no_crear(self, session):
        with pytest.raises(ValueError, match="(?i)no existe"):
            MigradorMultiCurso.migrar_interactivo(
                session, anio_inicio=2099, crear_si_no_existe=False
            )


# ─────────────────────────────────────────────────────────────────────────────
# ejecutar_migracion_si_necesario
# ─────────────────────────────────────────────────────────────────────────────


class TestEjecutarMigracionSiNecesario:
    def test_false_sin_huerfanas(self, session):
        assert ejecutar_migracion_si_necesario(session) is False

    def test_true_con_huerfanas(self, session):
        p = _make_profesor(session)
        z = _make_zona(session)
        for d in [date(2025, 10, 1), date(2025, 11, 1)]:
            _make_guardia_huerfana(session, p.id, z.id, d)
        result = ejecutar_migracion_si_necesario(session)
        assert result is True
