#!/usr/bin/env python3
"""
Script para regenerar guardias con el algoritmo v2.9 equitativo.

Uso:
    python3 scripts/regenerar_guardias.py --db data/users/66f06c9433d74e80/guardias_patio.db
    python3 scripts/regenerar_guardias.py --db data/users/66f06c9433d74e80/guardias_patio.db --backup
    python3 scripts/regenerar_guardias.py --db data/users/66f06c9433d74e80/guardias_patio.db --validate-only
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.database.models import Guardia
from services.asignador_guardias import generar_calendario_guardias
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def backup_database(db_path: str) -> str:
    """
    Crea un backup de la base de datos.

    Args:
        db_path: Ruta a la base de datos

    Returns:
        Ruta al archivo de backup
    """
    import shutil

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    print(f"📦 Creando backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print("✅ Backup creado exitosamente")

    return backup_path


def regenerar_guardias(db_path: str, crear_backup: bool = True, validate_only: bool = False):
    """
    Regenera las guardias con el algoritmo v2.9.

    Args:
        db_path: Ruta a la base de datos
        crear_backup: Si True, crea backup antes de regenerar
        validate_only: Si True, solo valida sin regenerar
    """
    print("=" * 100)
    print("REGENERACIÓN DE GUARDIAS - ALGORITMO v2.9 EQUITATIVO")
    print("=" * 100)

    # Verificar que el archivo existe
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Base de datos no encontrada: {db_path}")
        sys.exit(1)

    # Crear backup si se solicita
    if crear_backup and not validate_only:
        backup_path = backup_database(db_path)
        print(f"💾 Backup guardado en: {backup_path}")
        print()

    # Conectar a la base de datos
    print(f"🔌 Conectando a: {db_path}")
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Contar guardias actuales
        guardias_actuales = session.query(Guardia).count()
        print(f"📊 Guardias actuales: {guardias_actuales}")

        if validate_only:
            print("\n⚠️  Modo VALIDACIÓN - No se regenerarán guardias")
            print("   Ejecuta sin --validate-only para regenerar")
            return

        # Eliminar guardias actuales
        print(f"\n🗑️  Eliminando {guardias_actuales} guardias actuales...")
        session.query(Guardia).delete()
        session.commit()
        print("✅ Guardias eliminadas")

        # Regenerar guardias
        print("\n🔄 Regenerando guardias con algoritmo v2.9...")
        print("   (Esto puede tardar 30-60 segundos)")
        print()

        def progress_callback(porcentaje: int, mensaje: str):
            """Callback para mostrar progreso."""
            # Mostrar cada 5%
            if porcentaje % 5 == 0 or porcentaje >= 95:
                print(f"   [{porcentaje:3d}%] {mensaje}")

        # Generar calendario
        calendario, asignadas = generar_calendario_guardias(
            session, progress_callback=progress_callback
        )

        # Guardar guardias
        print(f"\n💾 Guardando {len(calendario)} guardias en base de datos...")
        for guardia in calendario:
            session.add(guardia)
        session.commit()

        print(f"✅ {len(calendario)} guardias generadas y guardadas")

        # Estadísticas finales
        print("\n" + "=" * 100)
        print("RESUMEN DE REGENERACIÓN")
        print("=" * 100)
        print(f"Guardias anteriores: {guardias_actuales}")
        print(f"Guardias nuevas:     {len(calendario)}")
        print(f"Diferencia:          {len(calendario) - guardias_actuales:+d}")

        # Mostrar distribución por profesor
        print("\n📊 DISTRIBUCIÓN POR PROFESOR:")
        print(f"   Total profesores con guardias: {len([a for a in asignadas.values() if a > 0])}")
        print(f"   Guardias mínimas: {min(asignadas.values()) if asignadas else 0}")
        print(f"   Guardias máximas: {max(asignadas.values()) if asignadas else 0}")
        print(
            f"   Guardias promedio: {sum(asignadas.values()) / len(asignadas):.1f}"
            if asignadas
            else 0
        )

        print("\n✅ REGENERACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 100)

    except Exception as e:
        print(f"\n❌ ERROR durante la regeneración: {e}")
        import traceback

        traceback.print_exc()

        if not validate_only:
            print("\n⚠️  La base de datos puede estar en estado inconsistente")
            if crear_backup:
                print(f"   Puedes restaurar el backup: {backup_path}")

        sys.exit(1)

    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Regenerar guardias con algoritmo v2.9 equitativo")
    parser.add_argument(
        "--db", required=True, help="Ruta a la base de datos (ej: data/users/XXX/guardias_patio.db)"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Crear backup antes de regenerar (recomendado)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Solo validar, no regenerar (útil para pruebas)",
    )

    args = parser.parse_args()

    try:
        regenerar_guardias(args.db, crear_backup=args.backup, validate_only=args.validate_only)
    except KeyboardInterrupt:
        print("\n\n⚠️  Regeneración cancelada por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
