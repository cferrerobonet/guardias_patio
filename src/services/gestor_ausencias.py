"""
Servicio para gestionar ausencias de profesores.
Permite registrar, editar y eliminar ausencias, así como encontrar y reasignar guardias afectadas.
"""

import json
from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import joinedload

from infrastructure.database.models import Ausencia, Guardia, GuardiaAuditLog, Profesor
from services.validators import AusenciaChecker, TurnoValidator
from utils import get_logger

logger = get_logger(__name__)

# Instancia del validador de turnos
_turno_validator = TurnoValidator()


def registrar_ausencia(
    session,
    profesor_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    tipo: str,
    motivo: Optional[str] = None,
    documento_path: Optional[str] = None,
) -> Ausencia:
    """
    Registra una nueva ausencia para un profesor.

    Args:
        session: Sesión de SQLAlchemy
        profesor_id: ID del profesor
        fecha_inicio: Fecha de inicio de la ausencia
        fecha_fin: Fecha de fin de la ausencia
        tipo: Tipo de ausencia (baja_medica, permiso, vacaciones, otros)
        motivo: Motivo de la ausencia (opcional)
        documento_path: Ruta al justificante (opcional)

    Returns:
        Objeto Ausencia creado

    Raises:
        ValueError: Si las fechas son inválidas o el profesor no existe
    """
    # Validaciones
    if fecha_fin < fecha_inicio:
        raise ValueError("La fecha de fin debe ser posterior o igual a la fecha de inicio")

    profesor = session.query(Profesor).get(profesor_id)
    if not profesor:
        raise ValueError(f"No existe el profesor con ID {profesor_id}")

    if tipo not in ["baja_medica", "permiso", "vacaciones", "otros"]:
        logger.warning(f"Tipo de ausencia no estándar: {tipo}")

    # Crear ausencia
    ausencia = Ausencia(
        profesor_id=profesor_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipo=tipo,
        motivo=motivo,
        documento_path=documento_path,
        activa=True,
    )

    session.add(ausencia)
    session.commit()

    logger.info(
        f"Ausencia registrada: {profesor.nombre_completo} "
        f"del {fecha_inicio} al {fecha_fin} ({tipo})"
    )

    return ausencia


def editar_ausencia(
    session,
    ausencia_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    tipo: Optional[str] = None,
    motivo: Optional[str] = None,
    documento_path: Optional[str] = None,
    activa: Optional[bool] = None,
) -> Ausencia:
    """
    Edita una ausencia existente.

    Args:
        session: Sesión de SQLAlchemy
        ausencia_id: ID de la ausencia a editar
        fecha_inicio: Nueva fecha de inicio (opcional)
        fecha_fin: Nueva fecha de fin (opcional)
        tipo: Nuevo tipo (opcional)
        motivo: Nuevo motivo (opcional)
        documento_path: Nueva ruta al documento (opcional)
        activa: Nuevo estado activo/inactivo (opcional)

    Returns:
        Objeto Ausencia actualizado

    Raises:
        ValueError: Si la ausencia no existe o las fechas son inválidas
    """
    ausencia = session.query(Ausencia).get(ausencia_id)
    if not ausencia:
        raise ValueError(f"No existe la ausencia con ID {ausencia_id}")

    # Actualizar campos si se proporcionan
    if fecha_inicio is not None:
        ausencia.fecha_inicio = fecha_inicio
    if fecha_fin is not None:
        ausencia.fecha_fin = fecha_fin
    if tipo is not None:
        ausencia.tipo = tipo
    if motivo is not None:
        ausencia.motivo = motivo
    if documento_path is not None:
        ausencia.documento_path = documento_path
    if activa is not None:
        ausencia.activa = activa

    # Validar fechas
    if ausencia.fecha_fin < ausencia.fecha_inicio:
        raise ValueError("La fecha de fin debe ser posterior o igual a la fecha de inicio")

    session.commit()
    logger.info(f"Ausencia {ausencia_id} actualizada")

    return ausencia


