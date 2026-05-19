#!/usr/bin/env python3
"""
Demo del Sistema de Observabilidad - Sprint 7

Demuestra las capacidades del sistema de métricas, health checks y tracking.
"""

import sys
import time
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.observability import (
    HealthChecker,
    get_metrics,
    track_time,
    with_metrics,
)
from database.db_manager import SessionLocal


# Funciones de ejemplo con decoradores
@track_time("operacion_lenta")
def operacion_lenta():
    """Simula una operación que toma tiempo."""
    time.sleep(0.5)
    return "completado"


@with_metrics("operacion_rapida")
def operacion_rapida():
    """Simula una operación rápida."""
    time.sleep(0.01)
    return "ok"


@track_time("operacion_con_error")
def operacion_con_error():
    """Simula una operación que falla."""
    time.sleep(0.1)
    raise ValueError("Error simulado")


def demo_metricas():
    """Demo del sistema de métricas."""
    print("\n" + "=" * 70)
    print("🎯 DEMO: Sistema de Métricas")
    print("=" * 70)

    metrics = get_metrics()

    # 1. Contadores simples
    print("\n1️⃣  Incrementando contadores...")
    metrics.increment_counter("app_requests_total", 1.0, {"operation": "test", "status": "success"})
    metrics.increment_counter("app_requests_total", 1.0, {"operation": "test", "status": "success"})
    metrics.increment_counter("app_requests_total", 1.0, {"operation": "test", "status": "error"})
    print("   ✅ 3 contadores incrementados")

    # 2. Gauges
    print("\n2️⃣  Estableciendo gauges...")
    metrics.set_gauge("profesores_total", 25.0)
    metrics.set_gauge("guardias_total", 150.0)
    metrics.set_gauge("ausencias_activas", 3.0)
    print("   ✅ Gauges de negocio establecidos")

    # 3. Histogramas con context manager
    print("\n3️⃣  Midiendo operaciones con timer...")
    with metrics.timer("operacion_timer_test"):
        time.sleep(0.1)
    print("   ✅ Operación medida con context manager")

    # 4. Métricas con decoradores
    print("\n4️⃣  Probando decoradores...")
    print("   ⏱️  Ejecutando operación lenta...")
    operacion_lenta()
    print("   ✅ Operación lenta completada")

    print("   ⚡ Ejecutando operación rápida...")
    operacion_rapida()
    print("   ✅ Operación rápida completada")

    print("   ❌ Ejecutando operación con error...")
    try:
        operacion_con_error()
    except ValueError:
        print("   ✅ Error capturado correctamente")

    # 5. Cache metrics
    print("\n5️⃣  Registrando métricas de cache...")
    metrics.record_cache_hit("profesor")
    metrics.record_cache_hit("profesor")
    metrics.record_cache_miss("profesor")
    print("   ✅ 2 hits, 1 miss registrados")

    # 6. Database metrics
    print("\n6️⃣  Registrando métricas de database...")
    metrics.record_database_query("select", 0.025, success=True)
    metrics.record_database_query("insert", 0.050, success=True)
    metrics.record_database_query("update", 0.035, success=False)
    print("   ✅ 3 queries registradas")

    # 7. Business metrics
    print("\n7️⃣  Actualizando métricas de negocio...")
    metrics.update_business_metrics(
        profesores_count=30,
        guardias_count=200,
        guardias_hoy=15,
        ausencias_activas=5,
    )
    print("   ✅ Métricas de negocio actualizadas")

    # 8. System metrics
    print("\n8️⃣  Actualizando métricas del sistema...")
    metrics.update_system_metrics()
    print("   ✅ Métricas de CPU y memoria actualizadas")

    # Resumen
    print("\n📊 RESUMEN DE MÉTRICAS:")
    print("-" * 70)
    summary = metrics.get_summary()
    print(f"   • Prometheus disponible: {summary['prometheus_available']}")
    print(f"   • Métricas registradas: {summary['metrics_count']}")
    print(f"   • Eventos en memoria: {summary['memory_store_size']}")

    # Exportar métricas
    print("\n📝 EXPORTANDO MÉTRICAS:")
    print("-" * 70)
    metrics_text = metrics.get_metrics_text()
    print(metrics_text[:500] + "\n... (truncado)")


