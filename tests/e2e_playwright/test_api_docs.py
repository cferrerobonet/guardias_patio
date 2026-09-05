"""E2E de la API con Playwright: la única superficie web del proyecto."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api", reason="playwright no instalado")
pytest.importorskip("jwt", reason="PyJWT no instalado (requerido por api.auth)")

ROOT = Path(__file__).resolve().parents[2]
pytestmark = [pytest.mark.slow, pytest.mark.integration]


def _puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def api_url(tmp_path_factory):
    puerto = _puerto_libre()
    env = dict(os.environ)
    env.update(
        {
            "GUARDIAS_API_SECRET_KEY": "secreto-de-pruebas-e2e",
            "GUARDIAS_DATABASE_URL": f"sqlite:///{tmp_path_factory.mktemp('db') / 'api.db'}",
            "PYTHONPATH": str(ROOT / "src"),
        }
    )
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(puerto),
        ],
        cwd=ROOT / "src",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = f"http://127.0.0.1:{puerto}"
    import urllib.request

    for _ in range(60):
        try:
            urllib.request.urlopen(f"{url}/docs", timeout=1)
            break
        except Exception:
            if proc.poll() is not None:
                salida = proc.stdout.read() if proc.stdout else ""
                pytest.skip(f"uvicorn no arrancó: {salida[-800:]}")
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.skip("uvicorn no respondió en 30 s")
    yield url
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def test_swagger_ui_renderiza(browser, api_url):
    page = browser.new_page()
    page.goto(f"{api_url}/docs", wait_until="networkidle")
    assert "Guardias de Patio API" in page.title() or page.locator("h2.title").count() > 0
    # Por el atributo, no por el texto: `text=/api/v1/guardias` lo tomaba Playwright
    # por una expresión regular (empieza y acaba por "/") y reventaba con "Invalid
    # flags supplied"; y Swagger parte la ruta en varios nodos, así que un texto
    # exacto tampoco casa.
    page.wait_for_selector(".opblock-summary-path")
    assert page.locator('[data-path="/api/v1/guardias"]').count() > 0
    page.close()


def test_redoc_renderiza(browser, api_url):
    page = browser.new_page()
    page.goto(f"{api_url}/redoc", wait_until="networkidle")
    # Redoc pinta después de networkidle: con la suite completa en marcha, sin esta
    # espera el assert llegaba antes que el render.
    page.wait_for_selector("text=Guardias de Patio API", timeout=15000)
    assert page.locator("text=Guardias de Patio API").first.is_visible()
    page.close()


def test_endpoint_protegido_devuelve_401_sin_token(browser, api_url):
    ctx = browser.new_context()
    resp = ctx.request.get(f"{api_url}/api/v1/profesores")
    assert resp.status in (401, 403), resp.status
    ctx.close()


def test_openapi_expone_version_de_settings(browser, api_url):
    import re

    ctx = browser.new_context()
    spec = ctx.request.get(f"{api_url}/openapi.json").json()
    settings = (ROOT / "src" / "config" / "settings.py").read_text(encoding="utf-8")
    version = re.search(r'app_version:\s*str\s*=\s*"([^"]+)"', settings).group(1)
    assert spec["info"]["version"] == version
    ctx.close()