def eliminar_ausencia(session, ausencia_id: int) -> None:
    """
    Elimina una ausencia de la base de datos.

    Args:
        session: Sesión de SQLAlchemy
        ausencia_id: ID de la ausencia a eliminar

    Raises:
        ValueError: Si la ausencia no existe
    """
    ausencia = session.query(Ausencia).get(ausencia_id)
    if not ausencia:
        raise ValueError(f"No existe la ausencia con ID {ausencia_id}")

    profesor_nombre = ausencia.profesor.nombre_completo
    session.delete(ausencia)
    session.commit()

    logger.info(f"Ausencia {ausencia_id} eliminada (Profesor: {profesor_nombre})")


def desactivar_ausencia(session, ausencia_id: int) -> Ausencia:
    """
    Desactiva una ausencia sin eliminarla (para mantener historial).

    Args:
        session: Sesión de SQLAlchemy
        ausencia_id: ID de la ausencia a desactivar

    Returns:
        Objeto Ausencia desactivado

    Raises:
        ValueError: Si la ausencia no existe
    """
    ausencia = session.query(Ausencia).get(ausencia_id)
    if not ausencia:
        raise ValueError(f"No existe la ausencia con ID {ausencia_id}")

    ausencia.activa = False
    session.commit()

    logger.info(f"Ausencia {ausencia_id} desactivada")
    return ausencia


def reactivar_ausencia(session, ausencia_id: int) -> Ausencia:
    ausencia = session.query(Ausencia).get(ausencia_id)
    if not ausencia:
        raise ValueError(f"No existe la ausencia con ID {ausencia_id}")

    ausencia.activa = True
    session.commit()

    logger.info(f"Ausencia {ausencia_id} reactivada")
    return ausencia


def obtener_guardias_afectadas(
    session,
    ausencia_id: int,
) -> List[Guardia]:
    """
    Obtiene todas las guardias asignadas a un profesor durante su ausencia.

    Args:
        session: Sesión de SQLAlchemy
        ausencia_id: ID de la ausencia

    Returns:
        Lista de guardias afectadas por la ausencia

    Raises:
        ValueError: Si la ausencia no existe
    """
    ausencia = session.query(Ausencia).get(ausencia_id)
    if not ausencia:
        raise ValueError(f"No existe la ausencia con ID {ausencia_id}")

    # Buscar guardias del profesor en el rango de fechas
    guardias = (
        session.query(Guardia)
        .options(joinedload(Guardia.zona), joinedload(Guardia.profesor))
        .filter(
            Guardia.profesor_id == ausencia.profesor_id,
            Guardia.fecha >= ausencia.fecha_inicio,
            Guardia.fecha <= ausencia.fecha_fin,
        )
        .all()
    )

    logger.info(
        f"Guardias afectadas por ausencia {ausencia_id}: {len(guardias)} guardias encontradas"
    )

    return guardias


def obtener_guardias_afectadas_por_periodo(
    session,
    profesor_id: int,
    fecha_inicio: date,
    fecha_fin: date,
) -> List[Guardia]:
    """
    Obtiene guardias de un profesor en un periodo específico.
    Útil para previsualizar guardias afectadas antes de crear la ausencia.

    Args:
        session: Sesión de SQLAlchemy
        profesor_id: ID del profesor
        fecha_inicio: Fecha de inicio del periodo
        fecha_fin: Fecha de fin del periodo

    Returns:
        Lista de guardias en el periodo especificado
    """
    guardias = (
        session.query(Guardia)
        .options(joinedload(Guardia.zona), joinedload(Guardia.profesor))
        .filter(
            Guardia.profesor_id == profesor_id,
            Guardia.fecha >= fecha_inicio,
            Guardia.fecha <= fecha_fin,
        )
        .all()
    )

    return guardias


