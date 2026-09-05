---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-05
estado: activo
prioridad: 1-urgente
tipo: referencia
---

# Registro canónico de hallazgos

> [!NOTE] Reglas
> Fuente única del estado. Un hallazgo por fila; la ficha completa vive en el documento indicado en *Ficha*. Al resolver: cambiar *Estado* a `RESUELTO VERIFICADO vX.Y.Z`, citar el test de regresión y tachar el ítem en el plan. Los recuentos de [[00_INDICE]] se derivan de esta tabla.

Leyenda de estado: `NUEVO` · `PERSISTE` · `RESUELTO VERIFICADO` · `REGRESIÓN` · `RIESGO ACEPTADO` · `BY DESIGN` · `NO VERIFICADO` · `DESCARTADO`. Confianza: alta / media / baja.

## CRW · Cierre en Windows, hilos y sesión

| ID | Sev. | Conf. | Título | Ubicación | Estado | Ficha |
| --- | --- | --- | --- | --- | --- | --- |
| CRW-001 | P0 | media | ~~Señales Qt emitidas desde hilos internos de OR-Tools durante el solve~~ | `_asignador_cpsat_helpers.py`, `asignador_guardias_cpsat.py` | **RESUELTO VERIFICADO v5.52.0** · `SolverCallback` sólo publica en `ProgresoSolver`; `resolver_con_progreso` sondea desde el hilo llamante · `test_callbacks_del_solver_no_salen_del_hilo_llamante`, `test_progreso_publicado_por_el_solver_lo_reporta_el_hilo_llamante`. Falta confirmar en Windows que era ésta la causa del cierre | [[06_CRASH_WINDOWS_GENERACION]] |
| CRW-002 | P1 | alta | ~~Handler de logging modifica widgets desde el hilo que loguea; loggers obsoletos~~ | `progress_handlers.py`, `progress_indicators.py` | **RESUELTO VERIFICADO v5.52.0** · el handler emite por señal en cola y se instala en los loggers vivos, subiéndoles el nivel para que el detalle se vea · `test_log_handler_no_toca_widgets_fuera_del_hilo_gui`, `test_log_handler_captura_los_loggers_de_los_algoritmos_actuales` | 06 |
| CRW-003 | P1 | alta | ~~Session SQLAlchemy compartida entre GUI, worker, sync y cierre~~ | `generacion_panel.py`, `sync_progress_dialog.py`, `reportes_form.py`, `import_export_form.py` | **RESUELTO VERIFICADO v5.55.0** · cada hilo abre su sesión con `get_db_session()`; `SyncWorker` ya no acepta una sesión de fuera; los seis cierres que `ejecutar_con_progreso` lanzaba en el worker (generación, 4 exportaciones de PDF, importación) usan la suya. Guardarraíl estático con AST para que no vuelva a colarse · `test_worker_no_reutiliza_sesion_gui`, `test_ninguna_tarea_en_hilo_usa_la_sesion_de_la_gui`, `test_dos_sesiones_sobre_la_misma_bd_en_fichero` | 06 |
| CRW-004 | P2 | alta | ~~Cancelar se ignora en las fases del solver (10 avisos) y sólo se propaga vía callback C++~~ | `asignador_guardias_cpsat.py`, `asignador_guardias_v4_hibrido.py`, `progress_worker.py` | **RESUELTO VERIFICADO v5.52.0** · cancelación por evento cooperativo hasta `stop_search()`; `reportar` ya no se traga `InterruptedError` · `test_cancelacion_interrumpe_la_generacion_sin_tragarse_la_excepcion`, `test_resolver_con_progreso_para_el_solver_al_cancelar`, `test_worker_no_lanza_dentro_del_callback_del_solver` | 06 |
| CRW-005 | P1 | alta | ~~`sys.excepthook` crea QMessageBox desde cualquier hilo; SyncWorker captura poco~~ | `main.py`, `sync_progress_dialog.py` | **RESUELTO VERIFICADO v5.53.0** · el hook compara el hilo actual con el de la QApplication antes de crear widgets; `SyncWorker` captura `Exception` · `test_excepthook_comprueba_el_hilo_antes_de_crear_widgets`, `test_syncworker_captura_cualquier_excepcion` | 06 |
| CRW-006 | P2 | alta | ~~Sin faulthandler; StreamHandler muerto en windowed~~ | `main.py:31-46` | **RESUELTO VERIFICADO v5.44.0** · `tests/audit/test_crash_windows_regresion.py::test_main_activa_faulthandler`. Queda pendiente el logging duplicado (COD-005) | 06 |
| CRW-007 | P2 | alta | ~~Sync SFTP en el hilo GUI tras generar; excepciones escapan del slot~~ | `generacion_panel.py` | **RESUELTO VERIFICADO v5.53.0** · `_sincronizar` usa `SyncWorker` + `SyncProgressDialog` y captura `Exception` · `test_sincronizar_del_panel_no_bloquea_el_hilo_gui` | 06 |
| CRW-008 | P3 | alta | ~~`SQLAlchemyError` sin importar en tres módulos y `Container` sin declarar~~ | `generacion_panel.py`, `gestion_cursos_widget.py`, `sync_manager.py`, `wiring.py` | **RESUELTO VERIFICADO v5.44.0** · `tests/audit/test_calidad_estatica.py::test_sin_nombres_indefinidos` | 06 |
| CRW-009 | P2 | media | ~~Audit log de generación sin commit propio~~ | `generar_guardias.py` | **RESUELTO VERIFICADO v5.53.0** · commit propio tras añadir el registro; `InterruptedError` se deja pasar antes que `Exception` · `test_generar_guardias_hace_commit_del_audit_log`, `test_generar_guardias_deja_pasar_la_cancelacion` | 06 |

