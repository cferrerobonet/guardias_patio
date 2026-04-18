#!/usr/bin/env python3
"""
Script de profiling de rendimiento para operaciones críticas.

Analiza:
1. generar_calendario_guardias() - Generación completa
2. calcular_distribucion() - Cálculo de distribución
3. Consultas SQL frecuentes
4. Operaciones de exportación

Uso:
    python scripts/profile_performance.py
    python scripts/profile_performance.py --operation generar
    python scripts/profile_performance.py --visualize
"""

import cProfile
import io
import pstats
import sys
import time
from contextlib import contextmanager
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.use_cases.profesor.listar_profesores import ListarProfesores
from database.db_manager import SessionLocal
from infrastructure.repositories.sqlalchemy_profesor_repository import SQLAlchemyProfesorRepository
from services.asignador_guardias import AsignadorGuardias
from services.calculador_guardias import CalculadorGuardias
from services.exportador import Exportador
from services.exportador_pdf import ExportadorPDF


@contextmanager
def profile_operation(operation_name: str, output_file: str = None):
    """
    Context manager para hacer profiling de una operación.

    Args:
        operation_name: Nombre de la operación para el reporte
        output_file: Archivo de salida para stats (.prof)
    """
    print(f"\n{'=' * 70}")
    print(f"🔍 PROFILING: {operation_name}")
    print(f"{'=' * 70}")

    profiler = cProfile.Profile()
    start_time = time.time()

    profiler.enable()
    yield profiler
    profiler.disable()

    elapsed = time.time() - start_time

    # Guardar stats si se especifica archivo
    if output_file:
        profiler.dump_stats(output_file)
        print(f"\n📁 Stats guardados en: {output_file}")
        print(f"   Visualizar con: snakeviz {output_file}")

    # Mostrar resumen
    print(f"\n⏱️  Tiempo total: {elapsed:.3f} segundos")
    print("\n📊 Top 20 funciones más lentas:\n")

    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(20)
    print(s.getvalue())


def profile_generar_calendario():
    """Profiling de generación completa de calendario."""
    with profile_operation("generar_calendario_guardias()", "profile_generar_calendario.prof"):
        session = SessionLocal()
        try:
            asignador = AsignadorGuardias(session)
            guardias = asignador.generar_calendario_guardias()
            print(f"\n✅ Generadas {len(guardias)} guardias")
        finally:
            session.close()


def profile_calcular_distribucion():
    """Profiling de cálculo de distribución."""
    with profile_operation("calcular_distribucion()", "profile_calcular_distribucion.prof"):
        session = SessionLocal()
        try:
            calculador = CalculadorGuardias(session)
            profesores_repo = SQLAlchemyProfesorRepository(session)
            profesores = profesores_repo.obtener_todos()
            distribucion = calculador.calcular_distribucion(profesores)
            print(f"\n✅ Distribución calculada para {len(distribucion)} profesores")
        finally:
            session.close()


def profile_listar_profesores():
    """Profiling de listado de profesores."""
    with profile_operation("listar_profesores()", "profile_listar_profesores.prof"):
        session = SessionLocal()
        try:
            repo = SQLAlchemyProfesorRepository(session)
            use_case = ListarProfesores(repo)
            profesores = use_case.execute()
            print(f"\n✅ Listados {len(profesores)} profesores")
        finally:
            session.close()


def profile_exportar_pdf():
    """Profiling de exportación PDF."""
    with profile_operation("exportar_pdf()", "profile_exportar_pdf.prof"):
        session = SessionLocal()
        try:
            asignador = AsignadorGuardias(session)
            guardias = asignador.obtener_todas_guardias()

            if not guardias:
                print("⚠️  No hay guardias para exportar")
                return

            exportador = ExportadorPDF()
            archivo = "/tmp/test_guardias.pdf"
            exportador.exportar(guardias, archivo)
            print(f"\n✅ PDF exportado: {archivo}")
        finally:
            session.close()


def profile_exportar_json():
    """Profiling de exportación JSON."""
    with profile_operation("exportar_json()", "profile_exportar_json.prof"):
        session = SessionLocal()
        try:
            exportador = Exportador(session)
            datos = exportador.exportar_todo()
            print(f"\n✅ Exportados {len(datos.get('profesores', []))} profesores")
        finally:
            session.close()


