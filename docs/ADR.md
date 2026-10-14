# Architecture Decision Records — Guardias de Patio

Registro de decisiones arquitectónicas significativas del proyecto.  
Formato: [MADR](https://adr.github.io/madr/) simplificado.

---

## ADR-001: Clean Architecture híbrida + DDD táctico

**Estado**: Adoptado  
**Fecha**: 2024-09

### Contexto

Aplicación de escritorio (PyQt6) con API REST (FastAPI) y algoritmo de optimización (OR-Tools CP-SAT). Necesidad de separar lógica de negocio de la infraestructura para facilitar tests unitarios y cambiar tecnologías sin impacto en el dominio.

### Decisión

Arquitectura en capas con separación estricta:

```
domain/          → Entidades, Value Objects, interfaces de repositorio
application/     → Use Cases, DTOs, factories
infrastructure/  → Repos concretos (SQLAlchemy), mappers, DB
presentation/    → PyQt6 (UI)
api/             → FastAPI (REST)
services/        → Servicios legacy (en migración)
```

DDD táctico: entidades con identidad, Value Objects inmutables (`Email`, `HorasContrato`, `Turno`, `ZonaPreferida`), repositorios como interfaces en `domain/`.

### Consecuencias

- Los use cases son testables sin UI ni BD
- Los mappers convierten entre modelos ORM ↔ entidades de dominio
- La capa `services/` (legacy) importa ORM directamente — en migración progresiva

---

## ADR-002: SQLite per-user con Alembic

**Estado**: Adoptado  
**Fecha**: 2024-09

### Contexto

Aplicación multiusuario en local (no servidor). Cada usuario tiene sus propios datos de guardias sin interferencia con otros.

### Decisión

Cada usuario tiene su propia BD SQLite en `data/users/{hash}/guardias_patio.db`. El hash se deriva del nombre de usuario para evitar colisiones. Alembic gestiona migraciones con `env.py` adaptado para localizar la BD por usuario.

### Consecuencias

- No hay servidor de BD → sin dependencias externas para instalación
- Backup sencillo: copiar el directorio del usuario
- Sin soporte multi-usuario concurrente real (SQLite por diseño)
- Las migraciones Alembic deben ejecutarse por cada BD de usuario

---

## ADR-003: OR-Tools CP-SAT para asignación de guardias

**Estado**: Adoptado  
**Fecha**: 2024-10

### Contexto

La asignación de guardias implica múltiples restricciones (turnos, zonas, equidad, disponibilidad, sustituciones). Los algoritmos greedy no garantizan optimalidad ni equidad.

### Decisión

Google OR-Tools CP-SAT (Constraint Programming — SAT solver). El solver recibe:
- Variables de decisión: qué profesor cubre cada franja
- Restricciones duras: disponibilidad, turno, zona preferida
- Restricciones blandas (penalizaciones): equidad de carga, preferencias

Implementado en `src/services/asignador_guardias_cpsat.py`.

### Consecuencias

- Soluciones óptimas o near-óptimas garantizadas
- Tiempo de cómputo acotado con `time_limit_in_seconds`
- Ejecución en `QThread` para no bloquear la UI (PERF-CORE)
- Dependencia de `ortools` (~50 MB) en el paquete final

---

## ADR-004: dependency-injector para wiring en FastAPI

**Estado**: Adoptado  
**Fecha**: 2025-01

### Contexto

La API FastAPI necesita inyectar repositorios y use cases en los endpoints. El patrón manual `Depends(get_db)` funciona pero no escala bien con múltiples dependencias.

### Decisión

`dependency-injector` (>=4.41.0) con un `Container` en `src/infrastructure/container.py`. El wiring se aplica en `src/api/main.py` con `container.wire(modules=[...])`.

Los endpoints usan `@inject` + `Provide[Container.xxx]` para recibir dependencias.

### Consecuencias

- Cambiar implementación de un repositorio no requiere tocar los endpoints
- El `Container` centraliza la configuración de dependencias
- Los tests sobrescriben dependencias con `app.dependency_overrides`
- Requiere activar el virtualenv para que `dependency_injector` compile sus extensiones C

---

## ADR-005: PyQt6 para la interfaz de usuario

**Estado**: Adoptado  
**Fecha**: 2024-09

### Contexto

Aplicación de escritorio nativa en macOS y Windows. Necesidad de widgets avanzados: tablas, calendarios, diálogos modales, progress bars.

### Decisión

PyQt6 6.7.0. Widgets organizados en `src/presentation/` con estructura:
- `windows/` — ventanas principales
- `dialogs/` — diálogos modales
- `widgets/` — widgets reutilizables
- `forms/` — formularios complejos con sub-widgets

### Consecuencias

- Licencia GPL/comercial de Qt — compatible con uso educativo/interno
- Operaciones pesadas (PDF, Excel, CP-SAT) en `QThread` para no bloquear el event loop
- Los tests de UI usan `pytest-qt` con `QApplication` mockeado

---

## ADR-006: FastAPI para API REST interna

**Estado**: Adoptado  
**Fecha**: 2025-01

### Contexto

Necesidad de exponer datos a herramientas externas (dashboards, integraciones futuras) sin acoplar a la UI de PyQt6.

### Decisión

FastAPI con Pydantic v2 para validación. La API corre en un proceso separado (`src/api/main.py`) con Uvicorn. Autenticación JWT (OAuth2 password flow) con `python-jose`.

### Consecuencias

- Documentación OpenAPI automática en `/docs`
- Validación de entrada con Pydantic garantiza integridad
- La API y la UI comparten la misma BD SQLite (mismo proceso o procesos distintos con misma ruta)
- Los endpoints síncronos (no `async def`) se ejecutan en threadpool de Starlette

---

## ADR-007: Ruff como linter y formatter

**Estado**: Adoptado  
**Fecha**: 2024-09

### Contexto

Necesidad de estilo de código consistente y detección de errores estáticos en un proyecto Python moderno.

### Decisión

Ruff (linter + formatter) configurado en `pyproject.toml`:
- `line-length = 100`
- `quote-style = "double"`
- Reglas: E, F, I, N, UP, B, SIM

mypy con strict progresivo: obligatorio en `domain/`, relajado en `presentation/`.

### Consecuencias

- `ruff check --fix` auto-corrige la mayoría de problemas
- Configuración en `pyproject.toml` y `mypy.ini`
- CI puede verificar con `ruff check src/ tests/`

---

## ADR-008: Sincronización SFTP con 1&1 IONOS

**Estado**: Adoptado  
**Fecha**: 2024-11

### Contexto

Necesidad de compartir datos de guardias entre la aplicación local y un servidor remoto para acceso desde múltiples equipos del centro educativo.

### Decisión

Sincronización SFTP bidireccional con Paramiko a un servidor 1&1 IONOS. Credenciales en `sftp_config.json` (gitignored). El módulo `src/sync/` gestiona la conexión con reintentos y progress dialog (`QThread`).

### Consecuencias

- Sin dependencia de servicios cloud de terceros (solo SFTP estándar)
- Las credenciales nunca se versionan
- Requiere conectividad de red — la app funciona offline sin sincronización
- Conflictos de sincronización resueltos por timestamp de modificación