## UXA · Accesibilidad y UX (Ola 4, 2026-08-04, reconciliados en este commit)

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| UXA-001 | P1 | alta | Ventana y diálogos no caben en pantallas/escalados habituales | **PARCIAL v5.60.0** · mínimo único de ventana 1024×700 (v5.58.0) y el calendario deja de exigir 1400×900 al abrirse. No queda ningún tamaño fijo por encima de 1024×700. Falta comprobarlo en una pantalla pequeña real y revisar el escalado al 125% | `_work/paquete_ux_accesibilidad.md` |
| UXA-002 | P1 | alta | ~~Sin foco visible consistente~~ | **RESUELTO VERIFICADO v5.60.0** · anillo de foco de 2 px en color primario para todo control enfocable —botones, casillas, fechas, tablas, listas—, con variante clara en el menú lateral oscuro · `test_la_hoja_de_estilos_marca_el_foco_en_todo_control` | ídem |
| UXA-003 | P1 | alta | Toasts no anunciables ni persistentes | PERSISTE | ídem |
| UXA-004 | P1 | alta | ~~Contrato de cambios sin guardar no conectado~~ | **RESUELTO VERIFICADO v5.59.0** · `BaseForm.vigilar_cambios()` conecta las señales de edición de los diez tipos de campo; `cargando()` evita que rellenar por código cuente como edición; guard central único en la ventana (navegación, cierre y cambio de curso) con Guardar / Descartar / Seguir editando. Conectado en Profesor, Zona y Ajustes, que además unifica su mecanismo paralelo · `tests/audit/test_cambios_sin_guardar.py` (16 tests) | ídem |
| UXA-005 | P1 | alta | ~~Campos sin nombre/relación accesible~~ | **RESUELTO VERIFICADO v5.60.0** · `asignar_nombres_accesibles()` deduce el nombre de la etiqueta del formulario, del marcador de posición, del propio control o del recuadro que lo contiene. De 76 controles sin nombre sobre 119 (63%) a **0 en Profesores, Zonas y Ajustes**. Las 20 casillas de la matriz de restricciones pasan a llamarse «Recreo N del lunes», con su estado · `test_ningun_control_se_queda_sin_nombre_accesible` | ídem |
| UXA-006 | P1 | alta | ~~Validaciones no identifican el campo~~ | **RESUELTO VERIFICADO v5.60.0** (en Zonas) · `marcar_error_en_campo()` marca el control en rojo, le pone el motivo como descripción accesible y le lleva el foco tras cerrar el aviso; `limpiar_errores()` lo deshace al reintentar. Profesores y Ajustes usan validadores propios que aún no dicen qué campo falla · `test_un_error_de_validacion_marca_el_campo_y_le_lleva_el_foco` | ídem |
| UXA-007 | P1 | alta | Cambio de curso no refresca vistas (`ContentWrapper` sin `content_widget`) | **RESUELTO VERIFICADO v5.49.0** · `ContentWrapper` conserva la vista y el refresco por cambio de curso funciona | ídem |
| UXA-008 | P2 | alta | Tablas sin contrato accesible/adaptable | **PARCIAL v5.60.0** · las tablas de Profesores y Zonas tienen nombre y descripción accesibles, y hay regla de foco para tablas y celdas. Falta el contrato completo (QTableView + modelo, cabecera ordenable, estados vacío y de carga), que es el lote 12 · `test_las_tablas_principales_se_presentan` | ídem |
| UXA-009 | P2 | alta | Gráficos QPainter sin semántica | PERSISTE | ídem |
| UXA-010 | P2 | alta | Sistema visual fragmentado y contrastes AA fallidos | **PARCIAL v5.58.0** · el primario pasa de 4,51:1 a 6,52:1 y su variante oscura a 7,98:1; los verdes de acento a 5,1:1 y 7,2:1. Falta auditar el resto de combinaciones y el anillo de foco (lote 11) | ídem |
| UXA-011 | P2 | media | Cargas de tablas bloquean el hilo GUI | **DESCARTADO v5.66.0** · mismo motivo que ESC-001: la carga más pesada medida es de 17 ms, por debajo del umbral de percepción. Cargar en segundo plano añadiría complejidad de hilos —justo lo que costó los lotes 1 a 3— sin beneficio | ídem |
| UXA-012 | P2 | alta | ~~Suite a11y con skips amplios~~ | **RESUELTO VERIFICADO v5.60.0** · retirado el `except Exception: pytest.skip` de `test_a11y_regression.py`, que tapaba una expectativa desactualizada. Nueva suite `tests/audit/test_accesibilidad_formularios.py` con 11 tests de introspección por `accessibleName` | ídem |
| UXA-013 | P2 | alta | Navegación sin título/estado accesible | PERSISTE | ídem |
| UXA-014 | P3 | alta | Anti-patrones y tipografía microscópica | PERSISTE (VIS-003) | ídem |

