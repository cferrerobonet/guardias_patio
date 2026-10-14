#!/usr/bin/env python3
"""
Script para limpiar datos de prueba de la base de datos de producción.

Elimina profesores con nombres genéricos creados por tests:
- "Profesor N" (donde N es un número)
- "Profesor Test", "Profesor Guardia", "Profesor Find", "Profesor Delete"
- "Test Profesor"
"""

import sys
from pathlib import Path

# Agregar src al path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from database.db_manager import SessionLocal
from infrastructure.database.models import Ausencia, Guardia, Profesor
from sqlalchemy import or_


def cleanup_test_professors():
    """Eliminar profesores de prueba de la base de datos."""
    session = SessionLocal()

    try:
        # Patrones de nombres de prueba
        test_patterns = [
            "Profesor 0%",
            "Profesor 1%",
            "Profesor 2%",
            "Profesor 3%",
            "Profesor 4%",
            "Profesor 5%",
            "Profesor 6%",
            "Profesor 7%",
            "Profesor 8%",
            "Profesor 9%",
            "Profesor Test%",
            "Profesor Guardia%",
            "Profesor Find%",
            "Profesor Delete%",
            "Test Profesor%",
            "%Test%",  # Cualquier nombre que contenga "Test"
        ]

        # Buscar profesores de prueba
        query = session.query(Profesor)
        conditions = [Profesor.nombre_completo.like(pattern) for pattern in test_patterns]
        test_professors = query.filter(or_(*conditions)).all()

        if not test_professors:
            print("✅ No se encontraron profesores de prueba para eliminar.")
            return

        print(f"🔍 Encontrados {len(test_professors)} profesores de prueba:")
        for prof in test_professors:
            print(f"   ID: {prof.id:3d} | {prof.nombre_completo}")

        # Confirmar eliminación
        print()
        respuesta = input("¿Desea eliminar estos profesores? (s/N): ").strip().lower()

        if respuesta != "s":
            print("❌ Operación cancelada.")
            return

        # Eliminar guardias y ausencias asociadas primero
        deleted_guardias = 0
        deleted_ausencias = 0

        for prof in test_professors:
            # Eliminar guardias
            guardias = session.query(Guardia).filter(Guardia.profesor_id == prof.id).all()
            deleted_guardias += len(guardias)
            for guardia in guardias:
                session.delete(guardia)

            # Eliminar ausencias
            ausencias = session.query(Ausencia).filter(Ausencia.profesor_id == prof.id).all()
            deleted_ausencias += len(ausencias)
            for ausencia in ausencias:
                session.delete(ausencia)

        # Eliminar profesores
        for prof in test_professors:
            session.delete(prof)

        session.commit()

        print()
        print("✅ Limpieza completada:")
        print(f"   - {len(test_professors)} profesores eliminados")
        print(f"   - {deleted_guardias} guardias eliminadas")
        print(f"   - {deleted_ausencias} ausencias eliminadas")

    except Exception as e:
        session.rollback()
        print(f"❌ Error durante la limpieza: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  LIMPIEZA DE DATOS DE PRUEBA")
    print("=" * 60)
    print()

    cleanup_test_professors()
