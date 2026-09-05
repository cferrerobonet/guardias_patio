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
| CRW-001 | P0 | media | Señales Qt emitidas desde hilos internos de OR-Tools durante el solve | `_asignador_cpsat_helpers.py:233-244`, `progress_worker.py:40-43` | NUEVO · RIESGO A CONFIRMAR en Windows | [[06_CRASH_WINDOWS_GENERACION]] |
| CRW-002 | P1 | alta | Handler de logging modifica widgets desde el hilo que loguea; loggers obsoletos | `progress_handlers.py:41-52`, `progress_indicators.py:278-292,343-359` | NUEVO | 06 |
| CRW-003 | P1 | alta | Session SQLAlchemy compartida entre GUI, worker, sync y cierre | `db_manager.py:344-350`, `ccleaner_main_window.py:262-270`, `main.py:390-398` | NUEVO | 06 |
| CRW-004 | P2 | alta | Cancelar se ignora en las fases del solver (10 avisos) y sólo se propaga vía callback C++ | `asignador_guardias_cpsat.py:77-82`, `progress_worker.py:41-42` | NUEVO (verificado con test) | 06 |
| CRW-005 | P1 | alta | `sys.excepthook` crea QMessageBox desde cualquier hilo; SyncWorker captura poco | `main.py:60-95`, `sync_progress_dialog.py:34-47` | NUEVO | 06 |
| CRW-006 | P2 | alta | ~~Sin faulthandler; StreamHandler muerto en windowed~~ | `main.py:31-46` | **RESUELTO VERIFICADO v5.44.0** · `tests/audit/test_crash_windows_regresion.py::test_main_activa_faulthandler`. Queda pendiente el logging duplicado (COD-005) | 06 |
| CRW-007 | P2 | alta | Sync SFTP en el hilo GUI tras generar; excepciones escapan del slot | `generacion_panel.py:314-316,327-328,416-427` | NUEVO | 06 |
| CRW-008 | P3 | alta | ~~`SQLAlchemyError` sin importar en tres módulos y `Container` sin declarar~~ | `generacion_panel.py`, `gestion_cursos_widget.py`, `sync_manager.py`, `wiring.py` | **RESUELTO VERIFICADO v5.44.0** · `tests/audit/test_calidad_estatica.py::test_sin_nombres_indefinidos` | 06 |
| CRW-009 | P2 | media | Audit log de generación sin commit propio | `generar_guardias.py:150-153` | NUEVO | 06 |

## UXA · Accesibilidad y UX (Ola 4, 2026-08-04, reconciliados en este commit)

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| UXA-001 | P1 | alta | Ventana y diálogos no caben en pantallas/escalados habituales | PERSISTE | `_work/paquete_ux_accesibilidad.md` |
| UXA-002 | P1 | alta | Sin foco visible consistente | PERSISTE | ídem |
| UXA-003 | P1 | alta | Toasts no anunciables ni persistentes | PERSISTE | ídem |
| UXA-004 | P1 | alta | Contrato de cambios sin guardar no conectado | PERSISTE | ídem |
| UXA-005 | P1 | alta | Campos sin nombre/relación accesible | PERSISTE | ídem |
| UXA-006 | P1 | alta | Validaciones no identifican el campo | PERSISTE | ídem |
| UXA-007 | P1 | alta | Cambio de curso no refresca vistas (`ContentWrapper` sin `content_widget`) | **RESUELTO VERIFICADO v5.49.0** · `ContentWrapper` conserva la vista y el refresco por cambio de curso funciona | ídem |
| UXA-008 | P2 | alta | Tablas sin contrato accesible/adaptable | PERSISTE | ídem |
| UXA-009 | P2 | alta | Gráficos QPainter sin semántica | PERSISTE | ídem |
| UXA-010 | P2 | alta | Sistema visual fragmentado y contrastes AA fallidos | PERSISTE (ampliado en VIS-001/002) | ídem |
| UXA-011 | P2 | media | Cargas de tablas bloquean el hilo GUI | PERSISTE (ESC-001) | ídem |
| UXA-012 | P2 | alta | Suite a11y con skips amplios | PERSISTE | ídem |
| UXA-013 | P2 | alta | Navegación sin título/estado accesible | PERSISTE | ídem |
| UXA-014 | P3 | alta | Anti-patrones y tipografía microscópica | PERSISTE (VIS-003) | ídem |

