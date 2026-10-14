---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Plan maestro de auditoría — app de escritorio Python/PyQt6/SQLAlchemy/OR-Tools

Este plan enumera **todo lo que debe auditarse** en una aplicación de escritorio con este stack, adaptado a Guardias de Patio. Cada ítem tiene un ID estable (`CHK-<dimensión>-<n>`) que se marca como `OK`, `HALLAZGO:<ID>`, `N/A:<motivo>` o `NO VERIFICADO:<motivo>` en la columna *Estado*. Los IDs de hallazgo remiten a [[30_REGISTRO_HALLAZGOS]].

> [!TIP] Protocolo
> El protocolo de seis olas, la taxonomía y las plantillas viven en `.agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md`. Este documento es su instancia para escritorio: sustituye las dimensiones web (PWA, cookies, navegadores) por hilos, empaquetado, sesión de BD, DPI y sistema operativo.

## Dimensiones y pesos

| Dim. | Nombre | Peso | Por qué importa en este proyecto |
| --- | --- | ---: | --- |
| A | Experiencia de uso: casos de uso, caminos dorados, clics, guardarraíles | 25 % | Petición explícita; la app la usa una jefatura con poco tiempo y flujos secuenciales |
| B | Consistencia visual y sistema de diseño | 15 % | Debe percibirse profesional, elegante y con patrones lógicos de un solo autor |
| C | Fiabilidad: hilos, sesión de BD, cierres abruptos, cancelación | 15 % | Cierre en Windows al terminar el cálculo |
| D | Funcionalidad y reglas de negocio (equidad, restricciones, ausencias) | 10 % | Núcleo del valor |
| E | Calidad de código y arquitectura | 10 % | Escalabilidad pedida |
| F | Tests y QA | 10 % | ~2.400 tests pero con huecos en flujos reales y hilos |
| G | Build, release y actualización (exe/dmg) | 5 % | Distribución a Windows y macOS |
| H | Rendimiento y escalabilidad (datos, solver, sync) | 5 % | Centros grandes, varios cursos |
| I | Seguridad, privacidad y datos personales | 3 % | Credenciales SFTP/SMTP, emails de profesorado |
| J | Accesibilidad (EN 301 549 / WCAG por equivalencia) | 2 % | Ya auditada en Ola 4 previa; se hereda |

## A · Experiencia de uso

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-A-01 | Inventario de casos de uso con actor, objetivo, precondiciones y resultado | HALLAZGO:UXF-001 (documentado en 03) |
| CHK-A-02 | Camino dorado por caso de uso con nº de clics/teclas actual y objetivo | HALLAZGO:UXF-003/010 |
| CHK-A-03 | Secuencia obligatoria de configuración visible y forzada por la UI (curso → ajustes → zonas → profesores → cuotas → generar) | HALLAZGO:UXF-001/002 |
| CHK-A-04 | Cada acción bloqueada explica por qué y enlaza a la solución (no solo tooltip) | HALLAZGO:UXF-008 |
| CHK-A-05 | Estado vacío de cada vista con llamada a la acción | NO VERIFICADO: requiere sesión manual por vista |
| CHK-A-06 | Confirmaciones sólo para acciones destructivas o irreversibles; resto inline | HALLAZGO:UXF-003 |
| CHK-A-07 | Acciones destructivas separadas visual y espacialmente de la primaria | HALLAZGO:UXF-006 |
| CHK-A-08 | Protección de cambios sin guardar en navegación, cierre y cambio de curso | HALLAZGO:UXA-004 |
| CHK-A-09 | Feedback de progreso para toda operación > 1 s, cancelable y con resultado persistente | HALLAZGO:CRW-004/007 |
| CHK-A-10 | Atajos de teclado por sección y acción primaria; Escape/Enter coherentes | HALLAZGO:UXF-011 |
| CHK-A-11 | Valores por defecto inteligentes (mes actual, último directorio, último profesor) | HALLAZGO:UXF-010 |
| CHK-A-12 | Deshacer o restaurar en operaciones con impacto (sustituciones, limpiar guardias) | HALLAZGO:FUN-004/012 |
| CHK-A-13 | Cambio de curso refresca todas las vistas y lo comunica una vez | HALLAZGO:UXA-007 |
| CHK-A-14 | Primer arranque sin servidor SFTP permite usar la app en local | HALLAZGO:UXF-005 |
| CHK-A-15 | Terminología única (guardia, slot, recreo, cuota, sustitución) en UI, PDF y logs | HALLAZGO:VIS-006 (parcial) |
| CHK-A-16 | Microcopy de errores: qué pasó, por qué, qué hacer | HALLAZGO:UXA-006 |
| CHK-A-17 | Cierre de la app: sincroniza sin bloquear y sin perder datos | OK parcial (worker + diálogo); ver CRW-005 |

