"""BLD-008 — un único spec de PyInstaller, y que sea el que usa el build.

Había dos: `Guardias de Patio.spec` (abril) y `GuardiasDePatio.spec`. El build
de macOS —Makefile y `build_dmg.sh`— tiraba del antiguo, mientras que los
cambios (los almacenes del llavero, por ejemplo) se hacían en el nuevo. El DMG
habría salido sin poder guardar contraseñas.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SPEC = "GuardiasDePatio.spec"


def test_hay_un_solo_spec():
    assert sorted(p.name for p in RAIZ.glob("*.spec")) == [SPEC]


def test_el_build_de_macos_usa_ese_spec():
    for fichero in ("Makefile", "scripts/build/build_dmg.sh"):
        texto = (RAIZ / fichero).read_text(encoding="utf-8")
        assert SPEC in texto, f"{fichero} no usa {SPEC}"
        assert "Guardias de Patio.spec" not in texto


def test_el_spec_lleva_los_almacenes_del_llavero():
    assert "keyring.backends" in (RAIZ / SPEC).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# BLD-009 — el spec único tiene que servir en las dos plataformas
# ---------------------------------------------------------------------------
def _fuente_spec() -> str:
    return (RAIZ / SPEC).read_text(encoding="utf-8")


def test_las_rutas_del_spec_no_llevan_barras_invertidas():
    """`src\\main.py` compilaba en Windows y dejaba a macOS sin DMG (v5.97.0–v5.99.0)."""
    assert "\\\\" not in _fuente_spec()


def test_el_spec_crea_el_bundle_que_busca_el_script_del_dmg():
    fuente = _fuente_spec()
    assert "BUNDLE(" in fuente, "sin BUNDLE no se genera el .app y el DMG falla"
    # `build_dmg.sh` busca exactamente `dist/Guardias de Patio.app`.
    assert 'NOMBRE = "Guardias de Patio" if ES_MACOS' in fuente
    guion = (RAIZ / "scripts/build/build_dmg.sh").read_text(encoding="utf-8")
    assert 'APP_NAME="Guardias de Patio"' in guion


def test_el_spec_conserva_el_nombre_que_espera_el_instalador_de_windows():
    fuente = _fuente_spec()
    assert 'else "GuardiasDePatio"' in fuente
    flujo = (RAIZ / ".github/workflows/compilar.yml").read_text(encoding="utf-8")
    assert "dist/GuardiasDePatio/GuardiasDePatio.exe" in flujo


def test_cada_plataforma_usa_su_icono():
    fuente = _fuente_spec()
    assert 'ICONO = "imagenes/icono.icns" if ES_MACOS else "imagenes/logo.ico"' in fuente
    assert (RAIZ / "imagenes" / "logo.ico").exists()
    # El .icns no se versiona: lo genera `make icon` antes de compilar.
    assert "icon" in (RAIZ / "Makefile").read_text(encoding="utf-8")


def test_el_flujo_publica_tambien_la_version_portable():
    """BLD-013 · en un centro casi nadie es administrador: hace falta una vía sin instalador."""
    flujo = (RAIZ / ".github/workflows/compilar.yml").read_text(encoding="utf-8")
    assert "Windows-Portable.zip" in flujo
    assert "dist/GuardiasDePatio/*" in flujo, "el zip sale de la carpeta que ya genera PyInstaller"
    assert "-name '*.zip'" in flujo, "sin esto el zip se queda en los artefactos y no llega al release"


def test_el_actualizador_no_confunde_el_portable_con_el_instalador():
    """El aviso de nueva versión filtra por extensión: el `.zip` no puede colarse."""
    checker = (RAIZ / "src/utils/update_checker.py").read_text(encoding="utf-8")
    assert '"Darwin": ".dmg"' in checker
    assert '"Windows": ".exe"' in checker
    assert ".zip" not in checker


# ---------------------------------------------------------------------------
# BLD-016 — el build de Windows también tiene que salir de ese spec
# ---------------------------------------------------------------------------
def _guion_de_windows() -> str:
    return (RAIZ / "scripts/build_windows.ps1").read_text(encoding="utf-8-sig")


def test_el_build_de_windows_usa_ese_spec():
    """Hasta v6.3.0 el script pasaba argumentos sueltos y `src/main.py`: PyInstaller
    escribía su propio spec encima de éste y el exe salía sin la hoja de estilos
    ni `upx=False`. El log del build de GitHub lo decía: «wrote …GuardiasDePatio.spec»."""
    guion = _guion_de_windows()
    assert SPEC in guion, "build_windows.ps1 no compila desde el spec"
    for argumento in ("--windowed", "--add-data", "--collect-all", "src/main.py", 'src\\main.py'):
        assert argumento not in guion, (
            f"{argumento!r} en build_windows.ps1: con argumentos sueltos PyInstaller "
            "regenera el spec y lo del repositorio no llega al exe"
        )


def test_la_variante_de_diagnostico_sale_del_mismo_spec():
    """Con consola y otro nombre, pero con las mismas piezas que la de verdad."""
    fuente = _fuente_spec()
    assert 'os.getenv("GUARDIAS_BUILD_DIAGNOSTICO")' in fuente
    assert "console=DIAGNOSTICO" in fuente
    assert 'NOMBRE += "-debug"' in fuente
    guion = _guion_de_windows()
    assert 'GUARDIAS_BUILD_DIAGNOSTICO = "1"' in guion
    assert "GuardiasDePatio-debug" in guion


def test_el_spec_lleva_los_widgets_de_carga_perezosa():
    """BLD-019 — v6.3.1 moría en Windows: los widgets se cargan con `importlib` y
    PyInstaller no los ve, así que ni el instalador ni el portable los llevaban."""
    spec = _fuente_spec()
    assert 'f"presentation.widgets.{f.stem}"' in spec
    assert '"src" / "presentation" / "widgets"' in spec
    widgets = RAIZ / "src" / "presentation" / "widgets"
    assert [f.stem for f in widgets.glob("*.py") if f.stem != "__init__"], "no hay widgets"
