"""
Módulo de utilidades para la aplicación de Guardias de Patio.
Contiene helpers, validadores, constantes y funciones comunes.
"""

# Constantes
# Excepciones (ahora desde core)
from core.exceptions import (
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

from . import constants

# Caché
from .cache import (
    cache_long,
    cache_medium,
    cache_query,
    cache_short,
    clear_all_cache,
    get_cache_stats,
    invalidate_cache,
    print_cache_stats,
    reset_cache_stats,
)

# Logging
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
    # Caché
    "cache_query",
    "cache_short",
    "cache_medium",
    "cache_long",
    "invalidate_cache",
    "clear_all_cache",
    "get_cache_stats",
    "print_cache_stats",
    "reset_cache_stats",
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
