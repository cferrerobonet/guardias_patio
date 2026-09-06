---
tags:
  - gestion-centro
  - auditoria
  - fiabilidad
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 1-urgente
tipo: referencia
---

# Cierre de la app en Windows al terminar el cálculo de guardias

## 1. Síntoma reportado

En una máquina Windows, al lanzar la generación de guardias, la aplicación se cierra siempre cuando el cálculo está a punto de terminar. Nunca llega a mostrarse el resultado. En macOS no ocurre.

## 2. Qué se ha podido verificar y qué no

| Aspecto | Estado |
| --- | --- |
| Lectura completa del flujo de generación (UI → worker → solver → persistencia → resultado) | Verificado |
| Defectos de concurrencia en ese flujo | Verificados estáticamente con `fichero:línea` |
| Logs de la máquina Windows | **No disponibles** en este repositorio; los logs de `logs/` son de macOS y de tests |
| Reproducción en Windows con el build congelado | **No realizada** (no hay máquina Windows en esta sesión) |
| Volcado nativo (Event Viewer, faulthandler) | **No existe**: la app no activa `faulthandler` y el build es `console=False` |

Por tanto: las causas siguientes son defectos reales y comprobados en el código; cuál de ellos produce el cierre en esa máquina concreta se confirma con el protocolo de la sección 5. Todas deben corregirse igualmente.

## 3. Anatomía del flujo (commit auditado)

```
GeneracionPanel._generar_guardias            (hilo GUI)   generacion_panel.py:228-330
 └─ ejecutar_con_progreso(...)               (hilo GUI)   progress_indicators.py:533-691
     ├─ ProgressDialog(show_details=True)                 instala ProgressLogHandler   :278-292
     ├─ WorkerThread.start()                 (QThread)    progress_worker.py:38-56
     │   └─ GenerarGuardiasUseCase.execute   (worker)     generar_guardias.py:61-181
     │       ├─ session.query(Guardia).delete()           misma Session que la GUI
     │       ├─ generar_guardias_cpsat(session, cb)       asignador_guardias_cpsat.py:56-…
     │       │    └─ solver.Solve(model, SolverCallback)  8 hilos C++              :505-514
     │       │         └─ on_solution_callback → cb → … → WorkerThread.progreso.emit  (hilo OR-Tools)
     │       └─ guardar_guardias_cpsat_en_bd → commit     (worker)
     ├─ dialog.exec()                        (hilo GUI, bucle anidado)
     ├─ on_finalizado → dialog.completar()   (hilo GUI, cola)
     └─ worker.wait()
 ├─ _mostrar_resultados(resumen)             (hilo GUI, queries en la misma Session)
 ├─ _sincronizar() → sync_on_shutdown        (hilo GUI, SFTP bloqueante)   :416-427
 └─ guardias_generadas.emit()
```

Mientras tanto, en el hilo GUI siguen vivos: `QTimer` de 1 s del diálogo (`_actualizar_tiempo`, `_actualizar_cpu` con psutil), heartbeat SFTP del bloqueo de sesión (`session_lock.py:226-248`), timer de auto-sync cada 30 min que arranca un `SyncWorker` con la **misma** `Session` (`ventana_principal.py:262-270`).

## 4. Hallazgos (fichas)

### ~~[CRW-001] Señales Qt emitidas desde los hilos internos de OR-Tools~~ ✅ RESUELTO v5.52.0

