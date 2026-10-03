"""Reparto agrupado: cada profesor en un carril y en bloques de días seguidos.

Un carril es un recreo en una zona: necesita a alguien todos los días. Llevar a
cada profesor por un solo carril, días seguidos hasta completar lo suyo, da a la
vez lo que pide el centro: guardias juntas en el tiempo, en la misma zona y en el
mismo recreo.

Medido con los calendarios reales de 2025/26 y 2026/27 (2026-10-03): el
generador anterior dejaba a un profesor típico en 10-12 tramos sueltos, 3-4
zonas y dos recreos; con esto quedan 2-3 tramos, una zona y un recreo, con la
equidad exacta.

El reparto se hace en dos pasos para que la equidad nunca se cambie por
agrupación:

1. `objetivos_justos`: cuántas guardias le tocan a cada uno, lo más cerca posible
   de su cuota con los días que de verdad puede hacer.
2. Los carriles (`repartir_por_carriles` + `reparar_equidad`) dan un calendario
   agrupado con esos objetivos, que CP-SAT recibe como punto de partida y pule.

Las cuotas del curso entero se concentran en el periodo de quien tiene fechas de
inicio o fin (decisión de CarlosFB, 2026-10-03); si no le caben, con una guardia
al día como mucho, el sobrante lo reparten los de su mismo turno.
"""

import bisect
import threading
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from ortools.sat.python import cp_model

from utils import get_logger

logger = get_logger(__name__)

#: Pesos del objetivo de agrupación. La equidad va aparte y pesa mucho más
#: (una guardia de diferencia cuesta más que cualquier mejora de agrupación).
PESO_TRAMO = 60  # cada tramo de días seguidos más allá del primero
PESO_CARRIL = 40  # cada carril (recreo y zona) distinto
PESO_RECREO = 40  # cada recreo distinto


def cuotas_alcanzables(
    slots: list, profesores: list, prof_slots: Dict[int, List[int]], cuotas: Dict[int, int]
) -> Dict[int, int]:
    """Ninguna cuota por encima de los días que el profesor puede hacer.

    Lo que sobra se reparte entre los de su mismo turno que tienen sitio, en
    proporción a su cuota.
    """
    dias = {p.id: {slots[i].fecha for i in prof_slots.get(p.id, [])} for p in profesores}
    turnos = {p.id: {slots[i].turno for i in prof_slots.get(p.id, [])} for p in profesores}
    capacidad = {pid: len(d) for pid, d in dias.items()}
    ajustadas = {p.id: min(cuotas.get(p.id, 0), capacidad[p.id]) for p in profesores}

    sobrante: Dict[str, float] = defaultdict(float)
    for p in profesores:
        exceso = cuotas.get(p.id, 0) - ajustadas[p.id]
        if exceso > 0 and turnos[p.id]:
            for turno in turnos[p.id]:
                sobrante[turno] += exceso / len(turnos[p.id])

    for turno, cantidad in sobrante.items():
        receptores = [
            p for p in profesores
            if turno in turnos[p.id] and cuotas.get(p.id, 0) <= capacidad[p.id]
        ]
        peso_total = sum(cuotas.get(p.id, 0) or 1 for p in receptores)
        for p in receptores:
            extra = round(cantidad * (cuotas.get(p.id, 0) or 1) / peso_total)
            ajustadas[p.id] = min(capacidad[p.id], ajustadas[p.id] + extra)

    imposibles = sum(1 for p in profesores if cuotas.get(p.id, 0) > capacidad[p.id])
    if imposibles:
        logger.info(f"  ✓ {imposibles} cuotas no caben en los días del profesor: se reparten")
    return ajustadas


def objetivos_justos(
    slots: list,
    profesores: list,
    prof_slots: Dict[int, List[int]],
    slot_profs: Dict[int, List[int]],
    cuotas: Dict[int, int],
    segundos: float,
    cancelacion: Optional[threading.Event] = None,
) -> Dict[int, int]:
    """Guardias de cada profesor en el reparto más justo que admiten los datos."""
    from services._asignador_cpsat_helpers import (
        ProgresoSolver,
        SolverCallback,
        resolver_con_progreso,
    )

    modelo = cp_model.CpModel()
    x = {(pid, i): modelo.NewBoolVar("") for pid, ids in prof_slots.items() for i in ids}
    vacios = []
    for i, pids in slot_profs.items():
        if pids:
            modelo.AddAtMostOne(x[pid, i] for pid in pids)
            vacios.append(1 - sum(x[pid, i] for pid in pids))
    _una_al_dia(modelo, x, slots, prof_slots)
    desviaciones, maxima = _desviaciones(modelo, x, prof_slots, profesores, cuotas)
    # Cubrir va antes que todo: un hueco vacío cuesta más que cualquier desviación.
    modelo.Minimize(1_000_000 * sum(vacios) + 100 * maxima + sum(desviaciones))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = segundos
    progreso = ProgresoSolver()
    estado = resolver_con_progreso(
        solver, modelo, SolverCallback(x, cuotas, progreso), progreso,
        lambda *_: None, cancelacion,
    )
    if estado not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logger.warning("  ⚠️ No se pudo calcular el reparto justo; se usan las cuotas")
        return dict(cuotas)
    objetivos = Counter(pid for (pid, _i), var in x.items() if solver.Value(var))
    logger.info(f"  ✓ Reparto justo: desviación máxima {solver.Value(maxima)} guardias")
    return {p.id: objetivos.get(p.id, 0) for p in profesores}


