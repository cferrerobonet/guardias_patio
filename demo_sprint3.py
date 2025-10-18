"""
Demo Sprint 3: Application Layer

Demuestra el funcionamiento de la capa de aplicación con Use Cases y DTOs.
"""

import sys
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Añadir src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from application.dtos import (  # noqa: E402
    CrearGuardiaDTO,
    CrearProfesorDTO,
    FiltroGuardiasDTO,
)
from application.use_cases.guardia import (  # noqa: E402
    AsignarGuardiaUseCase,
    ObtenerGuardiasUseCase,
)
from application.use_cases.profesor import (  # noqa: E402
    CrearProfesorUseCase,
    ListarProfesoresUseCase,
    ObtenerProfesorUseCase,
)
from core.exceptions import BusinessLogicError, NotFoundError, ValidationError  # noqa: E402
from core.logging import get_logger, setup_logging  # noqa: E402
from models.models import Base  # noqa: E402

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def crear_base_datos_temporal() -> Session:
    """Crea una base de datos en memoria para el demo."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def demo_dtos():
    """Demuestra el funcionamiento de los DTOs con validación."""
    print("\n" + "=" * 80)
    print("📦 1. DATA TRANSFER OBJECTS (DTOs)")
    print("=" * 80)

    # DTO válido
    print("\n✅ Crear DTO válido:")
    try:
        dto = CrearProfesorDTO(
            nombre_completo="GARCÍA LÓPEZ, JUAN",
            email_corporativo="juan.garcia@colegio.edu",
            horas_contrato=25.0,
            turno="mañana",
            es_tutor=True,
            dias_semana_permitidos=[0, 1, 2, 3, 4],  # Lunes a Viernes
            recreos_permitidos=[1, 2]
        )
        print(f"  • Nombre: {dto.nombre_completo}")
        print(f"  • Email: {dto.email_corporativo}")
        print(f"  • Horas: {dto.horas_contrato}")
        print(f"  • Turno: {dto.turno}")
        print("  ✅ DTO creado y validado correctamente")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # DTO inválido - email mal formateado
    print("\n❌ Intentar crear DTO con email inválido:")
    try:
        CrearProfesorDTO(  # noqa: F841
            nombre_completo="PÉREZ MARTÍN, ANA",
            email_corporativo="email-invalido",  # Email sin @
            horas_contrato=30.0,
            turno="tarde",
            es_tutor=False
        )
        print("  ⚠️  No debería llegar aquí")
    except Exception as e:
        print(f"  ✅ Validación detectó error: {type(e).__name__}")

    # DTO inválido - horas fuera de rango
    print("\n❌ Intentar crear DTO con horas inválidas:")
    try:
        CrearProfesorDTO(  # noqa: F841
            nombre_completo="LÓPEZ SÁNCHEZ, CARLOS",
            horas_contrato=50.0,  # Más de 40 horas
            turno="mañana",
            es_tutor=False
        )
        print("  ⚠️  No debería llegar aquí")
    except Exception:
        print("  ✅ Validación detectó error: horas > 40")


def demo_use_cases_profesor(session: Session):
    """Demuestra los Use Cases de Profesor."""
    print("\n" + "=" * 80)
    print("👤 2. USE CASES DE PROFESOR")
    print("=" * 80)

    # Crear profesor
    print("\n✅ Crear profesor:")
    try:
        crear_uc = CrearProfesorUseCase(session)
        dto_crear = CrearProfesorDTO(
            nombre_completo="MARTÍNEZ PÉREZ, ANA",
            email_corporativo="ana.martinez@colegio.edu",
            horas_contrato=30.0,
            turno="mañana",
            es_tutor=True,
            dias_semana_permitidos=[0, 1, 2, 3, 4],
            recreos_permitidos=[1, 2]
        )
        profesor_dto = crear_uc.execute(dto_crear)
        print(f"  • ID: {profesor_dto.id}")
        print(f"  • Nombre: {profesor_dto.nombre_completo}")
        print(f"  • Email: {profesor_dto.email_corporativo}")
        print(f"  • Horas: {profesor_dto.horas_contrato}h ({profesor_dto.porcentaje_jornada}%)")
        print(f"  • Es tutor: {profesor_dto.es_tutor}")
        print(f"  • Ajuste guardias: {profesor_dto.ajuste_guardias}")
        print(f"  • Guardias esperadas: {profesor_dto.guardias_esperadas:.2f}")
        print("  ✅ Profesor creado exitosamente")

        profesor_id = profesor_dto.id

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

    # Obtener profesor por ID
    print("\n✅ Obtener profesor por ID:")
    try:
        obtener_uc = ObtenerProfesorUseCase(session)
        profesor_dto = obtener_uc.execute(profesor_id)
        print(f"  • Encontrado: {profesor_dto.nombre_completo}")
        print(f"  • Turno: {profesor_dto.turno}")
        print("  ✅ Profesor obtenido correctamente")
    except NotFoundError as e:
        print(f"  ❌ No encontrado: {e}")

    # Listar profesores
    print("\n✅ Listar todos los profesores:")
    try:
        listar_uc = ListarProfesoresUseCase(session)
        profesores = listar_uc.execute()
        print(f"  • Total profesores: {len(profesores)}")
        for p in profesores:
            print(f"    - {p.nombre_completo} ({p.turno}, {p.horas_contrato}h)")
        print("  ✅ Profesores listados correctamente")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Intentar crear profesor duplicado
    print("\n❌ Intentar crear profesor duplicado:")
    try:
        dto_duplicado = CrearProfesorDTO(
            nombre_completo="MARTÍNEZ PÉREZ, ANA",  # Mismo nombre
            horas_contrato=25.0,
            turno="tarde",
            es_tutor=False
        )
        crear_uc.execute(dto_duplicado)
        print("  ⚠️  No debería llegar aquí")
    except ValidationError:
        print("  ✅ Validación detectó duplicado")

    return profesor_id


def demo_use_cases_guardia(session: Session, profesor_id: int):
    """Demuestra los Use Cases de Guardia."""
    print("\n" + "=" * 80)
    print("🛡️  3. USE CASES DE GUARDIA")
    print("=" * 80)

    # Primero necesitamos crear una zona
    from models.models import Zona
    zona = Zona(nombre_zona="Patio Principal", descripcion="Patio de recreo principal")
    session.add(zona)
    session.commit()
    zona_id = zona.id

    print(f"\n📍 Zona creada: {zona.nombre_zona} (ID: {zona_id})")

    # Asignar guardia
    print("\n✅ Asignar guardia:")
    try:
        asignar_uc = AsignarGuardiaUseCase(session)
        dto_guardia = CrearGuardiaDTO(
            fecha=date.today(),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor_id,
            zona_id=zona_id,
            es_sustitucion=False
        )
        guardia_dto = asignar_uc.execute(dto_guardia)
        print(f"  • ID Guardia: {guardia_dto.id}")
        print(f"  • Fecha: {guardia_dto.fecha}")
        print(f"  • Turno: {guardia_dto.turno} - Recreo {guardia_dto.numero_recreo}")
        print(f"  • Profesor: {guardia_dto.profesor_nombre}")
        print(f"  • Zona: {guardia_dto.zona_nombre}")
        print("  ✅ Guardia asignada exitosamente")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    # Intentar asignar guardia duplicada
    print("\n❌ Intentar asignar guardia duplicada (mismo profesor, momento):")
    try:
        dto_duplicada = CrearGuardiaDTO(
            fecha=date.today(),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor_id,
            zona_id=zona_id
        )
        asignar_uc.execute(dto_duplicada)
        print("  ⚠️  No debería llegar aquí")
    except BusinessLogicError:
        print("  ✅ Validación detectó conflicto")

    # Obtener guardias con filtros
    print("\n✅ Obtener guardias con filtros:")
    try:
        obtener_uc = ObtenerGuardiasUseCase(session)

        # Por profesor
        filtro = FiltroGuardiasDTO(profesor_id=profesor_id)
        guardias = obtener_uc.execute(filtro)
        print(f"  • Guardias del profesor: {len(guardias)}")
        for g in guardias:
            print(
                f"    - {g.fecha} {g.turno} R{g.numero_recreo} "
                f"en {g.zona_nombre}"
            )

        # Por fecha
        filtro_fecha = FiltroGuardiasDTO(
            fecha_inicio=date.today(),
            fecha_fin=date.today()
        )
        guardias_hoy = obtener_uc.execute(filtro_fecha)
        print(f"  • Guardias de hoy: {len(guardias_hoy)}")

        print("  ✅ Guardias obtenidas correctamente")

    except Exception as e:
        print(f"  ❌ Error: {e}")


def demo_integracion_completa(session: Session):
    """Demuestra un flujo completo de uso."""
    print("\n" + "=" * 80)
    print("🔗 4. FLUJO COMPLETO DE INTEGRACIÓN")
    print("=" * 80)

    print("\n📋 Escenario: Asignar guardias a múltiples profesores")

    # Crear 3 profesores
    print("\n1️⃣  Crear profesores:")
    crear_uc = CrearProfesorUseCase(session)
    profesores_ids = []

    for i, datos in enumerate([
        ("GARCÍA LÓPEZ, JUAN", "mañana", True, 30.0),
        ("PÉREZ MARTÍN, ANA", "tarde", False, 25.0),
        ("LÓPEZ SÁNCHEZ, CARLOS", "mixto", True, 40.0),
    ], 1):
        nombre, turno, es_tutor, horas = datos
        dto = CrearProfesorDTO(
            nombre_completo=nombre,
            horas_contrato=horas,
            turno=turno,
            es_tutor=es_tutor,
            horas_manana=25.0 if turno == "mixto" else None,
            horas_tarde=15.0 if turno == "mixto" else None,
        )
        profesor = crear_uc.execute(dto)
        profesores_ids.append(profesor.id)
        print(f"  ✅ {i}. {nombre} ({turno})")

    # Crear 2 zonas
    print("\n2️⃣  Crear zonas:")
    from models.models import Zona
    zonas = [
        Zona(nombre_zona="Patio Principal", descripcion="Patio grande"),
        Zona(nombre_zona="Patio Infantil", descripcion="Zona pequeños"),
    ]
    for zona in zonas:
        session.add(zona)
    session.commit()
    print(f"  ✅ {len(zonas)} zonas creadas")

    # Asignar guardias
    print("\n3️⃣  Asignar guardias:")
    asignar_uc = AsignarGuardiaUseCase(session)
    guardias_creadas = 0

    for i, (profesor_id, zona_id, turno) in enumerate([
        (profesores_ids[0], zonas[0].id, "mañana"),
        (profesores_ids[2], zonas[1].id, "mañana"),
    ], 1):
        try:
            dto = CrearGuardiaDTO(
                fecha=date.today(),
                turno=turno,
                numero_recreo=1,
                profesor_id=profesor_id,
                zona_id=zona_id
            )
            guardia = asignar_uc.execute(dto)
            guardias_creadas += 1
            print(f"  ✅ {i}. {guardia.profesor_nombre} → {guardia.zona_nombre}")
        except Exception as e:
            print(f"  ❌ {i}. Error: {e}")

    # Obtener resumen
    print("\n4️⃣  Resumen del sistema:")
    listar_prof_uc = ListarProfesoresUseCase(session)
    obtener_guard_uc = ObtenerGuardiasUseCase(session)

    profesores = listar_prof_uc.execute()
    guardias = obtener_guard_uc.execute(FiltroGuardiasDTO())

    print(f"  • Total profesores: {len(profesores)}")
    print(f"  • Total guardias: {len(guardias)}")
    print(f"  • Guardias asignadas hoy: {guardias_creadas}")
    print("\n  ✅ Integración completa exitosa")


def main():
    """Función principal del demo."""
    print("=" * 80)
    print("          🎯 DEMO SPRINT 3: APPLICATION LAYER")
    print("=" * 80)

    # Crear sesión temporal
    session = crear_base_datos_temporal()

    try:
        # 1. DTOs y validación
        demo_dtos()

        # 2. Use Cases de Profesor
        profesor_id = demo_use_cases_profesor(session)

        if profesor_id:
            # 3. Use Cases de Guardia
            demo_use_cases_guardia(session, profesor_id)

        # 4. Integración completa
        demo_integracion_completa(session)

        print("\n" + "=" * 80)
        print("          🎉 DEMO COMPLETADA - Application Layer funcionando")
        print("=" * 80)

        print("\n💡 Beneficios obtenidos:")
        print("  • DTOs con validación automática (Pydantic)")
        print("  • Use Cases encapsulan lógica de aplicación")
        print("  • Separación de concerns (UI → Use Cases → Domain → Infra)")
        print("  • Transacciones manejadas en Use Cases")
        print("  • Validaciones de negocio en Domain Entities")
        print("  • Type safety completo en toda la capa")

    except Exception as e:
        logger.error("Error en demo", error=str(e))
        print(f"\n❌ Error en demo: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
