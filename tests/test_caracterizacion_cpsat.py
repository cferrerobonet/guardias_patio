"""Caracterización de `generar_guardias_cpsat`: fija el modelo y el reparto actuales.

Sirve de red para partir la función sin cambiar nada de lo que hace. Para cada
escenario se guarda la huella del modelo CP-SAT exacto (variables, restricciones,
pesos, objetivo y punto de partida), los parámetros del solucionador, el reparto que
sale y el progreso que se anuncia. Los dos solves (reparto justo y modelo principal)
se fuerzan a un hilo después de anotar los parámetros que pone el código: con un
hilo y la semilla por defecto CP-SAT es reproducible en un mismo sistema. Entre
soluciones igual de buenas no elige la misma en macOS y en Linux, así que lo que
depende de la solución (el reparto, las asignadas y el modelo que parte del reparto
justo) se guarda para cada sistema en el que se ejecuta: el Mac de desarrollo y el
Linux de la CI. En otro sistema se comprueba lo que no depende de la solución.

Si un cambio en el algoritmo es intencionado, las huellas se recalculan a propósito.
Datos ficticios: «Profesor/a NN» y zonas inventadas.
"""

import hashlib
import json
import platform
import threading
from datetime import date, time

import pytest
from ortools.sat.python import cp_model
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import (
    Ausencia,
    Base,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)

RECREOS = json.dumps([
    {"id": 1, "etiqueta": "R1 Mañana", "turno": "mañana", "hora": "11:00"},
    {"id": 2, "etiqueta": "R2 Mañana", "turno": "mañana", "hora": "12:00"},
    {"id": 3, "etiqueta": "R1 Tarde", "turno": "tarde", "hora": "16:00"},
    {"id": 4, "etiqueta": "R2 Tarde", "turno": "tarde", "hora": "17:00"},
])
INICIO = date(2024, 9, 2)
FIN = date(2024, 9, 13)


@pytest.fixture
def sesion():
    motor = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(motor)
    s = sessionmaker(bind=motor)()
    yield s
    s.close()
    motor.dispose()


def _centro(sesion, profes, n_zonas=3):
    sesion.add(Configuracion(
        anio_inicio_curso=2024, fecha_inicio_curso=INICIO, fecha_fin_curso=FIN,
        hora_recreo1_manana=time(11, 0), hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0), hora_recreo2_tarde=time(17, 0),
        activar_festivos_automaticos=False, recreos_config=RECREOS,
        ajuste_tutores=1.0, ajuste_no_tutores=1.0,
    ))
    curso = CursoEscolar(nombre="Curso de prueba", anio_inicio=2024, anio_fin=2025,
                         fecha_inicio=INICIO, fecha_fin=FIN, activo=True)
    sesion.add(curso)
    sesion.flush()
    zonas = [Zona(nombre_zona=f"Zona {i + 1}", descripcion=f"Zona ficticia {i + 1}")
             for i in range(n_zonas)]
    sesion.add_all(zonas)
    sesion.flush()
    creados = []
    for i, cfg in enumerate(profes, start=1):
        dias = cfg.get("dias")
        p = Profesor(
            nombre_completo=f"Profesor/a {i:02d}", email_corporativo=f"p{i:02d}@example.com",
            horas_contrato=cfg.get("horas", 25.0), porcentaje_jornada=100.0,
            turno=cfg.get("turno", "mañana"), tutor=cfg.get("tutor", False), activo=True,
            fecha_inicio_guardias=cfg.get("inicio"),
            dias_semana_permitidos=json.dumps(dias) if dias is not None else None,
            zona_preferida_id=zonas[cfg["zona"]].id if "zona" in cfg else None,
        )
        sesion.add(p)
        creados.append(p)
    sesion.commit()
    return curso, creados, zonas


def _centro_completo(sesion):
    curso, profes, zonas = _centro(sesion, [
        {"turno": "mañana", "tutor": True},
        {"turno": "mañana", "zona": 1},
        {"turno": "mañana", "dias": [0, 2, 4]},
        {"turno": "tarde"},
        {"turno": "tarde", "zona": 2},
        {"turno": "completo"},
        {"turno": "mañana", "inicio": date(2024, 9, 9), "horas": 18.0},
    ])
    sesion.add(Ausencia(profesor_id=profes[0].id, fecha_inicio=date(2024, 9, 4),
                        fecha_fin=date(2024, 9, 5), tipo="permiso", activa=True))
    sesion.commit()
    return curso, profes, zonas