def repartir_por_carriles(
    slots: list,
    profesores: list,
    prof_slots: Dict[int, List[int]],
    slot_profs: Dict[int, List[int]],
    objetivo: Dict[int, int],
) -> Dict[int, int]:
    """Calendario agrupado: `{índice de hueco: profesor}`.

    Día a día, quien lleva un carril sigue en él mientras le queden guardias. Un
    carril libre lo coge quien menos margen tiene para completar lo suyo (por sus
    fechas o sus días), sin quitárselo a quien sólo falta ese día.
    """
    elegibles = {pid: set(ids) for pid, ids in prof_slots.items()}
    por_dia: Dict = defaultdict(list)
    for i, s in enumerate(slots):
        por_dia[s.fecha].append(i)
    dias = sorted(por_dia)
    dias_de = {pid: sorted({slots[i].fecha for i in ids}) for pid, ids in prof_slots.items()}
    zona_preferida = {p.id: p.zona_preferida_id for p in profesores}
    restante = {p.id: objetivo.get(p.id, 0) for p in profesores}
    hechas: Counter = Counter()
    lleva: Dict = {}  # carril -> profesor
    carril_de: Dict[int, tuple] = {}  # profesor -> su carril
    asignacion: Dict[int, int] = {}

    def margen(pid, dia):
        quedan = len(dias_de.get(pid, [])) - bisect.bisect_left(dias_de.get(pid, []), dia)
        return quedan - restante[pid]

    for dia in dias:
        ocupados = set()
        huecos = sorted(por_dia[dia], key=lambda i: (slots[i].recreo_id, slots[i].zona_id))
        pendientes = []
        for i in huecos:
            carril = (slots[i].recreo_id, slots[i].zona_id)
            pid = lleva.get(carril)
            if pid and restante[pid] > 0 and pid not in ocupados and i in elegibles.get(pid, ()):
                asignacion[i] = pid
                ocupados.add(pid)
                restante[pid] -= 1
                hechas[pid] += 1
            else:
                pendientes.append(i)

        for i in sorted(pendientes, key=lambda i: len(slot_profs.get(i, []))):
            carril = (slots[i].recreo_id, slots[i].zona_id)
            candidatos = [pid for pid in slot_profs.get(i, []) if pid not in ocupados]
            if not candidatos:
                continue
            con_cuota = [pid for pid in candidatos if restante[pid] > 0]
            if con_cuota:
                def clave(pid):
                    otro = carril_de.get(pid)
                    lleva_otro = otro not in (None, carril) and lleva.get(otro) == pid
                    return (
                        lleva_otro,
                        margen(pid, dia),
                        carril_de.get(pid) != carril,
                        zona_preferida.get(pid) not in (None, slots[i].zona_id),
                        pid,
                    )

                elegido = min(con_cuota, key=clave)
                titular = lleva.get(carril)
                if not (titular and restante.get(titular, 0) > 0):
                    viejo = carril_de.get(elegido)
                    if viejo and viejo != carril and lleva.get(viejo) == elegido:
                        lleva.pop(viejo)
                    lleva[carril] = elegido
                    carril_de[elegido] = carril
                restante[elegido] -= 1
            else:
                # Objetivos cumplidos: lo cubre quien menos se pasa del suyo.
                elegido = min(candidatos, key=lambda pid: (hechas[pid] - objetivo.get(pid, 0), pid))
            asignacion[i] = elegido
            ocupados.add(elegido)
            hechas[elegido] += 1
    return asignacion