## UXF · Flujo, guardarraíles y clics

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| UXF-001 | P1 | alta | Sin secuencia guiada ni panel de estado; la app abre en Profesores | **PARCIAL v5.57.0 · el panel de estado queda DESCARTADO por decisión de producto (CarlosFB, 2026-09-05).** Se construyó en v5.56.0 y se retiró: sólo tenía algo que decir en septiembre, al montar el curso, y el resto del año era una pantalla de paso. La guía de qué falta y cómo resolverlo vive donde surge la pregunta: el aviso visible del panel de generación, alimentado por `PreflightGeneracionUseCase`, que enumera los cinco requisitos con su detalle. La app vuelve a abrir en Profesores · `test_el_aviso_de_bloqueo_enumera_todo_lo_que_falta` | [[03_UX_CASOS_DE_USO_Y_CAMINOS_DORADOS]] |
| UXF-002 | P1 | alta | ~~Guardarraíl "cuotas antes de generar" es un flag de UI~~ | **RESUELTO VERIFICADO v5.56.0** · `PreflightGeneracionUseCase` comprueba curso activo, fechas, recreos, zonas y profesores contra los datos; la interfaz ya no puede conceder el permiso por su cuenta y el estado se reevalúa al cambiar de curso o de vista · `test_la_interfaz_no_puede_conceder_permiso_para_generar` | 03 |
| UXF-003 | P2 | alta | Generar requiere 2 modales previos y clic de cierre | NUEVO | 03 |
| UXF-004 | P2 | alta | ~~Cambio de curso: confirmación + toast sin refresco~~ | **RESUELTO VERIFICADO v5.59.0** · el refresco funciona desde v5.49.0, el panel de generación revalida sus prerrequisitos desde v5.56.0 y ahora, si hay cambios pendientes, se avisa y se ofrece guardarlos antes de descartarlos: pertenecen al curso anterior · `test_cambiar_de_curso_avisa_antes_de_descartar` | 03 |
| UXF-005 | P2 | alta | ~~Primer arranque exige SFTP; sin modo local~~ | **RESUELTO VERIFICADO v5.56.0** · cancelar la configuración inicial ofrece «Trabajar solo en este equipo» en vez de cerrar la aplicación, enumerando lo que se pierde; el indicador del menú lateral muestra «⚠ Solo en este equipo» de forma permanente · `test_sin_servidor_se_ofrece_el_modo_local_en_vez_de_cerrar` | 03 |
| UXF-006 | P2 | alta | Limpiar guardias con la misma prominencia que Generar | NUEVO | 03 |
| UXF-007 | P2 | alta | Sin protección de cambios sin guardar | DUPLICADO → UXA-004 | 03 |
| UXF-008 | P3 | alta | ~~Motivo de bloqueo sólo en tooltip~~ | **RESUELTO VERIFICADO v5.56.0** · el panel de generación pinta una etiqueta visible con los requisitos que faltan y su detalle · `test_motivo_de_bloqueo_visible_sin_hover` | 03 |
| UXF-009 | P2 | media | Ausencias sin deshacer ni vista previa | NUEVO | 03 |
| UXF-010 | P2 | alta | Cinco exportaciones PDF con diálogo cada una y sin recordar carpeta | NUEVO | 03 |
| UXF-011 | P3 | alta | Atajos de teclado casi inexistentes | NUEVO | 03 |

## VIS · Consistencia visual

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| VIS-001 | P2 | alta | Cuatro capas de estilo + 288 inline | **PARCIAL v5.58.0** · `light.qss` deja de llevar colores escritos a mano: usa marcadores `@TOKEN@` que `hoja_de_estilos.construir_hoja_de_estilos()` resuelve desde `tokens.Colors`, con test que impide volver a escribir un color que ya tiene token. Desde v5.65.0: las hojas repetidas literalmente pasan a reglas semánticas (`#tituloDialogo`, `[caja="aviso"]`, `[caja="info"]`, `#botonDialogo`) y **la hoja se aplica antes de mostrar el primer diálogo** — el de configuración inicial se abría sin estilos porque se aplicaba más abajo. Estilos en línea: 288 → 260; colores sueltos: 526 → 471. **Quedan 260, casi todos únicos por widget**: sacarlos exige mirar cada vista · `test_la_hoja_de_estilos_no_repite_colores_que_ya_son_token` | [[04_INVENTARIO_SUPERFICIES_E_INCONSISTENCIAS_VISUALES]] |
| VIS-002 | P2 | alta | ~~Dos identidades cromáticas (tokens vs Tailwind)~~ | **RESUELTO VERIFICADO v5.58.0** · una sola paleta: primario `#0E5FA8` (6,5:1 sobre blanco, frente al 4,51:1 justo del anterior), y los azules y verdes de Tailwind sustituidos por los tokens en 28 ficheros · `test_tokens_no_definen_dos_primarios_distintos` ya no es xfail | 04 |
| VIS-003 | P2 | alta | ~~Fuente `-apple-system` inexistente en Windows; usos < 12 px~~ | **RESUELTO VERIFICADO v5.58.0** · pila tipográfica por sistema (Segoe UI / SF Pro Text / Cantarell) con cuerpo base propio de cada uno, en la aplicación y en la hoja de estilos; los 89 tamaños por debajo de 12 px suben al mínimo del contrato · ratchet `font_size_menor_12px` a 0 | 04 |
| VIS-004 | P3 | alta | Emojis como iconos (327 líneas) | NUEVO | 04 |
| VIS-005 | P2 | alta | Terminal retro para resultados | NUEVO | 04 |
| VIS-006 | P2 | alta | Títulos inconsistentes; título registrado no se pinta | NUEVO | 04 |
| VIS-007 | P2 | alta | Botones sin jerarquía | NUEVO | 04 |
| VIS-008 | P3 | alta | Tres lenguajes de feedback | NUEVO | 04 |
| VIS-009 | P2 | alta | ~~Mínimo 1400×900 vs settings 1200×800~~ | **RESUELTO VERIFICADO v5.58.0** · un único mínimo, 1024×700, leído de `settings`. Pendiente de comprobar en una pantalla pequeña real: el entorno de pruebas sin pantalla recorta el tamaño de ventana y no permite verificarlo · `test_un_unico_minimo_de_ventana` | 04 |
| VIS-010 | P3 | alta | Identidad "ccleaner" y branding EPLA inconsistentes | NUEVO | 04 |

