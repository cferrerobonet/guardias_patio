"""
Tests para EstadisticasService y ValidadorGuardias.
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infrastructure.database.models import Base, Guardia, Profesor, Zona
from services.estadisticas_service import EstadisticasService
from services.validador_guardias import ResultadoValidacion, ValidadorGuardias


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _guardia(profesor_id: int, fecha: date, zona_id: int = 1, turno: str = "mañana", recreo: int = 1) -> MagicMock:
    g = MagicMock(spec=Guardia)
    g.profesor_id = profesor_id
    g.fecha = fecha
    g.zona_id = zona_id
    g.turno = turno
    g.recreo = recreo
    return g


def _profesor(pid: int, activo: bool = True, turno: str = "mañana") -> MagicMock:
    p = MagicMock(spec=Profesor)
    p.id = pid
    p.activo = activo
    p.turno = turno
    p.nombre_completo = f"Profesor {pid}"
    p.porcentaje_jornada = 100.0
    p.fecha_inicio_guardias = None
    p.fecha_fin_guardias = None
    return p


# ─────────────────────────────────────────────────────────────────────────────
# ResultadoValidacion — sin BD
# ─────────────────────────────────────────────────────────────────────────────


class TestResultadoValidacion:
    def test_sin_errores_es_valido(self):
        r = ResultadoValidacion()
        assert r.es_valido() is True

    def test_con_error_no_es_valido(self):
        r = ResultadoValidacion()
        r.agregar_error("Error crítico")
        assert r.es_valido() is False

    def test_calcular_estado_optimo(self):
        r = ResultadoValidacion()
        r.calcular_estado()
        assert r.estado == "ÓPTIMO"

    def test_calcular_estado_critico(self):
        r = ResultadoValidacion()
        r.agregar_error("error")
        r.calcular_estado()
        assert r.estado == "CRÍTICO"

    def test_calcular_estado_aceptable(self):
        r = ResultadoValidacion()
        for i in range(6):
            r.agregar_warning(f"warning {i}")
        r.calcular_estado()
        assert r.estado == "ACEPTABLE"

    def test_generar_reporte_con_errores(self):
        r = ResultadoValidacion()
        r.agregar_error("Error grave")
        r.calcular_estado()
        reporte = r.generar_reporte()
        assert "ERRORES CRÍTICOS" in reporte
        assert "Error grave" in reporte

    def test_generar_reporte_vacio(self):
        r = ResultadoValidacion()
        r.calcular_estado()
        reporte = r.generar_reporte()
        assert "ÓPTIMO" in reporte


# ─────────────────────────────────────────────────────────────────────────────
# EstadisticasService — puro (listas, sin BD)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def session_stats():
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    conn = eng.connect()
    txn = conn.begin()
    sess = sessionmaker(bind=conn)()
    yield sess
    sess.close()
    conn.close()


class TestEstadisticasService:
    @pytest.fixture(autouse=True)
    def setup(self, session_stats):
        self.svc = EstadisticasService(session_stats)

    def test_calcular_guardias_por_profesor(self):
        guardias = [
            _guardia(1, date(2025, 10, 1)),
            _guardia(1, date(2025, 10, 2)),
            _guardia(2, date(2025, 10, 1)),
        ]
        result = self.svc.calcular_guardias_por_profesor(guardias)
        assert result[1] == 2
        assert result[2] == 1

    def test_calcular_guardias_por_profesor_vacio(self):
        assert self.svc.calcular_guardias_por_profesor([]) == {}

    def test_calcular_cobertura(self):
        assert self.svc.calcular_cobertura(50, 100) == 0.5

    def test_calcular_cobertura_slots_cero(self):
        assert self.svc.calcular_cobertura(0, 0) == 0.0

    def test_calcular_cobertura_completa(self):
        assert self.svc.calcular_cobertura(100, 100) == 1.0

    def test_calcular_participacion(self):
        guardias = [_guardia(1, date(2025, 10, 1)), _guardia(2, date(2025, 10, 1))]
        result = self.svc.calcular_participacion(guardias, 4)
        assert result == 0.5

    def test_calcular_participacion_sin_profesores(self):
        assert self.svc.calcular_participacion([], 0) == 0.0

    def test_calcular_promedio_guardias(self):
        guardias = [
            _guardia(1, date(2025, 10, 1)),
            _guardia(1, date(2025, 10, 2)),
            _guardia(2, date(2025, 10, 1)),
        ]
        result = self.svc.calcular_promedio_guardias(guardias)
        assert result == 1.5  # 3 guardias / 2 profesores

    def test_calcular_promedio_guardias_vacio(self):
        assert self.svc.calcular_promedio_guardias([]) == 0.0

    def test_calcular_desviacion_cuotas(self):
        guardias = [_guardia(1, date(2025, 10, 1)), _guardia(1, date(2025, 10, 2))]
        cuotas = {1: 2, 2: 2}
        promedio, maxima = self.svc.calcular_desviacion_cuotas(guardias, cuotas)
        assert promedio >= 0
        assert maxima >= 0

    def test_calcular_desviacion_cuotas_vacias(self):
        assert self.svc.calcular_desviacion_cuotas([], {}) == (0.0, 0.0)

    def test_calcular_balance_equilibrado(self):
        guardias = [_guardia(1, date(2025, 10, d)) for d in range(1, 4)] + \
                   [_guardia(2, date(2025, 10, d)) for d in range(1, 4)]
        result = self.svc.calcular_balance(guardias)
        assert result == 0.0  # perfecto equilibrio

    def test_calcular_balance_vacio(self):
        assert self.svc.calcular_balance([]) == 0.0

    def test_identificar_profesores_sin_guardias(self):
        guardias = [_guardia(1, date(2025, 10, 1))]
        profesores = [_profesor(1), _profesor(2)]
        sin_guardias = self.svc.identificar_profesores_sin_guardias(guardias, profesores)
        assert len(sin_guardias) == 1
        assert sin_guardias[0].id == 2

    def test_identificar_profesores_sin_guardias_todos_tienen(self):
        guardias = [_guardia(1, date(2025, 10, 1)), _guardia(2, date(2025, 10, 1))]
        profesores = [_profesor(1), _profesor(2)]
        assert self.svc.identificar_profesores_sin_guardias(guardias, profesores) == []

    def test_calcular_guardias_por_fecha(self):
        d1 = date(2025, 10, 1)
        d2 = date(2025, 10, 2)
        guardias = [_guardia(1, d1), _guardia(2, d1), _guardia(1, d2)]
        result = self.svc.calcular_guardias_por_fecha(guardias)
        assert result[d1] == 2
        assert result[d2] == 1

    def test_calcular_guardias_por_zona(self):
        guardias = [_guardia(1, date(2025, 10, 1), zona_id=10), _guardia(2, date(2025, 10, 1), zona_id=10), _guardia(1, date(2025, 10, 2), zona_id=20)]
        result = self.svc.calcular_guardias_por_zona(guardias)
        assert result[10] == 2
        assert result[20] == 1

    def test_detectar_conflictos_mismo_dia(self):
        d = date(2025, 10, 1)
        guardias = [_guardia(1, d), _guardia(1, d), _guardia(2, d)]
        conflictos = self.svc.detectar_profesores_con_multiples_guardias_mismo_dia(guardias)
        assert len(conflictos) == 1
        assert conflictos[0][0] == 1
        assert conflictos[0][2] == 2

    def test_generar_resumen_completo_con_cuotas_y_slots(self):
        guardias = [_guardia(1, date(2025, 10, 1), zona_id=10), _guardia(1, date(2025, 10, 1), zona_id=20), _guardia(2, date(2025, 10, 2), zona_id=10)]
        profesores = [_profesor(1), _profesor(2), _profesor(3)]
        resumen = self.svc.generar_resumen_completo(
            guardias=guardias,
            profesores=profesores,
            cuotas={1: 2, 2: 2, 3: 1},
            total_slots=5,
        )
        assert resumen["total_guardias"] == 3
        assert resumen["profesores_sin_guardias"] == 1
        assert "cobertura_porcentaje" in resumen
        assert "participacion_porcentaje" in resumen
        assert "desviacion_promedio" in resumen
        assert "guardias_por_fecha" in resumen
        assert "guardias_por_zona" in resumen

    def test_generar_resumen_completo_sin_guardias(self):
        resumen = self.svc.generar_resumen_completo(guardias=[], profesores=[_profesor(1)], cuotas=None)
        assert resumen["total_guardias"] == 0
        assert resumen["min_guardias"] == 0
        assert resumen["max_guardias"] == 0

    def test_log_resumen(self):
        resumen = {
            "total_guardias": 3,
            "profesores_con_guardias": 2,
            "total_profesores": 3,
            "participacion_porcentaje": 66.7,
            "cobertura_porcentaje": 75.0,
            "promedio_guardias": 1.5,
            "min_guardias": 1,
            "max_guardias": 2,
            "desviacion_promedio": 0.1,
            "balance": 0.25,
            "profesores_sin_guardias": 1,
            "conflictos_mismo_dia": 1,
        }
        from unittest.mock import patch

        with patch("services.estadisticas_service.logger") as log:
            self.svc.log_resumen(resumen)
        assert log.info.called
        assert log.warning.called
        assert log.error.called


# ─────────────────────────────────────────────────────────────────────────────
# ValidadorGuardias — con BD SQLite en memoria
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine_val():
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session_val(engine_val) -> Session:
    conn = engine_val.connect()
    txn = conn.begin()
    sess = sessionmaker(bind=conn)()
    yield sess
    sess.rollback()
    sess.close()
    if txn.is_active:
        txn.rollback()
    conn.close()


class TestValidadorGuardias:
    def test_validar_todo_sin_guardias(self, session_val):
        """Sin guardias → todos los profesores aparecen como sin guardia."""
        prof1 = Profesor(nombre_completo="García", activo=True, turno="mañana", horas_contrato=25.0, porcentaje_jornada=100.0)
        session_val.add(prof1)
        session_val.flush()

        validador = ValidadorGuardias(session_val)
        resultado = validador.validar_todo([prof1], {prof1.id: 2})

        assert resultado.es_valido() is False
        assert "García" in " ".join(resultado.errores_criticos)
        assert resultado.estado == "CRÍTICO"

    def test_validar_todo_con_guardias(self, session_val):
        """Con guardias para todos los profesores → válido."""
        prof = Profesor(nombre_completo="López", activo=True, turno="mañana", horas_contrato=25.0, porcentaje_jornada=100.0)
        zona = Zona(nombre_zona="Patio")
        session_val.add_all([prof, zona])
        session_val.flush()

        guardia = Guardia(profesor_id=prof.id, zona_id=zona.id, fecha=date(2025, 10, 15), turno="mañana", recreo=1)
        session_val.add(guardia)
        session_val.flush()

        validador = ValidadorGuardias(session_val)
        resultado = validador.validar_todo([prof], {prof.id: 1})

        # No debería haber error de "sin guardias"
        errores_sin_guardia = [e for e in resultado.errores_criticos if "sin guardias" in e.lower()]
        assert len(errores_sin_guardia) == 0

    def test_reporte_generado(self, session_val):
        validador = ValidadorGuardias(session_val)
        resultado = validador.validar_todo([], {})
        reporte = resultado.generar_reporte()
        assert "REPORTE" in reporte
        assert len(reporte) > 0
