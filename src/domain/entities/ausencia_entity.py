"""
Domain Entity: Ausencia

Representa una ausencia de un profesor en un período determinado.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class AusenciaEntity:
    """
    Entidad de dominio que representa una ausencia de profesor.

    Attributes:
        id: Identificador único
        profesor_id: ID del profesor ausente
        fecha_inicio: Inicio de la ausencia
        fecha_fin: Fin de la ausencia
        tipo: Tipo de ausencia (baja_medica, permiso, vacaciones, otros)
        motivo: Motivo opcional de la ausencia
        documento_path: Ruta al justificante (opcional)
        activa: Si la ausencia está activa
        created_at: Fecha de creación del registro
        updated_at: Fecha de última actualización
    """

    id: Optional[int] = None
    profesor_id: int = 0
    fecha_inicio: date = field(default_factory=date.today)
    fecha_fin: date = field(default_factory=date.today)
    tipo: str = "otros"
    motivo: Optional[str] = None
    documento_path: Optional[str] = None
    activa: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def cubre_fecha(self, fecha: date) -> bool:
        """Devuelve True si la ausencia cubre la fecha dada."""
        return self.activa and self.fecha_inicio <= fecha <= self.fecha_fin

    def duracion_dias(self) -> int:
        """Devuelve la duración de la ausencia en días."""
        return (self.fecha_fin - self.fecha_inicio).days + 1