## BLD · Build y release

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| BLD-001 | P1 | alta | `.spec` ignorados por git y borrados por `make clean` | **RESUELTO VERIFICADO v5.50.0** · los `.spec` se versionan y `make clean` ya no los borra | [[09_BUILD_Y_RELEASE]] |
| BLD-002 | P1 | alta | Tres scripts Windows divergentes; Makefile/README apuntan a los obsoletos | **RESUELTO VERIFICADO v5.50.0** · eliminados los cuatro scripts obsoletos; queda `scripts/build_windows.ps1` como único de Windows | 09 |
| BLD-003 | P2 | alta | Cuatro versiones distintas en el repo | **RESUELTO VERIFICADO v5.50.0** · `pyproject.toml` sincronizado y test que lo vigila | 09 |
| BLD-004 | P2 | alta | Sin CI, sin firma/notarización | **PARCIAL v5.62.0** · el flujo de compilación existe desde v5.50.0. `build_dmg.sh` firma ahora con Developer ID y notariza **si se definen las variables** (`APPLE_DEVELOPER_ID`, `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_PASSWORD`); sin ellas sigue en ad-hoc y avisa por pantalla de que macOS pedirá «Abrir de todos modos». **No se puede completar hasta reactivar la cuenta de Apple Developer** (decisión de CarlosFB, 2026-09-05) | 09 |
| BLD-005 | P2 | alta | Actualizador sólo `.dmg`; Windows sin actualizaciones | **RESUELTO VERIFICADO v5.50.0** · el actualizador elige el instalador de su sistema, así que Windows ya recibe actualizaciones | 09 |
| BLD-006 | P3 | alta | ~~Instalador con admin y sin cierre de instancias~~ | **RESUELTO v5.62.0** · `PrivilegesRequired=lowest` con `PrivilegesRequiredOverridesAllowed=dialog`: en un centro lo normal es no tener permisos de administrador, y exigirlos impedía instalar. `CloseApplications=yes` cierra la aplicación abierta en vez de fallar al copiar. **Sin probar en Windows real** · `test_el_instalador_no_exige_administrador` | 09 |
| BLD-007 | P2 | alta | ~~Sin build de diagnóstico con consola~~ | **RESUELTO VERIFICADO v5.44.0** · `scripts/build_windows.ps1 -Diagnostico` | 09 |