@pytest.fixture
def registro(monkeypatch):
    """Intercepta los dos solves: anota modelo, parámetros y estado, y fija un hilo."""
    import importlib

    import services._asignador_cpsat_helpers as ayudantes
    import services.asignador_guardias_cpsat as asignador

    ajustes = importlib.import_module("config.settings")  # `config` exporta un objeto `settings`
    datos = {"solves": [], "progreso": [], "dentro": False}
    original = ayudantes.resolver_con_progreso

    def espia(solver, model, callback, progreso, reportar, cancelacion=None, **kw):
        params = str(solver.parameters)
        solver.parameters.num_search_workers = 1
        datos["dentro"] = True
        try:
            estado = original(solver, model, callback, progreso, reportar, cancelacion, **kw)
        finally:
            datos["dentro"] = False
        proto = str(model.Proto()).encode()  # formato de texto: el modelo entero
        datos["solves"].append({
            "modelo": hashlib.sha256(proto).hexdigest(),
            "parametros": params,
            "estado": "OPTIMAL" if estado == cp_model.OPTIMAL else str(estado),
        })
        return estado

    monkeypatch.setattr(ayudantes, "resolver_con_progreso", espia)
    monkeypatch.setattr(asignador, "resolver_con_progreso", espia)
    monkeypatch.setattr(ajustes, "hilos_del_solver", lambda *_: 4)

    def progreso(pct, msg):
        if not datos["dentro"]:
            datos["progreso"].append((pct, msg))

    datos["callback"] = progreso
    return datos


def _reparto(guardias):
    return sorted(
        (g.profesor_id, g.fecha.isoformat(), g.turno, g.recreo, g.zona_id, g.curso_id)
        for g in guardias
    )


def _huella(valor) -> str:
    return hashlib.sha256(json.dumps(valor, sort_keys=True, default=str).encode()).hexdigest()


def _generar(sesion, registro, **kw):
    from services.asignador_guardias_cpsat import generar_guardias_cpsat

    guardias, asignadas = generar_guardias_cpsat(
        sesion, registro["callback"], timeout_seconds=60, **kw
    )
    return {
        "reparto": _reparto(guardias),
        "asignadas": sorted(asignadas.items()),
        "solves": registro["solves"],
        "progreso": registro["progreso"],
    }


SISTEMA = f"{platform.system()}-{platform.machine()}"
GRABADO_EN = "Darwin-arm64"


def _comprobar(resultado, esperado):
    for s in resultado["solves"]:
        assert s["estado"] == "OPTIMAL", "con un hilo y sin agotar el tiempo"
    obtenido = {
        "modelos": [s["modelo"] for s in resultado["solves"]],
        "parametros": _huella([s["parametros"] for s in resultado["solves"]]),
        "reparto": _huella(resultado["reparto"]),
        "asignadas": resultado["asignadas"],
        "progreso": resultado["progreso"],
    }
    propios = esperado.get("por_sistema", {})
    base = {k: v for k, v in esperado.items() if k != "por_sistema"}
    if SISTEMA == GRABADO_EN or SISTEMA in propios:
        assert obtenido == {**base, **propios.get(SISTEMA, {})}
        return
    assert obtenido["modelos"][0] == base["modelos"][0]
    assert obtenido["parametros"] == base["parametros"]
    assert obtenido["progreso"] == base["progreso"]
    assert sorted(n for _, n in obtenido["asignadas"]) == sorted(n for _, n in base["asignadas"])


