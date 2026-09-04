---
tags:
  - gestion-centro
  - auditoria
  - tests
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Estrategia de tests

## 1. Estado actual

| Aspecto | Evidencia | Valoración |
| --- | --- | --- |
| Volumen | 2.432 tests colectados en 131 ficheros. Ejecutados por fichero: **2.376 pasan, 0 fallan**, 12 omitidos, 5 `xfail`, 7 `xpassed`, ~39 sin ejecutar por cuelgue | Alto y, salvo los cuelgues, sano |
| Base de datos | `sqlite:///:memory:` con rollback por test (`tests/conftest.py:28-62`) | Rápido, pero no prueba fichero, PRAGMAs, `journal_mode`, bloqueos ni migraciones reales |
| UI | pytest-qt con `QT_QPA_PLATFORM=offscreen` | Correcto; sin tests de afinidad de hilos ni de `ejecutar_con_progreso` con solver real |
| Formulario real de generación | `tests/ui/test_ui_asignacion.py` prueba `AsignacionGuardiasForm`, que no está registrada en la app | Cobertura ilusoria (QA-003) |
| Entorno | `.venv` sin intérprete válido; `/opt/homebrew/bin/python3.11` carece de `hypothesis`, `PyJWT`, `pytest-xdist`, `pytest-timeout`, `playwright` → 6 errores de colección y `make test-fast` inoperativo | QA-001 |
| Configuración | `pytest.ini` fuerza `--cov` y `filterwarnings = error`; `timeout = 300` sin plugin | QA-002 |
| Fallo tolerado | fichero de reglas de agentes (`.claude/`) documenta un test roto que "no se corrige" | QA-005 |
| Hilos | Ningún test verifica que widgets sólo se toquen en el hilo GUI | QA-004 |
| Build | Ningún test de spec/versión/artefacto | BLD |

## 2. Pirámide objetivo

| Nivel | Qué | Herramienta | BD | Tiempo objetivo |
| --- | --- | --- | --- | --- |
| Unitario dominio | VOs, entidades, reglas de equidad y elegibilidad | pytest + hypothesis | ninguna | < 20 s |
| Unitario aplicación | casos de uso con repos falsos; **Preflight** | pytest | memoria | < 30 s |
| Integración infraestructura | repos SQLAlchemy, migraciones Alembic, backups, exportadores | pytest + **SQLite en fichero** (`tests/audit/conftest.py::db_fichero`) | fichero en `tmp_path` con los mismos PRAGMAs que producción | < 60 s |
| Compliance solver | restricciones duras y métricas blandas por escenario | `tests/compliance` (existente) | memoria | < 120 s |
| UI de componentes | formularios, tablas, diálogos, estados vacío/error/bloqueado | pytest-qt | memoria | < 90 s |
| UI de flujo (caminos dorados) | GP-1…GP-6 sobre la ventana real (`CCleanerMainWindow`) con BD en fichero; cuenta de clics como aserción | pytest-qt | fichero | < 120 s |
| Hilos y cierre | afinidad de hilo, cancelación, excepthook, sesión por hilo | pytest-qt + `threading` | fichero | < 30 s |
| Ratchets estáticos | hex fuera de tokens, font-size < 12, `accessibleName` en tablas, F821, imports prohibidos | pytest + ruff | – | < 10 s |
| E2E web | FastAPI: `/docs`, login, endpoints, contratos | **Playwright** (Python) + `pytest-playwright` | fichero | < 60 s |
| Build | spec válido, versión única, arranque del artefacto (`--version`) | pytest + subprocess (CI) | – | – |

## 3. Qué se ha añadido en esta entrega

```
tests/audit/
├── conftest.py                          fixture db_fichero (SQLite real en tmp_path con PRAGMAs), qapp
├── test_crash_windows_regresion.py      CRW-001/002/004/005: hilos, callbacks, excepthook (xfail estricto hasta el fix)
├── test_guardarrailes_flujo.py          UXF-002: precondiciones de generación; secuencia (xfail estricto)
├── test_consistencia_visual_ratchet.py  VIS: ratchets con umbral actual; fallan si empeora
└── test_calidad_estatica.py             COD/CRW-008: F821 = 0 (xfail), sin PyQt6 en services/application
tests/e2e_playwright/
├── README.md                            instalación y alcance
└── test_api_docs.py                     Swagger, token, endpoints (skip si playwright no está)
```

Marcas: `@pytest.mark.audit` para toda la carpeta; `xfail(strict=True)` para los tests que describen el comportamiento objetivo (obligan a retirar la marca cuando el fix llega, evitando falsos verdes).

## 4. Sobre Playwright en una app PyQt6

Playwright automatiza navegadores; **no puede accionar widgets Qt**. En este proyecto aplica a:

