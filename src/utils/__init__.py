"""
Módulo de utilidades para la aplicación de Guardias de Patio.
Contiene helpers, validadores, constantes y funciones comunes.
"""

# Logging
# Constantes
from . import constants

# Excepciones
from .exceptions import (
    ConfiguracionError,
    DatabaseError,
    DuplicateGuardiaError,
    ExportError,
    GuardiaConflictError,
    GuardiasBaseException,
    ImportError,
    InsufficientProfesoresError,
    MaxGuardiasExceededError,
    ProfesorNotFoundError,
    ValidationError,
    ZonaNotFoundError,
)
from .logger import get_logger, log_function_call, setup_logging

# Validadores
from .validators import (
    validar_dias_semana,
    validar_email,
    validar_fecha,
    validar_horas_contrato,
    validar_nombre_completo,
    validar_rango_fechas,
    validar_turno,
)

__all__ = [
    # Logging
    "get_logger",
    "setup_logging",
    "log_function_call",
    # Validadores
    "validar_email",
    "validar_fecha",
    "validar_nombre_completo",
    "validar_rango_fechas",
    "validar_horas_contrato",
    "validar_turno",
    "validar_dias_semana",
    # Constantes
    "constants",
    # Excepciones
    "GuardiasBaseException",
    "ValidationError",
    "DatabaseError",
    "ConfiguracionError",
    "ProfesorNotFoundError",
    "ZonaNotFoundError",
    "GuardiaConflictError",
    "MaxGuardiasExceededError",
    "DuplicateGuardiaError",
    "InsufficientProfesoresError",
    "ExportError",
    "ImportError",
]
