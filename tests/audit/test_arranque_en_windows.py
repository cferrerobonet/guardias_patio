"""BLD-020 — el exe de Windows se cerraba solo a los dos segundos de abrir.

La prueba de humo en el Windows de GitHub lo dejó a la vista: «access violation»
en `PyQt6/Qt6/bin/MSVCP140.dll` 14.26 durante el `Solve` de la comprobación de
arranque. PyQt6 trae un runtime de C++ de 2020, se carga el primero y OR-Tools,
compilado para el de 2024, lo usa. En macOS no hay runtime de Microsoft.

Aquí se comprueba lo que se puede sin Windows: el reparto del runtime, que la
prueba de humo sigue en el flujo de compilación, que Alembic no se lleva el
registro de la aplicación y que el modo prueba hace de usuario como debe.
"""

import logging
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts" / "build"))

from runtime_msvc import unificar  # noqa: E402

QT_BIN = "PyQt6/Qt6/bin"


def _versiones(tabla):
    return lambda ruta: tabla.get(str(ruta), ())


# ---------------------------------------------------------------------------
# El runtime de C++ que viaja en el exe
# ---------------------------------------------------------------------------
def test_cada_copia_del_runtime_pasa_a_ser_la_mas_reciente(tmp_path):
    sistema = tmp_path / "System32"
    sistema.mkdir()
    (sistema / "msvcp140.dll").write_bytes(b"")
    binarios = [
        (f"{QT_BIN}/MSVCP140.dll", "C:/pyqt/MSVCP140.dll", "BINARY"),
        ("msvcp140.dll", "C:/py/msvcp140.dll", "BINARY"),
        ("Qt6Core.dll", "C:/pyqt/Qt6Core.dll", "BINARY"),
    ]
    versiones = {
        "C:/pyqt/MSVCP140.dll": (14, 26, 28720, 3),
        "C:/py/msvcp140.dll": (14, 38, 0, 0),
        str(sistema / "msvcp140.dll"): (14, 44, 35211, 0),
    }

    salida = unificar(binarios, sistema, _versiones(versiones), avisar=lambda _m: None)

    assert [d for d, _o, _t in salida] == [d for d, _o, _t in binarios], "los destinos no cambian"
    nuevas = {d: o for d, o, _t in salida}
    assert nuevas[f"{QT_BIN}/MSVCP140.dll"] == str(sistema / "msvcp140.dll")
    assert nuevas["msvcp140.dll"] == str(sistema / "msvcp140.dll")
    assert nuevas["Qt6Core.dll"] == "C:/pyqt/Qt6Core.dll", "lo que no es runtime no se toca"


def test_sin_copia_en_el_sistema_gana_la_mas_nueva_del_paquete(tmp_path):
    binarios = [
        (f"{QT_BIN}/VCRUNTIME140_1.dll", "C:/pyqt/VCRUNTIME140_1.dll", "BINARY"),
        ("vcruntime140_1.dll", "C:/py/vcruntime140_1.dll", "BINARY"),
    ]
    versiones = {"C:/pyqt/VCRUNTIME140_1.dll": (14, 26), "C:/py/vcruntime140_1.dll": (14, 42)}

    salida = unificar(binarios, tmp_path, _versiones(versiones), avisar=lambda _m: None)

    assert {o for _d, o, _t in salida} == {"C:/py/vcruntime140_1.dll"}


def test_un_runtime_anterior_a_14_40_no_llega_a_empaquetarse(tmp_path):
    binarios = [(f"{QT_BIN}/MSVCP140.dll", "C:/pyqt/MSVCP140.dll", "BINARY")]
    with pytest.raises(SystemExit, match="14.40"):
        unificar(
            binarios,
            tmp_path,
            _versiones({"C:/pyqt/MSVCP140.dll": (14, 26)}),
            avisar=lambda _m: None,
        )


def test_el_spec_reparte_el_runtime_en_windows():
    spec = (RAIZ / "GuardiasDePatio.spec").read_text(encoding="utf-8")
    assert "from runtime_msvc import unificar" in spec
    assert "a.binaries = unificar(a.binaries)" in spec
    assert spec.index("a.binaries = unificar(a.binaries)") < spec.index("pyz = PYZ(a.pure)")


# ---------------------------------------------------------------------------
# La prueba de humo se queda en el flujo que publica
# ---------------------------------------------------------------------------
def test_no_se_publica_un_exe_que_no_llega_a_la_ventana():
    flujo = (RAIZ / ".github" / "workflows" / "compilar.yml").read_text(encoding="utf-8")
    windows = flujo[flujo.index("  windows:"):flujo.index("  macos:")]
    assert "prueba_arranque_windows.ps1" in windows
    assert windows.index("prueba_arranque_windows.ps1") < windows.index("upload-artifact")


