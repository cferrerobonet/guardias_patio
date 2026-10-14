"""
Business Metrics — Métricas de negocio estructuradas.

Funciones tipadas para registrar eventos de negocio clave con logs
estructurados. Permiten filtrar por `event_type="business"` en los logs.
"""

from datetime import date
from typing import Optional

from core.logging import get_logger

_logger = get_logger("business.metrics")


def profesor_creado(profesor_id: int, nombre: str, turno: str, horas_contrato: float) -> None:
    """Registra la creación de un nuevo profesor."""
    _logger.info(
        "business.profesor_creado",
        event_type="business",
        event="profesor_creado",
        profesor_id=profesor_id,
        nombre=nombre,
        turno=turno,
        horas_contrato=horas_contrato,
    )


def profesor_eliminado(profesor_id: int, nombre: str) -> None:
    """Registra la eliminación de un profesor."""
    _logger.info(
        "business.profesor_eliminado",
        event_type="business",
        event="profesor_eliminado",
        profesor_id=profesor_id,
        nombre=nombre,
    )


def guardia_asignada(
    guardia_id: int,
    profesor_id: int,
    zona_id: int,
    fecha: date,
    turno: str,
    es_sustitucion: bool = False,
) -> None:
    """Registra la asignación de una guardia."""
    _logger.info(
        "business.guardia_asignada",
        event_type="business",
        event="guardia_asignada",
        guardia_id=guardia_id,
        profesor_id=profesor_id,
        zona_id=zona_id,
        fecha=str(fecha),
        turno=turno,
        es_sustitucion=es_sustitucion,
    )


def guardias_limpiadas(total: int, curso_id: Optional[int] = None) -> None:
    """Registra la limpieza masiva de guardias."""
    _logger.warning(
        "business.guardias_limpiadas",
        event_type="business",
        event="guardias_limpiadas",
        total_eliminadas=total,
        curso_id=curso_id,
    )


def ausencia_registrada(
    ausencia_id: int,
    profesor_id: int,
    tipo: str,
    fecha_inicio: date,
    fecha_fin: Optional[date] = None,
) -> None:
    """Registra el registro de una ausencia."""
    _logger.info(
        "business.ausencia_registrada",
        event_type="business",
        event="ausencia_registrada",
        ausencia_id=ausencia_id,
        profesor_id=profesor_id,
        tipo=tipo,
        fecha_inicio=str(fecha_inicio),
        fecha_fin=str(fecha_fin) if fecha_fin else None,
    )


def sustitucion_confirmada(
    guardia_id: int,
    profesor_original_id: int,
    profesor_sustituto_id: int,
    fecha: date,
) -> None:
    """Registra la confirmación de una sustitución."""
    _logger.info(
        "business.sustitucion_confirmada",
        event_type="business",
        event="sustitucion_confirmada",
        guardia_id=guardia_id,
        profesor_original_id=profesor_original_id,
        profesor_sustituto_id=profesor_sustituto_id,
        fecha=str(fecha),
    )


def asignacion_cpsat_completada(
    total_guardias: int,
    asignadas: int,
    duracion_ms: float,
    curso_id: Optional[int] = None,
) -> None:
    """Registra la finalización del algoritmo CP-SAT."""
    cobertura = round(asignadas / total_guardias * 100, 1) if total_guardias > 0 else 0.0
    nivel = "info" if cobertura >= 80 else "warning"
    log_fn = getattr(_logger, nivel)
    log_fn(
        "business.asignacion_cpsat_completada",
        event_type="business",
        event="asignacion_cpsat_completada",
        total_guardias=total_guardias,
        asignadas=asignadas,
        cobertura_pct=cobertura,
        duracion_ms=duracion_ms,
        curso_id=curso_id,
    )


def login_exitoso(username: str) -> None:
    """Registra un inicio de sesión exitoso."""
    _logger.info(
        "business.login_exitoso",
        event_type="business",
        event="login_exitoso",
        username=username,
    )


def login_fallido(username: str, razon: str) -> None:
    """Registra un intento de login fallido."""
    _logger.warning(
        "business.login_fallido",
        event_type="business",
        event="login_fallido",
        username=username,
        razon=razon,
    )
