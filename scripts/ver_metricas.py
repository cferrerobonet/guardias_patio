#!/usr/bin/env python3
"""
Script para visualizar métricas de observabilidad desde terminal.

Uso:
    python scripts/ver_metricas.py              # Ver todo
    python scripts/ver_metricas.py --health     # Solo health checks
    python scripts/ver_metricas.py --metrics    # Solo métricas
    python scripts/ver_metricas.py --perf       # Solo performance
    python scripts/ver_metricas.py --slow       # Solo operaciones lentas
"""

import argparse
import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.observability import (
    HealthChecker,
    get_metrics,
    get_performance_monitor,
)
from database.db_manager import SessionLocal


def print_header(title: str):
    """Imprime encabezado formateado."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Imprime sección formateada."""
    print(f"\n{title}")
    print("-" * 70)


def show_health_checks():
    """Muestra health checks del sistema."""
    print_header("🏥 HEALTH CHECKS DEL SISTEMA")

    session = SessionLocal()

    try:
        checker = HealthChecker(session)
        health_status = checker.check_all()
        health_data = health_status.to_dict()

        # Mostrar estado general
        status = health_data["status"]
        status_emoji = {
            "HEALTHY": "✅",
            "DEGRADED": "⚠️",
            "UNHEALTHY": "❌",
        }.get(status, "❓")

        print(f"\n{status_emoji} Estado General: {status}")
        print(f"   Timestamp: {health_data['timestamp']}")

        # Mostrar componentes
        print_section("📊 Componentes")

        for component_data in health_data["components"]:
            status = component_data["status"]
            emoji = {
                "healthy": "✅",
                "degraded": "⚠️",
                "unhealthy": "❌",
                "unknown": "❓",
            }.get(status, "❓")

            component_name = component_data["name"]
            response_time = component_data.get("response_time_ms", "N/A")
            if response_time != "N/A":
                response_time = f"{response_time:.2f}ms"

            print(f"\n{emoji} {component_name.replace('_', ' ').title()}")
            print(f"   Status: {status}")
            print(f"   Response Time: {response_time}")

            # Detalles adicionales
            details = component_data.get("details", {})
            if details:
                print("   Detalles:")
                for key, value in details.items():
                    print(f"     • {key}: {value}")

        # Mostrar en formato texto limpio
        print_section("📄 Formato JSON")
        import json

        print(json.dumps(health_data, indent=2, ensure_ascii=False))

    finally:
        session.close()


def show_metrics():
    """Muestra métricas del sistema."""
    print_header("📊 MÉTRICAS DEL SISTEMA")

    metrics = get_metrics()
    summary = metrics.get_summary()

    print(f"\nEstado: {'✅ Activo' if summary['prometheus_available'] else '⚠️  Memoria'}")
    print(f"Métricas Registradas: {summary['metrics_count']}")
    print(f"Memoria Usado: {summary['memory_store_size']} registros")

    # Mostrar métricas en formato Prometheus
    print_section("📈 Exportación Prometheus")
    metrics_text = metrics.get_metrics_text()

    # Filtrar solo las líneas con valores (no comentarios)
    lines = [line for line in metrics_text.split("\n") if line and not line.startswith("#")]

    if lines:
        print("\nMétricas con valores:")
        for line in lines[:20]:  # Mostrar primeras 20
            print(f"  {line}")
        if len(lines) > 20:
            print(f"\n  ... y {len(lines) - 20} métricas más")
    else:
        print("\n⚠️  No hay métricas registradas todavía")

    # Mostrar memoria store si está disponible
    memory_store = metrics.get_memory_store()
    if memory_store:
        print_section("💾 Últimas Métricas en Memoria")
        print(f"\nTotal: {len(memory_store)} registros")
        print("\nÚltimas 5:")
        for metric in memory_store[-5:]:
            print(f"  • {metric.name}: {metric.value} @ {metric.timestamp.strftime('%H:%M:%S')}")


