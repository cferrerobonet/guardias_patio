---
tags:
  - gestion-centro
  - auditoria
  - arquitectura
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Mejoras funcionales, calidad de código y escalabilidad

## 1. Mejoras funcionales propuestas (FUN)

Ordenadas por valor/esfuerzo. Sin severidad: son decisiones de producto.

| ID | Mejora | Valor | Esfuerzo | Depende de |
| --- | --- | --- | --- | --- |
| ~~FUN-001~~ **DESCARTADO v5.57.0** | ~~Panel "Estado del curso" como vista inicial~~ · Se implementó en v5.56.0 y se retiró por decisión de producto: sólo tenía algo que decir al montar el curso en septiembre; el resto del año era una pantalla de paso. **Lo que sí se conserva es la mitad valiosa**: el cálculo de prerrequisitos desde dominio (`PreflightGeneracionUseCase`), que alimenta el bloqueo del botón de generar y el aviso visible que enumera lo que falta | Alto | M | – |
| ~~FUN-002~~ ✅ **v5.67.0** | ~~Generación incremental~~ · congela lo anterior a la fecha, respeta las sustituciones posteriores y descuenta de las cuotas lo ya cubierto | Alto | L | CRW-003, ESC-002 |
| FUN-003 | **Edición manual en calendario**: mover/asignar una guardia con validación de restricciones | Alto | L | ESC-001 |
| ~~FUN-003b~~ ✅ **v5.75.0** | ~~Permutar una guardia entre dos profesores~~ · intercambio 1 a 1 desde el detalle del día; los totales no varían, así que el reparto sigue siendo equitativo. Cubre el caso concreto que se pedía sin abrir la edición libre | Alto | M | – |
| ~~FUN-004~~ ✅ **v5.63.0** | ~~Historial de generaciones y restauración~~ · copia automática antes de generar y de limpiar; listado de copias y restauración desde Importar/Exportar. La API de `db_manager` ya existía y no la llamaba nadie | Alto: red de seguridad | M | – |
| ~~FUN-005~~ ✅ **v5.76.0** | ~~Plantilla de curso~~ · al crear curso se hereda el claustro del anterior y los días no lectivos marcados a mano, desplazados un año. Zonas, recreos y ajustes de reparto no se copian porque son únicos para toda la aplicación. De paso: activar un curso ya mueve las fechas de la configuración | Alto en septiembre | M | – |
| ~~FUN-006~~ ✅ **v5.78.0 (parcial)** | ~~Emails en worker con vista previa y resultado por destinatario~~ · hecho, con una sola conexión SMTP y cancelación. Al hacerlo se descubrió que el envío estaba roto de raíz (`zona.nombre` en vez de `nombre_zona`). **Pendiente**: plantilla editable y adjuntar PDF individual e iCal —`send_calendar_pdf` ya sabe hacerlo, falta enlazarlo | Medio | M | CRW-003 |
| ~~FUN-007~~ ✅ **v5.79.0** | ~~Importación con validación previa (dry-run)~~ · informe fila a fila antes de escribir, con los repetidos del propio fichero distinguidos de los que ya están en la base de datos | Medio | S | – |
| FUN-008 | **Búsqueda y filtros persistentes** en tablas (profesor, zona, turno, estado) con chips | Medio | S | ESC-001 |
| FUN-009 | **Consulta web de solo lectura** para el profesorado (calendario propio, iCal suscribible) sobre la API FastAPI existente | Alto a medio plazo | L | ESC-004, SEC-002 |
| FUN-010 | **Tema oscuro y alto contraste** generados desde tokens | Medio | S tras VIS-001 | VIS-001 |
| FUN-011 | **Actualización automática en Windows** (asset `.exe` en release + descarga en banner) y notas de versión in-app | Medio | S | BLD-005 |
| ~~FUN-012~~ ✅ **v5.77.0** | ~~Deshacer en sustituciones/reasignaciones y en "Limpiar guardias" (papelera 24 h)~~ · el deshacer de sustituciones ya estaba (v5.63.0); ahora limpiar guarda las guardias en una papelera junto a la base de datos del usuario y un botón las devuelve durante 24 h | Medio | M | FUN-004 |
| ~~FUN-013~~ ✅ **v5.80.0** | ~~Diagnóstico accionable de slots sin cubrir~~ · por hueco, cuántos profesores excluyó cada regla dura y qué cambio mínimo lo desbloquea; sale en el panel de progreso de la generación | Alto para equidad | M | – |
| FUN-014 | Reparto de guardias con pesos por zona (dificultad) y preferencia de recreo, configurable | Medio | M | ESC-002 |

