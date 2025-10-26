#!/usr/bin/env python3
"""
Script de auditoría de N+1 queries.

Ejecuta flujos críticos con logging de queries SQLAlchemy activado
para identificar queries repetitivos y patrones N+1.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# Agregar src/ al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from models.models import Ausencia, Configuracion, Guardia, Profesor, Zona


class QueryAuditor:
    """Auditor de queries SQL para detectar N+1."""

    def __init__(self):
        self.queries = []
        self.query_counts = {}

    def log_query(self, sql_text: str):
        """Registra una query SQL."""
        # Normalizar query (quitar valores específicos)
        normalized = self._normalize_sql(sql_text)
        self.queries.append(sql_text)

        # Contar queries similares
        if normalized in self.query_counts:
            self.query_counts[normalized] += 1
        else:
            self.query_counts[normalized] = 1

    def _normalize_sql(self, sql: str) -> str:
        """Normaliza SQL quitando valores específicos."""
        # Simplificación básica
        import re

        sql = re.sub(r"\d+", "?", sql)  # Reemplazar números
        sql = re.sub(r"'[^']*'", "?", sql)  # Reemplazar strings
        return sql.strip()

    def report(self) -> dict:
        """Genera reporte de auditoría."""
        total_queries = len(self.queries)
        repeated_queries = {
            pattern: count for pattern, count in self.query_counts.items() if count > 5
        }

        return {
            "total_queries": total_queries,
            "unique_patterns": len(self.query_counts),
            "repeated_patterns": repeated_queries,
            "potential_n_plus_1": len(repeated_queries),
        }

    def print_report(self):
        """Imprime reporte legible."""
        report = self.report()

        print("\n" + "=" * 80)
        print("REPORTE DE AUDITORÍA N+1")
        print("=" * 80)
        print("\n📊 RESUMEN:")
        print(f"  Total de queries ejecutados: {report['total_queries']}")
        print(f"  Patrones únicos: {report['unique_patterns']}")
        print(f"  Patrones repetitivos (>5): {report['potential_n_plus_1']}")

        if report["repeated_patterns"]:
            print("\n⚠️  POTENCIALES N+1 DETECTADOS:")
            for pattern, count in sorted(
                report["repeated_patterns"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"\n  🔴 Repetido {count} veces:")
                print(f"     {pattern[:200]}...")  # Primeros 200 chars

        print("\n" + "=" * 80)


def setup_query_logging(engine):
    """Configura logging de queries en SQLAlchemy."""
    auditor = QueryAuditor()

    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
        auditor.log_query(statement)

    return auditor


def audit_flujo_carga_inicial(session: Session, auditor: QueryAuditor):
    """Audita el flujo de carga inicial de la aplicación."""
    print("\n🔍 AUDITANDO: Flujo de carga inicial...")

    # Cargar configuración
    config = session.query(Configuracion).first()

    # Cargar todos los profesores (típico en pantalla inicial)
    profesores = session.query(Profesor).order_by(Profesor.nombre_completo).all()
    print(f"  ✅ Cargados {len(profesores)} profesores")

    # Cargar todas las zonas
    zonas = session.query(Zona).all()
    print(f"  ✅ Cargadas {len(zonas)} zonas")

    # Cargar guardias del mes actual (típico en vista calendario)
    fecha_inicio = date.today().replace(day=1)
    if date.today().month == 12:
        fecha_fin = date(date.today().year + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin = date.today().replace(month=date.today().month + 1, day=1) - timedelta(days=1)

    guardias = (
        session.query(Guardia)
        .filter(Guardia.fecha >= fecha_inicio, Guardia.fecha <= fecha_fin)
        .all()
    )
    print(f"  ✅ Cargadas {len(guardias)} guardias del mes")

    # ⚠️ POTENCIAL N+1: Acceder a profesor y zona de cada guardia
    for guardia in guardias[:10]:  # Solo primeras 10 para no saturar
        _ = guardia.profesor.nombre_completo if guardia.profesor else None
        _ = guardia.zona.nombre_zona if guardia.zona else None

    print(f"  ⚠️  Accedidos relacionamientos de {min(10, len(guardias))} guardias")


def audit_flujo_asignacion_guardias(session: Session, auditor: QueryAuditor):
    """Audita el flujo de asignación de guardias."""
    print("\n🔍 AUDITANDO: Flujo de asignación de guardias...")

    # Obtener configuración
    config = session.query(Configuracion).first()

    # Obtener profesores disponibles (típico al asignar)
    profesores = session.query(Profesor).all()
    print(f"  ✅ Cargados {len(profesores)} profesores para asignación")

    # Por cada profesor, verificar guardias existentes (N+1 potencial)
    fecha_ejemplo = date.today()
    for profesor in profesores[:5]:  # Solo primeros 5
        guardias_profesor = (
            session.query(Guardia)
            .filter(
                Guardia.profesor_id == profesor.id,
                Guardia.fecha == fecha_ejemplo,
            )
            .all()
        )
        # print(f"  Profesor {profesor.id}: {len(guardias_profesor)} guardias")

    print(f"  ⚠️  Verificadas guardias de {min(5, len(profesores))} profesores")


def audit_flujo_gestion_ausencias(session: Session, auditor: QueryAuditor):
    """Audita el flujo de gestión de ausencias."""
    print("\n🔍 AUDITANDO: Flujo de gestión de ausencias...")

    # Obtener ausencias activas
    ausencias = session.query(Ausencia).filter(Ausencia.activa == True).all()
    print(f"  ✅ Cargadas {len(ausencias)} ausencias activas")

    # Por cada ausencia, obtener profesor (N+1 potencial)
    for ausencia in ausencias[:10]:  # Solo primeras 10
        _ = ausencia.profesor.nombre_completo if ausencia.profesor else None

    print(f"  ⚠️  Accedidos profesores de {min(10, len(ausencias))} ausencias")

    # Obtener guardias afectadas por ausencia
    if ausencias:
        ausencia_ejemplo = ausencias[0]
        guardias_afectadas = (
            session.query(Guardia)
            .filter(
                Guardia.profesor_id == ausencia_ejemplo.profesor_id,
                Guardia.fecha >= ausencia_ejemplo.fecha_inicio,
                Guardia.fecha <= ausencia_ejemplo.fecha_fin,
            )
            .all()
        )
        print(f"  ✅ Encontradas {len(guardias_afectadas)} guardias afectadas")


def main():
    """Función principal de auditoría."""
    print("=" * 80)
    print("AUDITORÍA DE N+1 QUERIES")
    print("=" * 80)

    # Conectar a base de datos
    db_path = project_root / "guardias.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)  # echo=False, usamos custom logger

    # Configurar auditor
    auditor = setup_query_logging(engine)

    # Crear sesión
    session = Session(engine)

    try:
        # Auditar flujos críticos
        audit_flujo_carga_inicial(session, auditor)
        audit_flujo_asignacion_guardias(session, auditor)
        audit_flujo_gestion_ausencias(session, auditor)

        # Generar reporte
        auditor.print_report()

    finally:
        session.close()


if __name__ == "__main__":
    main()
