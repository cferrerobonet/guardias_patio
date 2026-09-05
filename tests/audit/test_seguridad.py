"""Seguridad: secreto de la API, credenciales en disco y superficie de descarga.

Cubre SEC-001 (permisos del fichero de credenciales), SEC-002 (la API no arranca
sin secreto) y SEC-003 (hallazgos medios de bandit), más BLD-006 (el instalador
no exige administrador y cierra la aplicación abierta).
"""

import os
import re
import stat
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# SEC-002: la API falla cerrada
# ---------------------------------------------------------------------------
def _ajustes_con_secreto(valor: str):
    from config.settings import Settings

    return Settings(api_secret_key=valor)


def test_sin_secreto_la_api_no_arranca():
    from config.settings import SecretoDeApiNoConfigurado, validar_secreto_de_api

    with pytest.raises(SecretoDeApiNoConfigurado) as excinfo:
        validar_secreto_de_api(_ajustes_con_secreto(""))

    assert "GUARDIAS_API_SECRET_KEY" in str(excinfo.value)
    assert "secrets.token_urlsafe" in str(excinfo.value), "el error no dice cómo generarlo"


def test_un_secreto_de_juguete_tampoco_vale():
    """Un HS256 con clave de cuatro letras se firma igual y se adivina en segundos."""
    from config.settings import SecretoDeApiNoConfigurado, validar_secreto_de_api

    with pytest.raises(SecretoDeApiNoConfigurado):
        validar_secreto_de_api(_ajustes_con_secreto("test"))


def test_un_secreto_en_condiciones_pasa():
    from config.settings import validar_secreto_de_api

    validar_secreto_de_api(_ajustes_con_secreto("un-secreto-suficientemente-largo"))


def test_la_api_valida_el_secreto_antes_de_construirse():
    """La comprobación va arriba: si no, el fallo aparecía al firmar el primer token."""
    fuente = (ROOT / "src" / "api" / "main.py").read_text(encoding="utf-8")
    assert "validar_secreto_de_api()" in fuente
    assert fuente.index("validar_secreto_de_api()") < fuente.index("app = FastAPI(")


# ---------------------------------------------------------------------------
# SEC-001: el fichero de credenciales no queda legible por todo el equipo
# ---------------------------------------------------------------------------
@pytest.mark.skipif(os.name == "nt", reason="los permisos POSIX no aplican en Windows")
def test_el_fichero_de_credenciales_queda_solo_para_su_dueno(tmp_path):
    from core.paths import proteger_fichero_de_credenciales

    env = tmp_path / ".env"
    env.write_text("SFTP_PASSWORD=secreta")
    os.chmod(env, 0o644)

    proteger_fichero_de_credenciales(env)

    assert stat.S_IMODE(env.stat().st_mode) == 0o600


def test_todas_las_escrituras_del_env_protegen_el_fichero():
    """Si alguien añade otro punto de guardado, tiene que protegerlo también."""
    ofensores = []
    for f in (ROOT / "src").rglob("*.py"):
        texto = f.read_text(encoding="utf-8", errors="ignore")
        if 'open(env_path, "w")' not in texto:
            continue
        if texto.count("proteger_fichero_de_credenciales") < texto.count('open(env_path, "w")'):
            ofensores.append(str(f.relative_to(ROOT)))

    assert not ofensores, f"escriben el .env sin protegerlo: {ofensores}"


# ---------------------------------------------------------------------------
# SEC-003: sin hallazgos medios ni altos de bandit
# ---------------------------------------------------------------------------
def test_bandit_sin_hallazgos_medios_ni_altos():
    import json
    import subprocess
    import sys

    proceso = subprocess.run(
        [sys.executable, "-m", "bandit", "-r", "src", "-ll", "-q", "-f", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if "No module named" in proceso.stderr:
        pytest.skip("bandit no está instalado en este entorno")

    resultados = json.loads(proceso.stdout).get("results", [])
    detalle = [f"{r['test_id']} {r['filename']}:{r['line_number']}" for r in resultados]
    assert not resultados, f"bandit encuentra hallazgos medios o altos: {detalle}"


def test_las_descargas_solo_aceptan_https_de_github():
    """SEC-003 (B310): `urlopen` admite `file:` y esquemas propios."""
    from utils.update_checker import url_de_confianza

    assert url_de_confianza("https://github.com/cferrerobonet/x/releases/y.dmg")
    assert url_de_confianza("https://objects.githubusercontent.com/z")
    assert not url_de_confianza("file:///etc/passwd")
    assert not url_de_confianza("http://github.com/x")
    assert not url_de_confianza("https://sitio-que-no-toca.example.com/x.exe")
    assert not url_de_confianza("")


# ---------------------------------------------------------------------------
# BLD-006: el instalador
# ---------------------------------------------------------------------------
def test_el_instalador_no_exige_administrador():
    """En un centro lo normal es no tener permisos de administrador."""
    iss = (ROOT / "installer_windows.iss").read_text(encoding="utf-8", errors="ignore")
    assert re.search(r"^PrivilegesRequired=lowest", iss, re.M)
    assert "PrivilegesRequiredOverridesAllowed=dialog" in iss


def test_el_instalador_cierra_la_aplicacion_abierta():
    iss = (ROOT / "installer_windows.iss").read_text(encoding="utf-8", errors="ignore")
    assert "CloseApplications=yes" in iss
