"""
ProfesorFilter - Filtrado de profesores elegibles

Responsabilidad: Determinar qué profesores pueden realizar
una guardia específica según restricciones y disponibilidad.
"""

import ast
import json
from collections import defaultdict
from datetime import date
from typing import Dict, List, Set, Tuple

from models.models import Profesor
from services.assignment.slot_builder import Slot
from services.validators import AusenciaChecker, TurnoValidator
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)

# Caché global de elegibilidad
_cache_elegibilidad: Dict[Tuple[date, str, int, int], List[int]] = {}
_cache_hits = 0
_cache_misses = 0


def _limpiar_cache_elegibilidad() -> None:
    """Limpia el caché de elegibilidad."""
    global _cache_elegibilidad, _cache_hits, _cache_misses
    _cache_elegibilidad.clear()
    _cache_hits = 0
    _cache_misses = 0


class ProfesorFilter:
    """
    Filtrador de profesores para asignación de guardias.

    Aplica todas las restricciones y validaciones para determinar
    qué profesores son elegibles para un slot específico.
    """

    def __init__(self, session: Session):
        self.session = session
        self.ausencia_checker = AusenciaChecker(session)
        self.turno_validator = TurnoValidator()
        self.rechazos: Dict[str, int] = defaultdict(int)
        self.total_evaluaciones = 0

    def obtener_profesores_elegibles(
        self,
        profesores: List[Profesor],
        slot: Slot,
        asignaciones_profesor: Dict[int, int],
        cuotas: Dict[int, int],
        guardias_en_fecha: Dict[Tuple[date, int], Set[int]],
    ) -> List[Profesor]:
        """
        Filtra profesores elegibles para un slot.

        Args:
            profesores: Lista de todos los profesores
            slot: Slot a asignar
            asignaciones_profesor: Contador de guardias ya asignadas
            cuotas: Cuota objetivo por profesor
            guardias_en_fecha: Guardias ya asignadas por fecha

        Returns:
            Lista de profesores elegibles
        """
        # Intentar usar caché
        cache_key = (slot.fecha, slot.turno, slot.recreo_id, slot.zona_id)
        if cache_key in _cache_elegibilidad:
            global _cache_hits
            _cache_hits += 1
            profesor_ids = _cache_elegibilidad[cache_key]
            return [p for p in profesores if p.id in profesor_ids]

        elegibles = []

        for profesor in profesores:
            self.total_evaluaciones += 1

            # Validación 1: Profesor activo
            if not profesor.activo:
                self.rechazos["profesor_inactivo"] += 1
                continue

            # Validación 2: No ausente
            if self.ausencia_checker.profesor_ausente(profesor.id, slot.fecha):
                self.rechazos["ausente"] += 1
                continue

            # Validación 3: Turno compatible
            if not self.turno_validator.es_compatible(profesor.turno, slot.turno):
                self.rechazos["turno_incompatible"] += 1
                continue

            # Validación 4: Fecha inicio guardias
            if profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias:
                self.rechazos["antes_fecha_inicio"] += 1
                continue

            # Validación 5: Fecha fin guardias
            if profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias:
                self.rechazos["despues_fecha_fin"] += 1
                continue

            # Validación 6: Días semana permitidos
            if not self._dia_semana_permitido(profesor, slot.fecha):
                self.rechazos["dia_semana_no_permitido"] += 1
                continue

            # Validación 7: Recreos permitidos
            if not self._recreo_permitido(profesor, slot.fecha, slot.recreo_id):
                self.rechazos["recreo_no_permitido"] += 1
                continue

            # Validación 8: No exceder cuota
            if asignaciones_profesor[profesor.id] >= cuotas.get(profesor.id, 0):
                self.rechazos["cuota_excedida"] += 1
                continue

            # Validación 9: No dos guardias mismo día
            if profesor.id in guardias_en_fecha.get((slot.fecha, slot.recreo_id), set()):
                self.rechazos["ya_asignado_mismo_recreo"] += 1
                continue

            elegibles.append(profesor)

        # Guardar en caché
        global _cache_misses
        _cache_misses += 1
        _cache_elegibilidad[cache_key] = [p.id for p in elegibles]

        return elegibles

    def _dia_semana_permitido(self, profesor: Profesor, fecha: date) -> bool:
        """Valida si el profesor puede hacer guardias en este día de la semana."""
        if not profesor.dias_semana_permitidos:
            return True

        try:
            dias_permitidos = ast.literal_eval(profesor.dias_semana_permitidos)
            if not isinstance(dias_permitidos, (list, tuple)):
                return True
            return fecha.weekday() in dias_permitidos
        except (ValueError, SyntaxError):
            logger.warning(
                f"Error parseando dias_semana_permitidos: {profesor.dias_semana_permitidos}"
            )
            return True

    def _recreo_permitido(
        self, profesor: Profesor, fecha: date, recreo_id: int
    ) -> bool:
        """Valida si el profesor puede hacer guardias en este recreo."""
        if not profesor.recreos_permitidos:
            return True

        try:
            horario = json.loads(profesor.recreos_permitidos)

            # Formato 1: Lista simple [1, 2]
            if isinstance(horario, list):
                return recreo_id in horario

            # Formato 2: Matriz {"0": [1, 2], "1": [1, 2], ...}
            if isinstance(horario, dict):
                dia_semana = str(fecha.weekday())
                recreos_dia = horario.get(dia_semana, [])
                return recreo_id in recreos_dia

            return True

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(
                f"Error parseando recreos_permitidos para profesor {profesor.id}: {e}"
            )
            return True

    def get_estadisticas(self) -> dict:
        """Retorna estadísticas de filtrado."""
        return {
            "total_evaluaciones": self.total_evaluaciones,
            "cache_hits": _cache_hits,
            "cache_misses": _cache_misses,
            "hit_rate": (
                _cache_hits / (_cache_hits + _cache_misses)
                if (_cache_hits + _cache_misses) > 0
                else 0
            ),
            "rechazos": dict(self.rechazos),
        }
