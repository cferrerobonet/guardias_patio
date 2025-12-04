"""
SQLAlchemy ORM Models - Re-export Module

DEPRECATED: Este módulo existe solo para backward compatibility.

Los modelos ORM han sido movidos a su ubicación canónica según Clean Architecture:
    infrastructure/database/models.py

Para nuevos desarrollos, usar:
    from infrastructure.database.models import Profesor, Guardia, ...

O el alias más corto:
    from infrastructure.database import Profesor, Guardia, ...

Este módulo será eliminado en una futura versión.
"""

# Re-export desde la nueva ubicación para backward compatibility
from infrastructure.database.models import (
    Ausencia,
    Base,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)

__all__ = [
    "Base",
    "CursoEscolar",
    "Profesor",
    "Zona",
    "Configuracion",
    "Guardia",
    "Ausencia",
]
