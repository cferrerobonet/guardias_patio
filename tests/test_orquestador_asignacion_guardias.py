"""Tests de orquestación de asignación con fallback."""

import sys
import types
from datetime import date, time
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# El módulo orquestador importa desde "src.services.*" (ruta absoluta no estándar).
# Inyectamos stubs mínimos para poder importar y luego parchear en cada test.
if "src.services.asignador_iterativo" not in sys.modules:
    m = types.ModuleType("src.services.asignador_iterativo")
    m.AsignadorIterativo = object
    sys.modules["src.services.asignador_iterativo"] = m

if "src.services.calculador_guardias" not in sys.modules:
    m = types.ModuleType("src.services.calculador_guardias")
    m._parse_recreos_config = lambda _cfg: []
    sys.modules["src.services.calculador_guardias"] = m

if "src.services.diagnosticador_guardias" not in sys.modules:
    m = types.ModuleType("src.services.diagnosticador_guardias")
    m.DiagnosticadorGuardias = object
    m.DiagnosticoCompleto = object
    sys.modules["src.services.diagnosticador_guardias"] = m

if "src.services.validador_guardias" not in sys.modules:
    m = types.ModuleType("src.services.validador_guardias")
    m.ValidadorGuardias = object
    sys.modules["src.services.validador_guardias"] = m

from services.orquestador_asignacion_guardias import (
    EstrategiaUsada,
    OrquestadorAsignacionGuardias,
    ResultadoOrquestacion,
)


def _diagnostico(cobertura=100.0, criticos=0, altos=0, medios=0):
    return SimpleNamespace(
        mensaje_resumen="resumen",
        estadisticas={
            "cobertura_porcentaje": cobertura,
            "total_guardias_asignadas": 10,
            "total_slots_esperados": 10,
            "profesores_con_guardias": 5,
            "profesores_activos_totales": 5,
        },
        problemas_criticos=["x"] * criticos,
        problemas_altos=["x"] * altos,
        problemas_medios=["x"] * medios,
    )


def _build_orquestador(parse_recreos_return=None, zonas=None):
    config = MagicMock()
    config.hora_recreo1_manana = time(10, 30)
    config.hora_recreo2_manana = time(12, 0)
    config.hora_recreo1_tarde = None
    config.hora_recreo2_tarde = None

    db = MagicMock()
    db.query.return_value.all.return_value = zonas or [MagicMock()]

    with (
        patch("services.orquestador_asignacion_guardias._parse_recreos_config", return_value=parse_recreos_return or []),
        patch("services.orquestador_asignacion_guardias.AsignadorIterativo") as p_iter,
        patch("services.orquestador_asignacion_guardias.DiagnosticadorGuardias") as p_diag,
        patch("services.orquestador_asignacion_guardias.ValidadorGuardias"),
    ):
        p_iter.return_value = MagicMock()
        p_diag.return_value = MagicMock()
        orch = OrquestadorAsignacionGuardias(db, config, [date(2025, 10, 1)])

    return orch


class TestOrquestadorConfig:
    def test_enriquecer_configuracion_fallback_recreos(self):
        orch = _build_orquestador(parse_recreos_return=[])
        assert len(orch.config.recreos) == 2
        assert orch.config.recreos[0].numero == orch.config.recreos[0].id
        assert len(orch.config.zonas) == 1

    def test_enriquecer_configuracion_from_parse(self):
        recreos = [{"id": 7, "turno": "mañana", "zonas": 2}]
        orch = _build_orquestador(parse_recreos_return=recreos)
        assert len(orch.config.recreos) == 1
        assert orch.config.recreos[0].id == 7
        assert orch.config.recreos[0].numero == 7


