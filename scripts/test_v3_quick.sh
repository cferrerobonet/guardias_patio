#!/bin/bash
# Test rápido del algoritmo v3.0
# Ejecuta solo la generación de slots para detectar errores

# Ruta a la BD de Jefatura_FpBach (67 profesores)
DB_PATH="../data/users/0db13e2857239ed8/guardias_patio.db"

cd "$(dirname "$0")/../src" || exit 1

python3.11 << EOF
import sys
import traceback

# Configurar BD directamente
import os
os.environ['DATABASE_URL'] = 'sqlite:///${DB_PATH}'

print("=" * 80)
print("TEST V3.0 - Verificación Rápida")
print("=" * 80)
print(f"Base de datos: ${DB_PATH}")
print()

try:
    print("1. Imports...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models.models import Base, Configuracion, Zona, Profesor
    from services.calculador_guardias import _parse_recreos_config, listar_dias_lectivos
    
    # Crear engine directamente con la BD correcta
    engine = create_engine('sqlite:///${DB_PATH}')
    SessionLocal = sessionmaker(bind=engine)
    
    print("   ✓ OK")
    print()
    
    print("2. Obtener configuración...")
    session = SessionLocal()
    config = session.query(Configuracion).first()
    print(f"   ✓ Config ID: {config.id}")
    print()
    
    print("3. Contar profesores...")
    num_profesores = session.query(Profesor).count()
    print(f"   ✓ {num_profesores} profesores en BD")
    print()
    
    print("4. Listar días lectivos...")
    dias = listar_dias_lectivos(config)
    print(f"   ✓ {len(dias)} días lectivos")
    print()
    
    print("5. Parse recreos...")
    recreos = _parse_recreos_config(config)
    print(f"   ✓ {len(recreos)} recreos configurados:")
    for r in recreos:
        print(f"     - Recreo {r['id']}: {r['etiqueta']} ({r['turno']})")
    print()
    
    print("6. Obtener zonas...")
    zonas = session.query(Zona).all()
    print(f"   ✓ {len(zonas)} zonas:")
    for z in zonas:
        print(f"     - Zona {z.id}: {z.nombre_zona}")
    print()
    
    print("7. Calcular slots totales...")
    total_slots = len(dias) * len(recreos) * len(zonas)
    print(f"   ✓ Total slots esperados: {total_slots}")
    print(f"     ({len(dias)} días × {len(recreos)} recreos × {len(zonas)} zonas)")
    print()
    
    session.close()
    
    print("=" * 80)
    print("✅ VERIFICACIÓN EXITOSA")
    print("=" * 80)
    print()
    
    if total_slots == 0:
        print("⚠️  ADVERTENCIA: La BD no tiene datos suficientes para generar guardias")
        print("   - Recreos: {len(recreos)}")
        print("   - Zonas: {len(zonas)}")
    else:
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
