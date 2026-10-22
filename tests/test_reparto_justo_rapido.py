"""El reparto justo llega al óptimo enseguida también en un equipo modesto (2026-10-22).

Planteado hueco a hueco, con las zonas de un recreo como huecos distintos, en un
equipo de 2-4 núcleos agotaba sus 30 s con una solución a 10-25 guardias de la
justa, y la equidad de todo el reparto salía mucho peor que en un Mac potente.
Datos ficticios: «Profesor/a NN», con la forma de un claustro de tarde real.
"""

import json
from datetime import date, time

import pytest
from ortools.sat.python import cp_model
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Configuracion, CursoEscolar, Profesor, Zona

TODOS = [0, 1, 2, 3, 4]
# (tutor, horas, % jornada, días permitidos)
PROFES = (
    [(True, 30, 100, TODOS)] * 15 + [(False, 30, 100, TODOS)] * 9
    + [(True, 30, 100, [0, 2, 3]), (True, 30, 100, [0, 2, 3, 4]), (False, 30, 100, [0, 1, 3, 4]),
       (False, 16, 53.3, [0, 2]), (False, 15, 50, [0, 2, 3]), (False, 10, 33.3, [0]),
       (False, 10, 33.3, [1])]
)
RECREOS = json.dumps([
    {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:30", "zonas": 4},
    {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "18:30", "zonas": 4},
])


@pytest.fixture
def sesion():
    motor = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(motor)
    s = sessionmaker(bind=motor)()
    inicio, fin = date(2026, 9, 9), date(2027, 5, 28)
    s.add(Configuracion(
        anio_inicio_curso=2026, fecha_inicio_curso=inicio, fecha_fin_curso=fin,
        hora_recreo1_manana=time(9, 40), hora_recreo2_manana=time(10, 40),
        hora_recreo1_tarde=time(16, 30), hora_recreo2_tarde=time(18, 30),
        activar_festivos_automaticos=False, recreos_config=RECREOS,
        ajuste_tutores=0.5, ajuste_no_tutores=1.0,
    ))
    s.add(CursoEscolar(nombre="Curso ficticio", anio_inicio=2026, anio_fin=2027,
                       fecha_inicio=inicio, fecha_fin=fin, activo=True))
    s.add_all([Zona(nombre_zona=f"Zona {i}", descripcion="Ficticia") for i in range(1, 5)])
    for i, (tutor, horas, pct, dias) in enumerate(PROFES, start=1):
        s.add(Profesor(
            nombre_completo=f"Profesor/a {i:02d}", email_corporativo=f"p{i:02d}@example.com",
            horas_contrato=float(horas), porcentaje_jornada=float(pct), turno="tarde",
            tutor=tutor, activo=True, dias_semana_permitidos=json.dumps(dias),
        ))
    s.commit()
    yield s
    s.close()
    motor.dispose()


def test_reparto_justo_optimo_con_dos_hilos(sesion, monkeypatch):
    import services._asignador_cpsat_helpers as ayudantes
    import services.asignador_guardias_cpsat as asignador
    import services.reparto_agrupado as reparto

    datos = {}

    class Capturado(Exception):
        pass

    def capturar(*args, **kwargs):
        datos["args"], datos["kwargs"] = args, kwargs
        raise Capturado

    monkeypatch.setattr(asignador, "objetivos_justos", capturar)
    with pytest.raises(Capturado):
        asignador.generar_guardias_cpsat(sesion, lambda *_: None, timeout_seconds=120)

    original = ayudantes.resolver_con_progreso

    def dos_hilos(solver, model, *args, **kwargs):
        solver.parameters.num_workers = 2
        datos["estado"] = original(solver, model, *args, **kwargs)
        return datos["estado"]

    monkeypatch.setattr(ayudantes, "resolver_con_progreso", dos_hilos)
    reparto.objetivos_justos(*datos["args"], **dict(datos["kwargs"], segundos=10.0))
    assert datos["estado"] == cp_model.OPTIMAL
