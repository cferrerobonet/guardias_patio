"""
Sistema de caché avanzado para optimizar consultas frecuentes a la base de datos.

Este módulo proporciona decoradores y utilidades para cachear resultados
de consultas costosas, con soporte para TTL, invalidación selectiva, métricas
detalladas y límite de capacidad (LRU eviction).

Características:
- TTL (Time To Live) configurable por entrada
- Invalidación selectiva por patrón o regex
- Métricas detalladas por función
- Límite de capacidad con evicción LRU
- Estadísticas de hit/miss rate

Ejemplo de uso:
    from src.utils.cache import cache_query, invalidate_cache, clear_all_cache

    @cache_query(ttl=300)  # Cachea por 5 minutos
    def obtener_profesores_activos(session):
        return session.query(Profesor).filter_by(activo=True).all()

    # Invalidar caché cuando hay cambios
    invalidate_cache('obtener_profesores_activos')
"""

import re
import threading
import time
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

# Configuración del caché
MAX_CACHE_SIZE = 1000  # Máximo número de entradas (LRU eviction)

# Almacén global de caché con orden de acceso (LRU)
# Estructura: {cache_key: (resultado, timestamp, ttl, access_count)}
_cache_store: OrderedDict[str, Tuple[Any, float, float, int]] = OrderedDict()

# Estadísticas globales de caché
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "invalidations": 0,
    "evictions": 0,  # Entradas eliminadas por límite de capacidad
}

# Métricas por función
_function_metrics: Dict[str, Dict[str, int]] = {}

# Lock para acceso thread-safe al cache
_cache_lock = threading.RLock()


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
    args_str = ",".join(
        str(arg)
        for arg in args
        if not hasattr(arg, "query")  # Excluir sesiones SQLAlchemy
    )
    kwargs_str = ",".join(
        f"{k}={v}"
        for k, v in sorted(kwargs.items())
        if not hasattr(v, "query")  # Excluir sesiones SQLAlchemy
    )

    cache_key = f"{func_name}({args_str},{kwargs_str})"
    return cache_key


def _evict_if_needed():
    """
    Elimina la entrada más antigua (LRU) si se alcanzó el límite de capacidad.
    """
    if len(_cache_store) >= MAX_CACHE_SIZE:
        # Eliminar la entrada más antigua (primera en OrderedDict)
        oldest_key = next(iter(_cache_store))
        del _cache_store[oldest_key]
        _cache_stats["evictions"] += 1
        logger.debug(f"Cache EVICTED: {oldest_key} (limite alcanzado)")


def _update_function_metrics(func_name: str, hit: bool):
    """
    Actualiza las métricas específicas de una función.

    Args:
        func_name: Nombre de la función
        hit: True si fue cache hit, False si fue miss
    """
    if func_name not in _function_metrics:
        _function_metrics[func_name] = {"hits": 0, "misses": 0, "total": 0}

    _function_metrics[func_name]["total"] += 1
    if hit:
        _function_metrics[func_name]["hits"] += 1
    else:
        _function_metrics[func_name]["misses"] += 1


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

            func_name = func.__name__

            # Verificar si existe en caché y no ha expirado
            with _cache_lock:
                if cache_key in _cache_store:
                    cached_result, timestamp, cached_ttl, access_count = _cache_store[cache_key]
                    elapsed = time.time() - timestamp

                    if elapsed < cached_ttl:
                        # Cache HIT - mover al final (más reciente)
                        _cache_store.move_to_end(cache_key)
                        # Incrementar contador de accesos
                        _cache_store[cache_key] = (
                            cached_result,
                            timestamp,
                            cached_ttl,
                            access_count + 1,
                        )

                        _cache_stats["hits"] += 1
                        _update_function_metrics(func_name, hit=True)

                        logger.debug(
                            f"Cache HIT: {func_name} "
                            f"(age: {elapsed:.1f}s, ttl: {cached_ttl}s, "
                            f"accesses: {access_count + 1})"
                        )
                        return cached_result
                    else:
                        # Caché expirado
                        logger.debug(f"Cache EXPIRED: {func_name} (age: {elapsed:.1f}s)")
                        del _cache_store[cache_key]

                # Cache MISS: actualizar estadísticas antes de soltar el lock
                _cache_stats["misses"] += 1
                _update_function_metrics(func_name, hit=False)

            logger.debug(f"Cache MISS: {func_name}")

            # Ejecutar la función fuera del lock para no bloquear otros hilos
            result = func(*args, **kwargs)

            with _cache_lock:
                # Verificar capacidad y evictar si es necesario
                _evict_if_needed()

                # Guardar en caché (se añade al final - más reciente)
                _cache_store[cache_key] = (result, time.time(), ttl, 1)

            logger.debug(
                f"Cache STORED: {func_name} (ttl: {ttl}s, "
                f"size: {len(_cache_store)}/{MAX_CACHE_SIZE})"
            )

            return result

        # Agregar método para invalidar caché de esta función
        wrapper.invalidate_cache = lambda: invalidate_cache(func.__name__)

        return wrapper

    return decorator