class TestOrquestadorFlow:
    def test_iterativo_aceptable(self):
        orch = _build_orquestador()
        orch.asignador_iterativo.generar_guardias_iterativo.return_value = ([MagicMock()], {"iteracion_exitosa": 2})
        orch.diagnosticador.diagnosticar_resultado.return_value = _diagnostico(cobertura=100.0, criticos=0)

        result = orch.generar_guardias_con_fallback()

        assert isinstance(result, ResultadoOrquestacion)
        assert result.exitoso is True
        assert result.estrategia_usada == EstrategiaUsada.ITERATIVO
        assert result.requiere_intervencion_usuario is False

    def test_iterativo_no_aceptable_sin_callback(self):
        orch = _build_orquestador()
        orch.asignador_iterativo.generar_guardias_iterativo.return_value = ([MagicMock()], {"x": 1})
        orch.diagnosticador.diagnosticar_resultado.return_value = _diagnostico(cobertura=70.0, criticos=1)

        result = orch.generar_guardias_con_fallback(umbral_cobertura_minima=0.95)

        assert result.exitoso is False
        assert result.requiere_intervencion_usuario is True
        assert "REQUIERE SU ATENCIÓN" in result.mensaje_usuario

    def test_decision_ajustar(self):
        orch = _build_orquestador()
        orch.asignador_iterativo.generar_guardias_iterativo.return_value = ([MagicMock()], {"x": 1})
        orch.diagnosticador.diagnosticar_resultado.return_value = _diagnostico(cobertura=70.0, criticos=1)

        result = orch.generar_guardias_con_fallback(callback_decision_usuario=lambda _d: "ajustar")

        assert result.exitoso is False
        assert result.requiere_intervencion_usuario is True
        assert "ajuste la configuración" in result.mensaje_usuario

    def test_decision_cancelar(self):
        orch = _build_orquestador()
        orch.asignador_iterativo.generar_guardias_iterativo.return_value = ([MagicMock()], {"x": 1})
        orch.diagnosticador.diagnosticar_resultado.return_value = _diagnostico(cobertura=60.0, criticos=1)

        result = orch.generar_guardias_con_fallback(callback_decision_usuario=lambda _d: "cancelar")

        assert result.exitoso is False
        assert result.estrategia_usada == EstrategiaUsada.NINGUNA
        assert result.guardias == []

    def test_decision_timeout(self):
        orch = _build_orquestador()
        orch.asignador_iterativo.generar_guardias_iterativo.return_value = ([MagicMock()], {"x": 1})
        orch.diagnosticador.diagnosticar_resultado.return_value = _diagnostico(cobertura=60.0, criticos=1)

        result = orch.generar_guardias_con_fallback(callback_decision_usuario=lambda _d: "timeout")

        assert result.exitoso is False
        assert result.estrategia_usada == EstrategiaUsada.NINGUNA
        assert "no recibió respuesta" in result.mensaje_usuario

    def test_decision_callback_exception_maps_to_error(self):
        orch = _build_orquestador()
        orch.asignador_iterativo.generar_guardias_iterativo.return_value = ([MagicMock()], {"x": 1})
        orch.diagnosticador.diagnosticar_resultado.return_value = _diagnostico(cobertura=60.0, criticos=1)

        def _boom(_d):
            raise RuntimeError("boom")

        result = orch.generar_guardias_con_fallback(callback_decision_usuario=_boom)

        assert result.exitoso is False
        assert result.estrategia_usada == EstrategiaUsada.NINGUNA
        assert "error" in result.mensaje_usuario.lower()

    def test_decision_continuar_ilp_delega(self):
        orch = _build_orquestador()
        orch.asignador_iterativo.generar_guardias_iterativo.return_value = ([MagicMock()], {"x": 1})
        diag = _diagnostico(cobertura=60.0, criticos=1)
        orch.diagnosticador.diagnosticar_resultado.return_value = diag

        fake_result = ResultadoOrquestacion(
            exitoso=True,
            guardias=[MagicMock()],
            estrategia_usada=EstrategiaUsada.ILP,
            diagnostico=diag,
            metadatos={},
            requiere_intervencion_usuario=False,
            mensaje_usuario="ok",
        )

        with patch.object(orch, "_ejecutar_fase_ilp", return_value=fake_result) as p_ilp:
            result = orch.generar_guardias_con_fallback(callback_decision_usuario=lambda _d: "continuar_ilp")

        p_ilp.assert_called_once()
        assert result.estrategia_usada == EstrategiaUsada.ILP


class TestOrquestadorILPAndMessages:
    def test_ejecutar_fase_ilp_import_error_fallback(self):
        orch = _build_orquestador()
        result = orch._ejecutar_fase_ilp([MagicMock()], _diagnostico(), {"x": 1})

        assert result.exitoso is False
        assert result.estrategia_usada == EstrategiaUsada.ITERATIVO
        assert "ILP no disponible" in result.mensaje_usuario

    def test_generar_mensaje_exito_iterativo(self):
        orch = _build_orquestador()
        msg = orch._generar_mensaje_exito(EstrategiaUsada.ITERATIVO, _diagnostico(), {"iteracion_exitosa": 3})
        assert "ASIGNACIÓN COMPLETADA" in msg
        assert "Iteración exitosa" in msg

    def test_generar_mensaje_exito_ilp(self):
        orch = _build_orquestador()
        msg = orch._generar_mensaje_exito(EstrategiaUsada.ILP, _diagnostico(), {"tiempo_solucion": 1.2})
        assert "ILP" in msg
        assert "Tiempo de cálculo" in msg

    def test_generar_mensaje_intervencion(self):
        orch = _build_orquestador()
        diag = _diagnostico(cobertura=50.0, criticos=2, altos=1)
        msg = orch._generar_mensaje_requiere_intervencion(diag)
        assert "problema(s) crítico(s)" in msg
        assert "algoritmo ILP" in msg
