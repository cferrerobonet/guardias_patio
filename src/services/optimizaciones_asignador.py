"""
Optimizaciones de rendimiento para el asignador de guardias.

Este módulo contiene estructuras de datos y funciones optimizadas
para mejorar el rendimiento de la Fase 2.1 (pre-asignación equitativa).

Mejoras implementadas:
1. Índice de slots ocupados (O(1) en lugar de O(n))
2. Caché de profesores elegibles por slot-tipo
3. Pre-filtrado de profesores por turno/zona
4. Batch processing de asignaciones

Autor: Sistema de Guardias de Patio
Versión: 2.9.1
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from models.models import Guardia, Profesor
from utils import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SlotKey:
    """
    Clave única para identificar un slot de guardia.

    Usa frozen=True para permitir uso como key en diccionarios/sets.
    """
    fecha: date
    turno: str
    recreo: int
    zona_id: int


class IndiceSlots:
    """
    Índice optimizado de slots ocupados para búsquedas O(1).

    En lugar de buscar linealmente en la lista de guardias (O(n)),
    mantiene un set de slots ocupados para verificación instantánea.

    Uso:
        indice = IndiceSlots()
        indice.marcar_ocupado(fecha, turno, recreo, zona_id)
        if indice.esta_ocupado(fecha, turno, recreo, zona_id):
            print("Slot ya asignado")
    """

    def __init__(self):
        self._ocupados: Set[SlotKey] = set()

    def marcar_ocupado(
        self,
        fecha: date,
        turno: str,
        recreo: int,
        zona_id: int
    ) -> None:
        """Marca un slot como ocupado."""
        key = SlotKey(fecha, turno, recreo, zona_id)
        self._ocupados.add(key)

    def esta_ocupado(
        self,
        fecha: date,
        turno: str,
        recreo: int,
        zona_id: int
    ) -> bool:
        """Verifica si un slot está ocupado (O(1))."""
        key = SlotKey(fecha, turno, recreo, zona_id)
        return key in self._ocupados

    def desmarcar(
        self,
        fecha: date,
        turno: str,
        recreo: int,
        zona_id: int
    ) -> None:
        """Desmarca un slot (útil para backtracking)."""
        key = SlotKey(fecha, turno, recreo, zona_id)
        self._ocupados.discard(key)

    def total_ocupados(self) -> int:
        """Retorna el número total de slots ocupados."""
        return len(self._ocupados)

    @classmethod
    def desde_calendario(
        cls,
        calendario: List[Guardia]
    ) -> 'IndiceSlots':
        """
        Crea un índice a partir de un calendario existente.

        Args:
            calendario: Lista de guardias ya asignadas

        Returns:
            Índice con todos los slots del calendario marcados como ocupados
        """
        indice = cls()
        for guardia in calendario:
            indice.marcar_ocupado(
                guardia.fecha,
                guardia.turno,
                guardia.recreo,
                guardia.zona_id
            )
        return indice


class FiltroProfesores:
    """
    Filtro optimizado de profesores por características.

    Pre-filtra profesores por turno, zona preferida, etc.,
    para evitar evaluaciones innecesarias en cada slot.

    Uso:
        filtro = FiltroProfesores(profesores)
        profs_manana = filtro.por_turno("mañana")
        profs_zona1 = filtro.por_zona_preferida(1)
    """

    def __init__(self, profesores: List[Profesor]):
        self._profesores = profesores

        # Índices pre-calculados
        self._por_turno: Dict[str, List[Profesor]] = defaultdict(list)
        self._por_zona: Dict[int, List[Profesor]] = defaultdict(list)
        self._por_id: Dict[int, Profesor] = {}

        # Construir índices
        for prof in profesores:
            if prof.turno:
                self._por_turno[prof.turno].append(prof)
            if prof.zona_preferida_id:
                self._por_zona[prof.zona_preferida_id].append(prof)
            self._por_id[prof.id] = prof

    def por_turno(self, turno: str) -> List[Profesor]:
        """
        Retorna profesores del turno especificado.

        Args:
            turno: "mañana" o "tarde"

        Returns:
            Lista de profesores del turno (puede estar vacía)
        """
        return self._por_turno.get(turno, [])

    def por_zona_preferida(self, zona_id: int) -> List[Profesor]:
        """
        Retorna profesores con preferencia por la zona.

        Args:
            zona_id: ID de la zona

        Returns:
            Lista de profesores con esa zona preferida
        """
        return self._por_zona.get(zona_id, [])

    def por_id(self, profesor_id: int) -> Optional[Profesor]:
        """Retorna profesor por ID (O(1))."""
        return self._por_id.get(profesor_id)

    def filtrar_por_cuota(
        self,
        profesores: List[Profesor],
        asignadas: Dict[int, int],
        cuotas: Dict[int, int],
        minimo: Optional[int] = None,
        maximo: Optional[int] = None
    ) -> List[Profesor]:
        """
        Filtra profesores por rango de guardias asignadas vs cuota.

        Args:
            profesores: Lista de profesores a filtrar
            asignadas: Diccionario de guardias asignadas por profesor
            cuotas: Diccionario de cuotas ideales por profesor
            minimo: Número mínimo de guardias asignadas (inclusive)
            maximo: Número máximo de guardias asignadas (exclusive)

        Returns:
            Profesores que cumplen los criterios
        """
        resultado = []
        for prof in profesores:
            asignadas_prof = asignadas.get(prof.id, 0)
            cuota_prof = cuotas.get(prof.id, 0)

            if minimo is not None and asignadas_prof < minimo:
                continue
            if maximo is not None and asignadas_prof >= maximo:
                continue
            if asignadas_prof >= cuota_prof:
                continue

            resultado.append(prof)

        return resultado


class CacheElegibilidad:
    """
    Caché de profesores elegibles por tipo de slot.

    Reduce cálculos repetitivos al cachear resultados de elegibilidad
    para combinaciones de (fecha, turno, recreo, zona).

    NOTA: La caché se invalida cuando cambian las asignaciones,
    por lo que es más útil para búsquedas en batch.
    """

    def __init__(self):
        self._cache: Dict[Tuple, List[int]] = {}
        self._hits = 0
        self._misses = 0

    def obtener(
        self,
        fecha: date,
        turno: str,
        recreo: int,
        zona_id: int
    ) -> Optional[List[int]]:
        """
        Obtiene profesores elegibles cacheados.

        Returns:
            Lista de IDs de profesores elegibles, o None si no está cacheado
        """
        key = (fecha, turno, recreo, zona_id)
        if key in self._cache:
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def guardar(
        self,
        fecha: date,
        turno: str,
        recreo: int,
        zona_id: int,
        profesor_ids: List[int]
    ) -> None:
        """Guarda resultado en caché."""
        key = (fecha, turno, recreo, zona_id)
        self._cache[key] = profesor_ids.copy()

    def limpiar(self) -> None:
        """Limpia toda la caché."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def estadisticas(self) -> Dict[str, int]:
        """
        Retorna estadísticas de uso de la caché.

        Returns:
            Dict con 'hits', 'misses', 'total', 'hit_rate'
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            'hits': self._hits,
            'misses': self._misses,
            'total': total,
            'hit_rate': hit_rate,
            'cache_size': len(self._cache)
        }


def agrupar_slots_por_fecha(
    slots: List,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None
) -> Dict[date, List]:
    """
    Agrupa slots por fecha para procesamiento en batch.

    Args:
        slots: Lista de slots a agrupar
        fecha_inicio: Fecha mínima (inclusive, opcional)
        fecha_fin: Fecha máxima (inclusive, opcional)

    Returns:
        Diccionario {fecha: [slots de esa fecha]}
    """
    grupos: Dict[date, List] = defaultdict(list)

    for slot in slots:
        # Filtrar por rango de fechas si se especifica
        if fecha_inicio and slot.fecha < fecha_inicio:
            continue
        if fecha_fin and slot.fecha > fecha_fin:
            continue

        grupos[slot.fecha].append(slot)

    return grupos


def ordenar_profesores_equitativamente(
    profesores: List[Profesor],
    asignadas: Dict[int, int],
    cuotas: Dict[int, int],
    zona_actual: Optional[int] = None
) -> List[Profesor]:
    """
    Ordena profesores priorizando equidad y zona preferida.

    Criterios de ordenación (en orden de prioridad):
    1. Profesores con menos guardias asignadas (equidad)
    2. Profesores con zona preferida = zona actual (eficiencia)
    3. ID del profesor (determinismo)

    Args:
        profesores: Lista de profesores a ordenar
        asignadas: Guardias asignadas por profesor
        cuotas: Cuotas ideales por profesor
        zona_actual: Zona del slot actual (opcional)

    Returns:
        Lista ordenada de profesores
    """
    def clave_ordenacion(prof: Profesor) -> Tuple:
        asignadas_prof = asignadas.get(prof.id, 0)
        cuota_prof = cuotas.get(prof.id, 1)
        ratio = asignadas_prof / cuota_prof if cuota_prof > 0 else 0

        # Menor ratio = más prioritario (menos guardias relativas)
        # Zona preferida = más prioritario (si coincide)
        zona_match = (
            0 if zona_actual and prof.zona_preferida_id == zona_actual
            else 1
        )

        return (ratio, zona_match, prof.id)

    return sorted(profesores, key=clave_ordenacion)


def validar_indices(
    indice_slots: IndiceSlots,
    calendario: List[Guardia]
) -> bool:
    """
    Valida que el índice de slots esté sincronizado con el calendario.

    Útil para debugging y asegurar consistencia de datos.

    Args:
        indice_slots: Índice a validar
        calendario: Calendario de guardias

    Returns:
        True si están sincronizados, False en caso contrario
    """
    # Verificar tamaño
    if indice_slots.total_ocupados() != len(calendario):
        logger.error(
            f"Tamaños inconsistentes: índice={indice_slots.total_ocupados()}, "
            f"calendario={len(calendario)}"
        )
        return False

    # Verificar cada guardia del calendario
    for guardia in calendario:
        if not indice_slots.esta_ocupado(
            guardia.fecha,
            guardia.turno,
            guardia.recreo,
            guardia.zona_id
        ):
            logger.error(
                f"Guardia en calendario no está en índice: "
                f"{guardia.fecha} {guardia.turno} R{guardia.recreo} Z{guardia.zona_id}"
            )
            return False

    return True


def estadisticas_rendimiento(
    indice_slots: IndiceSlots,
    cache_elegibilidad: Optional[CacheElegibilidad] = None,
    total_slots: int = 0
) -> Dict[str, any]:
    """
    Recopila estadísticas de rendimiento de las estructuras optimizadas.

    Args:
        indice_slots: Índice de slots ocupados
        cache_elegibilidad: Caché de elegibilidad (opcional)
        total_slots: Total de slots a procesar

    Returns:
        Diccionario con estadísticas
    """
    stats = {
        'slots_ocupados': indice_slots.total_ocupados(),
        'slots_totales': total_slots,
        'cobertura': (
            indice_slots.total_ocupados() / total_slots * 100
            if total_slots > 0 else 0.0
        )
    }

    if cache_elegibilidad:
        stats.update(cache_elegibilidad.estadisticas())

    return stats
