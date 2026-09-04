---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Baseline y adaptador del proyecto

## Adaptador

| Campo | Valor |
| --- | --- |
| Proyecto | Guardias de Patio — gestión y asignación de guardias de patio (EPLA) |
| Repositorio / raíz | `github.com/cferrerobonet/guardias_patio` · carpeta `CODIGO FUENTE` dentro de la bóveda Obsidian (iCloud) |
| Commit | `742fe452fcdf646985011187eb9b4aea72cd9b0a` |
| Rama / worktree | `main` · limpio salvo `?? .agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md` y `?? auditoria/` (preservados) |
| Fecha / zona | 2026-09-04 · Europe/Madrid |
| Modo | `AUDIT_ONLY` sobre `src/`; entrega autorizada de `auditoria/`, `tests/audit`, `tests/e2e_playwright`, `.claude/skills`, fichero de instrucciones, `requirements.txt` (deps de test) y `pytest.ini` (marker `audit`) |
| Alcance | App de escritorio PyQt6 completa, API FastAPI, build/release, tests, agentes |
| Exclusiones autorizadas | Producción SFTP (sin acceso); máquina Windows (sin acceso); sesión manual con lector de pantalla |
| Stack verificado | Python 3.11.15 · PyQt6 6.7.0 (Qt 6.7.3) · SQLAlchemy 2.0 · Alembic · FastAPI · OR-Tools 9.14.6206 · Pydantic v2 · pytest 8.4.2 · pytest-qt 4.5.0 · ruff 0.14.0 · mypy 1.18.2 · bandit 1.8.6 · PyInstaller 6.16.0 |
| Módulos / superficies | 264 ficheros Python, 58.932 líneas en `src/`; 10 vistas registradas; 21 diálogos; 12 tablas; 6 routers API |
| Roles | Un único rol de usuario (jefatura) por perfil; perfiles aislados por BD |
| Versión canónica | `src/config/settings.py` → 5.42.3 (pyproject 5.9.8, README 3.2.1 desincronizados) |
| Esquema / migración | SQLAlchemy `models.py` + 26 revisiones Alembic |
| Build | macOS: `make dmg` · Windows: `scripts/build_windows.ps1` |
| Entorno dinámico local | Intérprete `/opt/homebrew/bin/python3.11`; `QT_QPA_PLATFORM=offscreen` |
| Contratos de producto/diseño | No existen `PRODUCT.md`/`DESIGN.md`; README y código como contrato provisional; borrador en [[05_CONTRATO_SISTEMA_DE_DISENO]] |
| Auditoría previa | `docs/AUDITORIA_INTEGRAL_2026.md` (referenciada en README, no presente en `docs/`); `auditoria/_work/paquete_ux_accesibilidad.md` (Ola 4, 2026-08-04) |

## Evidencia de comandos

### CMD-01 · Baseline git
- `git rev-parse HEAD; git status --short; git log --oneline -40` · exit 0 · commit arriba; sin cambios en ficheros versionados al inicio.

### CMD-02 · Entorno
- `.venv/bin/python --version` → sin salida (intérprete inválido). `.venv-1`, `.venv-win`: sin binario.
- `/opt/homebrew/bin/python3.11 -c "import PyQt6, ortools, pytest"` → OK (versiones en el adaptador).
- `pip list` → faltaban `hypothesis`, `PyJWT`, `pytest-xdist`, `pytest-timeout`, `playwright`. También faltaban `slowapi`, `fastapi`, `uvicorn`, `httpx`. Instalados con `--user` durante la auditoría para poder ejecutar la suite (QA-001). Los módulos de test de la API fallan al importar si `GUARDIAS_API_SECRET_KEY` está vacío (`jwt.exceptions.InvalidKeyError`), de modo que la suite requiere esa variable de entorno (no documentado hasta ahora).

### CMD-03 · Colección de tests
- `pytest --co -q --no-cov -p no:cacheprovider` (antes de instalar deps) → **2.295 tests, 6 errores** (`test_api*.py` por `jwt`; `test_hypothesis_domain.py` por `hypothesis`). Exit 2.

### CMD-04 · Lint y seguridad
- `ruff check src --statistics` → **355** avisos: E501 119, I001 95, F401 64, F811 26, W293 21, F841 13, E402 11, **F821 4**, F541 1, W291 1. Aviso de configuración obsoleta (`select`/`ignore` → `lint.*`).
- `ruff check src --select F821` → `wiring.py:68` (`Container`), `generacion_panel.py:413`, `gestion_cursos_widget.py:572`, `sync_manager.py:507` (`SQLAlchemyError`).
- `bandit -r src -q` → Low 26 · Medium 3 · High 0.

### CMD-05 · Métricas visuales deterministas
- Sobre `src/presentation`: `setStyleSheet` 287 · hex 631 (199 distintos) · `QMessageBox` 285 · `font-size` < 12 px 89 (< 11 px 43) · líneas con emoji 327 · `setMinimum*` 150 · `setFixed*` 21 · capas de estilo 4 ficheros (2.027 líneas).

### CMD-06 · Suite de auditoría nueva
- `pytest tests/audit -q --no-cov` → **9 passed, 19 xfailed** (0 fallos; los xfail estrictos documentan hallazgos abiertos). 1,3 s.

### CMD-07 · E2E web
- `pytest tests/e2e_playwright -q --no-cov` → 1 skipped (playwright no instalado). Comportamiento esperado.

