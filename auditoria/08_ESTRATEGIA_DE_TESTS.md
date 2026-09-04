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
| Volumen | **2.454 pasan, 0 fallan**, 11 omitidos, 29 `xfail`, en una sola pasada de 47 s (v5.44.0) | Sano |
| Base de datos | `sqlite:///:memory:` con rollback por test (`tests/conftest.py:28-62`) | Rápido, pero no prueba fichero, PRAGMAs, `journal_mode`, bloqueos ni migraciones reales |
| UI | pytest-qt con `QT_QPA_PLATFORM=offscreen` | Correcto; sin tests de afinidad de hilos ni de `ejecutar_con_progreso` con solver real |
| Formulario real de generación | `tests/ui/test_ui_asignacion.py` prueba `AsignacionGuardiasForm`, que no está registrada en la app | Cobertura ilusoria (QA-003) |
| Entorno | `.venv` sin intérprete válido; `/opt/homebrew/bin/python3.11` carece de `hypothesis`, `PyJWT`, `pytest-xdist`, `pytest-timeout`, `playwright` → 6 errores de colección y `make test-fast` inoperativo | QA-001 |
| Configuración | `pytest.ini` fuerza `--cov` y `filterwarnings = error`; `timeout = 300` sin plugin | QA-002 |
| Fallo tolerado | fichero de reglas de agentes (`.claude/`) documenta un test roto que "no se corrige" | QA-005 |
| Hilos | Ningún test verificaba la afinidad de hilo; ahora `tests/audit` la cubre | QA-004 |
| Diálogos modales | Guarda `dialogos_modales` en `tests/conftest.py`: ningún `exec()` sin parchear puede volver a bloquear la suite | QA-008 resuelto |
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

## 4 bis. Entorno de desarrollo en VS Code (v5.45.0)

El `.venv` del repositorio estaba inservible: se creó cuando el proyecto vivía en una carpeta de OneDrive y su intérprete apuntaba a un Python 3.11.14 que ya no existe, además de traer PyQt 6.11 frente al 6.7.0 que fija `requirements.txt`. `settings.json` apuntaba justamente a ese intérprete, así que el descubrimiento de tests del editor no funcionaba.

Repararlo en su sitio no era suficiente, porque el sitio es el problema: **el proyecto vive en iCloud Drive y ahí un entorno virtual se corrompe**. iCloud había creado 402 archivos duplicados dentro de `.venv` (`libqcocoa 2.dylib`, `QtGui 2.pyi`…). Qt inspeccionaba su carpeta de complementos, no reconocía ninguno válido y abortaba el proceso en `QGuiApplicationPrivate::createPlatformIntegration()` al construir la `QApplication`; la aplicación se cerraba nada más lanzarla desde el editor. El propio proyecto ya convivía con este problema: `build_dmg.sh` copia el bundle fuera de iCloud antes de firmarlo por la misma razón.

El entorno pasa a `~/.venvs/guardias-patio`, fuera de la carpeta sincronizada, alineado con `requirements.txt` e incluyendo PyInstaller, ruff y mypy. Verificado: crea la `QApplication` con el backend real de macOS, la aplicación arranca hasta el diálogo de acceso y la suite completa pasa.

```bash
python3.11 -m venv ~/.venvs/guardias-patio
~/.venvs/guardias-patio/bin/python -m pip install -r requirements.txt pyinstaller ruff mypy
```

El `.venv` que quedó dentro del repositorio está corrupto y ocupa 711 MB: se puede borrar.

`.vscode/launch.json`, `tasks.json` y `extensions.json` pasan a estar versionados (con `.vscode/*` y excepciones, porque git no entra en un directorio excluido) para que el PC de Windows tenga las mismas configuraciones. `settings.json` sigue siendo de cada equipo.

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
