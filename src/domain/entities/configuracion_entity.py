"""
Domain Entity: Configuracion

Representa la configuración global de la aplicación para un curso.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any, Optional


@dataclass
class ConfiguracionEntity:
    """
    Entidad de dominio que representa la configuración del sistema.

    Attributes:
        id: Identificador único
        anio_inicio_curso: Año de inicio del curso (ej: 2025)
        fecha_inicio_curso: Fecha de inicio del curso
        fecha_fin_curso: Fecha de fin del curso
        hora_recreo1_manana: Hora del primer recreo de mañana
        hora_recreo2_manana: Hora del segundo recreo de mañana
        hora_recreo1_tarde: Hora del primer recreo de tarde (opcional)
        hora_recreo2_tarde: Hora del segundo recreo de tarde (opcional)
        activar_festivos_automaticos: Si se activan festivos de forma automática
        dias_no_lectivos_personalizados: Lista de fechas no lectivas personalizadas
        recreos_config: Configuración detallada de recreos
        ajuste_tutores: Factor de ajuste de cuota para tutores
        ajuste_no_tutores: Factor de ajuste de cuota para no tutores
        algoritmo_asignacion: Versión del algoritmo a usar
        curso_activo_id: FK al curso escolar activo
    """

    id: Optional[int] = None
    anio_inicio_curso: int = 0
    fecha_inicio_curso: Optional[date] = None
    fecha_fin_curso: Optional[date] = None
    hora_recreo1_manana: Optional[time] = None
    hora_recreo2_manana: Optional[time] = None
    hora_recreo1_tarde: Optional[time] = None
    hora_recreo2_tarde: Optional[time] = None
    activar_festivos_automaticos: bool = True
    dias_no_lectivos_personalizados: list[str] = field(default_factory=list)
    recreos_config: list[dict[str, Any]] = field(default_factory=list)
    ajuste_tutores: float = 1.0
    ajuste_no_tutores: float = 1.0
    algoritmo_asignacion: str = "v2.9"
    curso_activo_id: Optional[int] = None