### CMD-08 · Suite completa
- Primer intento (sin `pytest-timeout`): el proceso quedó a 0 % CPU durante 18 min en `tests/test_config_widgets_extra.py::TestSMTPConfigWidgetExtra::test_toggle_editable` (abre un `QMessageBox` modal en `_show_global_warning`); segundo intento colgado en `tests/test_import_export_form.py`. Registrado como **QA-008**.
- Ejecución definitiva con `--timeout=90`: resultado en la sección "Resultado de la suite completa" al final de este documento.

### CMD-09 · Logs
- `logs/`: 720 ficheros (646 `comparacion_cuotas_*.json`, 71 `app_*.log`). Ningún `app_*.log` proviene de Windows. `guardias_patio.log` muestra cada línea por triplicado (handlers duplicados). Sin trazas de `EXCEPCIÓN NO MANEJADA` ni `Error en WorkerThread` reales (sólo de tests).

## Limitaciones declaradas

- Sin máquina Windows: el cierre al terminar el cálculo no se ha reproducido; el análisis es estático y las causas se confirman con el protocolo de [[06_CRASH_WINDOWS_GENERACION]] §5.
- Sin credenciales SFTP/SMTP de producción: sync, bloqueo de sesión y correo no se han ejecutado contra el servidor.
- Sin sesión manual con NVDA/VoiceOver.
- Cobertura por riesgo no medida (suite ejecutada con `--no-cov` por tiempo).
- Los recuentos de clics de [[03_UX_CASOS_DE_USO_Y_CAMINOS_DORADOS]] derivan del código; conviene confirmarlos con una grabación.

## Resultado de la suite completa

La suite **no puede ejecutarse de una sola vez**: cuatro ficheros la bloquean indefinidamente (QA-008). El baseline se obtuvo ejecutando cada fichero de test como invocación independiente con un límite de tiempo externo de 150 s (`perl -e 'alarm 150; exec @ARGV'`) y con el plugin de tiempo desactivado (`-p no:timeout`).

### Por qué hizo falta ese montaje

`pytest-timeout` usa por defecto el método `signal`: instala un manejador de `SIGALRM` y arma su propio temporizador **en cada test**, lo que descarta cualquier alarma externa pendiente. Su manejador tampoco llega a ejecutarse, porque el intérprete está retenido dentro del bucle de eventos de Qt en C++ y los manejadores de señales de Python sólo corren entre instrucciones de bytecode. Resultado: con `--timeout` la suite se queda colgada para siempre; sin él, la alarma externa sí termina el proceso.

### Resultado (131 ficheros, cada uno por separado)

| Resultado | Tests |
| --- | ---: |
| Pasan | 2.376 |
| Fallan | 0 |
| Omitidos | 12 |
| Fallo esperado (`xfail`) | 5 |
| Pasan pese a estar marcados como fallo esperado (`xpassed`) | 7 |
| No ejecutados por cuelgue del fichero | ~39 |

- El único fallo de la primera pasada fue `tests/test_cache_resilencia.py::TestSFTPRetry::test_sftp_importa_tenacity_cuando_disponible`, por faltar `tenacity` en el intérprete. Instalada la dependencia, el fichero pasa 14/14. **No hay ningún fallo de código en el baseline.**
- El fallo preexistente que documentaba el fichero de reglas de agentes (`test_info_algoritmos_muestra_solo_opciones_reales`) **pasa** al ejecutar su fichero aislado: era un efecto de contaminación entre tests, no un defecto del test.

### Ficheros que cuelgan y test exacto responsable

| Fichero | Test que bloquea | Colectados / ejecutados antes del cuelgue |
| --- | --- | --- |
| `tests/test_config_widgets_extra.py` | `TestSMTPConfigWidgetExtra::test_toggle_editable` (y la variante SFTP) | 14 / 4 |
| `tests/test_import_export_form.py` | `TestImportExportFormExportar::test_exportar_datos_error` | 17 / 7 |
| `tests/ui/test_ui_asignacion.py` | `TestAsignacionGeneracion::test_generar_con_mock_algoritmo_exitoso` | 11 / 8 |
| `tests/ui/test_ui_persistencia_campos.py` | `TestProfesorCamposHorarioPersis::test_horas_manana_persiste` | 24 / 8 |

Causa común: el código bajo prueba abre un diálogo modal y espera en `msg.exec()` sin que nadie responda. Verificado en `src/presentation/forms/config_widgets/smtp_widget.py:185-274`, cuyo `_toggle_editable()` llama a `_show_global_warning()` y éste termina en `return msg.exec() == QMessageBox.StandardButton.Yes`. Ninguno de estos tests puede pasar desatendido en ningún entorno.

Que el tercero sea justamente el test de generación de guardias refuerza QA-003: la suite cubre `AsignacionGuardiasForm`, formulario que la aplicación ya no registra, y encima lo hace de forma que bloquea la ejecución.

### Otras observaciones del baseline

- **7 `xpassed`** (6 en `tests/test_dialogs_basic.py`, 1 en `tests/test_gestor_ausencias.py`): marcas de fallo esperado obsoletas que ocultan comportamiento ya correcto. Deben retirarse; con `strict` activado serían fallos.
- **Caché de bytecode heredada:** `tests/__pycache__` conserva ficheros compilados desde una ubicación anterior del proyecto (una carpeta de OneDrive que ya no existe) y de una versión distinta de pytest (`...pytest-9.0.1.pyc` junto a `...pytest-8.4.2.pyc`). Conviene borrar `__pycache__` y añadirlo a la limpieza.
- **Dependencias ausentes en el intérprete** pese a estar declaradas: `tenacity`, `slowapi`, `fastapi`, `uvicorn`, `httpx`, `hypothesis`, `PyJWT`, `pytest-xdist`. Todas instaladas durante la auditoría para poder medir (QA-001).
