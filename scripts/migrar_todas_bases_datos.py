#!/usr/bin/env python3
"""
Script para migrar TODAS las bases de datos de usuarios.

Añade el campo algoritmo_asignacion a todas las BDs existentes.
"""

import os
import sqlite3
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def migrar_base_datos(db_path: str) -> bool:
    """
    Migra una base de datos añadiendo el campo algoritmo_asignacion.
    
    Args:
        db_path: Ruta a la base de datos
        
    Returns:
        True si se migró exitosamente, False si ya estaba migrada o hubo error
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si el campo ya existe
        cursor.execute("PRAGMA table_info(configuracion)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'algoritmo_asignacion' in columns:
            print(f"  ⚠️  Ya migrada (campo ya existe)")
            conn.close()
            return False
        
        # Añadir el campo
        cursor.execute("""
            ALTER TABLE configuracion 
            ADD COLUMN algoritmo_asignacion VARCHAR DEFAULT 'v2.9' NOT NULL
        """)
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Migrada exitosamente")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Migrar todas las bases de datos de usuarios."""
    print("=" * 80)
    print("MIGRACIÓN DE BASES DE DATOS - Campo algoritmo_asignacion")
    print("=" * 80)
    print()
    
    # Ruta base de datos
    data_dir = Path(__file__).parent.parent / "data"
    
    if not data_dir.exists():
        print(f"❌ No se encontró el directorio data: {data_dir}")
        return
    
    # Buscar todas las bases de datos
    db_files = []
    
    # Buscar en data/users/*/guardias_patio.db
    db_files.extend(list(data_dir.glob("users/*/guardias_patio.db")))
    
    # Buscar también guardias.db si existen
    db_files.extend(list(data_dir.glob("users/*/guardias.db")))
    
    if not db_files:
        print(f"❌ No se encontraron bases de datos en: {data_dir}")
        print(f"   Buscando en: {data_dir}/users/*/guardias_patio.db")
        print(f"   Buscando en: {data_dir}/users/*/guardias.db")
        return
    
    print(f"📊 Encontradas {len(db_files)} bases de datos")
    print()
    
    migradas = 0
    ya_migradas = 0
    errores = 0
    
    for db_file in db_files:
        user_id = db_file.parent.name
        print(f"🔧 Migrando BD de usuario: {user_id}")
        print(f"   Ruta: {db_file}")
        
        resultado = migrar_base_datos(str(db_file))
        
        if resultado:
            migradas += 1
        elif resultado is False and "Ya migrada" in str(resultado):
            ya_migradas += 1
        else:
            errores += 1
        
        print()
    
    # Resumen
    print("=" * 80)
    print("RESUMEN DE MIGRACIÓN")
    print("=" * 80)
    print(f"✅ Migradas exitosamente: {migradas}")
    print(f"⚠️  Ya estaban migradas: {ya_migradas}")
    print(f"❌ Errores: {errores}")
    print(f"📊 Total: {len(db_files)}")
    print()
    
    if migradas > 0:
        print("🎉 ¡Migración completada! Ahora puedes abrir la aplicación sin errores.")
    elif ya_migradas == len(db_files):
        print("✅ Todas las bases de datos ya estaban migradas.")
    else:
        print("⚠️  Algunas bases de datos tuvieron errores. Revisa los mensajes arriba.")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
