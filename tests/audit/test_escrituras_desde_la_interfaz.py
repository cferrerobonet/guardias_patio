"""COD-003 — que una pantalla no decida por su cuenta qué se escribe en la base.

La capa de presentación tenía dos escrituras directas: «Limpiar historial» hacía
un `UPDATE` masivo sobre las guardias y confirmaba la transacción, y eliminar un
curso llamaba al repositorio y hacía el `commit` la propia vista. Confirmar una
transacción es una decisión de negocio, no de una pantalla.

Las consultas de sólo lectura que quedan no se tocan: son listados para pintar
y sacarlas a un servicio sólo añadiría una capa que no decide nada.
"""

import ast
from pathlib import Path

import pytest

from infrastructure.database.models import Guardia, Profesor, Zona
from services.gestor_ausencias import limpiar_todas_las_sustituciones

RAIZ = Path(__file__).resolve().parents[2]
PRES = RAIZ / "src" / "presentation"

ESCRITURAS = {"commit", "add", "delete", "flush"}

#: Consultas de sólo lectura que quedan en las vistas. Sólo puede bajar.
TECHO_CONSULTAS = 14


def _ficheros():
    return [f for f in PRES.rglob("*.py") if "__pycache__" not in f.parts]


def test_ninguna_vista_confirma_una_transaccion():
    ofensores = []
    for fichero in _ficheros():
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            es_escritura = (
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr in ESCRITURAS
                and isinstance(nodo.func.value, ast.Attribute)
                and nodo.func.value.attr == "session"
            )
            if es_escritura:
                ofensores.append(f"{fichero.name}:{nodo.lineno} → session.{nodo.func.attr}()")
    assert ofensores == [], f"escrituras directas desde la interfaz: {ofensores}"


def test_las_consultas_de_lectura_no_crecen():
    """Ratchet: leer para pintar se tolera; que aumente, no."""
    consultas = sum(
        f.read_text(encoding="utf-8", errors="ignore").count("session.query(")
        for f in _ficheros()
    )
    assert consultas <= TECHO_CONSULTAS, (
        f"{consultas} consultas en la capa de presentación: si has reducido deuda, "
        "baja el techo; nunca lo subas"
    )


@pytest.fixture
def con_sustituciones(session):
    session.add_all(
        [
            Profesor(
                nombre_completo=f"Apellido{i}, Nombre",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            )
            for i in range(2)
        ]
    )
    session.add(Zona(nombre_zona="Patio A", activa=True))
    session.commit()
    titular, sustituto = session.query(Profesor).all()
    zona = session.query(Zona).first()
    import datetime

    session.add_all(
        [
            Guardia(
                profesor_id=sustituto.id,
                fecha=datetime.date(2025, 10, 6),
                turno="mañana",
                recreo=1,
                zona_id=zona.id,
                es_sustitucion=True,
                profesor_sustituido_id=titular.id,
            ),
            Guardia(
                profesor_id=titular.id,
                fecha=datetime.date(2025, 10, 7),
                turno="mañana",
                recreo=1,
                zona_id=zona.id,
            ),
        ]
    )
    session.commit()
    return session


def test_limpiar_devuelve_las_guardias_a_su_profesor(con_sustituciones):
    devueltas = limpiar_todas_las_sustituciones(con_sustituciones)

    assert devueltas == 1
    assert con_sustituciones.query(Guardia).filter_by(es_sustitucion=True).count() == 0


def test_limpiar_borra_tambien_a_quien_sustituia(con_sustituciones):
    limpiar_todas_las_sustituciones(con_sustituciones)

    restantes = con_sustituciones.query(Guardia).all()
    assert all(g.profesor_sustituido_id is None for g in restantes)


def test_limpiar_no_toca_las_guardias_normales(con_sustituciones):
    antes = con_sustituciones.query(Guardia).count()

    limpiar_todas_las_sustituciones(con_sustituciones)

    assert con_sustituciones.query(Guardia).count() == antes


def test_limpiar_sin_sustituciones_no_falla(session):
    assert limpiar_todas_las_sustituciones(session) == 0


def test_eliminar_un_curso_confirma_desde_el_servicio():
    """La vista llamaba al repositorio y hacía ella el `commit`."""
    import inspect

    from presentation.widgets.gestion_cursos_widget import GestionCursosWidget
    from services.gestor_cursos import GestorCursos

    assert "self.session.commit()" in inspect.getsource(GestorCursos.eliminar_curso)
    vista = inspect.getsource(GestionCursosWidget)
    assert "_svc.cursos.delete(" not in vista
