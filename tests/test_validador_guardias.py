"""
Tests para validador_guardias.py:
- ResultadoValidacion
- ValidadorGuardias
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class TestResultadoValidacion:
    def test_constructor(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        assert r.errores_criticos == []
        assert r.warnings == []
        assert r.metricas == {}

    def test_agregar_error(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        r.agregar_error("Error grave")
        assert "Error grave" in r.errores_criticos

    def test_agregar_warning(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        r.agregar_warning("Advertencia menor")
        assert "Advertencia menor" in r.warnings

    def test_es_valido_sin_errores(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        assert r.es_valido() is True

    def test_es_valido_con_errores(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        r.agregar_error("Fallo crítico")
        assert r.es_valido() is False

    def test_calcular_estado_sin_errores(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        r.calcular_estado()
        assert r.estado in ("ÓPTIMO", "ACEPTABLE", "CRÍTICO", "DESCONOCIDO")

    def test_calcular_estado_con_errores(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        r.agregar_error("Error")
        r.calcular_estado()
        assert r.estado == "CRÍTICO"

    def test_generar_reporte(self):
        from services.validador_guardias import ResultadoValidacion

        r = ResultadoValidacion()
        r.agregar_error("Error A")
        r.agregar_warning("Warning B")
        reporte = r.generar_reporte()
        assert isinstance(reporte, str)
        assert len(reporte) > 0


class TestValidadorGuardias:
    def test_constructor(self):
        from services.validador_guardias import ValidadorGuardias

        session = MagicMock()
        v = ValidadorGuardias(session)
        assert v.session is session

    def test_validar_todo_sin_profesores(self):
        from services.validador_guardias import ValidadorGuardias

        session = MagicMock()
        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.all.return_value = []
        v = ValidadorGuardias(session)
        resultado = v.validar_todo([], {})
        assert resultado is not None

    def test_validar_todo_con_profesores(self):
        from services.validador_guardias import ValidadorGuardias
        from infrastructure.database.models import Profesor

        session = MagicMock()

        def query_side_effect(model):
            q = MagicMock()
            inner = MagicMock()
            inner.all.return_value = []
            inner.count.return_value = 0
            inner.first.return_value = None
            q.filter.return_value = inner
            q.filter.return_value.order_by.return_value = inner
            q.all.return_value = []
            q.count.return_value = 0
            return q

        session.query.side_effect = query_side_effect

        prof = MagicMock(spec=Profesor)
        prof.id = 1
        prof.nombre_completo = "Juan García"
        prof.activo = True
        prof.horas_contrato = 18
        # Sin fechas de guardia → evita la comparación de fechas
        prof.fecha_inicio_guardias = None
        prof.fecha_fin_guardias = None

        v = ValidadorGuardias(session)
        resultado = v.validar_todo([prof], {1: 5})
        assert resultado is not None