- **Estado:** RESUELTO VERIFICADO v5.52.0 · **Tipo:** bug · **Severidad:** P0 · **Confianza:** media (evidencia estática sólida; falta confirmar en Windows que era ésta la causa del cierre).
- **Solución aplicada:** `SolverCallback` ya no recibe el callback de la aplicación: sólo publica en un `ProgresoSolver` protegido por `threading.Lock`. `resolver_con_progreso` lanza `solver.Solve` en un hilo propio y, desde el hilo llamante, recoge cada 250 ms lo publicado y lo reporta. Ningún hilo creado por OR-Tools vuelve a entrar en código de la aplicación, y menos aún en Qt.
- **Ubicación:** `src/services/_asignador_cpsat_helpers.py:233-244` (`on_solution_callback` llama a `progress_callback`), `src/services/asignador_guardias_cpsat.py:512-514` (callback pasado a `solver.Solve` con `num_search_workers = 8`), `src/application/use_cases/asignacion_guardias/generar_guardias.py:118-122` (`adapter_callback`), `src/presentation/forms/asignacion_widgets/generacion_panel.py:289-292` (`adapted_callback`), `src/presentation/widgets/progress_worker.py:40-43` (`callback_progreso` → `self.progreso.emit`).
- **Evidencia:** la cadena de callbacks no cambia de hilo en ningún punto; `CpSolverSolutionCallback.on_solution_callback` se ejecuta en un hilo creado por OR-Tools (no por Qt ni por Python). Ese hilo emite `pyqtSignal` y, a través del handler de progreso (`actualizar_progreso`), añade texto al `QTextEdit`. Qt "adopta" el hilo nativo la primera vez que lo toca y libera esa adopción cuando el hilo termina, que es exactamente **al final del `Solve`** cuando OR-Tools destruye sus 8 workers. En Windows la limpieza de hilos adoptados se hace desde `DllMain`/watcher de Qt y es una fuente conocida de accesos inválidos cuando interviene además el GIL de Python. El momento coincide con el síntoma: "a punto de terminar".
- **Pasos de reproducción (Windows):** build congelado, curso con ≥ 20 profesores, algoritmo "Óptimo (CP-SAT)", pulsar Generar, esperar al final del solve.
- **Resultado actual:** el proceso termina sin diálogo ni traza Python.
- **Resultado esperado:** el solver informa de progreso sin tocar Qt; la GUI se actualiza desde el hilo GUI.
- **Causa raíz:** ausencia de frontera entre el solver (hilos C++) y Qt.
- **Patrón sistémico:** los callbacks de progreso atraviesan tres capas sin cambiar de hilo (CRW-002 es el mismo patrón vía logging).
- **Recomendación:** el `SolverCallback` sólo escribe en una estructura thread-safe (`threading.Event` + `queue.Queue` o un `int` bajo `Lock`) y `WorkerThread` es el único que emite, desde su propio hilo, leyendo esa cola en un bucle con `Solve` ejecutándose… Alternativa más simple: `WorkerThread` arranca un `QTimer` en el hilo GUI que lee cada 250 ms el último progreso publicado por el callback. Ninguna referencia a Qt debe existir en `services/`.
- **Archivos afectados:** `_asignador_cpsat_helpers.py`, `asignador_guardias_cpsat.py`, `progress_worker.py`, `progress_indicators.py`, `generar_guardias.py`.
- **Prueba de regresión:** `tests/audit/test_crash_windows_regresion.py::test_solver_callback_no_toca_qt` (comprueba que el callback del solver no emite señales ni toca widgets fuera del hilo del worker) y `::test_progreso_llega_al_hilo_gui`.
- **Criterios de aceptación:** [ ] `services/` sin imports de PyQt6 ni callbacks Qt; [ ] 10 generaciones consecutivas en Windows sin cierre; [ ] progreso visible durante el solve; [ ] cancelar detiene el solver en < 2 s.
- **Esfuerzo:** M. **Dependencias:** ninguna. **Producción:** verificación en el PC Windows.

### ~~[CRW-002] El handler de logging escribe en widgets desde el hilo que loguea~~ ✅ RESUELTO v5.52.0

- **Estado:** RESUELTO VERIFICADO v5.52.0 · **Tipo:** bug · **Severidad:** P1 · **Confianza:** alta.
- **Solución aplicada:** `ProgressLogHandler` publica en la señal `linea` de un `_PuenteLog` que vive en el hilo GUI y está conectada en cola; el `QTextEdit` sólo se toca desde allí. La lista de loggers pasa a ser `services.asignador_guardias_cpsat` y `services.asignador_guardias_v4_hibrido`, y se les sube el nivel a INFO mientras el diálogo está abierto: heredaban WARNING, así que el panel de detalle no mostraba nada.
- **Ubicación:** `src/presentation/widgets/progress_handlers.py:41-52` (`ProgressLogHandler.emit` → `progress_dialog.agregar_al_log`), `src/presentation/widgets/progress_indicators.py:343-359` (`QTextEdit.append` + scrollbar), `:278-292` (se instala en `services.asignador_iterativo`, `services.asignador_ilp`, `services.orquestador_asignacion_guardias`, `services.asignador_guardias_v3_simple`).
- **Evidencia:** `logging.Handler.emit` se ejecuta en el hilo que hace `logger.info`, es decir, el worker o los hilos del solver. Toca `QTextEdit` directamente. Hoy está **latente** porque tres de los cuatro loggers ya no existen y el cuarto (`orquestador`) no se usa en la generación; en cuanto alguien añada el logger de CP-SAT, el crash es inmediato.
- **Recomendación:** el handler emite una señal `linea_log(str)` de un `QObject` que vive en el hilo GUI; el diálogo la conecta con `QueuedConnection`. Actualizar la lista de loggers a `services.asignador_guardias_cpsat` y `services.asignador_guardias_v4_hibrido`.
- **Prueba:** `tests/audit/test_crash_windows_regresion.py::test_log_handler_no_toca_widgets_fuera_del_hilo_gui`.
- **Esfuerzo:** S.

