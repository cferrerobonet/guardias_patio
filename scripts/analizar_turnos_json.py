#!/usr/bin/env python3
"""
Script para analizar la distribución de profesores por turno.
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    """Analizar profesores por turno."""
    print("=" * 80)
    print("ANÁLISIS DE PROFESORES POR TURNO")
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
    guardias = data.get('guardias', [])
    
    print(f"Total profesores: {len(profesores)}")
    print(f"Total guardias: {len(guardias)}")
    print()
    
    # Agrupar por turno
    turnos = defaultdict(list)
    for p in profesores:
        turno = p.get('turno', 'desconocido')
        turnos[turno].append(p)
    
    # Mostrar profesores por turno
    for turno in sorted(turnos.keys()):
        profs = turnos[turno]
        print(f"\n{turno.upper()}: {len(profs)} profesores")
        print("-" * 80)
        
        for p in profs[:15]:  # Primeros 15
            nombre = p.get('nombre_completo', 'Sin nombre')
            recreos = p.get('recreos', [])
            recreos_str = ','.join(map(str, sorted(recreos))) if recreos else 'NINGUNO'
            cuota = p.get('cuota_anual', 0)
            print(f"  - {nombre:40s} | Recreos: {recreos_str:12s} | Cuota: {cuota}")
        
        if len(profs) > 15:
            print(f"  ... y {len(profs) - 15} más")
    
    # Calcular cuotas totales
    print("\n" + "=" * 80)
    print("CUOTAS TOTALES POR TURNO")
    print("=" * 80)
    
    for turno in sorted(turnos.keys()):
        total = sum(p.get('cuota_anual', 0) for p in turnos[turno])
        print(f"{turno.capitalize():15s}: {total:6.0f} guardias")
    
    total_global = sum(p.get('cuota_anual', 0) for p in profesores)
    print("-" * 40)
    print(f"{'TOTAL':15s}: {total_global:6.0f} guardias")
    
    # Analizar guardias asignadas
    guardias_por_turno = defaultdict(int)
    for g in guardias:
        turno = g.get('turno', 'desconocido')
        guardias_por_turno[turno] += 1
    
    print("\n" + "=" * 80)
    print("GUARDIAS ASIGNADAS POR TURNO")
    print("=" * 80)
    
    for turno in sorted(guardias_por_turno.keys()):
        print(f"{turno.capitalize():15s}: {guardias_por_turno[turno]:6d} guardias")
    
    print("-" * 40)
    print(f"{'TOTAL':15s}: {len(guardias):6d} guardias")
    
    # Analizar profesores de tarde sin guardias
    profs_tarde = turnos.get('tarde', [])
    if profs_tarde:
        print("\n" + "=" * 80)
        print("ANÁLISIS DETALLADO: PROFESORES DE TARDE")
        print("=" * 80)
        
        # IDs de profesores de tarde
        ids_tarde = {p['id'] for p in profs_tarde}
        
        # Guardias asignadas a profesores de tarde
        guardias_tarde = [g for g in guardias if g.get('profesor_id') in ids_tarde]
        
        # Profesores de tarde con y sin guardias
        profs_con_guardias = set(g.get('profesor_id') for g in guardias_tarde)
        profs_sin_guardias = ids_tarde - profs_con_guardias
        
        print(f"\nTotal profesores de tarde: {len(profs_tarde)}")
        print(f"Con guardias asignadas: {len(profs_con_guardias)}")
        print(f"SIN guardias asignadas: {len(profs_sin_guardias)}")
        print(f"Total guardias de tarde: {len(guardias_tarde)}")
        
        if profs_sin_guardias:
            print("\n⚠️  PROFESORES DE TARDE SIN GUARDIAS:")
            print("-" * 80)
            for p in profs_tarde:
                if p['id'] in profs_sin_guardias:
                    nombre = p.get('nombre_completo', 'Sin nombre')
                    recreos = p.get('recreos', [])
                    recreos_str = ','.join(map(str, sorted(recreos))) if recreos else 'NINGUNO ❌'
                    cuota = p.get('cuota_anual', 0)
                    horario = p.get('recreos_permitidos', '')
                    tiene_horario = '✅' if horario else '❌'
                    print(f"  - {nombre:40s} | Recreos: {recreos_str:12s} | Cuota: {cuota:3.0f} | Horario: {tiene_horario}")
        
        if profs_con_guardias:
            print("\n✅ PROFESORES DE TARDE CON GUARDIAS:")
            print("-" * 80)
            count_shown = 0
            for p in profs_tarde:
                if p['id'] in profs_con_guardias and count_shown < 15:
                    nombre = p.get('nombre_completo', 'Sin nombre')
                    recreos = p.get('recreos', [])
                    recreos_str = ','.join(map(str, sorted(recreos))) if recreos else 'NINGUNO'
                    num_guardias = len([g for g in guardias_tarde if g.get('profesor_id') == p['id']])
                    print(f"  - {nombre:40s} | Guardias: {num_guardias:3d} | Recreos: {recreos_str}")
                    count_shown += 1
            if len(profs_con_guardias) > 15:
                print(f"  ... y {len(profs_con_guardias) - 15} más")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
