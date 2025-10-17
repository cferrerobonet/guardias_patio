#!/usr/bin/env python3
"""
Demo de los nuevos módulos implementados en Sprint 1.

Muestra el uso de:
- config.settings (configuración centralizada con Pydantic)
- core.exceptions (sistema robusto de excepciones)
- core.logging (logging estructurado)
"""

import sys
from pathlib import Path

# Añadir src/ al path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def demo_config():
    """Demuestra el módulo de configuración."""
    from config import settings

    print("=" * 70)
    print("🔧 DEMO: Configuración Centralizada (Pydantic Settings)")
    print("=" * 70)

    print("\n📱 Aplicación:")
    print(f"  • Nombre: {settings.app_name}")
    print(f"  • Versión: {settings.app_version}")
    print(f"  • Ambiente: {settings.environment}")

    print("\n💾 Base de Datos:")
    print(f"  • URL: {settings.database_url}")
    print(f"  • Pool size: {settings.pool_size}")
    print(f"  • Path: {settings.get_database_path()}")

    print("\n📊 Logging:")
    print(f"  • Nivel: {settings.log_level}")
    print(f"  • Archivo: {settings.log_file}")
    print(f"  • Estructurado: {settings.structured_logging}")

    print("\n🎛️ Features:")
    print(f"  • Zona Preferida: {settings.feature_zona_preferida}")
    print(f"  • Matriz Horario: {settings.feature_matriz_horario}")
    print(f"  • Ausencias: {settings.feature_ausencias}")

    print("\n⚙️ Validaciones:")
    print(f"  • Max guardias/día: {settings.max_guardias_por_profesor_dia}")
    print(f"  • Horas contrato: {settings.min_horas_contrato} - {settings.max_horas_contrato}")

    print("\n✅ Type Safety:")
    print(f"  • Turnos válidos: {settings.turnos_validos}")
    print(f"  • Días semana: {list(settings.dias_semana.values())}")


def demo_exceptions():
    """Demuestra el sistema de excepciones."""
    from core.exceptions import (
        InvalidEmailError,
        MaxGuardiasDiaExceededError,
        ProfesorNotFoundError,
        format_exception_for_user,
        is_user_error,
    )

    print("\n" + "=" * 70)
    print("🛡️ DEMO: Sistema de Excepciones Robusto")
    print("=" * 70)

    # Ejemplo 1: ProfesorNotFoundError
    print("\n1️⃣ Excepción con contexto:")
    try:
        raise ProfesorNotFoundError(
            profesor_id=123,
            message="No se encontró el profesor en la base de datos"
        )
    except ProfesorNotFoundError as e:
        print(f"   • String: {e}")
        print(f"   • Código: {e.code}")
        print(f"   • Contexto: {e.context}")
        print(f"   • Dict: {e.to_dict()}")
        print(f"   • Es error de usuario: {is_user_error(e)}")
        print(f"   • Mensaje para UI: {format_exception_for_user(e)}")

    # Ejemplo 2: ValidationError
    print("\n2️⃣ Error de validación:")
    try:
        raise InvalidEmailError(
            email="usuario@invalido",
            message="El formato del email no es válido"
        )
    except InvalidEmailError as e:
        print(f"   • {e}")
        print(f"   • Es error de usuario: {is_user_error(e)}")

    # Ejemplo 3: BusinessLogicError
    print("\n3️⃣ Error de lógica de negocio:")
    try:
        raise MaxGuardiasDiaExceededError(
            profesor_id=456,
            fecha="2025-10-17",
            message="El profesor ya tiene el máximo de guardias para este día"
        )
    except MaxGuardiasDiaExceededError as e:
        print(f"   • {e}")
        print(f"   • Contexto completo: {e.context}")


def demo_logging():
    """Demuestra el sistema de logging."""
    import time

    from core.logging import (
        get_logger,
        log_context,
        log_execution_time,
        log_function_call,
    )

    print("\n" + "=" * 70)
    print("📊 DEMO: Logging Estructurado")
    print("=" * 70)

    # Logger básico
    print("\n1️⃣ Logger estructurado:")
    logger = get_logger(__name__)
    logger.info("evento_simple", mensaje="Esto es un log estructurado")
    logger.info("profesor_creado", profesor_id=123, nombre="Juan García")

    # Context manager
    print("\n2️⃣ Context manager (contexto automático):")
    with log_context(user_id=999, operation="demo"):
        logger.info("operacion_con_contexto")
        logger.info("otra_operacion")

    # Tracking de tiempo
    print("\n3️⃣ Tracking de tiempo de ejecución:")
    with log_execution_time(logger, "operacion_lenta"):
        time.sleep(0.1)  # Simular operación

    # Decorador
    print("\n4️⃣ Decorador de función:")

    @log_function_call()
    def calcular_guardias(profesor_id: int, mes: int) -> dict:
        """Función de ejemplo."""
        time.sleep(0.05)
        return {"profesor_id": profesor_id, "guardias": 12}

    resultado = calcular_guardias(profesor_id=123, mes=10)
    print(f"   Resultado: {resultado}")


def demo_integration():
    """Demuestra integración de todos los módulos."""
    from core.exceptions import ProfesorNotFoundError, format_exception_for_user
    from core.logging import get_logger, log_context

    print("\n" + "=" * 70)
    print("🔗 DEMO: Integración de Módulos")
    print("=" * 70)

    logger = get_logger("integration_demo")

    print("\n💡 Caso de uso real: Buscar profesor")

    with log_context(operation="buscar_profesor", user="admin"):
        logger.info("inicio_operacion", profesor_id=999)

        try:
            # Simular búsqueda
            profesor_id = 999
            profesor = None  # Simular no encontrado

            if not profesor:
                logger.warning("profesor_no_encontrado", profesor_id=profesor_id)
                raise ProfesorNotFoundError(
                    profesor_id=profesor_id,
                    message=f"No existe profesor con ID {profesor_id}"
                )

        except ProfesorNotFoundError as e:
            logger.error(
                "error_busqueda",
                error_code=e.code,
                profesor_id=profesor_id,
            )

            # Mensaje para mostrar al usuario
            mensaje_ui = format_exception_for_user(e)
            print(f"\n   ⚠️ Mensaje para usuario: {mensaje_ui}")

            # Verificar si debemos loggear el error a Sentry/tracking
            from core.exceptions import is_user_error
            if not is_user_error(e):
                print("   📨 Se enviaría a sistema de tracking de errores")
            else:
                print("   ℹ️ Error de usuario, no se envía a tracking")


def main():
    """Ejecuta todas las demos."""
    print("\n")
    print("🎯" * 35)
    print("🎯 DEMO: Nuevos Módulos Sprint 1")
    print("🎯" * 35)

    try:
        demo_config()
        demo_exceptions()
        demo_logging()
        demo_integration()

        print("\n" + "=" * 70)
        print("✅ DEMO COMPLETADA - Todos los módulos funcionando correctamente")
        print("=" * 70)
        print("\n💡 Beneficios obtenidos:")
        print("  • Configuración centralizada y validada")
        print("  • Excepciones con contexto rico")
        print("  • Logging estructurado para análisis")
        print("  • Type safety con Pydantic")
        print("  • 100% backward compatible")
        print("\n📚 Ver documentación en:")
        print("  • documentacion/desarrollo/plan-refactorizacion-escalabilidad.md")
        print("  • documentacion/desarrollo/resumen-refactorizacion-sprint1.md")
        print()

    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
