"""Tests para services/diagnosticador_guardias.py."""
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services.diagnosticador_guardias import (
    DiagnosticoCompleto,
    DiagnosticadorGuardias,
    ProblemaDetectado,
)


def _cfg():
    recreos = [SimpleNamespace(numero=1, turno="mañana"), SimpleNamespace(numero=2, turno="tarde")]
    zonas = [SimpleNamespace(id=1, nombre="Patio A"), SimpleNamespace(id=2, nombre="Patio B")]
    return SimpleNamespace(recreos=recreos, zonas=zonas)


def _diag(db=None, dias=None):
    if db is None:
        db = MagicMock()
    if dias is None:
        dias = [date(2024, 9, 2), date(2024, 9, 3)]
    return DiagnosticadorGuardias(db=db, config=_cfg(), dias_lectivos=dias)


class TestSugestionesYResumen:
    def test_generar_sugerencias_profesores_con_causas(self):
        d = _diag()
        causas = {
            "slots_insuficientes": True,
            "ausencias_excesivas": [{"nombre": "A"}],
            "incompatibilidades_zona": [{"nombre": "B"}],
            "sin_disponibilidad_turno": ["C"],
        }
        s = d._generar_sugerencias_profesores_sin_guardias(causas, "mañana")
        assert len(s) >= 3
        assert any("CRÍTICO" in x for x in s)

    def test_generar_sugerencias_profesores_sin_causas(self):
        d = _diag()
        causas = {
            "slots_insuficientes": False,
            "ausencias_excesivas": [],
            "incompatibilidades_zona": [],
            "sin_disponibilidad_turno": [],
        }
        s = d._generar_sugerencias_profesores_sin_guardias(causas, "mañana")
        assert len(s) == 1
        assert "No se detectaron" in s[0]

    def test_generar_sugerencias_slots_vacios(self):
        d = _diag()
        huecos = {
            "por_turno": {"mañana": 5, "tarde": 2},
            "por_zona": {"Patio A": 4, "Patio B": 3},
            "dias_criticos": [("2024-09-02", 5), ("2024-09-03", 4)],
        }
        s = d._generar_sugerencias_slots_vacios(huecos)
        assert len(s) == 3

    def test_generar_mensaje_resumen_con_criticos(self):
        d = _diag()
        crit = [ProblemaDetectado("x", "CRITICA", "Problema crítico", {}, [])]
        msg = d._generar_mensaje_resumen(crit, [], [], {
            "total_guardias_asignadas": 3,
            "total_slots_esperados": 10,
            "cobertura_porcentaje": 30.0,
            "profesores_con_guardias": 1,
            "profesores_activos_totales": 4,
        })
        assert "PROBLEMAS CRÍTICOS" in msg
        assert "impiden una asignación válida" in msg

    def test_generar_mensaje_resumen_sin_problemas(self):
        d = _diag()
        msg = d._generar_mensaje_resumen([], [], [], {
            "total_guardias_asignadas": 10,
            "total_slots_esperados": 10,
            "cobertura_porcentaje": 100.0,
            "profesores_con_guardias": 4,
            "profesores_activos_totales": 4,
        })
        assert "asignación es aceptable" in msg


