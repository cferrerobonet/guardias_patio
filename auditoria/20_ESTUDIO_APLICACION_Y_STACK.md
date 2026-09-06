---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-06
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Estudio de la aplicación y su stack (medido el 2026-09-06)

> [!NOTE] Para qué sirve este documento
> Es la foto real de la aplicación sobre la que se diseña [[21_PLAN_DE_AUDITORIA_AMPLIADO]]. Todo lo que hay aquí está **medido con comandos**, no supuesto. Cuando un modelo más pequeño vaya a auditar, este es el documento que le dice qué hay, cuánto pesa y dónde están los puntos débiles conocidos. Los hallazgos concretos viven en [[30_REGISTRO_HALLAZGOS]]; aquí sólo se describe.

## 1. Qué es

Aplicación de escritorio para repartir las guardias de patio de un colegio (~200 docentes, ~2.400 alumnos) entre el profesorado, con equidad por jornada y tutoría, ausencias y sustituciones, calendario, PDF, correo e iCal. La usa **una persona** (jefatura) por curso; varios equipos se turnan mediante un bloqueo de sesión y una copia en un servidor SFTP del hosting del centro. Existe además una API REST separada (FastAPI) que no se empaqueta con la app.

| Dato | Valor medido |
| --- | --- |
| Versión | 5.96.2 (`src/config/settings.py`, `pyproject.toml`) |
| Código de aplicación | 61.790 líneas en 274 ficheros (`src/`) |
| Tests | 47.361 líneas en 183 ficheros; **2.877 pasan**, 10 saltados, 3 fallos conocidos |
| Cobertura | **70,5 %** de `src/` (branch) |
| Repositorio | **público**: `github.com/cferrerobonet/guardias_patio` |
| Plataformas | macOS (DMG firmado ad-hoc) y Windows 10/11 (exe + Inno Setup), compiladas en GitHub al publicar una etiqueta |

## 2. Stack verificado

| Capa | Tecnología | Versión / nota |
| --- | --- | --- |
| Lenguaje | Python | 3.11.15, intérprete en `~/.venvs/guardias-patio` (**fuera de iCloud**: dentro corrompe Qt) |
| Interfaz | PyQt6 | 6.7.0 fijado; Qt 6.7.3 |
| Persistencia | SQLite por usuario + SQLAlchemy 2.0 + Alembic | 26 revisiones, una sola cabeza (`9defacb2c7e9`); PRAGMAs y migraciones directas en `database/db_manager.py` |
| Optimización | OR-Tools CP-SAT | hilos = núcleos, tiempo máximo configurable |
| Nube | paramiko (SFTP) | `RejectPolicy` de claves de host + `known_hosts`; volcado JSON por usuario, 3 versiones rotadas |
| Correo | smtplib + STARTTLS | plantilla HTML propia |
| Secretos | `keyring` (Keychain / Administrador de credenciales) | desde v5.95.0; `.env` sólo con lo no secreto |
| API | FastAPI + PyJWT + slowapi + bcrypt | todas las rutas tras `get_current_user`; CORS sólo `localhost`; 60 req/min |
| Informes | reportlab, matplotlib, openpyxl | PDF, gráficos QPainter, importación Excel |
| Calidad | ruff (E, F, W, I; 100 col.), mypy (estricto sólo en `domain/`), bandit, pytest + pytest-qt + hypothesis + mutmut | mypy y bandit **no** corren en CI |
| Empaquetado | PyInstaller (`GuardiasDePatio.spec`, único desde v5.97.0), Inno Setup, `build_dmg.sh` | firma/notarización macOS lista a falta de cuenta Apple activa |
| Observabilidad | structlog, `RotatingFileHandler` 10 MB × 5, `faulthandler`, prometheus-client + psutil | prometheus/psutil en una app de escritorio: revisar si aportan algo |

## 3. Arquitectura y dónde está el peso

Clean Architecture híbrida con DDD táctico. Medido por paquete:

| Paquete | Ficheros | Líneas | Comentario |
| --- | ---: | ---: | --- |
| `services/` | 34 | 12.647 | El más grande: asignador CP-SAT, PDF, exportación, gestores. Aquí vive la lógica de negocio real |
| `presentation/forms/` (+ widgets por vista) | 57 | 15.958 | Diez vistas registradas en `ventana_principal.py` |
| `presentation/widgets/` | 17 | 5.606 | Calendario, progreso, gráficos, estadísticas |
| `presentation/dialogs/` | 15 | 3.998 | Configuración inicial, permuta, envío de avisos, informe de importación |
| `sync/` | 9 | 2.735 | `sync_manager` (qué y cuándo), `backends` (cómo), `cuentas`, `session_lock` |
| `core/` | 16 | 3.985 | rutas, logging, credenciales, limpieza de rastros, observabilidad |
| `application/` | 49 | 4.721 | casos de uso y DTOs |
| `domain/` + `infrastructure/` | 40 | 4.334 | entidades, repositorios, mappers |
| `api/` | 11 | 1.457 | routers, auth |

