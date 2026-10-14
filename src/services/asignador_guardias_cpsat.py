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

import threading
from collections import defaultdict
from datetime import date
from typing import Callable, Dict, List, Optional, Tuple

from ortools.sat.python import cp_model
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.database.models import (
    Configuracion,
    Guardia,
    Profesor,
    Zona,
)
from services._asignador_cpsat_helpers import (
    ProgresoSolver,
    SolverCallback,
    _es_elegible_basico,
    _generar_slots,
    resolver_con_progreso,
)
from services.distribucion_cuotas_service import DistribucionCuotasService
from services.reparto_agrupado import (
    cuotas_alcanzables,
    objetivos_justos,
    reparar_equidad,
    repartir_por_carriles,
    terminos_de_agrupacion,
)
from utils import get_logger

logger = get_logger(__name__)

# =============================================================================
# FUNCIÓN PRINCIPAL: GENERADOR CP-SAT
# =============================================================================


def _preparar_generacion_incremental(session, slots, desde: date, curso_id=None):
    """Reparte el trabajo entre lo que se conserva y lo que hay que recalcular.

    Devuelve `(guardias_conservadas, ya_asignadas, slots_pendientes)`:

    - **guardias_conservadas**: todo lo anterior a `desde`, más las sustituciones
      posteriores. Una sustitución la ha puesto una persona por una ausencia
      concreta; rehacerla sería tirar ese trabajo (decisión de producto, 2026-09-05).
    - **ya_asignadas**: cuántas guardias tiene ya cada profesor entre las conservadas.
      Sirve para descontarlas de su cuota y que el reparto siga siendo justo.
    - **slots_pendientes**: los huecos desde `desde` que no cubre ninguna guardia
      conservada.
    """
    # Sólo el curso activo: las guardias de un curso anterior también son
    # «anteriores a desde» y se descontaban de la cuota (2026-10-03).
    conservadas = (
        session.query(Guardia)
        .filter((Guardia.fecha < desde) | (Guardia.es_sustitucion.is_(True)))
        .filter(Guardia.curso_id == curso_id if curso_id else Guardia.curso_id.is_(None))
        .all()
    )
    # Una sustitución anterior a `desde` ya entra por la primera condición.
    conservadas = [g for g in conservadas if g.fecha < desde or g.es_sustitucion]

    ya_asignadas: Dict[int, int] = defaultdict(int)
    ocupados = set()
    for guardia in conservadas:
        ya_asignadas[guardia.profesor_id] += 1
        ocupados.add((guardia.fecha, guardia.recreo, guardia.zona_id))

    pendientes = [
        slot
        for slot in slots
        if slot.fecha >= desde
        and (slot.fecha, slot.recreo_id, slot.zona_id) not in ocupados
    ]
    return conservadas, dict(ya_asignadas), pendientes