def profile_query_patterns():
    """Analiza patrones de consultas SQL frecuentes."""
    print(f"\n{'=' * 70}")
    print("🔍 ANÁLISIS DE CONSULTAS SQL")
    print(f"{'=' * 70}\n")

    session = SessionLocal()
    try:
        # 1. SELECT * FROM profesores
        start = time.time()
        repo = SQLAlchemyProfesorRepository(session)
        profesores = repo.obtener_todos()
        elapsed = time.time() - start
        print("1️⃣  SELECT * FROM profesores")
        print(f"   Registros: {len(profesores)}")
        print(f"   Tiempo: {elapsed * 1000:.2f}ms\n")

        # 2. SELECT con filtro activo
        start = time.time()
        from infrastructure.database.models import Profesor

        activos = session.query(Profesor).filter(Profesor.activo).all()
        elapsed = time.time() - start
        print("2️⃣  SELECT * FROM profesores WHERE activo = True")
        print(f"   Registros: {len(activos)}")
        print(f"   Tiempo: {elapsed * 1000:.2f}ms\n")

        # 3. JOIN con zonas
        start = time.time()
        from infrastructure.database.models import Zona

        profesores_con_zonas = (
            session.query(Profesor).join(Zona, Profesor.zona_preferida_id == Zona.id).all()
        )
        elapsed = time.time() - start
        print("3️⃣  SELECT * FROM profesores JOIN zonas")
        print(f"   Registros: {len(profesores_con_zonas)}")
        print(f"   Tiempo: {elapsed * 1000:.2f}ms\n")

        # 4. COUNT
        start = time.time()
        count = session.query(Profesor).count()
        elapsed = time.time() - start
        print("4️⃣  SELECT COUNT(*) FROM profesores")
        print(f"   Count: {count}")
        print(f"   Tiempo: {elapsed * 1000:.2f}ms\n")

        # 5. Guardias por profesor
        start = time.time()
        from infrastructure.database.models import Guardia

        guardias = session.query(Guardia).filter(Guardia.profesor_id == profesores[0].id).all()
        elapsed = time.time() - start
        print("5️⃣  SELECT * FROM guardias WHERE profesor_id = X")
        print(f"   Registros: {len(guardias)}")
        print(f"   Tiempo: {elapsed * 1000:.2f}ms\n")
    finally:
        session.close()


def analyze_database_indices():
    """Analiza índices existentes en la base de datos."""
    print(f"\n{'=' * 70}")
    print("📑 ANÁLISIS DE ÍNDICES DE BASE DE DATOS")
    print(f"{'=' * 70}\n")

    session = SessionLocal()
    try:
        # SQLite: Obtener índices
        result = session.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index'")
        indices = result.fetchall()

        print(f"Total de índices: {len(indices)}\n")

        for idx in indices:
            if idx[2]:  # Tiene SQL (índices explícitos, no autoindex)
                print(f"📌 {idx[0]}")
                print(f"   Tabla: {idx[1]}")
                print(f"   SQL: {idx[2]}\n")
    finally:
        session.close()


