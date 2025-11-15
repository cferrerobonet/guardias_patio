"""
Infrastructure Repositories

Implementaciones concretas de los repositorios usando SQLAlchemy.
"""

from .sqlalchemy_ausencia_repository import SQLAlchemyAusenciaRepository
from .sqlalchemy_configuracion_repository import SQLAlchemyConfiguracionRepository
from .sqlalchemy_curso_escolar_repository import SQLAlchemyCursoEscolarRepository
from .sqlalchemy_guardia_repository import SQLAlchemyGuardiaRepository
from .sqlalchemy_profesor_repository import SQLAlchemyProfesorRepository
from .sqlalchemy_zona_repository import SQLAlchemyZonaRepository

__all__ = [
    "SQLAlchemyProfesorRepository",
    "SQLAlchemyZonaRepository",
    "SQLAlchemyGuardiaRepository",
    "SQLAlchemyAusenciaRepository",
    "SQLAlchemyConfiguracionRepository",
    "SQLAlchemyCursoEscolarRepository",
]
