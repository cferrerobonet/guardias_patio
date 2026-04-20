"""
Compatibilidad retroactiva para cache_service.

La implementación se movió a application/use_cases/configuracion/cache_service.py
como parte de ORG-01 (organización de código). Este módulo mantiene la API
estable para imports legacy.
"""

from application.use_cases.configuracion.cache_service import (
    cache_configuracion,
    cache_profesores_activos,
    cache_zonas_activas,
    invalidar_cache,
    invalidar_configuracion,
    invalidar_profesores,
    invalidar_zonas,
)

__all__ = [
    "cache_configuracion",
    "cache_zonas_activas",
    "cache_profesores_activos",
    "invalidar_cache",
    "invalidar_configuracion",
    "invalidar_zonas",
    "invalidar_profesores",
]
