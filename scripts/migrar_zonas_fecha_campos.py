#!/usr/bin/env python3
"""
Migrar todas las bases de datos para añadir campos fecha_inicio y fecha_fin a tabla zonas.
"""

import sqlite3
import sys
from pathlib import Path

# Lista de bases de datos a migrar
DBS = [
    "./data/66f06c9433d74e80/guardias.db",
    "./data/users/0db13e2857239ed8/guardias.db",
    "./data/users/0db13e2857239ed8/guardias_patio.db",
    "./data/users/66f06c9433d74e80/guardias_patio.db",
    "./guardias_patio.db",
    "./src/guardias_patio.db",
]


def migrar_zona_campos(db_path: str) -> bool:
    """Migra una BD añadiendo campos fecha_inicio y fecha_fin a tabla zonas."""
    if not Path(db_path).exists():
        print(f"  ⚠ BD no existe: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar si existe la tabla zonas
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='zonas'"
        )
        if not cursor.fetchone():
            print("  ⚠ No tiene tabla 'zonas'")
            conn.close()
            return False

        # Obtener columnas actuales
        cursor.execute("PRAGMA table_info(zonas)")
        columns = [col[1] for col in cursor.fetchall()]

        cambios = 0

        # Añadir fecha_inicio si no existe
        if "fecha_inicio" not in columns:
            cursor.execute("ALTER TABLE zonas ADD COLUMN fecha_inicio DATE")
            print("    + Añadida columna fecha_inicio")
            cambios += 1
        else:
            print("    ✓ Ya tiene fecha_inicio")

        # Añadir fecha_fin si no existe
        if "fecha_fin" not in columns:
            cursor.execute("ALTER TABLE zonas ADD COLUMN fecha_fin DATE")
            print("    + Añadida columna fecha_fin")
            cambios += 1
        else:
            print("    ✓ Ya tiene fecha_fin")

        if cambios > 0:
            conn.commit()
            print(f"  ✓ Migración exitosa ({cambios} columnas añadidas)")
        else:
            print("  ✓ Ya estaba migrada")

        conn.close()
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    print("=" * 80)
    print("MIGRACIÓN: Añadir campos fecha_inicio y fecha_fin a tabla zonas")
    print("=" * 80)
    print()

    exitosas = 0
    fallidas = 0

    for db_path in DBS:
        print(f"Procesando: {db_path}")
        if migrar_zona_campos(db_path):
            exitosas += 1
        else:
            fallidas += 1
        print()

    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"✅ Exitosas: {exitosas}")
    print(f"❌ Fallidas: {fallidas}")
    print(f"📊 Total: {len(DBS)}")
    print()

    if fallidas > 0:
        print("⚠️  Algunas migraciones fallaron. Revisar errores arriba.")
        return 1
    else:
        print("🎉 Todas las migraciones completadas exitosamente!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
