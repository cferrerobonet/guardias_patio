---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-06
estado: activo
prioridad: 1-urgente
tipo: referencia
---

# Plan de auditoría ampliado (ejecutable por modelos más pequeños)

> [!NOTE] Cómo se relaciona con el plan anterior
> [[02_PLAN_MAESTRO_AUDITORIA]] cubre siete dimensiones (A–G) y sigue siendo válido. Este documento **añade nueve** que allí no existían o quedaban en dos líneas, y reescribe cada comprobación en el formato que un modelo más pequeño puede ejecutar sin pensar demasiado: un comando literal, un criterio de paso y una severidad si falla. Los hallazgos se registran siempre en [[30_REGISTRO_HALLAZGOS]] con la ficha de la sección 4.

## 1. Qué cubría el plan anterior y qué faltaba

| Dimensión | En [[02_PLAN_MAESTRO_AUDITORIA]] | Estado real (2026-09-06) | Qué añade este plan |
| --- | --- | --- | --- |
| A · Experiencia de uso | 17 checks | 15 cerrados | Nada nuevo; se mantiene |
| B · Consistencia visual | 12 checks | 10 cerrados | Nada nuevo; se mantiene |
| C · Fiabilidad, hilos, sesión | 12 checks | 11 cerrados | Falta confirmar en Windows; se mantiene |
| D · Funcionalidad | 8 checks | 7 cerrados | Se mantiene |
| E · Calidad de código | 9 checks, sin métricas | Parcial | **Métricas medibles** (complejidad, mantenibilidad, código muerto, encoding, fechas) |
| F · Tests | 9 checks | 8 cerrados | **Calidad de los tests**: mocks, tests de texto fuente, barreras, cobertura por riesgo |
| G · Build y release | 5 checks | 4 cerrados | **Cadena de suministro** y CI con gates |
| **H · Seguridad** | 0 checks (sólo 3 hallazgos SEC sueltos) | — | **Nueva**: secretos, historial, SSH, API, actualizador, permisos |
| **I · Privacidad y datos personales** | 0 | — | **Nueva**: inventario de datos, datos de salud, retención, exportación, registros |
| **J · Dependencias y cadena de suministro** | 0 | — | **Nueva**: CVE, fijado, bloqueo, licencias, hooks de PyInstaller |
| **K · Integridad de datos y sincronización** | 15 SYNC cerrados | 1 abierto | **Nueva como dimensión**: integridad, bloqueo, copias remotas, conflictos |
| **L · Rendimiento y recursos** | 2 ESC medidos | — | **Nueva**: arranque, memoria, tamaño de volcado, solver con 200 profesores |
| **M · Observabilidad y soporte** | 1 check (C-07) | — | **Nueva**: qué se registra, qué sobra, cómo se diagnostica en el equipo de un usuario |
| **N · Documentación y onboarding** | 1 check (E-09) | — | **Nueva**: README, ADR, guías, coherencia con el código |
| **O · Entorno de desarrollo y agentes** | 6 DEV | 4 cerrados | **Nueva como dimensión**: instrucciones, skills, hooks, MCP, permisos, barreras |
| **P · Accesibilidad como verificación humana** | UXA | 12 cerrados | Protocolo para la sesión con lector de pantalla que nadie ha hecho |

## 2. Reglas para ejecutar este plan con un modelo más pequeño

> [!WARNING] Léelas antes de tocar nada
> 1. **Una dimensión por sesión.** Abrir sólo este documento, [[20_ESTUDIO_APLICACION_Y_STACK]] y [[30_REGISTRO_HALLAZGOS]]. No leer la carpeta `auditoria/` entera ni `.agents/`.
> 2. **Ejecutar los comandos tal cual están escritos**, desde la raíz del repositorio, con `PY=~/.venvs/guardias-patio/bin/python` y `export QT_QPA_PLATFORM=offscreen`. Si un comando no existe, anotarlo como hallazgo de la dimensión O; no inventar otro.
> 3. **Auditar no es arreglar.** En la sesión de auditoría sólo se escriben fichas de hallazgo. Arreglar es otra sesión, por lotes, según [[17_PLAN_DE_ATAQUE]].
> 4. **Barrera antes que test.** Si un test nuevo va a tocar red, llavero, `.env`, servidor o base de datos real, primero se escribe la barrera en `tests/conftest.py` y después el test. Hoy hay cuatro barreras (`dialogos_modales`, `sin_smtp_de_verdad`, `sin_llavero_de_verdad`, `sin_env_de_verdad`); las tres últimas llegaron después de que un test tocara lo real.
> 5. **No escribir nunca la palabra prohibida por la bóveda** (el nombre del asistente) en ningún fichero del proyecto. Decir «el asistente» o «el fichero de instrucciones».
> 6. **Ficheros protegidos**: no modificar `.env`, `data/`, `alembic/versions/` existentes ni los JSON de configuración. Leerlos sí.
> 7. Un hallazgo sin comando reproducible y sin fichero:línea **no vale**.

