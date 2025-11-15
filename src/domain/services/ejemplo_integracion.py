"""
Ejemplo de integración de Domain Services en asignadores existentes.

Este ejemplo muestra cómo refactorizar un asignador para usar
los nuevos servicios de dominio, eliminando validaciones duplicadas
y mejorando la separación de responsabilidades.
"""

from datetime import date
from typing import Dict, List, Tuple

from models.models import Configuracion, Guardia, Profesor, Zona
from services.estadisticas_service import EstadisticasService
from sqlalchemy.orm import Session
from utils import get_logger

from domain.services import (
    AsignacionGuardiaService,
    DisponibilidadProfesorService,
    DistribucionCuotasService,
    EquidadGuardiasService,
)

logger = get_logger(__name__)


def generar_guardias_con_servicios_dominio(
    session: Session,
    configuracion_id: int,
    reportar_progreso=None,
) -> Tuple[List[Guardia], Dict[int, int]]:
    """
    Ejemplo de generación de guardias usando Domain Services.

    Ventajas sobre implementación anterior:
    - Validaciones centralizadas en servicios de dominio
    - Lógica de negocio desacoplada de infraestructura
    - Fácil de testear (mockear servicios)
    - Consistencia garantizada en todas las validaciones

    Args:
        session: Sesión de SQLAlchemy
        configuracion_id: ID de la configuración
        reportar_progreso: Callback para reportar progreso

    Returns:
        Tupla (guardias_generadas, cuotas_asignadas)
    """
    if reportar_progreso is None:
        reportar_progreso = lambda p, m: None

    logger.info("=" * 80)
    logger.info("GENERACIÓN DE GUARDIAS - USANDO DOMAIN SERVICES")
    logger.info("=" * 80)

    # PASO 1: Inicializar servicios de dominio
    logger.info("Paso 1: Inicializando servicios de dominio...")
    reportar_progreso(5, "Inicializando servicios...")

    disponibilidad_service = DisponibilidadProfesorService(session)
    distribucion_service = DistribucionCuotasService(session)
    asignacion_service = AsignacionGuardiaService(session)
    equidad_service = EquidadGuardiasService(session)
    stats_service = EstadisticasService(session)

    # PASO 2: Obtener datos básicos
    logger.info("Paso 2: Cargando configuración y profesores...")
    reportar_progreso(10, "Cargando datos...")

    config = session.query(Configuracion).get(configuracion_id)
    if not config:
        raise ValueError(f"Configuración {configuracion_id} no encontrada")

    profesores = session.query(Profesor).filter(Profesor.activo == True).all()
    zonas = session.query(Zona).all()

    logger.info(f"  ✓ Profesores activos: {len(profesores)}")
    logger.info(f"  ✓ Zonas disponibles: {len(zonas)}")

    # PASO 3: Calcular cuotas usando servicio de dominio
    logger.info("Paso 3: Calculando cuotas...")
    reportar_progreso(20, "Calculando cuotas de guardias...")

    cuotas = distribucion_service.calcular_cuotas(profesores)
    total_cuota = sum(cuotas.values())

    logger.info(f"  ✓ Total cuota: {total_cuota} guardias")

    # Mostrar información detallada de cuotas (opcional)
    for profesor in profesores[:3]:  # Mostrar primeros 3 como ejemplo
        info = distribucion_service.obtener_info_cuota(profesor)
        logger.debug(
            f"    • {info.nombre_profesor}: {info.cuota} guardias "
            f"(factor: {info.factor_participacion:.2f})"
        )

    # PASO 4: Generar slots y asignar guardias
    logger.info("Paso 4: Asignando guardias...")
    reportar_progreso(30, "Iniciando asignación...")

    calendario = []
    incidencias = []

    # Aquí iría la lógica de generación de slots y asignación
    # Este es un ejemplo simplificado

    from services.calculador_guardias import listar_dias_lectivos

    dias_lectivos = listar_dias_lectivos(config)
    total_dias = len(dias_lectivos)

    for i, fecha in enumerate(dias_lectivos):
        progreso = 30 + int((i / total_dias) * 60)
        reportar_progreso(progreso, f"Asignando guardias para {fecha}...")

        # Ejemplo: Asignar guardias para esta fecha
        for zona in zonas:
            for recreo_id in [1, 2]:  # Ejemplo: 2 recreos
                turno = "mañana" if recreo_id == 1 else "tarde"

                # Obtener profesores disponibles usando servicio de dominio
                profesores_disponibles = (
                    disponibilidad_service.obtener_profesores_disponibles(
                        profesores=profesores,
                        fecha=fecha,
                        turno_recreo=turno,
                        recreo_id=recreo_id,
                    )
                )

                if not profesores_disponibles:
                    incidencias.append(
                        f"Sin profesores disponibles: {fecha} - Recreo {recreo_id} - Zona {zona.id}"
                    )
                    continue

                # Seleccionar profesor (aquí se aplicaría lógica de scoring)
                # Por simplicidad, tomamos el primero disponible
                profesor_seleccionado = profesores_disponibles[0]

                # Validar y asignar usando servicio de dominio
                puede, razon = asignacion_service.puede_asignar_guardia(
                    profesor=profesor_seleccionado,
                    fecha=fecha,
                    turno=turno,
                    recreo_id=recreo_id,
                    zona_id=zona.id,
                    verificar_cuota=True,
                    cuota_maxima=cuotas.get(profesor_seleccionado.id, 0),
                )

                if puede:
                    # Crear guardia usando servicio
                    guardia = asignacion_service.asignar_guardia(
                        profesor=profesor_seleccionado,
                        fecha=fecha,
                        turno=turno,
                        recreo_id=recreo_id,
                        zona_id=zona.id,
                        validar_antes=False,  # Ya validamos arriba
                    )
                    session.add(guardia)
                    calendario.append(guardia)
                else:
                    incidencias.append(
                        f"No se pudo asignar a {profesor_seleccionado.nombre_completo}: {razon}"
                    )

    session.flush()

    # PASO 5: Evaluar equidad usando servicio de dominio
    logger.info("Paso 5: Evaluando equidad...")
    reportar_progreso(90, "Evaluando equidad de la distribución...")

    # Generar reporte de equidad
    equidad_service.log_reporte_equidad(calendario, cuotas)

    # Sugerir reasignaciones si es necesario
    indice_equidad = equidad_service.calcular_indice_equidad(calendario, cuotas)
    logger.info(f"  ✓ Índice de equidad: {indice_equidad:.2%}")

    if indice_equidad < 0.90:  # Si equidad < 90%
        logger.warning("  ⚠️  Equidad por debajo del objetivo (90%)")
        sugerencias = equidad_service.sugerir_reasignaciones(
            calendario, cuotas, max_sugerencias=5
        )
        if sugerencias:
            logger.info(f"  💡 {len(sugerencias)} sugerencias de mejora:")
            for sug in sugerencias[:3]:
                logger.info(f"    • {sug.razon} (mejora: {sug.mejora_esperada:.2%})")

    # PASO 6: Estadísticas finales
    logger.info("Paso 6: Generando estadísticas...")
    reportar_progreso(95, "Generando estadísticas finales...")

    stats = stats_service.generar_resumen_completo(
        guardias=calendario, profesores=profesores, cuotas=cuotas, total_slots=None
    )
    stats_service.log_resumen(stats)

    reportar_progreso(100, "✅ Generación completada")

    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ GENERACIÓN COMPLETADA")
    logger.info("=" * 80)
    logger.info(f"  • Guardias asignadas: {len(calendario)}")
    logger.info(f"  • Incidencias: {len(incidencias)}")
    logger.info(f"  • Índice de equidad: {indice_equidad:.2%}")
    logger.info("")

    # Retornar calendario y resumen de cuotas
    resumen_cuotas = stats_service.calcular_guardias_por_profesor(calendario)

    return calendario, resumen_cuotas


