#!/usr/bin/env python3
"""
Script para regenerar guardias con algoritmo v3.1 mejorado.
Ejecuta la asignación con priorización de fecha_inicio y validación completa.
"""

import sys
from pathlib import Path

# Añadir src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from infrastructure.database.models import Configuracion, Profesor
from services.asignador_guardias_v3_simple import generar_guardias_v3_simple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def callback_progreso(porcentaje: int, mensaje: str):
    """Callback simple para mostrar progreso."""
    print(f"[{porcentaje:3d}%] {mensaje}")


def main():
    print("=" * 80)
    print("🔄 REGENERACIÓN DE GUARDIAS - ALGORITMO V3.1 MEJORADO")
    print("=" * 80)
    print()

    # Conectar a la BD
    db_path = Path("data/users/0db13e2857239ed8/guardias_patio.db")
    if not db_path.exists():
        print(f"❌ Error: No se encuentra la base de datos en {db_path}")
        return 1

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Verificar configuración
        config = session.query(Configuracion).first()
        if not config:
            print("❌ Error: No hay configuración activa")
            return 1

        print(f"📅 Curso: {config.fecha_inicio_curso} a {config.fecha_fin_curso}")
        print(f"🆔 Configuración ID: {config.id}")

        # Verificar profesores
        profesores = session.query(Profesor).filter(Profesor.activo).all()
        print(f"👥 Profesores activos: {len(profesores)}")

        profesores_con_fecha = [p for p in profesores if p.fecha_inicio_guardias]
        print(f"📌 Profesores con fecha_inicio: {len(profesores_con_fecha)}")

        print()
        print("-" * 80)
        print("🚀 INICIANDO GENERACIÓN DE GUARDIAS...")
        print("-" * 80)
        print()

        # Ejecutar algoritmo v3.1 con callback de progreso
        # Parámetros: session, configuracion_id, reportar_progreso (opcional)
        guardias, resumen = generar_guardias_v3_simple(session, config.id, callback_progreso)

        print()
        print("=" * 80)
        print("✅ REGENERACIÓN COMPLETADA")
        print("=" * 80)
        print()
        print(f"📊 Total guardias generadas: {len(guardias)}")
        print(
            f"👥 Profesores con guardias: {sum(1 for v in resumen.values() if v > 0)}/{len(profesores)}"
        )
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR DURANTE LA GENERACIÓN")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