ESPERADO_COMPLETO = {
    "modelos": [
        "3eec22804915b7e423e1756606016a823d4b5d4ff91b80cc48054133658c3751",
        "ecd8239fb3bdaf2ecd2a1c46798ddce58a68d3e4d2200f1654847949a2baa113",
    ],
    "parametros": "d494d5e2c26fa0fe8b519565862edfcf6a28ba13a37780bc980326b615126450",
    "reparto": "18be006ee49fd6dd2169074c07ea67cfb33a7bb3c60c54f7a60360a51f4c528e",
    "asignadas": [(1, 5), (2, 5), (3, 4), (4, 6), (5, 7), (6, 8), (7, 5)],
    "por_sistema": {
        "Linux-x86_64": {
            "modelos": [
                "3eec22804915b7e423e1756606016a823d4b5d4ff91b80cc48054133658c3751",
                "cdb3d536d25c523d92b809ba34647876148f63649558bad637f41ef73236837a",
            ],
            "reparto": "cdd828fe2cbbb02699fd9d0baa9cb33e524294b68bd4d9fce89662bbf5eea8fa",
            "asignadas": [(1, 5), (2, 5), (3, 5), (4, 6), (5, 7), (6, 8), (7, 4)],
        },
    },
    "progreso": [
        (0, "Iniciando generación con CP-SAT..."),
        (5, "Cargando configuración..."),
        (8, "Cargando profesores..."),
        (10, "Generando slots..."),
        (15, "Calculando elegibilidad..."),
        (20, "Creando modelo..."),
        (25, "Definiendo objetivo multi-criterio..."),
        (27, "Buscando el reparto más justo posible..."),
        (29, "Reparto justo calculado"),
        (30, "Generando solución inicial..."),
        (35, "Resolviendo modelo..."),
        (90, "Generando guardias..."),
        (100, "✅ Completado: IE=95.0% (Óptimo)"),
    ],
}
ESPERADO_DEFICIT_SIN_PISTAS = {
    "modelos": [
        "0f4d29e6166ac11fd96e2b751d0985866d55aff552e7f04e1adc50a907377541",
        "160da95d4f95940381d9bd221a7c02b1dd9cdaa9cbacd5c5dc26ffc7e1b3d6cd",
    ],
    "parametros": "d494d5e2c26fa0fe8b519565862edfcf6a28ba13a37780bc980326b615126450",
    "reparto": "ace7a02c3998c7aa79247a3619ff12edcd31d2c2b113c41c8bc3f4c4dfc1c739",
    "por_sistema": {
        "Linux-x86_64": {
            "reparto": "9ba4df016686026d3882994fd4f2dda0ee2b1736e9a32c5317a9646927c33cb1",
        },
    },
    "asignadas": [(1, 10), (2, 10)],
    "progreso": [
        (0, "Iniciando generación con CP-SAT..."),
        (5, "Cargando configuración..."),
        (8, "Cargando profesores..."),
        (10, "Generando slots..."),
        (15, "Calculando elegibilidad..."),
        (20, "Creando modelo..."),
        (25, "Definiendo objetivo multi-criterio..."),
        (27, "Buscando el reparto más justo posible..."),
        (29, "Reparto justo calculado"),
        (35, "Resolviendo modelo..."),
        (90, "Generando guardias..."),
        (100, "✅ Completado: IE=50.0% (Óptimo)"),
    ],
}
ESPERADO_INCREMENTAL = {
    "modelos": [
        "f2425bdd7d71b3da536077b30650aaf1e4917e4af9f61a62e723f4f1dde5fe64",
        "4edcafb4a11c0c047c7a558cb13ab5e1fb56d7d75a7f2502d589f9b72f409bf8",
    ],
    "parametros": "d494d5e2c26fa0fe8b519565862edfcf6a28ba13a37780bc980326b615126450",
    "reparto": "0a7a26a28e32577dbd521b5febc2ccf7953877c1cf51f640081d51f36422ead3",
    "por_sistema": {
        "Linux-x86_64": {
            "reparto": "59373a5b60ecee7b515b466267662e3a93d6c08b7ae8ff88893238ed334bd514",
        },
    },
    "asignadas": [(1, 3), (2, 3), (3, 1), (4, 4), (5, 3), (6, 3), (7, 3)],
    "progreso": [
        (0, "Iniciando generación con CP-SAT..."),
        (5, "Cargando configuración..."),
        (8, "Cargando profesores..."),
        (10, "Generando slots..."),
        (15, "Calculando elegibilidad..."),
        (20, "Creando modelo..."),
        (25, "Definiendo objetivo multi-criterio..."),
        (27, "Buscando el reparto más justo posible..."),
        (29, "Reparto justo calculado"),
        (30, "Generando solución inicial..."),
        (35, "Resolviendo modelo..."),
        (90, "Generando guardias..."),
        (100, "✅ Completado: IE=55.6% (Óptimo)"),
    ],
}


