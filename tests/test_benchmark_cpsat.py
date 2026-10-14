"""
Benchmarks de rendimiento (pytest-benchmark).

Mide el tiempo de las fases más costosas del sistema para detectar
regresiones silenciosas de rendimiento entre versiones.

Ejecución:
    pytest tests/test_benchmark_cpsat.py --benchmark-only
    pytest tests/test_benchmark_cpsat.py --benchmark-compare

Excluidos del test normal: marcados con 'benchmark' (ver pytest.ini).
"""

import sys
import string
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infrastructure.database.models import Base, Configuracion, CursoEscolar, Profesor, Zona
from sync.sync_manager import UserAuth

pytestmark = pytest.mark.benchmark


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="module")
def session_benchmark():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    curso = CursoEscolar(
        nombre="Bench 2025-2026",
        anio_inicio=2025,
        anio_fin=2026,
        fecha_inicio=date(2025, 9, 1),
        fecha_fin=date(2026, 6, 30),
    )
    db.add(curso)
    db.flush()

    config = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=date(2025, 9, 1),
        fecha_fin_curso=date(2026, 6, 30),
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 0),
        ajuste_tutores=0.9,
        ajuste_no_tutores=1.0,
        curso_activo_id=curso.id,
    )
    db.add(config)

    zona = Zona(nombre_zona="Patio Bench")
    db.add(zona)
    db.flush()

    for i in range(15):
        turno = "mañana" if i < 10 else "tarde"
        prof = Profesor(
            nombre_completo=f"Profesor Bench {i:02d}",
            horas_contrato=20.0,
            porcentaje_jornada=80.0,
            turno=turno,
            activo=True,
        )
        db.add(prof)

    db.commit()
    yield db
    db.close()


# ============================================================================
# BENCHMARKS: password validation
# ============================================================================


def test_bench_password_policy_valida(benchmark):
    """Mide el tiempo de validar una contraseña que cumple la política."""
    result = benchmark(UserAuth.validate_password_policy, "Segura1234!")
    assert result[0] is True


def test_bench_password_policy_invalida(benchmark):
    """Mide el tiempo de rechazar una contraseña inválida."""
    result = benchmark(UserAuth.validate_password_policy, "corta")
    assert result[0] is False


# ============================================================================
# BENCHMARKS: generación de slots
# ============================================================================


def test_bench_generar_slots(benchmark, session_benchmark):
    """Mide el tiempo de generar los slots a cubrir a partir de la configuración."""
    from services._asignador_cpsat_helpers import _generar_slots

    config = session_benchmark.query(Configuracion).first()
    result = benchmark(_generar_slots, config, session_benchmark)
    assert isinstance(result, list)


# ============================================================================
# BENCHMARKS: JWT encode/decode
# ============================================================================


def test_bench_jwt_encode(benchmark):
    """Mide el tiempo de generar un JWT."""
    from api.auth import _create_access_token

    result = benchmark(_create_access_token, "benchmark_user")
    assert isinstance(result, str)


def test_bench_jwt_decode(benchmark):
    """Mide el tiempo de verificar un JWT."""
    from api.auth import _create_access_token, get_current_user

    token = _create_access_token("bench_user")
    result = benchmark(get_current_user, token)
    assert result == "bench_user"


# ============================================================================
# BENCHMARKS: DataExporter export a JSON
# ============================================================================


def test_bench_export_to_json(benchmark, session_benchmark, tmp_path):
    """Mide el tiempo de exportar la BD completa a JSON."""
    from sync.data_exporter import DataExporter

    output = tmp_path / "bench_export.json"
    result = benchmark(DataExporter.export_to_json, session_benchmark, output)
    assert result is True
