"""
Script de migración: Convertir recreos de strings a enteros.

PROBLEMA:
Los profesores antiguos tienen recreos_permitidos con formato incorrecto:
  {"0": ["R1", "R2"], "1": ["R3", "R4"]}  ❌ INCORRECTO

Deben ser enteros:
  {"0": [1, 2], "1": [3, 4]}  ✅ CORRECTO

Este script:
1. Lee todos los profesores con recreos_permitidos
2. Detecta si tienen strings ("R1", "R2", etc.)
3. Los convierte a enteros (1, 2, 3, 4)
4. Actualiza la base de datos

USO:
    python scripts/migrar_recreos_strings_a_int.py
"""

import hashlib
import json
import re
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def calcular_hash_usuario(username: str) -> str:
    """Calcular el hash SHA256 del nombre de usuario."""
    return hashlib.sha256(username.encode()).hexdigest()


def convertir_recreo_string_a_int(recreo_str: str) -> int:
    """
    Convierte un recreo en formato string a entero.

    Ejemplos:
        "R1" -> 1
        "R2" -> 2
        "recreo1" -> 1
        "1" -> 1
    """
    # Intentar extraer el número del string
    match = re.search(r'\d+', recreo_str)
    if match:
        return int(match.group())

    # Si ya es un entero, devolverlo
    if isinstance(recreo_str, int):
        return recreo_str

    # Si no se puede convertir, error
    raise ValueError(f"No se pudo convertir '{recreo_str}' a entero")


def corregir_recreos_permitidos(recreos_json: str) -> tuple[str, bool]:
    """
    Corrige el formato de recreos_permitidos si es necesario.

    Args:
        recreos_json: String JSON con recreos

    Returns:
        Tupla (nuevo_json, fue_modificado)
    """
    if not recreos_json:
        return recreos_json, False

    try:
        recreos = json.loads(recreos_json)
    except json.JSONDecodeError:
        print(f"  ⚠️  JSON inválido: {recreos_json[:100]}")
        return recreos_json, False

    modificado = False

    # Si es un diccionario (por día)
    if isinstance(recreos, dict):
        nuevo_dict = {}
        for dia, lista_recreos in recreos.items():
            if isinstance(lista_recreos, list):
                nuevos_recreos = []
                for recreo in lista_recreos:
                    if isinstance(recreo, str):
                        # Convertir string a int
                        try:
                            nuevo_recreo = convertir_recreo_string_a_int(recreo)
                            nuevos_recreos.append(nuevo_recreo)
                            modificado = True
                        except ValueError as e:
                            print(f"  ⚠️  Error convirtiendo '{recreo}': {e}")
                            nuevos_recreos.append(recreo)
                    else:
                        nuevos_recreos.append(recreo)
                nuevo_dict[dia] = nuevos_recreos
            else:
                nuevo_dict[dia] = lista_recreos

        if modificado:
            return json.dumps(nuevo_dict), True
        return recreos_json, False

    # Si es una lista simple
    elif isinstance(recreos, list):
        nuevos_recreos = []
        for recreo in recreos:
            if isinstance(recreo, str):
                try:
                    nuevo_recreo = convertir_recreo_string_a_int(recreo)
                    nuevos_recreos.append(nuevo_recreo)
                    modificado = True
                except ValueError as e:
                    print(f"  ⚠️  Error convirtiendo '{recreo}': {e}")
                    nuevos_recreos.append(recreo)
            else:
                nuevos_recreos.append(recreo)

        if modificado:
            return json.dumps(nuevos_recreos), True
        return recreos_json, False

    return recreos_json, False


def migrar_base_datos(db_path: str):
    """Ejecuta la migración en una base de datos específica."""
    print(f"\n{'='*80}")
    print(f"Migrando base de datos: {db_path}")
    print(f"{'='*80}\n")

    # Crear engine y sesión
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Obtener todos los profesores con recreos_permitidos
        result = session.execute(text("""
            SELECT id, nombre_completo, recreos_permitidos
            FROM profesores
            WHERE recreos_permitidos IS NOT NULL
            AND recreos_permitidos != ''
            ORDER BY id
        """))

        profesores = result.fetchall()
        total = len(profesores)
        modificados = 0
        sin_cambios = 0
        errores = 0

        print(f"📊 Total de profesores con recreos: {total}\n")

        for profesor_id, nombre, recreos_json in profesores:
            print(f"[{profesor_id:3d}] {nombre}")

            # Intentar corregir
            nuevo_json, fue_modificado = corregir_recreos_permitidos(recreos_json)

            if fue_modificado:
                print("  ✅ CORREGIDO")
                print(f"     Antes: {recreos_json[:80]}...")
                print(f"     Después: {nuevo_json[:80]}...")

                # Actualizar en la base de datos
                try:
                    session.execute(
                        text("UPDATE profesores SET recreos_permitidos = :nuevo WHERE id = :id"),
                        {"nuevo": nuevo_json, "id": profesor_id}
                    )
                    modificados += 1
                except Exception as e:
                    print(f"  ❌ Error al actualizar: {e}")
                    errores += 1
            else:
                print("  ⏭️  Sin cambios necesarios")
                sin_cambios += 1

            print()

        # Confirmar cambios
        if modificados > 0:
            session.commit()
            print(f"\n{'='*80}")
            print("✅ Migración completada exitosamente")
            print(f"{'='*80}")
            print("📊 Resumen:")
            print(f"   - Total procesados: {total}")
            print(f"   - Modificados: {modificados}")
            print(f"   - Sin cambios: {sin_cambios}")
            print(f"   - Errores: {errores}")
            print(f"{'='*80}\n")
        else:
            print(f"\n{'='*80}")
            print("ℹ️  No se encontraron registros para modificar")
            print(f"{'='*80}\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR durante la migración: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("🔧 MIGRACIÓN: Recreos de strings a enteros")
    print("="*80)

    # Detectar usuario actual (usando el mismo método que el sistema)
    import getpass
    username = getpass.getuser()
    user_hash = calcular_hash_usuario(username)

    print(f"\n👤 Usuario detectado: {username}")
    print(f"🔑 Hash: {user_hash}")

    # Ruta a la base de datos del usuario
    db_path = Path(__file__).parent.parent / "data" / "users" / user_hash / "guardias_patio.db"

    if not db_path.exists():
        print(f"\n❌ ERROR: No se encontró la base de datos en: {db_path}")
        print("\nPor favor, verifica que:")
        print("  1. Has iniciado sesión en la aplicación al menos una vez")
        print("  2. La ruta del proyecto es correcta")
        return

    print(f"📁 Base de datos: {db_path}")

    # Confirmar antes de proceder
    respuesta = input("\n¿Proceder con la migración? (s/N): ").strip().lower()
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("\n❌ Migración cancelada por el usuario")
        return

    # Ejecutar migración
    migrar_base_datos(str(db_path))


if __name__ == "__main__":
    main()