### Ficha de hallazgo (copiar tal cual en [[30_REGISTRO_HALLAZGOS]])

```
| <FAMILIA>-<nnn> | P<0-3> | <confianza alta/media/baja> | <título en una línea> | NUEVO · <evidencia: fichero:línea o salida del comando> · <impacto en una frase> · <remedio propuesto> | 21 |
```

Familias: `SEC` seguridad · `PRIV` privacidad · `SUP` dependencias · `SYNC` sincronización · `PERF` rendimiento · `OBS` observabilidad · `DOC` documentación · `DEV` entorno y agentes · `COD` calidad · `QA` tests · `BLD` build · `UXA`/`UXF`/`VIS` (las de siempre).

Severidad: **P0** pérdida de datos o exposición de contraseñas/datos personales · **P1** fallo funcional sin rodeo o riesgo real de seguridad · **P2** deuda con consecuencia visible · **P3** mejora.

### Orden de olas

| Ola | Dimensiones | Por qué en este orden |
| --- | --- | --- |
| 1 | H, I | Lo que puede hacer daño fuera del equipo |
| 2 | J, K | Lo que puede perder datos o dejar la app sin arrancar |
| 3 | E, F, G | Deuda medible con ratchets |
| 4 | L, M, N | Calidad de vida |
| 5 | O | El propio entorno de trabajo |
| 6 | P + verificaciones humanas | Lo que sólo puede hacer una persona |

## 3. Checklists por dimensión

Cada fila: **ID · qué · cómo (comando) · pasa si · severidad si falla**.

### H · Seguridad

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-H-01 | Ningún secreto en el código | `$PY -m pytest tests/audit/test_credenciales_no_van_en_el_codigo.py -q` y `git grep -nE "(password|contraseña|api_key|secret)\s*[:=]\s*['\"][^'\"]{6,}" -- src` | Test verde y grep vacío (salvo `os.getenv`) | P0 |
| CHK-H-02 | Ningún secreto en el **historial** | `git log --all -p -S"<valor del llavero>" --format=%h` (obtener el valor con `$PY -c "from core.credenciales import leer; print(leer('SFTP_PASSWORD'))"` **sin pegarlo en la ficha**) | Ningún commit | P0 → rotar la contraseña |
| CHK-H-03 | Ningún dato real versionado | `$PY -m pytest tests/audit/test_sin_datos_reales_en_el_repositorio.py -q` | Verde | P0 |
| CHK-H-04 | Contraseñas en el llavero, no en el `.env` | `$PY -m pytest tests/audit/test_credenciales_en_el_llavero.py tests/audit/test_limpieza_de_rastros.py -q` | Verde | P1 |
| CHK-H-05 | `.env` con permisos de sólo dueño (macOS/Linux) | `stat -f %Sp .env ~/Library/Application\ Support/GuardiasDePatio/.env` | `-rw-------` | P1 |
| CHK-H-06 | bandit sin hallazgos medios/altos | `$PY -m bandit -r src -q -ll` | Salida vacía | P1 |
| CHK-H-07 | Claves de host SSH no se aceptan a ciegas | `grep -n "AutoAddPolicy\|WarningPolicy" src/sync/backends.py` | Vacío (`RejectPolicy`) | P1 |
| CHK-H-08 | Primer equipo sin `known_hosts` recibe instrucciones en pantalla, no sólo en el registro | Leer `src/sync/backends.py:255-262` y buscar `ssh-keyscan` en `src/presentation` | Aparece en un diálogo | P2 |
| CHK-H-09 | STARTTLS con verificación de certificado | `grep -rn "starttls(" src` → comprobar que no se pasa `context` inseguro ni se desactiva verificación | Sin `CERT_NONE`/`verify=False` | P1 |
| CHK-H-10 | API: todas las rutas autenticadas, CORS acotado, límite de peticiones | `grep -n "dependencies=\[_auth\]\|allow_origins\|default_limits" src/api/main.py` | 6 routers con `_auth`, orígenes `localhost`, límite presente | P1 |
| CHK-H-11 | Actualizador: sólo HTTPS a GitHub y sin ejecutar nada no verificado | `$PY -m pytest tests/audit/test_aviso_de_version.py tests/audit/test_seguridad.py -q` | Verde | P1 |
| CHK-H-12 | Secretos del entorno del asistente | `python3 -c "import json;print([k for s in json.load(open('$HOME/.claude/settings.json')).get('mcpServers',{}).values() for k in s.get('env',{})])"` | Ninguna clave `*_KEY`/`TOKEN` en claro; sin `NODE_TLS_REJECT_UNAUTHORIZED=0` | P2 |
| CHK-H-13 | Instaladores no empaquetan secretos | `grep -n "\.env\|_config.json" GuardiasDePatio.spec scripts/build_windows.ps1` | Vacío | P0 |
| CHK-H-14 | Recuperación de contraseña: código de un solo uso, caducidad, no se registra | Leer `src/presentation/forms/forgot_password_dialog.py` y `email_service.send_recovery_code` | Código `secrets`, caduca, no aparece en `logger.*` | P1 |

