"""
Data Transfer Objects (DTOs)

Objetos para transferir datos entre capas sin exponer entidades de dominio.
Usan Pydantic para validación automática y serialización.
"""

from application.dtos.configuracion_dto import ActualizarConfiguracionDTO, ConfiguracionDTO
from application.dtos.guardia_dto import CrearGuardiaDTO, FiltroGuardiasDTO, GuardiaDTO
from application.dtos.profesor_dto import ActualizarProfesorDTO, CrearProfesorDTO, ProfesorDTO
from application.dtos.zona_dto import ActualizarZonaDTO, CrearZonaDTO, ZonaDTO

__all__ = [
    # Profesor
    "ProfesorDTO",
    "CrearProfesorDTO",
    "ActualizarProfesorDTO",
    # Zona
    "ZonaDTO",
    "CrearZonaDTO",
    "ActualizarZonaDTO",
    # Guardia
    "GuardiaDTO",
    "CrearGuardiaDTO",
    "FiltroGuardiasDTO",
    # Configuracion
    "ConfiguracionDTO",
    "ActualizarConfiguracionDTO",
]
