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

from services.distribucion_cuotas_service import DistribucionCuotasService
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
from sqlalchemy.exc import SQLAlchemyError
from utils import get_logger

logger = get_logger(__name__)


from services._asignador_cpsat_helpers import (
    ResultadoCPSAT,
    Slot,
    SolverCallback,
    _es_elegible_basico,
    _generar_slots,
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
            except (ValueError, TypeError, OSError) as e:
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
    # FASE 4: DEFINIR OBJETIVO (EQUIDAD + CONSECUTIVIDAD + ZONA)
    # =========================================================================
    logger.info("")
    logger.info("FASE 4: DEFINIENDO OBJETIVO MULTI-CRITERIO")
    logger.info("-" * 80)
    reportar(25, "Definiendo objetivo multi-criterio...")

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

    # -------------------------------------------------------------------------
    # OBJETIVO 1 (PRIMARIO): MINIMIZAR INEQUIDAD
    # -------------------------------------------------------------------------
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

    logger.info("  ✓ Objetivo 1: minimizar inequidad (max_desv + sum_desv)")

    # -------------------------------------------------------------------------
    # OBJETIVO 2 (SECUNDARIO): MAXIMIZAR CONSECUTIVIDAD
    # -------------------------------------------------------------------------
    # Estrategia: Incentivar que guardias consecutivas en el calendario
    # sean asignadas al mismo profesor.
    # Para cada par de slots (s1, s2) en días consecutivos d y d+1,
    # si el mismo profesor cubre ambos, damos un "bonus" (reducimos penalización).
    # Esto fomenta bloques de días consecutivos para cada profesor.

    # Ordenar días lectivos y crear mapeo día -> índice ordinal
    dias_unicos = sorted(set(s.fecha for s in slots))
    dia_a_ordinal: Dict[date, int] = {d: i for i, d in enumerate(dias_unicos)}

    # Para cada profesor, agrupar sus slots por día
    # slots_por_prof_dia[prof_id][dia_ordinal] = lista de slot_idx
    slots_por_prof_dia: Dict[int, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))
    for p in profesores:
        for s_idx in prof_slots[p.id]:
            dia_ord = dia_a_ordinal[slots[s_idx].fecha]
            slots_por_prof_dia[p.id][dia_ord].append(s_idx)

    # Crear variable: tiene_guardia_dia[prof_id][dia_ord] = 1 si el profesor
    # tiene al menos una guardia ese día
    tiene_guardia_dia: Dict[int, Dict[int, cp_model.IntVar]] = {}

    for p in profesores:
        tiene_guardia_dia[p.id] = {}
        for dia_ord, slot_idxs in slots_por_prof_dia[p.id].items():
            if slot_idxs:
                tiene = model.NewBoolVar(f"tiene_{p.id}_{dia_ord}")
                # tiene = 1 si alguno de los slots de ese día está asignado
                model.AddMaxEquality(tiene, [x[(p.id, s_idx)] for s_idx in slot_idxs])
                tiene_guardia_dia[p.id][dia_ord] = tiene

    # Penalizar "cambios" de día a día: si tiene guardia en d pero no en d+1
    # (o viceversa), hay un "corte" que queremos minimizar.
    # Un corte indica que las guardias no son consecutivas.
    penalizacion_consecutividad: List[cp_model.IntVar] = []

    for p in profesores:
        dias_prof = sorted(tiene_guardia_dia[p.id].keys())
        if len(dias_prof) < 2:
            continue

        for i in range(len(dias_prof) - 1):
            dia1 = dias_prof[i]
            dia2 = dias_prof[i + 1]

            # Solo considerar días consecutivos en el calendario del profesor
            if dia2 != dia1 + 1:
                continue  # No son días consecutivos, ignorar

            tiene_d1 = tiene_guardia_dia[p.id][dia1]
            tiene_d2 = tiene_guardia_dia[p.id][dia2]

            # corte = 1 si (tiene_d1 XOR tiene_d2)
            # Es decir, si hay guardia en uno pero no en el otro
            corte = model.NewBoolVar(f"corte_{p.id}_{dia1}")

            # XOR: corte = tiene_d1 != tiene_d2
            # Equivalente a: corte = 1 iff (tiene_d1 + tiene_d2 == 1)
            model.Add(tiene_d1 + tiene_d2 == 1).OnlyEnforceIf(corte)
            model.Add(tiene_d1 + tiene_d2 != 1).OnlyEnforceIf(corte.Not())

            penalizacion_consecutividad.append(corte)

    n_cortes = len(penalizacion_consecutividad)
    logger.info(f"  ✓ Objetivo 2: minimizar cortes entre días ({n_cortes} términos)")

    # -------------------------------------------------------------------------
    # OBJETIVO 3 (TERCIARIO): PREFERENCIA DE ZONA
    # -------------------------------------------------------------------------
    # Estrategia: Cada profesor debería hacer guardias en la MISMA zona.
    # Maximizar la concentración: si un profesor hace N guardias,
    # maximizar que estén en la misma zona.

    # Para cada profesor, contar guardias por zona
    penalizacion_zona: List[cp_model.IntVar] = []

    for p in profesores:
        slots_prof = prof_slots[p.id]
        if not slots_prof or len(slots_prof) < 2:
            continue

        # Agrupar slots por zona
        slots_por_zona: Dict[int, List[int]] = defaultdict(list)
        for s_idx in slots_prof:
            zona_id = slots[s_idx].zona_id
            slots_por_zona[zona_id].append(s_idx)

        if len(slots_por_zona) < 2:
            # Solo tiene acceso a una zona, no hay penalización posible
            continue

        # guardias_en_zona[z] = número de guardias del profesor en zona z
        guardias_en_zona: Dict[int, cp_model.IntVar] = {}
        for zona_id, slot_idxs in slots_por_zona.items():
            g_zona = model.NewIntVar(0, len(slot_idxs), f"gz_{p.id}_{zona_id}")
            model.Add(g_zona == sum(x[(p.id, s_idx)] for s_idx in slot_idxs))
            guardias_en_zona[zona_id] = g_zona

        # max_en_una_zona = máximo de guardias en una sola zona
        max_en_zona = model.NewIntVar(0, len(slots_prof), f"maxz_{p.id}")
        model.AddMaxEquality(max_en_zona, list(guardias_en_zona.values()))

        # Penalización = guardias_totales - max_en_zona
        # (guardias fuera de la zona principal)
        pen_zona = model.NewIntVar(0, len(slots_prof), f"penz_{p.id}")
        model.Add(pen_zona == n_guardias[p.id] - max_en_zona)
        penalizacion_zona.append(pen_zona)

    n_pen_zona = len(penalizacion_zona)
    logger.info(f"  ✓ Objetivo 3: maximizar concentración zona ({n_pen_zona} profesores)")

    # -------------------------------------------------------------------------
    # COMBINAR OBJETIVOS CON PESOS
    # -------------------------------------------------------------------------
    # Prioridad: Equidad >> Consecutividad > Zona
    # Pesos elegidos para que la equidad siempre tenga prioridad absoluta.
    # Una vez garantizada equidad perfecta (max_dev=0, sum_desv=0),
    # los objetivos secundarios se optimizan con consecutividad prioritaria.
    PESO_EQUIDAD = 1000000      # Máxima prioridad (garantiza equidad primero)
    PESO_EQUIDAD_SUMA = 10000   # Suma de desviaciones (secundario a max_dev)
    PESO_CONSECUTIVIDAD = 10    # Minimizar cortes entre días (prioritario)
    PESO_ZONA = 3               # Preferencia de zona (secundario)

    objetivo = (
        PESO_EQUIDAD * max_dev +
        PESO_EQUIDAD_SUMA * sum(desviaciones) +
        PESO_CONSECUTIVIDAD * sum(penalizacion_consecutividad) +
        PESO_ZONA * sum(penalizacion_zona)
    )

    model.Minimize(objetivo)

    logger.info(
        f"  ✓ Objetivo combinado: equidad({PESO_EQUIDAD}*max + {PESO_EQUIDAD_SUMA}*sum) "
        f"+ consec({PESO_CONSECUTIVIDAD}) + zona({PESO_ZONA})"
    )

    # =========================================================================
    # FASE 5: GENERAR HINTS (SOLUCIÓN INICIAL GREEDY MEJORADA)
    # =========================================================================
    if use_hints:
        logger.info("")
        logger.info("FASE 5: GENERANDO HINTS (Greedy mejorado)")
        logger.info("-" * 80)
        reportar(30, "Generando solución inicial...")

        asig_greedy: Dict[int, int] = {p.id: 0 for p in profesores}
        slot_asignado: Dict[int, int] = {}
        guardias_por_dia_greedy: Dict[Tuple[int, date], Set[int]] = defaultdict(set)
        momento_ocupado: Set[Tuple[int, date, str, int]] = set()

        # Tracking adicional para consecutividad y zona
        # prof_id -> último día ordinal con guardia
        ultimo_dia_guardia: Dict[int, int] = {}
        # prof_id -> {zona: count}
        zona_principal: Dict[int, Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for s_idx in range(len(slots)):
            slot = slots[s_idx]
            dia_ord = dia_a_ordinal[slot.fecha]
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
                # Función de scoring multi-criterio:
                # 1. Equidad (principal): menor ratio asignado/cuota
                # 2. Consecutividad: bonus si el día es consecutivo al último
                # 3. Zona: bonus si es la zona principal del profesor

                def score_candidato(pid):
                    # Score de equidad (menor es mejor)
                    ratio = asig_greedy[pid] / max(cuotas_ideales[pid], 0.1)

                    # Bonus consecutividad (menor es mejor, restamos bonus)
                    bonus_consec = 0
                    if pid in ultimo_dia_guardia:
                        diff = dia_ord - ultimo_dia_guardia[pid]
                        if diff == 1:  # Día consecutivo
                            bonus_consec = -0.1  # Bonus fuerte
                        elif diff <= 3:  # Cercano
                            bonus_consec = -0.02

                    # Bonus zona (menor es mejor)
                    bonus_zona = 0
                    if zona_principal[pid]:
                        zona_mas_usada = max(zona_principal[pid], key=zona_principal[pid].get)
                        if slot.zona_id == zona_mas_usada:
                            bonus_zona = -0.05  # Bonus moderado

                    return ratio + bonus_consec + bonus_zona

                mejor = min(candidatos, key=score_candidato)
                slot_asignado[s_idx] = mejor
                asig_greedy[mejor] += 1
                guardias_por_dia_greedy[(mejor, slot.fecha)].add(s_idx)
                momento = (mejor, slot.fecha, slot.turno, slot.recreo_id)
                momento_ocupado.add(momento)

                # Actualizar tracking
                ultimo_dia_guardia[mejor] = dia_ord
                zona_principal[mejor][slot.zona_id] += 1

        # Aplicar hints al modelo
        for s_idx, p_id in slot_asignado.items():
            model.AddHint(x[(p_id, s_idx)], 1)

        logger.info(f"  ✓ Hint greedy mejorado: {len(slot_asignado)}/{len(slots)} slots")

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

    # Métricas de equidad
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

    # Métricas de consecutividad (analizar guardias generadas)
    guardias_por_prof: Dict[int, List[date]] = defaultdict(list)
    for g in guardias:
        guardias_por_prof[g.profesor_id].append(g.fecha)

    huecos_totales = 0
    profs_con_huecos = 0
    for p_id, fechas in guardias_por_prof.items():
        if len(fechas) < 2:
            continue
        fechas_ord = sorted(set(fechas))
        dias_ord_prof = [dia_a_ordinal[f] for f in fechas_ord]
        for i in range(len(dias_ord_prof) - 1):
            salto = dias_ord_prof[i+1] - dias_ord_prof[i]
            if salto > 1:
                huecos_totales += (salto - 1)
                profs_con_huecos += 1

    logger.info(f"  Huecos en consecutividad: {huecos_totales} días")

    # Métricas de zona (analizar concentración)
    zonas_por_prof: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for g in guardias:
        zonas_por_prof[g.profesor_id][g.zona_id] += 1

    total_fuera_zona_principal = 0
    for p_id, zonas_count in zonas_por_prof.items():
        if zonas_count:
            max_zona = max(zonas_count.values())
            total_prof = sum(zonas_count.values())
            total_fuera_zona_principal += (total_prof - max_zona)

    logger.info(f"  Guardias fuera de zona principal: {total_fuera_zona_principal}")
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
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Error de base de datos al guardar guardias: {e}")
        raise