## B · Consistencia visual y sistema de diseño

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-B-01 | Una sola cascada de estilos (QSS global generado desde tokens) | HALLAZGO:VIS-001 |
| CHK-B-02 | Paleta única semántica; cero hex fuera de tokens | HALLAZGO:VIS-002 |
| CHK-B-03 | Tipografía: familia por SO con fallback, escala de 5 tamaños, mínimo 12 px | HALLAZGO:VIS-003 |
| CHK-B-04 | Iconografía vectorial monocroma; sin emojis como iconos | HALLAZGO:VIS-004 |
| CHK-B-05 | Componentes con contrato (Button, FormField, Table, Panel, Toolbar, Feedback, Dialog, EmptyState) | HALLAZGO:VIS-007/008 |
| CHK-B-06 | Estados default/hover/focus/active/disabled/loading/error en todos los controles | HALLAZGO:UXA-002 |
| CHK-B-07 | Jerarquía: un título por vista, un botón primario por vista | HALLAZGO:VIS-006/007 |
| CHK-B-08 | Densidad y espaciado en múltiplos de 4 px desde tokens | HALLAZGO:VIS-001 (parcial) |
| CHK-B-09 | Layout adaptable a 1366×768 y escalado 125-200 % | HALLAZGO:UXA-001/VIS-009 |
| CHK-B-10 | Contraste ≥ 4,5:1 texto y ≥ 3:1 bordes/foco | HALLAZGO:UXA-010 |
| CHK-B-11 | Un solo lenguaje de feedback (inline, toast, modal) con reglas | HALLAZGO:VIS-008 |
| CHK-B-12 | Identidad visual propia y coherente entre ventana, diálogos, PDF y emails | HALLAZGO:VIS-010 |

## C · Fiabilidad, hilos y sesión de BD

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-C-01 | Ningún widget se toca fuera del hilo GUI (incluidos handlers de logging) | HALLAZGO:CRW-002 |
| CHK-C-02 | Ninguna señal Qt se emite desde hilos nativos ajenos (OR-Tools, paramiko) | HALLAZGO:CRW-001 |
| CHK-C-03 | Cancelación cooperativa sin lanzar excepciones a través de C++ | HALLAZGO:CRW-004 |
| CHK-C-04 | Una `Session` SQLAlchemy por hilo; la GUI recibe DTOs | HALLAZGO:CRW-003 |
| CHK-C-05 | `sys.excepthook` seguro en cualquier hilo; hilos secundarios capturan `Exception` | HALLAZGO:CRW-005 |
| CHK-C-06 | `faulthandler` y volcado nativo en builds congelados | HALLAZGO:CRW-006 |
| CHK-C-07 | Logging configurado una vez; sin handlers a `sys.stdout` en modo windowed | HALLAZGO:CRW-006 |
| CHK-C-08 | Transacciones explícitas en casos de uso (commit/rollback) | HALLAZGO:CRW-009 |
| CHK-C-09 | Operaciones de red (SFTP/SMTP/GitHub) siempre fuera del hilo GUI y con timeout | HALLAZGO:CRW-007 |
| CHK-C-10 | Bloqueo de sesión única y heartbeat robustos ante pérdida de red | NO VERIFICADO: requiere entorno SFTP |
| CHK-C-11 | Recuperación ante BD bloqueada/corrupta: backups automáticos y restauración desde UI | OK parcial (backups en db_manager; sin restauración desde UI → FUN-004) |
| CHK-C-12 | Migraciones Alembic sobre fichero real en cada arranque, idempotentes | NO VERIFICADO: sólo tests en memoria (QA-006) |

## D · Funcionalidad y reglas de negocio

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-D-01 | Restricciones duras (1 guardia/día, ausencias, fechas inicio/fin, turnos, recreos permitidos) verificadas por suite compliance | OK (`tests/compliance`) |
| CHK-D-02 | Equidad: cuotas por % jornada y tutoría; desviación máxima documentada | OK parcial (métricas en generación) |
| CHK-D-03 | Cobertura de todos los slots o diagnóstico accionable de los no cubiertos | HALLAZGO:UXF-002 (diagnóstico genérico) |
| CHK-D-04 | Ausencias: solapamientos, sustituto elegible, historial y reversión | OK parcial (FUN-012 propone deshacer) |
| CHK-D-05 | Multi-curso: aislamiento de datos por curso y migración | HALLAZGO:UXA-007 |
| CHK-D-06 | Exportaciones (PDF, iCal, JSON) paridad con BD | NO VERIFICADO: requiere comparación fichero a fichero |
| CHK-D-07 | Importación Excel: validación previa, duplicados, mapeo | HALLAZGO:FUN-007 |
| CHK-D-08 | Emails: plantilla, preview, envío en worker, errores por destinatario | HALLAZGO:FUN-006 |