## QA · Tests

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P1 | alta | ~~Entorno de tests no reproducible; errores de colección~~ | **RESUELTO PARCIAL v5.54.0** · `make venv` crea el entorno en `~/.venvs/guardias-patio` y todos los objetivos del Makefile lo usan; `tests/conftest.py` fija `GUARDIAS_API_SECRET_KEY` antes de importar nada, así que ya no hay errores de colección sin variables de entorno. Falta separar dependencias de ejecución y de desarrollo en dos ficheros (hoy `requirements.txt` las mezcla): va con el lote de build/CI | [[08_ESTRATEGIA_DE_TESTS]] |
| QA-002 | P2 | alta | ~~`pytest.ini` con cov obligatorio y `timeout` sin plugin~~ | **RESUELTO VERIFICADO v5.54.0** · la cobertura sale de `addopts` y pasa a `make coverage`; `pytest-timeout` está instalado y documentado; `xfail_strict = true` | 08 |
| QA-003 | P2 | alta | ~~Tests del formulario muerto `AsignacionGuardiasForm`~~ | **RESUELTO VERIFICADO v5.54.0** · `tests/ui/test_ui_asignacion.py` reescrito contra `AsignacionCalculoForm` y sus dos paneles (11 tests, con el guardarraíl de cuotas cubierto); borrado `tests/test_asignacion_guardias_form.py` (561 líneas sobre un formulario que ninguna vista registra). El formulario en sí sigue en pie: su borrado es COD-004 | 08 |
| QA-004 | P2 | alta | Sin tests de hilos/cancelación/excepthook | NUEVO (tests creados, xfail) | 08 |
| QA-005 | P2 | alta | ~~Fallo preexistente tolerado~~; skips amplios en a11y | **RESUELTO PARCIAL v5.54.0** · `test_swagger_ui_renderiza` fallaba porque `text=/api/v1/guardias` lo interpretaba Playwright como expresión regular: ahora localiza por `data-path`. `test_redoc_renderiza` espera al render en vez de fiarse de `networkidle`. **La suite completa pasa sin un solo fallo.** Los skips amplios de a11y siguen (UXA-012) | 08 |
| QA-006 | P3 | alta | Nada sobre SQLite en fichero ni migraciones reales | NUEVO (fixture creada) | 08 |
| QA-007 | P3 | alta | Sin E2E web | NUEVO (suite creada) | 08 |
| QA-008 | P1 | alta | ~~Cuatro tests bloquean la suite indefinidamente al abrir un diálogo modal~~ | **RESUELTO VERIFICADO v5.44.0** · guarda `dialogos_modales` en `tests/conftest.py` + dos tests de importación corregidos. La suite completa pasa de una sola pasada en 47 s | 08 |
| QA-009 | P3 | alta | ~~7 tests `xfail` que dependían del orden de ejecución~~ | **RESUELTO VERIFICADO v5.54.0** · causas reales encontradas: (1) `test_orquestador_asignacion_guardias.py` inyecta módulos falsos en `sys.modules` bajo `src.services.*` y el diálogo de diagnóstico importaba justo de ahí — corregido el prefijo a `services.*`; (2) `get_logger` devuelve structlog o el logging estándar según la configuración vigente en el primer import, así que `caplog` no podía capturar por nombre — el test espía ahora el logger del módulo. Marcas retiradas y `xfail_strict = true` para que no se acumulen | 08 |
| QA-010 | P3 | alta | ~~`tests/__pycache__` con bytecode de otra ubicación y otra versión de pytest~~ | **RESUELTO VERIFICADO v5.54.0** · 52 carpetas `__pycache__` borradas y `make clean` las limpia junto con `.pytest_cache`, `.ruff_cache` y los informes de cobertura | 08 |
| QA-011 | P2 | alta | ~~Tests intermitentes en `TestListarProfesoresUseCase`~~: causa identificada, la caché global se comparte entre tests por colisión de claves (ESC-007) | **RESUELTO VERIFICADO v5.45.0** · fixture `_cache_limpio` en `tests/conftest.py` | 08 |
| QA-012 | P1 | alta | El entorno virtual del repositorio estaba inservible y desalineado con `requirements.txt` | **RESUELTO PARCIAL v5.45.0, REABIERTO Y SUPERADO POR QA-013**: repararlo en su sitio no bastaba, porque el sitio es el problema | 08 |
| QA-013 | P1 | alta | **Un entorno virtual no puede vivir dentro de iCloud Drive.** El proyecto está en una carpeta sincronizada e iCloud creó 402 archivos duplicados (`… 2.dylib`, `… 2.so`) dentro de `.venv`, incluidos los complementos de Qt. Qt inspeccionaba la carpeta, no reconocía ningún complemento válido y abortaba el proceso en `QGuiApplicationPrivate::createPlatformIntegration()` al crear la `QApplication`: la app se cerraba nada más arrancar desde VS Code. Es el mismo motivo por el que `build_dmg.sh` ya tenía que copiar el bundle fuera de iCloud para firmarlo | **RESUELTO VERIFICADO v5.45.1** · entorno en `~/.venvs/guardias-patio`, fuera de iCloud; interfaz real y suite completa verificadas | 08 |

## SYNC · Sincronización en la nube

