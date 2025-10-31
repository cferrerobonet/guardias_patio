"""
DTOs para Configuración

Data Transfer Objects para la configuración del sistema.
"""

from datetime import date, time
from typing import Optional

from pydantic import BaseModel


class ConfiguracionDTO(BaseModel):
    """DTO de salida para Configuración (lectura)."""

    id: int
    fecha_inicio_curso: date
    fecha_fin_curso: date
    hora_recreo1_manana: time
    hora_recreo2_manana: time
    hora_recreo1_tarde: Optional[time] = None
    hora_recreo2_tarde: Optional[time] = None
    ajuste_tutores: float = 1.0
    ajuste_no_tutores: float = 1.0
    activar_festivos_automaticos: bool = True
    dias_no_lectivos_personalizados: Optional[str] = None
    recreos_config: Optional[str] = None
    algoritmo_asignacion: str = "v2.9"  # Nuevo en v3.0

    class Config:
        """Configuración de Pydantic."""
        from_attributes = True


class ActualizarConfiguracionDTO(BaseModel):
    """DTO de entrada para actualizar la configuración."""

    fecha_inicio_curso: Optional[date] = None
    fecha_fin_curso: Optional[date] = None
    hora_recreo1_manana: Optional[time] = None
    hora_recreo2_manana: Optional[time] = None
    hora_recreo1_tarde: Optional[time] = None
    hora_recreo2_tarde: Optional[time] = None
    ajuste_tutores: Optional[float] = None
    ajuste_no_tutores: Optional[float] = None
    activar_festivos_automaticos: Optional[bool] = None
    dias_no_lectivos_personalizados: Optional[str] = None
    recreos_config: Optional[str] = None
    algoritmo_asignacion: Optional[str] = None  # Nuevo en v3.0

    class Config:
        """Configuración de Pydantic."""
        # Permite valores time de Python
        arbitrary_types_allowed = True
