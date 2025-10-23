"""
Sistema de caching específico para repositories.
Optimiza consultas frecuentes con invalidación automática.
"""

from functools import wraps
from typing import Callable

from utils.cache import cache_query, invalidate_cache
from utils.logger import get_logger

logger = get_logger(__name__)


def cache_repository_query(ttl: int = 300, cache_key_prefix: str = ""):
    """
    Decorador para cachear queries de repositories con TTL configurable.
    
    Args:
        ttl: Tiempo de vida del cache en segundos (default: 5 min)
        cache_key_prefix: Prefijo opcional para la clave de cache
    
    Ejemplo:
        @cache_repository_query(ttl=600, cache_key_prefix="config")
        def obtener_configuracion(self):
            return self.session.query(Configuracion).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Aplicar cache_query subyacente
            cached_func = cache_query(ttl=ttl)(func)
            return cached_func(*args, **kwargs)
        return wrapper
    return decorator


def invalidate_repository_cache(pattern: str):
    """
    Invalida cache de repository por patrón.
    
    Args:
        pattern: Patrón regex para invalidar claves de cache
    
    Ejemplo:
        invalidate_repository_cache("configuracion")
        invalidate_repository_cache("zona.*")
    """
    count = invalidate_cache(pattern)
    logger.info(
        "Cache invalidado para repository",
        pattern=pattern,
        entries_invalidated=count
    )
    return count


def cache_configuracion(ttl: int = 600):
    """
    Decorador especializado para cachear configuración (10 min).
    La configuración cambia raramente, merece TTL largo.
    """
    return cache_repository_query(ttl=ttl, cache_key_prefix="config")


def cache_zonas(ttl: int = 300):
    """
    Decorador especializado para cachear zonas (5 min).
    Las zonas cambian ocasionalmente.
    """
    return cache_repository_query(ttl=ttl, cache_key_prefix="zona")


def invalidate_configuracion_cache():
    """Invalida todo el cache relacionado con configuración."""
    return invalidate_repository_cache(".*configuracion.*")


def invalidate_zonas_cache():
    """Invalida todo el cache relacionado con zonas."""
    return invalidate_repository_cache(".*zona.*")
