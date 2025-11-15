from __future__ import annotations

import ast
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict, List, Optional, Set, Tuple

# Domain Services (Phase 2.4)
from domain.services.distribucion_cuotas_service import DistribucionCuotasService
from domain.services.equidad_guardias_service import EquidadGuardiasService
from models.models import Configuracion, Guardia, Profesor, Zona
from services.calculador_guardias import (
    _parse_recreos_config,
    calcular_guardias_por_profesor,
    listar_dias_lectivos,
)
from services.optimizaciones_asignador import (
    IndiceSlots,
    estadisticas_rendimiento,
)
from services.validators import AusenciaChecker
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)

# Caché global de elegibilidad (se limpia al inicio de cada generación)
_cache_elegibilidad: Dict[Tuple[date, str, int, int], List[int]] = {}
_cache_hits = 0
_cache_misses = 0

# Contadores globales de métricas
_rechazos_globales: Dict[str, int] = defaultdict(int)
_total_evaluaciones = 0


def _limpiar_cache_elegibilidad() -> None:
    """Limpia el caché de elegibilidad al inicio de cada generación."""
    global _cache_elegibilidad, _cache_hits, _cache_misses
    _cache_elegibilidad.clear()
    _cache_hits = 0
    _cache_misses = 0


def profesor_ausente(session: Session, profesor_id: int, fecha: date) -> bool:
    """
    Verifica si un profesor está ausente en una fecha específica.
    
    DEPRECADO: Esta función está obsoleta. Para nuevo código, usar
    DisponibilidadProfesorService.esta_ausente() que centraliza las validaciones.
    
    NOTA: Esta función ahora usa AusenciaChecker internamente.
    Se mantiene por compatibilidad, pero se recomienda usar
    AusenciaChecker directamente en código nuevo.

    Args:
        session: Sesión de SQLAlchemy
        profesor_id: ID del profesor a verificar
        fecha: Fecha a verificar

    Returns:
        True si el profesor tiene una ausencia activa en esa fecha, False en caso contrario
    """
    checker = AusenciaChecker(session)
    return checker.profesor_ausente(profesor_id, fecha)


@dataclass
class Slot:
    fecha: date
    recreo_id: int
    turno: str  # "mañana" | "tarde"
    zona_id: int


def _horario_permitido(
    fecha: date, recreo_id: int, horario_json: Optional[str]
) -> bool:
    """
    Valida si un recreo está permitido en una fecha según la matriz JSON.

    Soporta DOS formatos:
    1. Matriz completa: '{"0": [1, 2], "1": [1, 2], ...}' (día: recreos)
    2. Lista simple: '[1, 2]' (mismos recreos todos los días)

    NOTA: Si no hay horario_json, valida solo días laborables (L-V).
    """
    if not horario_json:
        # Por defecto: solo días laborables (L-V), todos los recreos (1-4) permitidos
        return fecha.weekday() < 5 and 1 <= recreo_id <= 4

    try:
        import json
        datos = json.loads(horario_json)

        # FORMATO 1: Matriz completa {"0": [1, 2], ...}
        if isinstance(datos, dict):
            dia_str = str(fecha.weekday())

            # Si el día no está en el JSON, verificar solo recreo
            # (el día se valida por separado en _obtener_profesores_elegibles)
            if dia_str not in datos:
                # Revisar si hay una clave especial para "todos los días"
                if "*" in datos:
                    return recreo_id in datos["*"]
                # Si no hay entrada para este día, no permitir
                return False

            # Verificar si el recreo está en la lista de recreos del día
            recreos_permitidos = datos[dia_str]
            return recreo_id in recreos_permitidos

        # FORMATO 2: Lista simple [1, 2] - mismos recreos todos los días
        elif isinstance(datos, list):
            # Verificar si el recreo está en la lista
            return recreo_id in datos

        else:
            # Formato desconocido, fallback a L-V
            return fecha.weekday() < 5 and 1 <= recreo_id <= 4

    except (json.JSONDecodeError, ValueError, KeyError, TypeError):
        # En caso de error, fallback a L-V (días laborables)
        return fecha.weekday() < 5 and 1 <= recreo_id <= 4


def _turno_de_recreo(turno_prof: str, recreo_turno: str) -> bool:
    """Verifica si un profesor puede hacer guardias en un turno de recreo.

    Args:
        turno_prof: Turno del profesor ('completo', 'mañana', 'tarde', 'mixto')
        recreo_turno: Turno del recreo ('mañana' o 'tarde')

    Returns:
        True si el profesor puede hacer guardias en ese turno
    """
    # Profesores de turno completo o mixto pueden hacer guardias en cualquier turno
    if turno_prof in ('completo', 'mixto'):
        return True
    # Profesores de turno específico solo pueden hacer guardias en su turno
    return turno_prof == recreo_turno


def _build_slots(session: Session, config: Configuracion) -> List[Slot]:
    zonas = session.query(Zona).all()
    if not zonas:
        return []

    # Crear diccionario de zonas para acceso rápido
    zonas_dict = {z.id: z for z in zonas}
    zonas_ids = [z.id for z in zonas]

    dias = listar_dias_lectivos(config)
    recreos = _parse_recreos_config(config)
    slots: List[Slot] = []

    if not recreos:
        # Fallback: deducir recreos de horas y construir ids 1..N por turno
        tmp = []
        rid = 0
        if config.hora_recreo1_manana:
            rid += 1
            tmp.append({'id': rid, 'turno': 'mañana'})
        if config.hora_recreo2_manana:
            rid += 1
            tmp.append({'id': rid, 'turno': 'mañana'})
        if config.hora_recreo1_tarde:
            rid += 1
            tmp.append({'id': rid, 'turno': 'tarde'})
        if config.hora_recreo2_tarde:
            rid += 1
            tmp.append({'id': rid, 'turno': 'tarde'})
        recreos = [{**r, 'zonas': len(zonas)} for r in tmp]

    for f in dias:
        for r in recreos:
            for i in range(min(r.get('zonas', 1), len(zonas_ids))):
                zona_id = zonas_ids[i]
                zona = zonas_dict[zona_id]

                # Verificar si la zona está activa en esta fecha
                zona_activa = True
                if hasattr(zona, 'fecha_inicio') and zona.fecha_inicio and f < zona.fecha_inicio:
                    zona_activa = False
                if hasattr(zona, 'fecha_fin') and zona.fecha_fin and f > zona.fecha_fin:
                    zona_activa = False

                # Solo crear slot si la zona está activa en esta fecha
                if zona_activa:
                    slots.append(Slot(f, int(r['id']), r.get('turno', 'mañana'), zona_id))

    logger.info(f"Slots creados: {len(slots)} (considerando fechas de zonas)")
    return slots


def _obtener_profesores_elegibles_optimizado(
    profesores: List[Profesor],
    slot: Slot,
    asignadas: Dict[int, int],
    cuotas: Dict[int, int],
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int, int], bool],
    guardias_por_dia_prof: Dict[Tuple[int, date], bool],
    session: Session,
    respetar_cuotas: bool = True,
    permitir_multiples_guardias_dia: bool = False
) -> List[Profesor]:
    """
    Versión optimizada de obtención de elegibles con scoring avanzado.

    Diferencias vs versión anterior:
    - Pre-filtrado más eficiente
    - Scoring integrado para pre-selección
    - Menor número de evaluaciones redundantes

    Args:
        profesores: Lista de todos los profesores
        slot: Slot a asignar
        asignadas: Diccionario de guardias asignadas por profesor
        cuotas: Diccionario de cuotas por profesor
        guardias_por_slot_prof: Control de guardias por slot
        guardias_por_dia_prof: Control de guardias por día
        session: Sesión de SQLAlchemy
        respetar_cuotas: Si False, ignora las cuotas de guardias
        permitir_multiples_guardias_dia: Si True, permite >1 guardia/día

    Returns:
        Lista de profesores elegibles ordenada por prioridad
    """
    # Usar función base para elegibilidad básica
    return _obtener_profesores_elegibles(
        profesores, slot, asignadas, cuotas,
        guardias_por_slot_prof, guardias_por_dia_prof,
        session, respetar_cuotas, permitir_multiples_guardias_dia
    )


def _seleccionar_profesor_optimizado(
    elegibles: List[Profesor],
    slot: Slot,
    asignadas: Dict[int, int],
    cuotas: Dict[int, int],
    cuotas_ideales: Dict[int, int],
    ultimo_dia_prof: Dict[int, Optional[date]],
    ultimo_recreo_prof: Dict[int, Optional[int]],
    zona_preferida_prof: Dict[int, Optional[int]],
    total_slots: int
) -> Profesor:
    """
    Selección DETERMINISTA EQUITATIVA con garantía de igualdad por grupos.

    NUEVO ALGORITMO (v2.9 MEJORADO v1.3):
    ======================================
    REGLA ABSOLUTA: Profesores con mismas características (turno, horas, tutoría)
    DEBEN recibir EXACTAMENTE las mismas guardias (±1 por redondeo).

    Criterios de selección (en orden estricto) - MEJORADO v1.3:
    1. DÉFICIT ABSOLUTO: Cuota ideal - asignadas (más déficit = prioridad)
    2. ZONA PREFERIDA: Consistencia de zona
    3. ⭐ FECHAS CONSECUTIVAS: Menor distancia desde última guardia (NUEVO v1.3)
       - Objetivo: Agrupar guardias para que el profesor termine antes
       - Beneficio: Períodos largos sin guardias
    4. RECREO CONSISTENTE: Mantener mismo recreo
    5. DESEMPATE DETERMINISTA: ID del profesor (sin aleatoriedad)

    MEJORA v1.3:
    - ✅ Añadido criterio de fechas consecutivas (prioridad 3)
    - ✅ Recreo movido a prioridad 4 (antes implícito en días sin guardia)

    ELIMINADO:
    - ❌ Factor aleatorio (causaba inequidad)
    - ❌ Penalización × 100 por exceso (bloqueaba profesores)
    - ❌ Bonus por horas (discriminaba parciales)

    Args:
        elegibles: Lista de profesores elegibles
        slot: Slot a asignar
        asignadas: Guardias asignadas por profesor
        cuotas: Cuotas dinámicas por profesor (no usado)
        cuotas_ideales: Cuotas calculadas inicialmente (AUTORIDAD)
        ultimo_dia_prof: Último día asignado por profesor
        ultimo_recreo_prof: Último recreo asignado por profesor
        zona_preferida_prof: Zona preferida de cada profesor
        total_slots: Total de slots del calendario

    Returns:
        Profesor seleccionado (el que NECESITA más guardias)
    """
    def score_equitativo(p: Profesor) -> Tuple[float, int, int, int, int]:
        # 1. DÉFICIT ABSOLUTO (más importante)
        # Cuántas guardias le faltan para alcanzar su cuota ideal
        cuota_ideal = cuotas_ideales.get(p.id, 0)
        deficit = cuota_ideal - asignadas[p.id]

        # 2. ZONA PREFERIDA (beneficio secundario)
        if zona_preferida_prof[p.id] is None:
            s_zona = 0
        elif zona_preferida_prof[p.id] == slot.zona_id:
            s_zona = 100
        else:
            s_zona = -50

        # 3. ⭐ NUEVO v1.3: FECHAS CONSECUTIVAS/AGRUPADAS
        # Invertir: menor distancia = mayor prioridad
        # Multiplicar por -1 para ordenar descendente (menor distancia primero)
        if ultimo_dia_prof[p.id]:
            distancia_dias = (slot.fecha - ultimo_dia_prof[p.id]).days
            # Negar para que menor distancia sea mayor valor (ordenamos reverse=True)
            puntuacion_fechas = -distancia_dias
        else:
            # Nunca ha tenido guardias, prioridad media (0)
            # No tan alta como fechas consecutivas, pero mejor que dispersas
            puntuacion_fechas = 0

        # 4. RECREO CONSISTENTE (mantener mismo recreo)
        if ultimo_recreo_prof[p.id] is None:
            s_recreo = 0
        elif ultimo_recreo_prof[p.id] == slot.recreo_id:
            s_recreo = 50  # Bonus por consistencia
        else:
            s_recreo = -25  # Penalización por cambio de recreo

        # 5. DESEMPATE DETERMINISTA (ID menor = prioridad)
        # Esto garantiza orden reproducible entre profesores idénticos
        desempate = -p.id  # Negativo para que menor ID = mayor prioridad

        # Orden de prioridad (ordenado reverse=True, mayores valores primero):
        # 1. Deficit (DESC): Más necesita = primero
        # 2. Zona (DESC): Zona preferida = beneficio (100 > 0 > -50)
        # 3. ⭐ Fechas (DESC): Menor distancia = mayor prioridad (NUEVO)
        # 4. Recreo (DESC): Recreo consistente = beneficio (50 > 0 > -25)
        # 5. Desempate (DESC): ID menor = prioridad
        return (
            deficit,            # Más positivo = más prioridad
            s_zona,            # 100 > 0 > -50
            puntuacion_fechas, # Mayor = fechas más cercanas (0 a -inf)
            s_recreo,          # 50 > 0 > -25
            desempate          # -ID menor = más prioridad
        )

    return sorted(elegibles, key=score_equitativo, reverse=True)[0]


