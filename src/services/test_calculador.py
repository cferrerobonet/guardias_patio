"""Script de prueba para el calculador de guardias."""

from src.database.db_manager import SessionLocal
from src.services.calculador_guardias import (
    calcular_guardias_por_profesor,
    obtener_estadisticas,
)


def main():
    """Ejecuta una prueba del calculador de guardias."""
    session = SessionLocal()

    try:
        # Obtener estadísticas
        print("=" * 60)
        print("ESTADÍSTICAS DEL CÁLCULO DE GUARDIAS")
        print("=" * 60)

        stats = obtener_estadisticas(session)

        print("\nDatos del curso:")
        print(f"  - Días lectivos: {stats.get('dias_lectivos', 0)}")
        print(f"  - Recreos mañana: {stats.get('recreos_manana', 0)}")
        print(f"  - Recreos tarde: {stats.get('recreos_tarde', 0)}")
        print(f"  - Número de zonas: {stats.get('num_zonas', 0)}")
        print(f"  - Número de profesores: {stats.get('num_profesores', 0)}")
        print(f"  - Slots totales: {stats.get('slots_totales', 0)}")

        # Calcular distribución
        print("\n" + "=" * 60)
        print("DISTRIBUCIÓN DE GUARDIAS POR PROFESOR")
        print("=" * 60)

        distribucion = calcular_guardias_por_profesor(session)

        # Obtener datos de profesores para mostrar nombres
        from src.models.models import Profesor

        total_asignadas = 0
        for profesor_id, guardias in sorted(
            distribucion.items(), key=lambda x: x[1], reverse=True
        ):
            profesor = session.query(Profesor).get(profesor_id)
            if profesor:
                print(
                    f"\n{profesor.nombre} {profesor.apellidos} "
                    f"({profesor.turno}, {profesor.porcentaje_jornada * 100:.0f}%):"
                )
                print(f"  - Guardias asignadas: {guardias}")
                total_asignadas += guardias

        print("\n" + "=" * 60)
        print(f"TOTAL GUARDIAS ASIGNADAS: {total_asignadas}")
        print(f"SLOTS TOTALES: {stats.get('slots_totales', 0)}")

        if total_asignadas == stats.get("slots_totales", 0):
            print("✅ La suma coincide perfectamente")
        else:
            diff = abs(total_asignadas - stats.get("slots_totales", 0))
            print(f"⚠️  Diferencia: {diff}")

        print("=" * 60)

    except ValueError as e:
        print(f"\n❌ Error: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