| ID | Sev. | Conf. | Título | Ubicación | Estado | Ficha |
| --- | --- | --- | --- | --- | --- | --- |
| SYNC-001 | P0 | alta | La app cae a modo local en silencio si el servidor no está bien configurado o no responde: guarda, sincroniza y cierra sin un solo aviso, y los datos nunca salen del equipo | `sync/backend_factory.py:64-82` | **RESUELTO VERIFICADO v5.47.0** · `get_default_backend()` lanza `SyncConfigurationError`; la app avisa de que no habrá nube y no finge | [[12_SINCRONIZACION_NUBE]] |
| SYNC-002 | P1 | alta | La configuración se da por válida sin probar la conexión: solo comprueba que los campos no estén vacíos | `config/sftp_config.py:50-62`, `dialogs/initial_config_dialog.py:641-665` | NUEVO | 12 |
| SYNC-003 | P1 | alta | Si la descarga inicial falla, solo se escribe en el registro y se trabaja sobre datos viejos | `main.py:309-312` | **RESUELTO VERIFICADO v5.47.0** · aviso visible y sesión sin permiso de subida | 12 |
| SYNC-004 | P1 | alta | Si la subida final falla, no hay reintento ni marca de pendiente: la app ya se está cerrando | `main.py:378-415` | **RESUELTO VERIFICADO v5.47.0** · queda marcado `pendiente_subida` y bloquea la descarga siguiente para no perderlo | 12 |
| SYNC-005 | P0 | alta | La fusión empareja registros por el identificador autoincremental local: dos equipos generan el mismo número para entidades distintas | `sync/data_exporter.py:219,252,285…` | **RESUELTO VERIFICADO v5.47.0** · al abrir se reconstruye la base local desde la nube: no hay dos linajes que fusionar | 12 |
| SYNC-006 | P0 | alta | Las bajas no se propagan y reaparecen: la importación solo crea y actualiza | `sync/sync_manager.py:505` | **RESUELTO VERIFICADO v5.47.0** · mismo cambio; test de dos equipos con baja que se propaga | 12 |
| SYNC-007 | P1 | alta | La subida no es atómica: un corte deja truncado el único fichero del servidor | `sync/sync_manager.py:290-303` | **RESUELTO VERIFICADO v5.47.0** · subida a temporal y renombrado atómico en ambos backends | 12 |
| SYNC-008 | P1 | alta | No hay copias ni versiones en el servidor | copias solo locales en `database/db_manager.py` | **RESUELTO VERIFICADO v5.47.0** · se conservan 3 versiones anteriores en el servidor | 12 |
| SYNC-009 | P0 | alta | Las cuentas viven en cada equipo y la carpeta remota depende solo del nombre: no se puede entrar desde otro equipo, y la contraseña no protege nada. Cualquiera puede registrar el nombre de otro en su equipo y quedarse con sus datos | `sync/sync_manager.py:650-700,415-419` | **RESUELTO VERIFICADO v5.48.0** · la cuenta vive en `users/<hash>/cuenta.json`; el servidor manda al entrar, con copia local para trabajar sin conexión, y no se puede registrar un nombre ya existente | 12 |
| SYNC-010 | P2 | alta | El bloqueo de sesión falla abierto si no se puede leer su información | `main.py:290-292` | **RESUELTO VERIFICADO v5.47.0** · si no se puede leer el bloqueo, no se entra | 12 |
| SYNC-011 | P2 | alta | El bloqueo no cubre el trabajo sin red | `sync/session_lock.py` | NUEVO | 12 |
| SYNC-012 | P2 | alta | La guarda de descarga solo cuenta registros: rechaza borrados legítimos y no protege la subida | `sync/sync_manager.py:459-466` | **RESUELTO VERIFICADO v5.47.0** · la guarda pasa a ser validez del fichero y número de versión, no recuento de registros | 12 |
| SYNC-013 | P2 | alta | Credenciales de correo y servidor viajan en el JSON, cifradas con una clave propia de cada equipo, así que ni sirven fuera ni deberían estar ahí | `sync/data_exporter.py:66-68`, `data_exporter_helpers.py:25-36` | **RESUELTO VERIFICADO v5.48.0** · las credenciales salen del fichero de datos; las de ficheros antiguos se ignoran | 12 |
| SYNC-014 | P2 | alta | La sincronización automática cada 30 min solo sube, nunca descarga | `presentation/ccleaner_main_window.py:262-270` | NUEVO | 12 |
| SYNC-015 | P3 | alta | La decisión de descargar depende de comparar relojes de equipos distintos | `sync/sync_manager.py:440-447` | **RESUELTO VERIFICADO v5.47.0** · se decide por número de versión, no por fechas | 12 |
| SYNC-016 | P0 | alta | Un nombre de usuario es público: bastaba con conocerlo y registrarlo con cualquier contraseña para descargarse y manipular los datos de esa persona. Afectaba a las cuentas antiguas, con datos en el servidor pero sin ficha de contraseña publicada | `sync/sync_manager.py` (`_comprobar_nombre_disponible`) | **RESUELTO VERIFICADO v5.49.0** · no se puede registrar un nombre que ya tenga datos en el servidor; se indica cómo activarlo desde el equipo de origen | [[12_SINCRONIZACION_NUBE]] |
| SYNC-017 | P2 | alta | Una cuenta con datos solo en local no creaba su carpeta en el servidor hasta cerrar la aplicación | `sync/sync_manager.py` (`sync_on_startup`) | **RESUELTO VERIFICADO v5.49.0** · si la nube está vacía y el equipo tiene datos, se suben al abrir | 12 |
| UXA-015 | P1 | alta | Los datos recargados no se veían: había que cerrar y volver a abrir la aplicación. El envoltorio de cada vista no conservaba el widget y las señales de importación no las escuchaba nadie | `presentation/ccleaner_main_window.py` | **RESUELTO VERIFICADO v5.49.0** · recarga central que vacía la caché y repinta las vistas abiertas | 12 |