## 2. Calidad de código (COD)

Comandos y resultados en [[01_BASELINE_Y_ADAPTADOR]].

| ID | Sev. | Hallazgo | Evidencia | Recomendación |
| --- | --- | --- | --- | --- |
| COD-001 | P2 | Ruff: 355 avisos (119 E501, 95 I001, 64 F401, 26 F811, 13 F841, 11 E402, 4 F821); configuración `select/ignore` obsoleta | `ruff check src --statistics`; `pyproject.toml:[tool.ruff]` | `ruff check --fix` para I001/F401/F841; mover a `[tool.ruff.lint]`; añadir `B`, `UP`, `SIM`, `PL` gradualmente; gate en CI |
| COD-002 | P2 | Patrón comodín `except (ValueError, TypeError, OSError)` en ~40 sitios que no cubre `SQLAlchemyError`, `paramiko.SSHException`, `BusinessLogicError`; 67 `except Exception` | `grep` en `src` | Jerarquía de excepciones de app (`core/exceptions.py`) y captura por capa: dominio lanza, aplicación traduce, presentación muestra |
| COD-003 | P2 | Presentación consulta ORM y modelos directamente; servicios legacy importan ORM y Session | `generacion_panel.py:338-380` (`session.query(Profesor)`), `services/*` | Completar migración a casos de uso + DTOs; regla de import (`import-linter`) que prohíba `infrastructure.database.models` en `presentation` |
| COD-004 | P3 | Código muerto: `DashboardForm`, `HomeForm`, `AsignacionGuardiasForm` (379 líneas, con tests propios), `ui_styles.py`, `legacy_styles.py` parcial, loggers a módulos inexistentes, `.spec` duplicados | `ccleaner_main_window.py:139-166` vs `presentation/forms/__init__.py` | Borrar con sus tests o registrar en navegación; `vulture` como gate |
| COD-005 | P3 | Logging: `logger.error` para trazas informativas, DEBUG global, 646 ficheros `comparacion_cuotas_*.json` sin rotación, líneas triplicadas | `main.py:214,226`, `generar_guardias.py:_exportar_comparacion_cuotas`, `logs/` | Niveles correctos; rotación a 10 ficheros; un solo `setup_logging` |
| COD-006 | P3 | 25 `print(` en `src`, 7 TODO | `grep` | Sustituir por logger; TODO con ID de hallazgo |
| COD-007 | P2 | mypy estricto sólo en `domain`; `presentation/forms` y `dialogs` sin `disallow_untyped_defs` | `pyproject.toml:[tool.mypy]` | Subir un paquete por lote (`application` → `services` → `presentation/widgets`) |
| COD-008 | P3 | Módulos > 700 líneas: `ccleaner_theme.py` 822, `db_manager.py` 820, `sync_manager.py` 815, `vista_calendario.py` 809, `profesor_form.py` 798, `generacion_panel.py` 797 | `wc -l` | Dividir por responsabilidad (`sync_manager`: backend, exportador, auth; `generacion_panel`: panel, presentador de resultados, notificador) |

## 3. Escalabilidad y arquitectura objetivo (ESC)

### Situación

Clean Architecture híbrida con capa `services/` legacy (ADR-001). SQLite por usuario + JSON completo en SFTP. Una `Session` global. UI con `QTableWidget`. Solver CP-SAT con 8 workers y timeout fijo.

### Hallazgos