Módulos que siguen por encima de 778 líneas (COD-008): `generacion_panel.py` (955), `db_manager.py` (868), `profesor_form.py` (828), `tema_aplicacion.py` (822), `vista_calendario.py` (815), `initial_config_dialog.py` (785). Son vistas: partirlas por tamaño no compensa salvo costura real.

## 4. Flujos críticos (los que hay que auditar primero)

1. **Arranque**: configuración inicial (SFTP obligatorio) → login contra la ficha remota → base por usuario → migraciones → bloqueo de sesión → descarga de la nube → ventana. Desde v5.88.0 con pantalla de arranque; todo en el hilo de la interfaz a propósito.
2. **Generación de guardias**: preflight → cuotas → CP-SAT en `WorkerThread` con sesión propia, progreso por buzón, cancelación cooperativa → guardar → sincronizar. Fue el origen del cierre en Windows (nueve hallazgos CRW, todos resueltos; falta confirmar en la máquina).
3. **Sincronización**: exportar todo a JSON → comparar huella → rotar 3 versiones → subir atómico. Bloqueo de sesión con latido de 30 s.
4. **Ausencias y sustituciones**, permuta entre profesores, papelera de «Limpiar guardias».
5. **Salidas**: PDF individual y mensual, iCal, avisos por correo con vista previa, calendarios web estáticos con dirección secreta por profesor.

## 5. Datos personales que maneja (esto define la dimensión de privacidad)

| Dato | Dónde vive | Dónde viaja |
| --- | --- | --- |
| Nombre completo y correo corporativo del profesorado | `profesores` | Volcado JSON al SFTP del centro, PDF, correos, páginas web publicadas, registros de la app (correos en `logger.info`) |
| Jornada, turno, tutoría, restricciones | `profesores` | Volcado, PDF |
| **Ausencias con `tipo` (`baja_medica`, `permiso`…), `motivo` libre y `documento_path`** | `ausencias` | **Volcado JSON al servidor, en claro**. El tipo de ausencia es dato de salud a efectos de protección de datos |
| Contraseñas SFTP/SMTP | Llavero del sistema | No viajan desde v5.48.0. Antes: en base64 dentro del volcado (ver [[30_REGISTRO_HALLAZGOS]] SEC-004/005) |
| Cuentas de la app | `users.json` local y `cuenta.json` remoto, bcrypt | Ficha remota |

No hay política de retención ni de borrado: borrar un profesor arrastra sus guardias y ausencias (`ondelete=CASCADE`), pero no hay forma de exportar «todo lo de una persona» ni de anonimizar cursos antiguos.

## 6. Seguridad, medido hoy

| Comprobación | Resultado |
| --- | --- |
| `bandit -r src -ll` | 0 hallazgos medios o altos |
| `pip-audit` | **1 CVE**: `setuptools 82.0.1` → PYSEC-2026-3447 (corregido en 83.0.0) |
| `eval`/`exec`/`pickle`/`yaml.load`/`shell=True` | ninguno (los `exec()` son de diálogos Qt) |
| SQL crudo | sólo en migraciones directas de `db_manager.py`, con cadenas constantes |
| Aleatoriedad para secretos | `secrets` en recuperación de contraseña y enlaces web; `uuid4` para trazas |
| Temporales | `mkstemp` (SEC-003 resuelto) |
| Claves de host SSH | `RejectPolicy` + `known_hosts`: seguro, pero un equipo nuevo **no puede conectar** hasta que alguien haga `ssh-keyscan`; ningún diálogo lo explica |
| API | auth en todos los routers, bcrypt, JWT con caducidad, CORS `localhost`, límite 60/min. Valida contra `data/users.json` relativo al código |
| Secretos en el código | retirados en v5.94.0; test que impide que vuelvan |
| **Historial de git (público)** | contraseña SFTP en claro en 3 commits (2025-10) y en base64 en 1 (2025-11); listados del claustro en `docs/examples` desde 2025-11-15 hasta v5.96.2 |
| Entorno global del asistente | clave de la API de Obsidian en texto plano y `NODE_TLS_REJECT_UNAUTHORIZED=0` en `~/.claude/settings.json`, apuntando además a otra bóveda |
| CI | sólo se dispara con etiquetas; **no ejecuta ruff, mypy, bandit ni pip-audit** |

