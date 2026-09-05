"""Fixtures de la suite de auditoría.

- `db_fichero`: BD SQLite real en fichero (tmp_path) con los mismos PRAGMAs que producción.
- `session_fichero`: sesión sobre esa BD (expire_on_commit=False como en db_manager).
- `configuracion_basica`: curso, recreos, 2 zonas y 4 profesores para generar guardias.
"""

import json
from datetime import date, time

import pytest
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Configuracion, CursoEscolar


def pytest_collection_modifyitems(items):
    for item in items:
        if "tests/audit" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.audit)


@pytest.fixture
def db_fichero(tmp_path):
    """Engine SQLite en fichero con PRAGMAs equivalentes a db_manager (journal DELETE, FK on)."""
    db_path = tmp_path / "guardias_patio_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        poolclass=pool.NullPool,
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=DELETE")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_fichero(db_fichero):
    factory = sessionmaker(bind=db_fichero, autoflush=False, expire_on_commit=False)
    s = factory()
    yield s
    s.close()


@pytest.fixture
def configuracion_basica(session, zona_factory, profesor_factory):
    """Escenario mínimo generable (en memoria, sesión estándar del proyecto)."""
    zona_factory(nombre_zona="Patio A")
    zona_factory(nombre_zona="Patio B")
    profesor_factory("García, Juan", turno="mañana", horas_contrato=25.0)
    profesor_factory("López, Ana", turno="mañana", horas_contrato=20.0)
    profesor_factory("Pérez, Luis", turno="tarde", horas_contrato=18.0)
    profesor_factory("Ruiz, Marta", turno="mixto", horas_contrato=30.0)
    session.flush()
    config = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=date(2025, 9, 15),
        fecha_fin_curso=date(2025, 10, 15),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        algoritmo_asignacion="cpsat",
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=False,
        recreos_config=json.dumps(
            [
                {"id": 1, "etiqueta": "Recreo 1 Mañana", "turno": "mañana", "hora": "11:00"},
                {"id": 2, "etiqueta": "Recreo 2 Mañana", "turno": "mañana", "hora": "12:00"},
                {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:00"},
            ]
        ),
    )
    session.add(config)
    session.commit()
    return config


@pytest.fixture
def curso_generable(session, configuracion_basica):
    """Escenario con TODOS los prerrequisitos de generación cubiertos.

    `configuracion_basica` deja fechas, recreos, zonas y profesores, pero no un
    curso escolar activo, que es el primer requisito del preflight.
    """
    curso = CursoEscolar(
        anio_inicio=2025,
        anio_fin=2026,
        fecha_inicio=date(2025, 7, 1),
        fecha_fin=date(2026, 6, 30),
        nombre="Curso 2025/2026",
        activo=True,
        cerrado=False,
    )
    session.add(curso)
    session.commit()
    return curso