## COD · Calidad de código

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| COD-001 | P2 | alta | ~~Ruff 355 avisos; configuración obsoleta~~ | **RESUELTO PARCIAL v5.61.0** · `select`/`ignore` movidos a `[tool.ruff.lint]` (ruff avisaba en cada ejecución); **342 → 104 avisos**, todos `E501` en cadenas de texto, sobre todo el HTML de los correos. `E402` de `main.py` documentado como excepción en la configuración, no con `noqa` sueltos · ratchet `test_ratchet_de_avisos_de_ruff` | [[07_FUNCIONALIDAD_CALIDAD_ESCALABILIDAD]] |
| COD-002 | P2 | alta | Captura comodín `(ValueError, TypeError, OSError)` y `except Exception` | **PARCIAL v5.64.0** · atacadas las que tenían consecuencias: **las 39 que rodean acceso a la base de datos** dejaban escapar `SQLAlchemyError`, que subía hasta el manejador global y cerraba la vista. Ahora lo capturan, y `BaseForm.manejar_excepcion` **deshace la transacción** cuando el fallo es de base de datos: antes se mostraba el aviso pero la sesión quedaba inservible el resto de la vida de la vista. Quedan 72 en contextos de fichero, parseo e interfaz, donde la tupla sigue siendo arbitraria pero el daño es menor · `tests/audit/test_manejo_de_errores.py`, con guardarraíl por AST | 07 |
| COD-003 | P2 | alta | Presentación con ORM y queries; servicios con Session | NUEVO · pendiente, es cambio arquitectónico. Lote 14 bis | 07 |
| COD-004 | P3 | alta | ~~Código muerto (forms, estilos, loggers, specs)~~ | **RESUELTO VERIFICADO v5.61.0** · **2.130 líneas fuera**: `asignacion_guardias_form.py`, `home_form.py`, `dashboard_form.py`, `ui_styles.py` (envoltorio obsoleto), `orquestador_asignacion_guardias.py` (importaba dos módulos inexistentes) y su test, que fabricaba módulos falsos en `sys.modules`. Las diez vistas siguen instanciándose · `test_formularios_muertos_no_estan_registrados` | 07 |
| COD-005 | P3 | alta | ~~646 JSON sin rotación~~; niveles de logging | **RESUELTO PARCIAL v5.61.0** · cada generación dejaba un `comparacion_cuotas_*.json` con fecha y nadie los borraba; ahora se conservan los 20 últimos. El registro de la aplicación **ya tenía** rotación (10 MB × 5). Los niveles erróneos siguen sin revisar | 07 |
| COD-006 | P3 | alta | ~~25 `print`, 7 TODO~~ | **DESCARTADO v5.61.0 · falso positivo del recuento original.** De los 25 `print`, 9 están en ejemplos de docstring y 16 dentro de `print_cache_stats()`, cuya función es precisamente imprimir por consola. Y los 7 «TODO» son la palabra **TODOS** en español («todos los profesores»). Verificado recorriendo el AST: no hay nada que corregir | 07 |
| COD-007 | P2 | alta | ~~mypy estricto sólo en domain~~ | **RESUELTO PARCIAL v5.61.0** · el hallazgo se quedaba corto: convivían `mypy.ini` y `[tool.mypy]` en `pyproject.toml`, ganaba el primero y sus secciones por módulo apuntaban a rutas inexistentes (`src.domain.*`), **así que la rigurosidad declarada no se aplicaba a nada**. Unificado en `pyproject.toml`; al aplicarse de verdad afloraron 40 errores en `domain`, ahora **0**. Entre ellos, dos comparadores anotados como si sólo aceptaran su propio tipo, que hacían inalcanzable la rama que compara con números. Extenderlo a `application` (535 errores) queda para el 14 bis · `test_el_dominio_pasa_mypy_sin_errores`, `test_una_sola_configuracion_de_mypy` | 07 |
| COD-008 | P3 | alta | Siete módulos > 778 líneas | NUEVO · el mayor es `sync/sync_manager.py` (1.151). Partirlos es refactor con riesgo de regresión y conviene hacerlo módulo a módulo. Lote 14 bis | 07 |

## ESC · Escalabilidad y arquitectura

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| ESC-001 | P2 | alta | Tablas item-based sin modelo | **DESCARTADO v5.66.0 · medido, no hay problema.** Con los imports calientes: **17 ms** abrir el calendario con un curso entero (2.800 guardias) y **13 ms** la tabla de profesores con 200; con 1.000 profesores, 25 ms. El objetivo de la auditoría era p95 < 100 ms. Migrar las 12 tablas a `QTableView` + modelo es esfuerzo L y riesgo medio para no ganar nada medible. Se conserva como banco de pruebas `tests/audit/test_escalabilidad_vistas.py`, que avisa si algún día se vuelve lento | 07 |
| ESC-002 | P2 | media | ~~Solver con workers y timeout fijos~~; sin descomposición | **RESUELTO PARCIAL v5.66.0** · los hilos de búsqueda salen del número de núcleos (8 fijos sobrecargan un equipo de 4 y desaprovechan uno de 16) y el tiempo máximo pasa a `settings.solver_timeout_segundos`; ambos se pueden fijar a mano. La descomposición del problema sigue pendiente y sólo tendría sentido si aparece un caso que no resuelva en 120 s | 07 |
| ESC-003 | P2 | alta | Sync completa cada 30 min y al cerrar | NUEVO · desde v5.55.0 al menos corre en su propio hilo y con su propia sesión, así que ya no compite con la GUI. Sigue siendo una exportación completa cada vez: la sincronización incremental queda pendiente | 07 |
| ESC-004 | P3 | alta | Sin ruta a multiusuario real | NUEVO | 07 |
| ESC-005 | P2 | media | Caché por regex sin `curso_id` | NUEVO | 07 |
| ESC-006 | P3 | alta | Arranque secuencial en hilo GUI | NUEVO | 07 |
| ESC-007 | P2 | alta | ~~Clave de caché construida con la dirección de memoria; `cache_key_prefix` sin usar~~ | `utils/cache.py`, `utils/repository_cache.py` | **RESUELTO VERIFICADO v5.63.0** · `_representacion_estable()` sustituye la representación por defecto (`<Clase object at 0x…>`) por el nombre de la clase, así que la clave deja de depender de direcciones reutilizables; y el prefijo llega ya hasta la clave. Los argumentos normales y la exclusión de sesiones no cambian · `tests/audit/test_cache_claves.py` (11 tests) | 07 |

