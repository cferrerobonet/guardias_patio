# Guardias de Patio — Instrucciones del asistente

## Comunicación
- Español. Respuestas mínimas: sin explicaciones no pedidas, sin código de ejemplo no solicitado.
- No añadir docstrings, comentarios, type hints ni error handling a código no modificado. No refactorizar lo no pedido.
- No crear archivos nuevos (ni `.md`) salvo necesidad estricta o petición explícita.
- Nunca escribir la palabra prohibida por la bóveda (nombre del asistente) en ningún archivo del proyecto.

## Stack
Python 3.11 · PyQt6 6.7.0 · SQLAlchemy 2.0 + Alembic · FastAPI · OR-Tools CP-SAT · Pydantic v2 · Ruff (100 cols, comillas dobles) · mypy estricto sólo en `domain/` · pytest + pytest-qt.
Arquitectura: Clean Architecture híbrida + DDD táctico. BD: SQLite por usuario en `data/users/{hash}/guardias_patio.db`.

## Mapa rápido (no volver a explorar)
| Qué | Dónde |
| --- | --- |
| Entry GUI / API | `src/main.py` (login, sync, ventana) / `src/api/main.py` |
| Ventana y navegación | `src/presentation/ccleaner_main_window.py` (10 vistas registradas en `create_views`), `components/ccleaner_sidebar.py` |
| Vista de generación **real** | `forms/asignacion_calculo_form.py` → `asignacion_widgets/calculo_panel.py` (cuotas) + `generacion_panel.py` (generar, resultados, emails) |
| Progreso / hilos | `widgets/progress_indicators.py` (`ejecutar_con_progreso`, `ProgressDialog`), `progress_worker.py` (`WorkerThread`), `progress_handlers.py` |
| Caso de uso generación | `application/use_cases/asignacion_guardias/generar_guardias.py` → `services/asignador_guardias_cpsat.py` (+ `_asignador_cpsat_helpers.py`) o `services/asignador_guardias_v4_hibrido.py` |
| Sesión BD y PRAGMAs | `database/db_manager.py` (`initialize_user_database`, NullPool, `check_same_thread=False`, journal DELETE) |
| Sync SFTP y bloqueo | `sync/sync_manager.py`, `sync/session_lock.py`, `widgets/sync_progress_dialog.py` (`SyncWorker`) |
| Tema y tokens | `presentation/theme/tokens.py`, `theme/light.qss`, `themes/ccleaner_theme.py` (tres capas + inline) |
| Modelos ORM | `infrastructure/database/models.py` |
| Versión canónica | `src/config/settings.py` → `app_version` (pyproject/README están desincronizados) |
| Build | macOS: `Makefile` (`make dmg`) + `scripts/build/build_dmg.sh` · Windows: `scripts/build_windows.ps1` (canónico). Ignorar `scripts/build/build_windows.*`, `create_dmg.sh`, `build_simple.sh` |
| Código muerto (no tocar ni testear) | `forms/asignacion_guardias_form.py`, `forms/dashboard_form.py`, `forms/home_form.py`, `ui_styles.py` |
| Auditoría vigente | `auditoria/00_INDICE.md` → `30_REGISTRO_HALLAZGOS.md` (estado) · `17_PLAN_DE_ATAQUE.md` (backlog) · `06_CRASH_WINDOWS_GENERACION.md` |

## Comandos que funcionan
```bash
PY=.venv/bin/python; export QT_QPA_PLATFORM=offscreen   # .venv reparado en v5.45.0 (PyQt 6.7.0, igual que el build)
$PY -m pytest tests/test_x.py -q --no-cov -x                         # un fichero
$PY -m pytest tests/audit -q --no-cov                                 # suite de auditoría
$PY -m pytest tests/ -q --no-cov --timeout=120 -p no:cacheprovider    # todo (requiere pytest-timeout)
$PY -m ruff check src --statistics
```
Los tests de API necesitan `GUARDIAS_API_SECRET_KEY=<cualquiera>` en el entorno y `slowapi` instalado.
La suite completa pasa de una sola pasada (~2.454 tests, 47 s). La fixture automática `dialogos_modales` de `tests/conftest.py` impide que un `exec()` modal la bloquee; marcador `modales_reales` para desactivarla.

## Patrón polimórfico (Session | RepositoryFactory)
Servicios en `src/services/` y clases en `src/presentation/` aceptan ambos; normalizar en `__init__`:
```python
self.session = session_or_factory.session if isinstance(session_or_factory, RepositoryFactory) else session_or_factory
```
En funciones standalone, sin anotación `: Session` en el parámetro.

## Versionado, commits, changelog
- SemVer en `app_version`: fix → patch · feat → minor · breaking → major. Bump manual.
- Conventional Commits en español, minúscula tras los dos puntos: `tipo(scope): descripción`. Tipos: feat, fix, refactor, style, perf, test, chore, docs. Scopes: ui, api, domain, sync, db, algo, config, build.
- `CHANGELOG.md` (Keep a Changelog, español): secciones `🎯 Resumen`, `✨ Added`, `Changed`, `Fixed`, `🧹 Housekeeping`.

## Workflow post-modificaciones (obligatorio, sin pedir confirmación)
1. Tests: `$PY -m pytest tests/ --tb=no -q --no-cov` (corregir sólo fallos nuevos).
2. Bump `app_version`.
3. Entrada en `CHANGELOG.md` con fecha.
4. `git add -A && git commit -m "tipo(scope): descripción" && git tag v{versión} && git push && git push --tags`.

## Seguimiento de auditorías/guiones (obligatorio)
Al completar un ítem de un documento de auditoría o guion: tacharlo (`~~texto~~ ✅ RESUELTO vX.Y.Z`) en el documento fuente y en `auditoria/30_REGISTRO_HALLAZGOS.md`; commit junto al código.

## Archivos protegidos (no modificar)
`sftp_config.json`, `smtp_config.json`, `data/`, `alembic/versions/` existentes (sólo crear nuevas), `.env`.

## VS Code
Ejecución y Depuración trae 9 configuraciones (app, app sin bloqueo de sesión, app en modo diagnóstico, API, y cinco de tests) y Terminal → Ejecutar tarea otras 10 (tests, lint, formato, compilar macOS/Windows, limpiar). Usan el intérprete seleccionado en el editor: elegir `.venv`. `launch.json`, `tasks.json` y `extensions.json` están versionados; `settings.json` es de cada equipo.

## Skills del proyecto
`/build-windows-exe` · `/build-macos-dmg` · `/tests-locales` · `/auditoria-desktop`. No cargar `.agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md` completo: usar `auditoria/02_PLAN_MAESTRO_AUDITORIA.md`.

## Tokens
Leer por rangos con `grep -n`; no releer; no listar `src/` (usar el mapa); un fichero de tests a la vez; suite completa sólo al final.
