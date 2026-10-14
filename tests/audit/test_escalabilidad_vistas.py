"""ESC-001 / UXA-011: ¿de verdad hace falta cambiar las tablas?

La auditoría proponía migrar las 12 tablas de `QTableWidget` a `QTableView` con
modelo, y cargar en segundo plano, con un objetivo de p95 < 100 ms para 1.000
profesores. Antes de un refactor de ese tamaño conviene medir: EPLA tiene unos
200 educadores y un curso completo ronda las 2.800 guardias.

Medido en v5.66.0, ya con los imports calientes: calendario 17 ms con 2.800
guardias, profesores 13 ms con 200. El refactor no compraba nada.

Estos tests no persiguen una cifra fina —la máquina de cada uno es distinta—,
sino avisar si alguna vez se vuelve lento de verdad.
"""

import datetime
import time

import pytest
from PyQt6.QtWidgets import QApplication

from infrastructure.database.models import Guardia, Profesor, Zona

pytestmark = [pytest.mark.ui, pytest.mark.slow]

#: Umbral generoso: diez veces lo medido, para que no falle por ir la máquina cargada.
LIMITE_MS = 400


def _poblar_curso(session, n_profesores: int = 200, dias: int = 175) -> int:
    session.add_all([Zona(nombre_zona=f"Zona {i}", activa=True) for i in range(4)])
    for i in range(n_profesores):
        session.add(
            Profesor(
                nombre_completo=f"Apellido{i:04d}, Nombre",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            )
        )
    session.commit()

    profesores = session.query(Profesor).all()
    zonas = session.query(Zona).all()
    inicio = datetime.date(2025, 9, 15)
    total = 0
    for dia in range(dias):
        for recreo in range(1, 5):
            for zona in zonas:
                session.add(
                    Guardia(
                        profesor_id=profesores[total % len(profesores)].id,
                        zona_id=zona.id,
                        fecha=inicio + datetime.timedelta(days=dia),
                        turno="mañana",
                        recreo=recreo,
                    )
                )
                total += 1
    session.commit()
    return total


def _medir(construir) -> float:
    """Mediana de cinco aperturas, descontando el coste de importar."""
    construir().close()  # calentar

    tiempos = []
    for _ in range(5):
        inicio = time.perf_counter()
        vista = construir()
        QApplication.processEvents()
        tiempos.append((time.perf_counter() - inicio) * 1000)
        vista.close()
    return sorted(tiempos)[2]


def test_la_tabla_de_profesores_abre_rapido_con_un_claustro_grande(qapp, session):
    """1.000 profesores es cinco veces el claustro real de EPLA."""
    from presentation.forms.profesor_form import ProfesorForm

    for i in range(1000):
        session.add(
            Profesor(
                nombre_completo=f"Apellido{i:04d}, Nombre",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            )
        )
    session.commit()

    mediana = _medir(lambda: ProfesorForm(session))
    assert mediana < LIMITE_MS, f"abrir Profesores tardó {mediana:.0f} ms con 1.000 filas"


def test_el_calendario_abre_rapido_con_un_curso_completo(qapp, session):
    from presentation.widgets.vista_calendario import VistaCalendario

    total = _poblar_curso(session)
    assert total > 2500, "el escenario debería tener un curso entero de guardias"

    mediana = _medir(lambda: VistaCalendario(session))
    assert mediana < LIMITE_MS, f"abrir el calendario tardó {mediana:.0f} ms con {total} guardias"


# ---------------------------------------------------------------------------
# ESC-002: el solver se adapta al equipo
# ---------------------------------------------------------------------------
def test_los_hilos_del_solver_salen_del_equipo_no_de_una_constante():
    """8 hilos fijos sobrecargan un equipo de 4 núcleos y desaprovechan uno de 16."""
    import inspect
    import os

    from config.settings import Settings, hilos_del_solver
    from services import asignador_guardias_cpsat

    fuente = inspect.getsource(asignador_guardias_cpsat.generar_guardias_cpsat)
    assert "num_search_workers = 8" not in fuente
    assert "hilos_del_solver()" in fuente

    automatico = hilos_del_solver(Settings(solver_hilos=0))
    assert 1 <= automatico <= 16
    assert automatico == max(1, min(os.cpu_count() or 8, 16))


def test_los_hilos_se_pueden_fijar_a_mano():
    from config.settings import Settings, hilos_del_solver

    assert hilos_del_solver(Settings(solver_hilos=3)) == 3


def test_el_tiempo_maximo_del_solver_es_configurable():
    """Antes 120 s estaban escritos en el código, sin forma de cambiarlos."""
    import inspect

    from config.settings import Settings
    from services import asignador_guardias_cpsat

    firma = inspect.signature(asignador_guardias_cpsat.generar_guardias_cpsat)
    assert firma.parameters["timeout_seconds"].default is None, (
        "el tiempo máximo debe venir de los ajustes, no de un valor fijo en la firma"
    )
    assert Settings(solver_timeout_segundos=45.0).solver_timeout_segundos == 45.0