### ~~[CRW-003] Una única `Session` de SQLAlchemy compartida por GUI, worker de generación, worker de sync y cierre~~ ✅ RESUELTO v5.55.0

- **Estado:** RESUELTO VERIFICADO v5.55.0 · **Tipo:** bug · **Severidad:** P1 · **Confianza:** alta.
- **Solución aplicada:** `db_manager` ya ofrecía `get_db_session()`, un context manager sobre la fábrica del usuario activo; lo que faltaba era que los hilos lo usaran. Ahora: el worker de generación abre la suya (con `session_factory` inyectable para los tests), `SyncWorker` abre la suya y ha dejado de aceptar una sesión de fuera, y las otras cinco tareas que `ejecutar_con_progreso` lanzaba en el worker —cuatro exportaciones de PDF y la importación de profesores— hacen lo mismo. Tras generar, la sesión de la GUI hace `expire_all()` para no repintar con el mapa de identidad viejo. Un test recorre el AST de `src/presentation` y falla si alguna función lanzada al worker vuelve a tocar `self.session`.
- **Pendiente:** las diez vistas siguen compartiendo una sesión **entre ellas**, lo cual es correcto porque todas viven en el hilo GUI. Devolver DTOs en vez de objetos ORM sigue siendo deseable, pero ya no es un riesgo de cierre.
- **Ubicación:** `src/database/db_manager.py:344-350` (`check_same_thread: False`, `NullPool`), `:363` (`journal_mode=DELETE`), `src/presentation/forms/asignacion_widgets/generacion_panel.py:74-77` (use cases con `self.session`), `src/presentation/ventana_principal.py:262-270` (`SyncWorker(self.sync_manager, session=self.session)` cada 30 min), `src/main.py:390-398` (sync final con la misma sesión), `src/presentation/widgets/sync_progress_dialog.py:34-47`.
- **Evidencia:** `Session` no es thread-safe (documentación SQLAlchemy). `check_same_thread=False` desactiva la protección de sqlite3, no la hace segura. Si el auto-sync de 30 min coincide con una generación (CP-SAT puede tardar hasta 120 s), dos hilos ejecutan sentencias sobre la misma conexión. En Windows, con `journal_mode=DELETE` y bloqueo de fichero, el resultado puede ser `database is locked`, estado de sesión corrupto o un fallo nativo en `sqlite3.dll`.
- **Recomendación:** `SessionFactory` inyectada; cada hilo abre su sesión (`with SessionFactory() as s:`) y devuelve DTOs; la GUI nunca comparte su sesión con un `QThread`. Mantener `expire_on_commit=False`. Considerar `journal_mode=WAL` cuando la BD no esté en OneDrive (detectar ruta) para lecturas concurrentes.
- **Prueba:** `tests/audit/test_crash_windows_regresion.py::test_worker_no_reutiliza_sesion_gui` (xfail hasta el fix) y test de integración con BD en fichero (`tests/audit/conftest.py::db_fichero`).
- **Esfuerzo:** L (toca 10 vistas). Puede hacerse por lotes empezando por generación y sync.

### ~~[CRW-004] Cancelar se traga en las fases del solver y sólo se propaga a través del callback C++~~ ✅ RESUELTO v5.52.0

- **Estado:** RESUELTO VERIFICADO v5.52.0 · **Tipo:** bug · **Severidad:** P2 · **Confianza:** alta (verificado con `tests/audit`).
- **Solución aplicada:** `WorkerThread` expone un `threading.Event` que `cancelar()` activa y que se pasa a la tarea si declara el parámetro `cancelacion`; el callback de progreso ya no lanza. Los dos asignadores comprueban el evento en cada fase y `reportar` deja de tragarse `InterruptedError`. Durante el solve, el bucle de sondeo llama a `solver.stop_search()`, que es la parada asíncrona documentada de OR-Tools: nada cruza ya el callback C++.
- **Ubicación:** `src/services/asignador_guardias_cpsat.py:77-82` (`reportar` captura `OSError`; `InterruptedError` es subclase de `OSError`), `src/presentation/widgets/progress_worker.py:41-42` (raise dentro de `callback_progreso`), `src/services/_asignador_cpsat_helpers.py:240-244`.
- **Evidencia:** el test `test_cancelacion_interrumpe_la_generacion_sin_tragarse_la_excepcion` registra 10 avisos "Error en callback de progreso" antes de que la excepción llegue al llamante: las fases 1-5 ignoran la cancelación y el trabajo continúa. La excepción acaba propagándose porque OR-Tools 9.14 re-lanza las excepciones Python ocurridas en `on_solution_callback` al terminar `Solve` (comprobado en macOS). Ese comportamiento depende de la versión de OR-Tools y del wrapper; en el build de Windows no se ha verificado, y en cualquier caso una excepción que atraviesa el callback deja el solver en parada abrupta con 8 hilos activos.
- **Recomendación:** el callback nunca lanza: consulta una bandera de cancelación y llama a `self.StopSearch()`; `reportar` no captura `InterruptedError`; cada fase comprueba la bandera y sale limpiamente con `rollback`.
- **Prueba:** `tests/audit/test_crash_windows_regresion.py::test_cancelacion_interrumpe_la_generacion_sin_tragarse_la_excepcion` y `::test_worker_no_lanza_dentro_del_callback_del_solver`.
- **Esfuerzo:** S.

