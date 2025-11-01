#!/usr/bin/env python3
"""
Script para actualizar recreos_permitidos en profesores existentes.

Asigna automáticamente los recreos según el turno del profesor:
- Mañana: R1 y R2 (recreos 1 y 2) en todos los días
- Tarde: R3 y R4 (recreos 3 y 4) en todos los días
- Mixto/Completo: R1, R2, R3 y R4 en todos los días
"""

import json
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
            # Todos los recreos
            recreos_dict[str(dia)] = [1, 2, 3, 4]

    return json.dumps(recreos_dict) if recreos_dict else ""


def main():
    """Ejecutar actualización de recreos_permitidos."""
    print("=" * 80)
    print("ACTUALIZACIÓN DE RECREOS_PERMITIDOS EN PROFESORES EXISTENTES")
    print("=" * 80)
    print()

    # Ruta al JSON
    json_path = Path(__file__).parent.parent / "data/0db13e2857239ed8/guardias_patio_data.json"

    # Cargar datos
    with open(json_path, 'r') as f:
        data = json.load(f)

    profesores = data.get("profesores", [])

    print(f"Total de profesores en la base de datos: {len(profesores)}")
    print()

    # Contadores
    actualizados = 0
    ya_tenian = 0
    por_turno = {"mañana": 0, "tarde": 0, "mixto": 0, "completo": 0}

    print("ANALIZANDO PROFESORES...")
    print("-" * 80)

    for profesor in profesores:
        nombre = profesor.get("nombre_completo", "Sin nombre")
        turno = profesor.get("turno", "").lower()
        recreos_actual = profesor.get("recreos_permitidos", "")

        # Verificar si ya tiene recreos_permitidos
        if recreos_actual and recreos_actual.strip():
            ya_tenian += 1
            print(f"  ✓ {nombre} ({turno}): Ya tiene recreos configurados")
        else:
            # Generar y asignar recreos según turno
            recreos_json = generar_recreos_por_turno(turno)

            if recreos_json:
                profesor["recreos_permitidos"] = recreos_json
                actualizados += 1
                por_turno[turno] = por_turno.get(turno, 0) + 1

                # Mostrar recreos asignados
                recreos_dict = json.loads(recreos_json)
                recreos_ejemplo = recreos_dict.get("0", [])
                print(f"  🔄 {nombre} ({turno}): Asignados recreos {recreos_ejemplo}")

    # Mostrar resumen
    if actualizados > 0:
        print()
        print("=" * 80)
        print("RESUMEN DE CAMBIOS")
        print("=" * 80)
        print(f"  Total de profesores: {len(profesores)}")
        print(f"  Ya tenían recreos configurados: {ya_tenian}")
        print(f"  Actualizados: {actualizados}")
        print()
        print("ACTUALIZADOS POR TURNO:")
        for turno, count in por_turno.items():
            if count > 0:
                print(f"  - {turno.capitalize()}: {count}")
        print()

        # Pedir confirmación
        respuesta = input("¿Deseas guardar estos cambios en el archivo JSON? (s/n): ")

        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            # Guardar cambios
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print()
            print("✅ CAMBIOS GUARDADOS CORRECTAMENTE")
            print()
            print(f"Archivo actualizado: {json_path}")
            print("Ahora todos los profesores tienen recreos_permitidos configurados.")
            print("Los profesores de tarde ya podrán recibir guardias asignadas.")
        else:
            print()
            print("❌ CAMBIOS CANCELADOS")
            print("No se realizaron modificaciones en el archivo.")
    else:
        print()
        print("=" * 80)
        print("✓ TODOS LOS PROFESORES YA TIENEN RECREOS CONFIGURADOS")
        print("=" * 80)
        print("No es necesario realizar ninguna actualización.")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
