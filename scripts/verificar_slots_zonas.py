#!/usr/bin/env python3
"""
Script para verificar el cálculo de slots considerando fechas de zonas.

Muestra:
- Número de zonas y sus fechas de disponibilidad
- Días lectivos del curso
- Slots totales sin considerar fechas de zonas (antiguo)
- Slots totales considerando fechas de zonas (nuevo)
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.database import get_db_path
from models.models import Configuracion, Zona
from services.calculador_guardias import (
    _parse_recreos_config,
    calcular_recreos_activos,
    calcular_slots_reales,
    listar_dias_lectivos,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main():
    """Verificar cálculo de slots con fechas de zonas."""
    # Conectar a la base de datos
    db_path = get_db_path()
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    print("=" * 80)
    print("VERIFICACIÓN DE SLOTS CON FECHAS DE ZONAS")
    print("=" * 80)

    # Obtener configuración
    config = session.query(Configuracion).first()
    if not config:
        print("❌ No hay configuración del curso")
        return

    print(f"\n📅 Curso: {config.fecha_inicio_curso} a {config.fecha_fin_curso}")

    # Obtener zonas
    zonas = session.query(Zona).all()
    if not zonas:
        print("❌ No hay zonas registradas")
        return

    print(f"\n📍 Zonas registradas: {len(zonas)}")
    print("-" * 80)
    for zona in zonas:
        inicio = zona.fecha_inicio.strftime("%d/%m/%Y") if zona.fecha_inicio else "Sin límite"
        fin = zona.fecha_fin.strftime("%d/%m/%Y") if zona.fecha_fin else "Sin límite"

        if zona.fecha_inicio or zona.fecha_fin:
            print(f"  • {zona.nombre_zona} - Activa: {inicio} → {fin}")
        else:
            print(f"  • {zona.nombre_zona} - Activa: Todo el curso")

    # Calcular días lectivos
    dias_lectivos = listar_dias_lectivos(config)
    print(f"\n📆 Días lectivos: {len(dias_lectivos)}")

    # Calcular recreos
    recreos_manana, recreos_tarde = calcular_recreos_activos(session)
    recreos_total = recreos_manana + recreos_tarde
    print(f"🔔 Recreos por día: {recreos_total} ({recreos_manana} mañana + {recreos_tarde} tarde)")

    # Calcular slots SIN considerar fechas de zonas (método antiguo)
    lista_recreos = _parse_recreos_config(config)
    if lista_recreos:
        zonas_por_dia = sum(min(r.get('zonas', 1), len(zonas)) for r in lista_recreos)
        slots_antiguos = len(dias_lectivos) * zonas_por_dia
    else:
        slots_antiguos = len(dias_lectivos) * recreos_total * len(zonas)

    # Calcular slots CON fechas de zonas (método nuevo)
    slots_nuevos = calcular_slots_reales(session, config)

    print("\n" + "=" * 80)
    print("COMPARACIÓN DE CÁLCULOS")
    print("=" * 80)
    print(f"📊 Slots SIN considerar fechas de zonas: {slots_antiguos}")
    print(f"✅ Slots CON fechas de zonas:           {slots_nuevos}")

    diferencia = slots_antiguos - slots_nuevos
    porcentaje = (diferencia / slots_antiguos * 100) if slots_antiguos > 0 else 0

    if diferencia > 0:
        print(f"\n⚠️  Diferencia: {diferencia} slots menos ({porcentaje:.1f}%)")
        print("   Esto significa que hay zonas con fechas de inicio/fin que reducen")
        print("   el número total de slots disponibles.")
    elif diferencia < 0:
        print(f"\n⚠️  ADVERTENCIA: Hay más slots nuevos que antiguos ({abs(diferencia)})")
        print("   Esto NO debería ocurrir. Revisar la lógica.")
    else:
        print("\n✅ No hay diferencia (todas las zonas están activas todo el curso)")

    # Detallar slots por zona
    print("\n" + "=" * 80)
    print("DETALLE DE SLOTS POR ZONA")
    print("=" * 80)

    for zona in zonas:
        slots_zona = 0
        for dia in dias_lectivos:
            # Verificar si la zona está activa en este día
            zona_activa = True
            if zona.fecha_inicio and dia < zona.fecha_inicio:
                zona_activa = False
            if zona.fecha_fin and dia > zona.fecha_fin:
                zona_activa = False

            if zona_activa:
                slots_zona += recreos_total

        dias_activos = slots_zona // recreos_total if recreos_total > 0 else 0
        porcentaje_zona = (dias_activos / len(dias_lectivos) * 100) if len(dias_lectivos) > 0 else 0

        print(f"  • {zona.nombre_zona}:")
        print(f"    - Días activos: {dias_activos} de {len(dias_lectivos)} ({porcentaje_zona:.1f}%)")
        print(f"    - Slots totales: {slots_zona}")

    print("\n" + "=" * 80)
    session.close()

if __name__ == "__main__":
    main()
