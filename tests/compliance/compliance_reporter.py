"""
ComplianceReporter — persistencia de resultados de compliance y análisis histórico.

Cada ejecución de la suite genera un JSON en data/reports/compliance/ con:
  - timestamp, versión, algoritmos probados
  - resultados detallados por restricción × algoritmo
  - score global por algoritmo

El histórico acumulado permite detectar regresiones entre versiones y,
opcionalmente, alimentar sugerencias de mejora asistidas por IA.

Uso directo:
    from tests.compliance.compliance_reporter import ComplianceReporter
    ComplianceReporter.save_session(buffer)

Análisis de tendencias:
    history = ComplianceReporter.load_history()
    trends = ComplianceReporter.analyze_trends(history)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Directorio de informes (data/ está gitignored)
_REPORTS_DIR = Path(__file__).resolve().parents[2] / "data" / "reports" / "compliance"


def _app_version() -> str:
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
        from config.settings import settings

        return settings.app_version
    except Exception:
        return "unknown"


class ComplianceReporter:
    """
    Gestiona la persistencia y análisis del histórico de informes de compliance.
    """

    # ------------------------------------------------------------------
    # Guardar sesión
    # ------------------------------------------------------------------

    @staticmethod
    def save_session(buffer: list[dict]) -> Path:
        """
        Escribe el buffer de resultados de una sesión pytest como JSON.

        buffer: lista de dicts con keys escenario, algoritmo, results
                (producida por _ComplianceReporterCollector.record())

        Returns: ruta del archivo generado
        """
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc)
        filename = ts.strftime("%Y-%m-%d_%H-%M-%S") + "_compliance.json"
        path = _REPORTS_DIR / filename

        # Agrupar resultados por algoritmo
        by_algo: dict[str, dict[str, dict]] = {}
        for entry in buffer:
            algo = entry["algoritmo"]
            escenario = entry["escenario"]
            if algo not in by_algo:
                by_algo[algo] = {}
            for r in entry["results"]:
                key = f"{escenario}/{r['restriccion']}"
                by_algo[algo][key] = {
                    "escenario": escenario,
                    "restriccion": r["restriccion"],
                    "tipo": r["tipo"],
                    "total_evaluadas": r["total_evaluadas"],
                    "cumplidas": r["cumplidas"],
                    "cumplimiento_pct": r["cumplimiento_pct"],
                    "n_fallos": len(r["fallos"]),
                }

        # Score por algoritmo: % de restricciones DURA al 100% + blandas al umbral
        resumen: dict[str, dict] = {}
        for algo, resultados in by_algo.items():
            duras = [
                v for v in resultados.values() if v["tipo"] == "DURA" and v["total_evaluadas"] > 0
            ]
            blandas = [
                v for v in resultados.values() if v["tipo"] == "BLANDA" and v["total_evaluadas"] > 0
            ]
            duras_ok = sum(1 for v in duras if v["cumplimiento_pct"] >= 100.0)
            blandas_ok = sum(1 for v in blandas if v["cumplimiento_pct"] >= 50.0)
            total = len(duras) + len(blandas) or 1
            resumen[algo] = {
                "duras_total": len(duras),
                "duras_ok": duras_ok,
                "blandas_total": len(blandas),
                "blandas_ok": blandas_ok,
                "score_pct": (duras_ok + blandas_ok) / total * 100.0,
            }

        report = {
            "run_id": str(uuid.uuid4()),
            "timestamp": ts.isoformat(),
            "version": _app_version(),
            "algoritmos_probados": list(by_algo.keys()),
            "resultados": by_algo,
            "resumen": resumen,
            "n_entradas_buffer": len(buffer),
        }

        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[ComplianceReporter] Informe guardado en: {path}")
        return path

    # ------------------------------------------------------------------
    # Cargar histórico
    # ------------------------------------------------------------------

    @staticmethod
    def load_history(max_reports: int = 50) -> list[dict]:
        """
        Carga los últimos N informes de compliance del directorio.

        Returns: lista de reports ordenados de más antiguo a más reciente
        """
        if not _REPORTS_DIR.exists():
            return []
        files = sorted(_REPORTS_DIR.glob("*_compliance.json"))[-max_reports:]
        history = []
        for f in files:
            try:
                history.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return history

    # ------------------------------------------------------------------
    # Análisis de tendencias
    # ------------------------------------------------------------------

    @staticmethod
    def analyze_trends(history: list[dict]) -> dict[str, Any]:
        """
        Analiza el histórico y detecta tendencias.

        Devuelve:
            {
              "total_runs": N,
              "versiones": [...],
              "por_algoritmo": {
                "cpsat": {
                  "score_tendencia": [...],   # score_pct en cada run
                  "mejor_score": float,
                  "peor_score": float,
                  "restricciones_inestables": [...],  # R con alta varianza
                },
                ...
              },
              "regresiones_detectadas": [...],  # restricciones con score cayendo
              "sugerencias": [...],              # recomendaciones automáticas
            }
        """
        if not history:
            return {"total_runs": 0, "versiones": [], "por_algoritmo": {}, "sugerencias": []}

        versiones = [r.get("version", "?") for r in history]
        por_algo: dict[str, dict] = {}

        for report in history:
            for algo, resumen in report.get("resumen", {}).items():
                if algo not in por_algo:
                    por_algo[algo] = {
                        "score_tendencia": [],
                        "restricciones": {},
                    }
                por_algo[algo]["score_tendencia"].append(resumen.get("score_pct", 0))

            for algo, resultados in report.get("resultados", {}).items():
                if algo not in por_algo:
                    por_algo[algo] = {"score_tendencia": [], "restricciones": {}}
                for key, val in resultados.items():
                    restriccion = val["restriccion"]
                    if restriccion not in por_algo[algo]["restricciones"]:
                        por_algo[algo]["restricciones"][restriccion] = []
                    por_algo[algo]["restricciones"][restriccion].append(val["cumplimiento_pct"])

        # Calcular métricas por algoritmo
        resultado: dict[str, Any] = {}
        regresiones = []
        sugerencias = []

        for algo, datos in por_algo.items():
            scores = datos["score_tendencia"]
            mejor = max(scores) if scores else 0.0
            peor = min(scores) if scores else 0.0

            inestables = []
            for restriccion, pcts in datos["restricciones"].items():
                if len(pcts) < 2:
                    continue
                varianza = _varianza(pcts)
                if varianza > 100:  # SD > 10%
                    inestables.append(
                        {"restriccion": restriccion, "varianza": varianza, "pcts": pcts}
                    )

                # Detectar regresión: último valor < media previa - 10
                if len(pcts) >= 3:
                    media_previa = sum(pcts[:-1]) / len(pcts[:-1])
                    if pcts[-1] < media_previa - 10:
                        regresiones.append(
                            {
                                "algoritmo": algo,
                                "restriccion": restriccion,
                                "ultimo": pcts[-1],
                                "media_previa": media_previa,
                            }
                        )

            resultado[algo] = {
                "score_tendencia": scores,
                "mejor_score": mejor,
                "peor_score": peor,
                "restricciones_inestables": inestables,
            }

            # Sugerencias automáticas basadas en datos
            if len(scores) >= 2 and scores[-1] < scores[-2]:
                sugerencias.append(
                    f"[{algo}] El score global bajó de {scores[-2]:.1f}% a {scores[-1]:.1f}%. "
                    f"Revisar últimos cambios en el algoritmo."
                )

            duras_bajas = [
                r
                for r, pcts in datos["restricciones"].items()
                if pcts and pcts[-1] < 100.0 and r.startswith("R") and int(r[1:].split("_")[0]) <= 9
            ]
            for r in duras_bajas:
                sugerencias.append(
                    f"[{algo}] Restricción DURA {r} al {datos['restricciones'][r][-1]:.1f}% "
                    f"(debe ser 100%). Investigar regresión."
                )

        return {
            "total_runs": len(history),
            "versiones": versiones,
            "por_algoritmo": resultado,
            "regresiones_detectadas": regresiones,
            "sugerencias": sugerencias,
        }

    # ------------------------------------------------------------------
    # Imprimir resumen de tendencias en consola
    # ------------------------------------------------------------------

    @staticmethod
    def print_trend_summary(history: Optional[list[dict]] = None) -> None:
        if history is None:
            history = ComplianceReporter.load_history()
        trends = ComplianceReporter.analyze_trends(history)

        print(f"\n{'=' * 70}")
        print(f"HISTÓRICO DE COMPLIANCE — {trends['total_runs']} ejecuciones")
        print(f"Versiones: {', '.join(trends['versiones'])}")
        print(f"{'=' * 70}")

        for algo, datos in trends["por_algoritmo"].items():
            scores = datos["score_tendencia"]
            print(f"\n  [{algo}] Scores: {[f'{s:.1f}%' for s in scores[-5:]]}")
            print(f"           Mejor={datos['mejor_score']:.1f}%  Peor={datos['peor_score']:.1f}%")

        if trends["regresiones_detectadas"]:
            print("\n  ⚠️  REGRESIONES DETECTADAS:")
            for r in trends["regresiones_detectadas"]:
                print(
                    f"    [{r['algoritmo']}] {r['restriccion']}: "
                    f"{r['ultimo']:.1f}% (vs media {r['media_previa']:.1f}%)"
                )

        if trends["sugerencias"]:
            print("\n  💡 SUGERENCIAS:")
            for s in trends["sugerencias"]:
                print(f"    {s}")

        print(f"{'=' * 70}")


def _varianza(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    media = sum(values) / len(values)
    return sum((v - media) ** 2 for v in values) / len(values)