### I · Privacidad y datos personales

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-I-01 | Inventario de datos personales actualizado | Comparar `src/infrastructure/database/models.py` con la tabla de [[20_ESTUDIO_APLICACION_Y_STACK]] §5 | Coinciden | P2 |
| CHK-I-02 | Datos de salud (`Ausencia.tipo`, `motivo`, `documento_path`) no viajan en claro al servidor | `grep -n "motivo\|documento_path\|tipo" src/sync/dtos.py` | O no viajan, o van cifrados con clave que no está en el servidor | P1 |
| CHK-I-03 | Correos y nombres no se escriben en los registros | `grep -rnE "logger\.\w+\(.*(email|to_email|nombre_completo)" src` | Vacío o enmascarado | P2 |
| CHK-I-04 | Registros no incluyen contenido de correos ni de PDF | `grep -rn "logger" src/services/email_service.py src/services/notificador_guardias.py` | Sólo destinatarios enmascarados y resultados | P2 |
| CHK-I-05 | Páginas web publicadas: dirección no adivinable, sin índice, `noindex` | `$PY -m pytest tests/audit/test_publicacion_web.py -q` | Verde | P1 |
| CHK-I-06 | Existe forma de borrar o anonimizar a una persona y de exportar lo suyo | Buscar en `src/services` y en la UI un «borrar profesor» que explique qué arrastra, y una exportación por persona | Existe y está documentado | P2 |
| CHK-I-07 | Retención: cursos cerrados y copias antiguas tienen fecha de borrado | Buscar en `db_manager.listar_backups` y en Gestión de cursos una política | Existe | P3 |
| CHK-I-08 | Volcado en el servidor con permisos de sólo dueño y sin copias huérfanas | Listado SFTP (`scripts/` no lo tiene: usar el fragmento de la sesión del 2026-09-06 en [[23_LIMPIEZA]]) | Sólo `users/<hash>/` con 4 ficheros | P1 |

