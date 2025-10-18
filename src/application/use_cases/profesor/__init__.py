"""
Use Cases de Profesor

Casos de uso relacionados con la gestión de profesores.
"""

from .crear_profesor import CrearProfesorUseCase
from .listar_profesores import ListarProfesoresUseCase
from .obtener_profesor import ObtenerProfesorUseCase

__all__ = [
    "CrearProfesorUseCase",
    "ObtenerProfesorUseCase",
    "ListarProfesoresUseCase",
]
