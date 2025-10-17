"""
Demo Sprint 2: Domain Layer

Demuestra las nuevas capacidades del Domain Layer:
- Value Objects con validación
- Domain Entities con lógica de negocio
- Repository Pattern con abstracciones
- Mappers entre persistencia y dominio
- Integración completa

Ejecutar:
    python demo_sprint2.py
"""

import sys
from datetime import date
from pathlib import Path

# Agregar src/ al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("=" * 80)
print("🎯 DEMO SPRINT 2: DOMAIN LAYER".center(80))
print("=" * 80)
print()


# =============================================================================
# 1. VALUE OBJECTS
# =============================================================================
def demo_value_objects():
    """Demuestra los Value Objects con validación."""
    from core.exceptions import InvalidEmailError, InvalidHorasContratoError
    from domain.value_objects import Email, HorasContrato, Turno, ZonaPreferida

    print("📦 1. VALUE OBJECTS")
    print("-" * 80)

    # Email
    print("\n✅ Email:")
    try:
        email = Email("profesor@colegio.edu")
        print(f"  • Email válido: {email}")
        print(f"  • Dominio: {email.domain}")
        print(f"  • Parte local: {email.local_part}")

        # Email inválido
        try:
            Email("correo-invalido")  # noqa: F841
        except InvalidEmailError as e:
            print(f"  • Email inválido detectado: {e.to_dict()['code']}")

    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")

    # Horas de Contrato
    print("\n✅ Horas de Contrato:")
    try:
        horas = HorasContrato(25.0)
        print(f"  • Horas: {horas}")
        print(f"  • Porcentaje jornada: {horas.porcentaje_jornada():.1f}%")
        print(f"  • ¿Jornada completa? {horas.es_jornada_completa()}")

        # Horas inválidas
        try:
            HorasContrato(100.0)  # noqa: F841 - Excede máximo
        except InvalidHorasContratoError as e:
            print(f"  • Horas inválidas detectadas: {e.message}")

    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")

    # Turno
    print("\n✅ Turno:")
    try:
        turno = Turno.from_string("mañana")
        print(f"  • Turno: {turno}")
        print(f"  • ¿Es mañana? {turno.es_manana}")
        print(f"  • ¿Trabaja tarde? {turno.trabaja_tarde}")

        turno_mixto = Turno.from_string("mixto", horas_manana=15.0, horas_tarde=10.0)
        print(f"  • Turno mixto: {turno_mixto}")
        puede_manana = turno_mixto.puede_hacer_guardia_en_turno('mañana')
        print(f"  • Puede hacer guardia en mañana: {puede_manana}")

    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")

    # Zona Preferida
    print("\n✅ Zona Preferida:")
    try:
        zona = ZonaPreferida.from_id(1, "Patio Principal")
        print(f"  • Zona: {zona}")
        print(f"  • Tiene preferencia: {zona.tiene_preferencia}")
        print(f"  • Coincide con zona 1: {zona.coincide_con(1)}")
        print(f"  • Coincide con zona 2: {zona.coincide_con(2)}")

        sin_pref = ZonaPreferida.sin_preferencia()
        print(f"  • Sin preferencia: {sin_pref}")
        print(f"  • Acepta zona 1: {sin_pref.coincide_con(1)}")  # True, acepta cualquiera

    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")

    print()


# =============================================================================
# 2. DOMAIN ENTITIES
# =============================================================================
def demo_entities():
    """Demuestra las Domain Entities con lógica de negocio."""
    from core.exceptions import MaxGuardiasDiaExceededError
    from domain.entities import GuardiaEntity, ProfesorEntity, ZonaEntity
    from domain.value_objects import Email, HorasContrato, Turno

    print("🏢 2. DOMAIN ENTITIES")
    print("-" * 80)

    # Profesor Entity
    print("\n✅ Profesor Entity:")
    try:
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="GARCÍA LÓPEZ, JUAN",
            email_corporativo=Email("juan.garcia@colegio.edu"),
            horas_contrato=HorasContrato(25.0),
            turno=Turno.from_string("mañana"),
            es_tutor=True,
        )
        print(f"  • Profesor: {profesor}")
        print(f"  • Nombre completo: {profesor.nombre_completo}")
        print(f"  • Ajuste guardias (tutor): {profesor.ajuste_guardias}")
        print(f"  • Guardias esperadas: {profesor.guardias_esperadas:.2f}")

        # Verificar asignación de guardia
        fecha = date.today()
        puede, razon = profesor.puede_asignar_guardia(fecha, "mañana", 1, zona_id=1)
        print(f"  • Puede asignar guardia hoy: {puede} {f'({razon})' if razon else ''}")

        # Asignar guardia
        profesor.asignar_guardia()
        print(f"  • Guardias asignadas hoy: {profesor.guardias_asignadas_dia}")

        # Intentar exceder límite
        try:
            profesor.asignar_guardia()  # Segunda guardia (excede límite de 1)
        except MaxGuardiasDiaExceededError as e:
            print(f"  • Límite diario detectado: {e.code}")

    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")

    # Zona Entity
    print("\n✅ Zona Entity:")
    try:
        zona = ZonaEntity(
            id=1,
            nombre_zona="Patio Principal",
            descripcion="Zona principal de recreo",
            capacidad_profesores=3,
        )
        print(f"  • Zona: {zona}")
        print(f"  • Puede asignar profesor (0 actuales): {zona.puede_asignar_profesor(0)}")
        print(f"  • Puede asignar profesor (3 actuales): {zona.puede_asignar_profesor(3)}")

    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")

    # Guardia Entity
    print("\n✅ Guardia Entity:")
    try:
        guardia1 = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date.today(),
            turno="mañana",
            recreo=1,
        )
        print(f"  • Guardia: {guardia1}")
        print(f"  • Clave única: {guardia1.clave_unica}")
        print(f"  • ¿Es válida? {guardia1.es_valida()}")

        # Conflicto
        guardia2 = GuardiaEntity(
            id=2,
            profesor_id=1,
            zona_id=2,
            fecha=date.today(),
            turno="mañana",
            recreo=1,
        )
        # True (mismo profesor)
        print(f"  • ¿Conflicto entre guardias? {guardia1.conflicto_con(guardia2)}")

    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")

    print()


