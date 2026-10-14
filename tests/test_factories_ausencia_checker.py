"""
Tests para application/factories.py y services/validators/ausencia_checker.py.
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.database.models import Ausencia, Profesor
from services.validators.ausencia_checker import AusenciaChecker


# ─────────────────────────────────────────────────────────────────────────────
# Factories
# ─────────────────────────────────────────────────────────────────────────────


class TestFactories:
    def _mock_session(self):
        return MagicMock()

    def test_crear_listar_profesores(self):
        from application.factories import crear_listar_profesores_use_case
        from application.use_cases.profesor.listar_profesores import ListarProfesoresUseCase

        uc = crear_listar_profesores_use_case(self._mock_session())
        assert isinstance(uc, ListarProfesoresUseCase)

    def test_crear_obtener_profesor(self):
        from application.factories import crear_obtener_profesor_use_case
        from application.use_cases.profesor.obtener_profesor import ObtenerProfesorUseCase

        uc = crear_obtener_profesor_use_case(self._mock_session())
        assert isinstance(uc, ObtenerProfesorUseCase)

    def test_crear_crear_profesor(self):
        from application.factories import crear_crear_profesor_use_case
        from application.use_cases.profesor.crear_profesor import CrearProfesorUseCase

        uc = crear_crear_profesor_use_case(self._mock_session())
        assert isinstance(uc, CrearProfesorUseCase)

    def test_crear_obtener_guardias(self):
        from application.factories import crear_obtener_guardias_use_case
        from application.use_cases.guardia.obtener_guardias import ObtenerGuardiasUseCase

        uc = crear_obtener_guardias_use_case(self._mock_session())
        assert isinstance(uc, ObtenerGuardiasUseCase)

    def test_crear_asignar_guardia(self):
        from application.factories import crear_asignar_guardia_use_case
        from application.use_cases.guardia.asignar_guardia import AsignarGuardiaUseCase

        uc = crear_asignar_guardia_use_case(self._mock_session())
        assert isinstance(uc, AsignarGuardiaUseCase)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures de BD
# ─────────────────────────────────────────────────────────────────────────────


def _make_profesor(session, nombre="Profe Test", activo=True):
    p = Profesor(
        nombre_completo=nombre,
        horas_contrato=18.0,
        porcentaje_jornada=100.0,
        turno="mañana",
        activo=activo,
    )
    session.add(p)
    session.flush()
    return p


def _make_ausencia(session, profesor_id, fecha_inicio, fecha_fin, tipo="baja_medica"):
    a = Ausencia(
        profesor_id=profesor_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipo=tipo,
    )
    session.add(a)
    session.flush()
    return a


# ─────────────────────────────────────────────────────────────────────────────
# AusenciaChecker — profesor_ausente / obtener_ausencia
# ─────────────────────────────────────────────────────────────────────────────


class TestAusenciaCheckerPresencia:
    def test_profesor_ausente_dentro_del_rango(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 10), date(2025, 11, 15))
        checker = AusenciaChecker(session)
        assert checker.profesor_ausente(p.id, date(2025, 11, 12)) is True

    def test_profesor_no_ausente_fuera_del_rango(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 10), date(2025, 11, 15))
        checker = AusenciaChecker(session)
        assert checker.profesor_ausente(p.id, date(2025, 12, 1)) is False

    def test_profesor_no_ausente_sin_ausencias(self, session):
        p = _make_profesor(session)
        checker = AusenciaChecker(session)
        assert checker.profesor_ausente(p.id, date(2025, 11, 12)) is False

    def test_obtener_ausencia_existente(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 10), date(2025, 11, 20))
        checker = AusenciaChecker(session)
        result = checker.obtener_ausencia(p.id, date(2025, 11, 15))
        assert result is not None
        assert result.profesor_id == p.id

    def test_obtener_ausencia_no_existente(self, session):
        p = _make_profesor(session)
        checker = AusenciaChecker(session)
        result = checker.obtener_ausencia(p.id, date(2025, 11, 15))
        assert result is None

    def test_limite_exacto_inicio(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 10), date(2025, 11, 15))
        checker = AusenciaChecker(session)
        assert checker.profesor_ausente(p.id, date(2025, 11, 10)) is True

    def test_limite_exacto_fin(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 10), date(2025, 11, 15))
        checker = AusenciaChecker(session)
        assert checker.profesor_ausente(p.id, date(2025, 11, 15)) is True


# ─────────────────────────────────────────────────────────────────────────────
# AusenciaChecker — profesores_ausentes_en_fecha
# ─────────────────────────────────────────────────────────────────────────────


class TestAusenciaCheckerListados:
    def test_profesores_ausentes_en_fecha(self, session):
        p1 = _make_profesor(session, "Profe1")
        p2 = _make_profesor(session, "Profe2")
        _make_ausencia(session, p1.id, date(2025, 11, 10), date(2025, 11, 20))
        checker = AusenciaChecker(session)
        ausentes = checker.profesores_ausentes_en_fecha(date(2025, 11, 15))
        ids = [p.id for p in ausentes]
        assert p1.id in ids
        assert p2.id not in ids

    def test_profesores_ausentes_filtrado_por_ids(self, session):
        p1 = _make_profesor(session, "Profe1")
        p2 = _make_profesor(session, "Profe2")
        _make_ausencia(session, p1.id, date(2025, 11, 10), date(2025, 11, 20))
        _make_ausencia(session, p2.id, date(2025, 11, 10), date(2025, 11, 20))
        checker = AusenciaChecker(session)
        ausentes = checker.profesores_ausentes_en_fecha(date(2025, 11, 15), profesor_ids=[p1.id])
        ids = [p.id for p in ausentes]
        assert p1.id in ids
        assert p2.id not in ids

    def test_profesores_ausentes_sin_ausencias_ninguno(self, session):
        _make_profesor(session, "Solo")
        checker = AusenciaChecker(session)
        ausentes = checker.profesores_ausentes_en_fecha(date(2025, 11, 15))
        assert ausentes == []

    def test_profesores_disponibles_excluye_ausentes(self, session):
        p_disp = _make_profesor(session, "Disponible")
        p_aus = _make_profesor(session, "Ausente")
        _make_ausencia(session, p_aus.id, date(2025, 11, 10), date(2025, 11, 20))
        checker = AusenciaChecker(session)
        disponibles = checker.profesores_disponibles_en_fecha(date(2025, 11, 15))
        ids = [p.id for p in disponibles]
        assert p_disp.id in ids
        assert p_aus.id not in ids

    def test_profesores_disponibles_solo_activos(self, session):
        p_activo = _make_profesor(session, "Activo", activo=True)
        p_inactivo = _make_profesor(session, "Inactivo", activo=False)
        checker = AusenciaChecker(session)
        disponibles_activos = checker.profesores_disponibles_en_fecha(
            date(2025, 11, 15), solo_activos=True
        )
        ids = [p.id for p in disponibles_activos]
        assert p_activo.id in ids
        assert p_inactivo.id not in ids

    def test_profesores_disponibles_incluye_inactivos_si_flag_false(self, session):
        p_activo = _make_profesor(session, "Activo", activo=True)
        p_inactivo = _make_profesor(session, "Inactivo", activo=False)
        checker = AusenciaChecker(session)
        todos = checker.profesores_disponibles_en_fecha(date(2025, 11, 15), solo_activos=False)
        ids = [p.id for p in todos]
        assert p_activo.id in ids
        assert p_inactivo.id in ids


# ─────────────────────────────────────────────────────────────────────────────
# AusenciaChecker — contar_ausencias_profesor
# ─────────────────────────────────────────────────────────────────────────────


class TestAusenciaCheckerContadores:
    def test_contar_sin_filtro(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 1), date(2025, 11, 5))
        _make_ausencia(session, p.id, date(2025, 12, 1), date(2025, 12, 3))
        checker = AusenciaChecker(session)
        assert checker.contar_ausencias_profesor(p.id) == 2

    def test_contar_con_filtro_fecha_inicio(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 10, 1), date(2025, 10, 5))
        _make_ausencia(session, p.id, date(2025, 12, 1), date(2025, 12, 3))
        checker = AusenciaChecker(session)
        count = checker.contar_ausencias_profesor(p.id, fecha_inicio=date(2025, 11, 1))
        assert count == 1  # Solo la de diciembre

    def test_contar_con_filtro_fecha_fin(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 10, 1), date(2025, 10, 5))
        _make_ausencia(session, p.id, date(2025, 12, 1), date(2025, 12, 3))
        checker = AusenciaChecker(session)
        count = checker.contar_ausencias_profesor(p.id, fecha_fin=date(2025, 11, 30))
        assert count == 1  # Solo la de octubre

    def test_contar_sin_ausencias(self, session):
        p = _make_profesor(session)
        checker = AusenciaChecker(session)
        assert checker.contar_ausencias_profesor(p.id) == 0


# ─────────────────────────────────────────────────────────────────────────────
# AusenciaChecker — dias_ausente_en_periodo / tiene_ausencias_futuras
# ─────────────────────────────────────────────────────────────────────────────


class TestAusenciaCheckerDias:
    def test_dias_ausente_en_periodo(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 10), date(2025, 11, 15))
        checker = AusenciaChecker(session)
        dias = checker.dias_ausente_en_periodo(p.id, date(2025, 11, 1), date(2025, 11, 30))
        assert dias == 6  # 10, 11, 12, 13, 14, 15

    def test_dias_ausente_recortado_por_periodo(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2025, 11, 5), date(2025, 11, 20))
        checker = AusenciaChecker(session)
        # Solo contamos del 10 al 15
        dias = checker.dias_ausente_en_periodo(p.id, date(2025, 11, 10), date(2025, 11, 15))
        assert dias == 6

    def test_dias_ausente_sin_ausencias(self, session):
        p = _make_profesor(session)
        checker = AusenciaChecker(session)
        dias = checker.dias_ausente_en_periodo(p.id, date(2025, 11, 1), date(2025, 11, 30))
        assert dias == 0

    def test_tiene_ausencias_futuras_true(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2030, 1, 1), date(2030, 1, 10))
        checker = AusenciaChecker(session)
        assert checker.tiene_ausencias_futuras(p.id, desde_fecha=date(2025, 1, 1)) is True

    def test_tiene_ausencias_futuras_false(self, session):
        p = _make_profesor(session)
        _make_ausencia(session, p.id, date(2020, 1, 1), date(2020, 1, 10))
        checker = AusenciaChecker(session)
        assert checker.tiene_ausencias_futuras(p.id, desde_fecha=date(2025, 1, 1)) is False

    def test_tiene_ausencias_futuras_sin_fecha_usa_hoy(self, session):
        p = _make_profesor(session)
        checker = AusenciaChecker(session)
        # Sin ausencias → False independientemente de la fecha
        assert checker.tiene_ausencias_futuras(p.id) is False