def recommend_indices():
    """Recomienda índices basándose en consultas comunes."""
    print(f"\n{'=' * 70}")
    print("💡 RECOMENDACIONES DE ÍNDICES")
    print(f"{'=' * 70}\n")

    recommendations = [
        {
            "tabla": "profesores",
            "columna": "activo",
            "razon": "Filtro frecuente en WHERE activo = True",
            "sql": "CREATE INDEX idx_profesores_activo ON profesores(activo);",
        },
        {
            "tabla": "profesores",
            "columna": "zona_preferida_id",
            "razon": "Join frecuente con zonas",
            "sql": "CREATE INDEX idx_profesores_zona_preferida ON profesores(zona_preferida_id);",
        },
        {
            "tabla": "guardias",
            "columna": "profesor_id",
            "razon": "Join frecuente y filtros por profesor",
            "sql": "CREATE INDEX idx_guardias_profesor ON guardias(profesor_id);",
        },
        {
            "tabla": "guardias",
            "columna": "zona_id",
            "razon": "Join frecuente y filtros por zona",
            "sql": "CREATE INDEX idx_guardias_zona ON guardias(zona_id);",
        },
        {
            "tabla": "guardias",
            "columna": "fecha",
            "razon": "Filtros y ordenamiento por fecha",
            "sql": "CREATE INDEX idx_guardias_fecha ON guardias(fecha);",
        },
        {
            "tabla": "guardias",
            "columna": "turno",
            "razon": "Filtros por turno (mañana/tarde)",
            "sql": "CREATE INDEX idx_guardias_turno ON guardias(turno);",
        },
        {
            "tabla": "ausencias",
            "columna": "profesor_id",
            "razon": "Join frecuente con profesores",
            "sql": "CREATE INDEX idx_ausencias_profesor ON ausencias(profesor_id);",
        },
        {
            "tabla": "ausencias",
            "columna": "fecha_inicio, fecha_fin",
            "razon": "Búsqueda de rangos de fechas",
            "sql": "CREATE INDEX idx_ausencias_fechas ON ausencias(fecha_inicio, fecha_fin);",
        },
    ]

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}️⃣  {rec['tabla']}.{rec['columna']}")
        print(f"   📝 Razón: {rec['razon']}")
        print(f"   💻 SQL: {rec['sql']}\n")


def generate_summary():
    """Genera resumen ejecutivo del profiling."""
    print(f"\n{'=' * 70}")
    print("📊 RESUMEN EJECUTIVO DE PROFILING")
    print(f"{'=' * 70}\n")

    print("✅ OPERACIONES ANALIZADAS:")
    print("   1. generar_calendario_guardias()")
    print("   2. calcular_distribucion()")
    print("   3. listar_profesores()")
    print("   4. exportar_pdf()")
    print("   5. exportar_json()")
    print("   6. Patrones de consultas SQL\n")

    print("📁 ARCHIVOS GENERADOS:")
    print("   - profile_generar_calendario.prof")
    print("   - profile_calcular_distribucion.prof")
    print("   - profile_listar_profesores.prof")
    print("   - profile_exportar_pdf.prof")
    print("   - profile_exportar_json.prof\n")

    print("🔍 VISUALIZAR RESULTADOS:")
    print("   snakeviz profile_generar_calendario.prof")
    print("   snakeviz profile_calcular_distribucion.prof\n")

    print("💡 PRÓXIMOS PASOS:")
    print("   1. Revisar top 20 funciones más lentas en cada operación")
    print("   2. Implementar índices recomendados (ver arriba)")
    print("   3. Ejecutar tests de rendimiento después de optimizar")
    print("   4. Meta: <500ms para operaciones típicas\n")


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Profiling de rendimiento")
    parser.add_argument(
        "--operation",
        choices=["generar", "calcular", "listar", "pdf", "json", "queries", "indices", "all"],
        default="all",
        help="Operación a profilear",
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Abrir snakeviz después del profiling"
    )

    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print("🚀 INICIANDO PROFILING DE RENDIMIENTO")
    print(f"{'=' * 70}\n")

    operations = {
        "generar": profile_generar_calendario,
        "calcular": profile_calcular_distribucion,
        "listar": profile_listar_profesores,
        "pdf": profile_exportar_pdf,
        "json": profile_exportar_json,
        "queries": profile_query_patterns,
        "indices": lambda: (analyze_database_indices(), recommend_indices()),
    }

    if args.operation == "all":
        # Ejecutar todas
        for op_name, op_func in operations.items():
            try:
                op_func()
            except Exception as e:
                print(f"❌ Error en {op_name}: {e}")

        generate_summary()
    else:
        # Ejecutar operación específica
        operations[args.operation]()

    # Visualizar si se solicita
    if args.visualize and args.operation in ["generar", "calcular", "listar", "pdf", "json"]:
        import subprocess

        profile_file = f"profile_{args.operation}.prof"
        if Path(profile_file).exists():
            print(f"\n🌐 Abriendo snakeviz para {profile_file}...")
            subprocess.Popen(["snakeviz", profile_file])


if __name__ == "__main__":
    main()
