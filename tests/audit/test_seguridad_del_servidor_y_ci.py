"""Lote 18 — SEC-007 (gate en cada push) y SEC-008 (huella del servidor).

La huella se prueba con claves de mentira y un `known_hosts` en carpeta temporal:
nada de esto toca el servidor real ni el `~/.ssh` de quien ejecuta la suite.
"""

import re
from pathlib import Path

import pytest
import yaml

from sync import huella_servidor

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
FLUJOS = ROOT / ".github" / "workflows"


# ---------------------------------------------------------------------------
# SEC-007 · comprobaciones en cada push
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def comprobar():
    return yaml.safe_load((FLUJOS / "comprobar.yml").read_text(encoding="utf-8"))


def test_el_flujo_se_dispara_en_push_y_en_pull_request(comprobar):
    # PyYAML lee `on:` como el booleano True; da igual, lo que importa es su contenido.
    disparadores = comprobar.get("on", comprobar.get(True))
    assert "push" in disparadores and "pull_request" in disparadores
    assert "main" in disparadores["push"]["branches"]


def test_el_flujo_ejecuta_lint_tipos_seguridad_y_suite(comprobar):
    texto = " ".join(
        paso.get("run", "")
        for trabajo in comprobar["jobs"].values()
        for paso in trabajo["steps"]
    )
    for herramienta in ("ruff", "mypy", "bandit", "pip-audit", "pytest"):
        assert herramienta in texto, f"el gate no ejecuta {herramienta}"


def test_las_acciones_estan_fijadas_por_version():
    """CHK-J-07: cada `uses:` con su versión, no una rama que puede cambiar."""
    sueltas = []
    for flujo in FLUJOS.glob("*.yml"):
        for n, linea in enumerate(flujo.read_text(encoding="utf-8").splitlines(), 1):
            m = re.search(r"uses:\s*(\S+)", linea)
            if m and not re.search(r"@(v\d|[0-9a-f]{40})", m.group(1)):
                sueltas.append(f"{flujo.name}:{n}: {m.group(1)}")
    assert sueltas == [], "\n".join(sueltas)


# ---------------------------------------------------------------------------
# SEC-008 · huella del servidor
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def clave():
    """Una clave de verdad, generada aquí: `known_hosts` no acepta uno inventado."""
    import paramiko

    return paramiko.ECDSAKey.generate()


@pytest.fixture(scope="module")
def otra_clave():
    import paramiko

    return paramiko.ECDSAKey.generate()


def test_la_huella_tiene_el_formato_que_ensena_ssh(clave, otra_clave):
    huella = huella_servidor.huella_sha256(clave)
    assert huella.startswith("SHA256:") and not huella.endswith("=")
    assert huella != huella_servidor.huella_sha256(otra_clave)


def test_un_servidor_nuevo_no_esta_confiado(tmp_path):
    assert huella_servidor.esta_confiado("sftp.epla.es", 22, ruta=tmp_path / "known_hosts") is False


def test_confiar_lo_anota_y_a_partir_de_ahi_esta_confiado(tmp_path, clave):
    fichero = tmp_path / ".ssh" / "known_hosts"
    assert huella_servidor.confiar("sftp.epla.es", 22, clave, ruta=fichero) is True
    assert fichero.exists()
    assert huella_servidor.esta_confiado("sftp.epla.es", 22, ruta=fichero) is True


def test_el_puerto_no_estandar_se_anota_como_lo_escribe_ssh(tmp_path, clave):
    fichero = tmp_path / "known_hosts"
    huella_servidor.confiar("sftp.epla.es", 2222, clave, ruta=fichero)
    assert "[sftp.epla.es]:2222" in fichero.read_text(encoding="utf-8")
    assert huella_servidor.esta_confiado("sftp.epla.es", 2222, ruta=fichero) is True
    assert huella_servidor.esta_confiado("sftp.epla.es", 22, ruta=fichero) is False


def test_el_fichero_queda_solo_para_su_dueno(tmp_path, clave):
    fichero = tmp_path / "known_hosts"
    huella_servidor.confiar("sftp.epla.es", 22, clave, ruta=fichero)
    assert oct(fichero.stat().st_mode)[-3:] == "600"


def test_el_arranque_ofrece_confirmar_la_huella_antes_de_rendirse():
    fuente = (SRC / "main.py").read_text(encoding="utf-8")
    assert "confirmar_huella_si_hace_falta" in fuente
    # Y sigue sin aceptar claves a ciegas.
    backends = (SRC / "sync" / "backends.py").read_text(encoding="utf-8")
    assert "set_missing_host_key_policy(paramiko.RejectPolicy())" in backends
    assert "AutoAddPolicy()" not in backends
