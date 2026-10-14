"""
Repository Interfaces para el dominio de Guardias de Patio.

Los repositorios son abstracciones que definen cómo acceder a las entidades
sin acoplarse a una implementación específica de persistencia.

Esto permite:
- Separación de concerns (dominio vs infraestructura)
- Facilita testing con mocks
- Permite cambiar implementación sin afectar dominio
"""

from .ausencia_repository import IAusenciaRepository
from .base_repository import IBaseRepository
from .configuracion_repository import IConfiguracionRepository
from .curso_escolar_repository import ICursoEscolarRepository
from .guardia_repository import IGuardiaRepository
from .profesor_repository import IProfesorRepository
from .zona_repository import IZonaRepository

__all__ = [
    "IBaseRepository",
    "IProfesorRepository",
    "IAusenciaRepository",
    "IConfiguracionRepository",
    "ICursoEscolarRepository",
    "IZonaRepository",
    "IGuardiaRepository",
]
