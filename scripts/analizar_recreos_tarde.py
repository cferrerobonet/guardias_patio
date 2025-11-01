#!/usr/bin/env python3
"""Script para analizar la configuración de recreos y profesores de tarde."""

import json
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Cargar JSON
json_path = Path(__file__).parent.parent / "data/0db13e2857239ed8/guardias_patio_data.json"
with open(json_path) as f:
    data = json.load(f)

print("=" * 80)
print("ANÁLISIS DE CONFIGURACIÓN DE RECREOS Y PROFESORES DE TARDE")
print("=" * 80)
print()

# Configuración
config_list = data.get("configuracion", [])
config = config_list[0] if config_list else {}
recreos_config = config.get("recreos_config", "")

print("1. RECREOS CONFIGURADOS")
print("-" * 80)
if recreos_config:
    recreos = json.loads(recreos_config)
    print(f"Total de recreos: {len(recreos)}")
    for recreo in recreos:
        print(f"  - ID: {recreo['id']}, Etiqueta: {recreo['etiqueta']}, "
              f"Turno: {recreo['turno']}, Hora: {recreo['hora']}, Zonas: {recreo['zonas']}")
else:
    print("⚠️  NO HAY RECREOS CONFIGURADOS (recreos_config está vacío)")

print()

# Zonas
zonas = data.get("zonas", [])
print("2. ZONAS REGISTRADAS")
print("-" * 80)
print(f"Total de zonas: {len(zonas)}")
for zona in zonas:
    print(f"  - ID: {zona['id']}, Nombre: {zona['nombre_zona']}")

print()

# Profesores por turno
profesores = data.get("profesores", [])
manana = [p for p in profesores if p.get("turno") == "mañana"]
tarde = [p for p in profesores if p.get("turno") == "tarde"]
completo = [p for p in profesores if p.get("turno") == "completo"]

print("3. DISTRIBUCIÓN DE PROFESORES POR TURNO")
print("-" * 80)
print(f"Total profesores: {len(profesores)}")
print(f"  - Mañana: {len(manana)}")
print(f"  - Tarde: {len(tarde)}")
print(f"  - Completo: {len(completo)}")

print()

# Análisis de recreos_permitidos en profesores de tarde
print("4. RECREOS PERMITIDOS - PROFESORES DE TARDE")
print("-" * 80)
if tarde:
    for p in tarde[:5]:
        rp = p.get("recreos_permitidos", "")
        if rp:
            rp_data = json.loads(rp)
            recreos_ids = sorted(set(r for dia_recreos in rp_data.values() for r in dia_recreos))
            print(f"  {p['nombre_completo']}: {recreos_ids}")
        else:
            print(f"  {p['nombre_completo']}: SIN recreos_permitidos")
    if len(tarde) > 5:
        print(f"  ... y {len(tarde) - 5} más")
else:
    print("  No hay profesores de tarde")

print()

print("5. RECREOS PERMITIDOS - PROFESORES COMPLETO (MIXTOS)")
print("-" * 80)
if completo:
    for p in completo[:5]:
        rp = p.get("recreos_permitidos", "")
        if rp:
            rp_data = json.loads(rp)
            recreos_ids = sorted(set(r for dia_recreos in rp_data.values() for r in dia_recreos))
            print(f"  {p['nombre_completo']}: {recreos_ids}")
        else:
            print(f"  {p['nombre_completo']}: SIN recreos_permitidos")
    if len(completo) > 5:
        print(f"  ... y {len(completo) - 5} más")
else:
    print("  No hay profesores mixtos")

print()

# Diagnóstico
print("6. DIAGNÓSTICO")
print("-" * 80)

problemas = []

if not recreos_config:
    problemas.append("⚠️  recreos_config está vacío - no hay recreos definidos")
else:
    recreos = json.loads(recreos_config)
    recreos_tarde = [r for r in recreos if r['turno'] == 'tarde']
    if not recreos_tarde:
        problemas.append("⚠️  No hay recreos de tarde en recreos_config")
    else:
        ids_tarde = [r['id'] for r in recreos_tarde]
        print(f"✓ Recreos de tarde en config: IDs {ids_tarde}")

if not tarde and not completo:
    problemas.append("⚠️  No hay profesores de tarde ni mixtos")
else:
    # Verificar que tengan recreos_permitidos con IDs correctos
    for p in tarde + completo:
        rp = p.get("recreos_permitidos", "")
        if not rp:
            problemas.append(f"⚠️  {p['nombre_completo']} ({p['turno']}) no tiene recreos_permitidos")
        else:
            rp_data = json.loads(rp)
            recreos_ids = sorted(set(r for dia_recreos in rp_data.values() for r in dia_recreos))
            # Si es de tarde, debe tener IDs 3 y/o 4
            if p['turno'] == 'tarde' and not any(r in [3, 4] for r in recreos_ids):
                problemas.append(
                    f"⚠️  {p['nombre_completo']} (tarde) tiene recreos_permitidos={recreos_ids} "
                    f"pero debería tener [3, 4]"
                )

if problemas:
    for problema in problemas:
        print(problema)
else:
    print("✓ No se detectaron problemas obvios en la configuración")

print()
print("=" * 80)