def show_performance():
    """Muestra estadísticas de performance."""
    print_header("⚡ PERFORMANCE MONITORING")

    monitor = get_performance_monitor()
    summary = monitor.get_summary()

    print(f"\nTotal Operaciones: {summary['total_operations']}")
    print(f"Operaciones Lentas: {summary['slow_operations']}")
    print(f"Porcentaje Lento: {summary['slow_percentage']:.2f}%")
    print(f"Operaciones Recientes (5min): {summary['recent_operations_5min']}")
    print(f"Tipos de Operaciones: {summary['tracked_operation_types']}")
    print(f"Alertas Activas: {summary['active_alerts']}")
    print(f"Umbral Lento: {summary['slow_threshold_ms']}ms")

    # Mostrar alertas
    alerts = monitor.get_alerts(clear=False)
    if alerts:
        print_section("🚨 Alertas Activas")
        for i, alert in enumerate(alerts, 1):
            print(f"\n{i}. {alert}")

    # Mostrar operaciones lentas
    slow_ops = monitor.get_slow_operations(limit=10)
    if slow_ops:
        print_section("🐌 Operaciones Más Lentas (Top 10)")
        print(f"\n{'#':<3} {'Operación':<30} {'Duración':<12} {'Timestamp':<20}")
        print("-" * 70)
        for i, op in enumerate(slow_ops, 1):
            timestamp = op.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i:<3} {op.operation:<30} {op.duration_ms:>8.2f}ms  {timestamp}")

    # Mostrar estadísticas por operación
    all_stats = monitor.get_all_operations_stats()
    if all_stats:
        print_section("📊 Estadísticas por Operación (Top 5)")
        print(f"\n{'Operación':<25} {'Count':<8} {'Avg':<10} {'P95':<10} {'Slow':<6}")
        print("-" * 70)
        for stats in all_stats[:5]:
            print(
                f"{stats.operation:<25} {stats.count:<8} "
                f"{stats.avg_duration_ms:>7.2f}ms {stats.p95_duration_ms:>7.2f}ms "
                f"{stats.slow_operations:<6}"
            )


def show_slow_operations():
    """Muestra solo operaciones lentas."""
    print_header("🐌 OPERACIONES LENTAS")

    monitor = get_performance_monitor()
    slow_ops = monitor.get_slow_operations(limit=20, minutes=60)

    if not slow_ops:
        print("\n✅ No hay operaciones lentas en la última hora")
        return

    print(f"\nTotal operaciones lentas (última hora): {len(slow_ops)}\n")
    print(f"{'#':<4} {'Operación':<35} {'Duración':<12} {'Timestamp':<20}")
    print("-" * 75)

    for i, op in enumerate(slow_ops, 1):
        timestamp = op.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        duration_str = f"{op.duration_ms:.2f}ms"

        # Colorear según gravedad
        if op.duration_ms > 5000:
            marker = "🔴"
        elif op.duration_ms > 2000:
            marker = "🟠"
        else:
            marker = "🟡"

        print(f"{i:<4} {marker} {op.operation:<33} {duration_str:>10}  {timestamp}")

        # Mostrar metadata si existe
        if op.metadata:
            for key, value in op.metadata.items():
                print(f"       └─ {key}: {value}")


def show_all():
    """Muestra toda la información."""
    show_health_checks()
    show_metrics()
    show_performance()


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Visualizar métricas de observabilidad del sistema"
    )
    parser.add_argument("--health", action="store_true", help="Mostrar solo health checks")
    parser.add_argument("--metrics", action="store_true", help="Mostrar solo métricas")
    parser.add_argument("--perf", action="store_true", help="Mostrar solo performance")
    parser.add_argument("--slow", action="store_true", help="Mostrar solo operaciones lentas")

    args = parser.parse_args()

    # Si no se especifica nada, mostrar todo
    if not any([args.health, args.metrics, args.perf, args.slow]):
        show_all()
    else:
        if args.health:
            show_health_checks()
        if args.metrics:
            show_metrics()
        if args.perf:
            show_performance()
        if args.slow:
            show_slow_operations()

    print("\n")  # Línea final


if __name__ == "__main__":
    main()