## 7. Calidad de código, medido hoy

| Métrica | Valor | Lectura |
| --- | --- | --- |
| ruff | 97 avisos, todos `E501` (líneas > 100) | Sin errores reales |
| mypy | verde en `domain/`; el resto sin exigir | Progresivo, como se decidió |
| radon: funciones con complejidad ≥ C (> 10) | **92** | Las peores: `main()` E (36), `sync_on_shutdown` D (28), `import_from_json` D (26), `ProfesorMapper.to_entity` D (26), `revisar_y_limpiar` D (23, nuevo) |
| radon: índice de mantenibilidad más bajo | `ausencias_sustituciones.py` 21, `_exportador_import.py` 21, `generacion_panel.py` 27, `sync_manager.py` 28 | Todo por encima de 20 = rango A, pero en el límite |
| vulture (≥ 80 %) | 5 variables sin usar | Poco código muerto que quede |
| `except Exception` / tuplas comodín | 83 / 125 | Con techo que no puede subir |
| `setStyleSheet` en línea | 238, casi todos únicos por widget | No compensa extraer más |
| `open()` sin `encoding=` | 7 (`session_lock.py`, `sync_manager.py`) | En Windows es cp1252: acentos rotos en JSON de estado |
| `datetime.now()` sin zona horaria | 53 frente a 18 con zona | Mezcla; peligroso al comparar con lo que viene del servidor |
| Nombres de mes por `strftime("%B")` | 3 sitios, con `setlocale` sólo en uno | En Windows sin `es_ES` salen en inglés |

## 8. Tests: qué hay de verdad

| Señal | Valor |
| --- | --- |
| Tests | 2.877 pasan en ~60 s (sin benchmarks) |
| Ficheros que usan `MagicMock`/`patch` | 66 de 174 |
| Ficheros que leen el **código fuente como texto** (`inspect.getsource`, `read_text`) | **34 de los de `tests/audit`**. Son guardarraíles útiles pero frágiles: se rompen con cualquier refactor y no prueban comportamiento |
| Tests con base SQLite en fichero real | 26 ficheros |
| Skips / xfail | 42 / 3 (los 3 xfail son `downgrade` de Alembic: migraciones sin nombre de restricción, ficheros protegidos) |
| Barreras para que la suite no toque nada real | diálogos modales, SMTP, llavero, `.env`. **Las tres últimas se pusieron hoy después de que un test tocara cada cosa real** |
| Cobertura por zona de riesgo | `main.py` 10,7 %, PDF individual 16 %, PDF mensual 30 %, `services/assignment` 47 %, `sync/backends` 54 % |

## 9. Sincronización: lo que falta por cerrar

- Latido cada 30 s y caducidad del bloqueo a los 30 s: **un latido perdido basta** para que otro equipo entre.
- `release_lock()` no borra el bloqueo remoto (el backend no tiene `delete`): al cerrar, el siguiente equipo espera a que caduque.
- La descarga se valida por estructura (claves conocidas), **no por integridad** (sin hash ni tamaño esperado).
- La rotación de versiones remotas nunca ha producido `.1/.2/.3` en el servidor real (verificado el 2026-09-06): la copia de seguridad remota que promete el código no existe.
- SYNC-011: el bloqueo no cubre el trabajo sin red.

## 10. Documentación y entorno de desarrollo

- `README.md` manda crear el `.venv` **dentro** del repositorio, que está en iCloud: es justo lo que corrompe Qt (QA-013). Contradice al fichero de instrucciones del asistente.
- `docs/ADR.md` y `docs/API_TECHNICAL.md`: última edición 2026-04-20; no citan módulos inexistentes, pero no recogen nada de lo hecho desde entonces (llavero, papelera, publicación web, incremental).
- `.vscode/` versionado (9 configuraciones de ejecución, 10 tareas): útil.
- `.claude/settings.local.json` **versionado** pese a llamarse local; sólo contiene la lista de permisos.
- 36 dependencias sin fijar (`>=`), 2 fijadas exactas, sin fichero de bloqueo; 6 desactualizadas.

## 11. Puntos fuertes que conviene no romper

- Frontera solver↔Qt limpia y probada (buzón de progreso, cancelación cooperativa).
- Sesión de base de datos por hilo, con guardarraíl por AST.
- Ratchets de consistencia visual y de deuda que sólo pueden bajar.
- Contraseñas en el llavero y limpieza automática de rastros de versiones anteriores.
- Compilación de las dos plataformas en GitHub sin necesitar un PC con Windows.
- Registro de hallazgos único con estado y evidencia por versión.
