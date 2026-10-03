"""
Tests de restricciones DURAS (R1–R9) × 2 algoritmos.

Umbrales:
  R1–R6, R9  : 100% ambos algoritmos
  R7 CP-SAT  : cubierto desde v6.7.0 (antes xfail: dias_semana no implementado)
  R8 CP-SAT  : 100%
"""

from __future__ import annotations

import pytest

from tests.compliance.scenarios import (
    scenario_S01,
    scenario_S02,
    scenario_S03,
    scenario_S04,
    scenario_S05,
    scenario_S06,
    scenario_S07,
    scenario_S08,
)
from tests.compliance.verifiers import ComplianceVerifier

pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_algo(algo, run_cpsat):
    return run_cpsat()


def _verifier(profesores, guardias, session) -> ComplianceVerifier:
    return ComplianceVerifier(profesores, guardias, session)


# ---------------------------------------------------------------------------
# R1 — Turno compatible
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r1_turno_s01(algo, session, build_scenario, run_cpsat, compliance_reporter):
    s = scenario_S01()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    verifier = _verifier(profesores, guardias, session)
    result = verifier.check_r1_turno()
    compliance_reporter.record(f"{s.nombre}_{algo}", algo, [result])

    assert result.total_evaluadas > 0, "No se generaron guardias"
    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R1 turno: {result.cumplimiento_pct:.1f}% — fallos: {result.fallos[:3]}"
    )


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r1_turno_s02(algo, session, build_scenario, run_cpsat):
    s = scenario_S02()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    result = _verifier(profesores, guardias, session).check_r1_turno()
    assert result.total_evaluadas > 0
    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R1 S02: {result.cumplimiento_pct:.1f}% fallos={result.fallos[:3]}"
    )


# ---------------------------------------------------------------------------
# R2 — No ausente en fecha
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r2_ausencias(algo, session, build_scenario, build_ausencia, run_cpsat):
    from datetime import date

    s = scenario_S08()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)

    # Crear ausencia para los 2 primeros profesores en la semana 2
    for p in profesores[:2]:
        build_ausencia(p.id, date(2024, 9, 9), date(2024, 9, 13))

    guardias, _ = _run_algo(algo, run_cpsat)
    result = _verifier(profesores, guardias, session).check_r2_ausencias()

    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R2 ausencias: {result.cumplimiento_pct:.1f}% fallos={result.fallos[:3]}"
    )


# ---------------------------------------------------------------------------
# R3 — Fecha >= fecha_inicio_guardias
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r3_fecha_inicio(algo, session, build_scenario, run_cpsat):
    s = scenario_S03()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    result = _verifier(profesores, guardias, session).check_r3_fecha_inicio()
    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R3 fecha_inicio: {result.cumplimiento_pct:.1f}% fallos={result.fallos[:3]}"
    )


# ---------------------------------------------------------------------------
# R4 — Fecha <= fecha_fin_guardias
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r4_fecha_fin(algo, session, build_scenario, run_cpsat):
    s = scenario_S04()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    result = _verifier(profesores, guardias, session).check_r4_fecha_fin()
    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R4 fecha_fin: {result.cumplimiento_pct:.1f}% fallos={result.fallos[:3]}"
    )


# ---------------------------------------------------------------------------
# R5 — Recreos lista simple
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r5_recreos_lista(algo, session, build_scenario, run_cpsat):
    s = scenario_S05()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    result = _verifier(profesores, guardias, session).check_r5_recreos_lista()
    # Solo evalúa si hay guardias con profs que tienen restricción
    if result.total_evaluadas == 0:
        pytest.skip("Ningún profesor con recreos_permitidos (lista) recibió guardias")
    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R5 recreos_lista: {result.cumplimiento_pct:.1f}% fallos={result.fallos[:3]}"
    )


# ---------------------------------------------------------------------------
# R6 — Recreos dict por día
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r6_recreos_dict(algo, session, build_scenario, run_cpsat):
    s = scenario_S06()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    result = _verifier(profesores, guardias, session).check_r6_recreos_dict()
    if result.total_evaluadas == 0:
        pytest.skip("Ningún profesor con recreos_permitidos (dict) recibió guardias")
    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R6 recreos_dict: {result.cumplimiento_pct:.1f}% fallos={result.fallos[:3]}"
    )


# ---------------------------------------------------------------------------
# R7 — Días semana permitidos
# ---------------------------------------------------------------------------


def test_r7_dias_semana_cpsat(session, build_scenario, run_cpsat):
    s = scenario_S07()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = run_cpsat()

    result = ComplianceVerifier(profesores, guardias, session).check_r7_dias_semana()
    assert result.total_evaluadas > 0, "Profs con dias_semana_permitidos no recibieron guardias"
    assert result.cumplimiento_pct == 100.0


# ---------------------------------------------------------------------------
# R8 — Máximo 1 guardia por día
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo,min_pct", [("cpsat", 100.0)])
def test_r8_max_guardia_dia(algo, min_pct, session, build_scenario, run_cpsat):
    s = scenario_S01()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    result = _verifier(profesores, guardias, session).check_r8_max_guardia_dia()
    assert result.cumplimiento_pct >= min_pct, (
        f"[{algo}] R8 max_guardia_dia: {result.cumplimiento_pct:.1f}% < {min_pct}% "
        f"fallos={result.fallos[:3]}"
    )


# ---------------------------------------------------------------------------
# R9 — No simultaneidad
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algo", ["cpsat"])
def test_r9_no_simultaneidad(algo, session, build_scenario, run_cpsat):
    s = scenario_S01()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = _run_algo(algo, run_cpsat)

    result = _verifier(profesores, guardias, session).check_r9_no_simultaneidad()
    assert result.cumplimiento_pct == 100.0, (
        f"[{algo}] R9 no_simultaneidad: {result.cumplimiento_pct:.1f}% fallos={result.fallos[:3]}"
    )