def test_la_prueba_de_humo_nunca_usa_credenciales_reales():
    for nombre in ("compilar.yml", "arranque-windows.yml"):
        flujo = (RAIZ / ".github" / "workflows" / nombre).read_text(encoding="utf-8")
        assert "secrets." not in flujo, nombre
    diagnostico = (RAIZ / ".github" / "workflows" / "arranque-windows.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"SFTP_HOST=127\.0\.0\.1", diagnostico)


def test_el_script_de_humo_busca_la_marca_que_escribe_la_aplicacion():
    from core.prueba_de_arranque import MARCA_LOGIN, MARCA_VENTANA

    script = (RAIZ / "scripts" / "prueba_arranque_windows.ps1").read_text(encoding="utf-8")
    assert MARCA_LOGIN in script and MARCA_VENTANA in script
    assert "faulthandler.log" in script


# ---------------------------------------------------------------------------
# Alembic no se lleva el registro de la aplicación
# ---------------------------------------------------------------------------
def test_las_migraciones_no_sustituyen_el_registro_de_la_app(tmp_path, monkeypatch):
    """`fileConfig` quitaba el `FileHandler` de la app, silenciaba sus loggers y
    dejaba la raíz escribiendo en `sys.stderr`, que en el exe de Windows es None:
    desde el login no quedaba nada en `app_*.log`."""
    from sqlalchemy import create_engine

    from database.db_manager import _run_alembic_migrations

    raiz = logging.getLogger()
    propio = logging.FileHandler(tmp_path / "app.log", encoding="utf-8")
    raiz.addHandler(propio)
    del_arranque = logging.getLogger("prueba.arranque.bld020")
    monkeypatch.setattr(sys, "stderr", None)  # como en el exe sin consola
    try:
        antes = list(raiz.handlers)
        engine = create_engine(f"sqlite:///{tmp_path / 'guardias.db'}")
        assert _run_alembic_migrations(engine, tmp_path / "guardias.db") is True
        engine.dispose()

        assert raiz.handlers == antes
        assert del_arranque.disabled is False
        del_arranque.warning("sigue escribiendo")
        propio.flush()
        assert "sigue escribiendo" in (tmp_path / "app.log").read_text(encoding="utf-8")
    finally:
        raiz.removeHandler(propio)
        propio.close()


def test_env_py_solo_configura_el_registro_desde_la_linea_de_ordenes():
    env = (RAIZ / "alembic" / "env.py").read_text(encoding="utf-8")
    assert 'config.attributes.get("configure_logger", True)' in env


# ---------------------------------------------------------------------------
# El modo prueba hace de usuario
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "valor, esperado",
    [("", ""), ("1", "login"), ("login", "login"), ("VENTANA", "ventana"), ("otra", "")],
)
def test_el_modo_prueba_solo_se_activa_si_se_pide(monkeypatch, valor, esperado):
    from core import prueba_de_arranque

    monkeypatch.setenv(prueba_de_arranque.VARIABLE, valor)
    assert prueba_de_arranque.modo() == esperado


def test_sin_la_variable_no_hay_vigia(qapp, monkeypatch):
    from core import prueba_de_arranque

    monkeypatch.delenv(prueba_de_arranque.VARIABLE, raising=False)
    assert prueba_de_arranque.vigilar_si_se_pide(qapp) is None


def test_el_vigia_acepta_avisos_rechaza_dialogos_y_apunta_el_login(qapp, qtbot, caplog):
    from PyQt6.QtWidgets import QDialog, QMessageBox

    from core import prueba_de_arranque

    class LoginDialog(QDialog):
        pass

    aviso = QMessageBox(QMessageBox.Icon.Warning, "Aviso", "Sin nube")
    seguir = aviso.addButton("Seguir", QMessageBox.ButtonRole.AcceptRole)
    aviso.setDefaultButton(seguir)
    otro = QDialog()
    login = LoginDialog()
    for ventana in (aviso, otro, login):
        qtbot.addWidget(ventana)
        ventana.show()

    vigia = prueba_de_arranque._Vigia(qapp, "login")
    with caplog.at_level(logging.INFO, logger="core.prueba_de_arranque"):
        for _ in range(prueba_de_arranque.VUELTAS_A_LA_VISTA):
            vigia.revisar()

    assert aviso.clickedButton() is seguir
    assert otro.result() == QDialog.DialogCode.Rejected and not otro.isVisible()
    assert not login.isVisible()
    assert prueba_de_arranque.MARCA_LOGIN in caplog.text
