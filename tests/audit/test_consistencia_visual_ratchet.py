"""Ratchets de consistencia visual. Umbrales = valor medido en el commit auditado (2026-09-04).
Sólo pueden bajar. Ver auditoria/04 y 05."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PRES = ROOT / "src" / "presentation"
UMBRALES = {
    "setStyleSheet": 287,
    "hex_literales": 631,
    "font_size_menor_12px": 89,
    "lineas_con_emoji": 327,
    "setFixed": 21,
    "setMinimum": 150,
}
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")


def _fuentes():
    return [p.read_text(encoding="utf-8", errors="ignore") for p in PRES.rglob("*.py")]


def _contar():
    textos = _fuentes()
    todo = "\n".join(textos)
    return {
        "setStyleSheet": todo.count("setStyleSheet"),
        "hex_literales": len(re.findall(r"#[0-9A-Fa-f]{6}\b", todo)),
        "font_size_menor_12px": sum(
            1 for m in re.findall(r"font-size: ?(\d+)px", todo) if int(m) < 12
        ),
        "lineas_con_emoji": sum(1 for line in todo.splitlines() if EMOJI.search(line)),
        "setFixed": len(re.findall(r"setFixed(?:Size|Width|Height)\(", todo)),
        "setMinimum": len(re.findall(r"setMinimum(?:Size|Width|Height)\(", todo)),
    }


@pytest.mark.parametrize("metrica", sorted(UMBRALES))
def test_ratchet_no_empeora(metrica):
    valor = _contar()[metrica]
    assert valor <= UMBRALES[metrica], (
        f"{metrica}: {valor} > {UMBRALES[metrica]}. Si has reducido deuda, baja el umbral; "
        "nunca lo subas."
    )


def test_tokens_no_definen_dos_primarios_distintos():
    """VIS-002: los paneles usan Tailwind (#3B82F6/#10B981) mientras tokens usan #007ACC/#1E7E34."""
    todo = "\n".join(_fuentes()).upper()
    tailwind = {"#3B82F6", "#10B981", "#059669", "#2563EB"}
    usados = {c for c in tailwind if c in todo}
    if usados:
        pytest.xfail(f"VIS-002: colores fuera de tokens en uso: {sorted(usados)}")


def test_fuente_global_existe_en_windows():
    """VIS-003: '-apple-system' no es una familia válida en Windows/Linux."""
    main = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    if 'QFont("-apple-system")' in main:
        pytest.xfail("VIS-003: fuente global -apple-system; usar pila por SO")