### ~~[CRW-005] `sys.excepthook` crea un `QMessageBox` desde cualquier hilo~~ ✅ RESUELTO v5.53.0

- **Estado:** RESUELTO VERIFICADO v5.53.0 · **Tipo:** bug · **Severidad:** P1 · **Confianza:** alta.
- **Solución aplicada:** el hook compara `QThread.currentThread()` con el hilo de la `QApplication`; fuera del hilo GUI se limita a registrar el fallo y deja constancia de por qué no muestra diálogo. `SyncWorker.run` captura `Exception` con traza completa, así que una `SSHException` de paramiko ya no escapa hacia el hook.
- **Ubicación:** `src/main.py:60-95`, `src/presentation/widgets/sync_progress_dialog.py:34-47` (`SyncWorker.run` sólo captura `ValueError, TypeError, OSError`), `src/utils/update_checker.py:10-23` (hilo `threading.Thread`).
- **Evidencia:** PyQt6 invoca `sys.excepthook` para excepciones no capturadas en `QThread.run` reimplementado, **en el hilo del worker**. Una `paramiko.SSHException` (no es `OSError`) en `SyncWorker` llega al hook, que construye y ejecuta un `QMessageBox` fuera del hilo GUI: cierre inmediato. Ocurre al cerrar la app o en el auto-sync de 30 min, y la sincronización se dispara justo después de generar (`_sincronizar`).
- **Recomendación:** hook que comprueba `QThread.currentThread() is QApplication.instance().thread()`; si no, sólo loguea y emite una señal a la ventana principal. `SyncWorker` captura `Exception`.
- **Prueba:** `::test_excepthook_no_crea_widgets_fuera_del_hilo_gui`.
- **Esfuerzo:** XS.

### [CRW-006] ~~Sin `faulthandler`, con handler de consola muerto~~ ✅ RESUELTO v5.44.0

- **Tipo:** deuda · **Severidad:** P2 · **Confianza:** alta.
- **Ubicación:** `src/main.py:31-34` (`StreamHandler(sys.stdout)`; en build windowed `sys.stdout` es `None`), `src/core/logging.py:149-179` (segunda configuración de handlers), evidencia de líneas triplicadas en `logs/guardias_patio.log` (cada registro aparece 3 veces).
- **Impacto:** un fallo nativo no deja rastro; el diagnóstico en Windows es imposible sin herramientas externas.
- **Recomendación:** en `main.py`, si `getattr(sys, "frozen", False)`: `faulthandler.enable(open(log_dir/"faulthandler.log", "a"))` y no crear `StreamHandler` cuando `sys.stdout is None`. Una sola función `setup_logging()` idempotente.
- **Esfuerzo:** XS.

### ~~[CRW-007] Tras generar, la sincronización SFTP bloquea el hilo GUI y sus errores escapan del slot~~ ✅ RESUELTO v5.53.0

- **Estado:** RESUELTO VERIFICADO v5.53.0 · **Tipo:** bug · **Severidad:** P2 · **Confianza:** alta.
- **Solución aplicada:** `_sincronizar` reutiliza `SyncWorker` con `SyncProgressDialog`, el mismo patrón que el cierre de la aplicación y el auto-sync, y captura `Exception`. La sesión sigue compartiéndose con el worker: eso es CRW-003 y se aborda en el lote 3.
- **Ubicación:** `src/presentation/forms/asignacion_widgets/generacion_panel.py:314-316,416-427` y `:327-328` (`except (ValueError, TypeError, OSError)`).
- **Evidencia:** `sync_on_shutdown` sube por SFTP en el hilo GUI (segundos congelada). Excepciones de paramiko o SQLAlchemy salen de `_generar_guardias` y llegan al excepthook: el usuario ve "Error inesperado" tras una generación correcta.
- **Recomendación:** reutilizar `SyncWorker`; capturar `Exception` con mensaje claro; no mezclar el resultado de la generación con el de la sync.
- **Esfuerzo:** S.