def test_escenario_completo(sesion, registro):
    _centro_completo(sesion)
    _comprobar(_generar(sesion, registro), ESPERADO_COMPLETO)


def test_faltan_profesores_y_sin_punto_de_partida(sesion, registro):
    _centro(sesion, [{"turno": "mañana"}, {"turno": "tarde", "zona": 0}], n_zonas=3)
    _comprobar(_generar(sesion, registro, use_hints=False), ESPERADO_DEFICIT_SIN_PISTAS)


def test_incremental_conserva_lo_anterior_y_las_sustituciones(sesion, registro):
    curso, profes, zonas = _centro_completo(sesion)
    previas = [
        (profes[0], date(2024, 9, 2), "mañana", 1, zonas[0], False),
        (profes[1], date(2024, 9, 3), "mañana", 2, zonas[1], False),
        (profes[3], date(2024, 9, 3), "tarde", 3, zonas[2], False),
        (profes[5], date(2024, 9, 11), "mañana", 1, zonas[2], True),
        (profes[2], date(2024, 9, 12), "mañana", 2, zonas[0], False),
    ]
    for p, f, turno, recreo, z, sust in previas:
        sesion.add(Guardia(profesor_id=p.id, fecha=f, turno=turno, recreo=recreo,
                           zona_id=z.id, curso_id=curso.id, es_sustitucion=sust))
    sesion.commit()
    _comprobar(_generar(sesion, registro, desde=date(2024, 9, 9)), ESPERADO_INCREMENTAL)


def test_incremental_sin_nada_que_recalcular(sesion, registro):
    curso, profes, zonas = _centro(sesion, [{"turno": "mañana"}], n_zonas=1)
    sesion.add(Guardia(profesor_id=profes[0].id, fecha=date(2024, 9, 2), turno="mañana",
                       recreo=1, zona_id=zonas[0].id, curso_id=curso.id))
    sesion.commit()
    resultado = _generar(sesion, registro, desde=date(2024, 9, 14))
    assert resultado["reparto"] == [(profes[0].id, "2024-09-02", "mañana", 1, zonas[0].id,
                                     curso.id)]
    assert resultado["asignadas"] == [(profes[0].id, 1)]
    assert resultado["solves"] == []
    assert resultado["progreso"] == [
        (0, "Iniciando generación con CP-SAT..."),
        (5, "Cargando configuración..."),
        (8, "Cargando profesores..."),
        (10, "Generando slots..."),
        (100, "Sin cambios: no hay slots que recalcular"),
    ]


def test_errores_de_datos(sesion, registro):
    from services.asignador_guardias_cpsat import generar_guardias_cpsat

    with pytest.raises(ValueError, match="No existe configuración del curso"):
        generar_guardias_cpsat(sesion, timeout_seconds=5)
    _centro(sesion, [], n_zonas=1)
    with pytest.raises(ValueError, match="No hay profesores activos"):
        generar_guardias_cpsat(sesion, timeout_seconds=5)
    sesion.add(Profesor(nombre_completo="Profesor/a 01", horas_contrato=25.0,
                        porcentaje_jornada=100.0, turno="mañana", activo=True))
    for z in sesion.query(Zona).all():
        z.activa = False
    sesion.commit()
    with pytest.raises(ValueError, match="No hay zonas activas que cubrir"):
        generar_guardias_cpsat(sesion, timeout_seconds=5)


def test_cancelar_antes_de_empezar(sesion):
    from services.asignador_guardias_cpsat import generar_guardias_cpsat

    _centro_completo(sesion)
    evento = threading.Event()
    evento.set()
    with pytest.raises(InterruptedError):
        generar_guardias_cpsat(sesion, timeout_seconds=5, cancelacion=evento)
