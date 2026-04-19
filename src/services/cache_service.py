"""
Servicio de caché en memoria con TTL para datos frecuentes.

Usa cachetools.TTLCache (thread-safe con Lock). Los datos cacheados son
de solo lectura (configuración, zonas activas) con un TTL de 5 minutos.

Uso:
    from services.cache_service import cache_configuracion, cache_zonas_activas, invalidar_cache

    config = cache_configuracion(session)
    zonas = cache_zonas_activas(session)
    invalidar_cache()  # Llamar tras mutaciones en Configuracion o Zona
"""

from __future__ import annotations

import threading
from typing import List, Optional

from utils import get_logger

logger = get_logger(__name__)

try:
    from cachetools import TTLCache
    _CACHETOOLS_AVAILABLE = True
except ImportError:
    _CACHETOOLS_AVAILABLE = False
    logger.warning("cachetools no disponible — caché desactivada. Instalar con: pip install cachetools")

# TTL de 5 minutos para datos de configuración y zonas
_TTL = 300

if _CACHETOOLS_AVAILABLE:
    _cache_config: TTLCache = TTLCache(maxsize=10, ttl=_TTL)
    _cache_zonas: TTLCache = TTLCache(maxsize=50, ttl=_TTL)
    _cache_profesores: TTLCache = TTLCache(maxsize=200, ttl=_TTL)
else:
    _cache_config = {}  # type: ignore[assignment]
    _cache_zonas = {}  # type: ignore[assignment]
    _cache_profesores = {}  # type: ignore[assignment]

_lock = threading.Lock()

# =============================================================================
# API pública
# =============================================================================


def cache_configuracion(session) -> Optional[object]:
    """
    Devuelve la Configuracion del curso, cacheada hasta 5 min.

    El objeto devuelto es el mismo ORM, solo evita la query repetida
    dentro de la misma ventana temporal. NO usar tras mutaciones sin
    llamar a `invalidar_cache()`.
    """
    from infrastructure.database.models import Configuracion

    key = "configuracion"
    with _lock:
        if key in _cache_config:
            return _cache_config[key]

    config = session.query(Configuracion).first()

    with _lock:
        _cache_config[key] = config

    return config


def cache_zonas_activas(session) -> List[object]:
    """
    Devuelve las Zonas activas, cacheadas hasta 5 min.
    """
    from infrastructure.database.models import Zona

    key = "zonas_activas"
    with _lock:
        if key in _cache_zonas:
            return _cache_zonas[key]

    zonas = session.query(Zona).filter(Zona.activa == True).all()  # noqa: E712

    with _lock:
        _cache_zonas[key] = zonas

    return zonas


def cache_profesores_activos(session) -> List[object]:
    """
    Devuelve los Profesores activos, cacheados hasta 5 min.
    """
    from infrastructure.database.models import Profesor

    key = "profesores_activos"
    with _lock:
        if key in _cache_profesores:
            return _cache_profesores[key]

    profesores = session.query(Profesor).filter(Profesor.activo == True).all()  # noqa: E712

    with _lock:
        _cache_profesores[key] = profesores

    return profesores


def invalidar_cache() -> None:
    """
    Invalida todas las entradas de caché.

    Llamar después de operaciones de escritura en Configuracion, Zona o Profesor.
    """
    with _lock:
        _cache_config.clear()
        _cache_zonas.clear()
        _cache_profesores.clear()
    logger.debug("Caché invalidada")


def invalidar_configuracion() -> None:
    """Invalida solo la caché de configuración."""
    with _lock:
        _cache_config.clear()
    logger.debug("Caché de configuración invalidada")


def invalidar_zonas() -> None:
    """Invalida solo la caché de zonas."""
    with _lock:
        _cache_zonas.clear()
    logger.debug("Caché de zonas invalidada")


def invalidar_profesores() -> None:
    """Invalida solo la caché de profesores."""
    with _lock:
        _cache_profesores.clear()
    logger.debug("Caché de profesores invalidada")