| ID | Sev. | Hallazgo | Evidencia | Recomendación |
| --- | --- | --- | --- | --- |
| ESC-001 | P2 | Tablas item-based que materializan todas las filas en el hilo GUI; heatmap O(profesores × semanas) | `profesor_table_helpers.py:13-72`, `panel_estadisticas.py:250-336`, `auditoria_guardias_form.py:124-187` | `QAbstractTableModel` + `QTableView`, `fetchMore`, proxy de filtrado; presupuesto: 1.000 profesores / 20.000 guardias sin bloqueo > 100 ms |
| ESC-002 | P2 | Modelo CP-SAT con booleanas por (profesor, slot) y 8 workers fijos; timeout 120 s no configurable; sin descomposición | `asignador_guardias_cpsat.py:505-509` | Crear variables sólo para pares elegibles (verificar), `num_workers = min(8, os.cpu_count())`, timeout y `relative_gap_limit` en Ajustes, descomponer por turno/trimestre con equidad acumulada, hints desde solución previa; medir con `tests/test_benchmark_cpsat.py` |
| ESC-003 | P2 | Sync exporta toda la BD a JSON y la sube cada 30 min y al cerrar; crece linealmente; bloquea el cierre | `sync_manager.py:515-603`, `ccleaner_main_window.py:262-270` | Export incremental por `updated_at` o subir el `.db` comprimido (`gzip`); sync sólo si hay cambios (hash); nunca en el hilo GUI |
| ESC-004 | P3 | Multiusuario real no existe: un usuario = una BD; el bloqueo de sesión impide trabajo simultáneo | `sync/session_lock.py` | Ruta incremental documentada en ADR: (1) API FastAPI como servicio local, (2) Postgres compartido opcional (`db_manager` ya contempla QueuePool), (3) UI que consume DTOs; conserva SQLite para modo local |
| ESC-005 | P2 | Caché global con invalidación por regex y TTL; riesgo de datos de otro curso tras cambio | `utils/cache.py`, `utils/repository_cache.py`, CHANGELOG (fix cbbfe4f) | Clave de caché que incluya `curso_id`; invalidación por evento de dominio; medir si la caché aporta algo real |
| ESC-006 | P3 | Arranque secuencial en el hilo GUI: migración multi-curso, adquisición de lock con reintentos, sync de arranque | `main.py:206-283` | Splash con worker y pasos visibles; timeouts; la ventana principal aparece en < 2 s |
| ESC-007 | P2 | Clave de caché basada en la dirección de memoria del objeto: 300 instancias en serie producen una sola clave, de modo que un caso de uso puede servir el resultado de otro durante el TTL. `cache_key_prefix` se acepta y se ignora | `utils/cache.py:59-87`, `utils/repository_cache.py:40-63` | Construir la clave con datos estables: nombre cualificado de la función, identidad del recurso y `curso_id`; nunca con `str(self)`. Excluir `self` como se excluye la sesión. Usar el prefijo o eliminarlo del API |

### Arquitectura objetivo (ADR propuesto)

```
presentation/   PyQt6 — sólo widgets, señales y DTOs. Sin ORM. Sin hilos propios salvo QThread genérico.
application/    Casos de uso + Preflight + DTOs + puertos (Progress, Notifier, Clock). Gestiona transacciones.
domain/         Entidades, VOs, reglas de equidad y restricciones puras (sin SQLAlchemy).
infrastructure/ Repos SQLAlchemy, UnitOfWork (session por operación), solver adapters (CP-SAT, v4), SFTP, SMTP, PDF.
api/            FastAPI sobre application/ (mismos casos de uso).
```

Reglas de dependencia verificadas con `import-linter` en CI. Cada hilo obtiene su `UnitOfWork`; el progreso viaja por un puerto `ProgressSink` cuya implementación Qt vive en `presentation`.

## 4. Seguridad y privacidad (SEC)

| ID | Sev. | Hallazgo | Evidencia | Recomendación |
| --- | --- | --- | --- | --- |
| SEC-001 | P2 | Credenciales SFTP/SMTP en `.env` en texto plano en el directorio de la app | `initial_config_dialog.py:641-665`, `main.py:120-125` | `keyring` (Keychain/Credential Manager) con fallback cifrado; nunca loguear host/usuario completos |
| SEC-002 | P3 | `api_secret_key` vacío por defecto | `settings.py:151` | Fail-closed: la API no arranca sin secreto; test |
| SEC-003 | P3 | Bandit: 3 medios, 26 bajos | `bandit -r src` | Revisar los 3 medios (bind, tmp, subprocess) y documentar los aceptados |

## 5. Positivos a preservar

- Casos de uso y DTOs ya existen para profesores, zonas, configuración, perfiles y generación.
- Suite `tests/compliance` verifica restricciones duras del solver con escenarios: patrón excelente para FUN-013.
- Backups automáticos con retención en `db_manager`.
- `with_metrics`, `usage_log` y `health` dan observabilidad barata.
- Lazy loading de vistas y `WorkerThread` genérico con cancelación.