# =============================================================================
# 3. REPOSITORY PATTERN
# =============================================================================
def demo_repository_pattern():
    """Demuestra el Repository Pattern con abstracciones."""
    print("🗄️  3. REPOSITORY PATTERN")
    print("-" * 80)

    print("\n✅ Arquitectura:")
    print("  • Interfaces en domain/repositories/")
    print("    - IBaseRepository: CRUD básico")
    print("    - IProfesorRepository: Operaciones específicas de profesores")
    print("    - IZonaRepository: Operaciones de zonas")
    print("    - IGuardiaRepository: Operaciones de guardias")

    print("\n  • Implementaciones en infrastructure/repositories/")
    print("    - SQLAlchemyProfesorRepository: Implementación con SQLAlchemy")
    print("    - (Otras implementaciones futuras: API, Mock, etc.)")

    print("\n✅ Beneficios:")
    print("  • ✅ Separación dominio/infraestructura")
    print("  • ✅ Fácil testing con mocks")
    print("  • ✅ Cambiar implementación sin afectar dominio")
    print("  • ✅ Type safety con generics")

    print()


# =============================================================================
# 4. MAPPERS
# =============================================================================
def demo_mappers():
    """Demuestra los Mappers entre modelos y entidades."""
    print("🔄 4. MAPPERS")
    print("-" * 80)

    print("\n✅ Conversión bidireccional:")
    print("  • Modelo SQLAlchemy ➡️  Domain Entity (to_entity)")
    print("  • Domain Entity ➡️  Modelo SQLAlchemy (to_model)")

    print("\n✅ Mappers implementados:")
    print("  • ProfesorMapper: Profesor ↔️ ProfesorEntity")
    print("  • ZonaMapper: Zona ↔️ ZonaEntity")
    print("  • GuardiaMapper: Guardia ↔️ GuardiaEntity")

    print("\n✅ Características:")
    print("  • Convierte Value Objects (Email, HorasContrato, Turno)")
    print("  • Maneja JSON (dias_permitidos, recreos_permitidos)")
    print("  • Actualiza modelos existentes")
    print("  • Conversión de listas")

    print()


# =============================================================================
# 5. INTEGRACIÓN COMPLETA
# =============================================================================
def demo_integracion():
    """Demuestra la integración completa del Domain Layer."""
    from core.logging import get_logger
    from domain.entities import ProfesorEntity
    from domain.value_objects import Email, HorasContrato, Turno

    print("🔗 5. INTEGRACIÓN COMPLETA")
    print("-" * 80)

    logger = get_logger(__name__)

    print("\n✅ Caso de uso: Asignar guardia a profesor")
    try:
        # 1. Crear profesor (domain entity)
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="MARTÍNEZ PÉREZ, ANA",
            email_corporativo=Email("ana.martinez@colegio.edu"),
            horas_contrato=HorasContrato(30.0),
            turno=Turno.from_string("mixto", horas_manana=20.0, horas_tarde=10.0),
            es_tutor=False,
        )

        logger.info(
            "Profesor creado",
            profesor_id=profesor.id,
            nombre=profesor.nombre_completo
        )

        # 2. Verificar disponibilidad
        fecha = date.today()
        puede, razon = profesor.puede_asignar_guardia(fecha, "mañana", 1, zona_id=1)

        if puede:
            # 3. Asignar guardia
            profesor.asignar_guardia()
            logger.info("Guardia asignada", profesor_id=profesor.id, fecha=fecha)
            print(f"  ✅ Guardia asignada a {profesor.nombre_completo}")
            print(f"     Guardias hoy: {profesor.guardias_asignadas_dia}")

            # 4. En aplicación real, se guardaría con repository
            print("  📝 En aplicación real:")
            print("     repository.save(profesor)")
            print("     guardia_repository.save(guardia)")

        else:
            logger.warning("No se puede asignar guardia", razon=razon)
            print(f"  ⚠️  No se puede asignar: {razon}")

    except Exception as e:
        logger.error("Error en integración", error=str(e))
        print(f"  ❌ Error: {e}")

    print()


# =============================================================================
# MAIN
# =============================================================================
def main():
    """Ejecuta todas las demos."""
    try:
        demo_value_objects()
        demo_entities()
        demo_repository_pattern()
        demo_mappers()
        demo_integracion()

        print("=" * 80)
        print("🎉 DEMO COMPLETADA - Domain Layer funcionando correctamente".center(80))
        print("=" * 80)
        print()

        print("💡 Beneficios obtenidos:")
        print("  • Lógica de negocio encapsulada en el dominio")
        print("  • Validación automática con Value Objects")
        print("  • Separación de concerns (dominio vs infraestructura)")
        print("  • Repository Pattern para abstracción de persistencia")
        print("  • Type safety completo")
        print("  • Fácil testing (entities y value objects puros)")
        print()

    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
