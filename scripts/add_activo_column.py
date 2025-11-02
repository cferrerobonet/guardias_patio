#!/usr/bin/env python3
"""
Script para agregar la columna 'activo' a la tabla profesores.
Este campo indica si un profesor está activo en el sistema.
"""
import sqlite3
import sys
from pathlib import Path


def get_database_path():
    """Obtiene la ruta de la base de datos del usuario actual."""
    # Buscar la base de datos en el directorio data/users
    data_dir = Path(__file__).parent.parent / "data" / "users"

    # Buscar subdirectorios con base de datos
    for user_dir in data_dir.iterdir():
        if user_dir.is_dir():
            db_path = user_dir / "guardias_patio.db"
            if db_path.exists():
                return str(db_path)

    raise FileNotFoundError("No se encontró ninguna base de datos")


def add_activo_column():
    """Agrega la columna activo a la tabla profesores."""
    try:
        db_path = get_database_path()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"Conectando a base de datos: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(profesores)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'activo' in columns:
            print("⚠️  La columna 'activo' ya existe en la tabla profesores.")
            conn.close()
            return

        # Agregar la columna
        print("Agregando columna 'activo' a la tabla profesores...")
        cursor.execute("""
            ALTER TABLE profesores
            ADD COLUMN activo BOOLEAN NOT NULL DEFAULT 1
        """)

        # Actualizar todos los profesores existentes como activos
        print("Marcando todos los profesores existentes como activos...")
        cursor.execute("""
            UPDATE profesores
            SET activo = 1
            WHERE activo IS NULL
        """)

        conn.commit()
        print("✅ Columna 'activo' agregada exitosamente.")
        print("✅ Todos los profesores existentes marcados como activos.")

        # Verificar
        cursor.execute("SELECT COUNT(*) FROM profesores WHERE activo = 1")
        count = cursor.fetchone()[0]
        print(f"✅ {count} profesores activos en el sistema.")

    except sqlite3.Error as e:
        print(f"❌ Error al modificar la base de datos: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACIÓN: Agregar columna 'activo' a tabla profesores")
    print("=" * 60)
    add_activo_column()
    print("=" * 60)