### J · Dependencias y cadena de suministro

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-J-01 | Sin CVE conocidas | `$PY -m pip_audit --progress-spinner off` | Sin filas | P1 |
| CHK-J-02 | Dependencias fijadas y con fichero de bloqueo | `grep -c ">=" requirements.txt` y existencia de `requirements.lock` o `uv.lock` | Ejecución fijada (`==`), desarrollo aparte | P2 |
| CHK-J-03 | Separación ejecución / desarrollo | Existe `requirements-dev.txt` con pytest, mutmut, playwright… | Sí | P3 |
| CHK-J-04 | Licencias compatibles | `$PY -m pip install pip-licenses && $PY -m piplicenses --summary` | Sin GPL en dependencias de ejecución (la app es MIT) | P3 |
| CHK-J-05 | El spec de PyInstaller es único y lleva los hooks necesarios | `$PY -m pytest tests/audit/test_un_solo_spec.py tests/audit/test_credenciales_en_el_llavero.py -q` | Verde | P1 |
| CHK-J-06 | CI ejecuta lint, tipos, seguridad y suite en cada push | `grep -cE "ruff|mypy|bandit|pip_audit|pytest" .github/workflows/*.yml` y `on:` | Todos presentes y `on: [push, pull_request]` | P1 |
| CHK-J-07 | Acciones de GitHub fijadas por versión | `grep -n "uses:" .github/workflows/*.yml` | Cada `uses` con `@vN` o SHA | P3 |

### K · Integridad de datos y sincronización

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-K-01 | Lo descargado se verifica por integridad, no sólo por estructura | Leer `SyncManager._es_fichero_de_datos_valido` | Hay hash o tamaño esperado | P1 |
| CHK-K-02 | Bloqueo: caducidad > 3 latidos | `grep -n "lock_timeout\|heartbeat_interval" src/sync/session_lock.py` | `lock_timeout ≥ 3 × heartbeat_interval` | P1 |
| CHK-K-03 | Al cerrar se libera el bloqueo remoto | Leer `release_lock` | Borra o marca liberado en el servidor | P2 |
| CHK-K-04 | Las copias rotadas existen en el servidor | Listado SFTP: `guardias_patio_data.json.1` | Existe tras dos subidas | P2 |
| CHK-K-05 | Subida atómica y con versión creciente | `$PY -m pytest tests/audit/test_sincronizacion_nube.py tests/audit/test_sync_solo_si_hay_cambios.py -q` | Verde | P0 |
| CHK-K-06 | Restricciones de la base activas (`PRAGMA foreign_keys`) | `grep -n "foreign_keys" src/database/db_manager.py` | `ON` en cada conexión | P1 |
| CHK-K-07 | Copia local antes de generar y de limpiar; restauración probada | `$PY -m pytest tests/audit/test_historial_y_restauracion.py tests/audit/test_papelera_de_guardias.py -q` | Verde | P1 |
| CHK-K-08 | Ficheros de estado escritos con `encoding="utf-8"` | `grep -rnE "\bopen\([^)]*\)" src \| grep -v encoding` | Vacío | P2 |
| CHK-K-09 | Fechas con zona horaria coherente entre equipo y servidor | `grep -rn "datetime.now()" src \| wc -l` frente a `now(timezone` | Un solo criterio documentado | P2 |
| CHK-K-10 | Trabajo sin red no pisa lo de otro equipo (SYNC-011) | Escenario manual: editar sin red, reconectar, cerrar | No sobrescribe sin avisar | P1 |

### L · Rendimiento y recursos

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-L-01 | Arranque hasta ventana con datos reales | Cronometrar con `logs/app_*.log` (primera y última línea del arranque) | < 5 s sin red lenta | P2 |
| CHK-L-02 | Generación con 200 profesores y 4 zonas | `make bench` / `tests/benchmarks` | < 120 s | P2 |
| CHK-L-03 | Vistas con 3.000 guardias | `$PY -m pytest tests/audit/test_escalabilidad_vistas.py -q` | < 100 ms | P2 |
| CHK-L-04 | Memoria al cabo de una hora de uso | Observar `psutil` en `core/observability` o Monitor de Actividad | Sin crecimiento sostenido | P3 |
| CHK-L-05 | Tamaño del volcado y tiempo de subida | Medir `guardias_patio_data.json` | Documentado; comprimir si > 2 MB | P3 |
| CHK-L-06 | Registros no crecen sin límite | `ls -la logs/`, `faulthandler.log` | Rotación activa; `faulthandler.log` con tope | P3 |

