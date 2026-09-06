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


# ---------------------------------------------------------------------------
# COD-002 (segunda tanda): los errores del servidor SFTP
# ---------------------------------------------------------------------------
def test_la_tupla_de_transporte_cubre_los_errores_de_ssh():
    """`SSHException` no hereda de `OSError`: un banner ilegible o una clave de
    host cambiada escapaban del manejador y acababan en el aviso genérico."""
    import paramiko

    from sync.sync_manager import ERRORES_DE_TRANSPORTE

    assert issubclass(paramiko.SSHException, ERRORES_DE_TRANSPORTE)
    assert issubclass(paramiko.AuthenticationException, ERRORES_DE_TRANSPORTE)
    assert issubclass(OSError, ERRORES_DE_TRANSPORTE)


def test_la_tupla_funciona_aunque_falte_paramiko():
    """paramiko es opcional: sin él, el módulo tiene que seguir importándose."""
    import inspect

    from sync import sync_manager

    fuente = inspect.getsource(sync_manager)
    assert "except ImportError:" in fuente.split("ERRORES_DE_TRANSPORTE")[0]


def test_las_operaciones_sftp_usan_esa_tupla():
    """Si alguien añade otra operación, que no vuelva a la tupla arbitraria."""
    import ast
    import inspect

    from sync import sync_manager

    arbol = ast.parse(inspect.getsource(sync_manager))
    ofensores = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.ClassDef) or nodo.name != "SFTPSyncBackend":
            continue
        for sub in ast.walk(nodo):
            if not isinstance(sub, ast.Try):
                continue
            cuerpo = ast.dump(ast.Module(body=sub.body, type_ignores=[]))
            if not any(x in cuerpo for x in ("'put'", "'get'", "'rename'", "'listdir'")):
                continue
            for manejador in sub.handlers:
                if isinstance(manejador.type, ast.Tuple):
                    nombres = {n.id for n in manejador.type.elts if isinstance(n, ast.Name)}
                    if nombres and "SSHException" not in str(nombres):
                        ofensores.append(f"línea {manejador.lineno}: {sorted(nombres)}")

    assert not ofensores, f"operaciones SFTP con manejador incompleto: {ofensores}"


def test_probar_la_conexion_desde_ajustes_no_revienta_con_ssh():
    """Mismo fallo que en el diálogo inicial, en el widget de Ajustes.

    El método que prueba la conexión no puede quedarse con una tupla que deje
    escapar `SSHException`: hay que capturar todo y explicarlo.
    """
    import ast
    import inspect

    from presentation.forms.config_widgets import sftp_widget

    arbol = ast.parse(inspect.getsource(sftp_widget))
    metodos = [
        n
        for n in ast.walk(arbol)
        if isinstance(n, ast.FunctionDef) and "test" in n.name and "connection" in n.name
    ]
    assert metodos, "no se encontró el método que prueba la conexión"

    for metodo in metodos:
        for sub in ast.walk(metodo):
            if not isinstance(sub, ast.Try):
                continue
            for manejador in sub.handlers:
                if isinstance(manejador.type, ast.Tuple):
                    nombres = {n.id for n in manejador.type.elts if isinstance(n, ast.Name)}
                    assert nombres != {"OSError", "ValueError"}, (
                        f"{metodo.name} deja escapar SSHException"
                    )