## SEC · Seguridad y privacidad

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| SEC-001 | P2 | alta | Credenciales en `.env` en texto plano | **PARCIAL v5.62.0** · el fichero se creaba con los permisos por defecto: en un equipo compartido, cualquier otra cuenta podía leer las contraseñas de SFTP y de correo. Ahora queda en 0600 tras cada escritura, en los **siete** puntos que lo guardan (uno lo encontró el propio test). **Falta lo principal: pasar las credenciales al almacén de claves del sistema**, que añade dependencia y necesita migración con vuelta atrás · `test_el_fichero_de_credenciales_queda_solo_para_su_dueno`, `test_todas_las_escrituras_del_env_protegen_el_fichero` | 07 |
| SEC-002 | P3 | alta | ~~`api_secret_key` vacío por defecto~~ | **RESUELTO VERIFICADO v5.62.0** · `validar_secreto_de_api()` se ejecuta antes de construir la aplicación FastAPI: sin secreto, o con uno de menos de 16 caracteres, no arranca y el error dice qué configurar y cómo generarlo. Antes levantaba igual y reventaba al firmar el primer token con un error de la librería JWT · `tests/audit/test_seguridad.py` | 07 |
| SEC-003 | P3 | media | ~~Bandit: hallazgos medios~~ | **RESUELTO VERIFICADO v5.62.0** · eran 6, ahora **0 medios y 0 altos**. Cuatro `tempfile.mktemp()` en `sync_manager` (devuelve un nombre sin crear el fichero: deja una ventana para un ataque por enlace simbólico) pasan a `mkstemp()`. Los dos `urlopen`/`urlretrieve` validan ahora que la dirección sea https y apunte a GitHub — importa porque lo que se descarga es un instalador — y quedan documentados con `# nosec` y su motivo · `test_bandit_sin_hallazgos_medios_ni_altos` | 07 |

## DEV · Eficiencia de agentes

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| DEV-001 | P2 | alta | Instrucciones del proyecto duplican `.agents/*` | RESUELTO VERIFICADO v5.43.0 (reescritura) | [[11_EFICIENCIA_AGENTES_Y_TOKENS]] |
| DEV-002 | P2 | alta | Sin mapa rápido | RESUELTO VERIFICADO v5.43.0 | 11 |
| DEV-003 | P3 | alta | Comandos incorrectos/lentos | RESUELTO VERIFICADO v5.43.0 (documentación); Makefile pendiente (BLD-002) | 11 |
| DEV-004 | P3 | alta | Sin skills de proyecto | RESUELTO VERIFICADO v5.43.0 | 11 |
| DEV-005 | P3 | alta | Permisos mínimos → prompts | NUEVO | 11 |
| DEV-006 | P3 | alta | Agente portable de 41 KB leído entero | NUEVO | 11 |

## FUN · Mejoras funcionales (tipo `mejora`, sin severidad)

FUN-001…FUN-014 en [[07_FUNCIONALIDAD_CALIDAD_ESCALABILIDAD]] §1. Estado: `PROPUESTA` pendiente de decisión de producto, salvo:

- **FUN-001 (panel «Estado del curso»): `DESCARTADO` v5.57.0.** Implementado en v5.56.0 y retirado a petición de CarlosFB. Su parte de dominio (`PreflightGeneracionUseCase`) se conserva y es la que resuelve UXF-002 y UXF-008.
- **FUN-004 (historial y restauración): `RESUELTO` v5.63.0.** `backup_database()` y `restore_database()` llevaban tiempo escritas en `db_manager` sin que las llamara nadie. Ahora se hace copia antes de generar y de limpiar, `listar_backups()` las enumera y la vista de Importar/Exportar permite volver a un momento anterior · `tests/audit/test_historial_y_restauracion.py`.
- **FUN-002 (generación incremental): `RESUELTO` v5.67.0.** Se puede recalcular sólo desde una fecha: lo anterior se congela y las sustituciones posteriores se respetan, porque son decisiones tomadas a mano. Las cuotas descuentan lo ya cubierto, así que el reparto sigue siendo justo sobre el curso completo. El diálogo propone **hoy** y sustituye a la pregunta anterior de sí/no, cuyo «no» añadía guardias encima de las existentes · `tests/audit/test_generacion_incremental.py`.
- **Orden acordado para las mejoras de generación: ~~FUN-004~~ → ~~FUN-002~~ → FUN-003** (decisión de 2026-09-05).

## Positivos a preservar

Listados en 04 §5 y 07 §5.
