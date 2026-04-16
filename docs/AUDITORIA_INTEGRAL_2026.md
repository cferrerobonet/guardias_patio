# Auditoría Integral — Guardias de Patio

**Fecha**: 16 de abril de 2026  
**Versión analizada**: 3.2.1  
**Alcance**: Análisis completo de arquitectura, seguridad, base de datos, performance, UX/UI, testing, observabilidad, escalabilidad, resiliencia y buenas prácticas.

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura](#2-arquitectura)
3. [Seguridad y Encriptación](#3-seguridad-y-encriptación)
4. [Base de Datos y Normalización](#4-base-de-datos-y-normalización)
5. [Performance y Optimización](#5-performance-y-optimización)
6. [Caching](#6-caching)
7. [Procesamiento Asíncrono](#7-procesamiento-asíncrono)
8. [Escalabilidad y Resiliencia](#8-escalabilidad-y-resiliencia)
9. [API REST](#9-api-rest)
10. [Testing](#10-testing)
11. [Observabilidad](#11-observabilidad)
12. [UX/UI y Accesibilidad](#12-uxui-y-accesibilidad)
13. [Control de Acceso y Multi-tenancy](#13-control-de-acceso-y-multi-tenancy)
14. [Idempotencia](#14-idempotencia)
15. [Alta Disponibilidad](#15-alta-disponibilidad)
16. [Organización de Archivos y Carpetas](#16-organización-de-archivos-y-carpetas)
17. [Funcionalidades Pendientes de Implementar](#17-funcionalidades-pendientes-de-implementar)
18. [Refactorización y Código Huérfano](#18-refactorización-y-código-huérfano)
19. [Sanitización y Robustez del Código](#19-sanitización-y-robustez-del-código)
20. [Preparación para Migración Web](#20-preparación-para-migración-web)
21. [Reparabilidad y Diagnóstico de Errores](#21-reparabilidad-y-diagnóstico-de-errores)
22. [Sugerencias de Mejora General](#22-sugerencias-de-mejora-general)
23. [Roadmap de Implementación](#23-roadmap-de-implementación)

---

## 1. Resumen Ejecutivo

| Dimensión | Estado | Puntuación |
|---|---|---|
| Arquitectura | Clean Architecture híbrida con deuda técnica | ★★★☆☆ |
| Seguridad | Múltiples vulnerabilidades críticas | ★★☆☆☆ |
| Base de datos | Funcional pero con violaciones de normalización | ★★★☆☆ |
| Performance | Aceptable para la escala actual, con N+1 críticos | ★★★☆☆ |
| Caching | Implementado pero con bug crítico | ★★☆☆☆ |
| Async | GUI bien resuelto, SFTP bloqueante | ★★★☆☆ |
| Escalabilidad | Diseñada para uso local, no escala horizontalmente | ★★☆☆☆ |
| API REST | Solo lectura, sin auth, con fugas de info | ★★☆☆☆ |
| Testing | 990 tests, 39.75% coverage | ★★★☆☆ |
| Observabilidad | Prometheus + structlog bien diseñados | ★★★★☆ |
| UX/UI | Funcional, sin accesibilidad formal | ★★★☆☆ |
| Control de acceso | Autenticación débil, sin autorización granular | ★★☆☆☆ |
| Multi-tenancy | Aislamiento por BD SQLite — correcto | ★★★★☆ |
| Idempotencia | Parcial en migraciones y repositorios | ★★★☆☆ |
| Organización de archivos | Archivos mal ubicados, duplicaciones, ficheros gigantes | ★★☆☆☆ |
| Features completas | Varias funcionalidades a medio implementar | ★★★☆☆ |
| Código huérfano | 16+ ficheros muertos, 2500+ líneas sin uso | ★☆☆☆☆ |
| Sanitización | print() de debug, except:pass, pickle inseguro | ★★☆☆☆ |
| Preparación web | FastAPI existe pero cubre ~15%; servicios portables | ★★★☆☆ |
| Reparabilidad | Logging dual, sin error boundaries, diagnóstico parcial | ★★☆☆☆ |

**Total de hallazgos**: 4 críticos, 10 altos, 12 medios, 8 bajos (original) + 8 críticos, 15 altos, 16 medios, 4 bajos (refactorización/sanitización) + hallazgos de organización/features/web.

---

## 2. Arquitectura

### 2.1 Patrón

Clean Architecture híbrida + DDD táctico. Capas:

| Capa | Directorio | Responsabilidad |
|---|---|---|
| Core | `src/core/` | Excepciones, logging, observabilidad, paths |
| Domain | `src/domain/` | Entidades, value objects, interfaces de repositorio, servicios de dominio |
| Application | `src/application/` | Use cases (CQRS-like), DTOs, factories de DI |
| Infrastructure | `src/infrastructure/` | Repositorios SQLAlchemy, mappers ORM↔Entity, modelos BD |
| Services | `src/services/` | Lógica "legacy": algoritmos, exportadores, ML, email |
| Presentation | `src/presentation/` | GUI PyQt6 |
| API | `src/api/` | REST FastAPI |
| Config | `src/config/` | Settings Pydantic |
| Database | `src/database/` | Gestión conexiones, migraciones |
| Sync | `src/sync/` | Sincronización SFTP, bloqueo de sesión |
| Utils | `src/utils/` | Cache, constantes, helpers |

### 2.2 Hallazgos

| ID | Hallazgo | Severidad | Detalle |
|---|---|---|---|
| ARQ-01 | **Servicios bypasean repositorios** | ALTA | 20+ servicios en `src/services/` importan modelos ORM y hacen `session.query()` directamente, rompiendo la separación de capas |
| ARQ-02 | **Presentación accede a BD directamente** | ALTA | 15+ widgets en `src/presentation/` ejecutan queries SQLAlchemy directas en vez de pasar por use cases |
| ARQ-03 | **3 repositorios retornan modelos ORM** | ALTA | `AusenciaRepository`, `ConfiguracionRepository` y `CursoEscolarRepository` retornan modelos ORM en vez de entidades de dominio |
| ARQ-04 | **DI manual sin framework** | MEDIA | Factories manuales en `application/factories.py`. Funcional pero propenso a errores al crecer |
| ARQ-05 | **Dos ventanas principales coexisten** | MEDIA | `main_window.py` (tabs legacy) y `ccleaner_main_window.py` (sidebar moderna) — deuda técnica visual |
| ARQ-06 | **Capa `models/` es re-export legacy** | BAJA | Solo redirige a `infrastructure/database/models.py` — eliminar tras migrar imports |

### 2.3 Recomendaciones

- [ ] Migrar los 20+ servicios legacy para que usen repositorios de dominio en vez de `session.query()`
- [ ] Crear entidades de dominio para Ausencia, Configuracion y CursoEscolar con sus mappers
- [ ] Eliminar acceso directo a BD desde la capa de presentación → inyectar use cases
- [ ] Eliminar `main_window.py` legacy cuando la nueva UI esté completa
- [ ] Evaluar `dependency-injector` como framework DI

---

## 3. Seguridad y Encriptación

### 3.1 Hallazgos Críticos

| ID | Hallazgo | Severidad | Archivo |
|---|---|---|---|
| SEC-01 | **SHA-256 sin salt para contraseñas** | CRÍTICA | `sync/sync_manager.py`, `use_cases/perfil/cambiar_password.py` |
| SEC-02 | **Base64 como "encriptación" de credenciales SFTP/SMTP** | CRÍTICA | `services/exportador.py` |
| SEC-03 | **API REST sin autenticación** | CRÍTICA | `api/main.py` |
| SEC-04 | **Código de recuperación en texto plano en users.json** | CRÍTICA | `presentation/forms/forgot_password_dialog.py` |

**SEC-01**: `hashlib.sha256(password.encode()).hexdigest()` — vulnerable a rainbow tables y fuerza bruta con GPU. El propio código tiene un comentario "En producción, usar bcrypt/argon2" que nunca se implementó.

**SEC-02**: `base64.b64encode()` no es cifrado. Las credenciales en `sftp_config.json` y `smtp_config.json` son trivialmente reversibles.

**SEC-03**: Todos los endpoints son públicos. Combinado con `allow_origins=["*"]` + `allow_credentials=True` y `host="0.0.0.0"`, cualquier dispositivo en la red accede a datos de profesores/guardias.

**SEC-04**: El código de recuperación se guarda en texto plano Y hasheado en `data/users.json`, sin TTL de expiración.

### 3.2 Hallazgos Altos

| ID | Hallazgo | Severidad | Detalle |
|---|---|---|---|
| SEC-05 | **Contraseña mínima: 4 caracteres** | ALTA | Sin requisitos de complejidad |
| SEC-06 | **Sin protección brute force en login** | ALTA | Sin lockout, sin delay, sin CAPTCHA |
| SEC-07 | **Credenciales reales en config JSON** | ALTA | Host SFTP de 1&1 IONOS y username expuestos |
| SEC-08 | **API expone `str(e)` en errores 500** | ALTA | Fuga de rutas, esquema BD, versiones |
| SEC-09 | **Uvicorn escucha en 0.0.0.0** | ALTA | API expuesta a toda la red |

### 3.3 Hallazgos Medios

| ID | Hallazgo | Severidad | Detalle |
|---|---|---|---|
| SEC-10 | XSS potencial en templates email HTML | MEDIA | Username sin escapar en HTML |
| SEC-11 | Path traversal en LocalSyncBackend | MEDIA | `remote_path` sin sanitizar |
| SEC-12 | `users.json` sin permisos restrictivos | MEDIA | Guardado con permisos por defecto (644) |
| SEC-13 | Valores fallback en config exponen infraestructura | MEDIA | Host SFTP y username como defaults |
| SEC-14 | Username sin validación en registro | MEDIA | Acepta cualquier string tras `strip()` |

### 3.4 Buenas Prácticas Detectadas

- ✅ `paramiko.RejectPolicy()` — previene MITM en SFTP
- ✅ `server.starttls()` para SMTP
- ✅ Secretos en `.gitignore` (`.env`, configs JSON)
- ✅ Aislamiento de BD por usuario
- ✅ SQLAlchemy ORM con queries parametrizadas (sin inyección SQL)
- ✅ `secrets.token_urlsafe(32)` para tokens de recuperación

### 3.5 Recomendaciones

- [ ] **P0** — Migrar a `bcrypt` o `argon2id` para hashing de contraseñas con migración de hashes existentes
- [ ] **P0** — Reemplazar Base64 por `cryptography.fernet` o keyring del SO (`keyring` package)
- [ ] **P0** — Añadir autenticación JWT/API-key a la API REST
- [ ] **P0** — Eliminar recovery code en texto plano de `users.json`, guardar solo hash + TTL
- [ ] **P1** — Política de contraseñas: mínimo 8 chars + mayúscula + número + símbolo
- [ ] **P1** — Implementar lockout: 5 intentos → bloqueo 15 min con delay progresivo
- [ ] **P1** — Cambiar `host="0.0.0.0"` a `host="127.0.0.1"` en uvicorn
- [ ] **P1** — Reemplazar `str(e)` por mensajes genéricos en errores API
- [ ] **P2** — Escapar HTML en plantillas de email (`html.escape()`)
- [ ] **P2** — Validar y sanitizar `remote_path` contra path traversal
- [ ] **P2** — Establecer `chmod 600` en `users.json`
- [ ] **P2** — Eliminar valores reales de infraestructura en defaults de config
- [ ] **P2** — Validar username con regex whitelist (`[a-zA-Z0-9._-]`)

---

## 4. Base de Datos y Normalización

### 4.1 Esquema (6 tablas)

| Tabla | Campos clave |
|---|---|
| `cursos_escolares` | anio_inicio, anio_fin, activo, cerrado |
| `profesores` | nombre_completo, turno, horas_contrato, tutor, activo, zona_preferida_id |
| `zonas` | nombre_zona, fecha_inicio/fin |
| `configuracion` | fechas curso, recreos, festivos, algoritmo |
| `guardias` | curso_id, profesor_id, fecha, turno, recreo, zona_id |
| `ausencias` | profesor_id, fecha_inicio/fin, tipo, motivo |

### 4.2 Violaciones de Normalización (1NF)

| Tabla | Columna | Problema |
|---|---|---|
| `profesores` | `dias_semana_permitidos` | JSON en campo Text: `[0,1,2,3,4,5,6]` |
| `profesores` | `recreos_permitidos` | JSON en campo Text: `[1,2]` o dict `{"0":[1,2]}` |
| `configuracion` | `dias_no_lectivos_personalizados` | JSON en Text: `["YYYY-MM-DD",...]` |
| `configuracion` | `recreos_config` | JSON complejo en Text: `[{id, etiqueta, turno, hora, zonas}]` |

El `ProfesorMapper` tiene **130+ líneas** de código defensivo con `json.loads` → `ast.literal_eval` → fallbacks para parsear estos campos, evidenciando formatos inconsistentes históricos.

### 4.3 Foreign Keys y Constraints

| ID | Hallazgo | Severidad |
|---|---|---|
| DB-01 | `guardias.profesor_id` nullable — una guardia sin profesor no tiene sentido | ALTA |
| DB-02 | `guardias.zona_id` nullable — una guardia sin zona no tiene sentido | ALTA |
| DB-03 | Sin `ON DELETE CASCADE` en profesor→guardias/ausencias | ALTA |
| DB-04 | Sin UniqueConstraint en `guardias(fecha, turno, recreo, zona_id, profesor_id)` | ALTA |
| DB-05 | Sin CheckConstraint en `turno`, `ausencias.tipo`, `recreo`, `porcentaje_jornada` | MEDIA |
| DB-06 | `datetime.utcnow` como default — deprecated en Python 3.12+ | MEDIA |
| DB-07 | `guardias.curso_id` nullable (justificado como "migración gradual" pero sin cleanup) | MEDIA |

### 4.4 Índices

**Existentes** (buenos):
- `idx_guardias_profesor`, `idx_guardias_zona`, `idx_guardias_fecha`, `idx_guardias_turno`
- `idx_guardias_fecha_turno` (compuesto)
- `idx_ausencias_profesor`, `idx_ausencias_fechas`, `idx_ausencias_activa`

**Faltantes**:
- `guardias.curso_id` — se filtra frecuentemente por curso
- `guardias(fecha, turno, recreo)` — compuesto triple, usado en `find_by_fecha_turno_recreo()`
- `profesores.turno` — filtro habitual
- `profesores.activo` — filtro muy frecuente
- `ausencias(profesor_id, fecha_inicio, fecha_fin, activa)` — compuesto para queries de rango
- `zonas.nombre_zona` — para `find_by_nombre()`

### 4.5 Migraciones (Alembic)

16 migraciones con estos problemas:

| ID | Hallazgo | Severidad |
|---|---|---|
| DB-08 | Migración duplicada vacía `b939a8969a45` → `0122b6bbdc61` | BAJA |
| DB-09 | Columnas `fecha_inicio/fin` añadidas a zonas en 2 migraciones diferentes | MEDIA |
| DB-10 | Downgrade vacío en `a1b2c3d4e5f6` — rollback imposible | ALTA |
| DB-11 | Inconsistencia modelo/migración: ORM dice `cerrado`, migración crea `archivado` | ALTA |
| DB-12 | `create_user_database()` no ejecuta Alembic stamp — BD sin versión | ALTA |

### 4.6 Database Manager

| ID | Hallazgo | Severidad |
|---|---|---|
| DB-13 | **Triple estrategia de init**: Alembic + `create_all` + SQL directo — duplicación de lógica | ALTA |
| DB-14 | Variables globales mutables sin thread-safety (`_current_engine`, etc.) | ALTA |
| DB-15 | `set_sqlite_pragma` definida 3 veces — código duplicado | BAJA |
| DB-16 | `get_db_session()` auto-commit al salir del `with` — puede ser peligroso | MEDIA |

### 4.7 Recomendaciones

- [ ] Normalizar campos JSON a tablas relacionales (`profesor_dias_semana`, `profesor_recreos`, `recreos_config`)
- [ ] Añadir `NOT NULL` a `guardias.profesor_id` y `guardias.zona_id`
- [ ] Añadir `ON DELETE CASCADE` en profesor→guardias y profesor→ausencias
- [ ] Añadir UniqueConstraint en guardias para evitar asignaciones duplicadas
- [ ] Añadir CheckConstraints para `turno`, `tipo` de ausencia, `recreo >= 1`
- [ ] Crear índices faltantes (curso_id, turno, activo, compuesto triple)
- [ ] Unificar init de BD: solo Alembic, eliminar `_apply_direct_migrations()`
- [ ] Reemplazar `datetime.utcnow` por `datetime.now(timezone.utc)`
- [ ] Resolver inconsistencia `cerrado` vs `archivado`
- [ ] Añadir locks o thread-local storage en `db_manager.py`

---

## 5. Performance y Optimización

### 5.1 N+1 Queries

| ID | Hallazgo | Severidad | Detalle |
|---|---|---|---|
| PERF-01 | **N+1 en API `/api/guardias`** | CRÍTICA | Loop ejecuta 2 queries extra por guardia (zona + profesor). Con limit=100 → ~200 queries adicionales |
| PERF-02 | N+1 en `ProfesorRepository.get_all()` | MEDIA | Sin eager loading para `guardias` y `zona_preferida` |
| PERF-03 | N+1 en `sistema_sugerencias_automaticas.py` | MEDIA | `db.query(Profesor).get(id)` individual en loops |

### 5.2 Queries no Optimizadas

| ID | Hallazgo | Severidad |
|---|---|---|
| PERF-04 | `find_disponibles_en_fecha()` carga todos los profesores del turno y filtra en Python | MEDIA |
| PERF-05 | `.count() > 0` en vez de `.exists()` en varios repos | BAJA |
| PERF-06 | `get_all()` sin paginación en todos los repositorios | BAJA (escala actual) |

### 5.3 Buenas Prácticas Existentes

- ✅ `joinedload` correcto en `GuardiaRepository`, `exportador_pdf.py`, `icalendar_service.py`
- ✅ `PRAGMA journal_mode=DELETE` justificado por compatibilidad OneDrive
- ✅ `NullPool` para SQLite (correcto)
- ✅ Query optimizer helper disponible (`src/utils/query_optimizer.py`)

### 5.4 Recomendaciones

- [ ] **P0** — Añadir `joinedload` en el endpoint `/api/guardias` para zona y profesor
- [ ] Añadir `joinedload(Profesor.zona_preferida)` en `get_all()`
- [ ] Mover filtro de disponibilidad a la query SQL
- [ ] Reemplazar `.count() > 0` por `.exists()` o `.first() is not None`

---

## 6. Caching

### 6.1 Implementación

Sistema in-memory propio con `OrderedDict` LRU en `src/utils/cache.py`:
- TTL configurable (default 300s)
- Invalidación por patrón/regex
- LRU eviction (max 1000 entradas)
- Métricas hit/miss por función

### 6.2 Hallazgos

| ID | Hallazgo | Severidad |
|---|---|---|
| CACHE-01 | **`repository_cache.py` re-crea el decorador en cada llamada** — anula completamente el caché | CRÍTICA |
| CACHE-02 | **Cache no thread-safe** — `OrderedDict` global sin locks, usado con `QThread` | ALTA |
| CACHE-03 | Cache volátil — se pierde al reiniciar la app | BAJA |

**CACHE-01 detalle**: En `repository_cache.py` línea ~58, `cached_func = cache_query(ttl=ttl)(func)` crea un nuevo wrapper sin estado previo en cada invocación. El caché nunca retiene datos entre llamadas.

### 6.3 Recomendaciones

- [ ] **P0** — Corregir `repository_cache.py` para cachear la función decorada una sola vez
- [ ] **P1** — Añadir `threading.Lock` al `OrderedDict` del caché
- [ ] Evaluar `cachetools` como reemplazo (thread-safe, TTLCache, LRUCache built-in)

---

## 7. Procesamiento Asíncrono

### 7.1 GUI Threading (Bien resuelto)

| Componente | Función |
|---|---|
| `WorkerThread(QThread)` | Operaciones pesadas fuera del hilo GUI |
| `ProgressDialog` | Modal con barra progreso, timer, log, cancelación |
| `ejecutar_con_progreso()` | Función de conveniencia |
| `DecisionDialogHandler` | Comunicación bidireccional worker↔GUI con QMutex/QWaitCondition |

Usado en: generación de guardias (CP-SAT solver), exportación PDF, importación Excel, reportes.

### 7.2 Hallazgos

| ID | Hallazgo | Severidad |
|---|---|---|
| ASYNC-01 | **Sync SFTP no usa QThread** — solo `self.repaint()` manual. Potencial freeze de GUI | ALTA |
| ASYNC-02 | FastAPI endpoints síncronos (`def` en vez de `async def`) | BAJA (aceptable con SQLite) |
| ASYNC-03 | No hay asyncio, multiprocessing ni thread pools | BAJA |

### 7.3 Recomendaciones

- [ ] **P1** — Mover sincronización SFTP a `QThread` con `ProgressDialog`
- [ ] Evaluar `async def` + `run_in_threadpool` para endpoints FastAPI si se migra a PostgreSQL

---

## 8. Escalabilidad y Resiliencia

### 8.1 Retry Logic

| ID | Hallazgo | Severidad |
|---|---|---|
| RES-01 | `max_retries_db: int = 3` en settings pero **no implementado en código** | MEDIA |
| RES-02 | Sin retry en conexión SFTP — un fallo = operación perdida | MEDIA |

### 8.2 Circuit Breaker

❌ **No existe.** Ni para SFTP, ni para SMTP, ni para BD.

### 8.3 Graceful Degradation

- ✅ La app funciona offline (SQLite local) — sync SFTP es opcional
- ✅ `SessionLockedDialog` ofrece "Reintentar" cuando hay sesión bloqueada
- ❌ Sin fallback si CP-SAT solver no converge (solo diagnóstico manual)

### 8.4 Recomendaciones

- [ ] Implementar retry con backoff exponencial para SFTP (`tenacity` library)
- [ ] Implementar circuit breaker para servicios externos (SFTP, SMTP)
- [ ] Implementar el retry de BD que ya está configurado en settings

---

## 9. API REST

### 9.1 Endpoints

| Prefijo | Router | Operaciones |
|---|---|---|
| `/api/guardias` | guardias.py | GET (filtros, paginación), GET /count |
| `/api/profesores` | profesores.py | GET (filtros), GET /{id} |
| `/api/cuotas` | cuotas.py | GET |
| `/api/equidad` | equidad.py | GET |
| `/api/estadisticas` | estadisticas.py | GET /resumen, GET /por-profesor |
| `/health` | main.py | GET (hardcodeado) |

### 9.2 Hallazgos

| ID | Hallazgo | Severidad |
|---|---|---|
| API-01 | **Solo operaciones GET** — sin POST, PUT, DELETE, PATCH | MEDIA |
| API-02 | **Sin versionado** — no hay `/v1/` ni header de versión | MEDIA |
| API-03 | **Sin autenticación** (ver SEC-03) | CRÍTICA |
| API-04 | **Sin rate limiting** — vulnerable a abuse | ALTA |
| API-05 | **CORS wildcard** `allow_origins=["*"]` con `allow_credentials=True` | ALTA |
| API-06 | **`/health` hardcodeado** — no usa el `HealthChecker` real | MEDIA |
| API-07 | Profesores sin paginación — devuelve todos | MEDIA |
| API-08 | Sin sorting paramétrico | BAJA |
| API-09 | Sin schema de error estándar | MEDIA |
| API-10 | Cuotas, equidad, estadísticas sin `response_model` tipado | BAJA |

### 9.3 Buenas Prácticas Existentes

- ✅ Swagger UI en `/docs` y ReDoc en `/redoc`
- ✅ Pydantic response models para guardias y profesores
- ✅ Docstrings con Args, Returns, Examples
- ✅ Recursos en plural (`/guardias`, `/profesores`)

### 9.4 Recomendaciones

- [ ] Añadir autenticación JWT/API-key
- [ ] Restringir CORS a orígenes específicos
- [ ] Añadir rate limiting (`slowapi` o `fastapi-limiter`)
- [ ] Conectar `/health` al `HealthChecker` real
- [ ] Añadir paginación a `/api/profesores`
- [ ] Añadir versionado `/v1/`
- [ ] Definir schema de error estándar `{"error": {"code": "...", "message": "..."}}`
- [ ] Añadir middleware de error handling para no exponer `str(e)`

---

## 10. Testing

### 10.1 Estado Actual

- **990 tests**, 39.75% coverage
- **52 archivos de test** + `tests/utils/`
- Markers: `unit`, `integration`, `ui`, `slow`, `db`, `multicurso`
- pytest-qt para GUI, pytest-mock, coverage con branch

### 10.2 Fortalezas

- ✅ Domain layer bien cubierto (entities, value objects, domain services)
- ✅ Jerarquía de excepciones exhaustivamente testeada
- ✅ Repositories con SQLite in-memory
- ✅ Use cases con DTOs validados
- ✅ Conftest bien estructurado con 14+ fixtures y factories
- ✅ Auto-marking inteligente por path

### 10.3 Debilidades

| ID | Hallazgo | Severidad |
|---|---|---|
| TEST-01 | **39.75% coverage** — insuficiente, 60% sin validar | ALTA |
| TEST-02 | **0 tests para SFTP/SMTP** — sync sin cobertura | ALTA |
| TEST-03 | **0 tests para API REST** — endpoints no validados | ALTA |
| TEST-04 | GUI tests solo verifican inicialización, no interacción | MEDIA |
| TEST-05 | CP-SAT solver testeado solo indirectamente | MEDIA |

### 10.4 Recomendaciones

- [ ] Target coverage: mínimo 70%, ideal 80%
- [ ] Añadir tests de API con `TestClient` de FastAPI
- [ ] Añadir tests de SFTP con Paramiko mockeado
- [ ] Añadir tests de SMTP con `smtplib` mockeado
- [ ] Expandir GUI tests con simulación de clicks y edición (`qtbot.mouseClick`, `qtbot.keyClicks`)
- [ ] Añadir mutation testing (`mutmut`) para validar calidad de assertions

---

## 11. Observabilidad

### 11.1 Métricas (Prometheus)

`MetricsCollector` con dual-backend: `prometheus_client` cuando disponible, fallback in-memory.

Métricas definidas:
- `app_requests_total`, `app_request_duration_seconds`, `app_errors_total`
- `app_cache_hits/misses`, `db_query_duration_seconds`, `db_queries_total`
- Negocio: `profesores_total`, `guardias_total`, `ausencias_activas`
- Sistema: `memory`, `cpu` via psutil

Decoradores: `@track_time`, `@count_calls`, `@track_errors`, `@with_metrics` — usados en ~20+ use cases.

### 11.2 Logging

Structured logging con `structlog` (fallback stdlib):
- Procesadores: `merge_contextvars`, `TimeStamper(iso)`, `JSONRenderer`/`ConsoleRenderer`
- Rotación: `RotatingFileHandler`, 10MB max, 5 backups
- Decorador `@log_function_call` y context manager `log_context()`

### 11.3 Health Checks

`HealthChecker` con 4 componentes: database, cache, configuration, system_resources.
3 estados: HEALTHY, DEGRADED, UNHEALTHY.

### 11.4 Hallazgos

| ID | Hallazgo | Severidad |
|---|---|---|
| OBS-01 | **`/health` endpoint hardcodeado** — no usa el `HealthChecker` real | MEDIA |
| OBS-02 | **Sin alerting real** — `PerformanceMonitor` genera alertas in-memory sin envío | ALTA |
| OBS-03 | Sin dashboard de métricas en tiempo real | MEDIA |
| OBS-04 | Logging sin filtro de datos sensibles | MEDIA |

### 11.5 Recomendaciones

- [ ] Conectar `/health` al `HealthChecker`
- [ ] Implementar alerting vía email/webhook cuando hay estado UNHEALTHY
- [ ] Añadir filtro de datos sensibles en logging (contraseñas, tokens)
- [ ] Exponer endpoint `/metrics` para scraping de Prometheus
- [ ] Evaluar Grafana para dashboard visual

---

## 12. UX/UI y Accesibilidad

### 12.1 Diseño

GUI PyQt6 con diseño CCleaner: sidebar oscuro + QStackedWidget.
12 secciones: Dashboard, Profesores, Zonas, Ajustes, Conectividad, Reportes, Import/Export, Asignación, Perfiles, Calendario, Estadísticas, Ausencias.

### 12.2 Indicadores de Progreso

✅ Bien resuelto:
- `ProgressDialog` con barra, timer, log detallado, cancelación
- `SyncProgressDialog` con pasos numerados
- Todas las operaciones largas usan `ejecutar_con_progreso()`

### 12.3 Mensajes al Usuario

✅ Bien estandarizado via `BaseForm`:
- `mostrar_exito()`, `mostrar_error()`, `mostrar_advertencia()`, `confirmar_accion()`
- Icono corporativo, HTML formatting, estilos consistentes

### 12.4 Hallazgos

| ID | Hallazgo | Severidad |
|---|---|---|
| UX-01 | **Sin `QValidator` en campos** — validación solo al submit, sin feedback en tiempo real | MEDIA |
| UX-02 | **Sin `setAccessibleName`/`setAccessibleDescription`** — screen readers no pueden navegar | MEDIA |
| UX-03 | **Sin `setTabOrder`** — navegación por teclado puede ser caótica | MEDIA |
| UX-04 | **Sin DPI awareness** — no hay `setHighDpiScaleFactorRoundingPolicy` | MEDIA |
| UX-05 | Dos temas UI coexisten (legacy Material + CCleaner) | BAJA |
| UX-06 | `screen_validator.py` bloquea la app si resolución < 1280x720 | BAJA |

### 12.5 Recomendaciones

- [ ] Añadir `QValidator` (QRegularExpressionValidator, QIntValidator) a campos de formulario
- [ ] Añadir `setAccessibleName()` y `setAccessibleDescription()` a widgets interactivos
- [ ] Definir `setTabOrder()` explícito en formularios
- [ ] Añadir soporte DPI con `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough`
- [ ] Eliminar el tema legacy y unificar en CCleaner
- [ ] Permitir uso en baja resolución con scroll en vez de bloquear

---

## 13. Control de Acceso y Multi-tenancy

### 13.1 Autenticación

- Login por username + password hasheado con SHA-256 (ver SEC-01)
- Usuarios almacenados en `data/users.json`
- Recuperación de contraseña vía email con código temporal

### 13.2 Autorización

❌ **No existe.** No hay roles, permisos ni ACL. Todos los usuarios autenticados tienen acceso total a todas las funciones.

### 13.3 Multi-tenancy

✅ **Bien implementado**: Cada usuario tiene su propia BD SQLite en `data/users/{sha256(username)[:16]}/guardias_patio.db`. Aislamiento total a nivel de fichero.

| ID | Hallazgo | Severidad |
|---|---|---|
| MT-01 | Hash truncado a 16 chars (64 bits) — suficiente para pocos usuarios | BAJA |
| MT-02 | Username vacío genera hash válido — sin validación | MEDIA |
| MT-03 | Variables globales sin thread-safety para cambio de usuario | ALTA |
| MT-04 | Sin mecanismo explícito de logout | MEDIA |

### 13.4 Recomendaciones

- [ ] Implementar sistema de roles básico (admin/profesor) si la app crece
- [ ] Validar username no vacío antes de generar hash
- [ ] Implementar logout explícito con limpieza de sesión
- [ ] Considerar thread-local storage en vez de variables globales

---

## 14. Idempotencia

### 14.1 Estado Actual

| Operación | Idempotente? | Detalle |
|---|---|---|
| `initialize_user_database()` | ✅ | Alembic + create_all + guards |
| `_apply_direct_migrations()` | ✅ | Verifica existencia antes de ALTER |
| Migraciones Alembic individuales | ❌ Parcial | `0122b6bbdc61` y `36b14ee8a76d` fallan si se re-ejecutan |
| `deactivate_all()` en CursoEscolar | ✅ | UPDATE sin condición |
| `save()` en repositorios | ✅ | Patrón upsert (if id: update, else: insert) |
| Generación de guardias | ❌ | Regenerar sin limpiar previas puede duplicar |

### 14.2 Recomendaciones

- [ ] Hacer todas las migraciones idempotentes con guards de existencia
- [ ] Añadir UniqueConstraint en guardias para prevenir duplicados a nivel BD
- [ ] Documentar claramente qué operaciones son idempotentes y cuáles no

---

## 15. Alta Disponibilidad

### 15.1 Arquitectura Actual

La app es una **aplicación de escritorio con BD local (SQLite)**. No está diseñada para alta disponibilidad en el sentido tradicional (clustering, réplicas, failover).

| Aspecto | Estado |
|---|---|
| BD local | SQLite single-file — no replicable nativamente |
| Sincronización | SFTP manual/semi-automática a servidor 1&1 |
| Sesión única | Lock distribuido via SFTP (archivo de bloqueo) |
| Backup | Implícito via sincronización SFTP |
| Offline | ✅ Funciona sin conexión a internet |

### 15.2 Limitaciones

- No hay réplicas de BD
- No hay failover automático
- Sincronización SFTP puede perder datos si hay conflictos
- Lock de sesión depende de conectividad SFTP

### 15.3 Recomendaciones (si se migra a web)

- [ ] Migrar a PostgreSQL para soporte multi-conexión
- [ ] Implementar réplicas read-only
- [ ] Añadir cola de mensajes (Redis/RabbitMQ) para operaciones asíncronas
- [ ] Implementar resolución de conflictos para sync

---

## 16. Organización de Archivos y Carpetas

### 16.1 Archivos Mal Ubicados

| Archivo | Ubicación actual | Ubicación correcta | Acción |
|---|---|---|---|
| `src/ui_styles.py` | Raíz de `src/` | `src/presentation/themes/` | Mover y unificar con `ccleaner_theme.py` |
| `src/domain/services/ejemplo_integracion.py` | Domain services | `docs/examples/` o eliminar | Es código demo, no pertenece a producción |
| `src/services/migrar_a_multi_curso.py` | Services | `scripts/` | Es un script de migración one-off |
| `src/services/README_SISTEMA_HIBRIDO.md` | Services | `docs/architecture/` | Documentación fuera de lugar |
| `src/models/models.py` | Models (shim legacy) | Eliminar | Re-export deprecado, ya nadie lo importa |
| `scripts/test_icalendar.py` | Scripts | `tests/` | Es un test, no un script |
| `scripts/test_initial_config.py` | Scripts | `tests/` | Es un test, no un script |
| `scripts/test_contador_tiempo.py` | Scripts | `tests/` | Es un test, no un script |
| `scripts/prueba_calendario.ics` | Scripts | `tests/fixtures/` | Fixture de test |

### 16.2 Archivos Excesivamente Grandes (necesitan refactorización)

| Archivo | Líneas | Severidad | Propuesta de split |
|---|---|---|---|
| `src/services/exportador_pdf.py` | **1847** | CRÍTICA | → `pdf_calendario_individual.py`, `pdf_calendario_general.py`, `pdf_estilos.py`, `pdf_utils.py` |
| `src/presentation/widgets/vista_calendario.py` | **1368** | CRÍTICA | → Separar widget base, renderizado de celdas, diálogos de día, lógica de navegación |
| `src/services/exportador.py` | **1158** | CRÍTICA | → `exportador_json.py`, `exportador_base.py`, separar lógica de cifrado |
| `src/services/asignador_guardias_v4_hibrido.py` | **1140** | CRÍTICA | → `solver_hibrido.py`, `diagnostico.py`, `sugerencias.py` |
| `src/presentation/dialogs/initial_config_dialog.py` | **1051** | CRÍTICA | → Separar pasos del wizard en clases/archivos individuales |
| `src/presentation/widgets/progress_indicators.py` | 947 | ALTA | → `worker_thread.py`, `progress_dialog.py`, `decision_handler.py` |
| `src/presentation/forms/profesor_form.py` | 847 | ALTA | → Separar tabla, formulario de edición, validaciones |
| `src/services/asignador_guardias_cpsat.py` | 845 | ALTA | → `cpsat_model.py`, `cpsat_constraints.py`, `cpsat_solver.py` |
| `src/sync/data_exporter.py` | 822 | ALTA | → Separar exportación por entidad |
| `src/presentation/themes/ccleaner_theme.py` | 717 | MEDIA | Aceptable, pero podría separar paleta de colores |

### 16.3 Funcionalidad Duplicada

| Duplicación | Archivos involucrados | Recomendación |
|---|---|---|
| **Logging** | `src/utils/logger.py` (redirige a core) vs `src/core/logging.py` | Eliminar `utils/logger.py`, actualizar imports |
| **Iconos** | `src/utils/icons.py` vs `src/utils/icon_manager.py` | Unificar en un solo módulo |
| **Estilos UI** | `src/ui_styles.py` (legacy Material) vs `src/presentation/themes/ccleaner_theme.py` | Migrar todo a ccleaner_theme (20+ archivos importan `ui_styles`) |
| **Models ORM** | `src/models/models.py` vs `src/infrastructure/database/models.py` | Eliminar shim legacy |
| **Benchmarks** | 4 scripts: `benchmark_optimizaciones.py`, `benchmark_performance.py`, `profile_performance.py`, `profile_app.py` | Unificar en 1 script con subcomandos |
| **Auditoría N+1** | `scripts/audit_n_plus_1.py` + `scripts/audit_queries_n1.py` | Unificar en 1 |
| **Regenerar guardias** | `scripts/regenerar_guardias.py` + `scripts/regenerar_guardias_v3.py` | Eliminar v1, renombrar v3 |

### 16.4 Scripts — Clasificación y Limpieza

| Tipo | Scripts | Acción |
|---|---|---|
| **One-off (ya ejecutados)** | `add_activo_column.py`, `migrate_multi_curso.py`, `migrar_recreos_strings_a_int.py`, `migrar_recreos_profesores.py` | Mover a `scripts/archive/` o eliminar |
| **Auditoría puntual** | `audit_n_plus_1.py`, `audit_queries_n1.py`, `auditoria_algoritmo_guardias.py` | Mover a `scripts/archive/` |
| **Utilidades permanentes** | `importar_profesores_desde_excel.py`, `cleanup_project.py`, `consultar_fechas_guardias.py` | Mantener |
| **Build** | `build_windows.ps1`, `scripts/build/` | Mantener |
| **Dev** | `run_api.sh`, `dev/run_app.sh` | Mantener |
| **Benchmarks (4 duplicados)** | `benchmark_*.py`, `profile_*.py` | Unificar en 1 |
| **Tests sueltos (3)** | `test_icalendar.py`, `test_initial_config.py`, `test_contador_tiempo.py` | Mover a `tests/` |
| **Verificación** | `verificar_export_completo.py`, `verificar_sistema_hibrido.py`, `validar_equidad.py` | Mover a `tests/` como integration tests |

### 16.5 Documentación

- `docs/archive/historico/` contiene **80+ documentos históricos** — ballast considerable que dificulta encontrar documentación relevante
- Documentación actual bien organizada en `docs/dev/`, `docs/architecture/`, `docs/user/`, `docs/examples/`
- `CHANGELOG.md` bien mantenido (681 líneas)

### 16.6 Otros Hallazgos de Organización

| ID | Hallazgo | Severidad |
|---|---|---|
| ORG-01 | `src/services/` **no tiene `__init__.py`** — inconsistente con todos los demás paquetes | BAJA |
| ORG-02 | `data/users.json` posiblemente trackeado en git pese a contener hashes de contraseñas | ALTA |
| ORG-03 | `logs/` contiene 13 ficheros JSON de comparación de cuotas — deberían auto-limpiarse | BAJA |
| ORG-04 | 20+ archivos importan `import ui_styles` desde raíz de `src/` — rompe jerarquía de capas | MEDIA |
| ORG-05 | `Re-export chain`: `utils/__init__.py` re-exporta `core.exceptions` — coupling innecesario | BAJA |

### 16.7 Estructura Propuesta

```
src/
├── main.py
├── py.typed
├── api/                          # (sin cambios)
├── application/                   # (sin cambios)
├── config/                        # (sin cambios)
├── core/                          # (sin cambios)
├── database/                      # (sin cambios)
├── domain/                        # eliminar ejemplo_integracion.py
├── infrastructure/                # (sin cambios)
├── presentation/
│   ├── themes/
│   │   └── ccleaner_theme.py     # unificar ui_styles.py aquí
│   ├── forms/
│   ├── widgets/
│   ├── dialogs/
│   └── components/
├── services/
│   ├── __init__.py               # añadir
│   ├── assignment/
│   ├── export/                   # split de exportador.py y exportador_pdf.py
│   │   ├── pdf_individual.py
│   │   ├── pdf_general.py
│   │   ├── json_exporter.py
│   │   └── csv_exporter.py       # nuevo
│   ├── email/
│   ├── calendar/
│   └── validators/
├── sync/                          # (sin cambios)
└── utils/                         # eliminar logger.py, unificar icons

scripts/
├── archive/                       # mover scripts one-off aquí
├── build/
├── dev/
├── maintenance/
└── benchmark.py                   # unificado
```

---

## 17. Funcionalidades Pendientes de Implementar

### 17.1 TODOs Activos en Código

| Archivo | TODO | Criticidad | Impacto |
|---|---|---|---|
| `services/assignment/score_calculator.py:142` | Restar días para verificar guardias recientes | MEDIA | Afecta calidad del scoring de asignación |
| `services/gestor_cursos.py:298` | Filtrar profesores por `curso_id` | MEDIA | Profesores no se vinculan a cursos específicos |
| `services/gestor_cursos.py:305` | Cuando Profesor tenga `curso_id`, filtrar por curso | MEDIA | Misma deficiencia |
| `services/cache_soluciones_guardias.py:89` | Implementar conteo de ausencias en cache key | BAJA | Caché puede servir resultados stale tras ausencia |
| `config/settings.py:237` | Deprecar en v3.1 y eliminar en v4.0 | ALTA | **Ya estamos en v3.2.1** — TODO olvidado |
| `infrastructure/mappers/zona_mapper.py:34` | Agregar `capacidad_profesores` y `activa` al modelo Zona | MEDIA | Campos de entidad sin persistir |
| `infrastructure/mappers/guardia_mapper.py:37` | Agregar `es_sustitucion`, `profesor_sustituido_id`, `notas` | ALTA | **Bloquea tracking completo de sustituciones** |
| `infrastructure/repositories/sqlalchemy_guardia_repository.py:352` | Agregar campo `es_sustitucion` al modelo Guardia | ALTA | Misma deficiencia |

### 17.2 Sistema de Sustituciones — Incompleto

El mapper de Guardia hardcodea:
```python
es_sustitucion=False,        # TODO
profesor_sustituido_id=None,  # TODO
notas=None,                   # TODO
```

El widget `GestorSustituciones` existe en la UI pero **no puede persistir** quién fue sustituido ni el motivo. Esto invalida el tracking de sustituciones como funcionalidad real.

**Para completar**:
- [ ] Añadir columnas `es_sustitucion BOOLEAN`, `profesor_sustituido_id FK`, `notas TEXT` a tabla `guardias`
- [ ] Crear migración Alembic correspondiente
- [ ] Actualizar `GuardiaMapper` para mapear los nuevos campos
- [ ] Actualizar `GuardiaEntity` si no los tiene ya
- [ ] Actualizar repositorio y use cases

### 17.3 Exportaciones Faltantes

| Formato | Estado | Detalle |
|---|---|---|
| PDF calendario individual | ✅ Completo | `exportador_pdf.py` — funcional |
| PDF calendario general | ✅ Completo | `exportador_pdf.py` — funcional |
| JSON (guardias, profesores) | ✅ Completo | `exportador.py`, `data_exporter.py` |
| iCalendar (.ics) | ✅ Completo | `icalendar_service.py` — RFC 5545 |
| Email con adjuntos | ✅ Completo | `email_service.py` |
| **CSV / Excel de guardias** | ❌ No existe | Solo se exporta JSON. Falta export tabular |
| **PDF informe de ausencias** | ❌ No existe | No hay report de ausencias/sustituciones |
| **PDF informe trimestral** | ❌ No existe | No hay report de cumplimiento por periodo |
| **Excel de estadísticas** | ❌ No existe | Dashboard solo visual (matplotlib), no exportable |
| **Backup completo exportable** | ❌ Parcial | `data_exporter.py` exporta JSON pero no es un backup restaurable |

### 17.4 Importaciones Faltantes

| Funcionalidad | Estado | Detalle |
|---|---|---|
| Importar profesores desde Excel | ✅ Funcional | `importar_profesores_desde_excel.py` (como script) |
| **Importar profesores desde UI** | ⚠️ Parcial | `ImportExportForm` existe pero la integración con el script no es transparente |
| **Importar zonas desde Excel/CSV** | ❌ No existe | Solo alta manual |
| **Importar festivos desde archivo** | ❌ No existe | Solo configuración manual |
| **Restaurar backup** | ❌ No existe | No hay importación inversa del export JSON |
| **Importar desde otro curso** | ❌ No existe | Al crear un curso nuevo hay que re-configurar todo |

### 17.5 Campo `curso_id` en Profesor

Dos TODOs en `gestor_cursos.py` indican que los profesores no están vinculados a cursos específicos. Son "globales". Esto impide:
- Tener plantilla de profesores diferente por curso
- Desactivar automáticamente profesores que ya no están en un curso
- Histórico limpio de qué profesores participaron en cada curso

### 17.6 ML Predictor — Sin Valor Real

`ml_predictor_estrategia.py` está completamente implementado (sklearn RandomForest + pickle) pero:
- Requiere datos históricos que no existen al inicio
- No hay evidencia de integración en el flujo principal de asignación
- Añade `scikit-learn` + `numpy` como dependencias obligatorias (~200MB)
- El orquestador ya elige estrategia basándose en heurísticas simples

**Recomendación**: Hacer `sklearn` opcional (`try: import sklearn`) o eliminar el módulo hasta que haya suficiente histórico.

### 17.7 Sync Strategy Pattern — Incompleto

`SyncBackend` ABC define 4 métodos abstractos, pero:
- Solo `LocalSyncBackend` implementa la interfaz
- La sync SFTP real está en archivos separados y no implementa `SyncBackend`
- El patrón Strategy no se usa como tal

### 17.8 Scripts de Mantenimiento Documentados pero No Implementados

En la documentación de `mantenimiento_fase8` se planificaron 4 scripts que nunca se crearon:

| Script | Propósito | Prioridad |
|---|---|---|
| `backup_database.py` | Backup automático de la BD del usuario activo | MEDIA |
| `check_db_integrity.py` | Verificar integridad de FK, índices, datos huérfanos | MEDIA |
| `cleanup_old_backups.py` | Limpieza de backups antiguos (retención configurable) | BAJA |
| `optimize_database.py` | VACUUM + ANALYZE + REINDEX en SQLite | BAJA |

### 17.9 Homogeneización Visual Pendiente

Según `PLAN_HOMOGENEIZACION_FORMULARIOS`, 3 formularios usan CSS inline en vez del sistema de estilos común:
- `import_export_form.py`
- `gestor_sustituciones.py`
- `panel_estadisticas.py`

Deberían migrar a `ccleaner_theme.py` para consistencia visual.

### 17.10 Funcionalidades Sugeridas (no existentes)

| Feature | Valor | Esfuerzo |
|---|---|---|
| **Notificaciones push a profesores** | Alto — profesores ven sus guardias en tiempo real | Alto |
| **Vista de profesor individual** (modo lectura) | Alto — cada profesor ve solo sus guardias/calendario | Medio |
| **Comparativa inter-cursos** | Medio — estadísticas comparativas entre cursos | Medio |
| **Plantillas de configuración** | Medio — guardar/cargar configs tipo (recreos, zonas, horarios) | Bajo |
| **Log de auditoría** | Alto — quién hizo qué cambio y cuándo | Medio |
| **Modo oscuro** | Bajo — ya hay base con ccleaner_theme | Bajo |
| **Drag & drop en calendario** | Alto — reasignar guardias arrastrando | Alto |
| **Undo/Redo** | Medio — deshacer últimos cambios | Alto |
| **Suscripción iCal por URL permanente** | Alto — profesores sincronizan calendario automáticamente | Medio |

---

## 18. Refactorización y Código Huérfano

### 18.1 Ficheros Python Huérfanos (nunca importados)

| Fichero | Líneas | Severidad | Evidencia |
|---|---|---|---|
| `src/services/ml_predictor_estrategia.py` | 392 | **CRÍTICA** | Nunca importado desde `src/`. Además usa `pickle.load()` inseguro (ver §19). Añade ~200MB de deps (sklearn) |
| `src/services/sistema_sugerencias_automaticas.py` | ~200 | **CRÍTICA** | 0 imports encontrados en todo el proyecto |
| `src/services/visualizador_conflictos_guardias.py` | ~150 | **CRÍTICA** | 0 imports. Clase completa con matplotlib sin uso |
| `src/services/cache_soluciones_guardias.py` | ~180 | **CRÍTICA** | 0 imports. Sistema de caché completo sin integrar |
| `src/services/optimizaciones_asignador.py` | ~200 | **CRÍTICA** | 0 imports. Clases `SlotKey`, `IndiceSlots` sin uso |
| `src/services/integrador_orquestador_ui.py` | ~250 | **CRÍTICA** | Nunca importado. Además tiene import roto (`src/models/guardia.py` no existe) |
| `src/domain/services/ejemplo_integracion.py` | ~80 | ALTA | Código demo en producción |
| `src/models/models.py` | ~30 | ALTA | Shim deprecated. Solo importado por `alembic/env.py` y 1 test |
| `src/presentation/main_window.py` | ~300 | ALTA | Ventana principal legacy reemplazada por `ccleaner_main_window.py` |
| `src/presentation/components/top_bar.py` | ~100 | ALTA | Componente UI nunca importado |
| `src/presentation/components/sidebar_menu.py` | ~120 | ALTA | Sidebar legacy reemplazada por `ccleaner_sidebar.py` |
| `src/presentation/components/ccleaner_topbar.py` | ~80 | ALTA | 0 imports encontrados |
| `src/domain/schemas/` (3 ficheros) | ~200 | ALTA | Todo el directorio nunca importado. Pydantic schemas sin uso |
| `src/utils/query_optimizer.py` | 305 | MEDIA | Nunca importado. Funciones de análisis N+1 sin integrar |
| `src/utils/screen_validator.py` | ~50 | MEDIA | Nunca importado desde producción |
| `src/presentation/forms/simple_profesor_form.py` | ~150 | MEDIA | Formulario alternativo sin uso |

**Total: ~2.800 líneas de código muerto en 16 ficheros.**

### 18.2 Recomendaciones de Limpieza

- [ ] **P0** — Eliminar los 6 ficheros CRÍTICOS de `src/services/` (2.500+ líneas muertas)
- [ ] **P0** — Eliminar `src/domain/schemas/` completo (nunca usado)
- [ ] **P1** — Eliminar `src/models/models.py`, actualizar `alembic/env.py` para importar de `infrastructure/database/models.py`
- [ ] **P1** — Eliminar `main_window.py`, `top_bar.py`, `sidebar_menu.py`, `ccleaner_topbar.py` (UI legacy reemplazada)
- [ ] **P1** — Eliminar `simple_profesor_form.py`, `screen_validator.py`
- [ ] **P2** — Evaluar integración real de `query_optimizer.py` o eliminarlo

### 18.3 Funcionalidad Duplicada

| Duplicación | Archivos | Acción |
|---|---|---|
| **Logging** | `utils/logger.py` vs `core/logging.py` (19+ imports cada uno) | Unificar en `core/logging`, eliminar `utils/logger.py` |
| **Iconos** | `utils/icons.py` vs `utils/icon_manager.py` | Unificar en un solo módulo |
| **Estilos UI** | `ui_styles.py` (legacy) vs `presentation/themes/ccleaner_theme.py` (20+ archivos importan el legacy) | Migrar todo a `ccleaner_theme.py` |
| **Models ORM** | `models/models.py` vs `infrastructure/database/models.py` | Eliminar shim legacy |
| **Benchmarks** | 4 scripts: `benchmark_optimizaciones.py`, `benchmark_performance.py`, `profile_performance.py`, `profile_app.py` | Unificar en 1 con subcomandos |
| **Auditoría N+1** | `audit_n_plus_1.py` + `audit_queries_n1.py` | Unificar en 1 |
| **Regenerar guardias** | `regenerar_guardias.py` + `regenerar_guardias_v3.py` | Eliminar v1, renombrar v3 |

### 18.4 Configuración Huérfana

| Recurso | Detalle | Severidad |
|---|---|---|
| `sftp_config.json` (raíz) | Nunca referenciado desde `src/`. Las config SFTP se leen del `.env` vía `dotenv` | MEDIA |
| `smtp_config.json` (raíz) | Igual. Config SMTP se lee del `.env` | MEDIA |
| `settings.py` → `feature_*` flags (5) | `feature_zona_preferida`, `feature_matriz_horario`, `feature_ausencias`, `feature_sustituciones`, `feature_exportacion` — nunca consultados en código | MEDIA |
| `settings.py` → `recreo_manana_1/2`, `recreo_tarde_1/2` | Horarios por defecto nunca leídos. La config real viene de la BD | BAJA |
| Alembic: migraciones `b939a8969a45` + `0122b6bbdc61` | Duplicada: ambas añaden `horas_manana_tarde` a profesor | MEDIA |

---

## 19. Sanitización y Robustez del Código

### 19.1 Seguridad en el Código

| ID | Fichero | Problema | Severidad |
|---|---|---|---|
| SAN-01 | `services/ml_predictor_estrategia.py` L353-363 | **`pickle.load()` sin validación** — ejecución de código arbitrario si se modifica el fichero `.pkl` | **CRÍTICA** |
| SAN-02 | `sync/data_exporter.py` L470-505 | Contraseñas "encriptadas" con `base64.b64encode()` — reversible trivialmente | **CRÍTICA** |
| SAN-03 | `services/assignment/profesor_filter.py` L145 | `ast.literal_eval()` en datos de BD — smell, se repite en `profesor_mapper.py` y `parsers.py` | MEDIA |
| SAN-04 | `database/db_manager.py` L124-236 | SQL hardcodeado en migraciones manuales (`conn.execute(text("ALTER TABLE ..."))`) | ALTA |

### 19.2 Excepciones Silenciadas (`except Exception: pass`)

**15 bloques** que tragan errores silenciosamente, ocultando fallos reales:

| Fichero | Líneas |
|---|---|
| `services/exportador_pdf.py` | L1178 |
| `utils/corporate_branding.py` | L29 |
| `utils/ui_helpers.py` | L64 |
| `presentation/widgets/progress_indicators.py` | L77, L380, L396, L534, L765, L899 |
| `sync/sync_manager.py` | L245, L253 |
| `presentation/forms/profesor_widgets/restricciones_widget.py` | L450 |
| `core/observability/metrics.py` | L344 |
| `application/use_cases/guardia/obtener_guardias.py` | L111, L118 |

**Recomendación**: Reemplazar `except Exception: pass` por:
- `except SpecificException as e: logger.warning(...)` donde sea recuperable
- Dejar propagar donde deba fallar explícitamente
- Mínimo: logear el error en vez de silenciarlo

### 19.3 Sentencias `print()` de Debug en Producción

| Fichero | Líneas | Detalle |
|---|---|---|
| `presentation/widgets/gestion_cursos_widget.py` | L404-425 | **8 sentencias** `print("DEBUG: ...")` |
| `utils/icon_manager.py` | L69 | `print("⚠️ Icono no encontrado: ...")` |
| `utils/ui_helpers.py` | L91, L123 | `print("Error cargando logo...")` |
| `services/exportador_pdf.py` | L260 | `print(f"Error al exportar PDF: {e}")` |
| `core/app_initializer.py` | L35-65 | 4 prints de setup/bootstrap |

**Recomendación**: Reemplazar todos los `print()` por `logger.debug()` / `logger.warning()`.

### 19.4 Código Comentado

Revisar y eliminar bloques de código comentado > 5 líneas — son ruido que dificulta la lectura y no aportan valor (para eso está git).

### 19.5 Magic Numbers / Strings

| Fichero | Ejemplo | Recomendación |
|---|---|---|
| `icalendar_service.py` | `DURACION_RECREO_MINUTOS = 20` hardcodeado | Mover a configuración |
| `asignador_guardias_cpsat.py` | Pesos `(1_000_000, 10_000, 10, 3)` | Mover a configuración avanzada |
| `screen_validator.py` | `1280x720` mínimo hardcodeado | Mover a constante con nombre |

### 19.6 Recomendaciones de Sanitización

- [ ] **P0** — Eliminar `ml_predictor_estrategia.py` (contiene `pickle.load` inseguro y es código muerto)
- [ ] **P0** — Eliminar o reescribir `base64` como "cifrado" en `data_exporter.py`
- [ ] **P1** — Reemplazar los 15 `except Exception: pass` por logging explícito
- [ ] **P1** — Reemplazar todos los `print()` de debug por `logger.debug()`
- [ ] **P1** — Unificar sistema de logging dual (`core.logging` vs `utils.logger`)
- [ ] **P2** — Normalizar campos JSON en BD para eliminar `ast.literal_eval()` / `json.loads()` defensivos
- [ ] **P2** — Eliminar código comentado > 5 líneas
- [ ] **P2** — Extraer magic numbers a constantes o configuración

---

## 20. Preparación para Migración Web

### 20.1 Evaluación de Capas para Backend Web

| Capa | ¿Funciona "as-is"? | Problema | Esfuerzo de adaptación |
|---|---|---|---|
| `domain/entities/` | ✅ Sí | Dataclasses puros | 0 |
| `domain/value_objects/` | ✅ Sí | Frozen dataclasses | 0 |
| `domain/repositories/` | ✅ Sí | ABC interfaces | 0 |
| `domain/services/` | ❌ No | **4 servicios importan ORM + SQLAlchemy directamente** (viola Clean Architecture) | Medio |
| `application/use_cases/` | ⚠️ Parcial | 20+ imports de modelos ORM, pero funcionan con Session | Bajo-Medio |
| `infrastructure/` | ✅ Sí | SQLAlchemy portable | 0 |
| `services/` | ✅ 22/23 | Solo `integrador_orquestador_ui.py` importa PyQt6 (mover a presentation/) | Trivial |
| `config/` | ✅ Sí | Pydantic BaseSettings | 0 |
| `core/` | ✅ Sí | Sin dependencias de framework | 0 |

### 20.2 Acoplamiento Presentation → Infrastructure (Bloqueante)

**36 imports directos** de modelos ORM desde la capa de presentación. Ejemplos:

| Widget/Form | Violación |
|---|---|
| `vista_calendario.py` | `session.query(Guardia)`, `session.query(Zona)`, `session.query(Ausencia)` directamente |
| `gestion_cursos_widget.py` | 12+ queries directas con `self.session.query(...)` |
| `gestor_sustituciones.py` | Queries directas a Profesor, Guardia, Zona |
| `dashboard_form.py` | Import directo de Configuracion, Guardia, Profesor |
| `profesor_form.py` | 4 imports locales de modelos ORM |

Esto **impide** separar la UI del backend: cada widget es un monolito que mezcla lógica de presentación con acceso a datos.

### 20.3 Domain Services Contaminados

**4 domain services** importan directamente de `infrastructure.database.models` y `sqlalchemy.orm.Session`:
- `equidad_guardias_service.py`
- `asignacion_guardia_service.py`
- `disponibilidad_profesor_service.py`
- `distribucion_cuotas_service.py`

Esto **viola la regla fundamental** de Clean Architecture: el dominio no debería conocer la infraestructura.

### 20.4 Cobertura API Actual (FastAPI)

| Funcionalidad | GUI | API | Estado |
|---|---|---|---|
| CRUD Profesores | ✅ | ⚠️ Solo GET | Faltan POST/PUT/DELETE |
| CRUD Zonas | ✅ | ❌ | Router completo |
| CRUD Configuración | ✅ | ❌ | Router completo |
| Gestión Cursos | ✅ | ❌ | Router completo |
| Ausencias | ✅ | ❌ | Router completo |
| Generación Guardias | ✅ | ❌ | Endpoint POST |
| Exportar PDF/iCal/JSON | ✅ | ❌ | Endpoints de export |
| Sustituciones | ✅ | ❌ | Router completo |
| Cuotas/Equidad | ✅ | ✅ | Ya funciona |
| Estadísticas | ✅ | ⚠️ Parcial | Expandir |

**Cobertura API actual: ~15% de la funcionalidad.** Solo lectura.

### 20.5 Base de Datos: SQLite → PostgreSQL

| Aspecto | Estado | Impacto |
|---|---|---|
| Tipos SQLAlchemy | ✅ Compatibles | `Integer`, `String`, `Text`, `Boolean`, `Date` — estándar |
| PRAGMAs SQLite (6) | ❌ Incompatibles | `foreign_keys`, `journal_mode=DELETE`, etc. — condicionar al dialecto |
| `check_same_thread: False` | ❌ Solo SQLite | Eliminar para PostgreSQL |
| `NullPool` | ❌ Solo SQLite | PostgreSQL necesita pool real (`QueuePool`) |
| `strftime('%Y',...)` en SQL raw | ❌ SQLite-specific | PostgreSQL usa `EXTRACT(YEAR FROM ...)` |
| Patrón per-user SQLite | ❌ **Bloqueante** | 1 BD por usuario es incompatible con web multi-user. Requiere migrar a 1 BD con `user_id` en cada tabla |

### 20.6 Servicios Portables (Buena Noticia)

**22 de 23 servicios** son 100% portables a web backend sin cambios:
- CP-SAT solver, exportadores (PDF/JSON/iCal), email, estadísticas, gestor de ausencias, validadores, importador de profesores, etc.
- Solo `integrador_orquestador_ui.py` depende de PyQt6 (y es código muerto — ver §18.1).

### 20.7 Cambios a Adoptar AHORA para Facilitar Migración

| Cambio | Impacto para web | Esfuerzo |
|---|---|---|
| **Limpiar `domain/services/`** de imports ORM | Restaura Clean Architecture, dominio portable | Medio |
| **Hacer que los routers de profesores/guardias/estadísticas usen use cases** (ya existen) | API lista para CRUD | Bajo |
| **Condicionar PRAGMAs al dialecto SQLite** en `db_manager.py` | Permite cambiar a PostgreSQL con 1 env var | Trivial |
| **Extraer `integrador_orquestador_ui.py`** a `presentation/` (si se mantiene) | Deja `services/` 100% libre de PyQt6 | Trivial |
| **Añadir `user_id` como concepto en domain** (no tabla aún) | Prepara para multi-tenant | Bajo |
| **Eliminar queries directas desde presentation/** | Desacopla UI de BD | Alto |

### 20.8 Scorecard de Preparación Web

| Dimensión | Score | Nota |
|---|---|---|
| Pureza del dominio | 6/10 | Entities y VOs limpios, pero domain services contaminados |
| Portabilidad de servicios | 9/10 | 22/23 portables directamente |
| API readiness | 3/10 | FastAPI existe pero solo ~15% de funcionalidad |
| Portabilidad de BD | 5/10 | Schema compatible, patrón per-user bloqueante |
| **Web readiness global** | **6/10** | Buena base con Clean Architecture + FastAPI. Trabajo principal: expandir API y resolver multi-tenancy |

---

## 21. Reparabilidad y Diagnóstico de Errores

### 21.1 Sistema de Logging (Estado Dual)

Coexisten **dos sistemas de logging** que generan confusión y logs inconsistentes:

| Sistema | Módulo | Imports en codebase |
|---|---|---|
| Estructurado (structlog) | `core.logging.get_logger` | ~19 ficheros |
| Simple (wrapper) | `utils.logger.get_logger` | ~19 ficheros |

**Problema**: Un desarrollador no sabe cuál usar. Los logs pueden ir a destinos o formatos diferentes según qué import se eligió.

**Recomendación**: Unificar en `core.logging`, eliminar `utils.logger`, actualizar los ~19 imports.

### 21.2 Manejo de Errores

| Aspecto | Estado | Detalle |
|---|---|---|
| Jerarquía de excepciones | ✅ Bien diseñada | `core/exceptions.py` con excepciones tipadas por dominio |
| `except Exception: pass` | ❌ 15 bloques | Ocultan fallos reales (ver §19.2) |
| Error boundaries en GUI | ⚠️ Parcial | `BaseForm` tiene `mostrar_error()`, pero no hay `try/except` global en event handlers |
| Errores API | ❌ Expone `str(e)` | Fuga de info interna (ver SEC-08) |
| Logging de errores | ⚠️ Inconsistente | Algunos errores se logean, otros se imprimen con `print()`, otros se silencian |

### 21.3 Trazabilidad

| Aspecto | Estado |
|---|---|
| Request IDs / Correlation IDs | ❌ No existe — imposible trazar una operación a través de capas |
| Stack traces en logs | ⚠️ Parcial — solo cuando se usa structlog con `exc_info=True` |
| Contexto de usuario en logs | ❌ No se incluye qué usuario ejecutó qué operación |
| Timestamps en logs | ✅ ISO 8601 con structlog |
| Log rotation | ✅ `RotatingFileHandler`, 10MB max, 5 backups |

### 21.4 Diagnóstico en Tiempo de Ejecución

| Herramienta | Estado | Utilidad |
|---|---|---|
| `HealthChecker` | ✅ Existe | 4 componentes: database, cache, config, system — pero no conectado al endpoint `/health` |
| `PerformanceMonitor` | ✅ Existe | Genera alertas in-memory, pero sin envío a ningún destino |
| `MetricsCollector` | ✅ Prometheus | Métricas bien definidas, pero sin dashboard ni scraping configurado |
| Error dialogs GUI | ✅ Existe | `mostrar_error()` con detalles técnicos opcionalmente |

### 21.5 Recomendaciones de Reparabilidad

- [ ] **P0** — Unificar logging: eliminar `utils/logger.py`, migrar todo a `core/logging`
- [ ] **P1** — Añadir correlation IDs para trazar operaciones cross-capa
- [ ] **P1** — Reemplazar `except Exception: pass` por logging explícito (ver §19.2)
- [ ] **P1** — Añadir error boundary global en `ccleaner_main_window.py` que capture excepciones no manejadas y las muestre/logee
- [ ] **P2** — Conectar `HealthChecker` al endpoint `/health`
- [ ] **P2** — Incluir `user_id` en contexto de logging (structlog `bind()`)
- [ ] **P2** — Reemplazar `print()` por `logger.*()` (ver §19.3)
- [ ] **P3** — Configurar alerting real (email/webhook) desde `PerformanceMonitor`

---

## 22. Sugerencias de Mejora General

### 22.1 Proyecto y Metadatos

| ID | Sugerencia | Prioridad | Detalle |
|---|---|---|---|
| MEJ-01 | **Completar `pyproject.toml`** | ALTA | Falta `[project]` (name, version, description, authors, license, python-requires), `[project.dependencies]`, `[build-system]`, `[project.scripts]`. Actualmente solo tiene config de ruff/mypy |
| MEJ-02 | **Migrar de `requirements.txt` a `pyproject.toml`** | MEDIA | Centralizar dependencias en el estándar moderno PEP 621 |
| MEJ-03 | **Dependencias sin versión máxima** | MEDIA | `fastapi>=0.104.0` sin techo puede traer breaking changes. Usar `>=X,<Y` |
| MEJ-04 | **sklearn como dependencia obligatoria sin uso real** | MEDIA | ~200MB de dependencias para un módulo ML muerto. Eliminar |

### 22.2 Código y Anti-patrones

| ID | Sugerencia | Prioridad | Detalle |
|---|---|---|---|
| MEJ-05 | **God class `ExportadorPDF`** | ALTA | 1847 líneas en una sola clase. Dividir en módulos por tipo de exportación |
| MEJ-06 | **20+ imports de `ui_styles` desde raíz** | ALTA | Rompe jerarquía de capas. Migrar a `presentation/themes/` |
| MEJ-07 | **Services importan ORM directo** | ALTA | `from infrastructure.database.models import Profesor` en servicios viola Clean Architecture |
| MEJ-08 | **Re-export chain en `utils/__init__.py`** | BAJA | Re-exporta `core.exceptions` — coupling innecesario entre capas |

### 22.3 Calidad de Código

| ID | Sugerencia | Prioridad | Detalle |
|---|---|---|---|
| MEJ-09 | **Coverage 39.75% → target 70%** | ALTA | Priorizar tests en: servicios de asignación, exportadores, sync, API |
| MEJ-10 | **ProfesorMapper: 130+ líneas de parsing defensivo** | MEDIA | Normalizar campos JSON a tablas eliminaría este código frágil |
| MEJ-11 | **Añadir `py.typed` marker y tipado estricto progresivo** | BAJA | Ya existe `py.typed` y mypy strict en dominio. Expandir a application y services |

### 22.4 Experiencia de Desarrollo

| ID | Sugerencia | Prioridad | Detalle |
|---|---|---|---|
| MEJ-12 | **Unificar entry points** | BAJA | `make run` vs `scripts/dev/run_app.sh` vs `python src/main.py` — documentar el canónico |
| MEJ-13 | **Makefile: añadir targets de linting** | BAJA | `make lint`, `make typecheck`, `make format` |

### 22.5 Localización y Mensajes

| ID | Sugerencia | Prioridad | Detalle |
|---|---|---|---|
| MEJ-14 | **Mensajes bien localizados en español** ✅ | — | Ya implementado con emojis contextuales |
| MEJ-15 | **Preparar para i18n** | BAJA | Si se quisiera inglés/catalán: extraer strings a archivos de traducción Qt (.ts) |

### 22.6 Limpieza y Mantenimiento

| ID | Sugerencia | Prioridad | Detalle |
|---|---|---|---|
| MEJ-16 | **Auto-limpieza de logs** | BAJA | `logs/` acumula ficheros JSON de comparación. Añadir rotación/limpieza automática |
| MEJ-17 | **`data/users.json` fuera de git** | ALTA | Ejecutar `git rm --cached data/users.json` — contiene hashes de contraseñas |
| MEJ-18 | **Añadir `__init__.py` a `src/services/`** | BAJA | Único paquete sin él. Inconsistencia |
| MEJ-19 | **Completar `pyproject.toml` con metadatos** | MEDIA | `[project]`, `[build-system]`, centralizar deps |
| MEJ-20 | **Fijar versiones máximas en dependencias** | MEDIA | `>=X,<Y` para evitar breaking changes |

---

## 23. Roadmap de Implementación

### Fase 1 — Seguridad Crítica

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Migrar a bcrypt/argon2 para contraseñas | P0 | Medio |
| Cifrado real de credenciales SFTP/SMTP (Fernet/keyring) | P0 | Medio |
| Autenticación JWT en API REST | P0 | Alto |
| Eliminar recovery code en texto plano + añadir TTL | P0 | Bajo |
| Cambiar uvicorn a 127.0.0.1 | P0 | Trivial |
| Reemplazar str(e) por mensajes genéricos en API | P0 | Bajo |
| Restringir CORS a orígenes específicos | P0 | Trivial |

### Fase 2 — Código Muerto y Sanitización

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Eliminar 6 ficheros CRÍTICOS orphan de `src/services/` (~2.500 líneas) | P0 | Trivial |
| Eliminar `src/domain/schemas/`, `src/models/models.py`, UI legacy | P0 | Trivial |
| Eliminar sklearn de requirements.txt (módulo ML muerto) | P0 | Trivial |
| Reemplazar 15 `except Exception: pass` por logging | P1 | Bajo |
| Reemplazar `print("DEBUG:...")` por `logger.debug()` | P1 | Bajo |
| Unificar logging dual → solo `core/logging` | P1 | Bajo |
| Eliminar `sftp_config.json` y `smtp_config.json` legacy | P1 | Trivial |
| Limpiar feature flags y settings huérfanos | P2 | Trivial |

### Fase 3 — Performance y Bugs Críticos

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Corregir N+1 en `/api/guardias` (joinedload) | P0 | Bajo |
| Corregir bug de `repository_cache.py` (re-creación de wrapper) | P0 | Bajo |
| Añadir thread-safety al caché (Lock) | P1 | Bajo |
| Mover sync SFTP a QThread | P1 | Medio |

### Fase 4 — Integridad de BD

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Añadir NOT NULL a guardias.profesor_id y zona_id | P1 | Bajo |
| Añadir ON DELETE CASCADE profesor→guardias/ausencias | P1 | Bajo |
| Añadir UniqueConstraint en guardias | P1 | Bajo |
| Crear índices faltantes | P1 | Bajo |
| Resolver inconsistencia cerrado/archivado | P1 | Bajo |
| Unificar init BD: solo Alembic | P2 | Alto |

### Fase 5 — Seguridad Media y Autenticación

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Política contraseñas: 8+ chars + complejidad | P1 | Bajo |
| Lockout tras 5 intentos fallidos | P1 | Bajo |
| Rate limiting en API | P1 | Medio |
| Escapar HTML en emails | P2 | Bajo |
| Sanitizar paths en sync | P2 | Bajo |
| Validar/sanitizar username | P2 | Bajo |

### Fase 6 — Testing y Observabilidad

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Tests de API REST con TestClient | P1 | Medio |
| Tests de SFTP/SMTP con mocks | P1 | Medio |
| Conectar /health al HealthChecker real | P2 | Bajo |
| Target: coverage 70%+ | P2 | Alto |
| Añadir correlation IDs para trazabilidad | P2 | Medio |
| Añadir error boundary global en GUI | P2 | Bajo |

### Fase 7 — Arquitectura y Preparación Web

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Limpiar domain/services de imports ORM (4 ficheros) | P1 | Medio |
| Hacer que routers API usen use cases (ya existen) | P1 | Bajo |
| Condicionar PRAGMAs SQLite al dialecto en db_manager | P1 | Trivial |
| Migrar servicios legacy a usar repositorios | P2 | Alto |
| Crear entidades dominio para Ausencia/Config/Curso | P2 | Medio |
| Eliminar acceso directo a BD desde presentación (36 imports) | P2 | Alto |
| Normalizar campos JSON a tablas relacionales | P2 | Alto |
| Expandir API a CRUD completo | P2 | Alto |

### Fase 8 — UX/UI

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Añadir QValidator a formularios | P2 | Medio |
| Migrar 20+ imports de `ui_styles.py` a `ccleaner_theme.py` | P2 | Medio |
| Accesibilidad (AccessibleName, TabOrder) | P3 | Medio |
| Eliminar tema/ventana legacy | P3 | Bajo |
| Homogeneizar CSS inline en 3 formularios | P3 | Bajo |

### Fase 9 — Organización y Limpieza

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| `git rm --cached data/users.json` | P0 | Trivial |
| Unificar `utils/icons.py` + `utils/icon_manager.py` | P1 | Bajo |
| Mover scripts one-off a `scripts/archive/` | P2 | Trivial |
| Mover tests sueltos de `scripts/` a `tests/` | P2 | Trivial |
| Añadir `__init__.py` a `src/services/` | P2 | Trivial |
| Unificar 4 scripts de benchmark en 1 | P3 | Bajo |

### Fase 10 — Features Pendientes

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Implementar `es_sustitucion`/`profesor_sustituido_id`/`notas` en Guardia | P0 | Medio |
| Resolver TODO olvidado de settings.py (deprecar v3.1→v4.0) | P0 | Bajo |
| Añadir export CSV/Excel de guardias | P1 | Medio |
| Añadir export PDF de informe de ausencias | P1 | Medio |
| Completar import de profesores desde UI (no solo script) | P1 | Medio |
| Implementar import de zonas desde CSV/Excel | P2 | Medio |
| Implementar backup/restore completo | P2 | Alto |
| Implementar import de configuración desde otro curso | P2 | Medio |
| Añadir `capacidad_profesores` y `activa` al modelo Zona | P2 | Bajo |
| Vincular profesores a cursos (`curso_id` en Profesor) | P3 | Alto |

---

## Apéndice: Dependencias Externas

| Integración | Librería | Uso |
|---|---|---|
| GUI | PyQt6 6.7.0 | Interfaz de escritorio |
| BD | SQLAlchemy 2.0 + Alembic | ORM y migraciones |
| API | FastAPI + Uvicorn | REST API |
| SFTP | Paramiko | Sincronización remota |
| SMTP | smtplib (stdlib) | Envío de emails |
| PDF | ReportLab | Exportación de calendarios |
| Excel | openpyxl / pandas | Importación de profesores |
| Optimización | Google OR-Tools (CP-SAT) | Asignación óptima de guardias |
| Gráficos | matplotlib | Dashboards y visualización |
| Métricas | prometheus_client + psutil | Observabilidad |
| Validación | Pydantic | DTOs y settings |
| Logging | structlog | Logging estructurado |
| Linting | Ruff + mypy | Calidad de código |
| Testing | pytest + pytest-qt + pytest-mock | Tests |

---

*Documento generado automáticamente. Última actualización: 16/04/2026.*
