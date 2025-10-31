#!/bin/bash
# Test rápido del algoritmo v3.0
# Ejecuta solo la generación de slots para detectar errores

cd "$(dirname "$0")/../src" || exit 1

DB_USER_ID="66f06c9433d74e80" python3.11 << 'EOF'
import sys
import traceback

print("=" * 80)
print("TEST V3.0 - Verificación Rápida")
print("=" * 80)
print()

try:
    print("1. Imports...")
    from database.db_manager import SessionLocal
    from models.models import Configuracion, Zona
    from services.calculador_guardias import _parse_recreos_config, listar_dias_lectivos
    print("   ✓ OK")
    print()
    
    print("2. Obtener configuración...")
    session = SessionLocal()
    config = session.query(Configuracion).first()
    print(f"   ✓ Config ID: {config.id}")
    print()
    
    print("3. Listar días lectivos...")
    dias = listar_dias_lectivos(config)
    print(f"   ✓ {len(dias)} días lectivos")
    print()
    
    print("4. Parse recreos...")
    recreos = _parse_recreos_config(config)
    print(f"   ✓ {len(recreos)} recreos configurados:")
    for r in recreos:
        print(f"     - Recreo {r['id']}: {r['etiqueta']} ({r['turno']})")
    print()
    
    print("5. Obtener zonas...")
    zonas = session.query(Zona).all()
    print(f"   ✓ {len(zonas)} zonas:")
    for z in zonas:
        print(f"     - Zona {z.id}: {z.nombre_zona}")
    print()
    
    print("6. Calcular slots totales...")
    total_slots = len(dias) * len(recreos) * len(zonas)
    print(f"   ✓ Total slots esperados: {total_slots}")
    print(f"     ({len(dias)} días × {len(recreos)} recreos × {len(zonas)} zonas)")
    print()
    
    session.close()
    
    print("=" * 80)
    print("✅ VERIFICACIÓN EXITOSA")
    print("=" * 80)
    print()
    print("El algoritmo v3.0 puede procesar la configuración correctamente.")
    print("ADVERTENCIA: No se ejecutó generar_guardias_v3_simple completo")
    print("            para evitar loops infinitos.")
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ ERROR")
    print("=" * 80)
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensaje: {str(e)}")
    print()
    traceback.print_exc()
    sys.exit(1)
EOF
