"""Fixtures compartidas para la suite de tests UI (tests/ui/)."""

import json
from datetime import date, time

import pytest

from infrastructure.database.models import Configuracion


@pytest.fixture
def ui_session(session, zona_factory, profesor_factory):
    """BD con profesores y zonas suficientes para probar cualquier form."""
    zona_a = zona_factory(nombre_zona="Patio A")
    zona_b = zona_factory(nombre_zona="Patio B")
    profesor_factory(
        "García López, María",
        turno="mañana",
        horas_contrato=25.0,
        zona_preferida_id=zona_a.id,
    )
    profesor_factory("Martínez Ruiz, Juan", turno="tarde", horas_contrato=18.0)
    profesor_factory("Sánchez Pérez, Ana", turno="mixto", horas_contrato=30.0, tutor=True)
    session.flush()
    return session


@pytest.fixture
def ui_config(session):
    """Configuración básica para tests que necesitan curso configurado."""
    config = Configuracion(
        anio_inicio_curso=2024,
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        algoritmo_asignacion="v2.9",
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=True,
        recreos_config=json.dumps(
            [
                {"id": 1, "etiqueta": "Recreo 1 Mañana", "turno": "mañana", "hora": "11:00"},
                {"id": 2, "etiqueta": "Recreo 2 Mañana", "turno": "mañana", "hora": "12:00"},
                {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:00"},
                {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "17:00"},
            ]
        ),
    )
    session.add(config)
    session.commit()
    return config