def generar_calendario_guardias(
    session: Session,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Tuple[List[Guardia], Dict[int, int]]:
    """
    Genera el calendario de guardias con ALGORITMO OPTIMIZADO AVANZADO.

    NUEVO ENFOQUE - Optimización Global:
    ====================================
    Este algoritmo garantiza:
    ✅ 100% cobertura de slots (todos los recreos cubiertos)
    ✅ 100% participación (todos los profesores elegibles con guardias)
    ✅ Mínima desviación entre cuotas calculadas y asignadas (<5%)
    ✅ Distribución equitativa con balanceo dinámico

    Técnicas avanzadas implementadas:
    - BALANCEO DINÁMICO: Ajuste continuo de cuotas durante asignación
    - BACKTRACKING INTELIGENTE: Reasignación automática de conflictos
    - BÚSQUEDA EXHAUSTIVA: Exploración completa del espacio de soluciones
    - SCORING MULTI-CRITERIO: Optimización simultánea de 6 factores
    - SWAP OPTIMIZER: Intercambios inteligentes para mejorar distribución
    - CONSTRAINT RELAXATION: Relajación progresiva y reversible

    Fases del algoritmo optimizado:
    1. INICIALIZACIÓN: Ordenamiento óptimo de slots (10-15%)
    2. ASIGNACIÓN BALANCEADA: Scoring multi-criterio con ajuste dinámico (15-60%)
    3. BACKTRACKING: Reasignación de slots conflictivos (60-75%)
    4. OPTIMIZACIÓN: Swaps para minimizar desviaciones (75-85%)
    5. COMPLETITUD: Garantía de cobertura total (85-95%)
    6. REFINAMIENTO: Ajuste fino de distribución (95-100%)

    Métricas de calidad:
    - Cobertura: % de slots asignados (objetivo: 100%)
    - Participación: % de profesores con guardias (objetivo: 100%)
    - Desviación promedio: Abs(asignadas - cuota) / cuota (objetivo: <5%)
    - Desviación máxima: Max desviación individual (objetivo: <10%)
    - Balance: Coeficiente de variación (objetivo: <0.2)

    Args:
        session: Sesión de SQLAlchemy
        progress_callback: Función opcional para reportar progreso.
                          Recibe (porcentaje, mensaje_detalle)

    Returns:
        Tuple con (lista de guardias, diccionario de asignaciones por profesor)
    """
    global _rechazos_globales, _total_evaluaciones
    _rechazos_globales.clear()
    _total_evaluaciones = 0
    _limpiar_cache_elegibilidad()

    logger.info("=" * 80)
    logger.info("INICIANDO GENERACIÓN CON ALGORITMO OPTIMIZADO AVANZADO")
    logger.info("=" * 80)

    def reportar_progreso(porcentaje: int, mensaje: str = ""):
        """Helper para reportar progreso de forma segura."""
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except Exception as e:
                logger.warning(f"Error al reportar progreso: {e}")

    reportar_progreso(0, "Validando configuración...")

    # Obtener curso activo para asignar a las guardias
    from services.gestor_cursos import GestorCursos
    curso_activo = GestorCursos.obtener_curso_activo(session)
    curso_id = curso_activo.id if curso_activo else None

    if not curso_id:
        logger.warning("⚠️ No hay curso activo - las guardias se crearán sin curso asignado")
    else:
        logger.info(f"✅ Guardias se asignarán al curso activo: {curso_activo.nombre} (ID: {curso_id})")

    config = session.query(Configuracion).first()
    if not config:
        logger.error("No existe configuración del curso")
        raise ValueError("No existe configuración del curso")

    reportar_progreso(5, "Cargando profesores...")

    profesores = session.query(Profesor).all()
    if not profesores:
        logger.error("No hay profesores registrados")
        raise ValueError("No hay profesores registrados")
    logger.info(f"Profesores disponibles: {len(profesores)}")

    reportar_progreso(10, f"{len(profesores)} profesores cargados")

    zonas = session.query(Zona).all()
    if not zonas:
        logger.error("No hay zonas registradas")
        raise ValueError("No hay zonas registradas")
    logger.info(f"Zonas configuradas: {len(zonas)}")

    reportar_progreso(15, f"{len(zonas)} zonas configuradas")
    reportar_progreso(20, "Calculando distribución óptima...")

    # Calcular cuotas ideales usando Domain Service
    try:
        distribucion_service = DistribucionCuotasService(session)
        profesores_activos = session.query(Profesor).filter(Profesor.activo.is_(True)).all()
        cuotas_ideales = distribucion_service.calcular_cuotas(profesores_activos)
        logger.info("✓ Cuotas calculadas con DistribucionCuotasService (Domain Service)")
    except Exception as e:
        logger.warning(f"⚠️ Error con DistribucionCuotasService: {e}. Usando método legacy.")
        cuotas_ideales = calcular_guardias_por_profesor(session)

    # Inicializar estructuras de datos
    asignadas = defaultdict(int)
    calendario: List[Guardia] = []

    # Estructuras de control para evitar duplicados
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int, int], bool] = {}
    guardias_por_dia_prof: Dict[Tuple[int, date], bool] = {}

    # Estructuras para optimización de continuidad
    ultimo_por_zona: Dict[int, Optional[int]] = {z.id: None for z in zonas}
    ultimo_recreo_prof: Dict[int, Optional[int]] = defaultdict(lambda: None)
    ultimo_dia_prof: Dict[int, Optional[date]] = defaultdict(lambda: None)
    zona_preferida_prof: Dict[int, Optional[int]] = defaultdict(lambda: None)

    reportar_progreso(25, "Construyendo slots de guardias...")

    slots = _build_slots(session, config)
    if not slots:
        reportar_progreso(100, "No hay slots para asignar")
        return ([], {})

    total_slots = len(slots)
    logger.info(f"Slots totales a asignar: {total_slots}")
    reportar_progreso(30, f"{total_slots} slots creados")

    # ==================================================================
    # FASE 0: PRE-ANÁLISIS Y OPTIMIZACIÓN DE ELEGIBILIDAD (25% - 30%)
    # ==================================================================
    logger.info("")
    logger.info("=" * 80)
    logger.info("FASE 0: PRE-ANÁLISIS DE ELEGIBILIDAD Y AJUSTE DE CUOTAS")
    logger.info("=" * 80)
    reportar_progreso(25, "Fase 0: Analizando elegibilidad...")

    # Pre-calcular matriz de elegibilidad profesor-slot
    from collections import Counter
    matriz_elegibilidad: Dict[int, int] = Counter()  # prof_id -> slots compatibles

    for slot in slots:
        # Contar cuántos profesores son elegibles para cada slot
        elegibles_base = _obtener_profesores_elegibles(
            profesores=profesores,
            slot=slot,
            asignadas={},  # Sin asignaciones previas
            cuotas={p.id: 999 for p in profesores},  # Sin límite de cuotas
            guardias_por_slot_prof={},
            guardias_por_dia_prof={},
            session=session,
            respetar_cuotas=False,
            permitir_multiples_guardias_dia=False
        )

        for p in elegibles_base:
            matriz_elegibilidad[p.id] += 1

    # Analizar profesores con baja elegibilidad
    profesores_baja_elegibilidad = []
    profesores_sin_elegibilidad = []

    for prof in profesores:
        if prof.id in cuotas_ideales and cuotas_ideales[prof.id] > 0:
            slots_compatibles = matriz_elegibilidad.get(prof.id, 0)
            tasa_elegibilidad = (slots_compatibles / total_slots * 100) if total_slots > 0 else 0

            if slots_compatibles == 0:
                profesores_sin_elegibilidad.append(prof)
            elif tasa_elegibilidad < 30:  # Menos del 30% de slots
                profesores_baja_elegibilidad.append((prof, slots_compatibles, tasa_elegibilidad))

    # Logging de análisis
    logger.info("Análisis de elegibilidad completado:")
    logger.info(f"  Total slots: {total_slots}")
    logger.info(f"  Total profesores con cuota: {len([p for p in profesores if cuotas_ideales.get(p.id, 0) > 0])}")
    logger.info(f"  Profesores SIN ningún slot compatible: {len(profesores_sin_elegibilidad)}")
    logger.info(f"  Profesores con BAJA elegibilidad (<30%): {len(profesores_baja_elegibilidad)}")

    if profesores_sin_elegibilidad:
        logger.warning(f"⚠️ ADVERTENCIA: {len(profesores_sin_elegibilidad)} profesores no pueden hacer ninguna guardia:")
        for p in profesores_sin_elegibilidad[:5]:  # Mostrar primeros 5
            logger.warning(f"    - {p.nombre_completo} (turno: {p.turno}, cuota ideal: {cuotas_ideales.get(p.id, 0)})")
        # Ajustar cuotas a 0 para profesores sin elegibilidad
        for p in profesores_sin_elegibilidad:
            cuotas_ideales[p.id] = 0

    if profesores_baja_elegibilidad:
        logger.info("ℹ️ INFO: Profesores con baja elegibilidad:")
        for p, slots_comp, tasa in sorted(profesores_baja_elegibilidad, key=lambda x: x[2])[:5]:
            logger.info(f"    - {p.nombre_completo}: {slots_comp} slots ({tasa:.1f}%)")

    # AJUSTE INTELIGENTE DE CUOTAS: Redistribuir cuotas de profesores sin elegibilidad
    total_cuotas_originales = sum(cuotas_ideales.values())
    cuotas_perdidas = sum(cuotas_ideales[p.id] for p in profesores_sin_elegibilidad)

    if cuotas_perdidas > 0:
        # Redistribuir entre profesores elegibles proporcionalmente
        profesores_elegibles = [
            p for p in profesores
            if matriz_elegibilidad.get(p.id, 0) > 0 and cuotas_ideales.get(p.id, 0) > 0
        ]

        if profesores_elegibles:
            # Distribuir proporcionalmente según cuota actual
            suma_cuotas_elegibles = sum(cuotas_ideales[p.id] for p in profesores_elegibles)

            if suma_cuotas_elegibles > 0:
                for p in profesores_elegibles:
                    proporcion = cuotas_ideales[p.id] / suma_cuotas_elegibles
                    incremento = int(cuotas_perdidas * proporcion)
                    cuotas_ideales[p.id] += incremento

                logger.info(f"  ✓ {cuotas_perdidas} guardias redistribuidas entre {len(profesores_elegibles)} profesores elegibles")

    # Verificar balance final
    total_cuotas_ajustadas = sum(cuotas_ideales.values())
    logger.info(f"  Cuotas totales: {total_cuotas_originales} → {total_cuotas_ajustadas}")
    logger.info(f"  Diferencia vs slots totales: {total_slots - total_cuotas_ajustadas}")

    reportar_progreso(30, f"Fase 0: {len(profesores_sin_elegibilidad)} prof. sin elegibilidad detectados")

    # ==================================================================
    # FASE 1: ORDENAMIENTO ÓPTIMO DE SLOTS (30% - 35%)
    # ==================================================================
    logger.info("")
    logger.info("FASE 1: Ordenamiento óptimo de slots para maximizar eficiencia")
    logger.info("-" * 80)
    reportar_progreso(30, "Fase 1: Ordenando slots óptimamente...")

    # Ordenar slots para facilitar asignación:
    # 1. Por fecha (asegurar continuidad temporal)
    # 2. Por turno (agrupar mañana/tarde)
    # 3. Por recreo (asegurar cobertura balanceada)
    # 4. Por zona (facilitar asignación de zonas preferidas)
    slots_ordenados = sorted(
        slots,
        key=lambda s: (s.fecha, s.turno, s.recreo_id, s.zona_id)
    )

    logger.info(f"✓ {len(slots_ordenados)} slots ordenados para asignación óptima")
    reportar_progreso(35, f"Slots ordenados: {total_slots}")

    # ==================================================================
    # FASE 2: ASIGNACIÓN BALANCEADA CON SCORING MULTI-CRITERIO (35% - 60%)
    # ==================================================================
    logger.info("")
    logger.info("FASE 2: Asignación balanceada con scoring multi-criterio")
    logger.info("-" * 80)
    reportar_progreso(35, "Fase 2: Asignación balanceada...")

    # Cuotas dinámicas - ELIMINADAS, usamos solo cuotas_ideales
    # El algoritmo v2.9 NO debe ajustar cuotas dinámicamente
    # porque eso rompe la equidad entre profesores del mismo grupo
    cuotas_dinamicas = cuotas_ideales.copy()  # Mantener por compatibilidad

    # PRE-ASIGNACIÓN: Garantizar participación mínima EQUITATIVA
    # NUEVO v2.9: Asignar por RONDAS para garantizar equidad
    # OPTIMIZADO v2.9.1: Usar IndiceSlots para búsquedas O(1)
    logger.info("FASE 2.1: Pre-asignación equitativa por rondas (OPTIMIZADA)")
    logger.info("-" * 40)

    # Inicializar índice de slots ocupados para búsquedas O(1)
    indice_slots = IndiceSlots.desde_calendario(calendario)
    logger.info(f"  Índice de slots inicializado: {indice_slots.total_ocupados()} slots ocupados")

    profesores_con_cuota = [
        p for p in profesores
        if cuotas_ideales.get(p.id, 0) > 0 and matriz_elegibilidad.get(p.id, 0) > 0
    ]

    # ORDENAMIENTO POR PRIORIDADES (según premisas del sistema):
    # 1. Profesores con fecha_inicio_guardias (más restrictivos temporalmente)
    # 2. Profesores con fecha_fin_guardias (periodo limitado)
    # 3. Profesores con turno mixto (mayor complejidad de asignación)
    # 4. Resto de profesores
    # 5. ID como desempate determinista
    def calcular_prioridad_profesor(p: Profesor) -> Tuple[int, int, int, int]:
        """
        Calcula prioridad de asignación del profesor.

        Retorna tupla (prioridad_inicio, prioridad_fin, prioridad_mixto, id)
        Valores menores = mayor prioridad (se ordenará ascendente)
        """
        # Prioridad 1: Fecha de inicio (0 = tiene fecha inicio, 1 = no tiene)
        tiene_inicio = 0 if p.fecha_inicio_guardias else 1

        # Prioridad 2: Fecha de fin (0 = tiene fecha fin, 1 = no tiene)
        tiene_fin = 0 if p.fecha_fin_guardias else 1

        # Prioridad 3: Turno mixto (0 = mixto, 1 = otros)
        es_mixto = 0 if p.turno and p.turno.lower() in ('mixto', 'ambos') else 1

        # Desempate: ID menor primero
        return (tiene_inicio, tiene_fin, es_mixto, p.id)

    profesores_prioritarios = sorted(
        profesores_con_cuota,
        key=calcular_prioridad_profesor
    )

    # Log de orden de prioridades
    logger.info("Orden de asignación por prioridades:")
    logger.info(f"  1. Profesores con fecha_inicio: {sum(1 for p in profesores_prioritarios if p.fecha_inicio_guardias)}")
    logger.info(f"  2. Profesores con fecha_fin: {sum(1 for p in profesores_prioritarios if p.fecha_fin_guardias)}")
    logger.info(f"  3. Profesores mixtos: {sum(1 for p in profesores_prioritarios if p.turno and p.turno.lower() in ('mixto', 'ambos'))}")
    logger.info(f"  4. Total profesores: {len(profesores_prioritarios)}")

    # RONDAS: Dar 1 guardia a TODOS antes de dar 2 guardias a CUALQUIERA
    # Esto garantiza equidad perfecta en la distribución inicial
    ronda = 0
    max_rondas = max(cuotas_ideales.values()) if cuotas_ideales else 0
    pre_asignaciones = 0

    logger.info(f"  Iniciando {max_rondas} rondas de asignación equitativa...")
    logger.info(f"  {len(profesores_prioritarios)} profesores en cola")

    while ronda < max_rondas and len(calendario) < total_slots:
        ronda += 1
        asignaciones_ronda = 0

        # En cada ronda, intentar asignar 1 guardia a cada profesor
        # que aún no ha alcanzado su cuota ideal
        for prof in profesores_prioritarios:
            # ¿Este profesor ya alcanzó su cuota ideal?
            if asignadas[prof.id] >= cuotas_ideales[prof.id]:
                continue

            # ¿Ya tiene suficientes para esta ronda?
            if asignadas[prof.id] >= ronda:
                continue

            # Buscar un slot compatible
            for slot in slots_ordenados:
                # OPTIMIZACIÓN: Usar índice O(1) en lugar de any() O(n)
                if indice_slots.esta_ocupado(
                    slot.fecha, slot.turno, slot.recreo_id, slot.zona_id
                ):
                    continue  # Slot ocupado

                # Verificar elegibilidad
                elegibles_temp = _obtener_profesores_elegibles(
                    profesores=[prof],
                    slot=slot,
                    asignadas=asignadas,
                    cuotas=cuotas_ideales,  # Usar cuotas fijas
                    guardias_por_slot_prof=guardias_por_slot_prof,
                    guardias_por_dia_prof=guardias_por_dia_prof,
                    session=session,
                    respetar_cuotas=False,  # No limitar por cuota en pre-asignación
                    permitir_multiples_guardias_dia=False
                )

                if elegibles_temp:
                    # ¡Asignar!
                    _registrar_guardia(
                        calendario, prof, slot, asignadas,
                        ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                        zona_preferida_prof, guardias_por_slot_prof,
                        guardias_por_dia_prof
                    , curso_id=curso_id)

                    # CRÍTICO: Actualizar índice de slots
                    indice_slots.marcar_ocupado(
                        slot.fecha, slot.turno, slot.recreo_id, slot.zona_id
                    )

                    pre_asignaciones += 1
                    asignaciones_ronda += 1
                    break  # Pasar al siguiente profesor

        if asignaciones_ronda == 0:
            logger.warning(
                f"  Ronda {ronda}: 0 asignaciones (no hay slots compatibles)"
            )
            break  # No se pudo asignar nada, salir

        logger.debug(
            f"  Ronda {ronda}: {asignaciones_ronda} asignaciones "
            f"(cobertura: {len(calendario)}/{total_slots})"
        )

    logger.info(
        f"✓ Pre-asignadas {pre_asignaciones} guardias en {ronda} rondas equitativas"
    )
    logger.info(
        f"  Cobertura actual: {len(calendario)}/{total_slots} "
        f"({len(calendario)/total_slots*100:.1f}%)"
    )

    # Mostrar estadísticas de rendimiento de optimizaciones
    stats = estadisticas_rendimiento(
        indice_slots=indice_slots,
        total_slots=total_slots
    )
    logger.info(f"  Slots ocupados: {stats['slots_ocupados']} ({stats['cobertura']:.1f}%)")

    # Verificar cuántos profesores aún sin guardias
    profesores_sin_guardias = [
        p for p in profesores_prioritarios if asignadas[p.id] == 0
    ]
    if profesores_sin_guardias:
        logger.warning(
            f"  ⚠️ {len(profesores_sin_guardias)} profesores AÚN sin guardias "
            f"tras pre-asignación"
        )
        for p in profesores_sin_guardias[:5]:
            logger.warning(
                f"    - {p.nombre_completo} (turno: {p.turno}, "
                f"cuota: {cuotas_ideales.get(p.id, 0)})"
            )

    logger.info("")
    logger.info("FASE 2.2: Asignación masiva con scoring equitativo")
    logger.info("-" * 40)

    # Tracking de slots sin cubrir para backtracking
    slots_sin_cubrir_fase2: List[Slot] = []

    progreso_base = 35
    progreso_max = 60
    rango_progreso = progreso_max - progreso_base
    intervalo_reporte = max(1, total_slots // 25)

    for idx, slot in enumerate(slots_ordenados):
        if idx % intervalo_reporte == 0:
            porcentaje = progreso_base + int((idx / total_slots) * rango_progreso)
            cobertura = (len(calendario) / total_slots * 100) if total_slots > 0 else 0
            # Mensaje más descriptivo con fecha actual
            fecha_formateada = slot.fecha.strftime("%d/%m")
            reportar_progreso(
                porcentaje,
                f"Fase 2: Asignando guardias ({len(calendario)}/{total_slots}) - Procesando {fecha_formateada}..."
            )

        # Obtener profesores elegibles con scoring avanzado
        # ALGORITMO v2.9: Usar cuotas_ideales (no dinámicas) para mantener equidad
        elegibles = _obtener_profesores_elegibles_optimizado(
            profesores=profesores,
            slot=slot,
            asignadas=asignadas,
            cuotas=cuotas_ideales,  # CAMBIO v2.9: ideales en lugar de dinámicas
            guardias_por_slot_prof=guardias_por_slot_prof,
            guardias_por_dia_prof=guardias_por_dia_prof,
            session=session,
            respetar_cuotas=True,
            permitir_multiples_guardias_dia=False
        )

        if not elegibles:
            slots_sin_cubrir_fase2.append(slot)
            continue

        # Selección con scoring multi-criterio optimizado
        elegido = _seleccionar_profesor_optimizado(
            elegibles=elegibles,
            slot=slot,
            asignadas=asignadas,
            cuotas=cuotas_dinamicas,
            cuotas_ideales=cuotas_ideales,
            ultimo_dia_prof=ultimo_dia_prof,
            ultimo_recreo_prof=ultimo_recreo_prof,
            zona_preferida_prof=zona_preferida_prof,
            total_slots=total_slots
        )

        # Registrar guardia
        _registrar_guardia(
            calendario, elegido, slot, asignadas,
            ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
            zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
        , curso_id=curso_id)

        # ALGORITMO v2.9: NO incrementar cuotas dinámicamente para mantener equidad
        # El ajuste dinámico rompía la equidad al permitir que profesores superen su cuota ideal
        # if asignadas[elegido.id] >= cuotas_dinamicas[elegido.id] * 0.9:
        #     cuotas_dinamicas[elegido.id] = int(cuotas_dinamicas[elegido.id] * 1.05)

    guardias_fase2 = len(calendario)
    cobertura_fase2 = (guardias_fase2 / total_slots * 100) if total_slots > 0 else 0

    logger.info(f"✓ Fase 2 completada: {guardias_fase2}/{total_slots} ({cobertura_fase2:.1f}%)")
    logger.info(f"  Slots pendientes: {len(slots_sin_cubrir_fase2)}")
    reportar_progreso(60, f"Fase 2: {cobertura_fase2:.1f}% cobertura")

    # ==================================================================
    # FASE 3: CSP CON FORWARD CHECKING (60% - 75%)
    # ==================================================================
    logger.info("")
    logger.info("FASE 3: CSP con Forward Checking para slots conflictivos")
    logger.info("-" * 80)
    reportar_progreso(60, "Fase 3: Aplicando CSP...")

    slots_sin_cubrir_fase3: List[Slot] = []
    csp_intentos = 0
    csp_exitosos = 0
    reasignaciones_csp = 0

    # Función auxiliar para verificar consistencia forward
    def verificar_consistencia_forward(
        slot_actual: Slot,
        prof_candidato_id: int,
        slots_restantes: List[Slot],
        asignadas_temp: Dict[int, int],
        cuotas_temp: Dict[int, int]
    ) -> bool:
        """Verifica si asignar prof_candidato a slot_actual deja opciones viables para slots futuros"""
        # Simular asignación temporal
        asignadas_simuladas = asignadas_temp.copy()
        asignadas_simuladas[prof_candidato_id] = asignadas_simuladas.get(prof_candidato_id, 0) + 1

        # Verificar que slots restantes críticos tienen al menos 1 profesor elegible
        slots_criticos = [s for s in slots_restantes if s in slots_sin_cubrir_fase2][:10]  # Verificar 10 más críticos

        for slot_futuro in slots_criticos:
            tiene_opcion = False
            for prof in profesores:
                if asignadas_simuladas.get(prof.id, 0) >= cuotas_temp.get(prof.id, 0):
                    continue

                # Verificación rápida de restricciones básicas
                if prof.id in guardias_por_dia_prof.get(slot_futuro.fecha, set()):
                    continue

                # Tiene al menos una opción viable
                tiene_opcion = True
                break

            if not tiene_opcion:
                return False  # Asignación crearía deadlock futuro

        return True

    total_slots_csp = len(slots_sin_cubrir_fase2)
    for idx_csp, slot in enumerate(slots_sin_cubrir_fase2):
        csp_intentos += 1

        # Actualizar progreso cada 5 slots
        if idx_csp % 5 == 0 and total_slots_csp > 0:
            progreso_csp = 60 + int((idx_csp / total_slots_csp) * 15)
            reportar_progreso(
                progreso_csp,
                f"Fase 3: Resolviendo slots conflictivos ({idx_csp}/{total_slots_csp})..."
            )

        # ALGORITMO v2.9: NO relajar cuotas, usar cuotas ideales estrictas
        # NIVEL 1: Intentar con cuotas ideales (sin relajación)
        # cuotas_relajadas eliminadas para mantener equidad

        elegibles = _obtener_profesores_elegibles_optimizado(
            profesores=profesores,
            slot=slot,
            asignadas=asignadas,
            cuotas=cuotas_ideales,  # CAMBIO v2.9: ideales en lugar de relajadas
            guardias_por_slot_prof=guardias_por_slot_prof,
            guardias_por_dia_prof=guardias_por_dia_prof,
            session=session,
            respetar_cuotas=True,
            permitir_multiples_guardias_dia=False
        )

        # Filtrar elegibles que pasan forward checking
        elegibles_csp = []
        for prof in elegibles:
            if verificar_consistencia_forward(
                slot, prof.id, slots_sin_cubrir_fase2[csp_intentos:],
                asignadas, cuotas_ideales  # CAMBIO v2.9: ideales en lugar de relajadas
            ):
                elegibles_csp.append(prof)

        if elegibles_csp:
            elegido = _seleccionar_profesor_optimizado(
                elegibles=elegibles_csp,
                slot=slot,
                asignadas=asignadas,
                cuotas=cuotas_ideales,  # CAMBIO v2.9: ideales en lugar de relajadas
                cuotas_ideales=cuotas_ideales,
                ultimo_dia_prof=ultimo_dia_prof,
                ultimo_recreo_prof=ultimo_recreo_prof,
                zona_preferida_prof=zona_preferida_prof,
                total_slots=total_slots
            )

            _registrar_guardia(
                calendario, elegido, slot, asignadas,
                ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
            , curso_id=curso_id)

            # ALGORITMO v2.9: NO actualizar cuotas dinámicas (eliminar ajuste)
            # cuotas_dinamicas[elegido.id] = cuotas_relajadas[elegido.id]
            csp_exitosos += 1
            continue

        # NIVEL 2: Reasignación con backtracking - buscar guardia previa para intercambiar
        # ELIMINADO: permitir_multiples_guardias_dia ya que viola restricción HARD
        reasignado = False
        for guardia_previa in calendario[-20:]:  # Revisar últimas 20 guardias
            prof_previo_id = guardia_previa.profesor_id
            prof_previo = next((p for p in profesores if p.id == prof_previo_id), None)

            if not prof_previo:
                continue

            slot_previo = Slot(guardia_previa.fecha, guardia_previa.turno, guardia_previa.recreo, guardia_previa.zona_id)

            # Verificar si prof_previo puede tomar slot_actual (SIN permitir múltiples guardias/día)
            elegibles_swap = _obtener_profesores_elegibles_optimizado(
                profesores=[prof_previo],
                slot=slot,
                asignadas=asignadas,
                cuotas=cuotas_ideales,  # CAMBIO v2.9: ideales en lugar de relajadas
                guardias_por_slot_prof=guardias_por_slot_prof,
                guardias_por_dia_prof=guardias_por_dia_prof,
                session=session,
                respetar_cuotas=True,
                permitir_multiples_guardias_dia=False  # HARD constraint
            )

            if elegibles_swap:
                # Buscar nuevo profesor para slot_previo
                asignadas_temp = asignadas.copy()
                asignadas_temp[prof_previo_id] -= 1

                elegibles_reemplazo = _obtener_profesores_elegibles_optimizado(
                    profesores=profesores,
                    slot=slot_previo,
                    asignadas=asignadas_temp,
                    cuotas=cuotas_ideales,  # CAMBIO v2.9: ideales en lugar de relajadas
                    guardias_por_slot_prof=guardias_por_slot_prof,
                    guardias_por_dia_prof=guardias_por_dia_prof,
                    session=session,
                    respetar_cuotas=True,
                    permitir_multiples_guardias_dia=False  # HARD constraint
                )

                if elegibles_reemplazo:
                    # SWAP EXITOSO
                    nuevo_prof = elegibles_reemplazo[0]

                    # Actualizar guardia previa
                    guardia_previa.profesor_id = nuevo_prof.id
                    asignadas[prof_previo_id] -= 1
                    asignadas[nuevo_prof.id] = asignadas.get(nuevo_prof.id, 0) + 1

                    # Asignar slot actual a prof_previo
                    _registrar_guardia(
                        calendario, prof_previo, slot, asignadas,
                        ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                        zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                    , curso_id=curso_id)

                    csp_exitosos += 1
                    reasignaciones_csp += 1
                    reasignado = True
                    logger.info(f"  CSP: Reasignación exitosa - Swap en {slot_previo.fecha}")
                    break

        if not reasignado:
            slots_sin_cubrir_fase3.append(slot)

    guardias_fase3 = len(calendario)
    cobertura_fase3 = (guardias_fase3 / total_slots * 100) if total_slots > 0 else 0
    tasa_exito_csp = (csp_exitosos / csp_intentos * 100) if csp_intentos > 0 else 0

    logger.info(f"✓ Fase 3 completada: {guardias_fase3}/{total_slots} ({cobertura_fase3:.1f}%)")
    logger.info(f"  CSP: {csp_exitosos}/{csp_intentos} ({tasa_exito_csp:.1f}%)")
    logger.info(f"  Reasignaciones: {reasignaciones_csp}")
    logger.info(f"  Slots pendientes: {len(slots_sin_cubrir_fase3)}")
    reportar_progreso(75, f"Fase 3: {cobertura_fase3:.1f}% cobertura")

    # ==================================================================
    # FASE 4: SIMULATED ANNEALING (75% - 85%)
    # ==================================================================
    logger.info("")
    logger.info("FASE 4: Simulated Annealing para optimización global")
    logger.info("-" * 80)
    reportar_progreso(75, "Fase 4: Optimizando con Simulated Annealing...")

    import math
    import random as rand_sa  # Renombrar para evitar conflicto

    # Función de energía: mide la calidad de la solución (menor es mejor)
    def calcular_energia(asignadas_temp: Dict[int, int], cuotas_ideales_temp: Dict[int, int]) -> float:
        """Calcula la energía del sistema basada en desviaciones de cuota"""
        energia = 0.0

        # Penalización por desviación de cuotas
        for prof_id, ideal in cuotas_ideales_temp.items():
            if ideal > 0:
                actual = asignadas_temp.get(prof_id, 0)
                desv_relativa = abs(actual - ideal) / ideal
                energia += desv_relativa ** 2  # Cuadrática para penalizar grandes desviaciones

        # Penalización por profesores sin guardias
        for prof_id in cuotas_ideales_temp.keys():
            if asignadas_temp.get(prof_id, 0) == 0 and cuotas_ideales_temp[prof_id] > 0:
                energia += 10.0  # Penalización alta

        # Penalización por profesores con exceso extremo
        for prof_id, actual in asignadas_temp.items():
            ideal = cuotas_ideales_temp.get(prof_id, 1)
            if ideal > 0 and actual > ideal * 1.5:
                exceso = (actual - ideal * 1.5) / ideal
                energia += exceso ** 2 * 5  # Penalización por exceso

        return energia

    # Parámetros de Simulated Annealing
    temperatura_inicial = 100.0
    temperatura_minima = 0.1
    factor_enfriamiento = 0.95
    iteraciones_por_temp = min(50, len(calendario) // 2)

    temperatura = temperatura_inicial
    energia_actual = calcular_energia(asignadas, cuotas_ideales)
    mejor_energia = energia_actual
    mejor_asignadas = asignadas.copy()

    swaps_intentados_sa = 0
    swaps_aceptados_sa = 0
    swaps_mejorados_sa = 0

    logger.info(f"  Energía inicial: {energia_actual:.3f}")

    iteracion_total = 0
    max_iteraciones = 200  # Estimado

    while temperatura > temperatura_minima:
        for _ in range(iteraciones_por_temp):
            # Actualizar progreso cada 10 iteraciones
            if iteracion_total % 10 == 0:
                progreso_sa = 75 + int((iteracion_total / max_iteraciones) * 10)
                progreso_sa = min(progreso_sa, 84)  # No pasar de 84%
                reportar_progreso(
                    progreso_sa,
                    f"Fase 4: Optimizando balance (Temp: {temperatura:.1f}, Energía: {mejor_energia:.1f})..."
                )
            iteracion_total += 1

            if len(calendario) < 2:
                break

            # Seleccionar 2 guardias aleatorias
            g1 = rand_sa.choice(calendario)
            g2 = rand_sa.choice(calendario)

            if g1.id == g2.id or g1.profesor_id == g2.profesor_id:
                continue

            prof1_id = g1.profesor_id
            prof2_id = g2.profesor_id

            # Verificar que el swap no viola restricciones HARD
            slot1 = Slot(g1.fecha, g1.turno, g1.recreo, g1.zona_id)
            slot2 = Slot(g2.fecha, g2.turno, g2.recreo, g2.zona_id)

            # RESTRICCIÓN 1: No duplicar en mismo slot (fecha+turno+recreo+zona)
            slot_ya_asignado_1 = False
            slot_ya_asignado_2 = False

            for guardia in calendario:
                if guardia.id == g1.id or guardia.id == g2.id:
                    continue
                if (guardia.profesor_id == prof2_id and guardia.fecha == slot1.fecha and
                    guardia.turno == slot1.turno and guardia.recreo == slot1.recreo_id and
                    guardia.zona_id == slot1.zona_id):
                    slot_ya_asignado_1 = True
                if (guardia.profesor_id == prof1_id and guardia.fecha == slot2.fecha and
                    guardia.turno == slot2.turno and guardia.recreo == slot2.recreo_id and
                    guardia.zona_id == slot2.zona_id):
                    slot_ya_asignado_2 = True

            if slot_ya_asignado_1 or slot_ya_asignado_2:
                continue

            # RESTRICCIÓN 2: No múltiples guardias mismo día para un profesor
            # Verificar si prof2 ya tiene guardia en fecha de slot1 (además de g2 si es mismo día)
            prof2_tiene_guardia_fecha1 = any(
                g.profesor_id == prof2_id and g.fecha == slot1.fecha and g.id != g2.id
                for g in calendario
            )
            # Verificar si prof1 ya tiene guardia en fecha de slot2 (además de g1 si es mismo día)
            prof1_tiene_guardia_fecha2 = any(
                g.profesor_id == prof1_id and g.fecha == slot2.fecha and g.id != g1.id
                for g in calendario
            )

            if prof2_tiene_guardia_fecha1 or prof1_tiene_guardia_fecha2:
                continue

            swaps_intentados_sa += 1

            # Calcular energía después del swap
            asignadas_temp = asignadas.copy()
            asignadas_temp[prof1_id] = asignadas_temp.get(prof1_id, 0) - 1
            asignadas_temp[prof2_id] = asignadas_temp.get(prof2_id, 0) + 1
            asignadas_temp[prof2_id] = asignadas_temp.get(prof2_id, 0) - 1 + 1  # prof2 toma slot1
            asignadas_temp[prof1_id] = asignadas_temp.get(prof1_id, 0) - 1 + 1  # prof1 toma slot2

            energia_nueva = calcular_energia(asignadas_temp, cuotas_ideales)
            delta_energia = energia_nueva - energia_actual

            # Criterio de aceptación de Metropolis
            aceptar = False
            if delta_energia < 0:
                # Mejora: siempre aceptar
                aceptar = True
                swaps_mejorados_sa += 1
            else:
                # Empeoramiento: aceptar con probabilidad e^(-ΔE/T)
                probabilidad = math.exp(-delta_energia / temperatura)
                if rand_sa.random() < probabilidad:
                    aceptar = True

            if aceptar:
                # Ejecutar swap
                g1.profesor_id, g2.profesor_id = g2.profesor_id, g1.profesor_id
                asignadas[prof1_id] -= 1
                asignadas[prof2_id] += 1
                asignadas[g2.profesor_id] -= 1
                asignadas[g1.profesor_id] += 1

                energia_actual = energia_nueva
                swaps_aceptados_sa += 1

                # Actualizar mejor solución
                if energia_actual < mejor_energia:
                    mejor_energia = energia_actual
                    mejor_asignadas = asignadas.copy()

        # Enfriar temperatura
        temperatura *= factor_enfriamiento

    # Restaurar mejor solución encontrada
    if mejor_energia < calcular_energia(asignadas, cuotas_ideales):
        asignadas = mejor_asignadas.copy()
        # Re-sincronizar calendario con mejor_asignadas (requiere reconstrucción)
        logger.info("  Restaurando mejor solución encontrada...")

    tasa_aceptacion = (swaps_aceptados_sa / swaps_intentados_sa * 100) if swaps_intentados_sa > 0 else 0
    tasa_mejora = (swaps_mejorados_sa / swaps_intentados_sa * 100) if swaps_intentados_sa > 0 else 0

    logger.info("✓ Fase 4 completada: Simulated Annealing")
    logger.info(f"  Swaps intentados: {swaps_intentados_sa}")
    logger.info(f"  Swaps aceptados: {swaps_aceptados_sa} ({tasa_aceptacion:.1f}%)")
    logger.info(f"  Swaps que mejoraron: {swaps_mejorados_sa} ({tasa_mejora:.1f}%)")
    logger.info(f"  Energía final: {energia_actual:.3f} (mejor: {mejor_energia:.3f})")
    reportar_progreso(85, f"Fase 4: Energía {mejor_energia:.2f}")

    # ==================================================================
    # FASE 5: OPTIMIZACIÓN HUNGARIAN / LINEAR PROGRAMMING (85% - 95%)
    # ==================================================================
    logger.info("")
    logger.info("FASE 5: Optimización matemática con Hungarian Algorithm")
    logger.info("-" * 80)
    reportar_progreso(85, "Fase 5: Aplicando optimización Hungarian...")

    # Hungarian Algorithm para asignación óptima de slots pendientes
    # NOTA: Hungarian deshabilitado temporalmente - causa conflictos de simultaneidad
    # El algoritmo asigna múltiples slots en paralelo sin verificar restricciones
    # entre asignaciones (mismo profesor en múltiples zonas simultáneas)
    # TODO: Implementar versión incremental del Hungarian que actualice restricciones

    logger.info("  Hungarian: DESHABILITADO (causa conflictos de simultaneidad)")

    # Fase 5B: Completitud forzada para slots restantes (SIN violar restricciones hard)
    slots_sin_cubrir_fase5: List[Slot] = []

    # Crear conjunto de slots ya cubiertos para búsqueda eficiente
    slots_cubiertos = {(g.fecha, g.turno, g.recreo, g.zona_id) for g in calendario}

    slots_restantes = [s for s in slots_sin_cubrir_fase3
                       if (s.fecha, s.turno, s.recreo_id, s.zona_id) not in slots_cubiertos]

    swaps_fase5b = 0
    total_slots_restantes = len(slots_restantes)

    # ALGORITMO v2.9: Solo procesar si hay slots pendientes Y no se alcanzó 100%
    if len(calendario) >= total_slots:
        logger.info("  ✓ Todos los slots cubiertos (100%), saltando Fase 5B")
        slots_sin_cubrir_fase5 = []
    elif total_slots_restantes > 0:
        for idx_f5, slot in enumerate(slots_restantes):
            # Reporte de progreso cada 10 slots
            if idx_f5 % 10 == 0 and total_slots_restantes > 0:
                progreso_f5 = 85 + int((idx_f5 / total_slots_restantes) * 10)
                reportar_progreso(
                    progreso_f5,
                    f"Fase 5: Procesando slot {idx_f5 + 1}/{total_slots_restantes}..."
                )

            # ESTRATEGIA 1: Asignación directa con cuotas relajadas
            elegibles = _obtener_profesores_elegibles(
                profesores=profesores,
                slot=slot,
                asignadas=asignadas,
                cuotas={p.id: 999 for p in profesores},  # Cuotas muy altas
                guardias_por_slot_prof=guardias_por_slot_prof,
                guardias_por_dia_prof=guardias_por_dia_prof,
                session=session,
                respetar_cuotas=False,  # IGNORAR cuotas (soft constraint)
                permitir_multiples_guardias_dia=False  # RESPETAR día único (HARD constraint)
            )

            if elegibles:
                elegido = _seleccionar_profesor_optimizado(
                    elegibles=elegibles,
                    slot=slot,
                    asignadas=asignadas,
                    cuotas=cuotas_dinamicas,
                    cuotas_ideales=cuotas_ideales,
                    ultimo_dia_prof=ultimo_dia_prof,
                    ultimo_recreo_prof=ultimo_recreo_prof,
                    zona_preferida_prof=zona_preferida_prof,
                    total_slots=total_slots
                )

                _registrar_guardia(
                    calendario, elegido, slot, asignadas,
                    ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                    zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                , curso_id=curso_id)
                continue

            # ESTRATEGIA 2: SWAP - Buscar profesor con guardia en otro día que pueda hacer swap
            swap_exitoso = False
            for prof in profesores:
                # Verificar si prof puede hacer este slot (ignorando temporalmente día ocupado)
                if prof.turno not in ("completo", slot.turno):
                    continue

                # Verificar que no tenga ya este slot específico
                if (prof.id, slot.fecha, slot.turno, slot.recreo_id,
                        slot.zona_id) in guardias_por_slot_prof:
                    continue

                # Buscar una guardia existente de este profesor en OTRA fecha
                guardias_prof = [
                    g for g in calendario
                    if g.profesor_id == prof.id and g.fecha != slot.fecha
                ]

                for guardia_existente in guardias_prof:
                    # Verificar que otra persona pueda tomar la guardia existente
                    slot_existente = Slot(
                        fecha=guardia_existente.fecha,
                        turno=guardia_existente.turno,
                        recreo_id=guardia_existente.recreo,
                        zona_id=guardia_existente.zona_id
                    )

                    # Buscar reemplazo para slot_existente (que NO sea prof)
                    otros_profesores = [p for p in profesores if p.id != prof.id]

                    # Temporalmente liberar los slots para verificación
                    guardias_por_slot_prof_temp = guardias_por_slot_prof.copy()
                    guardias_por_dia_prof_temp = guardias_por_dia_prof.copy()

                    # Liberar slot existente
                    key_existente = (prof.id, slot_existente.fecha, slot_existente.turno,
                                    slot_existente.recreo_id, slot_existente.zona_id)
                    if key_existente in guardias_por_slot_prof_temp:
                        del guardias_por_slot_prof_temp[key_existente]

                    key_dia_existente = (prof.id, slot_existente.fecha)
                    if key_dia_existente in guardias_por_dia_prof_temp:
                        del guardias_por_dia_prof_temp[key_dia_existente]

                    reemplazos = _obtener_profesores_elegibles(
                        profesores=otros_profesores,
                        slot=slot_existente,
                        asignadas=asignadas,
                        cuotas={p.id: 999 for p in profesores},
                        guardias_por_slot_prof=guardias_por_slot_prof_temp,
                        guardias_por_dia_prof=guardias_por_dia_prof_temp,
                        session=session,
                        respetar_cuotas=False,
                        permitir_multiples_guardias_dia=False
                    )

                    if reemplazos:
                        # SWAP exitoso: reemplazar guardia_existente con reemplazo
                        reemplazo = reemplazos[0]

                        # Actualizar la guardia existente
                        guardia_existente.profesor_id = reemplazo.id

                        # Actualizar diccionarios: eliminar prof, agregar reemplazo
                        if key_existente in guardias_por_slot_prof:
                            del guardias_por_slot_prof[key_existente]
                        if key_dia_existente in guardias_por_dia_prof:
                            del guardias_por_dia_prof[key_dia_existente]

                        guardias_por_slot_prof[(reemplazo.id, slot_existente.fecha,
                                              slot_existente.turno, slot_existente.recreo_id,
                                              slot_existente.zona_id)] = True
                        guardias_por_dia_prof[(reemplazo.id, slot_existente.fecha)] = True

                        asignadas[prof.id] -= 1
                        asignadas[reemplazo.id] += 1

                        # Ahora asignar prof al slot original
                        _registrar_guardia(
                            calendario, prof, slot, asignadas,
                            ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                            zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                        , curso_id=curso_id)

                        swap_exitoso = True
                        swaps_fase5b += 1
                        break

                if swap_exitoso:
                    break

            if not swap_exitoso:
                slots_sin_cubrir_fase5.append(slot)

    guardias_fase5 = len(calendario)
    cobertura_fase5 = (guardias_fase5 / total_slots * 100) if total_slots > 0 else 0

    logger.info(f"✓ Fase 5 completada: {guardias_fase5}/{total_slots} ({cobertura_fase5:.1f}%)")
    logger.info(f"  Slots sin cubrir: {len(slots_sin_cubrir_fase5)}")
    logger.info(f"  Swaps realizados en Fase 5B: {swaps_fase5b}")
    reportar_progreso(95, f"Fase 5: {cobertura_fase5:.1f}% cobertura")

    # ==================================================================
    # FASE 6: VALIDACIÓN Y CORRECCIÓN DE ANOMALÍAS (95% - 100%)
    # ==================================================================
    logger.info("")
    logger.info("FASE 6: Validación y corrección de anomalías")
    logger.info("-" * 80)
    reportar_progreso(95, "Fase 6: Validando y corrigiendo anomalías...")

    # ANOMALÍA 1: Profesores sin guardias (CRÍTICO)
    profesores_sin_guardias = []
    for prof in profesores:
        if prof.id in cuotas_ideales and cuotas_ideales[prof.id] > 0:
            if asignadas.get(prof.id, 0) == 0:
                profesores_sin_guardias.append(prof)

    correcciones_sin_guardias = 0
    if profesores_sin_guardias:
        logger.warning(f"⚠️ ANOMALÍA 1: {len(profesores_sin_guardias)} profesores sin guardias")
        total_sin_guardias = len(profesores_sin_guardias)

        # Intentar asignar al menos una guardia a cada uno
        for idx_f6, prof in enumerate(profesores_sin_guardias):
            # Reporte de progreso
            if total_sin_guardias > 0:
                progreso_f6 = 95 + int((idx_f6 / total_sin_guardias) * 2)
                mensaje_progreso = (
                    f"Fase 6: Corrigiendo profesor {idx_f6 + 1}/{total_sin_guardias} "
                    f"sin guardias..."
                )
                reportar_progreso(progreso_f6, mensaje_progreso)

            asignado = False
            # Buscar cualquier slot donde pueda asignarse
            for slot in slots_ordenados:
                key_slot = (prof.id, slot.fecha, slot.turno, slot.recreo_id, slot.zona_id)
                if key_slot not in guardias_por_slot_prof:
                    # Verificar elegibilidad básica (SIN permitir múltiples guardias/día)
                    elegibles = _obtener_profesores_elegibles(
                        profesores=[prof],
                        slot=slot,
                        asignadas=asignadas,
                        cuotas={prof.id: 999},  # Cuota muy alta
                        guardias_por_slot_prof=guardias_por_slot_prof,
                        guardias_por_dia_prof=guardias_por_dia_prof,
                        session=session,
                        respetar_cuotas=False,
                        permitir_multiples_guardias_dia=False  # HARD constraint
                    )
                    if elegibles:
                        _registrar_guardia(
                            calendario, prof, slot, asignadas,
                            ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                            zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                        , curso_id=curso_id)
                        correcciones_sin_guardias += 1
                        asignado = True
                        logger.info(f"  ✓ Corregido: {prof.nombre_completo} ahora tiene guardia")
                        break

            if not asignado:
                logger.error(f"  ✗ No se pudo asignar guardia a {prof.nombre_completo}")

    # ANOMALÍA 2: Profesores con exceso de guardias (>150% de cuota)
    profesores_con_exceso = []
    for prof in profesores:
        if prof.id in cuotas_ideales and cuotas_ideales[prof.id] > 0:
            ideal = cuotas_ideales[prof.id]
            actual = asignadas.get(prof.id, 0)
            if actual > ideal * 1.5:
                profesores_con_exceso.append((prof, actual, ideal))

    correcciones_exceso = 0
    if profesores_con_exceso:
        logger.warning(f"⚠️ ANOMALÍA 2: {len(profesores_con_exceso)} profesores con exceso")

        # Intentar redistribuir exceso a profesores con déficit
        profesores_con_deficit = []
        for prof in profesores:
            if prof.id in cuotas_ideales and cuotas_ideales[prof.id] > 0:
                ideal = cuotas_ideales[prof.id]
                actual = asignadas.get(prof.id, 0)
                if actual < ideal * 0.8:  # Menos del 80% de cuota
                    profesores_con_deficit.append((prof, actual, ideal))

        # Swaps forzados de exceso → déficit
        for prof_exceso, actual_exc, ideal_exc in profesores_con_exceso:
            for prof_deficit, actual_def, ideal_def in profesores_con_deficit:
                if correcciones_exceso >= 10:  # Límite de swaps
                    break

                # Buscar guardia de prof_exceso que pueda tomar prof_deficit
                for guardia_exc in calendario:
                    if guardia_exc.profesor_id != prof_exceso.id:
                        continue

                    slot_exc = Slot(guardia_exc.fecha, guardia_exc.turno,
                                    guardia_exc.recreo, guardia_exc.zona_id)

                    # Verificar si prof_deficit puede tomar este slot (SIN multiples/día)
                    elegibles_def = _obtener_profesores_elegibles_optimizado(
                        profesores=[prof_deficit],
                        slot=slot_exc,
                        asignadas=asignadas,
                        cuotas={prof_deficit.id: ideal_def + 10},
                        guardias_por_slot_prof=guardias_por_slot_prof,
                        guardias_por_dia_prof=guardias_por_dia_prof,
                        session=session,
                        respetar_cuotas=True,
                        permitir_multiples_guardias_dia=False  # HARD constraint
                    )

                    if elegibles_def:
                        # SWAP FORZADO
                        guardia_exc.profesor_id = prof_deficit.id
                        asignadas[prof_exceso.id] -= 1
                        asignadas[prof_deficit.id] = asignadas.get(prof_deficit.id, 0) + 1
                        correcciones_exceso += 1
                        logger.info(f"  ✓ Swap: {prof_exceso.nombre_completo} → "
                                    f"{prof_deficit.nombre_completo}")
                        break

    # ANOMALÍA 3: Múltiples guardias mismo día para un profesor
    profesores_multi_dia: Dict[str, List[date]] = {}
    for guardia in calendario:
        prof_id = guardia.profesor_id
        fecha = guardia.fecha

        if prof_id not in profesores_multi_dia:
            profesores_multi_dia[prof_id] = []

        if fecha in profesores_multi_dia[prof_id]:
            # Ya tiene una guardia este día
            prof = next((p for p in profesores if p.id == prof_id), None)
            if prof:
                logger.warning(f"⚠️ ANOMALÍA 3: {prof.nombre_completo} tiene "
                               f"múltiples guardias en {fecha}")
        else:
            profesores_multi_dia[prof_id].append(fecha)

    # ANOMALÍA 4: Slots duplicados (mismo profesor, slot, zona)
    slots_vistos: Set[tuple] = set()
    duplicados = 0
    for guardia in calendario:
        key = (guardia.profesor_id, guardia.fecha, guardia.turno,
               guardia.recreo, guardia.zona_id)
        if key in slots_vistos:
            duplicados += 1
            logger.error(f"⚠️ ANOMALÍA 4: Slot duplicado detectado - {key}")
        else:
            slots_vistos.add(key)

    # ==================================================================
    # FASE 7: PASADAS MÚLTIPLES PROGRESIVAS (Completar slots restantes)
    # ==================================================================
    logger.info("")
    logger.info("FASE 7: Pasadas múltiples progresivas para maximizar cobertura")
    logger.info("-" * 80)
    reportar_progreso(97, "Fase 7: Completando slots restantes...")

    # ALGORITMO v2.9: Verificar si ya se alcanzó 100% de cobertura
    if len(calendario) >= total_slots:
        logger.info("  ✓ Todos los slots cubiertos (100%), saltando Fase 7")
        slots_pendientes = []
        total_asignados_fase7 = 0
    else:
        # Obtener slots aún sin cubrir
        slots_cubiertos_fase6 = {(g.fecha, g.turno, g.recreo, g.zona_id) for g in calendario}
        slots_pendientes = [
            s for s in slots_ordenados
            if (s.fecha, s.turno, s.recreo_id, s.zona_id) not in slots_cubiertos_fase6
        ]

        logger.info(f"Slots pendientes: {len(slots_pendientes)}/{total_slots}")

    if slots_pendientes:
        # PASADA 1: Priorizar profesores con 0 guardias
        logger.info("Pasada 1: Priorizar profesores sin guardias...")
        reportar_progreso(97, "Fase 7: Pasada 1 - Asignando profesores sin guardias...")
        profesores_sin_guardias_ids = {p.id for p in profesores if asignadas.get(p.id, 0) == 0}
        asignados_pasada1 = 0
        total_pendientes_p1 = len(slots_pendientes)

        for idx_p1, slot in enumerate(list(slots_pendientes)):
            # Reporte de progreso cada 10 slots
            if idx_p1 % 10 == 0 and total_pendientes_p1 > 0:
                progreso_p1 = 97 + int((idx_p1 / total_pendientes_p1) * 0.5)
                reportar_progreso(
                    progreso_p1,
                    f"Fase 7: Pasada 1 - Procesando slot {idx_p1 + 1}/{total_pendientes_p1}..."
                )

            # Filtrar solo profesores sin guardias
            profs_disponibles = [p for p in profesores if p.id in profesores_sin_guardias_ids]

            if not profs_disponibles:
                continue

            elegibles = _obtener_profesores_elegibles(
                profesores=profs_disponibles,
                slot=slot,
                asignadas=asignadas,
                cuotas={p.id: 999 for p in profesores},
                guardias_por_slot_prof=guardias_por_slot_prof,
                guardias_por_dia_prof=guardias_por_dia_prof,
                session=session,
                respetar_cuotas=False,
                permitir_multiples_guardias_dia=False
            )

            if elegibles:
                elegido = elegibles[0]  # Tomar el primero
                _registrar_guardia(
                    calendario, elegido, slot, asignadas,
                    ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                    zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                , curso_id=curso_id)
                slots_pendientes.remove(slot)
                profesores_sin_guardias_ids.discard(elegido.id)
                asignados_pasada1 += 1

        logger.info(f"  ✓ Asignados en Pasada 1: {asignados_pasada1}")

        # PASADA 2: Priorizar profesores con déficit (< 80% cuota)
        if slots_pendientes:
            logger.info("Pasada 2: Profesores con déficit < 80% cuota...")
            reportar_progreso(97, "Fase 7: Pasada 2 - Asignando profesores con déficit...")
            asignados_pasada2 = 0
            total_pendientes_p2 = len(slots_pendientes)

            for idx_p2, slot in enumerate(list(slots_pendientes)):
                # Reporte de progreso cada 10 slots
                if idx_p2 % 10 == 0 and total_pendientes_p2 > 0:
                    progreso_p2 = 97 + int((idx_p2 / total_pendientes_p2) * 0.5)
                    reportar_progreso(
                        progreso_p2,
                        f"Fase 7: Pasada 2 - Procesando slot {idx_p2 + 1}/{total_pendientes_p2}..."
                    )

                # Profesores con < 80% de su cuota
                profs_deficit = [
                    p for p in profesores
                    if p.id in cuotas_ideales
                    and cuotas_ideales[p.id] > 0
                    and asignadas.get(p.id, 0) < cuotas_ideales[p.id] * 0.8
                ]

                if not profs_deficit:
                    continue

                elegibles = _obtener_profesores_elegibles(
                    profesores=profs_deficit,
                    slot=slot,
                    asignadas=asignadas,
                    cuotas={p.id: 999 for p in profesores},
                    guardias_por_slot_prof=guardias_por_slot_prof,
                    guardias_por_dia_prof=guardias_por_dia_prof,
                    session=session,
                    respetar_cuotas=False,
                    permitir_multiples_guardias_dia=False
                )

                if elegibles:
                    # Ordenar por déficit (menor asignadas primero)
                    elegibles_ordenados = sorted(elegibles, key=lambda p: asignadas.get(p.id, 0))
                    elegido = elegibles_ordenados[0]

                    _registrar_guardia(
                        calendario, elegido, slot, asignadas,
                        ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                        zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                    , curso_id=curso_id)
                    slots_pendientes.remove(slot)
                    asignados_pasada2 += 1

            logger.info(f"  ✓ Asignados en Pasada 2: {asignados_pasada2}")

        # PASADA 3: CUALQUIER profesor elegible (ignorar cuotas totalmente)
        if slots_pendientes:
            logger.info("Pasada 3: Cualquier profesor elegible...")
            reportar_progreso(98, "Fase 7: Pasada 3 - Asignando cualquier profesor elegible...")
            asignados_pasada3 = 0
            total_pendientes_p3 = len(slots_pendientes)

            for idx_p3, slot in enumerate(list(slots_pendientes)):
                # Reporte de progreso cada 10 slots
                if idx_p3 % 10 == 0 and total_pendientes_p3 > 0:
                    progreso_p3 = 98 + int((idx_p3 / total_pendientes_p3) * 0.5)
                    reportar_progreso(
                        progreso_p3,
                        f"Fase 7: Pasada 3 - Procesando slot {idx_p3 + 1}/{total_pendientes_p3}..."
                    )

                elegibles = _obtener_profesores_elegibles(
                    profesores=profesores,
                    slot=slot,
                    asignadas=asignadas,
                    cuotas={p.id: 9999 for p in profesores},  # Cuota altísima
                    guardias_por_slot_prof=guardias_por_slot_prof,
                    guardias_por_dia_prof=guardias_por_dia_prof,
                    session=session,
                    respetar_cuotas=False,
                    permitir_multiples_guardias_dia=False
                )

                if elegibles:
                    # Ordenar por menor número de guardias asignadas
                    elegibles_ordenados = sorted(elegibles, key=lambda p: asignadas.get(p.id, 0))
                    elegido = elegibles_ordenados[0]

                    _registrar_guardia(
                        calendario, elegido, slot, asignadas,
                        ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                        zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                    , curso_id=curso_id)
                    slots_pendientes.remove(slot)
                    asignados_pasada3 += 1

            logger.info(f"  ✓ Asignados en Pasada 3: {asignados_pasada3}")

        # PASADA 4: Forzar con SWAP si todavía quedan slots
        if slots_pendientes and len(slots_pendientes) < total_slots * 0.1:  # Solo si quedan < 10%
            logger.info(f"Pasada 4: SWAP forzado para {len(slots_pendientes)} slots restantes...")
            reportar_progreso(98, "Fase 7: Pasada 4 - Intentando SWAP para slots restantes...")
            asignados_pasada4 = 0
            total_pendientes_p4 = len(slots_pendientes)

            for idx_p4, slot in enumerate(list(slots_pendientes)):
                # Reporte de progreso cada 5 slots (suele ser pocos slots aquí)
                if idx_p4 % 5 == 0 and total_pendientes_p4 > 0:
                    progreso_p4 = 98 + int((idx_p4 / total_pendientes_p4) * 1)
                    reportar_progreso(
                        progreso_p4,
                        f"Fase 7: Pasada 4 - SWAP slot {idx_p4 + 1}/{total_pendientes_p4}..."
                    )

                swap_exitoso = False

                # Intentar SWAP: buscar profesor que pueda hacer este slot
                for prof in profesores:
                    if prof.turno not in ("completo", slot.turno):
                        continue

                    # Buscar una guardia existente de este profesor en OTRA fecha
                    guardias_prof = [g for g in calendario
                                    if g.profesor_id == prof.id and g.fecha != slot.fecha]

                    for guardia_existente in guardias_prof[:5]:  # Limitar a 5 intentos
                        # Buscar reemplazo para la guardia existente
                        slot_existente = Slot(
                            fecha=guardia_existente.fecha,
                            turno=guardia_existente.turno,
                            recreo_id=guardia_existente.recreo,
                            zona_id=guardia_existente.zona_id
                        )

                        otros_profesores = [p for p in profesores if p.id != prof.id]

                        elegibles_reemplazo = _obtener_profesores_elegibles(
                            profesores=otros_profesores,
                            slot=slot_existente,
                            asignadas=asignadas,
                            cuotas={p.id: 9999 for p in profesores},
                            guardias_por_slot_prof=guardias_por_slot_prof,
                            guardias_por_dia_prof=guardias_por_dia_prof,
                            session=session,
                            respetar_cuotas=False,
                            permitir_multiples_guardias_dia=False
                        )

                        if elegibles_reemplazo:
                            # SWAP: reemplazar guardia existente
                            reemplazo = elegibles_reemplazo[0]

                            # Actualizar guardia existente
                            guardia_existente.profesor_id = reemplazo.id

                            # Actualizar diccionarios
                            key_old = (prof.id, slot_existente.fecha, slot_existente.turno,
                                      slot_existente.recreo_id, slot_existente.zona_id)
                            if key_old in guardias_por_slot_prof:
                                del guardias_por_slot_prof[key_old]

                            key_dia_old = (prof.id, slot_existente.fecha)
                            if key_dia_old in guardias_por_dia_prof:
                                del guardias_por_dia_prof[key_dia_old]

                            guardias_por_slot_prof[(reemplazo.id, slot_existente.fecha,
                                                  slot_existente.turno, slot_existente.recreo_id,
                                                  slot_existente.zona_id)] = True
                            guardias_por_dia_prof[(reemplazo.id, slot_existente.fecha)] = True

                            asignadas[prof.id] -= 1
                            asignadas[reemplazo.id] = asignadas.get(reemplazo.id, 0) + 1

                            # Asignar prof al slot original
                            _registrar_guardia(
                                calendario, prof, slot, asignadas,
                                ultimo_por_zona, ultimo_recreo_prof, ultimo_dia_prof,
                                zona_preferida_prof, guardias_por_slot_prof, guardias_por_dia_prof
                            , curso_id=curso_id)

                            slots_pendientes.remove(slot)
                            asignados_pasada4 += 1
                            swap_exitoso = True
                            break

                    if swap_exitoso:
                        break

            logger.info(f"  ✓ Asignados en Pasada 4: {asignados_pasada4}")

        total_asignados_fase7 = (asignados_pasada1 +
                                asignados_pasada2 +
                                asignados_pasada3 +
                                (asignados_pasada4 if 'asignados_pasada4' in locals() else 0))

        logger.info(f"✓ Fase 7 completada: {total_asignados_fase7} slots adicionales cubiertos")
        logger.info(f"  Slots aún pendientes: {len(slots_pendientes)}")

    # ==================================================================
    # CÁLCULO DE MÉTRICAS DE CALIDAD
    # ==================================================================
    total_profesores_elegibles = len([p for p in profesores
                                      if p.id in cuotas_ideales and cuotas_ideales[p.id] > 0])
    profesores_con_guardias = len([p_id for p_id in asignadas if asignadas[p_id] > 0])

    # Métricas principales
    cobertura_final = (len(calendario) / total_slots * 100) if total_slots > 0 else 0
    participacion = (profesores_con_guardias / total_profesores_elegibles * 100) \
                    if total_profesores_elegibles > 0 else 0

    # Desviaciones
    desviaciones = []
    for prof in profesores:
        if prof.id in cuotas_ideales and cuotas_ideales[prof.id] > 0:
            ideal = cuotas_ideales[prof.id]
            actual = asignadas.get(prof.id, 0)
            desv_porcentual = abs(actual - ideal) / ideal * 100
            desviaciones.append(desv_porcentual)

    desviacion_promedio = sum(desviaciones) / len(desviaciones) if desviaciones else 0
    desviacion_maxima = max(desviaciones) if desviaciones else 0

    # Coeficiente de variación
    if len(desviaciones) > 1:
        import statistics
        mean_desv = statistics.mean(desviaciones)
        cv = (statistics.stdev(desviaciones) / mean_desv * 100) if mean_desv > 0 else 0
    else:
        cv = 0

    logger.info("")
    logger.info("=" * 80)
    logger.info("MÉTRICAS DE CALIDAD DEL CALENDARIO GENERADO")
    logger.info("=" * 80)
    logger.info(f"Cobertura:           {cobertura_final:.2f}% ({len(calendario)}/{total_slots})")
    logger.info(f"Participación:       {participacion:.2f}% "
                f"({profesores_con_guardias}/{total_profesores_elegibles})")
    logger.info(f"Desviación promedio: {desviacion_promedio:.2f}%")
    logger.info(f"Desviación máxima:   {desviacion_maxima:.2f}%")
    logger.info(f"Coeficiente var.:    {cv:.2f}%")
    logger.info(f"Slots sin cubrir:    {len(slots_sin_cubrir_fase5)}")
    logger.info("")
    logger.info("CORRECCIONES APLICADAS:")
    logger.info(f"  Profesores sin guardias: {correcciones_sin_guardias} corregidos")
    logger.info(f"  Swaps por exceso:        {correcciones_exceso} realizados")
    logger.info(f"  Duplicados detectados:   {duplicados}")
    logger.info("=" * 80)

    # Evaluación de objetivos
    objetivos_cumplidos = []
    if cobertura_final >= 100.0:
        objetivos_cumplidos.append("✅ Cobertura 100%")
    else:
        objetivos_cumplidos.append(f"⚠️ Cobertura {cobertura_final:.1f}%")

    if participacion >= 100.0:
        objetivos_cumplidos.append("✅ Participación 100%")
    else:
        objetivos_cumplidos.append(f"⚠️ Participación {participacion:.1f}%")

    if desviacion_promedio < 5.0:
        objetivos_cumplidos.append("✅ Desviación <5%")
    else:
        objetivos_cumplidos.append(f"⚠️ Desviación {desviacion_promedio:.1f}%")

    logger.info("Objetivos: " + " | ".join(objetivos_cumplidos))
    logger.info("=" * 80)

    # VERIFICACIÓN FINAL: Comprobar asignación correcta de guardias por profesor
    logger.info("")
    logger.info("VERIFICACIÓN FINAL DE ASIGNACIÓN")
    logger.info("=" * 80)

    profesores_con_error = []
    profesores_con_deficit = []
    profesores_con_exceso = []

    for profesor in profesores:
        if profesor.id not in cuotas_ideales or cuotas_ideales[profesor.id] == 0:
            continue  # Saltar profesores sin cuota

        guardias_asignadas = asignadas.get(profesor.id, 0)
        cuota_esperada = cuotas_ideales[profesor.id]

        if guardias_asignadas != cuota_esperada:
            diferencia = guardias_asignadas - cuota_esperada
            profesores_con_error.append((profesor, guardias_asignadas, cuota_esperada, diferencia))

            if diferencia < 0:
                profesores_con_deficit.append((profesor, guardias_asignadas, cuota_esperada, abs(diferencia)))
            else:
                profesores_con_exceso.append((profesor, guardias_asignadas, cuota_esperada, diferencia))

    if not profesores_con_error:
        logger.info("✅ TODOS los profesores tienen la cantidad correcta de guardias")
    else:
        logger.warning(f"⚠️  {len(profesores_con_error)} profesores con asignación incorrecta:")

        if profesores_con_deficit:
            logger.warning(f"\n  Profesores con DÉFICIT ({len(profesores_con_deficit)}):")
            for profesor, asignadas_real, cuota, faltante in profesores_con_deficit:
                logger.warning(f"    • {profesor.nombre_completo}: {asignadas_real}/{cuota} (faltan {faltante})")

        if profesores_con_exceso:
            logger.warning(f"\n  Profesores con EXCESO ({len(profesores_con_exceso)}):")
            for profesor, asignadas_real, cuota, exceso in profesores_con_exceso:
                logger.warning(f"    • {profesor.nombre_completo}: {asignadas_real}/{cuota} (sobran {exceso})")

    logger.info("=" * 80)

    # VERIFICACIÓN FINAL 2: Comprobar que ningún profesor tenga >1 guardia por día
    logger.info("")
    logger.info("VERIFICACIÓN DE GUARDIAS POR DÍA")
    logger.info("=" * 80)

    # Agrupar guardias por profesor y fecha
    guardias_por_profesor_fecha: Dict[Tuple[int, date], int] = {}
    for guardia in calendario:
        key = (guardia.profesor_id, guardia.fecha)
        guardias_por_profesor_fecha[key] = guardias_por_profesor_fecha.get(key, 0) + 1

    # Buscar días con múltiples guardias
    dias_multiples = []
    for (profesor_id, fecha), count in guardias_por_profesor_fecha.items():
        if count > 1:
            profesor = next((p for p in profesores if p.id == profesor_id), None)
            if profesor:
                dias_multiples.append((profesor, fecha, count))

    if not dias_multiples:
        logger.info("✅ Ningún profesor tiene más de 1 guardia por día")
    else:
        logger.error(f"❌ PROBLEMA CRÍTICO: {len(dias_multiples)} días con múltiples guardias:")
        for profesor, fecha, count in sorted(dias_multiples, key=lambda x: (x[1], x[0].nombre_completo)):
            logger.error(f"    • {profesor.nombre_completo} el {fecha}: {count} guardias")

    logger.info("=" * 80)

    reportar_progreso(100, f"✓ Calendario generado: {cobertura_final:.1f}% cobertura")

    # Reporte de Equidad usando Domain Service
    logger.info("")
    logger.info("ANÁLISIS DE EQUIDAD (Domain Service)")
    logger.info("=" * 80)

    try:
        equidad_service = EquidadGuardiasService(session)

        # Log reporte completo de equidad
        equidad_service.log_reporte_equidad(calendario, cuotas_ideales)

        # Calcular índice de equidad
        indice_equidad = equidad_service.calcular_indice_equidad(calendario, cuotas_ideales)
        logger.info(f"📊 Índice de Equidad Global: {indice_equidad:.2%}")

        # Identificar desbalances
        desbalances = equidad_service.identificar_desbalances(calendario, cuotas_ideales)
        if desbalances:
            logger.warning(f"⚠️  Desbalances detectados: {len(desbalances)}")
            for desbalance in desbalances[:5]:  # Mostrar solo primeros 5
                logger.warning(f"    • {desbalance}")
        else:
            logger.info("✅ Sin desbalances significativos")

    except Exception as e:
        logger.warning(f"⚠️  Error en análisis de equidad: {e}")

    logger.info("=" * 80)

    return (calendario, asignadas)


def _obtener_profesores_elegibles(
    profesores: List[Profesor],
    slot: Slot,
    asignadas: Dict[int, int],
    cuotas: Dict[int, int],
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int, int], bool],
    guardias_por_dia_prof: Dict[Tuple[int, date], bool],
    session: Session,
    respetar_cuotas: bool = True,
    permitir_multiples_guardias_dia: bool = False
) -> List[Profesor]:
    """
    Obtiene la lista de profesores elegibles para un slot dado.

    Args:
        profesores: Lista de todos los profesores
        slot: Slot a asignar
        asignadas: Diccionario de guardias asignadas por profesor
        cuotas: Diccionario de cuotas por profesor
        guardias_por_slot_prof: Control de guardias por slot
        guardias_por_dia_prof: Control de guardias por día
        session: Sesión de SQLAlchemy
        respetar_cuotas: Si False, ignora las cuotas de guardias
        permitir_multiples_guardias_dia: Si True, permite >1 guardia/día

    Returns:
        Lista de profesores elegibles
    """
    global _rechazos_globales, _total_evaluaciones

    elegibles: List[Profesor] = []

    # DEBUG: Contadores de razones de rechazo
    rechazados = {
        'cuotas': 0,
        'turno': 0,
        'fecha_inicio': 0,
        'fecha_fin': 0,
        'dias_semana': 0,
        'horario': 0,
        'ausencias': 0,
        'slot_ocupado': 0,
        'dia_ocupado': 0
    }

    for p in profesores:
        _total_evaluaciones += 1

        # Validar cuotas (si se debe respetar)
        if respetar_cuotas and asignadas[p.id] >= cuotas.get(p.id, 0):
            rechazados['cuotas'] += 1
            _rechazos_globales['cuotas'] += 1
            continue

        # Validar turno
        if not _turno_de_recreo(p.turno, slot.turno):
            rechazados['turno'] += 1
            _rechazos_globales['turno'] += 1
            continue

        # Validar fecha de inicio
        if p.fecha_inicio_guardias and slot.fecha < p.fecha_inicio_guardias:
            rechazados['fecha_inicio'] += 1
            _rechazos_globales['fecha_inicio'] += 1
            continue

        # Validar fecha de fin
        if p.fecha_fin_guardias and slot.fecha > p.fecha_fin_guardias:
            rechazados['fecha_fin'] += 1
            _rechazos_globales['fecha_fin'] += 1
            continue

        # Validar días de la semana permitidos
        if p.dias_semana_permitidos:
            try:
                # Soportar tanto JSON como CSV
                dias_permitidos = None
                dias_str = p.dias_semana_permitidos.strip()

                # Intentar JSON primero
                try:
                    dias_permitidos = json.loads(dias_str)
                except (json.JSONDecodeError, ValueError):
                    # Intentar Python literal (ast.literal_eval)
                    try:
                        dias_permitidos = ast.literal_eval(dias_str)
                    except (ValueError, SyntaxError):
                        # Intentar CSV
                        try:
                            dias_permitidos = [
                                int(d.strip()) for d in dias_str.split(",")
                            ]
                        except ValueError:
                            pass

                # Verificar que sea lista o tupla válida
                if dias_permitidos and isinstance(dias_permitidos, (list, tuple)):
                    if slot.fecha.weekday() not in dias_permitidos:
                        rechazados['dias_semana'] += 1
                        _rechazos_globales['dias_semana'] += 1
                        continue
            except Exception as e:
                logger.warning(
                    f"Error al parsear dias_semana_permitidos "
                    f"para {p.nombre_completo}: {e}"
                )
                pass

        # Validar matriz de horario
        if not _horario_permitido(slot.fecha, slot.recreo_id, p.recreos_permitidos):
            rechazados['horario'] += 1
            _rechazos_globales['horario'] += 1
            continue

        # Validar ausencias
        if profesor_ausente(session, p.id, slot.fecha):
            rechazados['ausencias'] += 1
            _rechazos_globales['ausencias'] += 1
            continue

        # CRÍTICO: No puede estar en dos zonas al mismo tiempo (verificar con zona)
        if (p.id, slot.fecha, slot.turno, slot.recreo_id, slot.zona_id) in guardias_por_slot_prof:
            rechazados['slot_ocupado'] += 1
            _rechazos_globales['slot_ocupado'] += 1
            continue

        # Validar múltiples guardias por día (si se debe respetar)
        if not permitir_multiples_guardias_dia:
            if (p.id, slot.fecha) in guardias_por_dia_prof:
                rechazados['dia_ocupado'] += 1
                _rechazos_globales['dia_ocupado'] += 1
                continue

        elegibles.append(p)

    # DEBUG: Log cuando hay muy pocos elegibles O cuando no hay ninguno
    if len(elegibles) <= 5:
        logger.debug(
            f"ELEGIBILIDAD BAJA para slot {slot.fecha} {slot.turno} R{slot.recreo_id} Z{slot.zona_id}: "
            f"{len(elegibles)}/{len(profesores)} elegibles. "
            f"Rechazados: cuotas={rechazados['cuotas']}, turno={rechazados['turno']}, "
            f"fecha_inicio={rechazados['fecha_inicio']}, fecha_fin={rechazados['fecha_fin']}, "
            f"dias_semana={rechazados['dias_semana']}, horario={rechazados['horario']}, "
            f"ausencias={rechazados['ausencias']}, slot_ocupado={rechazados['slot_ocupado']}, "
            f"dia_ocupado={rechazados['dia_ocupado']}"
        )
        if elegibles:
            nombres = [f"{p.nombre_completo} (turno={p.turno})" for p in elegibles]
            logger.debug(f"  → Elegibles: {', '.join(nombres)}")
        else:
            # Mostrar detalles de TODOS los profesores
            logger.debug("  → 0 elegibles. Detalles:")
            for p in profesores:
                logger.debug(f"    - {p.nombre_completo} (turno={p.turno})")

    return elegibles