def generar_guardias_cpsat(
    session,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    timeout_seconds: Optional[float] = None,
    use_hints: bool = True,
    cancelacion: Optional[threading.Event] = None,
    desde: Optional[date] = None,
) -> Tuple[List[Guardia], Dict[int, int]]:
    """
    Genera el calendario de guardias usando CP-SAT de OR-Tools.

    Este algoritmo GARANTIZA encontrar la solución óptima (si existe)
    minimizando la inequidad entre profesores.

    Args:
        session: Sesión de SQLAlchemy
        progress_callback: Callback para reportar progreso (porcentaje, mensaje)
        timeout_seconds: Tiempo máximo de resolución. None = el de los ajustes
        use_hints: Si True, genera una solución greedy como hint inicial
        cancelacion: Evento que, al activarse, detiene la generación en la fase en curso
        desde: Si se indica, sólo se recalcula a partir de esa fecha. Lo anterior se
            conserva, y también las sustituciones posteriores, que son decisiones
            tomadas a mano (FUN-002)

    Returns:
        Tupla (lista de guardias, diccionario profesor_id -> guardias_asignadas)
    """

    if timeout_seconds is None:
        from config.settings import get_settings

        timeout_seconds = get_settings().solver_timeout_segundos

    def reportar(porcentaje: int, mensaje: str = ""):
        # La cancelación se comprueba en cada fase: así se sale limpiamente en vez de
        # seguir trabajando hasta el final (CRW-004).
        if cancelacion is not None and cancelacion.is_set():
            raise InterruptedError("Operación cancelada por el usuario")
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except InterruptedError:
                # Petición de cancelación del llamante: nunca se traga.
                raise
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

    curso_activo = GestorCursos.from_session(session).obtener_curso_activo()
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
        if not session.query(Zona).filter(Zona.activa.is_(True)).count():
            raise ValueError("No hay zonas activas que cubrir: crea al menos una zona")
        raise ValueError(
            "No hay huecos que cubrir: revisa las fechas del curso, los recreos y las zonas"
        )

    # Generación incremental: se congela lo anterior a `desde` y se respetan las
    # sustituciones posteriores, que son decisiones tomadas a mano (FUN-002).
    guardias_conservadas: List[Guardia] = []
    ya_asignadas: Dict[int, int] = {}
    if desde is not None:
        guardias_conservadas, ya_asignadas, slots = _preparar_generacion_incremental(
            session, slots, desde, curso_id
        )
        logger.info(
            f"  ✓ Incremental desde {desde}: se conservan {len(guardias_conservadas)} guardias"
        )

    logger.info(f"  ✓ {len(profesores)} profesores activos")
    logger.info(f"  ✓ {len(slots)} slots a cubrir")

    if not slots:
        logger.info("  ✓ No queda nada que recalcular en el rango pedido")
        reportar(100, "Sin cambios: no hay slots que recalcular")
        return list(guardias_conservadas), dict(ya_asignadas)

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
        f"({100 * total_elegibles / (len(profesores) * len(slots)):.1f}%)"
    )

    # Verificar que todos los slots tienen al menos un profesor
    slots_sin_cobertura = [i for i in range(len(slots)) if not slot_profs[i]]
    if slots_sin_cobertura:
        # Decir cuántos huecos hay no ayuda a arreglarlos: hace falta saber qué
        # regla dejó fuera a cada profesor y qué cambio mínimo lo desbloquea (FUN-013).
        from services.diagnostico_cobertura import diagnosticar, registrar

        registrar(diagnosticar(profesores, [slots[i] for i in slots_sin_cobertura], session))

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
    # RESTRICCIÓN 1: Cada slot, como mucho un profesor; dejarlo vacío se penaliza
    # -------------------------------------------------------------------------
    # Con «exactamente uno», un día sin profesores suficientes volvía el modelo
    # imposible y no se generaba nada. Ahora se cubre todo lo posible y lo que
    # falta queda en el resumen (2026-10-03).
    huecos_vacios = []
    for s_idx in range(len(slots)):
        profs_elegibles = slot_profs[s_idx]
        if profs_elegibles:
            model.AddAtMostOne(x[(p_id, s_idx)] for p_id in profs_elegibles)
            huecos_vacios.append(1 - sum(x[(p_id, s_idx)] for p_id in profs_elegibles))

    logger.info("  ✓ Restricción: cada slot, como mucho 1 profesor")

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
    if ya_asignadas:
        # Lo ya cubierto cuenta: quien hizo muchas guardias en el primer trimestre
        # debe hacer menos en el resto, o el reparto dejaría de ser justo.
        for p_id in list(cuotas_ideales):
            cuotas_ideales[p_id] = max(0.0, cuotas_ideales[p_id] - ya_asignadas.get(p_id, 0))
        logger.info(
            f"  ✓ Cuotas ajustadas descontando {sum(ya_asignadas.values())} guardias ya hechas"
        )

    logger.info(f"  ✓ Cuotas calculadas por turno (suma={sum(cuotas_ideales.values()):.0f})")

    # Lo que de verdad toca a cada uno: su cuota si le cabe y, si no, el reparto
    # más justo posible del sobrante. Es la referencia de la equidad (2026-10-03).
    reportar(27, "Buscando el reparto más justo posible...")
    cuotas_base = {p.id: int(round(cuotas_ideales[p.id])) for p in profesores}
    alcanzables = cuotas_alcanzables(slots, profesores, prof_slots, cuotas_base)
    objetivo = objetivos_justos(
        slots, profesores, prof_slots, slot_profs, alcanzables,
        segundos=min(30.0, timeout_seconds * 0.25), cancelacion=cancelacion,
    )
    reportar(29, "Reparto justo calculado")

    # Variable auxiliar: número de guardias por profesor
    n_guardias: Dict[int, cp_model.IntVar] = {}
    for p in profesores:
        if prof_slots[p.id]:
            n_guardias[p.id] = model.NewIntVar(0, len(prof_slots[p.id]), f"n_{p.id}")
            model.Add(n_guardias[p.id] == sum(x[(p.id, s_idx)] for s_idx in prof_slots[p.id]))
        else:
            n_guardias[p.id] = model.NewIntVar(0, 0, f"n_{p.id}")

    # Equidad primero (2026-10-06): nadie pasa de su cuota en más de una guardia
    # para tapar un hueco; si no hay quien lo cubra sin eso, el hueco se queda.
    # El reparto justo ya cumple este tope, así que el modelo nunca es imposible.
    # Sin cuotas (todas a 0) no hay referencia de equidad: no se limita a nadie.
    for p in profesores if any(alcanzables.values()) else []:
        if prof_slots[p.id]:
            tope = max(objetivo.get(p.id, 0), alcanzables.get(p.id, 0) + 1)
            model.Add(n_guardias[p.id] <= tope)

    # -------------------------------------------------------------------------
    # OBJETIVO 1 (PRIMARIO): MINIMIZAR INEQUIDAD
    # -------------------------------------------------------------------------
    # Desviación de cada profesor respecto a su cuota
    desviaciones: List[cp_model.IntVar] = []
    for p in profesores:
        cuota = objetivo.get(p.id, 0)
        if prof_slots[p.id]:
            # Cota holgada: con 50 fijo, una diferencia mayor volvía el modelo imposible.
            dev = model.NewIntVar(0, len(prof_slots[p.id]) + cuota, f"dev_{p.id}")
            model.Add(dev >= n_guardias[p.id] - cuota)
            model.Add(dev >= cuota - n_guardias[p.id])
            desviaciones.append(dev)

    # Máxima desviación
    max_dev = model.NewIntVar(0, 10_000, "max_dev")
    model.AddMaxEquality(max_dev, desviaciones)

    logger.info("  ✓ Objetivo 1: minimizar inequidad (max_desv + sum_desv)")

    # -------------------------------------------------------------------------
    # OBJETIVO 2: AGRUPAR (tramos de días seguidos, un carril, un recreo)
    # -------------------------------------------------------------------------
    # Sustituye al «span» (días entre la primera y la última guardia), que no
    # distinguía un tramo largo de muchas guardias sueltas, y a la concentración
    # por zona, que no miraba el recreo (2026-10-03).
    dias_unicos = sorted(set(s.fecha for s in slots))
    dia_a_ordinal: Dict[date, int] = {d: i for i, d in enumerate(dias_unicos)}
    agrupacion = terminos_de_agrupacion(model, x, slots, prof_slots)
    logger.info("  ✓ Objetivo 2: tramos de días seguidos, un carril y un recreo")

    # -------------------------------------------------------------------------
    # OBJETIVO 3b: PENALIZAR GUARDIAS FUERA DE ZONA PREFERIDA EXPLÍCITA
    # -------------------------------------------------------------------------
    # Cuando un profesor tiene zona_preferida_id configurada, se añade una
    # penalización por cada guardia asignada en una zona diferente.
    PESO_ZONA_PREF = 50
    penalizacion_zona_preferida: List[cp_model.IntVar] = []

    for p in profesores:
        if not p.zona_preferida_id:
            continue
        slots_fuera = [
            s_idx for s_idx in prof_slots[p.id]
            if slots[s_idx].zona_id != p.zona_preferida_id
        ]
        if not slots_fuera:
            continue
        pen_pref = model.NewIntVar(0, len(slots_fuera), f"penz_pref_{p.id}")
        model.Add(pen_pref == sum(x[(p.id, s_idx)] for s_idx in slots_fuera))
        penalizacion_zona_preferida.append(pen_pref)

    n_pen_zona_pref = len(penalizacion_zona_preferida)
    if n_pen_zona_pref:
        logger.info(f"  ✓ Objetivo 3b: zona preferida explícita ({n_pen_zona_pref} profesores)")

    # -------------------------------------------------------------------------
    # COMBINAR OBJETIVOS CON PESOS
    # -------------------------------------------------------------------------
    # Una guardia de diferencia con el objetivo pesa más que cualquier mejora de
    # agrupación: la equidad nunca se cambia por tener las guardias más juntas.
    PESO_EQUIDAD = 50_000
    PESO_EQUIDAD_SUMA = 5_000

    PESO_HUECO_VACIO = 10_000_000

    objetivo_modelo = (
        PESO_HUECO_VACIO * sum(huecos_vacios)
        + PESO_EQUIDAD * max_dev
        + PESO_EQUIDAD_SUMA * sum(desviaciones)
        + sum(agrupacion)
        + PESO_ZONA_PREF * sum(penalizacion_zona_preferida)
    )

    model.Minimize(objetivo_modelo)

    logger.info(
        f"  ✓ Objetivo combinado: equidad({PESO_EQUIDAD}*max + {PESO_EQUIDAD_SUMA}*sum) "
        f"+ agrupación + zona_pref({PESO_ZONA_PREF}*{n_pen_zona_pref} profs)"
    )

    # =========================================================================
    # FASE 5: PUNTO DE PARTIDA (CARRILES)
    # =========================================================================
    if use_hints:
        logger.info("")
        logger.info("FASE 5: PUNTO DE PARTIDA POR CARRILES")
        logger.info("-" * 80)
        reportar(30, "Generando solución inicial...")
        semilla = reparar_equidad(
            slots,
            repartir_por_carriles(slots, profesores, prof_slots, slot_profs, objetivo),
            prof_slots,
            objetivo,
        )
        for s_idx, p_id in semilla.items():
            model.AddHint(x[(p_id, s_idx)], 1)
        logger.info(f"  ✓ Punto de partida: {len(semilla)}/{len(slots)} slots")

    # =========================================================================
    # FASE 6: RESOLVER
    # =========================================================================
    logger.info("")
    logger.info("FASE 6: RESOLVIENDO CON CP-SAT")
    logger.info("-" * 80)
    reportar(35, "Resolviendo modelo...")

    from config.settings import hilos_del_solver

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    # Tantos hilos como núcleos, no 8 fijos: 8 sobrecargan un equipo de 4 núcleos
    # y desaprovechan uno de 16 (ESC-002).
    solver.parameters.num_search_workers = hilos_del_solver()
    solver.parameters.linearization_level = 2
    solver.parameters.cp_model_presolve = True

    # El callback sólo publica en un buzón; informar es cosa del hilo llamante (CRW-001)
    progreso_solver = ProgresoSolver()
    callback = SolverCallback(x, cuotas_ideales, progreso_solver)

    status = resolver_con_progreso(
        solver, model, callback, progreso_solver, reportar, cancelacion
    )

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
    asignaciones: Dict[int, int] = {p.id: solver.Value(n_guardias[p.id]) for p in profesores}

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
    indice_equidad = 100 * (1 - suma_desv / suma_cuotas) if suma_cuotas else 100.0

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
            salto = dias_ord_prof[i + 1] - dias_ord_prof[i]
            if salto > 1:
                huecos_totales += salto - 1
                profs_con_huecos += 1

    logger.info(f"  Huecos en consecutividad: {huecos_totales} días")

    # Métrica de concentración: guardias / span_natural × 100
    concentraciones = []
    for p in profesores:
        fechas_p = sorted(set(g.fecha for g in guardias if g.profesor_id == p.id))
        if len(fechas_p) >= 2:
            span_nat = (fechas_p[-1] - fechas_p[0]).days
            if span_nat > 0:
                concentraciones.append(len(fechas_p) / span_nat * 100)

    if concentraciones:
        c_media = sum(concentraciones) / len(concentraciones)
        c_min = min(concentraciones)
        c_max = max(concentraciones)
        logger.info(
            f"  Concentración (guardias/span_natural): "
            f"media={c_media:.1f}%, min={c_min:.1f}%, max={c_max:.1f}%"
        )

    # Métricas de zona (analizar concentración)
    zonas_por_prof: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for g in guardias:
        zonas_por_prof[g.profesor_id][g.zona_id] += 1

    total_fuera_zona_principal = 0
    for p_id, zonas_count in zonas_por_prof.items():
        if zonas_count:
            max_zona = max(zonas_count.values())
            total_prof = sum(zonas_count.values())
            total_fuera_zona_principal += total_prof - max_zona

    logger.info(f"  Guardias fuera de zona principal: {total_fuera_zona_principal}")
    logger.info(f"  Solución óptima: {'SÍ' if es_optimo else 'NO (tiempo agotado)'}")

    opt_str = "Óptimo" if es_optimo else "Factible"
    reportar(100, f"✅ Completado: IE={indice_equidad:.1f}% ({opt_str})")

    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ ALGORITMO CP-SAT COMPLETADO")
    logger.info("=" * 80)

    return (guardias, asignaciones)


def guardar_guardias_cpsat_en_bd(session, guardias: List[Guardia]) -> None:
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
