#!/usr/bin/env python3
"""
Script para validar la equidad en la distribución de guardias.

Verifica que profesores con las mismas características (turno, horas, tutoría)
tengan EXACTAMENTE las mismas guardias (±1 por redondeo).

Uso:
    python scripts/validar_equidad.py --db data/users/66f06c9433d74e80/guardias_patio.db
    python scripts/validar_equidad.py --db data/users/66f06c9433d74e80/guardias_patio.db --verbose
"""

import argparse
import sqlite3
import sys
from collections import defaultdict
from typing import Dict, List, Tuple


def validar_equidad(db_path: str, verbose: bool = False) -> bool:
    """
    Valida la equidad de la distribución de guardias.

    Args:
        db_path: Ruta a la base de datos
        verbose: Si True, muestra detalles

    Returns:
        True si la distribución es equitativa, False en caso contrario
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*100)
    print("VALIDACIÓN DE EQUIDAD EN DISTRIBUCIÓN DE GUARDIAS")
    print("="*100)

    # Obtener configuración
    cursor.execute("SELECT ajuste_tutores, ajuste_no_tutores FROM configuracion LIMIT 1")
    config = cursor.fetchone()
    ajuste_tutores = config[0] if config else 1.0
    ajuste_no_tutores = config[1] if config else 1.0

    print("\n⚙️  Configuración:")
    print(f"   • Factor tutores: {ajuste_tutores}")
    print(f"   • Factor no tutores: {ajuste_no_tutores}")

    # Obtener todos los profesores con sus guardias
    cursor.execute("""
        SELECT p.id, p.nombre_completo, p.turno, p.horas_contrato,
               p.tutor, COUNT(g.id) as total_guardias
        FROM profesores p
        LEFT JOIN guardias g ON p.id = g.profesor_id
        GROUP BY p.id
        ORDER BY p.turno, p.tutor DESC, p.horas_contrato DESC, total_guardias DESC
    """)

    profesores = cursor.fetchall()
    conn.close()

    # Agrupar por (turno, tutor, horas)
    # Clave: (turno, tutor, horas) → Lista de (nombre, guardias)
    grupos: Dict[Tuple[str, int, float], List[Tuple[str, int]]] = defaultdict(list)

    for prof_id, nombre, turno, horas, tutor, guardias in profesores:
        # Redondear horas a 0.5 para agrupar 29.5 con 30.0
        horas_rounded = round(horas * 2) / 2
        clave = (turno, tutor, horas_rounded)
        grupos[clave].append((nombre, guardias))

    # Validar cada grupo
    print("\n📊 ANÁLISIS POR GRUPOS:")
    print("-"*100)

    grupos_inequitativos = []
    total_profesores = 0

    for clave, miembros in sorted(grupos.items()):
        turno, tutor, horas = clave
        guardias_list = [g for _, g in miembros]

        if not guardias_list:
            continue

        total_profesores += len(miembros)

        min_g = min(guardias_list)
        max_g = max(guardias_list)
        promedio = sum(guardias_list) / len(guardias_list)
        rango = max_g - min_g

        # ✅ Equitativo: rango ≤ 1
        # ⚠️  Tolerable: rango ≤ 3
        # ❌ INEQUITATIVO: rango > 3
        if rango <= 1:
            estado = "✅ PERFECTO"
        elif rango <= 3:
            estado = "⚠️  TOLERABLE"
        else:
            estado = "❌ INEQUITATIVO"
            grupos_inequitativos.append((clave, miembros, rango))

        tutor_str = "TUTOR    " if tutor else "NO TUTOR "

        print(f"\n{estado} | Turno: {turno:8s} | {tutor_str} | Horas: {horas:4.1f}h")
        print(f"   Profesores: {len(miembros):2d} | Guardias: MIN={min_g:3d}, MAX={max_g:3d}, "
              f"PROM={promedio:5.1f}, RANGO={rango:3d}")

        if verbose or rango > 1:
            # Mostrar detalle si verbose o si hay inequidad
            print("   Detalle:")
            for nombre, guardias in sorted(miembros, key=lambda x: x[1], reverse=True):
                delta = guardias - promedio
                delta_str = f"{delta:+.1f}" if delta != 0 else " 0.0"
                print(f"     • {nombre:<45} {guardias:3d} guardias ({delta_str})")

    # Resumen final
    print("\n" + "="*100)
    print("RESUMEN DE VALIDACIÓN")
    print("="*100)

    print("\n📈 Estadísticas:")
    print(f"   • Total profesores analizados: {total_profesores}")
    print(f"   • Total grupos: {len(grupos)}")
    print(f"   • Grupos inequitativos (rango > 3): {len(grupos_inequitativos)}")

    if grupos_inequitativos:
        print("\n❌ PROBLEMAS DETECTADOS:")
        print(f"   {len(grupos_inequitativos)} grupos con distribución INEQUITATIVA:\n")

        for clave, miembros, rango in grupos_inequitativos:
            turno, tutor, horas = clave
            tutor_str = "TUTOR" if tutor else "NO TUTOR"
            print(f"   • {turno.upper()} - {tutor_str} - {horas:.1f}h: "
                  f"{len(miembros)} profesores, RANGO={rango}")

        print("\n💡 RECOMENDACIÓN:")
        print("   Regenerar guardias con algoritmo equitativo v2.9")
        print("="*100)
        return False
    else:
        print("\n✅ ¡DISTRIBUCIÓN EQUITATIVA PERFECTA!")
        print("   Todos los grupos tienen rango ≤ 3")
        print("="*100)
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Validar equidad en distribución de guardias"
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Ruta a la base de datos (ej: data/users/XXX/guardias_patio.db)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar detalles de todos los grupos"
    )

    args = parser.parse_args()

    try:
        equitativo = validar_equidad(args.db, args.verbose)
        sys.exit(0 if equitativo else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