def obtener_profesores_disponibles(
    session,
    fecha: date,
    turno: str,
    recreo_id: int,
    excluir_profesor_id: Optional[int] = None,
) -> List[Tuple[Profesor, int]]:
    """
    Obtiene lista de profesores disponibles para una guardia específica.

    Args:
        session: Sesión de SQLAlchemy
        fecha: Fecha de la guardia
        turno: Turno de la guardia (mañana/tarde)
        recreo_id: ID del recreo
        excluir_profesor_id: ID del profesor a excluir (opcional)

    Returns:
        Lista de tuplas (Profesor, guardias_asignadas_hoy)
        Ordenada por menor carga actual
    """
    profesores = session.query(Profesor).options(joinedload(Profesor.zona_preferida)).all()

    # Crear checker de ausencias
    checker = AusenciaChecker(session)

    disponibles = []
    for p in profesores:
        # Excluir profesor específico si se indica
        if excluir_profesor_id and p.id == excluir_profesor_id:
            continue

        # Verificar turno compatible usando el validador centralizado
        if _turno_validator.es_compatible(p.turno, turno):
            # Verificar que no esté ausente
            if not checker.profesor_ausente(p.id, fecha):
                # Contar guardias ya asignadas ese día
                guardias_dia = (
                    session.query(Guardia)
                    .filter(
                        Guardia.profesor_id == p.id,
                        Guardia.fecha == fecha,
                    )
                    .count()
                )

                # Si ya tiene guardia ese día, no está disponible
                if guardias_dia == 0:
                    disponibles.append((p, guardias_dia))

    # Pre-calcular sustituciones acumuladas para ordenar por equidad
    sust_acumuladas: dict[int, int] = {}
    for p, _ in disponibles:
        sust_acumuladas[p.id] = (
            session.query(Guardia)
            .filter(Guardia.profesor_id == p.id, Guardia.es_sustitucion == True)  # noqa: E712
            .count()
        )

    # Ordenar por (guardias hoy, sustituciones acumuladas) — menor carga primero
    disponibles.sort(key=lambda x: (x[1], sust_acumuladas.get(x[0].id, 0)))

    return disponibles


def reasignar_guardia(
    session,
    guardia_id: int,
    nuevo_profesor_id: int,
) -> Guardia:
    """
    Reasigna una guardia a un nuevo profesor.

    Args:
        session: Sesión de SQLAlchemy
        guardia_id: ID de la guardia a reasignar
        nuevo_profesor_id: ID del nuevo profesor

    Returns:
        Guardia actualizada

    Raises:
        ValueError: Si la guardia o el profesor no existen,
            o si el nuevo profesor no está disponible
    """
    guardia = session.query(Guardia).get(guardia_id)
    if not guardia:
        raise ValueError(f"No existe la guardia con ID {guardia_id}")

    nuevo_profesor = session.query(Profesor).get(nuevo_profesor_id)
    if not nuevo_profesor:
        raise ValueError(f"No existe el profesor con ID {nuevo_profesor_id}")

    # Crear checker de ausencias
    checker = AusenciaChecker(session)

    # Validar disponibilidad
    if checker.profesor_ausente(nuevo_profesor_id, guardia.fecha):
        raise ValueError(
            f"El profesor {nuevo_profesor.nombre_completo} está ausente el {guardia.fecha}"
        )

    # Validar que no tenga ya una guardia ese día
    guardias_dia = (
        session.query(Guardia)
        .filter(
            Guardia.profesor_id == nuevo_profesor_id,
            Guardia.fecha == guardia.fecha,
        )
        .count()
    )

    if guardias_dia > 0:
        raise ValueError(
            f"El profesor {nuevo_profesor.nombre_completo} ya tiene una guardia el {guardia.fecha}"
        )

    # Reasignar
    profesor_anterior_id = guardia.profesor_id
    profesor_anterior = guardia.profesor.nombre_completo
    guardia.es_sustitucion = True
    guardia.profesor_sustituido_id = profesor_anterior_id
    guardia.profesor_id = nuevo_profesor_id
    session.add(
        GuardiaAuditLog(
            guardia_id=guardia_id,
            accion="SUSTITUIDA",
            profesor_id=nuevo_profesor_id,
            detalle=json.dumps({"profesor_anterior": str(profesor_anterior), "origen": "ausencia"}),
        )
    )
    session.commit()

    logger.info(
        f"Guardia {guardia_id} reasignada: {profesor_anterior} → {nuevo_profesor.nombre_completo}"
    )

    return guardia


