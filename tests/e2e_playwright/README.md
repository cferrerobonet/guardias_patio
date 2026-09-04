# E2E con Playwright (superficie web)

Playwright automatiza navegadores, no widgets PyQt6. En este proyecto cubre la API FastAPI
(`src/api/main.py`): Swagger UI, ReDoc y endpoints. Para la app de escritorio, usar pytest-qt (`tests/ui`, `tests/audit`).

```bash
PY=/opt/homebrew/bin/python3.11
$PY -m pip install playwright pytest-playwright PyJWT
$PY -m playwright install chromium
$PY -m pytest tests/e2e_playwright -q --no-cov
```

Los tests arrancan `uvicorn` en un puerto libre con una BD SQLite temporal y un secreto de API de prueba.
Si `playwright` no está instalado, la suite se omite (skip) sin fallar.