### M · Observabilidad y soporte

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-M-01 | Un usuario puede enviar un diagnóstico sin saber de ficheros | Existe «Guardar informe de diagnóstico» en Ajustes o Acerca de | Existe | P2 |
| CHK-M-02 | Niveles de registro correctos (nada normal como `ERROR`) | `grep -rn 'logger.error("' src \| grep -viE "error|fall|no se pudo"` | Vacío | P3 |
| CHK-M-03 | prometheus-client y psutil aportan algo en escritorio | `grep -rn "prometheus\|get_metrics" src --include=*.py \| grep -v observability` | Se usan desde la UI o se retiran | P3 |
| CHK-M-04 | Excepciones no capturadas quedan registradas con hilo y versión | Leer `main.exception_hook` | Sí | P1 |
| CHK-M-05 | El registro de cambios (`CHANGELOG`) explica cada versión en lenguaje del usuario | Leer las últimas 5 entradas | Sí | P3 |

### N · Documentación y onboarding

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-N-01 | README instala como manda el proyecto (venv **fuera** de iCloud) | `grep -n "venv" README.md` | Cita `~/.venvs/guardias-patio` | P2 |
| CHK-N-02 | ADR recogen las decisiones de 2026-09 | `grep -c "2026-09" docs/ADR.md` | ≥ 5 (llavero, incremental, permuta, web estática, no multiusuario) | P3 |
| CHK-N-03 | Guía de primer arranque para un equipo nuevo (Windows) | Existe y cubre `known_hosts`, llavero y modo local | Sí | P2 |
| CHK-N-04 | Las skills del proyecto no contradicen al código | `/tests-locales`, `/build-*`, `/auditoria-desktop` leídas frente a Makefile y scripts | Sin contradicciones | P2 |
| CHK-N-05 | `docs/` sin ficheros de datos ni documentos de oficina | `$PY -m pytest tests/audit/test_sin_datos_reales_en_el_repositorio.py -q` | Verde | P0 |

### O · Entorno de desarrollo y agentes

| ID | Qué | Cómo | Pasa si | Sev. |
| --- | --- | --- | --- | --- |
| CHK-O-01 | Las instrucciones del asistente caben en una pantalla y no repiten otras fuentes | `wc -c .claude/claude.md .agents/*.md` | < 8 KB el principal; `.agents/` sólo el agente portable | P3 |
| CHK-O-02 | Ningún hook global ejecuta herramientas de otro stack | `python3 -c "import json;print(json.load(open('$HOME/.claude/settings.local.json')).get('hooks'))"` | Sin hooks web en un proyecto PyQt | P2 |
| CHK-O-03 | MCP de Obsidian apunta a **esta** bóveda y sin clave en claro | Ver [[22_RECURSOS_DE_IA]] §4 | `.mcp.json` por bóveda, clave por variable de entorno | P2 |
| CHK-O-04 | Skills instaladas: cada una tiene un uso declarado en [[22_RECURSOS_DE_IA]] | Leer la tabla | Todas clasificadas | P3 |
| CHK-O-05 | Barreras de la suite presentes | `grep -c "autouse=True" tests/conftest.py` | ≥ 4 | P1 |
| CHK-O-06 | Lista de permisos cubre lecturas y tests sin pedir confirmación | Leer `.claude/settings.local.json` | Sí | P3 |

### P · Verificaciones que sólo puede hacer una persona

| ID | Qué | Protocolo |
| --- | --- | --- |
| CHK-P-01 | Cierre en Windows al generar | [[06_CRASH_WINDOWS_GENERACION]] §5 |
| CHK-P-02 | Pantalla 1366×768 al 125 % | Abrir las diez vistas y los diálogos de configuración, permuta y envío; capturar |
| CHK-P-03 | Sesión con VoiceOver (macOS) y NVDA (Windows) | Recorrer Profesores → editar → guardar; Generar; Calendario → día; anotar lo que no se anuncia |
| CHK-P-04 | Primer arranque en un PC limpio | Sin `known_hosts`, sin `.env`: ¿llega a sincronizar sin ayuda? |
| CHK-P-05 | Instalador nuevo sobre versión anterior | Datos y contraseñas sobreviven; el `.env` queda sin contraseñas |

## 4. Gates de cierre de una ola

Una ola se da por cerrada cuando: todos los comandos de sus dimensiones se han ejecutado y anotado; cada hallazgo tiene ficha en [[30_REGISTRO_HALLAZGOS]]; los P0 tienen lote asignado en [[17_PLAN_DE_ATAQUE]]; y `$PY -m pytest tests/audit -q --no-cov` sigue verde.
