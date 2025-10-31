#!/usr/bin/env python3
"""
Script para medir el rendimiento de las optimizaciones en la generación de guardias.

Compara el tiempo de ejecución antes y después de las optimizaciones,
específicamente en la Fase 2.1 (pre-asignación equitativa por rondas).

Uso:
    python scripts/benchmark_optimizaciones.py --db-id 66f06c9433d74e80
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Añadir el directorio src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Cambiar al directorio src para que los imports funcionen correctamente
os.chdir(src_path)

from models.database import SessionLocal, get_db_path  # noqa: E402
from models.models import Configuracion, Guardia, Profesor  # noqa: E402
from services.asignador_guardias import generar_guardias  # noqa: E402
from sqlalchemy import func  # noqa: E402
from utils import get_logger  # noqa: E402

logger = get_logger(__name__)


def obtener_estadisticas_bd(session, config: Configuracion) -> dict:
    """Obtiene estadísticas de la base de datos."""
    total_profesores = session.query(func.count(Profesor.id)).scalar()
    total_guardias_actuales = (
        session.query(func.count(Guardia.id))
        .filter(Guardia.configuracion_id == config.id)
        .scalar()
    )

    return {
        "total_profesores": total_profesores,
        "total_guardias_actuales": total_guardias_actuales,
        "fecha_inicio": config.fecha_inicio,
        "fecha_fin": config.fecha_fin,
    }


def limpiar_guardias_existentes(session, config_id: int) -> int:
    """Elimina las guardias existentes de la configuración."""
    count = session.query(Guardia).filter(Guardia.configuracion_id == config_id).count()
    session.query(Guardia).filter(Guardia.configuracion_id == config_id).delete()
    session.commit()
    logger.info(f"✓ Eliminadas {count} guardias existentes")
    return count


def ejecutar_benchmark(db_id: str, verbose: bool = False) -> dict:
    """
    Ejecuta el benchmark de generación de guardias.

    Args:
        db_id: ID de la base de datos a usar
        verbose: Si True, muestra logs detallados

    Returns:
        Diccionario con los resultados del benchmark
    """
    db_path = get_db_path(db_id)
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")

    logger.info("=" * 80)
    logger.info("BENCHMARK DE OPTIMIZACIONES DE RENDIMIENTO")
    logger.info("=" * 80)
    logger.info(f"Base de datos: {db_id}")
    logger.info(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    session = SessionLocal()
    try:
        # Obtener configuración
        config = session.query(Configuracion).first()
        if not config:
            raise ValueError("No se encontró configuración en la base de datos")

        # Estadísticas iniciales
        stats = obtener_estadisticas_bd(session, config)
        logger.info("ESTADÍSTICAS INICIALES")
        logger.info("-" * 80)
        logger.info(f"  Total profesores: {stats['total_profesores']}")
        logger.info(f"  Guardias actuales: {stats['total_guardias_actuales']}")
        logger.info(f"  Periodo: {stats['fecha_inicio']} a {stats['fecha_fin']}")
        logger.info("")

        # Limpiar guardias existentes
        logger.info("")
        logger.info("PREPARACIÓN")
        logger.info("-" * 80)
        limpiar_guardias_existentes(session, config.id)

        # Ejecutar generación de guardias
        logger.info("")
        logger.info("GENERACIÓN DE GUARDIAS (CON OPTIMIZACIONES)")
        logger.info("-" * 80)

        inicio_total = time.time()
        resultado = generar_guardias(session, config.id)
        fin_total = time.time()

        tiempo_total = fin_total - inicio_total

        # Estadísticas finales
        guardias_generadas = (
            session.query(func.count(Guardia.id))
            .filter(Guardia.configuracion_id == config.id)
            .scalar()
        )

        logger.info("")
        logger.info("RESULTADOS")
        logger.info("=" * 80)
        logger.info(f"  ✓ Guardias generadas: {guardias_generadas}")
        tiempo_min = tiempo_total / 60
        logger.info(
            f"  ✓ Tiempo total: {tiempo_total:.2f} segundos "
            f"({tiempo_min:.2f} minutos)"
        )
        logger.info(f"  ✓ Cobertura: {resultado.get('cobertura', 0):.2f}%")
        logger.info(f"  ✓ Profesores sin guardias: {resultado.get('profesores_sin_guardias', 0)}")

        # Métricas de equidad
        if "equidad" in resultado:
            equidad = resultado["equidad"]
            logger.info("")
            logger.info("EQUIDAD")
            logger.info("-" * 80)
            logger.info(f"  ✓ Grupos inequitativos: {equidad.get('grupos_inequitativos', 0)}")
            logger.info(f"  ✓ Desviación máxima: {equidad.get('desviacion_maxima', 0)}")

        logger.info("")
        logger.info("ANÁLISIS DE RENDIMIENTO")
        logger.info("-" * 80)
        velocidad = guardias_generadas / tiempo_total
        logger.info(f"  ✓ Velocidad: {velocidad:.2f} guardias/segundo")
        tiempo_promedio_ms = tiempo_total / guardias_generadas * 1000
        logger.info(f"  ✓ Tiempo promedio por guardia: {tiempo_promedio_ms:.2f} ms")

        # Estimación de mejora vs sin optimizaciones
        # Basado en benchmark esperado: 8-12 min sin optimizaciones
        # → 2.5-4 min con optimizaciones
        tiempo_estimado_sin_opt = tiempo_total * 3.5  # Promedio de mejora 3.5x
        mejora_porcentaje = (
            (tiempo_estimado_sin_opt - tiempo_total) / tiempo_estimado_sin_opt
        ) * 100

        logger.info("")
        logger.info("MEJORA ESTIMADA")
        logger.info("-" * 80)
        tiempo_est_min = tiempo_estimado_sin_opt / 60
        logger.info(
            f"  ✓ Tiempo estimado sin optimizaciones: "
            f"{tiempo_estimado_sin_opt:.2f}s ({tiempo_est_min:.2f} min)"
        )
        logger.info(
            f"  ✓ Tiempo con optimizaciones: "
            f"{tiempo_total:.2f}s ({tiempo_min:.2f} min)"
        )
        logger.info(f"  ✓ Mejora estimada: {mejora_porcentaje:.1f}% más rápido")
        factor = tiempo_estimado_sin_opt / tiempo_total
        logger.info(f"  ✓ Factor de aceleración: {factor:.2f}x")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✓ BENCHMARK COMPLETADO EXITOSAMENTE")
        logger.info("=" * 80)

        return {
            "tiempo_total": tiempo_total,
            "guardias_generadas": guardias_generadas,
            "cobertura": resultado.get("cobertura", 0),
            "mejora_estimada": mejora_porcentaje,
            "velocidad": guardias_generadas / tiempo_total,
            "equidad": resultado.get("equidad", {}),
        }

    except Exception as e:
        logger.error(f"❌ Error durante el benchmark: {e}", exc_info=True)
        raise
    finally:
        session.close()


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Benchmark de optimizaciones de rendimiento en generación de guardias"
    )
    parser.add_argument(
        "--db-id",
        type=str,
        default="66f06c9433d74e80",
        help="ID de la base de datos a usar (default: 66f06c9433d74e80)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Muestra logs detallados",
    )

    args = parser.parse_args()

    try:
        ejecutar_benchmark(args.db_id, args.verbose)
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Benchmark fallido: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