## UXF · Flujo, guardarraíles y clics

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| UXF-001 | P1 | alta | Sin secuencia guiada ni panel de estado; la app abre en Profesores | NUEVO | [[03_UX_CASOS_DE_USO_Y_CAMINOS_DORADOS]] |
| UXF-002 | P1 | alta | Guardarraíl "cuotas antes de generar" es un flag de UI, no precondición de dominio | NUEVO | 03 |
| UXF-003 | P2 | alta | Generar requiere 2 modales previos y clic de cierre | NUEVO | 03 |
| UXF-004 | P2 | alta | Cambio de curso: confirmación + toast sin refresco | NUEVO (dup. parcial UXA-007) | 03 |
| UXF-005 | P2 | alta | Primer arranque exige SFTP; sin modo local | NUEVO · decidido 2026-09-05: se añade modo local con aviso persistente (lote 6) | 03 |
| UXF-006 | P2 | alta | Limpiar guardias con la misma prominencia que Generar | NUEVO | 03 |
| UXF-007 | P2 | alta | Sin protección de cambios sin guardar | DUPLICADO → UXA-004 | 03 |
| UXF-008 | P3 | alta | Motivo de bloqueo sólo en tooltip | NUEVO | 03 |
| UXF-009 | P2 | media | Ausencias sin deshacer ni vista previa | NUEVO | 03 |
| UXF-010 | P2 | alta | Cinco exportaciones PDF con diálogo cada una y sin recordar carpeta | NUEVO | 03 |
| UXF-011 | P3 | alta | Atajos de teclado casi inexistentes | NUEVO | 03 |

## VIS · Consistencia visual

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| VIS-001 | P2 | alta | Cuatro capas de estilo + 287 inline | NUEVO | [[04_INVENTARIO_SUPERFICIES_E_INCONSISTENCIAS_VISUALES]] |
| VIS-002 | P2 | alta | Dos identidades cromáticas (tokens vs Tailwind vs terminal) | NUEVO | 04 |
| VIS-003 | P2 | alta | Fuente `-apple-system` inexistente en Windows; 43 usos < 11 px | NUEVO | 04 |
| VIS-004 | P3 | alta | Emojis como iconos (327 líneas) | NUEVO | 04 |
| VIS-005 | P2 | alta | Terminal retro para resultados | NUEVO | 04 |
| VIS-006 | P2 | alta | Títulos inconsistentes; título registrado no se pinta | NUEVO | 04 |
| VIS-007 | P2 | alta | Botones sin jerarquía | NUEVO | 04 |
| VIS-008 | P3 | alta | Tres lenguajes de feedback | NUEVO | 04 |
| VIS-009 | P2 | alta | Mínimo 1400×900 vs settings 1200×800 | NUEVO (dup. parcial UXA-001) | 04 |
| VIS-010 | P3 | alta | Identidad "ccleaner" y branding EPLA inconsistentes | NUEVO | 04 |

## BLD · Build y release

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| BLD-001 | P1 | alta | `.spec` ignorados por git y borrados por `make clean` | **RESUELTO VERIFICADO v5.50.0** · los `.spec` se versionan y `make clean` ya no los borra | [[09_BUILD_Y_RELEASE]] |
| BLD-002 | P1 | alta | Tres scripts Windows divergentes; Makefile/README apuntan a los obsoletos | **RESUELTO VERIFICADO v5.50.0** · eliminados los cuatro scripts obsoletos; queda `scripts/build_windows.ps1` como único de Windows | 09 |
| BLD-003 | P2 | alta | Cuatro versiones distintas en el repo | **RESUELTO VERIFICADO v5.50.0** · `pyproject.toml` sincronizado y test que lo vigila | 09 |
| BLD-004 | P2 | alta | Sin CI, sin firma/notarización | **RESUELTO PARCIAL v5.50.0** · flujo `.github/workflows/compilar.yml` con pruebas y compilación de Windows y macOS. Falta la firma y notarización | 09 |
| BLD-005 | P2 | alta | Actualizador sólo `.dmg`; Windows sin actualizaciones | **RESUELTO VERIFICADO v5.50.0** · el actualizador elige el instalador de su sistema, así que Windows ya recibe actualizaciones | 09 |
| BLD-006 | P3 | alta | Instalador con admin y sin cierre de instancias | NUEVO | 09 |
| BLD-007 | P2 | alta | ~~Sin build de diagnóstico con consola~~ | **RESUELTO VERIFICADO v5.44.0** · `scripts/build_windows.ps1 -Diagnostico` | 09 |

