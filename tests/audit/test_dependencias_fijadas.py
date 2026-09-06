"""Lote 19 — cadena de suministro (SUP-001, SUP-002, DEV-010).

Ejecución fijada con `==` en `requirements.txt`, desarrollo aparte en
`requirements-dev.txt`, foto completa en `requirements.lock`, `setuptools` sin la
CVE PYSEC-2026-3447 y los permisos del asistente compartidos como `settings.json`.
"""

import re
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DESARROLLO = {
    "pytest", "pytest-qt", "pytest-cov", "mutmut", "playwright", "ruff", "mypy", "pyinstaller"
}


def _requisitos(nombre: str) -> dict[str, str]:
    """{nombre normalizado: versión} de un fichero de requisitos."""
    pares = {}
    for linea in (RAIZ / nombre).read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea or linea.startswith("-r"):
            continue
        m = re.fullmatch(r"([A-Za-z0-9_.\-]+)(\[[^\]]+\])?\s*==\s*(\S+)", linea)
        assert m, f"{nombre}: '{linea}' no está fijada con =="
        pares[m.group(1).lower().replace("_", "-")] = m.group(3)
    return pares


def test_la_ejecucion_esta_fijada():
    assert len(_requisitos("requirements.txt")) >= 25


def test_las_herramientas_de_desarrollo_no_van_con_la_ejecucion():
    assert not DESARROLLO & set(_requisitos("requirements.txt"))


def test_el_desarrollo_incluye_la_ejecucion_y_las_herramientas():
    texto = (RAIZ / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "-r requirements.txt" in texto
    assert DESARROLLO <= set(_requisitos("requirements-dev.txt"))


def test_setuptools_sin_la_cve():
    """SUP-001: PYSEC-2026-3447, corregida en 83.0.0."""
    version = _requisitos("requirements-dev.txt")["setuptools"]
    assert tuple(int(x) for x in version.split(".")[:2]) >= (83, 0)
    pyproject = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    requisito = [r for r in pyproject["build-system"]["requires"] if r.startswith("setuptools")][0]
    assert re.search(r">=\s*8[3-9]|>=\s*9\d", requisito), requisito


def test_el_lock_recoge_todo_lo_fijado():
    lock = _requisitos("requirements.lock")
    fijadas = {**_requisitos("requirements.txt"), **_requisitos("requirements-dev.txt")}
    for nombre, version in fijadas.items():
        assert lock.get(nombre) == version, f"{nombre}: lock {lock.get(nombre)} ≠ {version}"


def test_pyproject_y_requirements_dicen_lo_mismo():
    pyproject = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    declaradas = {}
    for dep in pyproject["project"]["dependencies"]:
        m = re.fullmatch(r"([A-Za-z0-9_.\-]+)(\[[^\]]+\])?==(\S+)", dep)
        assert m, f"pyproject: '{dep}' no está fijada"
        declaradas[m.group(1).lower().replace("_", "-")] = m.group(3)
    assert declaradas == _requisitos("requirements.txt")
    assert "pytest" in " ".join(pyproject["project"]["optional-dependencies"]["dev"])


def test_los_permisos_del_asistente_se_comparten_como_settings_json():
    """DEV-010: `settings.local.json` es de cada equipo; lo compartido es `settings.json`."""
    assert (RAIZ / ".claude" / "settings.json").exists()
    assert ".claude/settings.local.json" in (RAIZ / ".gitignore").read_text(encoding="utf-8")
