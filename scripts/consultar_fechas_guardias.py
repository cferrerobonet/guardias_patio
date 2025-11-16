#!/usr/bin/env python3
"""
Script para consultar estadísticas sobre fechas de inicio/fin de guardias en profesores.
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.models import Profesor
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker


def consultar_fechas_guardias(db_path: str = "data/guardias_patio.db"):
    """Consulta estadísticas sobre fechas de inicio/fin de guardias."""

    # Conectar a la base de datos
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("=" * 80)
        print("📊 ESTADÍSTICAS DE FECHAS DE INICIO/FIN DE GUARDIAS")
        print("=" * 80)
        print()

        # Total de profesores
        total_profesores = session.query(func.count(Profesor.id)).scalar()
        print(f"📋 Total de profesores en BD: {total_profesores}")

        # Profesores activos
        profesores_activos = session.query(func.count(Profesor.id)).filter(
            Profesor.activo
        ).scalar()
        print(f"✅ Profesores activos: {profesores_activos}")

        # Profesores inactivos
        profesores_inactivos = total_profesores - profesores_activos
        print(f"❌ Profesores inactivos: {profesores_inactivos}")
        print()

        print("-" * 80)
        print("📅 FECHA DE INICIO DE GUARDIAS")
        print("-" * 80)

        # Profesores con fecha de inicio
        con_fecha_inicio = session.query(func.count(Profesor.id)).filter(
            Profesor.fecha_inicio_guardias.isnot(None)
        ).scalar()
        print(f"✓ Profesores con fecha_inicio_guardias: {con_fecha_inicio}")

        # Profesores activos con fecha de inicio
        activos_con_fecha_inicio = session.query(func.count(Profesor.id)).filter(
            Profesor.activo,
            Profesor.fecha_inicio_guardias.isnot(None)
        ).scalar()
        print(f"✓ Profesores activos con fecha_inicio_guardias: {activos_con_fecha_inicio}")

        # Profesores sin fecha de inicio
        sin_fecha_inicio = session.query(func.count(Profesor.id)).filter(
            Profesor.fecha_inicio_guardias.is_(None)
        ).scalar()
        print(f"✗ Profesores sin fecha_inicio_guardias: {sin_fecha_inicio}")

        # Profesores activos sin fecha de inicio
        activos_sin_fecha_inicio = session.query(func.count(Profesor.id)).filter(
            Profesor.activo,
            Profesor.fecha_inicio_guardias.is_(None)
        ).scalar()
        print(f"✗ Profesores activos sin fecha_inicio_guardias: {activos_sin_fecha_inicio}")

        print()
        print("-" * 80)
        print("📅 FECHA DE FIN DE GUARDIAS")
        print("-" * 80)

        # Profesores con fecha de fin
        con_fecha_fin = session.query(func.count(Profesor.id)).filter(
            Profesor.fecha_fin_guardias.isnot(None)
        ).scalar()
        print(f"✓ Profesores con fecha_fin_guardias: {con_fecha_fin}")

        # Profesores activos con fecha de fin
        activos_con_fecha_fin = session.query(func.count(Profesor.id)).filter(
            Profesor.activo,
            Profesor.fecha_fin_guardias.isnot(None)
        ).scalar()
        print(f"✓ Profesores activos con fecha_fin_guardias: {activos_con_fecha_fin}")

        # Profesores sin fecha de fin
        sin_fecha_fin = session.query(func.count(Profesor.id)).filter(
            Profesor.fecha_fin_guardias.is_(None)
        ).scalar()
        print(f"✗ Profesores sin fecha_fin_guardias: {sin_fecha_fin}")

        # Profesores activos sin fecha de fin
        activos_sin_fecha_fin = session.query(func.count(Profesor.id)).filter(
            Profesor.activo,
            Profesor.fecha_fin_guardias.is_(None)
        ).scalar()
        print(f"✗ Profesores activos sin fecha_fin_guardias: {activos_sin_fecha_fin}")

        print()
        print("-" * 80)
        print("📊 RESUMEN DE CUMPLIMIENTO")
        print("-" * 80)

        # Porcentajes sobre profesores activos
        if profesores_activos > 0:
            pct_inicio = (activos_con_fecha_inicio / profesores_activos) * 100
            pct_fin = (activos_con_fecha_fin / profesores_activos) * 100

            print(f"Porcentaje de profesores activos con fecha_inicio: {pct_inicio:.1f}%")
            print(f"Porcentaje de profesores activos con fecha_fin: {pct_fin:.1f}%")
            print()

            # Conclusión
            if pct_inicio > 80:
                print("✅ EXCELENTE: >80% de profesores activos tienen fecha de inicio configurada")
            elif pct_inicio > 50:
                print("⚠️  ACEPTABLE: 50-80% de profesores activos tienen fecha de inicio configurada")
            elif pct_inicio > 0:
                print("❌ BAJO: <50% de profesores activos tienen fecha de inicio configurada")
            else:
                print("❌ CRÍTICO: Ningún profesor tiene fecha de inicio configurada")

        print()
        print("-" * 80)
        print("👥 LISTADO DE PROFESORES CON FECHAS CONFIGURADAS")
        print("-" * 80)
        print()

        # Listar profesores con fechas
        profesores_con_fechas = session.query(Profesor).filter(
            (Profesor.fecha_inicio_guardias.isnot(None)) |
            (Profesor.fecha_fin_guardias.isnot(None))
        ).order_by(Profesor.nombre_completo).all()

        if profesores_con_fechas:
            for prof in profesores_con_fechas:
                estado = "✅" if prof.activo else "❌"
                inicio = prof.fecha_inicio_guardias.strftime("%d/%m/%Y") if prof.fecha_inicio_guardias else "-"
                fin = prof.fecha_fin_guardias.strftime("%d/%m/%Y") if prof.fecha_fin_guardias else "-"
                print(f"{estado} {prof.nombre_completo:40} | Inicio: {inicio:10} | Fin: {fin:10}")
        else:
            print("No hay profesores con fechas de inicio/fin configuradas")

        print()
        print("=" * 80)

    finally:
        session.close()


if __name__ == "__main__":
    import os

    # Cambiar al directorio raíz del proyecto
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    os.chdir(project_dir)

    consultar_fechas_guardias()
