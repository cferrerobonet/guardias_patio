"""API routers package."""

from .cuotas import router as cuotas_router
from .equidad import router as equidad_router
from .estadisticas import router as estadisticas_router
from .guardias import router as guardias_router
from .profesores import router as profesores_router

__all__ = [
    "cuotas_router",
    "equidad_router",
    "guardias_router",
    "profesores_router",
    "estadisticas_router",
]
