"""COD-002: qué se captura y qué se hace con ello.

La tupla `(ValueError, TypeError, OSError)` aparecía 111 veces. Parece concreta,
pero es arbitraria: se traga `InterruptedError` (que hereda de `OSError`) y deja
escapar justo lo que suele fallar, `SQLAlchemyError`. Y cuando ese error escapaba,
además, la sesión quedaba inservible para el resto de la vida de la vista.
"""

import ast
from pathlib import Path

import pytest
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.ui


def test_un_error_de_base_de_datos_deshace_la_transaccion(qapp, session):
    """Sin `rollback()`, todo lo que venga después en esa vista falla."""
    from presentation.forms.base_form import BaseForm

    formulario = BaseForm(session)
    deshecho = []
    session.rollback = lambda: deshecho.append(True)
    formulario.mostrar_error = lambda *a, **k: None

    formulario.manejar_excepcion(SQLAlchemyError("la base de datos dijo que no"), "guardar")

    assert deshecho, "un error de base de datos no deshizo la transacción"
    formulario.close()


def test_un_error_que_no_es_de_base_de_datos_no_toca_la_transaccion(qapp, session):
    from presentation.forms.base_form import BaseForm

    formulario = BaseForm(session)
    deshecho = []
    session.rollback = lambda: deshecho.append(True)
    formulario.mostrar_error = lambda *a, **k: None

    formulario.manejar_excepcion(ValueError("dato mal escrito"), "validar")

    assert not deshecho, "se deshizo la transacción por un error que no era de la base de datos"
    formulario.close()


def test_los_bloques_que_tocan_la_base_de_datos_capturan_sus_errores():
    """Si un `try` toca la base de datos, su `except` tiene que contemplarla.

    Es el guardarraíl del hallazgo: sin él vuelve a colarse en el próximo
    formulario que guarde algo.
    """
    TUPLA_COMODIN = {"ValueError", "TypeError", "OSError"}
    SENALES_DE_BD = ("'commit'", "'query'", "'execute'", "'flush'", "'add'", "'delete'")

    ofensores = []
    for fichero in (ROOT / "src").rglob("*.py"):
        if "egg-info" in str(fichero):
            continue
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue

        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Try):
                continue
            cuerpo = ast.dump(ast.Module(body=nodo.body, type_ignores=[]))
            if not any(senal in cuerpo for senal in SENALES_DE_BD):
                continue

            for manejador in nodo.handlers:
                tipo = manejador.type
                if not isinstance(tipo, ast.Tuple):
                    continue
                nombres = {n.id for n in tipo.elts if isinstance(n, ast.Name)}
                if nombres == TUPLA_COMODIN:
                    ofensores.append(
                        f"{fichero.relative_to(ROOT)}:{manejador.lineno}"
                    )

    assert not ofensores, (
        "estos bloques tocan la base de datos y dejan escapar SQLAlchemyError: "
        + str(ofensores)
    )
