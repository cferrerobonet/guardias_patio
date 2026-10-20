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

# Pesos del objetivo. Una guardia de diferencia con el objetivo pesa más que cualquier
# mejora de agrupación: la equidad nunca se cambia por tener las guardias más juntas.
PESO_EQUIDAD = 50_000
PESO_EQUIDAD_SUMA = 5_000
PESO_HUECO_VACIO = 10_000_000
# Penalización por cada guardia fuera de la zona preferida explícita del profesor.
PESO_ZONA_PREF = 50
# Reparto del déficit entre zonas: su peso máximo (3 × 1000) queda por debajo de una
# guardia de equidad (5000) y por encima de la agrupación (CarlosFB, 2026-10-15).
PESO_REPARTO_ZONAS = 3

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


def _reportador(
    progress_callback: Optional[Callable[[int, str], None]],
    cancelacion: Optional[threading.Event],
) -> Callable[..., None]:
    """Función que anuncia el progreso y corta la generación si se ha cancelado."""

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

    return reportar


def _cabecera_de_fase(titulo: str) -> None:
    logger.info("")
    logger.info(titulo)
    logger.info("-" * 80)


def _cargar_datos(session, reportar):
    """FASE 1: configuración, curso activo, profesores activos y huecos que cubrir."""
    _cabecera_de_fase("FASE 1: PREPARACIÓN DE DATOS")
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
    return curso_id, profesores, slots


def _calcular_elegibilidad(session, profesores, slots, reportar):
    """FASE 2: qué huecos puede cubrir cada profesor y quién puede cubrir cada hueco."""
    _cabecera_de_fase("FASE 2: PRE-CÁLCULO DE ELEGIBILIDAD")
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
    return prof_slots, slot_profs


def _crear_variables(model, profesores, prof_slots):
    """x[(prof_id, slot_idx)] = 1 si el profesor cubre el hueco."""
    x: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for p in profesores:
        for s_idx in prof_slots[p.id]:
            x[(p.id, s_idx)] = model.NewBoolVar(f"x_{p.id}_{s_idx}")

    logger.info(f"  ✓ {len(x)} variables booleanas creadas")
    return x


def _restriccion_un_profesor_por_hueco(model, x, slots, slot_profs):
    """RESTRICCIÓN 1: cada slot, como mucho un profesor; dejarlo vacío se penaliza.

    Con «exactamente uno», un día sin profesores suficientes volvía el modelo
    imposible y no se generaba nada. Ahora se cubre todo lo posible y lo que
    falta queda en el resumen (2026-10-03).
    """
    huecos_vacios = []
    # Por zona, para repartir el déficit (objetivo 4)
    vacios_por_zona: Dict[int, list] = defaultdict(list)
    for s_idx in range(len(slots)):
        profs_elegibles = slot_profs[s_idx]
        if profs_elegibles:
            model.AddAtMostOne(x[(p_id, s_idx)] for p_id in profs_elegibles)
            vacio = 1 - sum(x[(p_id, s_idx)] for p_id in profs_elegibles)
            huecos_vacios.append(vacio)
            vacios_por_zona[slots[s_idx].zona_id].append(vacio)

    logger.info("  ✓ Restricción: cada slot, como mucho 1 profesor")
    return huecos_vacios, vacios_por_zona


def _restriccion_una_al_dia(model, x, profesores, prof_slots, slots):
    """RESTRICCIÓN 2: máximo 1 guardia por día por profesor."""
    slots_por_dia: Dict[Tuple[int, date], List[int]] = defaultdict(list)
    for p in profesores:
        for s_idx in prof_slots[p.id]:
            fecha = slots[s_idx].fecha
            slots_por_dia[(p.id, fecha)].append(s_idx)

    for (p_id, _fecha), slot_idxs in slots_por_dia.items():
        if len(slot_idxs) > 1:
            model.AddAtMostOne(x[(p_id, s_idx)] for s_idx in slot_idxs)

    logger.info("  ✓ Restricción: máx 1 guardia/día/profesor")


def _restriccion_sin_simultaneidad(model, x, profesores, prof_slots, slots):
    """RESTRICCIÓN 3: no simultaneidad (mismo recreo = mismo momento)."""
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


def _cuotas_ideales(session, profesores, ya_asignadas: Dict[int, int]) -> Dict[int, float]:
    """Cuotas por turno del servicio de distribución, descontando lo ya hecho."""
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
    return cuotas_ideales


def _variables_de_carga(model, x, profesores, prof_slots, objetivo, alcanzables):
    """Número de guardias de cada profesor, con el tope que impone la equidad."""
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
    return n_guardias


