"""SEC-004 — ningún dato real del centro puede estar versionado.

El repositorio es público. Desde 2025-11-15 estuvieron en él dos PDF y cuatro
Excel con listados reales del claustro, bajo `docs/examples/`. Es información
personal de trabajadores de un centro educativo: nombres, tutorías, turnos.

Este test recorre lo que git tiene versionado y falla si vuelve a entrar algo
con esa pinta. Los datos de ejemplo que se quieran para pruebas se inventan.
"""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

#: Nombres que sólo pueden ser datos reales de un equipo o del servidor.
FICHEROS_DE_DATOS = {
    "guardias_patio_data.json",
    "last_sync.json",
    "session.lock",
    "cuenta.json",
    "guardias_patio.db",
    ".env",
    "sftp_config.json",
    "smtp_config.json",
}

#: Documentos de oficina: en este proyecto no hay ninguno que no sea del centro.
EXTENSIONES_DE_OFICINA = {".xlsx", ".xls", ".pdf", ".docx"}


def _versionados() -> list:
    salida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True
    ).stdout
    return [Path(p.decode("utf-8")) for p in salida.split(b"\0") if p]


def test_ningun_fichero_de_datos_esta_versionado():
    culpables = [str(p) for p in _versionados() if p.name in FICHEROS_DE_DATOS]
    assert culpables == [], f"datos reales en el repositorio: {culpables}"


def test_ningun_documento_de_oficina_esta_versionado():
    culpables = [
        str(p) for p in _versionados() if p.suffix.lower() in EXTENSIONES_DE_OFICINA
    ]
    assert culpables == [], f"documentos del centro en el repositorio: {culpables}"


def test_la_carpeta_de_ejemplos_no_existe():
    """Se retiró entera: lo que hubo dentro eran listados reales."""
    assert not (RAIZ / "docs" / "examples").exists()
