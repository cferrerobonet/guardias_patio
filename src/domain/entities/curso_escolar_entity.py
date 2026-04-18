"""
Domain Entity: CursoEscolar

Representa un curso académico con sus fechas de inicio y fin.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class CursoEscolarEntity:
    """
    Entidad de dominio que representa un curso escolar.

    Attributes:
        id: Identificador único
        anio_inicio: Año de inicio (ej: 2024)
        anio_fin: Año de fin (ej: 2025)
        nombre: Nombre legible del curso (ej: "Curso 2024/2025")
        fecha_inicio: Fecha de inicio del curso
        fecha_fin: Fecha de fin del curso
        activo: Si es el curso activo actualmente
        cerrado: Si el curso está cerrado/finalizado
        created_at: Fecha de creación del registro
    """

    id: Optional[int] = None
    anio_inicio: int = 0
    anio_fin: int = 0
    nombre: str = ""
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    activo: bool = False
    cerrado: bool = False
    created_at: Optional[datetime] = None

    def nombre_display(self) -> str:
        """Devuelve el nombre del curso para mostrar en UI."""
        if self.nombre:
            return self.nombre
        return f"Curso {self.anio_inicio}/{self.anio_fin}"

    def esta_vigente(self) -> bool:
        """Devuelve True si el curso está activo y no cerrado."""
        return self.activo and not self.cerrado
