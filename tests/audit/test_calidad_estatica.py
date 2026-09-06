"""Gates estáticos: nombres indefinidos, versión única, código muerto y scripts de build."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _ruff(*args):
    resultado = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if "No module named ruff" in resultado.stderr:
        pytest.skip("ruff no está instalado en este intérprete")
    return resultado


def test_sin_nombres_indefinidos():
    """CRW-008 resuelto en v5.44.0: ruff no debe encontrar ningún nombre indefinido."""
    r = _ruff("src", "--select", "F821", "--quiet")
    if r.returncode not in (0, 1):
        pytest.skip(f"ruff no disponible: {r.stderr[:200]}")
    assert r.returncode == 0, r.stdout


def test_version_unica():
    """BLD-003 resuelto en v5.50.0: el bump toca settings.py y pyproject.toml."""
    settings = (ROOT / "src" / "config" / "settings.py").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    v_settings = re.search(r'app_version:\s*str\s*=\s*"([^"]+)"', settings).group(1)
    v_pyproject = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M).group(1)
    assert v_settings == v_pyproject


def test_formularios_muertos_no_estan_registrados():
    """COD-004: si alguien registra un formulario muerto, debe hacerlo a propósito."""
    ventana = (ROOT / "src" / "presentation" / "ventana_principal.py").read_text(
        encoding="utf-8"
    )
    for muerto in ("AsignacionGuardiasForm", "DashboardForm", "HomeForm"):
        assert muerto not in ventana, f"{muerto} se considera código muerto (COD-004)"


def test_los_scripts_de_build_invocan_specs_que_existen():
    """BLD-002 resuelto en v5.50.0: se eliminaron los scripts obsoletos.

    Solo se miran las invocaciones reales al compilador; antes se inspeccionaba
    todo el texto y los mensajes por pantalla daban falsos positivos.
    """
    invocacion = re.compile(r"""pyinstaller[^\n]*?["']?([\w .\-]+\.spec)""", re.I)
    ofensores = []
    for script in (ROOT / "scripts").rglob("*"):
        if script.suffix.lower() not in (".ps1", ".bat", ".sh"):
            continue
        texto = script.read_text(encoding="utf-8", errors="ignore")
        for spec in invocacion.findall(texto):
            nombre = spec.strip()
            if "$" in nombre or "%" in nombre:
                continue  # se resuelve en tiempo de ejecución
            if not (ROOT / nombre).exists():
                ofensores.append(f"{script.name}: {nombre}")
    assert not ofensores, ofensores


def test_make_clean_no_borra_specs():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    bloque = makefile[makefile.index("clean:") :].split("\n\n")[0]
    if "*.spec" in bloque:
        pytest.xfail("BLD-001: make clean borra *.spec, entrada del build de macOS")


def test_los_scripts_de_powershell_llevan_marca_de_orden():
    """
    Windows PowerShell 5.1 lee los ficheros sin marca de orden con la codificación
    ANSI del sistema. Entonces una «Ó» pasa a ser dos caracteres, y el segundo es
    una comilla tipográfica que PowerShell toma como delimitador de cadena: el
    script deja de analizarse. Con acentos, la marca es obligatoria.
    """
    sin_marca = []
    for script in ROOT.rglob("*.ps1"):
        if ".venv" in script.parts or "build" in script.parts[:1]:
            continue
        datos = script.read_bytes()
        tiene_acentos = any(b > 127 for b in datos)
        if tiene_acentos and not datos.startswith(b"\xef\xbb\xbf"):
            sin_marca.append(str(script.relative_to(ROOT)))
    assert not sin_marca, sin_marca


# ---------------------------------------------------------------------------
# COD-001 / COD-007: ratchets de calidad estática
# ---------------------------------------------------------------------------

#: Avisos de ruff que quedan en `src/`, todos `E501` (líneas largas), concentrados
#: en cadenas de texto —sobre todo el HTML de los correos—. Sólo puede bajar.
AVISOS_RUFF = 104


def _ejecutar(comando: list, cwd: Path | None = None) -> tuple:
    """Lanza una herramienta con el intérprete del entorno y devuelve (salida, ok)."""
    proceso = subprocess.run(
        [sys.executable, "-m", *comando],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )
    return proceso.stdout + proceso.stderr, proceso.returncode == 0


def test_ratchet_de_avisos_de_ruff():
    """COD-001: la deuda de estilo sólo puede bajar."""
    salida, _ = _ejecutar(["ruff", "check", "src", "--statistics"])
    if "No module named" in salida:
        pytest.skip("ruff no está instalado en este entorno")

    total = sum(
        int(m) for m in re.findall(r"^\s*(\d+)\s+[EWFI]\d+", salida, re.M)
    )
    assert total <= AVISOS_RUFF, (
        f"ruff: {total} avisos (umbral {AVISOS_RUFF}). Si has reducido deuda, baja el "
        "umbral; nunca lo subas.\n" + salida
    )


def test_el_dominio_pasa_mypy_sin_errores():
    """COD-007: la rigurosidad declarada para `domain` tiene que aplicarse de verdad.

    Hasta v5.61.0 convivían `mypy.ini` y `[tool.mypy]` en `pyproject.toml`. Ganaba
    el primero, cuyas secciones por módulo apuntaban a rutas inexistentes, así que
    las reglas estrictas del segundo nunca llegaron a aplicarse.
    """
    # mypy resuelve los módulos desde `src/`, que es la raíz de paquetes.
    salida, ok = _ejecutar(["mypy", "domain", "--no-error-summary"], cwd=ROOT / "src")
    if "No module named" in salida:
        pytest.skip("mypy no está instalado en este entorno")

    errores = [línea for línea in salida.splitlines() if ": error:" in línea]
    assert not errores, "mypy encuentra errores en domain:\n" + "\n".join(errores)


def test_una_sola_configuracion_de_mypy():
    """Dos ficheros de configuración significan que uno de los dos no se aplica."""
    assert not (ROOT / "mypy.ini").exists(), (
        "mypy.ini vuelve a existir: gana sobre pyproject.toml y deja sus reglas sin efecto"
    )
