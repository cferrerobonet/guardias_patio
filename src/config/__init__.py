"""
Módulo de configuración centralizada.

Proporciona acceso a settings de la aplicación mediante Pydantic.
"""

from .settings import get_settings, settings

__all__ = ["settings", "get_settings"]
