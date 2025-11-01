#!/usr/bin/env python3
"""
Script para actualizar recreos_permitidos en profesores existentes usando SQLite.

Asigna automáticamente los recreos según el turno del profesor:
- Mañana: R1 y R2 (recreos 1 y 2) en todos los días
- Tarde: R3 y R4 (recreos 3 y 4) en todos los días
- Mixto/Completo: R1, R2, R3 y R4 en todos los días
"""

import json
import sqlite3
from pathlib import Path


def generar_recreos_por_turno(turno: str) -> str:
    """
    Genera el JSON de recreos_permitidos según el turno.

    Args:
        turno: Turno del profesor ("mañana", "tarde", "mixto" o "completo")

    Returns:
        JSON con formato {"0": [1, 2], "1": [1, 2], ...}
    """
    recreos_dict = {}

    # Para todos los días (0-6: Lun-Dom)
    for dia in range(7):
        if turno.lower() == "mañana":
            # Recreos de mañana: 1 y 2
            recreos_dict[str(dia)] = [1, 2]
        elif turno.lower() == "tarde":
            # Recreos de tarde: 3 y 4
            recreos_dict[str(dia)] = [3, 4]
        elif turno.lower() in ["mixto", "completo"]:
            # Todos los recreos R1, R2, R3, R4
            recreos_dict[str(dia)] = [1, 2, 3, 4]

    return json.dumps(recreos_dict) if recreos_dict else ""


def actualizar_db(db_path: Path, db_id: str):
    """Actualizar profesores en una base de datos específica."""
    print(f"\n{'=' * 80}")
    print(f"ACTUALIZANDO BASE DE DATOS: {db_id}")
    print(f"{'=' * 80}")

    if not db_path.exists():
        print(f"  ⚠️  Base de datos no encontrada: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Obtener profesores
        cursor.execute(
            "SELECT id, nombre_completo, turno, recreos_permitidos FROM profesores"
        )
        profesores = cursor.fetchall()

        print(f"Total de profesores: {len(profesores)}")
        print()

        # Contadores
        actualizados = 0
        ya_tenian = 0
        por_turno = {"mañana": 0, "tarde": 0, "mixto": 0, "completo": 0}

        print("ANALIZANDO PROFESORES...")
        print("-" * 80)

        for profesor_id, nombre, turno, recreos_actual in profesores:
            turno_lower = turno.lower()

            # Generar recreos según turno
            recreos_esperados = generar_recreos_por_turno(turno_lower)

            # Verificar si ya tiene los recreos correctos
            if recreos_actual and recreos_actual.strip():
                # Verificar si son correctos
                try:
                    recreos_dict = json.loads(recreos_actual)
                    esperados_dict = json.loads(recreos_esperados)

                    if recreos_dict == esperados_dict:
                        ya_tenian += 1
                        print(f"  ✓ {nombre} ({turno}): Ya tiene recreos correctos")
                        continue
                except json.JSONDecodeError:
                    pass

            # Actualizar
            cursor.execute(
                "UPDATE profesores SET recreos_permitidos = ? WHERE id = ?",
                (recreos_esperados, profesor_id),
            )

            actualizados += 1
            por_turno[turno_lower] = por_turno.get(turno_lower, 0) + 1

            # Mostrar recreos asignados
            recreos_dict = json.loads(recreos_esperados)
            recreos_ejemplo = recreos_dict.get("0", [])
            print(f"  🔄 {nombre} ({turno}): Asignados recreos {recreos_ejemplo}")

        # Mostrar resumen
        print()
        print("=" * 80)
        print("RESUMEN DE CAMBIOS")
        print("=" * 80)
        print(f"  Total de profesores: {len(profesores)}")
        print(f"  Ya tenían recreos correctos: {ya_tenian}")
        print(f"  Actualizados: {actualizados}")

        if actualizados > 0:
            print()
            print("ACTUALIZADOS POR TURNO:")
            for turno, count in por_turno.items():
                if count > 0:
                    print(f"  - {turno.capitalize()}: {count}")

        # Confirmar cambios
        if actualizados > 0:
            print()
            respuesta = input(
                "¿Deseas guardar estos cambios en la base de datos? (s/n): "
            )

            if respuesta.lower() in ["s", "si", "sí", "y", "yes"]:
                conn.commit()
                print()
                print("✅ CAMBIOS GUARDADOS CORRECTAMENTE")
                print(
                    f"Ahora todos los profesores de {db_id} tienen recreos correctos."
                )
            else:
                conn.rollback()
                print()
                print("❌ CAMBIOS CANCELADOS")
        else:
            print()
            print("✓ TODOS LOS PROFESORES YA TIENEN RECREOS CORRECTOS")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


def main():
    """Ejecutar actualización de recreos_permitidos."""
    print("=" * 80)
    print("ACTUALIZACIÓN DE RECREOS_PERMITIDOS EN PROFESORES (SQLite)")
    print("=" * 80)

    base_path = Path(__file__).parent.parent / "data"

    # Buscar todas las carpetas de usuarios
    db_ids = []
    for item in base_path.iterdir():
        if item.is_dir() and item.name != "users":
            db_path = item / "guardias_patio.db"
            if db_path.exists():
                db_ids.append((item.name, db_path))

    if not db_ids:
        print("⚠️  No se encontraron bases de datos")
        return

    print(f"\nSe encontraron {len(db_ids)} base(s) de datos:")
    for db_id, db_path in db_ids:
        print(f"  - {db_id}")

    print()

    # Actualizar cada BD
    for db_id, db_path in db_ids:
        actualizar_db(db_path, db_id)

    print()
    print("=" * 80)
    print("✓ PROCESO COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