## E · Calidad de código y arquitectura

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-E-01 | Lint limpio (ruff) y formato único | HALLAZGO:COD-001 |
| CHK-E-02 | Cero nombres indefinidos / imports rotos | HALLAZGO:CRW-008 |
| CHK-E-03 | Excepciones: capturar lo que se puede manejar; nunca `except (ValueError, TypeError, OSError)` como comodín | HALLAZGO:COD-002 |
| CHK-E-04 | Capas: presentación sin ORM ni queries; servicios sin Qt | HALLAZGO:COD-003 |
| CHK-E-05 | Código muerto eliminado (forms, estilos, loggers) | HALLAZGO:COD-004 |
| CHK-E-06 | Logging con niveles correctos, rotación y sin artefactos ilimitados | HALLAZGO:COD-005 |
| CHK-E-07 | Tipado: mypy verde en domain/application; progresivo en presentation | HALLAZGO:COD-007 |
| CHK-E-08 | Tamaño de módulos < 500 líneas o justificado | HALLAZGO:COD-004 (parcial) |
| CHK-E-09 | ADR actualizados y decisiones de escalabilidad registradas | HALLAZGO:ESC-004 |

## F · Tests y QA

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-F-01 | Entorno reproducible (`requirements`, intérprete, `make test` funciona en limpio) | HALLAZGO:QA-001 |
| CHK-F-02 | Suite verde sin fallos tolerados ni skips amplios | HALLAZGO:QA-005 |
| CHK-F-03 | Tests de la UI real registrada (no de formularios muertos) | HALLAZGO:QA-003 |
| CHK-F-04 | Tests de afinidad de hilos y de cancelación | HALLAZGO:QA-004 (creados en `tests/audit/`) |
| CHK-F-05 | Tests con BD SQLite en fichero, PRAGMAs reales y migraciones | HALLAZGO:QA-006 (fixture creada) |
| CHK-F-06 | Ratchets de consistencia visual (hex, font-size, accesibleName) | Creados en `tests/audit/test_consistencia_visual_ratchet.py` |
| CHK-F-07 | E2E de la superficie web (FastAPI) con Playwright | HALLAZGO:QA-007 (suite creada) |
| CHK-F-08 | Tests de build (spec válido, versión única, artefacto arranca) | HALLAZGO:BLD-001/003 |
| CHK-F-09 | Cobertura por riesgo (generación, sync, sesión) > cobertura global | NO VERIFICADO: cov desactivado en esta ejecución por tiempo |

## G · Build, release y actualización

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-G-01 | Un script canónico por plataforma, versión leída de una sola fuente | HALLAZGO:BLD-002/003 |
| CHK-G-02 | Ficheros `.spec` versionados; `make clean` no destruye entradas del build | HALLAZGO:BLD-001 |
| CHK-G-03 | CI que ejecuta tests, lint y build en Windows y macOS | HALLAZGO:BLD-004 |
| CHK-G-04 | Firma y notarización macOS; firma Windows | HALLAZGO:BLD-004 |
| CHK-G-05 | Actualizador funciona en ambas plataformas | HALLAZGO:BLD-005 |
| CHK-G-06 | Variante de build con consola para diagnóstico | HALLAZGO:BLD-007 |
| CHK-G-07 | Instalador Windows: privilegios mínimos, cierre de instancias, desinstalación limpia | HALLAZGO:BLD-006 |

## H · Rendimiento y escalabilidad

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-H-01 | Tablas con modelo (QTableView) y carga por páginas | HALLAZGO:ESC-001 |
| CHK-H-02 | Solver: variables sólo para pares elegibles, workers = CPUs, timeout configurable, descomposición | HALLAZGO:ESC-002 |
| CHK-H-03 | Sync incremental o comprimida; no bloquear GUI | HALLAZGO:ESC-003 |
| CHK-H-04 | Arranque < 3 s percibido; trabajo pesado en splash/worker | HALLAZGO:ESC-006 |
| CHK-H-05 | Caché con invalidación por evento, no por regex | HALLAZGO:ESC-005 |
| CHK-H-06 | Ruta a multiusuario real (API + BD compartida) documentada | HALLAZGO:ESC-004 |

## I · Seguridad y privacidad

| ID | Ítem | Estado |
| --- | --- | --- |
| CHK-I-01 | Credenciales SFTP/SMTP fuera de texto plano (keyring del SO) | HALLAZGO:SEC-001 |
| CHK-I-02 | API: secreto obligatorio, fail-closed, rate limit | HALLAZGO:SEC-002 |
| CHK-I-03 | Datos personales (emails profesorado) minimizados en logs, JSON de sync y exportaciones | NO VERIFICADO: requiere revisión de `data_exporter` y plantillas |
| CHK-I-04 | Análisis estático de seguridad (bandit) sin medios/altos | HALLAZGO:SEC-003 |
| CHK-I-05 | Dependencias con vulnerabilidades conocidas (pip-audit) | NO VERIFICADO: pip-audit no instalado |

## J · Accesibilidad

Se hereda íntegramente el paquete Ola 4 (`_work/paquete_ux_accesibilidad.md`, UXA-001…014). Gate pendiente: sesión manual con NVDA (Windows) y VoiceOver (macOS).

## Gates de cierre por dimensión

- Ninguna dimensión se certifica con `NO VERIFICADO` bloqueantes.
- Dimensión C se certifica sólo tras reproducir la generación completa en Windows con el build congelado y `faulthandler` activo, sin cierres en 10 ejecuciones consecutivas.
- Dimensión A y B se certifican con la matriz de caminos dorados dentro de presupuesto de clics y con los ratchets visuales en cero.
