"""
Tests para validar que el algoritmo mantiene a los profesores
en la misma zona preferida durante el curso.
"""

import sys
from datetime import date, time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.models import Configuracion, Profesor, Zona
from services.asignador_guardias import generar_calendario_guardias


def test_zona_preferida():
    """
    Valida que cada profesor se mantiene en su zona preferida
    el máximo posible de veces durante el curso.
    """
    # Base de datos en memoria
    engine = create_engine("sqlite:///:memory:")
    from models.models import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Configuración del curso
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 2),
            fecha_fin_curso=date(2024, 9, 30),  # 1 mes para facilitar test
            hora_recreo1_manana=time(11, 0),
            hora_recreo2_manana=time(12, 0),
            hora_recreo1_tarde=time(16, 0),
        )
        session.add(config)

        # Crear 3 zonas
        zona1 = Zona(nombre_zona="Patio Principal")
        zona2 = Zona(nombre_zona="Patio Infantil")
        zona3 = Zona(nombre_zona="Polideportivo")
        session.add_all([zona1, zona2, zona3])
        session.flush()

        # Crear 6 profesores (2 por zona ideal)
        profesores = []
        for i in range(1, 7):
            prof = Profesor(
                nombre_completo=f"Profesor {i}",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                email_corporativo=f"profesor{i}@test.com",
            )
            profesores.append(prof)
            session.add(prof)

        session.commit()

        # Generar calendario
        calendario, asignadas = generar_calendario_guardias(session)

        print(f"\n{'='*80}")
        print("RESUMEN DE ASIGNACIONES")
        print(f"{'='*80}")
        print(f"Total guardias generadas: {len(calendario)}")
        print("\nDistribución por profesor:")
        for prof_id, count in asignadas.items():
            prof = session.query(Profesor).get(prof_id)
            print(f"  {prof.nombre_completo}: {count} guardias")

        # Analizar zona preferida de cada profesor
        print(f"\n{'='*80}")
        print("ANÁLISIS DE ZONA PREFERIDA")
        print(f"{'='*80}")

        zonas_por_profesor = {}
        for guardia in calendario:
            if guardia.profesor_id not in zonas_por_profesor:
                zonas_por_profesor[guardia.profesor_id] = []
            zonas_por_profesor[guardia.profesor_id].append(guardia.zona_id)

        for prof_id, zonas in zonas_por_profesor.items():
            prof = session.query(Profesor).get(prof_id)
            zona_counts = {}
            for z in zonas:
                zona_counts[z] = zona_counts.get(z, 0) + 1

            zona_preferida = max(zona_counts, key=zona_counts.get)
            total_guardias = len(zonas)
            guardias_zona_preferida = zona_counts[zona_preferida]
            porcentaje = (guardias_zona_preferida / total_guardias) * 100

            print(f"\n{prof.nombre_completo}:")
            print(f"  Total guardias: {total_guardias}")
            print(
                f"  Zona preferida: {zona_preferida} "
                f"({guardias_zona_preferida} guardias = {porcentaje:.1f}%)"
            )
            print(f"  Distribución por zona: {zona_counts}")

            # VALIDACIÓN: Al menos el 70% de las guardias deberían ser en la misma zona
            assert porcentaje >= 70, (
                f"{prof.nombre_completo} tiene menos del 70% de guardias "
                f"en su zona preferida ({porcentaje:.1f}%)"
            )

        print(f"\n{'='*80}")
        print("✅ TEST APROBADO: Todos los profesores mantienen su zona preferida")
        print(f"{'='*80}\n")

    finally:
        session.close()


if __name__ == "__main__":
    test_zona_preferida()