class TestAnalisisInterno:
    def test_analizar_slots_vacios_detalle(self):
        d = _diag(dias=[date(2024, 9, 2)])
        # 1 día * 2 recreos * 2 zonas = 4 slots esperados
        guardias = [SimpleNamespace(fecha=date(2024, 9, 2), recreo=1, zona=1)]
        detalle = d._analizar_slots_vacios_detalle(guardias)
        assert sum(detalle["por_turno"].values()) == 3
        assert "Patio A" in detalle["por_zona"] or "Patio B" in detalle["por_zona"]
        assert len(detalle["dias_criticos"]) >= 1

    def test_calcular_estadisticas(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 5
        d = _diag(db=db, dias=[date(2024, 9, 2)])
        guardias = [SimpleNamespace(profesor_id=1), SimpleNamespace(profesor_id=2)]
        stats = d._calcular_estadisticas(guardias)
        assert stats["total_guardias_asignadas"] == 2
        assert stats["profesores_activos_totales"] == 5
        assert stats["cobertura_porcentaje"] >= 0

    def test_diagnosticar_slots_vacios_con_huecos(self):
        d = _diag(dias=[date(2024, 9, 2)])
        d._analizar_slots_vacios_detalle = MagicMock(
            return_value={"por_turno": {"mañana": 1}, "por_zona": {"Patio A": 1}, "dias_criticos": []}
        )
        guardias = [SimpleNamespace(fecha=date(2024, 9, 2), recreo=1, zona=1)]
        problemas = d._diagnosticar_slots_vacios(guardias)
        assert len(problemas) == 1
        assert problemas[0].tipo == "slots_vacios"

    def test_diagnosticar_slots_vacios_sin_huecos(self):
        d = _diag(dias=[date(2024, 9, 2)])
        # cubrir 4 slots
        guardias = [
            SimpleNamespace(fecha=date(2024, 9, 2), recreo=1, zona=1),
            SimpleNamespace(fecha=date(2024, 9, 2), recreo=1, zona=2),
            SimpleNamespace(fecha=date(2024, 9, 2), recreo=2, zona=1),
            SimpleNamespace(fecha=date(2024, 9, 2), recreo=2, zona=2),
        ]
        problemas = d._diagnosticar_slots_vacios(guardias)
        assert problemas == []

    def test_diagnosticar_desbalances(self):
        d = _diag()
        guardias = [
            SimpleNamespace(zona="A"),
            SimpleNamespace(zona="A"),
            SimpleNamespace(zona="A"),
            SimpleNamespace(zona="B"),
        ]
        problemas = d._diagnosticar_desbalances(guardias)
        assert len(problemas) == 1
        assert problemas[0].tipo == "desbalance_zonas"

    def test_analizar_causas_sin_guardias(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 10
        d = _diag(db=db, dias=[date(2024, 9, 2)])
        # slots_disponibles = 1 día * 1 recreo mañana * 2 zonas = 2 < 10
        p1 = SimpleNamespace(nombre_completo="P1", turno="tarde", ausencias=[1, 2, 3])
        causas = d._analizar_causas_sin_guardias([p1], "mañana")
        assert causas["slots_insuficientes"] is True
        assert "P1" in causas["sin_disponibilidad_turno"]


class TestOrquestacionDiagnostico:
    def test_diagnosticar_resultado_orquesta_todo(self):
        d = _diag()
        d._diagnosticar_profesores_sin_guardias = MagicMock(return_value=[ProblemaDetectado("a", "CRITICA", "a", {}, [])])
        d._diagnosticar_slots_vacios = MagicMock(return_value=[])
        d._diagnosticar_fechas_inicio = MagicMock(return_value=[])
        d._diagnosticar_cuotas_incompletas = MagicMock(return_value=[])
        d._diagnosticar_desbalances = MagicMock(return_value=[])
        d._calcular_estadisticas = MagicMock(return_value={
            "total_guardias_asignadas": 1,
            "total_slots_esperados": 2,
            "cobertura_porcentaje": 50.0,
            "profesores_con_guardias": 1,
            "profesores_activos_totales": 2,
        })
        d._generar_mensaje_resumen = MagicMock(return_value="ok")

        res = d.diagnosticar_resultado([SimpleNamespace(profesor_id=1)])
        assert isinstance(res, DiagnosticoCompleto)
        assert res.puede_continuar_ilp is True
        assert res.mensaje_resumen == "ok"

    def test_diagnosticar_cuotas_incompletas(self, monkeypatch):
        d = _diag()
        db_prof = SimpleNamespace(nombre_completo="Prof X")
        d.db.query.return_value.get.return_value = db_prof

        import services.calculador_guardias as calc
        monkeypatch.setattr(calc, "calcular_guardias_por_profesor", lambda _db: {1: 10})

        problemas = d._diagnosticar_cuotas_incompletas([SimpleNamespace(profesor_id=1)])
        assert len(problemas) == 1
        assert problemas[0].tipo == "cuota_incompleta"

    def test_diagnosticar_fechas_inicio(self):
        d = _diag()
        prof = SimpleNamespace(nombre_completo="Prof Y", fecha_inicio_guardias=date(2024, 9, 1))
        d.db.query.return_value.get.return_value = prof

        guardias = [SimpleNamespace(profesor_id=1, fecha=date(2024, 12, 1))]
        problemas = d._diagnosticar_fechas_inicio(guardias)
        assert len(problemas) == 1
        assert problemas[0].tipo == "fecha_inicio_incumplida"

    def test_diagnosticar_profesores_sin_guardias(self):
        d = _diag()
        p1 = SimpleNamespace(id=1, nombre_completo="P1", turno="mañana")
        p2 = SimpleNamespace(id=2, nombre_completo="P2", turno="completo")
        d.db.query.return_value.options.return_value.filter.return_value.all.return_value = [p1, p2]
        d._analizar_causas_sin_guardias = MagicMock(return_value={
            "slots_insuficientes": False,
            "ausencias_excesivas": [],
            "incompatibilidades_zona": [],
            "sin_disponibilidad_turno": [],
        })
        guardias = [SimpleNamespace(profesor_id=1)]
        problemas = d._diagnosticar_profesores_sin_guardias(guardias)
        assert len(problemas) >= 1
        assert all(p.tipo == "profesor_sin_guardias" for p in problemas)
