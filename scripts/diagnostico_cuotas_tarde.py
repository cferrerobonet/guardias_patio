#!/usr/bin/env python3
"""
Script de diagnóstico para verificar por qué profesores de tarde no tienen cuota.
"""

import os
import sys

# Agregar el directorio src al path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

from database.db_manager import SessionLocal  # noqa: E402
from models.models import Configuracion, Profesor  # noqa: E402
from services.calculador_guardias import (  # noqa: E402
    _parse_recreos_config,
    calcular_factor_participacion,
    calcular_guardias_por_profesor,
    calcular_recreos_activos,
)


def main():
    session = SessionLocal()

    print("=" * 80)
    print("DIAGNÓSTICO DE CUOTAS - PROFESORES DE TARDE")
    print("=" * 80)
    print()

    # 1. Verificar configuración de recreos
    config = session.query(Configuracion).first()
    print("1. CONFIGURACIÓN DE RECREOS:")
    print("-" * 80)
    print(f"recreos_config raw: {config.recreos_config}")
    print()

    recreos_parsed = _parse_recreos_config(config)
    print(f"recreos_config parseado ({len(recreos_parsed)} recreos):")
    for r in recreos_parsed:
        print(f"  - ID {r['id']}: {r['etiqueta']} (turno={r['turno']}, zonas={r['zonas']})")
    print()

    # 2. Calcular recreos activos
    recreos_manana, recreos_tarde = calcular_recreos_activos(session)
    print("2. RECREOS ACTIVOS:")
    print("-" * 80)
    print(f"Recreos mañana: {recreos_manana}")
    print(f"Recreos tarde: {recreos_tarde}")
    print(f"Total recreos: {recreos_manana + recreos_tarde}")
    print()

    # 3. Analizar factores de participación
    print("3. FACTORES DE PARTICIPACIÓN:")
    print("-" * 80)
    profesores_tarde = session.query(Profesor).filter(Profesor.turno == 'tarde').limit(5).all()
    for p in profesores_tarde:
        factor = calcular_factor_participacion(p, recreos_manana, recreos_tarde)
        print(f"{p.nombre_completo}:")
        print(f"  - Turno: {p.turno}")
        print(f"  - Factor participación: {factor:.4f}")
        print(f"  - Horas contrato: {p.horas_contrato}")
        print(f"  - Horas tarde: {p.horas_tarde}")
        print()

    # 4. Calcular cuotas
    print("4. CUOTAS CALCULADAS:")
    print("-" * 80)
    cuotas = calcular_guardias_por_profesor(session)

    todos_tarde = session.query(Profesor).filter(Profesor.turno == 'tarde').all()
    total_cuota = 0
    profesores_con_cuota = 0

    for p in todos_tarde:
        cuota = cuotas.get(p.id, 0)
        total_cuota += cuota
        if cuota > 0:
            profesores_con_cuota += 1
            print(f"{p.nombre_completo}: {cuota} guardias")

    print()
    print(f"Total profesores tarde: {len(todos_tarde)}")
    print(f"Profesores con cuota > 0: {profesores_con_cuota}")
    print(f"Profesores con cuota = 0: {len(todos_tarde) - profesores_con_cuota}")
    print(f"Total cuota asignada: {total_cuota}")
    print()

    # 5. Verificar profesores mixto
    print("5. PROFESORES MIXTO:")
    print("-" * 80)
    profesores_mixto = session.query(Profesor).filter(Profesor.turno == 'mixto').all()
    for p in profesores_mixto:
        factor = calcular_factor_participacion(p, recreos_manana, recreos_tarde)
        cuota = cuotas.get(p.id, 0)
        print(f"{p.nombre_completo}:")
        print(f"  - Factor participación: {factor:.4f}")
        print(f"  - Horas mañana: {p.horas_manana}")
        print(f"  - Horas tarde: {p.horas_tarde}")
        print(f"  - Cuota: {cuota}")
        print()

    session.close()

if __name__ == '__main__':
    main()
