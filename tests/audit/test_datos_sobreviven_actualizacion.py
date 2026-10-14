"""Actualizar la aplicación no puede llevarse por delante los datos del usuario.

Instalar una versión nueva sustituye el programa. Si los datos vivieran dentro de
él, cada actualización empezaría de cero. Estas pruebas fijan que viven en la
carpeta del usuario del sistema operativo, aparte del programa.
"""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _rutas_como_app_instalada(monkeypatch, sistema: str, home: Path):
    """Recarga core.paths simulando la aplicación ya empaquetada e instalada."""
    import core.paths as paths

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.platform, "system", lambda: sistema)
    monkeypatch.setattr(paths.Path, "home", staticmethod(lambda: home))
    if sistema == "Windows":
        monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))
    return paths


@pytest.mark.parametrize(
    "sistema, esperado",
    [
        ("Darwin", ("Library", "Application Support", "GuardiasDePatio")),
        ("Windows", ("AppData", "Roaming", "GuardiasDePatio")),
        ("Linux", (".local", "share", "GuardiasDePatio")),
    ],
)
def test_los_datos_viven_en_la_carpeta_del_usuario(monkeypatch, tmp_path, sistema, esperado):
    paths = _rutas_como_app_instalada(monkeypatch, sistema, tmp_path)

    base = paths.get_base_directory()

    assert base.parts[-len(esperado) :] == esperado
    assert str(tmp_path) in str(base), "debe colgar del perfil del usuario"


def test_datos_y_registros_quedan_fuera_del_programa(monkeypatch, tmp_path):
    """Ni la base de datos ni los registros pueden estar dentro de la aplicación."""
    paths = _rutas_como_app_instalada(monkeypatch, "Darwin", tmp_path)

    for carpeta in (paths.get_data_directory(), paths.get_logs_directory(),
                    paths.get_user_data_directory()):
        assert str(carpeta).startswith(str(tmp_path))
        assert ".app/" not in str(carpeta)
        assert "_MEI" not in str(carpeta), "no puede estar en el temporal de PyInstaller"


def test_la_configuracion_tambien_sobrevive(monkeypatch, tmp_path):
    """El .env guarda la conexión al servidor: si se perdiera, habría que reconfigurar."""
    paths = _rutas_como_app_instalada(monkeypatch, "Darwin", tmp_path)

    env = paths.get_base_directory() / ".env"
    assert str(env).startswith(str(tmp_path))


def test_al_abrir_se_actualiza_el_esquema_y_se_hace_copia():
    """
    Una versión nueva puede traer cambios de estructura. Si no se aplicaran sobre
    la base que ya existe, la aplicación fallaría con los datos del usuario.
    """
    fuente = (ROOT / "src" / "database" / "db_manager.py").read_text(encoding="utf-8")
    inicio = fuente.index("def initialize_user_database")
    cuerpo = fuente[inicio : fuente.index("\ndef ", inicio + 10)]

    assert "_run_alembic_migrations" in cuerpo, "hay que migrar el esquema al abrir"
    assert "_run_automatic_backup_if_needed" in cuerpo, "y hacer copia antes de tocar nada"


def test_se_puede_entrar_con_un_usuario_que_este_equipo_no_conoce():
    """Tras instalar en un equipo nuevo la lista local está vacía: hay que poder teclearlo."""
    fuente = (ROOT / "src" / "presentation" / "forms" / "login_dialog.py").read_text(
        encoding="utf-8"
    )
    assert "self.username_combo.setEditable(True)" in fuente


def test_el_instalador_de_windows_no_toca_los_datos_del_usuario():
    iss = (ROOT / "installer_windows.iss").read_text(encoding="utf-8", errors="ignore")
    prohibido = ("{userappdata}", "{localappdata}", "UninstallDelete")
    encontrados = [t for t in prohibido if t in iss]
    assert not encontrados, f"el instalador toca carpetas de datos: {encontrados}"


def test_importar_core_paths_no_rompe_tras_los_parches():
    """La recarga del módulo no debe dejar rastro para el resto de la suite."""
    import core.paths as paths

    importlib.reload(paths)
    assert paths.get_base_directory().exists()
