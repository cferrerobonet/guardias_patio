"""
10 escenarios predefinidos para la suite de compliance.

Cada función devuelve un dict listo para pasar a build_scenario():
  prof_configs, n_zonas, inicio, fin

Los ProfCfg son dicts con campos:
  nombre, turno, horas_contrato, porcentaje_jornada, tutor,
  fecha_inicio_guardias, fecha_fin_guardias,
  dias_semana_permitidos, recreos_permitidos, zona_preferida_idx
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------


@dataclass
class ScenarioDef:
    nombre: str
    descripcion: str
    prof_configs: list[dict[str, Any]]
    n_zonas: int = 2
    inicio: date = field(default_factory=lambda: date(2024, 9, 2))
    fin: date = field(default_factory=lambda: date(2024, 9, 13))
    restricciones_bajo_prueba: list[str] = field(default_factory=list)


def _prof(nombre: str, turno: str, **kwargs) -> dict:
    return {"nombre": nombre, "turno": turno, **kwargs}


# ---------------------------------------------------------------------------
# S01 — Base equidad (10 prof sin restricciones)
# ---------------------------------------------------------------------------


def scenario_S01() -> ScenarioDef:
    """10 profesores sin restricciones, mix de turno mañana y tarde."""
    profs = [_prof(f"Mañana {i}", "mañana") for i in range(1, 6)] + [
        _prof(f"Tarde {i}", "tarde") for i in range(1, 6)
    ]
    return ScenarioDef(
        nombre="S01_base_equidad",
        descripcion="10 prof sin restricciones, turno mixto",
        prof_configs=profs,
        n_zonas=2,
        restricciones_bajo_prueba=["R1", "R8", "R9"],
    )


# ---------------------------------------------------------------------------
# S02 — Turnos segregados
# ---------------------------------------------------------------------------


def scenario_S02() -> ScenarioDef:
    """5 profesores de mañana + 5 de tarde, sin mezcla posible."""
    profs = [_prof(f"M{i}", "mañana") for i in range(1, 6)] + [
        _prof(f"T{i}", "tarde") for i in range(1, 6)
    ]
    return ScenarioDef(
        nombre="S02_turnos_segregados",
        descripcion="5 mañana + 5 tarde — verifica R1 turno",
        prof_configs=profs,
        n_zonas=1,
        restricciones_bajo_prueba=["R1"],
    )


# ---------------------------------------------------------------------------
# S03 — Fecha inicio diferida
# ---------------------------------------------------------------------------


def scenario_S03() -> ScenarioDef:
    """3 prof con fecha_inicio_guardias a mitad del curso (sep 8)."""
    profs = [_prof(f"Normal {i}", "mañana") for i in range(1, 5)] + [
        _prof(
            f"Diferido {i}",
            "mañana",
            fecha_inicio_guardias=date(2024, 9, 8),
        )
        for i in range(1, 4)
    ]
    return ScenarioDef(
        nombre="S03_fecha_inicio_diferida",
        descripcion="3 prof con fecha_inicio_guardias=2024-09-08",
        prof_configs=profs,
        n_zonas=1,
        restricciones_bajo_prueba=["R3"],
    )


# ---------------------------------------------------------------------------
# S04 — Fecha fin anticipada
# ---------------------------------------------------------------------------


def scenario_S04() -> ScenarioDef:
    """3 prof con fecha_fin_guardias el 2024-09-09 (2/3 del curso de 2 semanas)."""
    profs = [_prof(f"Normal {i}", "mañana") for i in range(1, 5)] + [
        _prof(
            f"Finaliza {i}",
            "mañana",
            fecha_fin_guardias=date(2024, 9, 9),
        )
        for i in range(1, 4)
    ]
    return ScenarioDef(
        nombre="S04_fecha_fin_anticipada",
        descripcion="3 prof con fecha_fin_guardias=2024-09-09",
        prof_configs=profs,
        n_zonas=1,
        restricciones_bajo_prueba=["R4"],
    )


# ---------------------------------------------------------------------------
# S05 — Recreos lista simple
# ---------------------------------------------------------------------------


def scenario_S05() -> ScenarioDef:
    """4 prof con recreos_permitidos=[1] o [2] (solo un recreo por prof)."""
    profs = [
        _prof("SoloR1 a", "mañana", recreos_permitidos=[1]),
        _prof("SoloR1 b", "mañana", recreos_permitidos=[1]),
        _prof("SoloR2 a", "mañana", recreos_permitidos=[2]),
        _prof("SoloR2 b", "mañana", recreos_permitidos=[2]),
        # Profesores sin restricción para rellenar slots
        _prof("Libre 1", "mañana"),
        _prof("Libre 2", "mañana"),
        _prof("Tarde 1", "tarde"),
        _prof("Tarde 2", "tarde"),
    ]
    return ScenarioDef(
        nombre="S05_recreos_lista",
        descripcion="4 prof con recreos_permitidos=[1] o [2]",
        prof_configs=profs,
        n_zonas=1,
        restricciones_bajo_prueba=["R5"],
    )


# ---------------------------------------------------------------------------
# S06 — Recreos dict por día
# ---------------------------------------------------------------------------


def scenario_S06() -> ScenarioDef:
    """2 prof con recreos_permitidos como dict por día de semana."""
    # Lun/Mié/Vie → recreo 1; Mar/Jue → recreo 2
    recreos_dict = {"0": [1], "1": [2], "2": [1], "3": [2], "4": [1]}
    profs = [
        _prof("DictRecreos A", "mañana", recreos_permitidos=recreos_dict),
        _prof("DictRecreos B", "mañana", recreos_permitidos=recreos_dict),
        # Relleno
        _prof("Libre 1", "mañana"),
        _prof("Libre 2", "mañana"),
        _prof("Libre 3", "mañana"),
        _prof("Tarde 1", "tarde"),
        _prof("Tarde 2", "tarde"),
        _prof("Tarde 3", "tarde"),
    ]
    return ScenarioDef(
        nombre="S06_recreos_dict",
        descripcion='2 prof con recreos_permitidos={"0":[1],"1":[2],...}',
        prof_configs=profs,
        n_zonas=1,
        restricciones_bajo_prueba=["R6"],
    )


# ---------------------------------------------------------------------------
# S07 — Días semana limitados (CP-SAT xfail)
# ---------------------------------------------------------------------------


def scenario_S07() -> ScenarioDef:
    """3 prof con dias_semana_permitidos=[0,2,4] (lunes, miércoles, viernes)."""
    profs = (
        [_prof(f"SoloDias {i}", "mañana", dias_semana_permitidos=[0, 2, 4]) for i in range(1, 4)]
        + [_prof(f"Libre {i}", "mañana") for i in range(1, 4)]
        + [_prof(f"Tarde {i}", "tarde") for i in range(1, 4)]
    )
    return ScenarioDef(
        nombre="S07_dias_semana",
        descripcion="3 prof con dias_semana_permitidos=[0,2,4]",
        prof_configs=profs,
        n_zonas=1,
        restricciones_bajo_prueba=["R7"],
    )


# ---------------------------------------------------------------------------
# S08 — Ausencias en curso
# ---------------------------------------------------------------------------


def scenario_S08() -> ScenarioDef:
    """Base de 8 profesores; 2 tendrán ausencia en la segunda semana."""
    profs = [_prof(f"Mañana {i}", "mañana") for i in range(1, 5)] + [
        _prof(f"Tarde {i}", "tarde") for i in range(1, 5)
    ]
    # Las ausencias se crean en el test con build_ausencia (requieren IDs de BD)
    return ScenarioDef(
        nombre="S08_ausencias",
        descripcion="2 prof con ausencia semana 2024-09-09..13",
        prof_configs=profs,
        n_zonas=1,
        restricciones_bajo_prueba=["R2"],
    )


# ---------------------------------------------------------------------------
# S09 — Zona preferida
# ---------------------------------------------------------------------------


def scenario_S09() -> ScenarioDef:
    """5 prof con zona_preferida_id distinto para verificar R10."""
    profs = [
        _prof("ZonaA 1", "mañana", zona_preferida_idx=0),
        _prof("ZonaA 2", "mañana", zona_preferida_idx=0),
        _prof("ZonaB 1", "mañana", zona_preferida_idx=1),
        _prof("ZonaB 2", "mañana", zona_preferida_idx=1),
        _prof("ZonaB 3", "mañana", zona_preferida_idx=1),
        _prof("Tarde 1", "tarde"),
        _prof("Tarde 2", "tarde"),
        _prof("Tarde 3", "tarde"),
    ]
    return ScenarioDef(
        nombre="S09_zona_preferida",
        descripcion="5 prof con zona preferida definida",
        prof_configs=profs,
        n_zonas=2,
        restricciones_bajo_prueba=["R10"],
    )


# ---------------------------------------------------------------------------
# S10 — Mixto completo (regression)
# ---------------------------------------------------------------------------


def scenario_S10() -> ScenarioDef:
    """
    15 profesores con combinación de todas las restricciones activas.
    Curso de 3 semanas para mayor cobertura estadística.
    """
    recreos_dict = {"0": [1], "1": [2], "2": [1], "3": [2], "4": [1]}
    profs = [
        # Sin restricciones
        _prof("Libre M1", "mañana"),
        _prof("Libre M2", "mañana"),
        _prof("Libre T1", "tarde"),
        _prof("Libre T2", "tarde"),
        # Turno completo
        _prof("Completo 1", "completo", horas_contrato=25, porcentaje_jornada=100),
        # Fecha inicio diferida
        _prof("DifInicio 1", "mañana", fecha_inicio_guardias=date(2024, 9, 8)),
        _prof("DifInicio 2", "mañana", fecha_inicio_guardias=date(2024, 9, 10)),
        # Fecha fin anticipada
        _prof("FinAntic 1", "tarde", fecha_fin_guardias=date(2024, 9, 16)),
        # Recreos lista
        _prof("RecLista 1", "mañana", recreos_permitidos=[1]),
        _prof("RecLista 2", "tarde", recreos_permitidos=[3]),
        # Recreos dict
        _prof("RecDict 1", "mañana", recreos_permitidos=recreos_dict),
        # Días semana
        _prof("DiasLim 1", "mañana", dias_semana_permitidos=[0, 2, 4]),
        # Zona preferida (idx 0 = Zona 1, idx 1 = Zona 2)
        _prof("ZonaA 1", "mañana", zona_preferida_idx=0),
        _prof("ZonaB 1", "tarde", zona_preferida_idx=1),
        # Tutor
        _prof("Tutor 1", "mañana", tutor=True),
    ]
    return ScenarioDef(
        nombre="S10_mixto_completo",
        descripcion="15 prof con todas las restricciones activas",
        prof_configs=profs,
        n_zonas=2,
        inicio=date(2024, 9, 2),
        fin=date(2024, 9, 20),
        restricciones_bajo_prueba=[
            "R1",
            "R2",
            "R3",
            "R4",
            "R5",
            "R6",
            "R7",
            "R8",
            "R9",
            "R10",
            "R11",
            "R12",
            "R13",
        ],
    )
