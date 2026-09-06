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
| Ventana y navegación | `src/presentation/ventana_principal.py` (10 vistas en `create_views`; `ContentWrapper` con margen inferior), `components/menu_lateral.py` |
| Vista de generación **real** | `forms/asignacion_calculo_form.py` → `asignacion_widgets/calculo_panel.py` (cuotas) + `generacion_panel.py` (generar, resultados, emails) |
| Progreso / hilos | `widgets/progress_indicators.py` (`ejecutar_con_progreso`, `ProgressDialog`), `progress_worker.py` (`WorkerThread`), `progress_handlers.py` |
| Caso de uso generación | `application/use_cases/asignacion_guardias/generar_guardias.py` → `services/asignador_guardias_cpsat.py` (+ `_asignador_cpsat_helpers.py`) o `services/asignador_guardias_v4_hibrido.py` |
| Sesión BD y PRAGMAs | `database/db_manager.py` (`initialize_user_database`, NullPool, `check_same_thread=False`, journal DELETE) |
| Sync SFTP y bloqueo | `sync/sync_manager.py` (qué se sube y cuándo), `sync/backends.py` (SFTP y carpeta local), `sync/cuentas.py` (ficha remota), `sync/session_lock.py`, `widgets/sync_progress_dialog.py` (`SyncWorker`) |
| Tema y tokens | `presentation/theme/tokens.py`, `theme/light.qss`, `themes/tema_aplicacion.py` (tres capas + inline) |
| Modelos ORM | `infrastructure/database/models.py` |
| Versión canónica | `src/config/settings.py` → `app_version` (pyproject/README están desincronizados) |
| Build | Sin PC Windows: publicar etiqueta `vX.Y.Z` → `.github/workflows/compilar.yml` compila las dos y las adjunta al release. En local: macOS `make dmg`; Windows `scripts/build_windows.ps1` (`-Diagnostico` para consola). **Un solo spec**: `GuardiasDePatio.spec` (lleva `keyring.backends`) |
| Auditoría vigente | `auditoria/00_INDICE.md` → `30_REGISTRO_HALLAZGOS.md` (estado) · `17_PLAN_DE_ATAQUE.md` (backlog) · **`21_PLAN_DE_AUDITORIA_AMPLIADO.md`** (checks con comando, para auditar con modelos más pequeños) · `22_RECURSOS_DE_IA.md` (qué skill usar cuándo) |

## Comandos que funcionan
```bash
PY=~/.venvs/guardias-patio/bin/python; export QT_QPA_PLATFORM=offscreen   # fuera de iCloud, obligatorio
$PY -m pytest tests/test_x.py -q --no-cov -x                         # un fichero
$PY -m pytest tests/audit -q --no-cov                                 # suite de auditoría
$PY -m pytest tests/ -q --no-cov --timeout=120 -p no:cacheprovider    # todo (requiere pytest-timeout)
$PY -m ruff check src --statistics
$PY -m bandit -r src -q -ll · $PY -m pip_audit --progress-spinner off · $PY -m radon cc src -s -n C · $PY -m vulture src --min-confidence 80
```
Los tests de API necesitan `GUARDIAS_API_SECRET_KEY=<cualquiera>` en el entorno y `slowapi` instalado.
La suite completa pasa de una sola pasada (~2.880 tests, 60 s sin `tests/benchmarks`). Cuatro barreras automáticas en `tests/conftest.py` impiden que un test toque algo real: `dialogos_modales`, `sin_smtp_de_verdad`, `sin_llavero_de_verdad`, `sin_env_de_verdad` (marcadores `modales_reales`, `smtp_real`, `llavero_real`, `env_real` para desactivarlas).

## Patrón polimórfico (Session | RepositoryFactory)
Servicios en `src/services/` y clases en `src/presentation/` aceptan ambos; normalizar en `__init__`:
```python
self.session = session_or_factory.session if isinstance(session_or_factory, RepositoryFactory) else session_or_factory
```
En funciones standalone, sin anotación `: Session` en el parámetro.

## Versionado, commits, changelog
- SemVer en `app_version` **y en `pyproject.toml`** (un test vigila que coincidan): fix → patch · feat → minor · breaking → major.
- Conventional Commits en español, minúscula tras los dos puntos: `tipo(scope): descripción`. Tipos: feat, fix, refactor, style, perf, test, chore, docs. Scopes: ui, api, domain, sync, db, algo, config, build.
- `CHANGELOG.md` (Keep a Changelog, español): secciones `🎯 Resumen`, `✨ Added`, `Changed`, `Fixed`, `🧹 Housekeeping`.

## Workflow post-modificaciones (obligatorio, sin pedir confirmación)
1. Tests: `$PY -m pytest tests/ --tb=no -q --no-cov` (corregir sólo fallos nuevos).
2. Bump `app_version`.
3. Entrada en `CHANGELOG.md` con fecha.
4. `git add -A && git commit -m "tipo(scope): descripción" && git tag v{versión} && git push && git push --tags`.

## Barrera antes que test (obligatorio)
Un test que pueda tocar red, llavero, `.env`, servidor SFTP/SMTP o una base real se escribe **después** de la barrera en `tests/conftest.py`, nunca antes. El 2026-09-06 tres tests llegaron a IONOS, al Keychain y al `.env` de desarrollo por hacerlo al revés. Un fallo de test preexistente (no causado por la sesión) se anota y no se corrige en la misma sesión.

## Seguimiento de auditorías/guiones (obligatorio)
Al completar un ítem de un documento de auditoría o guion: tacharlo (`~~texto~~ ✅ RESUELTO vX.Y.Z`) en el documento fuente y en `auditoria/30_REGISTRO_HALLAZGOS.md`; commit junto al código.

## Archivos protegidos (no modificar)
`sftp_config.json`, `smtp_config.json`, `data/`, `alembic/versions/` existentes (sólo crear nuevas), `.env`.

## Entorno
El intérprete vive en `~/.venvs/guardias-patio`, **fuera de iCloud**: dentro del repositorio iCloud duplica y altera los binarios (402 copias " 2" en `.venv`), Qt deja de reconocer sus complementos y la app aborta al crear la `QApplication`. El `.venv` del repo está corrupto y se puede borrar. Recrear con:
```bash
python3.11 -m venv ~/.venvs/guardias-patio
~/.venvs/guardias-patio/bin/python -m pip install -r requirements.txt pyinstaller ruff mypy
```

## VS Code
Ejecución y Depuración trae 9 configuraciones (app, app sin bloqueo de sesión, app en modo diagnóstico, API, y cinco de tests) y Terminal → Ejecutar tarea otras 10 (tests, lint, formato, compilar macOS/Windows, limpiar). Usan el intérprete seleccionado en el editor: elegir `.venv`. `launch.json`, `tasks.json` y `extensions.json` están versionados; `settings.json` es de cada equipo.

## Skills del proyecto
`/build-windows-exe` · `/build-macos-dmg` · `/tests-locales` · `/auditoria-desktop`. No cargar `.agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md` completo: usar `auditoria/02_PLAN_MAESTRO_AUDITORIA.md`.

## Tokens
Leer por rangos con `grep -n`; no releer; no listar `src/` (usar el mapa); un fichero de tests a la vez; suite completa sólo al final.
