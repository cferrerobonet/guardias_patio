"""
Use Cases de Profesor

Casos de uso relacionados con la gestión de profesores.
"""

from .actualizar_profesor import ActualizarProfesorUseCase
from .buscar_profesores import BuscarProfesoresUseCase
from .crear_profesor import CrearProfesorUseCase
from .eliminar_profesor import EliminarProfesorUseCase
from .listar_profesores import ListarProfesoresUseCase
from .obtener_profesor import ObtenerProfesorUseCase

__all__ = [
    "CrearProfesorUseCase",
    "ObtenerProfesorUseCase",
    "ListarProfesoresUseCase",
    "ActualizarProfesorUseCase",
    "EliminarProfesorUseCase",
    "BuscarProfesoresUseCase",
]
