#!/usr/bin/env python3.11
"""
Script de benchmarking para medir mejoras de rendimiento.
Crea datos sintéticos y mide queries, tiempo y memoria.
"""

import sys
import time
import traceback
import tracemalloc
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db_manager import SessionLocal, engine
from models.models import Base, Guardia, Profesor, Zona
from services.exportador import ExportadorDatos


def setup_test_db():
    """Crear base de datos temporal con datos sintéticos."""
    print("📦 Creando base de datos temporal...")

    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        # Crear profesores
        profesores = []
        for i in range(50):
            prof = Profesor(
                nombre_completo=f"Profesor{i}, Test",
                email_corporativo=f"profesor{i}@example.com",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana" if i % 2 == 0 else "tarde",
                tutor=False
            )
            profesores.append(prof)
            session.add(prof)

        # Crear zonas
        zonas = []
        for i in range(20):
            zona = Zona(nombre_zona=f"Zona{i}", descripcion=f"Zona de test {i}")
            zonas.append(zona)
            session.add(zona)

        session.commit()

        # Crear guardias (100 guardias distribuidas)
        hoy = date.today()
        for i in range(100):
            guardia = Guardia(
                profesor_id=profesores[i % len(profesores)].id,
                fecha=hoy + timedelta(days=i // 4),
                turno="mañana" if i % 2 == 0 else "tarde",
                recreo=1 if i % 4 == 0 else 2,
                zona_id=zonas[i % len(zonas)].id
            )
            session.add(guardia)

        session.commit()

        print(f"✅ Creados: {len(profesores)} profesores, "
              f"{len(zonas)} zonas, 100 guardias\n")

    finally:
        session.close()


def count_queries(func):
    """Decorator para contar queries SQL."""
    query_count = [0]

    def count_sql(*args):
        query_count[0] += 1

    from sqlalchemy import event
    event.listen(engine, "before_cursor_execute", count_sql)

    try:
        result = func()
        return result, query_count[0]
    finally:
        event.remove(engine, "before_cursor_execute", count_sql)


def benchmark_load_guardias():
    """Benchmark: Cargar 100 guardias con relaciones."""
    print("🔹 Benchmark: Cargar 100 guardias con relaciones")

    session = SessionLocal()

    def load():
        guardias = session.query(Guardia).all()
        # Acceder a relaciones (simula uso real)
        for g in guardias:
            _ = g.profesor.nombre_completo if g.profesor else None
            _ = g.zona.nombre_zona if g.zona else None
        return len(guardias)

    # Medir con conteo de queries
    tracemalloc.start()
    start_time = time.perf_counter()

    count, queries = count_queries(load)

    elapsed = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    session.close()

    return {
        "name": "load_guardias",
        "count": count,
        "queries": queries,
        "time": elapsed,
        "memory_peak_kb": peak / 1024,
    }


def benchmark_export_guardias():
    """Benchmark: Exportar guardias a diccionario."""
    print("🔹 Benchmark: Exportar guardias a diccionario")

    session = SessionLocal()

    def export():
        data = ExportadorDatos.exportar_guardias(session)
        return len(data)

    tracemalloc.start()
    start_time = time.perf_counter()

    count, queries = count_queries(export)

    elapsed = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    session.close()

    return {
        "name": "export_guardias",
        "count": count,
        "queries": queries,
        "time": elapsed,
        "memory_peak_kb": peak / 1024,
    }


def benchmark_calendar_generation():
    """Benchmark: Generar estructura de calendario mensual."""
    print("🔹 Benchmark: Generar calendario mensual")

    session = SessionLocal()

    def generate_calendar():
        hoy = date.today()
        primer_dia = date(hoy.year, hoy.month, 1)
        ultimo_dia = primer_dia + timedelta(days=31)

        guardias = (
            session.query(Guardia)
            .filter(Guardia.fecha >= primer_dia, Guardia.fecha < ultimo_dia)
            .all()
        )

        # Construir estructura de calendario
        calendario = {}
        for g in guardias:
            fecha_key = g.fecha.isoformat()
            if fecha_key not in calendario:
                calendario[fecha_key] = []

            calendario[fecha_key].append({
                "profesor": g.profesor.nombre_completo if g.profesor else "N/A",
                "zona": g.zona.nombre_zona if g.zona else "N/A",
                "turno": g.turno,
            })

        return len(guardias)

    tracemalloc.start()
    start_time = time.perf_counter()

    count, queries = count_queries(generate_calendar)

    elapsed = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    session.close()

    return {
        "name": "calendar_generation",
        "count": count,
        "queries": queries,
        "time": elapsed,
        "memory_peak_kb": peak / 1024,
    }


def print_results(results: list[dict]):
    """Imprimir resultados de benchmarks."""
    print("\n" + "=" * 80)
    print("📊 RESULTADOS DE BENCHMARKING")
    print("=" * 80)

    total_queries = sum(r["queries"] for r in results)
    total_time = sum(r["time"] for r in results)
    total_memory = sum(r["memory_peak_kb"] for r in results)

    for r in results:
        print(f"\n🔹 {r['name'].upper().replace('_', ' ')}")
        print(f"   Items procesados: {r['count']}")
        print(f"   Queries SQL: {r['queries']}")
        print(f"   Tiempo: {r['time']:.4f}s")
        print(f"   Memoria pico: {r['memory_peak_kb']:.2f} KB")

    print("\n" + "=" * 80)
    print("📈 TOTALES:")
    print(f"   Total queries: {total_queries}")
    print(f"   Total tiempo: {total_time:.4f}s")
    print(f"   Total memoria: {total_memory:.2f} KB")
    print("=" * 80)

    print("\n💡 MÉTRICAS OBJETIVO:")
    print("   - Queries por guardia: < 2 (ideal: 1)")
    print("   - Tiempo total: < 0.1s para 100 guardias")
    print("   - Memoria: < 5000 KB")
    print("=" * 80 + "\n")


def main():
    """Ejecutar suite de benchmarks."""
    print("🚀 Iniciando benchmarks de rendimiento...\n")

    try:
        # Setup
        setup_test_db()

        # Ejecutar benchmarks
        results = []
        results.append(benchmark_load_guardias())
        results.append(benchmark_export_guardias())
        results.append(benchmark_calendar_generation())

        # Mostrar resultados
        print_results(results)

        print("✅ Benchmarks completados exitosamente")
        return 0

    except Exception as e:
        print(f"❌ Error durante benchmarking: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