def reasignar_guardias_automaticamente(
    session,
    guardias: List[Guardia],
) -> Dict[str, any]:
    """
    Reasigna automáticamente una lista de guardias a profesores disponibles.

    Args:
        session: Sesión de SQLAlchemy
        guardias: Lista de guardias a reasignar

    Returns:
        Diccionario con resultados:
        {
            "reasignadas": int,  # Número de guardias reasignadas con éxito
            "fallidas": int,  # Número de guardias que no se pudieron reasignar
            "detalles": List[Dict]  # Detalles de cada reasignación
        }
    """
    resultados = {
        "reasignadas": 0,
        "fallidas": 0,
        "detalles": [],
    }

    for guardia in guardias:
        try:
            # Buscar profesores disponibles
            disponibles = obtener_profesores_disponibles(
                session,
                guardia.fecha,
                guardia.turno,
                guardia.recreo,
                excluir_profesor_id=guardia.profesor_id,
            )

            if not disponibles:
                logger.warning(
                    f"No hay profesores disponibles para guardia {guardia.id} "
                    f"({guardia.fecha}, {guardia.turno}, recreo {guardia.recreo})"
                )
                resultados["fallidas"] += 1
                resultados["detalles"].append(
                    {
                        "guardia_id": guardia.id,
                        "fecha": guardia.fecha,
                        "turno": guardia.turno,
                        "recreo": guardia.recreo,
                        "zona": guardia.zona.nombre_zona if guardia.zona else "N/A",
                        "estado": "fallida",
                        "razon": "No hay profesores disponibles",
                    }
                )
                continue

            # Asignar al primero disponible (menor carga)
            nuevo_profesor, _ = disponibles[0]
            profesor_anterior = guardia.profesor.nombre_completo

            guardia.profesor_id = nuevo_profesor.id
            resultados["reasignadas"] += 1
            resultados["detalles"].append(
                {
                    "guardia_id": guardia.id,
                    "fecha": guardia.fecha,
                    "turno": guardia.turno,
                    "recreo": guardia.recreo,
                    "zona": guardia.zona.nombre_zona if guardia.zona else "N/A",
                    "estado": "reasignada",
                    "profesor_anterior": profesor_anterior,
                    "profesor_nuevo": nuevo_profesor.nombre_completo,
                }
            )

            logger.info(
                f"Guardia {guardia.id} reasignada automáticamente: "
                f"{profesor_anterior} → {nuevo_profesor.nombre_completo}"
            )

        except (ValueError, LookupError, AttributeError) as e:
            logger.error(f"Error al reasignar guardia {guardia.id}: {str(e)}")
            resultados["fallidas"] += 1
            resultados["detalles"].append(
                {
                    "guardia_id": guardia.id,
                    "fecha": guardia.fecha,
                    "estado": "fallida",
                    "razon": str(e),
                }
            )

    # Commit solo si todas fueron exitosas o si queremos commit parcial
    if resultados["fallidas"] == 0:
        session.commit()
        logger.info(
            f"Reasignación automática completada: {resultados['reasignadas']} guardias reasignadas"
        )
    else:
        logger.warning(
            f"Reasignación parcial: {resultados['reasignadas']} exitosas, "
            f"{resultados['fallidas']} fallidas"
        )
        # Hacer commit parcial si hay al menos una exitosa
        if resultados["reasignadas"] > 0:
            session.commit()

    return resultados


class GestorAusencias:
    """Facade estática para mantener un punto de entrada único del servicio."""

    registrar_ausencia = staticmethod(registrar_ausencia)
    editar_ausencia = staticmethod(editar_ausencia)
    eliminar_ausencia = staticmethod(eliminar_ausencia)
    desactivar_ausencia = staticmethod(desactivar_ausencia)
    reactivar_ausencia = staticmethod(reactivar_ausencia)
    obtener_guardias_afectadas = staticmethod(obtener_guardias_afectadas)
    obtener_guardias_afectadas_por_periodo = staticmethod(obtener_guardias_afectadas_por_periodo)
    obtener_profesores_disponibles = staticmethod(obtener_profesores_disponibles)
    reasignar_guardia = staticmethod(reasignar_guardia)
    reasignar_guardias_automaticamente = staticmethod(reasignar_guardias_automaticamente)
