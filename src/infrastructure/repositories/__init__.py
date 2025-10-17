"""
Infrastructure Repositories

Implementaciones concretas de los repositorios usando SQLAlchemy.
"""

from .sqlalchemy_profesor_repository import SQLAlchemyProfesorRepository

__all__ = [
    "SQLAlchemyProfesorRepository",
]
