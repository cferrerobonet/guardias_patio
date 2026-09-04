"""Gates estáticos: nombres indefinidos, versión única, código muerto y scripts de build."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _ruff(*args):
    return subprocess.run(
        [sys.executable, "-m", "ruff", "check", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_sin_nombres_indefinidos():
    """CRW-008 resuelto en v5.44.0: ruff no debe encontrar ningún nombre indefinido."""
    r = _ruff("src", "--select", "F821", "--quiet")
    if r.returncode not in (0, 1):
        pytest.skip(f"ruff no disponible: {r.stderr[:200]}")
    assert r.returncode == 0, r.stdout


@pytest.mark.xfail(strict=True, reason="BLD-003: pyproject.toml 5.9.8 vs settings 5.42.x")
def test_version_unica():
    settings = (ROOT / "src" / "config" / "settings.py").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    v_settings = re.search(r'app_version:\s*str\s*=\s*"([^"]+)"', settings).group(1)
    v_pyproject = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M).group(1)
    assert v_settings == v_pyproject


def test_formularios_muertos_no_estan_registrados():
    """COD-004: si alguien registra un formulario muerto, debe hacerlo a propósito."""
    ventana = (ROOT / "src" / "presentation" / "ccleaner_main_window.py").read_text(
        encoding="utf-8"
    )
    for muerto in ("AsignacionGuardiasForm", "DashboardForm", "HomeForm"):
        assert muerto not in ventana, f"{muerto} se considera código muerto (COD-004)"


@pytest.mark.xfail(
    strict=True, reason="BLD-002: scripts obsoletos referencian guardias_patio_windows.spec"
)
def test_scripts_de_build_no_referencian_specs_inexistentes():
    ofensores = []
    for script in (ROOT / "scripts").rglob("*"):
        if script.suffix.lower() in (".ps1", ".bat", ".sh"):
            texto = script.read_text(encoding="utf-8", errors="ignore")
            for spec in re.findall(r"[\w \-]+\.spec", texto):
                if not (ROOT / spec.strip()).exists() and "SPEC_FILE" not in texto:
                    ofensores.append(f"{script.name}: {spec.strip()}")
    assert not ofensores, ofensores


def test_make_clean_no_borra_specs():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    bloque = makefile[makefile.index("clean:") :].split("\n\n")[0]
    if "*.spec" in bloque:
        pytest.xfail("BLD-001: make clean borra *.spec, entrada del build de macOS")
