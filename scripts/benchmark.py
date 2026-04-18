#!/usr/bin/env python3
"""
Benchmark unificado — Guardias de Patio

Punto de entrada único para todos los scripts de medición de rendimiento.

Uso:
    python scripts/benchmark.py optimizaciones --db-id <hash>
    python scripts/benchmark.py performance
    python scripts/benchmark.py profile-app
    python scripts/benchmark.py profile-perf [--operation generar|distribucion|queries]
    python scripts/benchmark.py --help
"""

import argparse
import runpy
import sys
from pathlib import Path

ARCHIVE = Path(__file__).parent / "archive"

SCRIPTS = {
    "optimizaciones": ARCHIVE / "benchmark_optimizaciones.py",
    "performance": ARCHIVE / "benchmark_performance.py",
    "profile-app": ARCHIVE / "profile_app.py",
    "profile-perf": ARCHIVE / "profile_performance.py",
}

DESCRIPTIONS = {
    "optimizaciones": "Mide tiempos de generación de guardias antes/después de optimizaciones",
    "performance": "Benchmark de carga, exportación y generación de calendarios con datos sintéticos",
    "profile-app": "Profiling de flujos críticos: carga datos, renderizado calendario, exportación PDF",
    "profile-perf": "Profiling detallado con cProfile: generación, distribución, queries, índices BD",
}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "subcommand",
        choices=list(SCRIPTS.keys()),
        nargs="?",
        help="Benchmark a ejecutar",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Argumentos adicionales pasados al script seleccionado",
    )
    parser.add_argument("--list", "-l", action="store_true", help="Lista los benchmarks disponibles")

    args = parser.parse_args()

    if args.list or not args.subcommand:
        print("\nBenchmarks disponibles:\n")
        for name, desc in DESCRIPTIONS.items():
            script = SCRIPTS[name]
            print(f"  {name:<18} {desc}")
            print(f"  {'':18} Archivo: {script.relative_to(Path(__file__).parent.parent)}\n")
        return

    script_path = SCRIPTS[args.subcommand]
    if not script_path.exists():
        print(f"Error: script no encontrado en {script_path}", file=sys.stderr)
        sys.exit(1)

    # Reemplazar argv para que el subscript vea sus propios argumentos
    sys.argv = [str(script_path)] + args.args
    runpy.run_path(str(script_path), run_name="__main__")


if __name__ == "__main__":
    main()