def _terminos_de_equidad(model, n_guardias, profesores, prof_slots, objetivo):
    """OBJETIVO 1 (PRIMARIO): desviación de cada profesor respecto a su cuota y la mayor."""
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
    return desviaciones, max_dev


def _penalizacion_zona_preferida(model, x, profesores, prof_slots, slots):
    """OBJETIVO 3b: penalizar guardias fuera de la zona preferida explícita.

    Cuando un profesor tiene zona_preferida_id configurada, se añade una
    penalización por cada guardia asignada en una zona diferente.
    """
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
    return penalizacion_zona_preferida


def _peor_zona_vacia(model, vacios_por_zona):
    """OBJETIVO 4: si faltan profesores, que el déficit se reparta entre zonas.

    Con menos profesores que huecos, cualquier solución que cubra el máximo
    valía lo mismo, y una dejó una zona sin ninguna guardia en toda la semana
    (test_cobertura_todas_zonas, en la CI de la 7.3.0, 2026-10-14). Se minimiza
    el mayor porcentaje (en milésimas) de huecos vacíos de una zona. Su peso
    máximo (3 × 1000) queda por debajo de una guardia de equidad (5000) y por
    encima de la agrupación: decisión de CarlosFB del 2026-10-15. Sin déficit
    vale 0. No volver a dejar el déficit sin repartir.
    """
    peor_zona_vacia = model.NewIntVar(0, 1000, "peor_zona_vacia_milesimas")
    for vacios in vacios_por_zona.values():
        model.Add(peor_zona_vacia * len(vacios) >= 1000 * sum(vacios))
    if vacios_por_zona:
        logger.info(f"  ✓ Objetivo 4: déficit repartido entre {len(vacios_por_zona)} zonas")
    return peor_zona_vacia


def _fijar_objetivo(
    model, huecos_vacios, max_dev, desviaciones, agrupacion, penalizacion_zona_preferida,
    peor_zona_vacia,
) -> None:
    """Combina los objetivos con sus pesos (ver `PESO_*` al principio del módulo)."""
    objetivo_modelo = (
        PESO_HUECO_VACIO * sum(huecos_vacios)
        + PESO_EQUIDAD * max_dev
        + PESO_EQUIDAD_SUMA * sum(desviaciones)
        + sum(agrupacion)
        + PESO_ZONA_PREF * sum(penalizacion_zona_preferida)
        + PESO_REPARTO_ZONAS * peor_zona_vacia
    )

    model.Minimize(objetivo_modelo)

    logger.info(
        f"  ✓ Objetivo combinado: equidad({PESO_EQUIDAD}*max + {PESO_EQUIDAD_SUMA}*sum) "
        f"+ agrupación + zona_pref({PESO_ZONA_PREF}*{len(penalizacion_zona_preferida)} profs)"
    )


def _punto_de_partida(model, x, slots, profesores, prof_slots, slot_profs, objetivo, reportar):
    """FASE 5: pista inicial por carriles para el solucionador."""
    _cabecera_de_fase("FASE 5: PUNTO DE PARTIDA POR CARRILES")
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


def _resolver(model, x, cuotas_ideales, timeout_seconds, reportar, cancelacion):
    """FASE 6: resuelve el modelo con progreso y cancelación desde el hilo llamante."""
    _cabecera_de_fase("FASE 6: RESOLVIENDO CON CP-SAT")
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
    return solver, callback, status


def _comprobar_solucion(solver, callback, status) -> bool:
    """FASE 7: falla si no hay solución; devuelve si es óptima."""
    _cabecera_de_fase("FASE 7: PROCESANDO RESULTADO")

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
    return es_optimo


def _guardias_de_la_solucion(solver, x, slots, curso_id) -> List[Guardia]:
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
    return guardias


def _metricas_de_equidad(guardias, slots, profesores, asignaciones, cuotas_ideales) -> float:
    """Registra las métricas de equidad y devuelve el índice de equidad."""
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
    return indice_equidad


def _metricas_de_consecutividad(guardias, slots) -> None:
    """Días sin guardia entre dos guardias seguidas de un mismo profesor."""
    dias_unicos = sorted(set(s.fecha for s in slots))
    dia_a_ordinal: Dict[date, int] = {d: i for i, d in enumerate(dias_unicos)}
    guardias_por_prof: Dict[int, List[date]] = defaultdict(list)
    for g in guardias:
        guardias_por_prof[g.profesor_id].append(g.fecha)

    huecos_totales = 0
    for fechas in guardias_por_prof.values():
        if len(fechas) < 2:
            continue
        dias_ord_prof = [dia_a_ordinal[f] for f in sorted(set(fechas))]
        for i in range(len(dias_ord_prof) - 1):
            salto = dias_ord_prof[i + 1] - dias_ord_prof[i]
            if salto > 1:
                huecos_totales += salto - 1

    logger.info(f"  Huecos en consecutividad: {huecos_totales} días")


