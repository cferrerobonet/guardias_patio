#!/usr/bin/env python3
"""
Análisis de índices de base de datos y recomendaciones de optimización.

Uso:
    python scripts/analyze_indices.py
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db_manager import SessionLocal
from sqlalchemy import text


def analyze_existing_indices():
    """Analiza índices existentes en la base de datos."""
    print("\n" + "=" * 70)
    print("📑 ANÁLISIS DE ÍNDICES EXISTENTES")
    print("=" * 70 + "\n")

    session = SessionLocal()
    try:
        # SQLite: Obtener índices
        query = text(
            "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name"
        )
        result = session.execute(query)
        indices = result.fetchall()

        print(f"Total de índices encontrados: {len(indices)}\n")

        # Agrupar por tabla
        indices_por_tabla = {}
        for idx in indices:
            tabla = idx[1]
            if tabla not in indices_por_tabla:
                indices_por_tabla[tabla] = []
            indices_por_tabla[tabla].append(idx)

        for tabla, idxs in sorted(indices_por_tabla.items()):
            print(f"📊 Tabla: {tabla}")
            print(f"   Índices: {len(idxs)}")
            for idx in idxs:
                if idx[2]:  # Tiene SQL (índices explícitos, no autoindex)
                    print(f"   ✓ {idx[0]}")
                    print(f"     SQL: {idx[2]}")
                else:
                    print(f"   • {idx[0]} (autoindex)")
            print()

    finally:
        session.close()


def recommend_indices():
    """Recomienda índices basándose en consultas comunes."""
    print("=" * 70)
    print("💡 RECOMENDACIONES DE ÍNDICES")
    print("=" * 70 + "\n")

    recommendations = [
        {
            "tabla": "profesores",
            "columna": "activo",
            "razon": "Filtro frecuente en WHERE activo = True",
            "sql": "CREATE INDEX IF NOT EXISTS idx_profesores_activo ON profesores(activo);",
            "prioridad": "ALTA",
        },
        {
            "tabla": "profesores",
            "columna": "zona_preferida_id",
            "razon": "Join frecuente con zonas",
            "sql": "CREATE INDEX IF NOT EXISTS idx_profesores_zona_preferida ON profesores(zona_preferida_id);",
            "prioridad": "ALTA",
        },
        {
            "tabla": "guardias",
            "columna": "profesor_id",
            "razon": "Join frecuente y filtros por profesor",
            "sql": "CREATE INDEX IF NOT EXISTS idx_guardias_profesor ON guardias(profesor_id);",
            "prioridad": "ALTA",
        },
        {
            "tabla": "guardias",
            "columna": "zona_id",
            "razon": "Join frecuente y filtros por zona",
            "sql": "CREATE INDEX IF NOT EXISTS idx_guardias_zona ON guardias(zona_id);",
            "prioridad": "ALTA",
        },
        {
            "tabla": "guardias",
            "columna": "fecha",
            "razon": "Filtros y ordenamiento por fecha",
            "sql": "CREATE INDEX IF NOT EXISTS idx_guardias_fecha ON guardias(fecha);",
            "prioridad": "MEDIA",
        },
        {
            "tabla": "guardias",
            "columna": "turno",
            "razon": "Filtros por turno (mañana/tarde)",
            "sql": "CREATE INDEX IF NOT EXISTS idx_guardias_turno ON guardias(turno);",
            "prioridad": "MEDIA",
        },
        {
            "tabla": "guardias",
            "columnas": "fecha, turno",
            "razon": "Búsqueda combinada fecha+turno (muy frecuente)",
            "sql": "CREATE INDEX IF NOT EXISTS idx_guardias_fecha_turno ON guardias(fecha, turno);",
            "prioridad": "ALTA",
        },
        {
            "tabla": "ausencias",
            "columna": "profesor_id",
            "razon": "Join frecuente con profesores",
            "sql": "CREATE INDEX IF NOT EXISTS idx_ausencias_profesor ON ausencias(profesor_id);",
            "prioridad": "ALTA",
        },
        {
            "tabla": "ausencias",
            "columnas": "fecha_inicio, fecha_fin",
            "razon": "Búsqueda de rangos de fechas",
            "sql": "CREATE INDEX IF NOT EXISTS idx_ausencias_fechas ON ausencias(fecha_inicio, fecha_fin);",
            "prioridad": "MEDIA",
        },
    ]

    for i, rec in enumerate(recommendations, 1):
        prioridad_emoji = "🔴" if rec["prioridad"] == "ALTA" else "🟡"
        columna_str = rec.get("columnas", rec.get("columna", ""))
        print(f"{i}. {prioridad_emoji} {rec['tabla']}.{columna_str} [{rec['prioridad']}]")
        print(f"   📝 Razón: {rec['razon']}")
        print(f"   💻 SQL: {rec['sql']}\n")


def generate_alembic_migration():
    """Genera el código para una migración de Alembic con los índices."""
    print("=" * 70)
    print("🔧 CÓDIGO PARA MIGRACIÓN DE ALEMBIC")
    print("=" * 70 + "\n")

    print("Para crear la migración, ejecuta:")
    print('  alembic revision -m "add_performance_indices"\n')

    print("Luego, en el archivo generado, agrega este código en upgrade():\n")
    print("```python")
    print("def upgrade():")
    print("    # Índices para tabla profesores")
    print("    op.create_index('idx_profesores_activo', 'profesores', ['activo'])")
    print(
        "    op.create_index('idx_profesores_zona_preferida', 'profesores', ['zona_preferida_id'])"
    )
    print()
    print("    # Índices para tabla guardias")
    print("    op.create_index('idx_guardias_profesor', 'guardias', ['profesor_id'])")
    print("    op.create_index('idx_guardias_zona', 'guardias', ['zona_id'])")
    print("    op.create_index('idx_guardias_fecha', 'guardias', ['fecha'])")
    print("    op.create_index('idx_guardias_turno', 'guardias', ['turno'])")
    print("    op.create_index('idx_guardias_fecha_turno', 'guardias', ['fecha', 'turno'])")
    print()
    print("    # Índices para tabla ausencias")
    print("    op.create_index('idx_ausencias_profesor', 'ausencias', ['profesor_id'])")
    print("    op.create_index('idx_ausencias_fechas', 'ausencias', ['fecha_inicio', 'fecha_fin'])")
    print("```\n")

    print("Y este código en downgrade():\n")
    print("```python")
    print("def downgrade():")
    print("    op.drop_index('idx_ausencias_fechas', 'ausencias')")
    print("    op.drop_index('idx_ausencias_profesor', 'ausencias')")
    print("    op.drop_index('idx_guardias_fecha_turno', 'guardias')")
    print("    op.drop_index('idx_guardias_turno', 'guardias')")
    print("    op.drop_index('idx_guardias_fecha', 'guardias')")
    print("    op.drop_index('idx_guardias_zona', 'guardias')")
    print("    op.drop_index('idx_guardias_profesor', 'guardias')")
    print("    op.drop_index('idx_profesores_zona_preferida', 'profesores')")
    print("    op.drop_index('idx_profesores_activo', 'profesores')")
    print("```\n")


def estimate_impact():
    """Estima el impacto de los índices propuestos."""
    print("=" * 70)
    print("📈 ESTIMACIÓN DE IMPACTO")
    print("=" * 70 + "\n")

    session = SessionLocal()
    try:
        # Contar registros por tabla
        from infrastructure.database.models import Guardia, Profesor, Zona

        count_profesores = session.query(Profesor).count()
        count_guardias = session.query(Guardia).count()
        count_zonas = session.query(Zona).count()

        print("📊 Tamaño de las tablas:")
        print(f"   • profesores: {count_profesores} registros")
        print(f"   • guardias: {count_guardias} registros")
        print(f"   • zonas: {count_zonas} registros\n")

        print("🚀 Impacto esperado de los índices:\n")

        if count_guardias < 1000:
            print("   ⚠️  Con menos de 1,000 guardias, el impacto será mínimo")
            print("      Las consultas ya son rápidas sin índices.\n")
        elif count_guardias < 10000:
            print("   ✅ Con 1K-10K guardias, los índices mejorarán notablemente:")
            print("      • Consultas por profesor: 50-70% más rápidas")
            print("      • Consultas por fecha: 40-60% más rápidas")
            print("      • Joins: 30-50% más rápidas\n")
        else:
            print("   🔥 Con más de 10K guardias, los índices son CRÍTICOS:")
            print("      • Consultas por profesor: 80-90% más rápidas")
            print("      • Consultas por fecha: 70-85% más rápidas")
            print("      • Joins: 60-80% más rápidas\n")

        print("💾 Espacio adicional estimado:")
        # SQLite: ~1KB por 10 registros para índices simples
        espacio_kb = count_guardias * 9 * 0.1  # 9 índices propuestos
        print(f"   • Aproximadamente {espacio_kb:.1f} KB adicionales")
        print(f"   • {espacio_kb / 1024:.2f} MB adicionales\n")

    finally:
        session.close()


def main():
    """Función principal."""
    print("\n" + "=" * 70)
    print("🔍 ANÁLISIS DE OPTIMIZACIÓN DE BASE DE DATOS")
    print("=" * 70 + "\n")

    try:
        analyze_existing_indices()
        estimate_impact()
        recommend_indices()
        generate_alembic_migration()

        print("=" * 70)
        print("✅ ANÁLISIS COMPLETADO")
        print("=" * 70 + "\n")

        print("📋 PRÓXIMOS PASOS:")
        print("   1. Revisar los índices recomendados arriba")
        print("   2. Crear migración de Alembic con el código generado")
        print("   3. Ejecutar: alembic upgrade head")
        print("   4. Verificar mejora de rendimiento con queries reales\n")

    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
