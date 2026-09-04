---
name: tests-locales
description: Ejecutar los tests de Guardias de Patio en local (pytest, pytest-qt, BD SQLite en fichero, suite de auditoría y Playwright para la API). Usar antes de cualquier commit o cuando se pida correr tests.
---

# Tests en local

## Desde VS Code

Ejecución y Depuración → "Tests: fichero abierto", "Tests: suite completa", "Tests: auditoría" o "Tests: cumplimiento del algoritmo". Terminal → Ejecutar tarea para las mismas sin depurador. Requiere tener seleccionado el intérprete `.venv`.

## Intérprete y dependencias

```bash
PY=.venv/bin/python                      # reparado y alineado con requirements.txt (PyQt 6.7.0)
export QT_QPA_PLATFORM=offscreen
$PY -m pip install -r requirements.txt
$PY -m pip install hypothesis pytest-xdist pytest-timeout PyJWT slowapi playwright pytest-playwright
export GUARDIAS_API_SECRET_KEY=secreto-de-pruebas   # los tests de API fallan al importar sin secreto
$PY -m playwright install chromium       # sólo para tests/e2e_playwright
```

`.venv-1` y `.venv-win` son restos de otras instalaciones: no usarlos.

## Comandos

| Objetivo | Comando |
| --- | --- |
| Rápido, un fichero | `$PY -m pytest tests/test_x.py -q --no-cov -x` |
| Suite de auditoría (hilos, guardarraíles, ratchets, estática) | `$PY -m pytest tests/audit -q --no-cov` |
| Todo, sin cobertura, con timeout | `$PY -m pytest tests/ -q --no-cov --timeout=120 -p no:cacheprovider` |
| Paralelo (sin UI) | `$PY -m pytest tests/ -m "not ui and not slow and not benchmark" -n auto --no-cov -q` |
| Cobertura | `$PY -m pytest tests/ -q` (pytest.ini activa `--cov`) |
| E2E web | `$PY -m pytest tests/e2e_playwright -q --no-cov` |
| Compliance del solver | `$PY -m pytest tests/compliance -q --no-cov` |

## Notas

- `tests/audit` contiene tests `xfail(strict=True)`: describen el comportamiento objetivo de hallazgos abiertos. Cuando un fix llega, el test pasa, `strict` lo convierte en fallo y hay que **retirar la marca** en el mismo commit.
- Los ratchets de `test_consistencia_visual_ratchet.py` tienen umbrales con el valor actual: bajarlos al mejorar, nunca subirlos.
- `tests/audit/conftest.py::db_fichero` crea una BD SQLite real en `tmp_path` con los PRAGMAs de producción; usarla para tests de sesión, migraciones y concurrencia.
- Conocido: `tests/test_config_widgets_extra.py::TestSMTPConfigWidgetExtra::test_toggle_editable` se cuelga en offscreen (QA-008). Ejecutar siempre con `--timeout`.
- Playwright no automatiza PyQt6; sólo la API FastAPI (`src/api/main.py`).
