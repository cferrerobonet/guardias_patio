"""
Script para comparar los dos métodos de cálculo de slots.
"""
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db_manager import get_session
from models.models import Configuracion, Zona
from services.asignador_guardias import _build_slots
from services.calculador_guardias import _parse_recreos_config, calcular_slots_reales


def main():
    session = next(get_session())
    try:
        config = session.query(Configuracion).first()
        if not config:
            print("❌ No hay configuración")
            return

        zonas = session.query(Zona).all()
        print(f"Zonas: {len(zonas)}")
        for z in zonas:
            print(f"  - {z.nombre_zona}: {z.fecha_inicio} → {z.fecha_fin}")

        recreos = _parse_recreos_config(config)
        print(f"\nRecreos configurados: {len(recreos)}")
        for r in recreos:
            print(f"  - Recreo {r['id']}, turno={r['turno']}, zonas={r['zonas']}")

        # Método 1: calcular_slots_reales (usado en distribución)
        slots_calculados = calcular_slots_reales(session, config)
        print(f"\n✅ Slots calculados (calcular_slots_reales): {slots_calculados}")

        # Método 2: _build_slots (usado en generación)
        slots_list = _build_slots(session, config)
        print(f"✅ Slots generados (_build_slots): {len(slots_list)}")

        # Mostrar diferencia
        diferencia = abs(slots_calculados - len(slots_list))
        print(f"\n{'⚠️ ' if diferencia > 0 else '✅ '}DIFERENCIA: {diferencia} slots")

        if diferencia > 0:
            print("\n🔍 PROBLEMA DETECTADO:")
            print("El cálculo de distribución y la generación usan métodos diferentes")
            print("para contar slots, lo que causa discrepancias en las guardias asignadas.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
