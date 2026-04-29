"""
Suite de regresión mixta (S10) — verifica todas las restricciones (R1–R13)
con ambos algoritmos en un escenario realista de 15 profesores × 3 semanas.

Este test es el canario de la mina: si falla algo aquí, hay una regresión.
"""

from __future__ import annotations

import pytest

from tests.compliance.scenarios import scenario_S10
from tests.compliance.verifiers import ComplianceVerifier

pytestmark = [pytest.mark.slow, pytest.mark.integration]

# Umbrales de aceptación por restricción y algoritmo
_THRESHOLDS = {
    # (restriccion, algo) → (min_pct, strict)
    ("R1_turno", "cpsat"): (100.0, True),
    ("R1_turno", "v4"): (100.0, True),
    ("R2_ausencias", "cpsat"): (100.0, True),
    ("R2_ausencias", "v4"): (100.0, True),
    ("R3_fecha_inicio", "cpsat"): (100.0, True),
    ("R3_fecha_inicio", "v4"): (100.0, True),
    ("R4_fecha_fin", "cpsat"): (100.0, True),
    ("R4_fecha_fin", "v4"): (100.0, True),
    ("R5_recreos_lista", "cpsat"): (100.0, True),
    ("R5_recreos_lista", "v4"): (100.0, True),
    ("R6_recreos_dict", "cpsat"): (100.0, True),
    ("R6_recreos_dict", "v4"): (100.0, True),
    # R7 CP-SAT: gap conocido — se verifica sin assert (solo registra)
    ("R7_dias_semana", "cpsat"): (0.0, False),
    ("R7_dias_semana", "v4"): (100.0, True),
    ("R8_max_guardia_dia", "cpsat"): (100.0, True),
    ("R8_max_guardia_dia", "v4"): (95.0, True),
    ("R9_no_simultaneidad", "cpsat"): (100.0, True),
    ("R9_no_simultaneidad", "v4"): (100.0, True),
    ("R10_zona_preferida", "cpsat"): (30.0, True),
    ("R10_zona_preferida", "v4"): (30.0, True),
    ("R11_equidad", "cpsat"): (0.0, False),   # S10 tiene restricciones que sesgan la distribución
    ("R11_equidad", "v4"): (0.0, False),
    ("R12_ajuste_tutor", "cpsat"): (0.0, False),  # depende de distribución
    ("R12_ajuste_tutor", "v4"): (0.0, False),
    ("R13_consecutividad", "cpsat"): (40.0, True),
    ("R13_consecutividad", "v4"): (40.0, True),
}


def _run_and_verify(algo: str, session, build_scenario, run_cpsat, run_v4, compliance_reporter):
    s = scenario_S10()
    profesores, _ = build_scenario(s.prof_configs, s.n_zonas, s.inicio, s.fin)
    guardias, _ = run_cpsat() if algo == "cpsat" else run_v4()

    verifier = ComplianceVerifier(profesores, guardias, session)
    all_results = verifier.run_all()

    # Registrar en el reporter para el JSON histórico
    compliance_reporter.record(f"{s.nombre}_{algo}", algo, all_results)

    # Imprimir tabla de resultados en la salida de pytest
    verifier.print_report()

    # Verificar umbrales
    fallos_regresion = []
    for result in all_results:
        key = (result.restriccion, algo)
        min_pct, strict = _THRESHOLDS.get(key, (0.0, False))
        if strict and result.total_evaluadas > 0 and result.cumplimiento_pct < min_pct:
            fallos_regresion.append(
                f"  {result.restriccion}: {result.cumplimiento_pct:.1f}% < {min_pct}% requerido"
                + (f" | fallos[0]: {result.fallos[0]}" if result.fallos else "")
            )

    return fallos_regresion


@pytest.mark.parametrize("algo", ["v4", "cpsat"])
def test_regression_s10_completo(
    algo, session, build_scenario, run_cpsat, run_v4, compliance_reporter
):
    """
    Escenario mixto completo S10 como suite de regresión.

    Verifica simultáneamente R1–R13 con umbrales definidos en _THRESHOLDS.
    R7 CP-SAT sigue marcado como gap conocido (threshold=0%, no strict).
    """
    fallos = _run_and_verify(algo, session, build_scenario, run_cpsat, run_v4, compliance_reporter)

    assert not fallos, (
        f"\n[{algo}] REGRESIÓN DETECTADA en S10 ({len(fallos)} restricciones):\n"
        + "\n".join(fallos)
    )