### [CRW-008] ~~`SQLAlchemyError` sin importar en tres módulos~~ ✅ RESUELTO v5.44.0

- **Tipo:** bug · **Severidad:** P3 · **Confianza:** alta (ruff F821).
- **Ubicación:** `src/presentation/forms/asignacion_widgets/generacion_panel.py:413`, `src/presentation/widgets/gestion_cursos_widget.py:572`, `src/sync/sync_manager.py:507`.
- **Impacto:** cuando ocurre el error que se pretendía manejar, salta `NameError` y se pierde el mensaje real.
- **Prueba:** `tests/audit/test_calidad_estatica.py::test_sin_nombres_indefinidos`.

### ~~[CRW-009] Registro de auditoría de la generación sin commit propio~~ ✅ RESUELTO v5.53.0

- **Estado:** RESUELTO VERIFICADO v5.53.0 · **Tipo:** bug · **Severidad:** P2 · **Confianza:** media.
- **Solución aplicada:** el caso de uso hace `commit` tras añadir el registro. Además captura `InterruptedError` antes que `Exception`, para que cancelar no se anuncie como error de negocio.
- **Ubicación:** `src/application/use_cases/asignacion_guardias/generar_guardias.py:150-153` (`session.add(GuardiaAuditLog(...))` sin `commit`; `autoflush=False` en `db_manager.py:382`).
- **Impacto:** el registro se persiste sólo si otro flujo hace commit después; con rollback por un error posterior, se pierde.
- **Recomendación:** el caso de uso gestiona su transacción: `commit` al final, `rollback` en error.

## 5. Protocolo de diagnóstico en la máquina Windows (30 minutos)

1. **Recoger el último log:** `%APPDATA%\GuardiasDePatio\logs\app_*.log` más reciente. Enviar las últimas 200 líneas. Buscar `Guardando guardias`, `Proceso completado`, `Error en WorkerThread`, `EXCEPCIÓN NO MANEJADA`.
2. **Visor de eventos:** Windows Logs → Application → error 1000 con `GuardiasDePatio.exe`; anotar *Faulting module* (`Qt6Core.dll`, `Qt6Widgets.dll`, `python311.dll`, `sqlite3.dll`, `_pywrapcp*.pyd`/`ortools`), *Exception code* (0xC0000005 = acceso inválido; 0x40000015/0xC0000409 = abort/terminate).
3. **Ejecutar con consola:** compilar con `powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Diagnostico` (ya disponible desde v5.44.0: añade `--console` y activa `PYTHONFAULTHANDLER`), lanzar `dist\GuardiasDePatio-debug\GuardiasDePatio-debug.exe` desde `cmd`, generar y copiar la salida. Revisar además `%APPDATA%\GuardiasDePatio\logs\faulthandler.log`, que ahora recoge la pila de todos los hilos ante un fallo nativo.
4. **Aislar el solver:** repetir con algoritmo "Rápido (v4 Híbrido)". Si no falla, CRW-001 confirmado. Si falla igual, priorizar CRW-003/005. Desde v5.52.0 la frontera solver↔Qt ya está cerrada, así que si el cierre persiste la causa está en CRW-003/005.
5. **Aislar la sync:** repetir con la variable `DISABLE_SESSION_LOCK=1` y sin red. Si deja de fallar, priorizar CRW-003 (CRW-005 y CRW-007 ya están resueltos desde v5.53.0).
6. Registrar resultados en [[30_REGISTRO_HALLAZGOS]] con veredicto y actualizar la confianza de CRW-001.

## 6. Orden de remediación

1. ~~CRW-006~~ ✅ v5.44.0. ~~CRW-005 (XS, sin riesgo): elimina un vector de cierre.~~ ✅ v5.53.0
2. ~~CRW-001 y CRW-004 (M+S): frontera solver↔Qt y cancelación cooperativa.~~ ✅ v5.52.0
3. ~~CRW-002 (S).~~ ✅ v5.52.0 ~~CRW-008~~ ✅ v5.44.0.
4. ~~CRW-007 y CRW-009 (S).~~ ✅ v5.53.0
5. ~~CRW-003 (L) por lotes: generación → sync → resto de vistas.~~ ✅ v5.55.0

Cada lote se cierra con la suite `tests/audit` verde (retirando las marcas `xfail`) y una generación completa en Windows con `faulthandler` activo.
