"""
Helpers de CP-SAT: estructuras de datos y funciones auxiliares.

Extraído de asignador_guardias_cpsat.py para reducir su tamaño (ARQ-05).
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Dict, List, Optional, Tuple

from ortools.sat.python import cp_model

from infrastructure.database.models import (
    Ausencia,
    Configuracion,
    Guardia,
    Profesor,
    Zona,
)
from services.calculador_guardias import (
    _parse_recreos_config,
    listar_dias_lectivos,
)
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


def _generar_slots(config: Configuracion, session) -> List[Slot]:
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


def _profesor_ausente(session, profesor_id: int, fecha: date) -> bool:
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


def _es_elegible_basico(profesor: Profesor, slot: Slot, session) -> bool:
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


class ProgresoSolver:
    """Buzón seguro entre los hilos de OR-Tools y el hilo que lanzó el solve (CRW-001).

    Los hilos internos del solver sólo escriben aquí; nadie más los toca. El hilo
    llamante recoge el último aviso con ``tomar()`` y es el único que informa hacia
    fuera, de modo que ninguna capa superior (Qt incluida) se ejecuta en un hilo
    creado por C++.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._pendiente: Optional[Tuple[int, str]] = None

    def publicar(self, porcentaje: int, mensaje: str = "") -> None:
        with self._lock:
            self._pendiente = (porcentaje, mensaje)

    def tomar(self) -> Optional[Tuple[int, str]]:
        """Devuelve el último aviso publicado y lo consume, o None si no hay nada."""
        with self._lock:
            pendiente, self._pendiente = self._pendiente, None
        return pendiente


class SolverCallback(cp_model.CpSolverSolutionCallback):
    """Callback de soluciones de CP-SAT.

    Se ejecuta en los hilos internos de OR-Tools, así que se limita a publicar en un
    ``ProgresoSolver``: no llama a callbacks de la aplicación ni toca la interfaz.
    """

    def __init__(
        self,
        variables: Dict,
        cuotas_ideales: Dict[int, float],
        progreso: Optional["ProgresoSolver"] = None,
    ):
        super().__init__()
        self.variables = variables
        self.cuotas_ideales = cuotas_ideales
        self.progreso = progreso
        self.solution_count = 0
        self.best_objective = float("inf")

    def on_solution_callback(self):
        self.solution_count += 1
        current_obj = self.ObjectiveValue()

        if current_obj < self.best_objective:
            self.best_objective = current_obj

            if self.progreso is not None:
                # Estimar progreso basado en mejora del objetivo
                porcentaje = min(85, 40 + self.solution_count * 2)
                self.progreso.publicar(
                    porcentaje, f"Solución {self.solution_count}: obj={current_obj}"
                )


def resolver_con_progreso(
    solver,
    model,
    callback: "SolverCallback",
    progreso: "ProgresoSolver",
    reportar: Callable[[int, str], None],
    cancelacion: Optional[threading.Event] = None,
    intervalo: float = 0.25,
) -> int:
    """Ejecuta ``solver.Solve`` en un hilo aparte y vigila desde el hilo llamante.

    El solve bloquea, así que corre en su propio hilo; el llamante se queda en un
    bucle que cada ``intervalo`` segundos recoge el progreso publicado y lo reporta.
    Así el callback de la aplicación se invoca siempre desde el hilo llamante
    (CRW-001) y la cancelación se propaga con ``stop_search()``, sin lanzar
    excepciones a través del callback C++ de CP-SAT (CRW-004).
    """
    resultado: Dict[str, object] = {}

    def _resolver():
        try:
            resultado["status"] = solver.Solve(model, callback)
        except BaseException as e:  # noqa: BLE001 - se re-lanza en el hilo llamante
            resultado["error"] = e

    hilo = threading.Thread(target=_resolver, name="cpsat-solve", daemon=True)
    hilo.start()

    try:
        while hilo.is_alive():
            hilo.join(intervalo)
            if cancelacion is not None and cancelacion.is_set():
                solver.stop_search()
            pendiente = progreso.tomar()
            if pendiente is not None:
                reportar(*pendiente)
    except BaseException:
        # Cancelación o error del propio reportar: parar el solver y esperar a que
        # sus hilos terminen antes de dejar salir la excepción.
        solver.stop_search()
        hilo.join(timeout=30)
        raise

    hilo.join()

    if "error" in resultado:
        raise resultado["error"]

    pendiente = progreso.tomar()
    if pendiente is not None:
        reportar(*pendiente)

    return resultado["status"]


