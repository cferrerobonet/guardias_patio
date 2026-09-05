"""
Sistema de caching específico para repositories.
Optimiza consultas frecuentes con invalidación automática.

⚠️ IMPORTANTE - DECISIÓN DE ARQUITECTURA:
Este archivo NO es código duplicado de cache.py. Es un WRAPPER especializado
que proporciona decoradores y utilidades específicas para repositories.

Relación con cache.py:
- cache.py: Sistema genérico de caché (LRU, TTL, métricas)
- repository_cache.py: Decoradores especializados para repositories
  * Usa cache.py internamente
  * Añade convenientes por dominio (cache_configuracion, cache_zonas)
  * Facilita invalidación por patrones de negocio

Razón de mantener ambos:
- Separación de responsabilidades (genérico vs especializado)
- cache.py es reutilizable en otros contextos
- repository_cache.py simplifica el uso en la capa de datos
- Patrones DDD: el repository no debe conocer detalles de caché

Uso:
    # En repositories
    from utils.repository_cache import cache_configuracion

    @cache_configuracion(ttl=600)
    def obtener_configuracion(self):
        return self.session.query(Configuracion).first()
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
        cached_func = cache_query(ttl=ttl, prefijo=cache_key_prefix)(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
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
    count = invalidate_cache(pattern, use_regex=True)
    logger.info(
        f"Cache invalidado para repository - pattern: {pattern}, entries_invalidated: {count}"
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


def cache_profesores(ttl: int = 180):
    """
    Decorador especializado para cachear profesores (3 min).
    Los profesores cambian con cierta frecuencia.
    """
    return cache_repository_query(ttl=ttl, cache_key_prefix="profesor")


def invalidate_configuracion_cache():
    """Invalida todo el cache relacionado con configuración."""
    return invalidate_repository_cache(".*configuracion.*")


def invalidate_zonas_cache():
    """Invalida todo el cache relacionado con zonas."""
    return invalidate_repository_cache(".*zona.*")


def invalidate_profesores_cache():
    """Invalida todo el cache relacionado con profesores."""
    return invalidate_repository_cache(".*profesor.*")