# ============================================================================
# EJEMPLO: Uso en caso de uso existente
# ============================================================================


def ejemplo_integracion_caso_uso(session: Session):
    """
    Ejemplo de cómo integrar Domain Services en un caso de uso existente.
    """
    from domain.services import (
        AsignacionGuardiaService,
        DisponibilidadProfesorService,
    )

    # Caso de uso: Asignar guardia manual
    profesor = session.query(Profesor).filter(Profesor.activo == True).first()
    fecha = date.today()
    turno = "mañana"
    recreo_id = 1
    zona_id = 1

    # Usar servicios de dominio para validación y asignación
    disponibilidad = DisponibilidadProfesorService(session)
    asignacion = AsignacionGuardiaService(session)

    # 1. Verificar disponibilidad
    disponible, razon = disponibilidad.esta_disponible(profesor, fecha, turno)

    if not disponible:
        logger.error(f"Profesor no disponible: {razon}")
        return None

    # 2. Validar asignación completa
    puede, razon = asignacion.puede_asignar_guardia(
        profesor, fecha, turno, recreo_id, zona_id
    )

    if not puede:
        logger.error(f"No se puede asignar guardia: {razon}")
        return None

    # 3. Asignar guardia
    try:
        guardia = asignacion.asignar_guardia(
            profesor, fecha, turno, recreo_id, zona_id, validar_antes=True
        )
        session.add(guardia)
        session.commit()
        logger.info(f"✅ Guardia asignada: {guardia.id}")
        return guardia
    except Exception as e:
        logger.error(f"Error al asignar guardia: {e}")
        session.rollback()
        return None


# ============================================================================
# EJEMPLO: Testing con Domain Services
# ============================================================================


def ejemplo_testing_con_mock():
    """
    Ejemplo de cómo testear código que usa Domain Services.

    Los servicios de dominio son fáciles de mockear, lo que permite
    tests unitarios rápidos sin necesidad de base de datos.
    """
    from unittest.mock import Mock

    # Mock de session
    mock_session = Mock()

    # Mock de servicios
    mock_disponibilidad = Mock(spec=DisponibilidadProfesorService)
    mock_asignacion = Mock(spec=AsignacionGuardiaService)

    # Configurar comportamiento
    mock_disponibilidad.esta_disponible.return_value = (True, None)
    mock_asignacion.puede_asignar_guardia.return_value = (True, None)

    # Usar mocks en el código
    profesor = Mock(spec=Profesor)
    profesor.id = 1
    profesor.activo = True

    disponible, _ = mock_disponibilidad.esta_disponible(
        profesor, date.today(), "mañana"
    )

    assert disponible is True

    # Test de caso negativo
    mock_disponibilidad.esta_disponible.return_value = (
        False,
        "Profesor ausente",
    )
    disponible, razon = mock_disponibilidad.esta_disponible(
        profesor, date.today(), "mañana"
    )

    assert disponible is False
    assert razon == "Profesor ausente"


if __name__ == "__main__":
    # Ejemplo de uso
    from database.database import SessionLocal

    session = SessionLocal()
    try:
        # Generar guardias usando servicios de dominio
        calendario, cuotas = generar_guardias_con_servicios_dominio(
            session, configuracion_id=1
        )
        session.commit()
        print(f"✅ {len(calendario)} guardias generadas")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()
