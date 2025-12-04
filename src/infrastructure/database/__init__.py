# Infrastructure Database Layer
# Este módulo contiene los modelos ORM de SQLAlchemy

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