def demo_health_checks():
    """Demo del sistema de health checks."""
    print("\n" + "=" * 70)
    print("🏥 DEMO: Health Checks")
    print("=" * 70)

    session = SessionLocal()
    health_checker = HealthChecker(session)

    # 1. Check individual de database
    print("\n1️⃣  Verificando base de datos...")
    db_health = health_checker.check_database()
    print(f"   Estado: {db_health.state.value}")
    print(f"   Mensaje: {db_health.message}")
    print(f"   Tiempo de respuesta: {db_health.response_time_ms}ms")

    # 2. Check individual de cache
    print("\n2️⃣  Verificando cache...")
    cache_health = health_checker.check_cache()
    print(f"   Estado: {cache_health.state.value}")
    print(f"   Mensaje: {cache_health.message}")
    print(f"   Tiempo de respuesta: {cache_health.response_time_ms}ms")

    # 3. Check individual de configuración
    print("\n3️⃣  Verificando configuración...")
    config_health = health_checker.check_configuration()
    print(f"   Estado: {config_health.state.value}")
    print(f"   Mensaje: {config_health.message}")
    print(f"   Tiempo de respuesta: {config_health.response_time_ms}ms")

    # 4. Check individual de recursos
    print("\n4️⃣  Verificando recursos del sistema...")
    resources_health = health_checker.check_system_resources()
    print(f"   Estado: {resources_health.state.value}")
    print(f"   Mensaje: {resources_health.message}")
    if resources_health.details:
        print(f"   Detalles: {resources_health.details}")

    # 5. Check completo
    print("\n5️⃣  Ejecutando health check completo...")
    status = health_checker.check_all()
    print(f"\n   🎯 Estado General: {status.overall_state.value.upper()}")
    print(f"   • Saludable: {status.is_healthy}")
    print(f"   • Degradado: {status.is_degraded}")
    print(f"   • No saludable: {status.is_unhealthy}")

    # 6. Resumen textual
    print("\n📋 RESUMEN DE SALUD:")
    print("-" * 70)
    summary = health_checker.get_status_summary()
    print(summary)

    # 7. Formato JSON
    print("\n📄 FORMATO JSON:")
    print("-" * 70)
    import json

    print(json.dumps(status.to_dict(), indent=2))

    session.close()


def demo_integration():
    """Demo de integración con el sistema existente."""
    print("\n" + "=" * 70)
    print("🔗 DEMO: Integración con Sistema Existente")
    print("=" * 70)

    session = SessionLocal()

    try:
        # Importar use case real
        from application.use_cases.profesor import ListarProfesoresUseCase

        print("\n1️⃣  Ejecutando use case real con tracking...")

        # Obtener métricas antes
        metrics = get_metrics()
        print("   📊 Métricas antes de la operación:")
        print(f"      {metrics.get_summary()['memory_store_size']} eventos registrados")

        # Ejecutar use case
        with metrics.timer("listar_profesores"):
            use_case = ListarProfesoresUseCase(session)
            profesores = use_case.execute()

        print(f"   ✅ {len(profesores)} profesores obtenidos")

        # Métricas después
        print("   📊 Métricas después de la operación:")
        print(f"      {metrics.get_summary()['memory_store_size']} eventos registrados")

        # Health check
        print("\n2️⃣  Verificando salud del sistema...")
        health_checker = HealthChecker(session)
        if health_checker.is_healthy():
            print("   ✅ Sistema saludable")
        else:
            print("   ⚠️  Sistema no está completamente saludable")
            status = health_checker.check_all()
            for component in status.components:
                if not component.is_healthy:
                    print(f"      • {component.name}: {component.message}")

    finally:
        session.close()


def main():
    """Ejecuta todas las demos."""
    print("\n" + "🎯" * 35)
    print("🚀 DEMO COMPLETO - SISTEMA DE OBSERVABILIDAD - SPRINT 7")
    print("🎯" * 35)

    try:
        # Demo 1: Métricas
        demo_metricas()

        # Demo 2: Health Checks
        demo_health_checks()

        # Demo 3: Integración
        demo_integration()

        print("\n" + "=" * 70)
        print("✅ DEMO COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print("\n📚 Próximos pasos:")
        print("   1. Revisar documentación en documentacion/SPRINT_7_OBSERVABILIDAD.md")
        print("   2. Agregar decoradores a use cases críticos")
        print("   3. Implementar dashboard de observabilidad en UI")
        print("   4. Configurar exportación de métricas")
        print()

    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