1. La API FastAPI y su Swagger/ReDoc (`src/api/main.py`), incluido el flujo de token.
2. Cualquier futura consulta web para el profesorado (FUN-009).
3. Verificación visual de los PDF exportados abriéndolos en Chromium (captura y comparación de píxeles), útil para regresión de plantillas.

Para el escritorio, el equivalente es pytest-qt (`qtbot.mouseClick`, `waitSignal`, `waitUntil`) con la ventana real y BD en fichero, que es lo que hace `tests/audit`. Si se quiere grabación de vídeo/capturas de la app nativa, usar `QWidget.grab()` en tests y guardar PNG como evidencia.

## 5. Comandos canónicos

```bash
PY=/opt/homebrew/bin/python3.11
export QT_QPA_PLATFORM=offscreen

# Instalar dependencias de test que faltan
$PY -m pip install hypothesis pytest-xdist pytest-timeout PyJWT playwright pytest-playwright
$PY -m playwright install chromium

# Rápido, sin cobertura
$PY -m pytest tests/ -q --no-cov -p no:cacheprovider -x

# Sólo auditoría
$PY -m pytest tests/audit -q --no-cov -m audit

# Paralelo (unit)
$PY -m pytest tests/ -m "not ui and not slow and not benchmark" -n auto --no-cov -q

# E2E web
$PY -m pytest tests/e2e_playwright -q --no-cov
```

## 6. Gates

| Gate | Condición | Dónde |
| --- | --- | --- |
| G-T1 | Colección sin errores (0 `ERROR` en `--co`) | CI, pre-commit |
| G-T2 | Suite completa verde sin `xfail` que pase (`strict`) ni skips sin motivo | CI |
| G-T3 | Ratchets no empeoran (umbrales en `test_consistencia_visual_ratchet.py`) | CI |
| G-T4 | `tests/audit` verde tras cada lote de remediación con marcas retiradas | Lote |
| G-T5 | Generación completa en Windows congelado ×10 sin cierre (manual con `faulthandler`) | Release |

## 7. Hallazgos QA

| ID | Sev. | Hallazgo | Recomendación |
| --- | --- | --- | --- |
| QA-001 | P1 | Entorno de tests no reproducible: venvs rotos, deps ausentes (`hypothesis`, `PyJWT`, `slowapi`, `pytest-timeout`, `xdist`) y variable `GUARDIAS_API_SECRET_KEY` obligatoria no documentada | `requirements-dev.txt` + `make venv` que cree `.venv` con `python3.11` y lo use en todos los targets; `conftest` de API que fije un secreto de pruebas |
| QA-002 | P2 | `pytest.ini` con cov obligatorio, `filterwarnings=error`, `timeout` sin plugin | cov sólo en `make coverage`; instalar `pytest-timeout`; warnings a error sólo en CI |
| QA-003 | P2 | Tests del formulario muerto `AsignacionGuardiasForm` | Migrar a `AsignacionCalculoForm`/`GeneracionPanel` y borrar el formulario |
| QA-004 | P2 | Sin tests de hilos/cancelación/excepthook | `tests/audit/test_crash_windows_regresion.py` |
| QA-005 | P2 | Fallo preexistente tolerado; skips amplios en a11y | Corregir o borrar el test; prohibir `except Exception: pytest.skip` |
| QA-006 | P3 | Nada se prueba sobre SQLite en fichero ni migraciones reales | fixture `db_fichero` + test de `alembic upgrade head` sobre fichero |
| QA-007 | P3 | Sin E2E de la superficie web | `tests/e2e_playwright` |
| QA-008 | P1 | Tests que bloquean la suite para siempre: `test_toggle_editable` (SMTP y SFTP) llama a `_toggle_editable()`, que abre un `QMessageBox` modal y espera en `msg.exec()` (`smtp_widget.py:185-274`); hay más casos en `tests/test_import_export_form.py`. `pytest-timeout` no los interrumpe porque el manejador de señales de Python no se ejecuta mientras el bucle de eventos de Qt corre en C++ | Los tests que puedan abrir un modal deben parchearlo (`monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.StandardButton.No)`) o llamar a la lógica sin el diálogo; en CI, ejecutar por fichero con límite de tiempo externo hasta corregirlos |
| QA-009 | P3 | 7 marcas `xfail` obsoletas que ya pasan (`test_dialogs_basic.py` ×6, `test_gestor_ausencias.py` ×1) | Retirarlas; activar `xfail_strict = true` en `pytest.ini` para que no vuelvan a acumularse |
| QA-010 | P3 | `tests/__pycache__` con bytecode de una ubicación anterior del proyecto y de otra versión de pytest | Borrar `__pycache__` y añadir la limpieza a `make clean` |
