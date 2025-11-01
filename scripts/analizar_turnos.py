#!/usr/bin/env python3
"""
Script para analizar la distribución de profesores por turno y sus recreos.
"""
import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Ahora podemos importar
import models.database  # noqa: E402
import models.models  # noqa: E402

from models.database import SessionLocal  # noqa: E402
from models.models import Profesor, Configuracion, Guardia  # noqa: E402

def main():
    session = SessionLocal()
    config = session.query(Configuracion).first()
    
    if not config:
        print("❌ No hay configuración")
        return
    
    profesores = session.query(Profesor).filter(
        Profesor.configuracion_id == config.id
    ).all()
    
    print('=' * 80)
    print('ANÁLISIS DE PROFESORES POR TURNO')
    print('=' * 80)
    
    turnos = {}
    for p in profesores:
        turno = p.turno
        if turno not in turnos:
            turnos[turno] = []
        turnos[turno].append(p)
    
    for turno in sorted(turnos.keys()):
        profs = turnos[turno]
        print(f'\n{turno.upper()}: {len(profs)} profesores')
        print('-' * 80)
        for p in profs[:10]:
            recreos_str = ','.join(map(str, sorted(p.recreos))) if p.recreos else 'ninguno'
            cuota = p.cuota_anual if p.cuota_anual else 0
            print(f'  - {p.nombre_completo:30s} | Recreos: {recreos_str:10s} | Cuota: {cuota}')
        if len(profs) > 10:
            print(f'  ... y {len(profs) - 10} más')
    
    # Cuotas totales
    total_cuota_manana = sum(p.cuota_anual or 0 for p in profesores if p.turno == 'mañana')
    total_cuota_tarde = sum(p.cuota_anual or 0 for p in profesores if p.turno == 'tarde')
    total_cuota_mixto = sum(p.cuota_anual or 0 for p in profesores if p.turno == 'mixto')
    
    print('\n' + '=' * 80)
    print('CUOTAS TOTALES')
    print('=' * 80)
    print(f'Mañana: {total_cuota_manana}')
    print(f'Tarde: {total_cuota_tarde}')
    print(f'Mixto: {total_cuota_mixto}')
    print(f'TOTAL: {total_cuota_manana + total_cuota_tarde + total_cuota_mixto}')
    
    # Verificar guardias asignadas por turno
    guardias_manana = session.query(Guardia).filter(
        Guardia.configuracion_id == config.id,
        Guardia.turno == 'mañana'
    ).count()
    
    guardias_tarde = session.query(Guardia).filter(
        Guardia.configuracion_id == config.id,
        Guardia.turno == 'tarde'
    ).count()
    
    print('\n' + '=' * 80)
    print('GUARDIAS ASIGNADAS')
    print('=' * 80)
    print(f'Mañana: {guardias_manana}')
    print(f'Tarde: {guardias_tarde}')
    print(f'TOTAL: {guardias_manana + guardias_tarde}')
    
    # Profesores de tarde con guardias
    profs_tarde = [p for p in profesores if p.turno == 'tarde']
    profs_tarde_con_guardias = []
    profs_tarde_sin_guardias = []
    
    for p in profs_tarde:
        guardias_count = session.query(Guardia).filter(
            Guardia.profesor_id == p.id
        ).count()
        if guardias_count > 0:
            profs_tarde_con_guardias.append((p, guardias_count))
        else:
            profs_tarde_sin_guardias.append(p)
    
    print('\n' + '=' * 80)
    print('PROFESORES DE TARDE - DETALLE')
    print('=' * 80)
    print(f'Total profesores de tarde: {len(profs_tarde)}')
    print(f'Con guardias asignadas: {len(profs_tarde_con_guardias)}')
    print(f'SIN guardias asignadas: {len(profs_tarde_sin_guardias)}')
    
    if profs_tarde_sin_guardias:
        print('\n⚠️  PROFESORES DE TARDE SIN GUARDIAS:')
        print('-' * 80)
        for p in profs_tarde_sin_guardias:
            recreos_str = ','.join(map(str, sorted(p.recreos))) if p.recreos else 'NINGUNO'
            cuota = p.cuota_anual if p.cuota_anual else 0
            print(f'  - {p.nombre_completo:30s} | Recreos: {recreos_str:10s} | Cuota: {cuota}')
    
    if profs_tarde_con_guardias:
        print('\n✅ PROFESORES DE TARDE CON GUARDIAS:')
        print('-' * 80)
        for p, count in profs_tarde_con_guardias[:10]:
            recreos_str = ','.join(map(str, sorted(p.recreos))) if p.recreos else 'NINGUNO'
            print(f'  - {p.nombre_completo:30s} | Guardias: {count:3d} | Recreos: {recreos_str}')
    
    session.close()

if __name__ == "__main__":
    main()
