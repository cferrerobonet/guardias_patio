#!/usr/bin/env python3.11
"""
Script para probar la FASE 7 del algoritmo con datos REALES de producción.
Analiza la cobertura antes/después y el uso de profesores sin guardias.
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import json

from models.models import Configuracion, Guardia, Profesor, Zona
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main():
    # Base de datos de producción
    db_path = 'data/users/66f06c9433d74e80/guardias_patio.db'

    print('\n' + '=' * 80)
    print('PRUEBA FASE 7 CON DATOS DE PRODUCCIÓN')
    print('=' * 80)

    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. ANÁLISIS INICIAL
        print('\n📊 1. ANÁLISIS DE DATOS ACTUALES')
        print('-' * 80)

        profesores = session.query(Profesor).all()
        zonas = session.query(Zona).all()
        config = session.query(Configuracion).first()

        print(f'Total profesores: {len(profesores)}')
        print(f'Total zonas: {len(zonas)}')

        # Analizar guardias por profesor
        profs_info = []
        for p in profesores:
            guardias_count = session.query(Guardia).filter(Guardia.profesor_id == p.id).count()
            profs_info.append({
                'id': p.id,
                'nombre': p.nombre_completo,
                'guardias': guardias_count,
                'turno': p.turno,
                'tutor': p.tutor
            })

        profs_sin_guardias = [p for p in profs_info if p['guardias'] == 0]
        profs_con_guardias = [p for p in profs_info if p['guardias'] > 0]

        print(f'\nProfesores con guardias: {len(profs_con_guardias)}')
        print(f'Profesores SIN guardias: {len(profs_sin_guardias)}')

        if profs_sin_guardias:
            print('\n⚠️  Profesores sin ninguna guardia:')
            for i, p in enumerate(profs_sin_guardias[:10], 1):
                print(f'  {i}. {p["nombre"]}')
            if len(profs_sin_guardias) > 10:
                print(f'  ... y {len(profs_sin_guardias) - 10} más')

        # 2. ANÁLISIS DE COBERTURA
        print('\n\n📅 2. ANÁLISIS DE COBERTURA POR DÍA')
        print('-' * 80)

        # Obtener todas las guardias
        todas_guardias = session.query(Guardia).all()

        # Agrupar por fecha
        from collections import defaultdict
        guardias_por_fecha = defaultdict(list)
        for g in todas_guardias:
            guardias_por_fecha[g.fecha].append(g)

        # Configuración de recreos (si existe)
        recreos_config = json.loads(config.recreos_config) if config and config.recreos_config else []
        num_recreos = len(recreos_config) if recreos_config else 4  # Por defecto 4

        # Slots esperados por día
        slots_por_dia = len(zonas) * num_recreos

        print(f'Slots esperados por día: {len(zonas)} zonas × {num_recreos} recreos = {slots_por_dia}')
        print(f'Días con guardias: {len(guardias_por_fecha)}')

        # Analizar días con slots sin cubrir
        dias_incompletos = []
        for fecha, guardias_dia in sorted(guardias_por_fecha.items()):
            guardias_count = len(guardias_dia)
            if guardias_count < slots_por_dia:
                faltantes = slots_por_dia - guardias_count
                dias_incompletos.append((fecha, guardias_count, faltantes))

        if dias_incompletos:
            print(f'\n⚠️  Días con slots SIN cubrir: {len(dias_incompletos)}')
            print('\nPrimeros 10 días con cobertura incompleta:')
            for i, (fecha, guardias, faltantes) in enumerate(dias_incompletos[:10], 1):
                porcentaje = (guardias / slots_por_dia) * 100
                print(f'  {i}. {fecha}: {guardias}/{slots_por_dia} slots ({porcentaje:.1f}%) - Faltan {faltantes}')

            if len(dias_incompletos) > 10:
                print(f'  ... y {len(dias_incompletos) - 10} días más')

            # Calcular total de slots sin cubrir
            total_slots_faltantes = sum(f for _, _, f in dias_incompletos)
            total_slots_posibles = len(guardias_por_fecha) * slots_por_dia
            total_slots_cubiertos = len(todas_guardias)

            print('\n📊 Resumen global:')
            print(f'  Total slots posibles: {total_slots_posibles}')
            print(f'  Total slots cubiertos: {total_slots_cubiertos}')
            print(f'  Total slots sin cubrir: {total_slots_faltantes}')
            cobertura_global = (total_slots_cubiertos / total_slots_posibles) * 100
            print(f'  Cobertura global: {cobertura_global:.2f}%')
        else:
            print('\n✅ Todos los días tienen cobertura completa')

        # 3. ANÁLISIS DE UN DÍA ESPECÍFICO
        if dias_incompletos:
            print('\n\n🔍 3. ANÁLISIS DETALLADO DE UN DÍA INCOMPLETO')
            print('-' * 80)

            fecha_ejemplo = dias_incompletos[0][0]
            guardias_dia = guardias_por_fecha[fecha_ejemplo]

            print(f'Fecha seleccionada: {fecha_ejemplo}')
            print(f'Guardias asignadas: {len(guardias_dia)}/{slots_por_dia}')

            # Ver qué slots están cubiertos
            slots_cubiertos = set((g.zona_id, g.recreo) for g in guardias_dia)

            print('\nSlots cubiertos:')
            for g in guardias_dia[:5]:
                zona = session.query(Zona).filter(Zona.id == g.zona_id).first()
                profesor = session.query(Profesor).filter(Profesor.id == g.profesor_id).first()
                print(f'  - {zona.nombre_zona} Recreo {g.recreo}: {profesor.nombre_completo}')
            if len(guardias_dia) > 5:
                print(f'  ... y {len(guardias_dia) - 5} más')

            # Ver qué slots faltan
            print('\nSlots SIN cubrir:')
            slots_sin_cubrir = []
            for zona in zonas:
                for recreo in range(1, num_recreos + 1):
                    if (zona.id, recreo) not in slots_cubiertos:
                        slots_sin_cubrir.append((zona.nombre_zona, recreo))

            for zona_nombre, recreo in slots_sin_cubrir[:10]:
                print(f'  - {zona_nombre} Recreo {recreo}')
            if len(slots_sin_cubrir) > 10:
                print(f'  ... y {len(slots_sin_cubrir) - 10} más')

        # 4. CONCLUSIONES Y RECOMENDACIONES
        print('\n\n💡 4. CONCLUSIONES')
        print('-' * 80)

        if profs_sin_guardias and dias_incompletos:
            print('✅ SITUACIÓN PERFECTA PARA FASE 7:')
            print(f'   • Hay {len(profs_sin_guardias)} profesores disponibles sin guardias')
            print(f'   • Hay {len(dias_incompletos)} días con cobertura incompleta')
            print(f'   • Total de {total_slots_faltantes} slots que podrían asignarse')
            print('\n🚀 La FASE 7 del algoritmo debería:')
            print('   1. Usar profesores sin guardias en PASADA 1')
            print('   2. Llenar los slots vacíos disponibles')
            print('   3. Mejorar la cobertura global significativamente')
        elif profs_sin_guardias:
            print('⚠️  Hay profesores sin guardias pero cobertura completa')
            print('   Esto sugiere que la carga está desbalanceada')
        elif dias_incompletos:
            print('⚠️  Hay slots sin cubrir pero no hay profesores disponibles')
            print('   Se necesitarían más profesores o ajustar restricciones')
        else:
            print('✅ Cobertura perfecta y todos los profesores utilizados')

    finally:
        session.close()

    print('\n' + '=' * 80)

if __name__ == '__main__':
    main()