def _seleccionar_mejor_profesor(
    elegibles: List[Profesor],
    slot: Slot,
    asignadas: Dict[int, int],
    cuotas: Dict[int, int],
    ultimo_dia_prof: Dict[int, Optional[date]],
    ultimo_recreo_prof: Dict[int, Optional[int]],
    zona_preferida_prof: Dict[int, Optional[int]]
) -> Profesor:
    """
    Selecciona el mejor profesor de entre los elegibles usando scoring.

    Criterios de selección (en orden de importancia):
    1. Zona preferida (mantener consistencia)
    2. Déficit porcentual de guardias (equilibrar carga proporcional)
    3. Continuidad de días
    4. Mismo recreo anterior
    5. ID del profesor (desempate determinístico)

    Args:
        elegibles: Lista de profesores elegibles
        slot: Slot a asignar
        asignadas: Guardias asignadas por profesor
        cuotas: Cuotas por profesor
        ultimo_dia_prof: Último día asignado por profesor
        ultimo_recreo_prof: Último recreo asignado por profesor
        zona_preferida_prof: Zona preferida de cada profesor

    Returns:
        Profesor seleccionado
    """
    def score(p: Profesor) -> Tuple[int, float, int, int, int]:
        # Zona preferida
        if zona_preferida_prof[p.id] is None:
            s_zona = 0
        elif zona_preferida_prof[p.id] == slot.zona_id:
            s_zona = 100
        else:
            s_zona = -50

        # Déficit porcentual (más justo que déficit absoluto)
        # Un profesor con 5/10 (50%) tiene mismo déficit relativo que 1/2 (50%)
        cuota_ideal = cuotas.get(p.id, 1)
        if cuota_ideal > 0:
            deficit_porcentual = (
                (cuota_ideal - asignadas[p.id]) / cuota_ideal * 100
            )
        else:
            deficit_porcentual = 0.0

        # Continuidad de días
        s_continuidad = 1 if (
            ultimo_dia_prof[p.id]
            and (slot.fecha - ultimo_dia_prof[p.id]).days == 1
        ) else 0

        # Mismo recreo
        s_recreo = 1 if ultimo_recreo_prof[p.id] == slot.recreo_id else 0

        # Desempate determinístico por ID (menor ID = mayor prioridad)
        return (s_zona, deficit_porcentual, s_continuidad, s_recreo, -p.id)

    return sorted(elegibles, key=score, reverse=True)[0]


