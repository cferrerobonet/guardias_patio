#!/usr/bin/env python3
"""
Script de prueba para validar el nuevo algoritmo optimizado de asignación de guardias.
Ejecuta una generación completa y muestra las métricas de calidad.
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.models import Configuracion, Profesor, Zona
from services.asignador_guardias import generar_calendario_guardias
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main():
    """Ejecuta una prueba del algoritmo optimizado."""

    print("=" * 80)
    print("TEST DEL ALGORITMO OPTIMIZADO DE ASIGNACIÓN DE GUARDIAS")
    print("=" * 80)
    print()

    # Conectar a la base de datos de desarrollo
    db_path = Path(__file__).parent / "data" / "guardias_patio.db"

    if not db_path.exists():
        print(f"❌ No se encontró la base de datos en: {db_path}")
        print("   Asegúrate de tener datos de prueba configurados.")
        return

    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Verificar configuración
        config = session.query(Configuracion).first()
        if not config:
            print("❌ No hay configuración en la base de datos")
            return

        print("✓ Configuración encontrada")
        print(f"  Fecha inicio: {config.fecha_inicio}")
        print(f"  Fecha fin: {config.fecha_fin}")
        print(f"  Recreos: {config.recreos}")
        print()

        # Verificar profesores
        profesores = session.query(Profesor).all()
        print(f"✓ Profesores disponibles: {len(profesores)}")
        print()

        # Verificar zonas
        zonas = session.query(Zona).all()
        print(f"✓ Zonas configuradas: {len(zonas)}")
        print()

        # Ejecutar generación
        print("-" * 80)
        print("EJECUTANDO GENERACIÓN CON ALGORITMO OPTIMIZADO")
        print("-" * 80)
        print()

        def progreso_callback(porcentaje: int, mensaje: str):
            """Callback para mostrar progreso."""
            print(f"[{porcentaje:3d}%] {mensaje}")

        calendario, asignadas = generar_calendario_guardias(
            session=session,
            config=config,
            reportar_progreso=progreso_callback
        )

        print()
        print("=" * 80)
        print("RESULTADO DE LA GENERACIÓN")
        print("=" * 80)
        print(f"Total de guardias generadas: {len(calendario)}")
        print(f"Profesores con guardias: {len([k for k, v in asignadas.items() if v > 0])}")
        print()

        # Mostrar distribución por profesor
        print("DISTRIBUCIÓN POR PROFESOR:")
        print("-" * 80)
        print(f"{'Profesor':<30} {'Asignadas':>10} {'ID':>5}")
        print("-" * 80)

        for prof in profesores:
            if prof.id in asignadas:
                guardias = asignadas[prof.id]
                print(f"{prof.nombre:<30} {guardias:>10} {prof.id:>5}")

        print("=" * 80)
        print()
        print("✅ TEST COMPLETADO EXITOSAMENTE")

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR DURANTE LA EJECUCIÓN: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()

    finally:
        session.close()


if __name__ == "__main__":
    main()
