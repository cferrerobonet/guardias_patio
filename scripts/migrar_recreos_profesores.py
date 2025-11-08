#!/usr/bin/env python3
"""
Script de migración: Rellenar recreos_permitidos para profesores antiguos.

Este script actualiza todos los profesores que tienen recreos_permitidos NULL o vacío,
asignándoles los valores por defecto según su turno:
- Mañana: R1, R2 (todos los días L-V)
- Tarde: R3, R4 (todos los días L-V)
- Mixto: R1, R2, R3, R4 (todos los días L-V)

Uso:
    python scripts/migrar_recreos_profesores.py [user_id]

Si no se proporciona user_id, intentará usar el del archivo users.json
"""

import json
import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))

import hashlib

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database.db_manager import USER_DATA_DIR


def obtener_recreos_por_defecto(turno: str) -> dict:
    """
    Obtener recreos por defecto según turno.

    Returns:
        Dict con formato {0: ['R1', 'R2'], 1: ['R1', 'R2'], ...}
        donde las claves son días de la semana (0=Lunes, 4=Viernes)
    """
    # Normalizar turno a minúsculas para comparación
    turno_lower = turno.lower() if turno else ""

    # Definir recreos según turno
    if turno_lower == "mañana":
        recreos = ["R1", "R2"]
    elif turno_lower == "tarde":
        recreos = ["R3", "R4"]
    else:  # Mixto o cualquier otro
        recreos = ["R1", "R2", "R3", "R4"]

    # Aplicar a todos los días de la semana (L-V)
    return {
        dia: recreos.copy()
        for dia in range(5)  # 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes
    }


def migrar_recreos_profesores():
    """Actualizar recreos_permitidos para todos los profesores que lo tienen vacío."""

    # Intentar obtener user_id
    user_id = None
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        # Intentar leer del archivo users.json
        users_file = root_dir / "users.json"
        if users_file.exists():
            try:
                with open(users_file) as f:
                    users_data = json.load(f)
                    if users_data and len(users_data) > 0:
                        user_id = list(users_data.keys())[0]
                        print(f"Usando usuario del archivo users.json: {user_id}")
            except Exception as e:
                print(f"Error leyendo users.json: {e}")

    if not user_id:
        print("ERROR: No se pudo determinar el user_id")
        print("Uso: python scripts/migrar_recreos_profesores.py [user_id]")
        sys.exit(1)

    # Calcular hash del usuario (mismo algoritmo que db_manager)
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]

    # Conectar directamente a la BD sin ejecutar migraciones
    db_path = USER_DATA_DIR / user_hash / "guardias_patio.db"

    if not db_path.exists():
        print(f"❌ ERROR: No existe base de datos para usuario {user_id}")
        print(f"   Ruta esperada: {db_path}")
        sys.exit(1)

    print(f"\n🔧 Conectando directamente a: {db_path}")

    # Crear conexión directa sin migraciones
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Obtener todos los profesores que necesitan actualización usando SQL directo
        query = text("""
            SELECT id, nombre_completo, turno, recreos_permitidos
            FROM profesores
        """)

        print("\n🔍 Ejecutando query...")
        result = session.execute(query)
        profesores_data = result.fetchall()
        print(f"🔍 Obtenidos {len(profesores_data)} registros")

        actualizados = 0
        ya_tenian_datos = 0
        errores = []

        print(f"\n{'='*70}")
        print("MIGRACIÓN DE RECREOS PERMITIDOS PARA PROFESORES")
        print(f"{'='*70}\n")
        print(f"Total de profesores en BD: {len(profesores_data)}\n")

        for prof_id, nombre, turno, recreos_actual in profesores_data:
            # Verificar si ya tiene datos
            tiene_datos = False

            if recreos_actual:
                try:
                    datos = json.loads(recreos_actual)
                    if datos and isinstance(datos, dict) and len(datos) > 0:
                        tiene_datos = True
                except (json.JSONDecodeError, TypeError):
                    pass

            if tiene_datos:
                ya_tenian_datos += 1
                print(f"  ✓ {nombre:<40} → Ya tiene datos")
                continue

            # No tiene datos → asignar por defecto según turno
            try:
                recreos_defecto = obtener_recreos_por_defecto(turno)
                recreos_json = json.dumps(recreos_defecto)

                # Actualizar con SQL directo
                update_query = text("""
                    UPDATE profesores
                    SET recreos_permitidos = :recreos
                    WHERE id = :prof_id
                """)
                session.execute(update_query, {"recreos": recreos_json, "prof_id": prof_id})

                actualizados += 1

                # Mostrar recreos asignados (son iguales para todos los días L-V)
                recreos_str = ", ".join(recreos_defecto[0])
                print(f"  ✅ {nombre:<40} → Turno {turno.lower():<8} → {recreos_str} (L-V)")

            except Exception as e:
                errores.append(f"{nombre}: {str(e)}")
                print(f"  ❌ {nombre:<40} → ERROR: {str(e)}")

        # Confirmar cambios
        if actualizados > 0:
            print(f"\n{'-'*70}")
            respuesta = input(f"\n¿Confirmar actualización de {actualizados} profesor(es)? (s/N): ")

            if respuesta.lower() in ['s', 'si', 'sí', 'yes', 'y']:
                session.commit()
                print("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
                print(f"   • Profesores actualizados: {actualizados}")
                print(f"   • Profesores que ya tenían datos: {ya_tenian_datos}")
                if errores:
                    print(f"   • Errores: {len(errores)}")
                    for error in errores:
                        print(f"     - {error}")
            else:
                session.rollback()
                print("\n⚠️  MIGRACIÓN CANCELADA - No se guardaron cambios")
        else:
            print("\n✓ No hay profesores para actualizar")
            print(f"  Todos los {ya_tenian_datos} profesores ya tienen datos de recreos")

        print(f"\n{'='*70}\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR DURANTE LA MIGRACIÓN: {str(e)}")
        raise

    finally:
        session.close()


if __name__ == "__main__":
    migrar_recreos_profesores()
