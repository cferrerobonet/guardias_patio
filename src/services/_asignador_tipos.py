"""
Tipos de datos para el asignador de guardias v4 híbrido.

Contiene los dataclasses Slot, ContextoAsignacion y ResultadoGeneracion
que representan las estructuras de datos del algoritmo.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from infrastructure.database.models import Guardia, Profesor, Zona


@dataclass(frozen=True)
class Slot:
    """
    Unidad atómica de asignación: una guardia en un momento y lugar específico.

    Frozen para poder usar como clave de diccionario/set.
    """

    fecha: date
    turno: str  # "mañana" | "tarde"
    recreo_id: int
    zona_id: int

    def __hash__(self):
        return hash((self.fecha, self.turno, self.recreo_id, self.zona_id))



@dataclass
class ContextoAsignacion:
    """
    Contexto compartido durante toda la asignación.

    Centraliza el estado para evitar pasar múltiples diccionarios.
    """

    # Datos de entrada
    profesores: List[Profesor] = field(default_factory=list)
    slots: List[Slot] = field(default_factory=list)
    cuotas_ideales: Dict[int, int] = field(default_factory=dict)

    # Estado de asignación
    asignadas: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    slots_ocupados: Set[Slot] = field(default_factory=set)
    guardias_por_dia: Dict[Tuple[int, date], bool] = field(default_factory=dict)

    # Simultaneidad: (profesor_id, fecha, turno, recreo) -> ocupado
    # Un profesor NO puede estar en 2 zonas al mismo tiempo
    momentos_ocupados: Set[Tuple[int, date, str, int]] = field(default_factory=set)

    # Tracking de patrones para consistencia
    ultima_zona: Dict[int, Optional[int]] = field(default_factory=dict)
    ultimo_recreo: Dict[int, Optional[int]] = field(default_factory=dict)
    ultima_fecha: Dict[int, Optional[date]] = field(default_factory=dict)

    # Calendario generado
    calendario: List[Guardia] = field(default_factory=list)

    # Metadatos
    curso_id: Optional[int] = None
    total_slots: int = 0


# =============================================================================

@dataclass
class ResultadoGeneracion:
    """Resultado completo de la generación de guardias."""

    guardias: List[Guardia]
    resumen_por_profesor: Dict[int, int]

    # Métricas
    total_slots: int = 0
    slots_cubiertos: int = 0
    slots_sin_cubrir: int = 0
    cobertura: float = 0.0

    profesores_con_deficit: List[Tuple[int, str, int, int]] = field(default_factory=list)
    profesores_con_exceso: List[Tuple[int, str, int, int]] = field(default_factory=list)

    es_valido: bool = True
    errores: List[str] = field(default_factory=list)