def reparar_equidad(
    slots: list,
    asignacion: Dict[int, int],
    prof_slots: Dict[int, List[int]],
    objetivo: Dict[int, int],
    rondas: int = 50,
) -> Dict[int, int]:
    """Pasa días de quien va por encima de su objetivo a quien va por debajo.

    Se prefieren días pegados a un tramo del que recibe y en el borde del tramo
    del que cede, en el mismo carril, para no romper la agrupación.
    """
    elegibles = {pid: set(ids) for pid, ids in prof_slots.items()}
    fechas = sorted({s.fecha for s in slots})
    orden = {d: k for k, d in enumerate(fechas)}
    for _ in range(rondas):
        cuenta = Counter(asignacion.values())
        diferencia = {pid: cuenta.get(pid, 0) - objetivo.get(pid, 0) for pid in prof_slots}
        faltan = sorted((pid for pid, d in diferencia.items() if d < 0), key=diferencia.get)
        if not faltan:
            break
        dias_de: Dict[int, set] = defaultdict(set)
        ocupa: Dict[int, set] = defaultdict(set)
        for i, pid in asignacion.items():
            s = slots[i]
            dias_de[pid].add(s.fecha)
            ocupa[pid].add((s.recreo_id, s.zona_id, s.fecha))

        def vecinos(pid, s):
            k = orden[s.fecha]
            return sum(
                1 for j in (k - 1, k + 1)
                if 0 <= j < len(fechas) and (s.recreo_id, s.zona_id, fechas[j]) in ocupa[pid]
            )

        movido = False
        for b in faltan:
            opciones = [
                (-(2 * vecinos(b, slots[i]) - vecinos(a, slots[i])), -diferencia[a], i)
                for i, a in asignacion.items()
                if a != b and diferencia[a] > 0
                and slots[i].fecha not in dias_de[b] and i in elegibles.get(b, ())
            ]
            if not opciones:
                continue
            i = min(opciones)[2]
            a = asignacion[i]
            asignacion[i] = b
            diferencia[a] -= 1
            diferencia[b] += 1
            dias_de[b].add(slots[i].fecha)
            dias_de[a].discard(slots[i].fecha)
            movido = True
        if not movido:
            break
    return asignacion


def terminos_de_agrupacion(modelo, x, slots: list, prof_slots: Dict[int, List[int]]) -> list:
    """Términos del objetivo que premian tramos largos, un carril y un recreo.

    Los tramos se cuentan sobre los días que cada profesor puede hacer: un día
    que tiene vetado no corta su tramo.
    """
    terminos = []
    for pid, ids in prof_slots.items():
        if not ids:
            continue
        por_dia, por_carril, por_recreo = defaultdict(list), defaultdict(list), defaultdict(list)
        for i in ids:
            s = slots[i]
            por_dia[s.fecha].append(i)
            por_carril[(s.recreo_id, s.zona_id)].append(i)
            por_recreo[s.recreo_id].append(i)
        trabaja = {}
        for dia, lista in por_dia.items():
            trabaja[dia] = modelo.NewBoolVar("")
            modelo.Add(sum(x[pid, i] for i in lista) == trabaja[dia])  # una al día
        propios = sorted(trabaja)
        for k, dia in enumerate(propios):
            empieza = modelo.NewBoolVar("")
            anterior = trabaja[propios[k - 1]] if k else 0
            modelo.Add(empieza >= trabaja[dia] - anterior)
            terminos.append(PESO_TRAMO * empieza)
        for grupo, peso in ((por_carril, PESO_CARRIL), (por_recreo, PESO_RECREO)):
            for lista in grupo.values():
                usa = modelo.NewBoolVar("")
                for i in lista:
                    modelo.AddImplication(x[pid, i], usa)
                terminos.append(peso * usa)
    return terminos


def _una_al_dia(modelo, x, slots, prof_slots) -> None:
    for pid, ids in prof_slots.items():
        por_dia = defaultdict(list)
        for i in ids:
            por_dia[slots[i].fecha].append(i)
        for lista in por_dia.values():
            if len(lista) > 1:
                modelo.AddAtMostOne(x[pid, i] for i in lista)


def _desviaciones(modelo, x, prof_slots, profesores, objetivo):
    desviaciones = []
    for p in profesores:
        ids = prof_slots.get(p.id, [])
        if not ids:
            continue
        n = sum(x[p.id, i] for i in ids)
        meta = objetivo.get(p.id, 0)
        d = modelo.NewIntVar(0, len(ids) + meta, "")
        modelo.Add(d >= n - meta)
        modelo.Add(d >= meta - n)
        desviaciones.append(d)
    maxima = modelo.NewIntVar(0, 10_000, "")
    modelo.AddMaxEquality(maxima, desviaciones or [0])
    return desviaciones, maxima
