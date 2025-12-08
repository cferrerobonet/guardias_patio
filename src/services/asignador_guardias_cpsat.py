"""
Asignador de Guardias con CP-SAT (Constraint Programming - SAT)
===============================================================

Este módulo implementa un asignador de guardias usando el solver CP-SAT
de Google OR-Tools. Garantiza encontrar la solución ÓPTIMA matemáticamente.

CARACTERÍSTICAS:
- Garantiza cobertura 100% (si es factible)
- Minimiza la inequidad de forma óptima
- Considera TODAS las restricciones: turno, recreos, ausencias, etc.
- Tiempo típico de resolución: 5-15 segundos

COMPARATIVA CON v4 HÍBRIDO:
- v4 Híbrido: Rápido (~1s), heurístico, puede no alcanzar el óptimo
- CP-SAT: Más lento (~10s), pero garantiza la solución óptima

USO:
    from services.asignador_guardias_cpsat import generar_guardias_cpsat

    guardias, resumen = generar_guardias_cpsat(session, progress_callback)
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Dict, List, Optional, Set, Tuple

from domain.services.distribucion_cuotas_service import DistribucionCuotasService
from infrastructure.database.models import (
    Ausencia,
    Configuracion,
    Guardia,
    Profesor,
    Zona,
)
from ortools.sat.python import cp_model
from services.calculador_guardias import (
    _parse_recreos_config,
    listar_dias_lectivos,
)
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================


@dataclass(frozen=True)
class Slot:
    """Unidad atómica de asignación: una guardia en un momento y lugar específico."""

    fecha: date
    turno: str  # "mañana" | "tarde"
    recreo_id: int
    zona_id: int

    def __hash__(self):
        return hash((self.fecha, self.turno, self.recreo_id, self.zona_id))


@dataclass
class ResultadoCPSAT:
    """Resultado de la generación con CP-SAT."""

    guardias: List[Guardia]
    resumen_por_profesor: Dict[int, int]

    # Métricas
    total_slots: int = 0
    slots_cubiertos: int = 0
    cobertura: float = 0.0

    # Métricas de equidad
    indice_equidad: float = 0.0
    max_desviacion: float = 0.0
    desviacion_media: float = 0.0

    # Información del solver
    es_optimo: bool = False
    tiempo_resolucion: float = 0.0
    soluciones_exploradas: int = 0

    errores: List[str] = field(default_factory=list)


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================


def _generar_recreos_fallback(config: Configuracion) -> List[dict]:
    """Genera recreos a partir de los campos de hora si recreos_config está vacío."""
    recreos = []
    rid = 0

    if config.hora_recreo1_manana:
        rid += 1
        recreos.append({"id": rid, "turno": "mañana", "etiqueta": "R1 Mañana"})
    if config.hora_recreo2_manana:
        rid += 1
        recreos.append({"id": rid, "turno": "mañana", "etiqueta": "R2 Mañana"})
    if config.hora_recreo1_tarde:
        rid += 1
        recreos.append({"id": rid, "turno": "tarde", "etiqueta": "R1 Tarde"})
    if config.hora_recreo2_tarde:
        rid += 1
        recreos.append({"id": rid, "turno": "tarde", "etiqueta": "R2 Tarde"})

    return recreos


def _generar_slots(config: Configuracion, session: Session) -> List[Slot]:
    """Genera todos los slots a cubrir."""
    dias_lectivos = listar_dias_lectivos(config)
    zonas = session.query(Zona).all()
    recreos = _parse_recreos_config(config)

    if not recreos:
        recreos = _generar_recreos_fallback(config)

    if not dias_lectivos or not zonas or not recreos:
        logger.warning(
            f"Datos insuficientes: {len(dias_lectivos)} días, "
            f"{len(zonas)} zonas, {len(recreos)} recreos"
        )
        return []

    slots = []
    zonas_ids = [z.id for z in zonas]
    zonas_dict = {z.id: z for z in zonas}

    for dia in dias_lectivos:
        for recreo in recreos:
            num_zonas_recreo = min(recreo.get("zonas", len(zonas)), len(zonas))

            for i in range(num_zonas_recreo):
                if i >= len(zonas_ids):
                    break
                zona_id = zonas_ids[i]
                zona = zonas_dict[zona_id]

                if zona.fecha_inicio and dia < zona.fecha_inicio:
                    continue
                if zona.fecha_fin and dia > zona.fecha_fin:
                    continue

                slots.append(
                    Slot(
                        fecha=dia,
                        turno=recreo.get("turno", "mañana"),
                        recreo_id=int(recreo["id"]),
                        zona_id=zona.id,
                    )
                )

    return slots


def _profesor_ausente(session: Session, profesor_id: int, fecha: date) -> bool:
    """Verifica si un profesor tiene ausencia activa en una fecha."""
    return (
        session.query(Ausencia)
        .filter(
            Ausencia.profesor_id == profesor_id,
            Ausencia.fecha_inicio <= fecha,
            Ausencia.fecha_fin >= fecha,
            Ausencia.activa == True,  # noqa: E712
        )
        .first()
        is not None
    )


def _parse_json_field(value: Optional[str], default: list) -> list:
    """Parsea un campo JSON de forma segura."""
    if not value:
        return default
    try:
        result = json.loads(value)
        return result if isinstance(result, (list, dict)) else default
    except (json.JSONDecodeError, TypeError):
        return default


def _es_elegible_basico(profesor: Profesor, slot: Slot, session: Session) -> bool:
    """
    Verifica si un profesor puede cubrir un slot (restricciones HARD).

    Estas restricciones NUNCA se relajan:
    1. Turno compatible
    2. No ausente
    3. Fecha en rango del profesor
    4. Recreo permitido
    """
    # 1. TURNO COMPATIBLE
    if profesor.turno and profesor.turno not in ("completo", "mixto", "ambos"):
        if profesor.turno != slot.turno:
            return False

    # 2. NO AUSENTE
    if _profesor_ausente(session, profesor.id, slot.fecha):
        return False

    # 3. FECHA EN RANGO
    if profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias:
        return False
    if profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias:
        return False

    # 4. RECREO PERMITIDO
    recreos_permitidos = _parse_json_field(profesor.recreos_permitidos, [1, 2, 3, 4])
    if isinstance(recreos_permitidos, dict):
        dia_key = str(slot.fecha.weekday())
        recreos_del_dia = recreos_permitidos.get(dia_key, [])
        if slot.recreo_id not in recreos_del_dia:
            return False
    elif isinstance(recreos_permitidos, list):
        if slot.recreo_id not in recreos_permitidos:
            return False

    return True


# =============================================================================
# CALLBACK DE PROGRESO PARA EL SOLVER
# =============================================================================


class SolverCallback(cp_model.CpSolverSolutionCallback):
    """Callback para reportar progreso durante la resolución."""

    def __init__(
        self,
        variables: Dict,
        cuotas_ideales: Dict[int, float],
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        super().__init__()
        self.variables = variables
        self.cuotas_ideales = cuotas_ideales
        self.progress_callback = progress_callback
        self.solution_count = 0
        self.best_objective = float("inf")

    def on_solution_callback(self):
        self.solution_count += 1
        current_obj = self.ObjectiveValue()

        if current_obj < self.best_objective:
            self.best_objective = current_obj

            if self.progress_callback:
                # Estimar progreso basado en mejora del objetivo
                progreso = min(85, 40 + self.solution_count * 2)
                self.progress_callback(
                    progreso, f"Solución {self.solution_count}: obj={current_obj}"
                )


# =============================================================================
# FUNCIÓN PRINCIPAL: GENERADOR CP-SAT
# =============================================================================


def generar_guardias_cpsat(
    session: Session,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    timeout_seconds: float = 120.0,
    use_hints: bool = True,
) -> Tuple[List[Guardia], Dict[int, int]]:
    """
    Genera el calendario de guardias usando CP-SAT de OR-Tools.

    Este algoritmo GARANTIZA encontrar la solución óptima (si existe)
    minimizando la inequidad entre profesores.

    Args:
        session: Sesión de SQLAlchemy
        progress_callback: Callback para reportar progreso (porcentaje, mensaje)
        timeout_seconds: Tiempo máximo de resolución (default: 120s)
        use_hints: Si True, genera una solución greedy como hint inicial

    Returns:
        Tupla (lista de guardias, diccionario profesor_id -> guardias_asignadas)
    """

    def reportar(porcentaje: int, mensaje: str = ""):
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except Exception as e:
                logger.warning(f"Error en callback de progreso: {e}")

    logger.info("=" * 80)
    logger.info("ALGORITMO CP-SAT - GENERACIÓN ÓPTIMA DE GUARDIAS")
    logger.info("=" * 80)

    reportar(0, "Iniciando generación con CP-SAT...")

    # =========================================================================
    # FASE 1: PREPARACIÓN DE DATOS
    # =========================================================================
    logger.info("")
    logger.info("FASE 1: PREPARACIÓN DE DATOS")
    logger.info("-" * 80)
    reportar(5, "Cargando configuración...")

    config = session.query(Configuracion).first()
    if not config:
        raise ValueError("No existe configuración del curso")

    # Curso activo
    from services.gestor_cursos import GestorCursos

    curso_activo = GestorCursos.obtener_curso_activo(session)
    curso_id = curso_activo.id if curso_activo else None

    # Profesores activos
    reportar(8, "Cargando profesores...")
    profesores = session.query(Profesor).filter(Profesor.activo == True).all()  # noqa: E712
    if not profesores:
        raise ValueError("No hay profesores activos")

    # Generar slots
    reportar(10, "Generando slots...")
    slots = _generar_slots(config, session)
    if not slots:
        raise ValueError("No se pudieron generar slots")

    logger.info(f"  ✓ {len(profesores)} profesores activos")
    logger.info(f"  ✓ {len(slots)} slots a cubrir")

    # =========================================================================
    # FASE 2: PRE-CÁLCULO DE ELEGIBILIDAD
    # =========================================================================
    logger.info("")
    logger.info("FASE 2: PRE-CÁLCULO DE ELEGIBILIDAD")
    logger.info("-" * 80)
    reportar(15, "Calculando elegibilidad...")

    # prof_slots[prof_id] = lista de índices de slots elegibles
    prof_slots: Dict[int, List[int]] = {p.id: [] for p in profesores}
    # slot_profs[slot_idx] = lista de prof_ids elegibles
    slot_profs: Dict[int, List[int]] = {i: [] for i in range(len(slots))}

    for p in profesores:
        for i, slot in enumerate(slots):
            if _es_elegible_basico(p, slot, session):
                prof_slots[p.id].append(i)
                slot_profs[i].append(p.id)

    total_elegibles = sum(len(v) for v in prof_slots.values())
    logger.info(
        f"  ✓ {total_elegibles} asignaciones elegibles "
        f"({100*total_elegibles/(len(profesores)*len(slots)):.1f}%)"
    )

    # Verificar que todos los slots tienen al menos un profesor
    slots_sin_cobertura = [i for i in range(len(slots)) if not slot_profs[i]]
    if slots_sin_cobertura:
        logger.error(f"  ⚠️ {len(slots_sin_cobertura)} slots sin profesores elegibles")
        # Podríamos lanzar error o continuar con cobertura parcial

    # =========================================================================
    # FASE 3: CREAR MODELO CP-SAT
    # =========================================================================
    logger.info("")
    logger.info("FASE 3: CREANDO MODELO CP-SAT")
    logger.info("-" * 80)
    reportar(20, "Creando modelo...")

    model = cp_model.CpModel()

    # Variables: x[(prof_id, slot_idx)] = 1 si profesor cubre slot
    x: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for p in profesores:
        for s_idx in prof_slots[p.id]:
            x[(p.id, s_idx)] = model.NewBoolVar(f"x_{p.id}_{s_idx}")

    logger.info(f"  ✓ {len(x)} variables booleanas creadas")

    # -------------------------------------------------------------------------
    # RESTRICCIÓN 1: Cada slot debe tener exactamente 1 profesor
    # -------------------------------------------------------------------------
    for s_idx in range(len(slots)):
        profs_elegibles = slot_profs[s_idx]
        if profs_elegibles:
            model.AddExactlyOne(x[(p_id, s_idx)] for p_id in profs_elegibles)

    logger.info("  ✓ Restricción: cada slot = 1 profesor")

    # -------------------------------------------------------------------------
    # RESTRICCIÓN 2: Máximo 1 guardia por día por profesor
    # -------------------------------------------------------------------------
    slots_por_dia: Dict[Tuple[int, date], List[int]] = defaultdict(list)
    for p in profesores:
        for s_idx in prof_slots[p.id]:
            fecha = slots[s_idx].fecha
            slots_por_dia[(p.id, fecha)].append(s_idx)

    for (p_id, _fecha), slot_idxs in slots_por_dia.items():
        if len(slot_idxs) > 1:
            model.AddAtMostOne(x[(p_id, s_idx)] for s_idx in slot_idxs)

    logger.info("  ✓ Restricción: máx 1 guardia/día/profesor")

    # -------------------------------------------------------------------------
    # RESTRICCIÓN 3: No simultaneidad (mismo recreo = mismo momento)
    # -------------------------------------------------------------------------
    slots_simultaneos: Dict[Tuple[int, date, str, int], List[int]] = defaultdict(list)
    for p in profesores:
        for s_idx in prof_slots[p.id]:
            slot = slots[s_idx]
            key = (p.id, slot.fecha, slot.turno, slot.recreo_id)
            slots_simultaneos[key].append(s_idx)

    for key, slot_idxs in slots_simultaneos.items():
        if len(slot_idxs) > 1:
            p_id = key[0]
            model.AddAtMostOne(x[(p_id, s_idx)] for s_idx in slot_idxs)

    logger.info("  ✓ Restricción: no simultaneidad (1 zona/recreo)")

    # =========================================================================
    # FASE 4: DEFINIR OBJETIVO (MINIMIZAR INEQUIDAD)
    # =========================================================================
    logger.info("")
    logger.info("FASE 4: DEFINIENDO OBJETIVO")
    logger.info("-" * 80)
    reportar(25, "Definiendo objetivo de equidad...")

    # Calcular cuotas ideales usando el servicio de distribución
    # Esto considera correctamente los turnos de cada profesor
    cuotas_service = DistribucionCuotasService(session)
    cuotas_ideales_int = cuotas_service.calcular_cuotas(profesores)
    cuotas_ideales: Dict[int, float] = {
        p_id: float(cuota) for p_id, cuota in cuotas_ideales_int.items()
    }
    logger.info(f"  ✓ Cuotas calculadas por turno (suma={sum(cuotas_ideales.values()):.0f})")

    # Variable auxiliar: número de guardias por profesor
    n_guardias: Dict[int, cp_model.IntVar] = {}
    for p in profesores:
        if prof_slots[p.id]:
            n_guardias[p.id] = model.NewIntVar(0, len(prof_slots[p.id]), f"n_{p.id}")
            model.Add(
                n_guardias[p.id] == sum(x[(p.id, s_idx)] for s_idx in prof_slots[p.id])
            )
        else:
            n_guardias[p.id] = model.NewIntVar(0, 0, f"n_{p.id}")

    # Desviación de cada profesor respecto a su cuota
    desviaciones: List[cp_model.IntVar] = []
    for p in profesores:
        cuota = int(round(cuotas_ideales[p.id]))
        if prof_slots[p.id]:
            dev = model.NewIntVar(0, 50, f"dev_{p.id}")
            model.Add(dev >= n_guardias[p.id] - cuota)
            model.Add(dev >= cuota - n_guardias[p.id])
            desviaciones.append(dev)

    # Máxima desviación
    max_dev = model.NewIntVar(0, 50, "max_dev")
    model.AddMaxEquality(max_dev, desviaciones)

    # Objetivo: minimizar max_dev prioritariamente, luego suma de desviaciones
    # El factor 10000 asegura que primero se minimice max_dev
    model.Minimize(10000 * max_dev + sum(desviaciones))

    logger.info("  ✓ Objetivo: minimizar max_desviación + sum(desviaciones)")

    # =========================================================================
    # FASE 5: GENERAR HINTS (SOLUCIÓN INICIAL GREEDY)
    # =========================================================================
    if use_hints:
        logger.info("")
        logger.info("FASE 5: GENERANDO HINTS (Greedy)")
        logger.info("-" * 80)
        reportar(30, "Generando solución inicial...")

        asig_greedy: Dict[int, int] = {p.id: 0 for p in profesores}
        slot_asignado: Dict[int, int] = {}
        guardias_por_dia_greedy: Dict[Tuple[int, date], Set[int]] = defaultdict(set)
        momento_ocupado: Set[Tuple[int, date, str, int]] = set()

        for s_idx in range(len(slots)):
            slot = slots[s_idx]
            candidatos = []
            for p_id in slot_profs[s_idx]:
                # Max 1/día
                if guardias_por_dia_greedy[(p_id, slot.fecha)]:
                    continue
                # No simultaneidad
                momento = (p_id, slot.fecha, slot.turno, slot.recreo_id)
                if momento in momento_ocupado:
                    continue
                candidatos.append(p_id)

            if candidatos:
                # Elegir el de menor asignación normalizada
                mejor = min(
                    candidatos,
                    key=lambda pid: asig_greedy[pid] / max(cuotas_ideales[pid], 0.1),
                )
                slot_asignado[s_idx] = mejor
                asig_greedy[mejor] += 1
                guardias_por_dia_greedy[(mejor, slot.fecha)].add(s_idx)
                momento = (mejor, slot.fecha, slot.turno, slot.recreo_id)
                momento_ocupado.add(momento)

        # Aplicar hints al modelo
        for s_idx, p_id in slot_asignado.items():
            model.AddHint(x[(p_id, s_idx)], 1)

        logger.info(f"  ✓ Hint greedy: {len(slot_asignado)}/{len(slots)} slots")

    # =========================================================================
    # FASE 6: RESOLVER
    # =========================================================================
    logger.info("")
    logger.info("FASE 6: RESOLVIENDO CON CP-SAT")
    logger.info("-" * 80)
    reportar(35, "Resolviendo modelo...")

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    solver.parameters.num_search_workers = 8  # Usar múltiples cores
    solver.parameters.linearization_level = 2
    solver.parameters.cp_model_presolve = True

    # Callback para progreso
    callback = SolverCallback(x, cuotas_ideales, progress_callback)

    status = solver.Solve(model, callback)

    # =========================================================================
    # FASE 7: PROCESAR RESULTADO
    # =========================================================================
    logger.info("")
    logger.info("FASE 7: PROCESANDO RESULTADO")
    logger.info("-" * 80)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logger.error(f"❌ No se encontró solución (status: {status})")
        raise ValueError(
            f"CP-SAT no encontró solución. Status: {status}. "
            "Verifique que hay suficientes profesores para cubrir todos los slots."
        )

    es_optimo = status == cp_model.OPTIMAL
    status_str = "ÓPTIMA" if es_optimo else "FACTIBLE"
    logger.info(f"✅ Solución {status_str} encontrada")
    logger.info(f"   Tiempo: {solver.WallTime():.2f} segundos")
    logger.info(f"   Soluciones exploradas: {callback.solution_count}")

    reportar(90, "Generando guardias...")

    # Extraer asignaciones
    asignaciones: Dict[int, int] = {
        p.id: solver.Value(n_guardias[p.id]) for p in profesores
    }

    # Crear objetos Guardia
    guardias: List[Guardia] = []
    for (p_id, s_idx), var in x.items():
        if solver.Value(var) == 1:
            slot = slots[s_idx]
            guardia = Guardia(
                profesor_id=p_id,
                fecha=slot.fecha,
                turno=slot.turno,
                recreo=slot.recreo_id,
                zona_id=slot.zona_id,
                curso_id=curso_id,
            )
            guardias.append(guardia)

    # =========================================================================
    # FASE 8: MÉTRICAS FINALES
    # =========================================================================
    logger.info("")
    logger.info("MÉTRICAS FINALES")
    logger.info("-" * 80)

    diferencias = [asignaciones[p.id] - cuotas_ideales[p.id] for p in profesores]
    max_desviacion = max(abs(d) for d in diferencias)
    desviacion_media = sum(abs(d) for d in diferencias) / len(diferencias)
    suma_desv = sum(abs(d) for d in diferencias)
    suma_cuotas = sum(cuotas_ideales.values())
    indice_equidad = 100 * (1 - suma_desv / suma_cuotas)

    logger.info(f"  Total guardias: {len(guardias)} / {len(slots)}")
    logger.info(f"  Índice de Equidad: {indice_equidad:.1f}%")
    logger.info(f"  Máxima desviación: {max_desviacion:.1f} guardias")
    logger.info(f"  Desviación media: {desviacion_media:.2f} guardias")
    logger.info(f"  Solución óptima: {'SÍ' if es_optimo else 'NO (tiempo agotado)'}")

    opt_str = 'Óptimo' if es_optimo else 'Factible'
    reportar(100, f"✅ Completado: IE={indice_equidad:.1f}% ({opt_str})")

    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ ALGORITMO CP-SAT COMPLETADO")
    logger.info("=" * 80)

    return (guardias, asignaciones)


def guardar_guardias_cpsat_en_bd(session: Session, guardias: List[Guardia]) -> None:
    """
    Guarda las guardias generadas por CP-SAT en la base de datos.

    Args:
        session: Sesión de SQLAlchemy
        guardias: Lista de guardias a guardar
    """
    try:
        for guardia in guardias:
            if guardia not in session:
                session.add(guardia)
        session.commit()
        logger.info(f"✓ {len(guardias)} guardias guardadas en BD")
    except Exception as e:
        session.rollback()
        logger.error(f"Error al guardar guardias: {e}")
        raise
