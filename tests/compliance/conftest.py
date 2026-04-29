"""
Fixtures para la suite de tests de cumplimiento de restricciones.

Proporciona:
- engine/session propios (SQLite en memoria, scope=function)
- build_scenario(): construye BD con profesores, zonas y config
- run_cpsat() / run_v4(): ejecutan los algoritmos contra la sesión activa
- compliance_reporter: recolector de resultados por sesión → JSON
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import date, time
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from infrastructure.database.models import (  # noqa: E402
    Ausencia,
    Base,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)

# ---------------------------------------------------------------------------
# Constantes compartidas
# ---------------------------------------------------------------------------

# 2 semanas sin festivos (lunes 2 sep → viernes 13 sep 2024 = 10 días lectivos)
INICIO_CURSO = date(2024, 9, 2)
FIN_CURSO = date(2024, 9, 13)

# 3 semanas para escenario mixto S10
FIN_CURSO_3W = date(2024, 9, 20)

RECREOS_CONFIG = json.dumps(
    [
        {"id": 1, "etiqueta": "R1 Mañana", "turno": "mañana", "hora": "11:00"},
        {"id": 2, "etiqueta": "R2 Mañana", "turno": "mañana", "hora": "12:00"},
        {"id": 3, "etiqueta": "R1 Tarde", "turno": "tarde", "hora": "16:00"},
        {"id": 4, "etiqueta": "R2 Tarde", "turno": "tarde", "hora": "17:00"},
    ]
)
# Sin "zonas" → _generar_slots usa len(zonas), garantizando que todas las zonas reciben slots

# ---------------------------------------------------------------------------
# Fixtures de BD
# ---------------------------------------------------------------------------

_compliance_buffer: list = []


@pytest.fixture(scope="function")
def engine():
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture(scope="function")
def session(engine):
    SessionLocal = sessionmaker(bind=engine)
    sess = SessionLocal()
    yield sess
    sess.close()


# ---------------------------------------------------------------------------
# build_scenario
# ---------------------------------------------------------------------------


def _build_scenario(
    session,
    prof_configs: list[dict[str, Any]],
    n_zonas: int = 2,
    inicio: date = INICIO_CURSO,
    fin: date = FIN_CURSO,
) -> tuple[list[Profesor], list[Zona]]:
    """
    Popula la BD con la configuración mínima necesaria para que los algoritmos
    funcionen: Configuracion, CursoEscolar, Zonas y Profesores.

    prof_configs: lista de dicts con campos de Profesor.
      Campos especiales:
        - dias_semana_permitidos: list[int] → serializado a JSON
        - recreos_permitidos: list|dict → serializado a JSON
        - zona_preferida_idx: int → índice en la lista de zonas creadas
    """
    config = Configuracion(
        anio_inicio_curso=inicio.year,
        fecha_inicio_curso=inicio,
        fecha_fin_curso=fin,
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        activar_festivos_automaticos=False,
        recreos_config=RECREOS_CONFIG,
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        algoritmo_asignacion="v2.9",
    )
    session.add(config)

    curso = CursoEscolar(
        nombre=f"Test {inicio.year}/{fin.year}",
        anio_inicio=inicio.year,
        anio_fin=fin.year,
        fecha_inicio=inicio,
        fecha_fin=fin,
        activo=True,
    )
    session.add(curso)
    session.flush()

    zonas = []
    for i in range(n_zonas):
        z = Zona(nombre_zona=f"Zona {i + 1}", descripcion=f"Zona de prueba {i + 1}")
        session.add(z)
        zonas.append(z)
    session.flush()

    profesores = []
    for i, cfg in enumerate(prof_configs):
        dias_raw = cfg.get("dias_semana_permitidos")
        recreos_raw = cfg.get("recreos_permitidos")
        zona_idx = cfg.get("zona_preferida_idx")

        p = Profesor(
            nombre_completo=cfg.get("nombre", f"Prof {i + 1}"),
            horas_contrato=cfg.get("horas_contrato", 25.0),
            porcentaje_jornada=cfg.get("porcentaje_jornada", 100.0),
            turno=cfg.get("turno", "mañana"),
            tutor=cfg.get("tutor", False),
            activo=True,
            fecha_inicio_guardias=cfg.get("fecha_inicio_guardias"),
            fecha_fin_guardias=cfg.get("fecha_fin_guardias"),
            dias_semana_permitidos=json.dumps(dias_raw) if dias_raw is not None else None,
            recreos_permitidos=json.dumps(recreos_raw) if recreos_raw is not None else None,
            zona_preferida_id=zonas[zona_idx].id
            if zona_idx is not None and zona_idx < len(zonas)
            else None,
        )
        session.add(p)
        profesores.append(p)

    session.commit()
    return profesores, zonas


@pytest.fixture
def build_scenario(session):
    """Fixture que devuelve una función para construir escenarios en la BD."""

    def _build(prof_configs, n_zonas=2, inicio=INICIO_CURSO, fin=FIN_CURSO):
        return _build_scenario(session, prof_configs, n_zonas, inicio, fin)

    return _build


@pytest.fixture
def build_ausencia(session):
    """Fixture que devuelve una función para crear ausencias."""

    def _create(profesor_id, fecha_inicio, fecha_fin, tipo="baja_medica"):
        a = Ausencia(
            profesor_id=profesor_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
            activa=True,
        )
        session.add(a)
        session.commit()
        return a

    return _create


# ---------------------------------------------------------------------------
# run_cpsat / run_v4
# ---------------------------------------------------------------------------


@pytest.fixture
def run_cpsat(session):
    """Devuelve callable que ejecuta CP-SAT con timeout corto para tests."""

    def _run(timeout: float = 20.0) -> tuple[list[Guardia], dict]:
        from services.asignador_guardias_cpsat import generar_guardias_cpsat

        return generar_guardias_cpsat(session, timeout_seconds=timeout)

    return _run


@pytest.fixture
def run_v4(session):
    """Devuelve callable que ejecuta el algoritmo v4 híbrido."""

    def _run() -> tuple[list[Guardia], dict]:
        from services.asignador_guardias_v4_hibrido import generar_guardias_v4_hibrido

        return generar_guardias_v4_hibrido(session)

    return _run


# ---------------------------------------------------------------------------
# Compliance reporter (recolector de resultados)
# ---------------------------------------------------------------------------


class _ComplianceReporterCollector:
    def __init__(self, buffer: list):
        self._buf = buffer

    def record(self, escenario: str, algoritmo: str, results: list):
        self._buf.append(
            {
                "escenario": escenario,
                "algoritmo": algoritmo,
                "results": [asdict(r) for r in results],
            }
        )


@pytest.fixture(scope="session")
def compliance_reporter():
    return _ComplianceReporterCollector(_compliance_buffer)


def pytest_sessionfinish(session, exitstatus):
    if _compliance_buffer:
        from tests.compliance.compliance_reporter import ComplianceReporter

        ComplianceReporter.save_session(_compliance_buffer)