def invalidate_cache(pattern: str = None, use_regex: bool = False):
    """
    Invalida entradas de caché que coincidan con el patrón.

    Args:
        pattern: Patrón para filtrar claves de caché.
                 Si es None, invalida todo el caché.
        use_regex: Si True, interpreta el patrón como expresión regular.

    Returns:
        Número de entradas invalidadas

    Example:
        # Invalidar todas las entradas de una función específica
        invalidate_cache('obtener_profesores_activos')

        # Invalidar todas las entradas relacionadas con profesores
        invalidate_cache('profesor')

        # Invalidar con expresión regular
        invalidate_cache(r'obtener_.*_activos', use_regex=True)

        # Invalidar todo el caché
        invalidate_cache()
    """
    if pattern is None:
        # Invalidar todo
        with _cache_lock:
            count = len(_cache_store)
            _cache_store.clear()
            _cache_stats["invalidations"] += count
        logger.info(f"Cache invalidado completamente ({count} entradas)")
        return count

    # Compilar regex si es necesario
    if use_regex:
        try:
            regex_pattern = re.compile(pattern, re.IGNORECASE)

            def regex_matcher(key: str) -> bool:
                return regex_pattern.search(key) is not None

            matcher = regex_matcher
        except re.error as e:
            logger.error(f"Patrón regex inválido '{pattern}': {e}")
            return 0
    else:
        # Búsqueda simple por substring
        def substring_matcher(key: str) -> bool:
            return pattern.lower() in key.lower()

        matcher = substring_matcher

    # Invalidar entradas que coincidan
    with _cache_lock:
        keys_to_delete = [key for key in _cache_store.keys() if matcher(key)]
        for key in keys_to_delete:
            del _cache_store[key]
        count = len(keys_to_delete)
        _cache_stats["invalidations"] += count

    if count > 0:
        pattern_type = "regex" if use_regex else "patrón"
        logger.info(f"Cache invalidado: {count} entradas con {pattern_type} '{pattern}'")
    else:
        logger.debug(f"Cache: no se encontraron entradas con patrón '{pattern}'")

    return count


def invalidate_by_function(func_name: str) -> int:
    """
    Invalida todas las entradas de caché de una función específica.

    Args:
        func_name: Nombre de la función

    Returns:
        Número de entradas invalidadas

    Example:
        invalidate_by_function('obtener_profesores_activos')
    """
    return invalidate_cache(func_name)


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
    with _cache_lock:
        count = len(_cache_store)
        _cache_store.clear()
        _cache_stats["invalidations"] += count
    logger.info(f"Cache limpiado completamente ({count} entradas)")


def get_cache_stats() -> dict:
    """
    Obtiene estadísticas del sistema de caché.

    Returns:
        Diccionario con estadísticas:
        - hits: Número de cache hits
        - misses: Número de cache misses
        - invalidations: Número de invalidaciones
        - evictions: Número de evictiones por límite de capacidad
        - size: Número de entradas en caché
        - max_size: Capacidad máxima del caché
        - hit_rate: Porcentaje de aciertos
        - total_requests: Total de peticiones

    Example:
        stats = get_cache_stats()
        print(f"Hit rate: {stats['hit_rate']:.1f}%")
        print(f"Cache size: {stats['size']}/{stats['max_size']}")
    """
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

    return {
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "invalidations": _cache_stats["invalidations"],
        "evictions": _cache_stats["evictions"],
        "size": len(_cache_store),
        "max_size": MAX_CACHE_SIZE,
        "hit_rate": hit_rate,
        "total_requests": total_requests,
    }


def get_function_metrics(func_name: str = None) -> dict:
    """
    Obtiene métricas detalladas por función.

    Args:
        func_name: Nombre de la función. Si es None, retorna todas las funciones.

    Returns:
        Diccionario con métricas por función:
        - hits: Número de cache hits
        - misses: Número de cache misses
        - total: Total de peticiones
        - hit_rate: Porcentaje de aciertos

    Example:
        # Métricas de una función específica
        metrics = get_function_metrics('obtener_profesores_activos')
        print(f"Hit rate: {metrics['hit_rate']:.1f}%")

        # Métricas de todas las funciones
        all_metrics = get_function_metrics()
        for func, stats in all_metrics.items():
            print(f"{func}: {stats['hit_rate']:.1f}% hit rate")
    """
    if func_name is not None:
        if func_name not in _function_metrics:
            return {"hits": 0, "misses": 0, "total": 0, "hit_rate": 0.0}

        metrics = _function_metrics[func_name].copy()
        metrics["hit_rate"] = (
            (metrics["hits"] / metrics["total"] * 100) if metrics["total"] > 0 else 0.0
        )
        return metrics

    # Retornar todas las funciones
    result = {}
    for func, metrics in _function_metrics.items():
        func_metrics = metrics.copy()
        func_metrics["hit_rate"] = (
            (metrics["hits"] / metrics["total"] * 100) if metrics["total"] > 0 else 0.0
        )
        result[func] = func_metrics

    return result


