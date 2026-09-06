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
