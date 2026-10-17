# Guardias de Patio — Instrucciones para agentes

Fuente única de instrucciones para cualquier asistente de código. El `CLAUDE.md` de la raíz solo la importa: los cambios se hacen aquí.

## Comunicación
- Español. Respuestas mínimas: sin explicaciones no pedidas, sin código de ejemplo no solicitado.
- No añadir docstrings, comentarios, type hints ni error handling a código no modificado. No refactorizar lo no pedido.
- No crear archivos nuevos (ni `.md`) salvo necesidad estricta o petición explícita.
- Reglas comunes (puerto 22, barrera de secretos, datos ficticios en tests, palabra prohibida, coautoría): CLAUDE.md de usuario.

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
| Caso de uso generación | `application/use_cases/asignacion_guardias/generar_guardias.py` → `services/asignador_guardias_cpsat.py` (+ `_asignador_cpsat_helpers.py`, `reparto_agrupado.py`: cuotas alcanzables, reparto justo y carriles). Criterios: `.claude/rules/reparto-guardias.md` |
| Sesión BD y PRAGMAs | `database/db_manager.py` (`initialize_user_database`, NullPool, `check_same_thread=False`, journal DELETE) |
| Sync SFTP y bloqueo | `sync/sync_manager.py` (qué se sube y cuándo), `sync/backends.py` (SFTP y carpeta local), `sync/cuentas.py` (ficha remota), `sync/session_lock.py`, `widgets/sync_progress_dialog.py` (`SyncWorker`). Reglas: `.claude/rules/sincronizacion.md` |
| Tema, tokens y PDF impresos | `presentation/theme/tokens.py`, `theme/light.qss`, `services/pdf_styles.py` y `_pdf_*.py`. Detalle: `.claude/rules/interfaz-y-documentos.md` |
| Modelos ORM | `infrastructure/database/models.py` |
| Versión canónica | `src/config/settings.py` → `app_version`, igual que `pyproject.toml` (lo vigila `tests/audit/test_calidad_estatica.py`). La insignia del README no se mantiene |
| Build y empaquetado | `.claude/rules/empaquetado.md`. La etiqueta `vX.Y.Z` compila las dos plataformas en GitHub. **Nunca compilar en local** (ni `make dmg`, que publica el release, ni `pyinstaller`) |

## Comandos que funcionan
```bash
PY=~/.venvs/guardias-patio/bin/python; export QT_QPA_PLATFORM=offscreen   # fuera de iCloud, obligatorio
$PY -m pytest tests/test_x.py -q --no-cov -x                         # un fichero
$PY -m pytest tests/audit -q --no-cov                                 # suite de auditoría
$PY -m pytest tests/ -q --no-cov --timeout=120 -p no:cacheprovider    # todo (requiere pytest-timeout)
$PY -m ruff check src --statistics
$PY -m bandit -r src -q -ll · $PY -m pip_audit --progress-spinner off · $PY -m radon cc src -s -n C · $PY -m vulture src --min-confidence 80
```
Reglas de tests (barreras, secreto de la API de 16+ caracteres, `timeout` en macOS): `.claude/rules/tests.md`. La suite completa pasa de una sola pasada (unos 2 minutos sin `tests/test_benchmark_cpsat.py`); el repositorio no se formatea con `ruff format`: la barrera es `ruff check`.

## Patrón polimórfico (Session | RepositoryFactory)
Servicios en `src/services/` y clases en `src/presentation/` aceptan ambos; normalizar en `__init__`:
```python
self.session = session_or_factory.session if isinstance(session_or_factory, RepositoryFactory) else session_or_factory
```
En funciones standalone, sin anotación `: Session` en el parámetro.

## Interfaz
Detalle en `.claude/rules/interfaz-y-documentos.md`. Lo esencial:
- Listados sin paginación (CarlosFB, 2026-10-17): todas las filas, con buscador, filtros y orden (`widgets/listado_filtrable.py`).
- **Icono de la app (`imagenes/icono.png`) ≠ logo de EPLA**: el icono en ventanas, Dock e instaladores; el logo solo dentro (cabeceras, inicio, PDF, correos).
- **Recreos**: toda salida traduce el id con `services/recreos.py`; nunca pintar `guardia.recreo` tal cual.

## Versionado, commits, changelog
- SemVer en `app_version` **y en `pyproject.toml`** (un test vigila que coincidan): fix → patch · feat → minor · breaking → major.
- Conventional Commits en español, minúscula tras los dos puntos: `tipo(scope): descripción`. Tipos: feat, fix, refactor, style, perf, test, chore, docs. Scopes: ui, api, domain, sync, db, algo, config, build.
- `CHANGELOG.md` (Keep a Changelog, español): secciones `🎯 Resumen`, `✨ Added`, `Changed`, `Fixed`, `🧹 Housekeeping`.

## Workflow post-modificaciones (obligatorio, sin pedir confirmación)
1. Tests: `$PY -m pytest tests/ --tb=no -q --no-cov --timeout=120 -p no:cacheprovider` (corregir sólo fallos nuevos; sin `--timeout` se cuelga QA-008).
2. Bump `app_version`.
3. Entrada en `CHANGELOG.md` con fecha.
4. `git add <rutas> && git commit -m "tipo(scope): descripción" && git tag v{versión} && git push && git push --tags`.

## Seguimiento de guiones (obligatorio)
Al completar un ítem de un guion: tacharlo (`~~texto~~ ✅ RESUELTO vX.Y.Z`) en el documento fuente; commit junto al código.

## Archivos protegidos (no modificar)
`data/`, `alembic/versions/` existentes (sólo crear nuevas), `.env`.

## Entorno
Intérprete en `~/.venvs/guardias-patio`, **fuera de iCloud** (dentro, iCloud duplica los binarios con copias « 2» y Qt aborta al crear la `QApplication`). El `.venv` del repo está corrupto y se puede borrar. Recrear con:
```bash
python3.11 -m venv ~/.venvs/guardias-patio
~/.venvs/guardias-patio/bin/python -m pip install -r requirements-dev.txt
```

## VS Code
Configuraciones de depuración y tareas versionadas (`launch.json`, `tasks.json`); usan el intérprete `~/.venvs/guardias-patio/bin/python`, no el `.venv` del repo.

## Comprobación tras editar
Ganchos comunes (`.claude/hooks/`, registrados en `.claude/settings.json`): `tras_editar.sh` compila cada `.py` editado y `guardia_bash.sh` bloquea las órdenes vetadas (`git add -A`, push forzado, `--no-verify`). No sustituyen a `ruff` ni a los tests.

## Datos de ejemplo
Están fuera del repositorio, en `../DATOS DE EJEMPLO (fuera del repositorio)/`. No copiarlos dentro: son datos reales del centro.

## Skills del proyecto
En `.claude/skills/`: `/build-windows-exe` · `/build-macos-dmg` · `/tests-locales`.
Auditoría: skill de usuario `auditoria-apps`; hallazgos en la bóveda, `GUARDIAS DE PATIO — Auditoría.md`.

## Tokens
Leer por rangos con `grep -n`; no releer; no listar `src/` (usar el mapa); un fichero de tests a la vez; suite completa sólo al final.

## Secretos y datos personales
Barrera: `scripts/comprobar_secretos.sh` (gancho de git y CI «Secretos»); excepciones en `.secretos-ignorar`, siempre con su motivo. La sincronización SFTP de la app cuenta en el presupuesto de conexiones: límite de reintentos en `.claude/rules/sincronizacion.md`.