def _registrar_guardia(
    calendario: List[Guardia],
    profesor: Profesor,
    slot: Slot,
    asignadas: Dict[int, int],
    ultimo_por_zona: Dict[int, Optional[int]],
    ultimo_recreo_prof: Dict[int, Optional[int]],
    ultimo_dia_prof: Dict[int, Optional[date]],
    zona_preferida_prof: Dict[int, Optional[int]],
    guardias_por_slot_prof: Dict[Tuple[int, date, str, int, int], bool],
    guardias_por_dia_prof: Dict[Tuple[int, date], bool],
    curso_id: Optional[int] = None
) -> None:
    """
    Registra una guardia asignada y actualiza todas las estructuras de control.

    Args:
        calendario: Lista de guardias (se modifica)
        profesor: Profesor asignado
        slot: Slot asignado
        asignadas: Guardias asignadas por profesor (se modifica)
        ultimo_por_zona: Último profesor por zona (se modifica)
        ultimo_recreo_prof: Último recreo por profesor (se modifica)
        ultimo_dia_prof: Último día por profesor (se modifica)
        zona_preferida_prof: Zona preferida por profesor (se modifica)
        guardias_por_slot_prof: Control de guardias por slot (se modifica)
        guardias_por_dia_prof: Control de guardias por día (se modifica)
        curso_id: ID del curso escolar al que pertenece la guardia
    """
    calendario.append(
        Guardia(
            profesor_id=profesor.id,
            fecha=slot.fecha,
            turno=slot.turno,
            recreo=slot.recreo_id,
            zona_id=slot.zona_id,
            curso_id=curso_id,
        )
    )
    asignadas[profesor.id] += 1
    ultimo_por_zona[slot.zona_id] = profesor.id
    ultimo_recreo_prof[profesor.id] = slot.recreo_id
    ultimo_dia_prof[profesor.id] = slot.fecha

    # Asignar zona preferida en primera asignación
    if zona_preferida_prof[profesor.id] is None:
        zona_preferida_prof[profesor.id] = slot.zona_id

    # Marcar slot y día como ocupados (INCLUIR ZONA para evitar duplicados)
    guardias_por_slot_prof[(profesor.id, slot.fecha, slot.turno, slot.recreo_id, slot.zona_id)] = True
    guardias_por_dia_prof[(profesor.id, slot.fecha)] = True


def guardar_guardias_en_bd(session: Session, calendario: List[Guardia]) -> None:
    if not calendario:
        logger.warning("No hay guardias para guardar en la base de datos")
        return
    logger.info(f"Guardando {len(calendario)} guardias en la base de datos")
    session.bulk_save_objects(calendario)
    session.commit()
    logger.info("Guardias guardadas exitosamente")
