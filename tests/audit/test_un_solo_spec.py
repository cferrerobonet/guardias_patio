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