## QA · Tests

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| QA-001 | P1 | alta | Entorno de tests no reproducible; 6 errores de colección | NUEVO | [[08_ESTRATEGIA_DE_TESTS]] |
| QA-002 | P2 | alta | `pytest.ini` con cov obligatorio y `timeout` sin plugin | NUEVO | 08 |
| QA-003 | P2 | alta | Tests del formulario muerto `AsignacionGuardiasForm` | NUEVO | 08 |
| QA-004 | P2 | alta | Sin tests de hilos/cancelación/excepthook | NUEVO (tests creados, xfail) | 08 |
| QA-005 | P2 | alta | Fallo preexistente tolerado; skips amplios | NUEVO | 08 |
| QA-006 | P3 | alta | Nada sobre SQLite en fichero ni migraciones reales | NUEVO (fixture creada) | 08 |
| QA-007 | P3 | alta | Sin E2E web | NUEVO (suite creada) | 08 |
| QA-008 | P1 | alta | ~~Cuatro tests bloquean la suite indefinidamente al abrir un diálogo modal~~ | **RESUELTO VERIFICADO v5.44.0** · guarda `dialogos_modales` en `tests/conftest.py` + dos tests de importación corregidos. La suite completa pasa de una sola pasada en 47 s | 08 |
| QA-009 | P3 | alta | 7 tests marcados `xfail` pasan al ejecutarse aislados pero fallan dentro de la suite completa (`test_dialogs_basic.py` ×6, `test_gestor_ausencias.py` ×1): dependen del orden de ejecución | NUEVO (verificado) | 08 |
| QA-010 | P3 | alta | `tests/__pycache__` conserva bytecode compilado desde una ubicación anterior del proyecto (carpeta OneDrive inexistente) y de otra versión de pytest | NUEVO (verificado) | 08 |
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
| COD-001 | P2 | alta | Ruff 355 avisos; configuración obsoleta | NUEVO | [[07_FUNCIONALIDAD_CALIDAD_ESCALABILIDAD]] |
| COD-002 | P2 | alta | Captura comodín `(ValueError, TypeError, OSError)` y 67 `except Exception` | NUEVO | 07 |
| COD-003 | P2 | alta | Presentación con ORM y queries; servicios con Session | NUEVO | 07 |
| COD-004 | P3 | alta | Código muerto (forms, estilos, loggers, specs) | NUEVO | 07 |
| COD-005 | P3 | alta | Logging con niveles erróneos y 646 JSON sin rotación | NUEVO | 07 |
| COD-006 | P3 | alta | 25 `print`, 7 TODO | NUEVO | 07 |
| COD-007 | P2 | alta | mypy estricto sólo en domain | NUEVO | 07 |
| COD-008 | P3 | alta | Seis módulos > 790 líneas | NUEVO | 07 |

## ESC · Escalabilidad y arquitectura

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| ESC-001 | P2 | alta | Tablas item-based sin modelo | NUEVO | 07 |
| ESC-002 | P2 | media | Solver sin descomposición, workers y timeout fijos | NUEVO | 07 |
| ESC-003 | P2 | alta | Sync completa cada 30 min y al cerrar | NUEVO | 07 |
| ESC-004 | P3 | alta | Sin ruta a multiusuario real | NUEVO | 07 |
| ESC-005 | P2 | media | Caché por regex sin `curso_id` | NUEVO | 07 |
| ESC-006 | P3 | alta | Arranque secuencial en hilo GUI | NUEVO | 07 |
| ESC-007 | P2 | alta | La clave de la caché de consultas se construye con `str(self)`, que incluye la dirección de memoria del objeto. Python reutiliza direcciones: 300 instancias creadas y destruidas en serie generan **una sola clave**. Un caso de uso nuevo puede recibir el resultado cacheado de otro anterior durante el TTL (3 min en profesores). Además `cache_key_prefix` se acepta pero nunca se usa | `utils/cache.py:59-87`, `utils/repository_cache.py:40-63,100-105`, `application/use_cases/profesor/listar_profesores.py:40-41` | NUEVO (verificado con demostración) | 07 |

## SEC · Seguridad y privacidad

| ID | Sev. | Conf. | Título | Estado | Ficha |
| --- | --- | --- | --- | --- | --- |
| SEC-001 | P2 | alta | Credenciales en `.env` en texto plano | NUEVO | 07 |
| SEC-002 | P3 | alta | `api_secret_key` vacío por defecto | NUEVO | 07 |
| SEC-003 | P3 | media | Bandit 3 medios | NUEVO | 07 |

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

FUN-001…FUN-014 en [[07_FUNCIONALIDAD_CALIDAD_ESCALABILIDAD]] §1. Estado: `PROPUESTA` pendiente de decisión de producto.

## Positivos a preservar

Listados en 04 §5 y 07 §5.
