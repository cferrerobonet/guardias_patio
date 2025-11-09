#!/usr/bin/env python3.11
"""
Script de profiling para analizar rendimiento de flujos críticos.
Genera flamegraphs para visualizar hotspots de rendimiento.
"""

import sys
import time
from datetime import date, timedelta
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session

from database.db_manager import SessionLocal
from models.models import Guardia, Profesor, Zona
from services.exportador_pdf import ExportadorPDF


def profile_data_loading(session: Session) -> dict:
    """
    Perfilar carga de datos inicial (similar a startup de la app).

    Returns:
        dict: Métricas de rendimiento
    """
    print("🔍 Profiling: Carga inicial de datos...")

    start = time.perf_counter()

    # Operaciones típicas del startup
    profesores = session.query(Profesor).all()
    zonas = session.query(Zona).all()

    # Cargar guardias del mes actual
    hoy = date.today()
    primer_dia = date(hoy.year, hoy.month, 1)
    ultimo_dia = primer_dia + timedelta(days=31)

    guardias = (
        session.query(Guardia)
        .filter(Guardia.fecha >= primer_dia, Guardia.fecha < ultimo_dia)
        .all()
    )

    # Acceder a relaciones (simula renderizado de UI)
    for g in guardias[:50]:  # Limitar para no saturar
        _ = g.profesor.nombre_completo if g.profesor else None
        _ = g.zona.nombre_zona if g.zona else None

    elapsed = time.perf_counter() - start

    return {
        "name": "data_loading",
        "elapsed": elapsed,
        "profesores": len(profesores),
        "zonas": len(zonas),
        "guardias": len(guardias),
    }


def profile_calendar_rendering(session: Session) -> dict:
    """
    Perfilar renderizado de vista de calendario mensual.

    Returns:
        dict: Métricas de rendimiento
    """
    print("📅 Profiling: Renderizado calendario mensual...")

    start = time.perf_counter()

    # Simular carga de calendario mensual
    hoy = date.today()
    primer_dia = date(hoy.year, hoy.month, 1)
    ultimo_dia = primer_dia + timedelta(days=31)

    guardias = (
        session.query(Guardia)
        .filter(Guardia.fecha >= primer_dia, Guardia.fecha < ultimo_dia)
        .all()
    )

    # Simular construcción de estructura de datos para calendario
    calendario = {}
    for g in guardias:
        fecha_key = g.fecha.isoformat()
        if fecha_key not in calendario:
            calendario[fecha_key] = []

        calendario[fecha_key].append({
            "profesor": g.profesor.nombre_completo if g.profesor else "N/A",
            "zona": g.zona.nombre_zona if g.zona else "N/A",
            "turno": g.turno,
            "recreo": g.recreo,
        })

    elapsed = time.perf_counter() - start

    return {
        "name": "calendar_rendering",
        "elapsed": elapsed,
        "guardias": len(guardias),
        "dias_con_guardias": len(calendario),
    }


def profile_pdf_export(session: Session, output_dir: Path) -> dict:
    """
    Perfilar exportación de PDFs.

    Returns:
        dict: Métricas de rendimiento
    """
    print("📄 Profiling: Exportación PDF...")

    # Limpiar directorio temporal
    if output_dir.exists():
        for f in output_dir.glob("*.pdf"):
            f.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()

    # Exportar PDFs del mes actual para todos los profesores
    hoy = date.today()

    pdfs_generados = ExportadorPDF.exportar_todos_los_profesores(
        session=session,
        mes=hoy.month,
        anio=hoy.year,
        carpeta_salida=str(output_dir),
    )

    elapsed = time.perf_counter() - start

    return {
        "name": "pdf_export",
        "elapsed": elapsed,
        "pdfs_generados": pdfs_generados,
    }


def print_results(metrics: list[dict]) -> None:
    """Imprimir resultados de profiling."""
    print("\n" + "=" * 80)
    print("📊 RESULTADOS DE PROFILING")
    print("=" * 80)

    for m in metrics:
        print(f"\n🔹 {m['name'].upper().replace('_', ' ')}")
        print(f"   Tiempo: {m['elapsed']:.3f}s")

        for key, value in m.items():
            if key not in ["name", "elapsed"]:
                print(f"   {key.capitalize()}: {value}")

    print("\n" + "=" * 80)
    print("💡 INSTRUCCIONES PARA FLAMEGRAPH:")
    print("=" * 80)
    print("Para generar flamegraph completo de la app:")
    print("  py-spy record -o flamegraph.svg --python /opt/homebrew/bin/python3.11 -- src/main.py")
    print("\nPara profiling en tiempo real:")
    print("  py-spy top --python /opt/homebrew/bin/python3.11 -- src/main.py")
    print("=" * 80 + "\n")


def main():
    """Ejecutar profiling de flujos críticos."""
    print("🚀 Iniciando profiling de rendimiento...\n")

    # Configurar base de datos
    db_path = Path("guardias_patio.db")

    if not db_path.exists():
        print("❌ Error: Base de datos no encontrada. Ejecuta la app primero.")
        return 1

    try:
        session = SessionLocal()

        metrics = []

        # 1. Carga inicial de datos
        metrics.append(profile_data_loading(session))

        # 2. Renderizado de calendario
        metrics.append(profile_calendar_rendering(session))

        # 3. Exportación de PDFs
        output_dir = Path("temp_pdfs_profiling")
        metrics.append(profile_pdf_export(session, output_dir))

        # Limpiar archivos temporales
        if output_dir.exists():
            for f in output_dir.glob("*.pdf"):
                f.unlink()
            output_dir.rmdir()

        print_results(metrics)

        return 0

    except Exception as e:
        print(f"❌ Error durante profiling: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
