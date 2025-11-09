"""
DTOs para gestión de perfiles de usuario.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PerfilDTO:
    """DTO para representar un perfil de usuario."""

    username: str
    email: str
    tiene_bd: bool
    tiene_logo: bool
    es_actual: bool
    fecha_creacion: Optional[datetime] = None
    ruta_logo: Optional[str] = None


@dataclass
class CrearPerfilDTO:
    """DTO para crear un nuevo perfil."""

    username: str
    email: str
    password: str


@dataclass
class ActualizarPerfilDTO:
    """DTO para actualizar un perfil existente."""

    username: str
    email: str


@dataclass
class CambiarPasswordDTO:
    """DTO para cambiar contraseña."""

    username: str
    password_actual: str
    password_nueva: str
    password_confirmacion: str
