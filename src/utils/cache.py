"""
Sistema de caché para optimizar consultas frecuentes a la base de datos.

Este módulo proporciona decoradores y utilidades para cachear resultados
de consultas costosas, reduciendo el tiempo de respuesta y la carga en la BD.

Ejemplo de uso:
    from src.utils.cache import cache_query, invalidate_cache, clear_all_cache

    @cache_query(ttl=300)  # Cachea por 5 minutos
    def obtener_profesores_activos(session):
        return session.query(Profesor).filter_by(activo=True).all()

    # Invalidar caché cuando hay cambios
    invalidate_cache('obtener_profesores_activos')
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Almacén global de caché
# Estructura: {cache_key: (resultado, timestamp, ttl)}
_cache_store: Dict[str, Tuple[Any, float, float]] = {}

# Estadísticas de caché
_cache_stats = {
    'hits': 0,
    'misses': 0,
    'invalidations': 0
}


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """
    Genera una clave única para el caché basada en la función y sus argumentos.

    Args:
        func: Función a cachear
        args: Argumentos posicionales
        kwargs: Argumentos nombrados

    Returns:
        Clave única para el caché
    """
    # Nombre de la función
    func_name = f"{func.__module__}.{func.__name__}"

    # Convertir argumentos a string (excluyendo objetos de sesión)
    args_str = ','.join(
        str(arg) for arg in args
        if not hasattr(arg, 'query')  # Excluir sesiones SQLAlchemy
    )
    kwargs_str = ','.join(
        f"{k}={v}" for k, v in sorted(kwargs.items())
        if not hasattr(v, 'query')  # Excluir sesiones SQLAlchemy
    )

    cache_key = f"{func_name}({args_str},{kwargs_str})"
    return cache_key


def cache_query(ttl: float = 300, key_func: Optional[Callable] = None):
    """
    Decorador para cachear resultados de consultas a la base de datos.

    Args:
        ttl: Tiempo de vida del caché en segundos (default: 300 = 5 minutos)
        key_func: Función opcional para generar la clave de caché personalizada

    Returns:
        Decorador que cachea la función

    Example:
        @cache_query(ttl=600)  # Cachea por 10 minutos
        def obtener_zonas_activas(session):
            return session.query(Zona).filter_by(activa=True).all()

        # Primera llamada: consulta BD y cachea
        zonas = obtener_zonas_activas(session)  # MISS

        # Segunda llamada (dentro de 10 min): retorna desde caché
        zonas = obtener_zonas_activas(session)  # HIT
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func, args, kwargs)

            # Verificar si existe en caché y no ha expirado
            if cache_key in _cache_store:
                cached_result, timestamp, cached_ttl = _cache_store[cache_key]
                elapsed = time.time() - timestamp

                if elapsed < cached_ttl:
                    # Cache HIT
                    _cache_stats['hits'] += 1
                    logger.debug(
                        f"Cache HIT: {func.__name__} "
                        f"(age: {elapsed:.1f}s, ttl: {cached_ttl}s)"
                    )
                    return cached_result
                else:
                    # Caché expirado
                    logger.debug(f"Cache EXPIRED: {func.__name__} (age: {elapsed:.1f}s)")
                    del _cache_store[cache_key]

            # Cache MISS: ejecutar función
            _cache_stats['misses'] += 1
            logger.debug(f"Cache MISS: {func.__name__}")

            result = func(*args, **kwargs)

            # Guardar en caché
            _cache_store[cache_key] = (result, time.time(), ttl)
            logger.debug(f"Cache STORED: {func.__name__} (ttl: {ttl}s)")

            return result

        # Agregar método para invalidar caché de esta función
        wrapper.invalidate_cache = lambda: invalidate_cache(func.__name__)

        return wrapper

    return decorator


def invalidate_cache(pattern: str = None):
    """
    Invalida entradas de caché que coincidan con el patrón.

    Args:
        pattern: Patrón para filtrar claves de caché.
                 Si es None, invalida todo el caché.

    Example:
        # Invalidar todas las entradas de una función específica
        invalidate_cache('obtener_profesores_activos')

        # Invalidar todas las entradas relacionadas con profesores
        invalidate_cache('profesor')

        # Invalidar todo el caché
        invalidate_cache()
    """
    if pattern is None:
        # Invalidar todo
        count = len(_cache_store)
        _cache_store.clear()
        _cache_stats['invalidations'] += count
        logger.info(f"Cache invalidado completamente ({count} entradas)")
        return count

    # Invalidar entradas que coincidan con el patrón
    keys_to_delete = [
        key for key in _cache_store.keys()
        if pattern.lower() in key.lower()
    ]

    for key in keys_to_delete:
        del _cache_store[key]

    count = len(keys_to_delete)
    _cache_stats['invalidations'] += count

    if count > 0:
        logger.info(f"Cache invalidado: {count} entradas con patrón '{pattern}'")
    else:
        logger.debug(f"Cache: no se encontraron entradas con patrón '{pattern}'")

    return count