def _metricas_de_concentracion(guardias, profesores) -> None:
    """Guardias / span natural × 100, por profesor."""
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


def _metricas_de_zona(guardias) -> None:
    """Guardias de cada profesor fuera de la zona en la que más hace."""
    zonas_por_prof: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for g in guardias:
        zonas_por_prof[g.profesor_id][g.zona_id] += 1

    total_fuera_zona_principal = 0
    for zonas_count in zonas_por_prof.values():
        if zonas_count:
            max_zona = max(zonas_count.values())
            total_prof = sum(zonas_count.values())
            total_fuera_zona_principal += total_prof - max_zona

    logger.info(f"  Guardias fuera de zona principal: {total_fuera_zona_principal}")


def _registrar_metricas(guardias, slots, profesores, asignaciones, cuotas_ideales,
                        es_optimo) -> float:
    """FASE 8: métricas finales en el registro; devuelve el índice de equidad."""
    _cabecera_de_fase("MÉTRICAS FINALES")
    indice_equidad = _metricas_de_equidad(guardias, slots, profesores, asignaciones,
                                          cuotas_ideales)
    _metricas_de_consecutividad(guardias, slots)
    _metricas_de_concentracion(guardias, profesores)
    _metricas_de_zona(guardias)
    logger.info(f"  Solución óptima: {'SÍ' if es_optimo else 'NO (tiempo agotado)'}")
    return indice_equidad


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

    reportar = _reportador(progress_callback, cancelacion)

    logger.info("=" * 80)
    logger.info("ALGORITMO CP-SAT - GENERACIÓN ÓPTIMA DE GUARDIAS")
    logger.info("=" * 80)

    reportar(0, "Iniciando generación con CP-SAT...")

    curso_id, profesores, slots = _cargar_datos(session, reportar)

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

    prof_slots, slot_profs = _calcular_elegibilidad(session, profesores, slots, reportar)

    # FASE 3: modelo y restricciones duras
    _cabecera_de_fase("FASE 3: CREANDO MODELO CP-SAT")
    reportar(20, "Creando modelo...")
    model = cp_model.CpModel()
    x = _crear_variables(model, profesores, prof_slots)
    huecos_vacios, vacios_por_zona = _restriccion_un_profesor_por_hueco(
        model, x, slots, slot_profs
    )
    _restriccion_una_al_dia(model, x, profesores, prof_slots, slots)
    _restriccion_sin_simultaneidad(model, x, profesores, prof_slots, slots)

    # FASE 4: objetivo (equidad + agrupación + zona)
    _cabecera_de_fase("FASE 4: DEFINIENDO OBJETIVO MULTI-CRITERIO")
    reportar(25, "Definiendo objetivo multi-criterio...")
    cuotas_ideales = _cuotas_ideales(session, profesores, ya_asignadas)

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

    n_guardias = _variables_de_carga(model, x, profesores, prof_slots, objetivo, alcanzables)
    desviaciones, max_dev = _terminos_de_equidad(
        model, n_guardias, profesores, prof_slots, objetivo
    )

    # OBJETIVO 2: agrupar (tramos de días seguidos, un carril, un recreo). Sustituye
    # al «span» (días entre la primera y la última guardia), que no distinguía un
    # tramo largo de muchas guardias sueltas, y a la concentración por zona, que no
    # miraba el recreo (2026-10-03).
    agrupacion = terminos_de_agrupacion(model, x, slots, prof_slots)
    logger.info("  ✓ Objetivo 2: tramos de días seguidos, un carril y un recreo")

    penalizacion_zona_preferida = _penalizacion_zona_preferida(
        model, x, profesores, prof_slots, slots
    )
    peor_zona_vacia = _peor_zona_vacia(model, vacios_por_zona)
    _fijar_objetivo(
        model, huecos_vacios, max_dev, desviaciones, agrupacion,
        penalizacion_zona_preferida, peor_zona_vacia,
    )

    if use_hints:
        _punto_de_partida(model, x, slots, profesores, prof_slots, slot_profs, objetivo,
                          reportar)

    solver, callback, status = _resolver(
        model, x, cuotas_ideales, timeout_seconds, reportar, cancelacion
    )
    es_optimo = _comprobar_solucion(solver, callback, status)

    reportar(90, "Generando guardias...")

    asignaciones: Dict[int, int] = {p.id: solver.Value(n_guardias[p.id]) for p in profesores}
    guardias = _guardias_de_la_solucion(solver, x, slots, curso_id)

    indice_equidad = _registrar_metricas(
        guardias, slots, profesores, asignaciones, cuotas_ideales, es_optimo
    )

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