def get_cache_entries_info() -> list:
    """
    Obtiene información detallada de todas las entradas en caché.

    Returns:
        Lista de diccionarios con información de cada entrada:
        - key: Clave de caché
        - age: Edad en segundos
        - ttl: Tiempo de vida configurado
        - remaining: Tiempo restante hasta expiración
        - access_count: Número de accesos
        - expired: Si la entrada ha expirado

    Example:
        entries = get_cache_entries_info()
        for entry in sorted(entries, key=lambda x: x['access_count'], reverse=True):
            print(f"{entry['key']}: {entry['access_count']} accesses")
    """
    current_time = time.time()
    entries = []

    for key, (_, timestamp, ttl, access_count) in _cache_store.items():
        age = current_time - timestamp
        remaining = ttl - age
        expired = remaining <= 0

        entries.append(
            {
                "key": key,
                "age": age,
                "ttl": ttl,
                "remaining": remaining,
                "access_count": access_count,
                "expired": expired,
            }
        )

    return entries


def print_cache_stats(detailed: bool = False):
    """
    Imprime estadísticas del caché en formato legible.

    Args:
        detailed: Si True, muestra también métricas por función

    Útil para debugging y análisis de rendimiento.

    Example:
        print_cache_stats()
        # Output:
        # ========== Cache Statistics ==========
        # Hits:           150 (75.0%)
        # Misses:          50 (25.0%)
        # Invalidations:   10
        # Evictions:        5
        # Cache size:      25 / 1000
        # ======================================

        print_cache_stats(detailed=True)
        # Incluye también métricas por función
    """
    stats = get_cache_stats()

    logger.debug("=" * 50)
    logger.debug("Cache Statistics".center(50))
    logger.debug("=" * 50)
    logger.debug(f"Hits:           {stats['hits']:5d} ({stats['hit_rate']:.1f}%)")
    logger.debug(f"Misses:         {stats['misses']:5d}")
    logger.debug(f"Invalidations:  {stats['invalidations']:5d}")
    logger.debug(f"Evictions:      {stats['evictions']:5d}")
    logger.debug(
        f"Cache size:     {stats['size']:5d} / {stats['max_size']} "
        f"({stats['size'] / stats['max_size'] * 100:.1f}% full)"
    )
    logger.debug(f"Total requests: {stats['total_requests']:5d}")
    logger.debug("=" * 50)

    if detailed:
        logger.debug("")
        logger.debug("Per-Function Metrics".center(50))
        logger.debug("=" * 50)

        function_metrics = get_function_metrics()
        if function_metrics:
            # Ordenar por número total de peticiones (descendente)
            sorted_funcs = sorted(
                function_metrics.items(), key=lambda x: x[1]["total"], reverse=True
            )

            for func_name, metrics in sorted_funcs:
                # Truncar nombre de función si es muy largo
                display_name = func_name[:40] + "..." if len(func_name) > 43 else func_name
                logger.debug(
                    f"{display_name:43s} | "
                    f"Total: {metrics['total']:4d} | "
                    f"Hit Rate: {metrics['hit_rate']:5.1f}%"
                )
        else:
            logger.debug("No function metrics available yet".center(50))

        logger.debug("=" * 50)


def reset_cache_stats():
    """
    Reinicia las estadísticas del caché (sin limpiar el caché ni métricas por función).

    Útil para medir rendimiento en períodos específicos.

    Example:
        reset_cache_stats()
        # ... ejecutar operaciones ...
        stats = get_cache_stats()
        print(f"Hit rate en esta sesión: {stats['hit_rate']:.1f}%")
    """
    _cache_stats["hits"] = 0
    _cache_stats["misses"] = 0
    _cache_stats["invalidations"] = 0
    _cache_stats["evictions"] = 0

    logger.info("Estadísticas de caché reiniciadas")


def reset_function_metrics():
    """
    Reinicia las métricas por función.

    Example:
        reset_function_metrics()
        # ... ejecutar operaciones ...
        metrics = get_function_metrics()
    """
    _function_metrics.clear()
    logger.info("Métricas por función reiniciadas")


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