def clear_all_cache():
    """
    Limpia completamente el caché y las estadísticas.

    Útil al inicio de la aplicación o después de operaciones masivas.

    Example:
        # Al inicio de la aplicación
        clear_all_cache()

        # Después de importar datos
        importar_datos(archivo)
        clear_all_cache()
    """
    count = len(_cache_store)
    _cache_store.clear()
    _cache_stats['invalidations'] += count

    logger.info(f"Cache limpiado completamente ({count} entradas)")


def get_cache_stats() -> dict:
    """
    Obtiene estadísticas del sistema de caché.

    Returns:
        Diccionario con estadísticas:
        - hits: Número de cache hits
        - misses: Número de cache misses
        - invalidations: Número de invalidaciones
        - size: Número de entradas en caché
        - hit_rate: Porcentaje de aciertos

    Example:
        stats = get_cache_stats()
        print(f"Hit rate: {stats['hit_rate']:.1f}%")
        print(f"Cache size: {stats['size']} entries")
    """
    total_requests = _cache_stats['hits'] + _cache_stats['misses']
    hit_rate = (_cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

    return {
        'hits': _cache_stats['hits'],
        'misses': _cache_stats['misses'],
        'invalidations': _cache_stats['invalidations'],
        'size': len(_cache_store),
        'hit_rate': hit_rate,
        'total_requests': total_requests
    }


def print_cache_stats():
    """
    Imprime estadísticas del caché en formato legible.

    Útil para debugging y análisis de rendimiento.

    Example:
        print_cache_stats()
        # Output:
        # ========== Cache Statistics ==========
        # Hits:           150 (75.0%)
        # Misses:          50 (25.0%)
        # Invalidations:   10
        # Cache size:      25 entries
        # ======================================
    """
    stats = get_cache_stats()

    print("=" * 40)
    print("Cache Statistics".center(40))
    print("=" * 40)
    print(f"Hits:           {stats['hits']:4d} ({stats['hit_rate']:.1f}%)")
    print(f"Misses:         {stats['misses']:4d}")
    print(f"Invalidations:  {stats['invalidations']:4d}")
    print(f"Cache size:     {stats['size']:4d} entries")
    print("=" * 40)


def reset_cache_stats():
    """
    Reinicia las estadísticas del caché (sin limpiar el caché).

    Útil para medir rendimiento en períodos específicos.

    Example:
        reset_cache_stats()
        # ... ejecutar operaciones ...
        stats = get_cache_stats()
        print(f"Hit rate en esta sesión: {stats['hit_rate']:.1f}%")
    """
    _cache_stats['hits'] = 0
    _cache_stats['misses'] = 0
    _cache_stats['invalidations'] = 0

    logger.info("Estadísticas de caché reiniciadas")


# Decorador conveniente para TTL corto (1 minuto)
def cache_short(func: Callable) -> Callable:
    """
    Decorador conveniente para caché de corta duración (60 segundos).

    Útil para datos que cambian frecuentemente pero necesitan optimización.

    Example:
        @cache_short
        def obtener_guardias_hoy(session, fecha):
            return session.query(Guardia).filter_by(fecha=fecha).all()
    """
    return cache_query(ttl=60)(func)


# Decorador conveniente para TTL medio (5 minutos)
def cache_medium(func: Callable) -> Callable:
    """
    Decorador conveniente para caché de duración media (300 segundos).

    Útil para datos que cambian ocasionalmente (default recomendado).

    Example:
        @cache_medium
        def obtener_profesores_activos(session):
            return session.query(Profesor).filter_by(activo=True).all()
    """
    return cache_query(ttl=300)(func)


# Decorador conveniente para TTL largo (30 minutos)
def cache_long(func: Callable) -> Callable:
    """
    Decorador conveniente para caché de larga duración (1800 segundos).

    Útil para datos que raramente cambian (configuración, zonas).

    Example:
        @cache_long
        def obtener_configuracion_curso(session):
            return session.query(Configuracion).first()
    """
    return cache_query(ttl=1800)(func)
