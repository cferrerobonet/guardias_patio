#!/usr/bin/env python3
"""
Script para actualizar COMPLETAMENTE los profesores:
1. Campo 'recreos' (lista simple: [1, 2] para mañana, [3, 4] para tarde)
2. Campo 'recreos_permitidos' (matriz JSON de horarios)
3. Campo 'cuota_anual' (calculada automáticamente)

IMPORTANTE: Este script actualiza la estructura de datos completa.
"""

import json
from pathlib import Path


def generar_recreos_por_turno(turno: str) -> list:
    """
    Genera la lista de recreos según el turno.
    
    Args:
        turno: Turno del profesor ("mañana", "tarde", "mixto" o "completo")
        
    Returns:
        Lista de recreos [1, 2] o [3, 4] o [1, 2, 3, 4]
    """
    if turno.lower() == "mañana":
        return [1, 2]
    elif turno.lower() == "tarde":
        return [3, 4]
    elif turno.lower() in ["mixto", "completo"]:
        return [1, 2, 3, 4]
    return []


def generar_recreos_permitidos_por_turno(turno: str) -> str:
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
            recreos_dict[str(dia)] = [1, 2]
        elif turno.lower() == "tarde":
            recreos_dict[str(dia)] = [3, 4]
        elif turno.lower() in ["mixto", "completo"]:
            recreos_dict[str(dia)] = [1, 2, 3, 4]

    return json.dumps(recreos_dict) if recreos_dict else ""


def calcular_cuota_anual(configuracion: dict) -> float:
    """
    Calcula la cuota anual base según la configuración.
    
    Para simplificar, usamos la fórmula:
    cuota = días_lectivos * recreos_por_día * profesores_por_recreo / num_profesores
    
    Args:
        configuracion: Diccionario con la configuración
        
    Returns:
        Cuota anual calculada
    """
    # Por ahora usamos un valor fijo razonable
    # En la aplicación real esto se calcula con el algoritmo completo
    return 30.0  # Valor por defecto razonable


def main():
    """Ejecutar actualización completa de profesores."""
    print("=" * 80)
    print("ACTUALIZACIÓN COMPLETA DE PROFESORES")
    print("=" * 80)
    print()

    # Ruta al JSON
    json_path = Path(__file__).parent.parent / "data/0db13e2857239ed8/guardias_patio_data.json"
    
    if not json_path.exists():
        print(f"❌ No se encontró el archivo: {json_path}")
        return
    
    # Cargar datos
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    profesores = data.get('profesores', [])
    configuracion = data.get('configuracion', {})
    
    print(f"Total profesores a actualizar: {len(profesores)}")
    print()
    
    # Contadores
    actualizados = 0
    por_turno = {"mañana": 0, "tarde": 0, "mixto": 0, "otro": 0}
    
    # Actualizar cada profesor
    for profesor in profesores:
        turno = profesor.get('turno', '').lower()
        nombre = profesor.get('nombre_completo', 'Sin nombre')
        
        # 1. Actualizar campo 'recreos' (lista simple)
        recreos_lista = generar_recreos_por_turno(turno)
        profesor['recreos'] = recreos_lista
        
        # 2. Actualizar campo 'recreos_permitidos' (JSON de matriz)
        recreos_json = generar_recreos_permitidos_por_turno(turno)
        profesor['recreos_permitidos'] = recreos_json
        
        # 3. Actualizar cuota_anual si está en 0 o None
        if not profesor.get('cuota_anual') or profesor.get('cuota_anual') == 0:
            profesor['cuota_anual'] = calcular_cuota_anual(configuracion)
        
        # Contar
        actualizados += 1
        if turno in por_turno:
            por_turno[turno] += 1
        else:
            por_turno["otro"] += 1
        
        # Mostrar primeros 5 de cada turno
        if por_turno.get(turno, 0) <= 5:
            recreos_str = ','.join(map(str, recreos_lista))
            print(f"  ✓ {nombre:40s} | Turno: {turno:8s} | Recreos: {recreos_str}")
    
    # Guardar cambios
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 80)
    print("RESUMEN DE ACTUALIZACIÓN")
    print("=" * 80)
    print(f"  ✓ Total actualizados: {actualizados}")
    print(f"  ✓ Mañana: {por_turno['mañana']}")
    print(f"  ✓ Tarde: {por_turno['tarde']}")
    print(f"  ✓ Mixto: {por_turno['mixto']}")
    if por_turno['otro'] > 0:
        print(f"  ⚠ Otros turnos: {por_turno['otro']}")
    print()
    print(f"  ✓ Archivo guardado: {json_path}")
    print()
    print("=" * 80)
    print("✅ ACTUALIZACIÓN COMPLETADA")
    print("=" * 80)
    print()
    print("📌 SIGUIENTE PASO:")
    print("   Abre la aplicación y regenera las guardias para aplicar los cambios.")
    print()


if __name__ == "__main__":
    main()
