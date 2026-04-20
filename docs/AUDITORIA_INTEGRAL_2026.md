# Auditoría Integral — Guardias de Patio v5.15.0

> **Fecha**: 20 de abril de 2026 · **Versión**: v5.15.0 · **Tests**: 1.068+ passing · **Coverage**: ~3.68%
>
> **ACTUALIZACIÓN v5.15.0 (20 abr)**: 
> - ✅ ARQ-01 fase core (5 servicios) v5.14.1
> - ✅ ARQ-01 fase extensión #1 (importador_profesores) v5.14.2
> - ✅ ARQ-04 (Contenedor DI) v5.15.0
>
> **SOLO ÍTEMS PENDIENTES** — Los 73+ ítems resueltos (v3.7.0–v5.0.0) han sido eliminados de este documento.
> Cada ítem incluye instrucciones detalladas para que un modelo de IA pueda implementarlo sin ambigüedad.

---

## Contexto técnico del proyecto

- **Stack**: Python 3.11+, PyQt6 6.7.0, SQLAlchemy 2.0, FastAPI, OR-Tools CP-SAT, Pydantic v2
- **Arquitectura**: Clean Architecture híbrida + DDD táctico (entities, VOs, repo pattern)
- **BD**: SQLite per-user (`data/users/{hash}/guardias_patio.db`), migraciones Alembic
- **Entry points**: GUI (`src/main.py`), API REST (`src/api/main.py`)
- **Linter**: Ruff (line-length=100, quote-style=double)
- **Types**: mypy strict progresivo — obligatorio en `domain/`, relajado en `presentation/`
- **Tests**: pytest + pytest-qt. Ejecutar con `make test` o `pytest tests/ -v`
- **Presentación**: 59 archivos PyQt6 (36 forms, 10 dialogs, 10 widgets, 1 component, 1 theme, 1 main window)

---

## Puntuación Global: 29/60

| Dimensión | Nota | Estado |
|---|---|---|
| Arquitectura | 2/4 | ⚠️ |
| Seguridad | 3/4 | ✅ |
| Base de Datos | 2/4 | ⚠️ |
| Rendimiento | 2/4 | ⚠️ |
| Caché | 1/4 | 🔴 |
| Async/Concurrencia | 1/4 | 🔴 |
| Resiliencia | 1/4 | 🔴 |
| API REST | 2/4 | ⚠️ |
| Testing | 2/4 | ⚠️ |
| Observabilidad | 2/4 | ⚠️ |
| UX/UI y Accesibilidad | 1/4 | 🔴 |
| Diseño Visual | 2/4 | ⚠️ |
| Casos de Uso | 3/4 | ✅ |
| Control de Acceso | 3/4 | ✅ |
| Organización | 2/4 | ⚠️ |

---

## Resumen: 68+ ítems pendientes (reducido de 74 tras ARQ-01, ARQ-04)

| Severidad | Cantidad | Cambio |
|---|---|---|
| P0 — Crítico | 1 | JWT API |
| P1 — Alto | 26 | (↓ 6 items tras ARQ-01 core + extensión #1) |
| P2 — Medio | 31 | (↓ 1 item tras ARQ-04) |
| P3 — Bajo | 10 | (sin cambios) |

**Cambios desde v5.6.0 → v5.15.0**:
- ❌ ARQ-01 (5 core): gestor_ausencias, calculador_guardias, orquestador, cpsat, gestor_cursos
- ❌ ARQ-01 (ext #1): importador_profesores
- ❌ ARQ-04: Contenedor DI
- ✅ 22 servicios aún pendientes en ARQ-01

---

## 1. Arquitectura

### ARQ-01 — 28 servicios acoplados a ORM (P1) — ✅ Fase core (5 servicios) RESUELTA v5.14.1; Fase extensión iniciada v5.14.2

**Problema**: 28 archivos en `src/services/` hacen `from sqlalchemy.orm import Session` e invocan `session.query()`, `session.add()`, `session.commit()` directamente. Viola Clean Architecture: la capa de aplicación/servicios no debería conocer SQLAlchemy.

**Progreso**:
- ✅ **Fase core (v5.14.1)**: 5 servicios core completados:
  1. `gestor_ausencias.py` → Clase facade `GestorAusencias`
  2. `calculador_guardias.py` → Session untyped, joinedload eliminado
  3. `orquestador_asignacion_guardias.py` → Session import eliminado
  4. `asignador_guardias_cpsat.py` → Type hints Session eliminados
  5. `gestor_cursos.py` → Ya usa RepositoryFactory (pre-existente)

- ✅ **Fase extensión #1 (v5.14.2)**: 1 servicio:
  1. `importador_profesores.py` → Polimórfico (Session legacy | ProfesorRepository)

**Archivos restantes pendientes (22)**:
1. `src/services/asignacion_guardia_service.py` (L24)
2. `src/services/distribucion_cuotas_service.py` (L31)
3. ~~`src/services/importador_profesores.py` (L13)~~ ✅ RESUELTO v5.14.2
4. `src/services/icalendar_service.py` (L10)
5. `src/services/_pdf_mes_consolidado.py` (L19)
6. `src/services/disponibilidad_profesor_service.py` (L18)
7. `src/services/migrar_a_multi_curso.py` (L17)
8. `src/services/equidad_guardias_service.py` (L20)
9. `src/services/_exportador_import.py` (L19)
10. `src/services/validador_guardias.py` (L17)
11. `src/services/exportador.py` (L31)
12. `src/services/assignment/assignment_executor.py` (L21)
13. `src/services/assignment/slot_builder.py` (L14)
14. `src/services/assignment/profesor_filter.py` (L17)
15. `src/services/_pdf_individual_optimizado.py` (L20)
16. `src/services/estadisticas_service.py` (L13)
17. `src/services/importador_zonas.py` (L16)
18. `src/services/diagnosticador_guardias.py` (L13)
19. `src/services/validators/ausencia_checker.py` (L15)
20. `src/services/asignador_guardias_v4_hibrido.py` (L47)
21. `src/services/_asignador_v4_fases.py` (L21)
22. `src/services/_asignador_v4_helpers.py` (L19)
23. `src/services/exportador_pdf.py` (L28)

**Cómo resolver** (progresivo, no hace falta todo de golpe):

1. **Para cada servicio**, identificar qué queries ORM hace (ej: `session.query(Profesor).filter_by(activo=True).all()`).
2. **Crear interfaz de repositorio** en `src/domain/repositories/` si no existe (ej: `ProfesorRepositoryInterface` con método `obtener_activos() -> list[Profesor]`).
3. **Crear implementación** en `src/infrastructure/repositories/` que use SQLAlchemy (ej: `SQLAlchemyProfesorRepository`).
4. **Refactorizar el servicio** para recibir el repositorio por constructor en vez de `Session`.
5. **Priorizar estos 5 servicios core** primero:
   - `asignador_guardias_cpsat.py` (845L, motor de generación)
   - `calculador_guardias.py` (servicio central)
   - `orquestador_asignacion_guardias.py` (coordinador)
   - `gestor_cursos.py` (CRUD cursos)
   - `gestor_ausencias.py` (CRUD ausencias)

**Verificación**: `grep -rn "from sqlalchemy" src/services/ | wc -l` debe reducirse progresivamente a 0.

---

### ARQ-02 — 22 archivos de presentación importan Session (P2) — ✅ Fase 1 RESUELTA v5.6.0

**Problema**: 22 archivos en `src/presentation/` importan `Session` de SQLAlchemy. 3 de ellos ejecutan queries directas.

**Queries directas (peor caso — resolver primero)** ✅ RESUELTO v5.6.0:
- `src/presentation/forms/asignacion_widgets/generacion_panel.py` L217: `self.session.query(Configuracion).first()`
- `src/presentation/forms/profesor_form.py` L630 y L697: `self.session.query(Profesor).filter_by(id=id_profesor).first()`
- `src/presentation/widgets/gestor_sustituciones.py` L436: `self.session.query(GuardiaModel).filter_by(id=guardia.id).first()`

**Archivos con import de Session** (22, sin query directa — reciben Session como parámetro):
`ajustes_form.py`, `incidencias_panel.py`, `calculo_panel.py`, `cuotas_panel.py`, `resultados_panel.py`, `asignacion_calculo_form.py`, `dashboard_form.py`, `pdf_export_widget.py`, `calendarios_pdf_widget.py`, `informes_estadisticos_widget.py`, `zona_form.py`, `conectividad_form.py`, `asignacion_guardias_form.py`, `base_form.py`, `perfiles_usuario_form.py`, `ccleaner_main_window.py`, `dialogo_crear_curso.py`, `gestion_cursos_widget.py`, `selector_curso_widget.py`

**Cómo resolver**:
1. **Fase 1**: Las 3 queries directas → extraer a use cases en `src/application/use_cases/`:
   - `generacion_panel.py:217` → crear `obtener_configuracion_actual.py`
   - `profesor_form.py:630,697` → crear `obtener_profesor_por_id.py`
   - `gestor_sustituciones.py:436` → crear `obtener_guardia_por_id.py`
2. **Fase 2**: Cambiar firma de constructores de widgets para recibir servicios/use cases en vez de `Session`.

**Verificación**: `grep -rn "session\.query" src/presentation/` debe devolver 0 resultados.

---

### ARQ-04 — Sin contenedor de inyección de dependencias (P2) — ✅ RESUELTO v5.15.0

**Problema**: Los servicios se instancian manualmente pasando `Session` como argumento. No hay lifecycle management ni wiring automático.

**Solución implementada (v5.15.0)**:
1. ✅ Instalado: `pip install dependency-injector>=4.41.0`
2. ✅ Creado: `src/infrastructure/container.py` con `Container(DeclarativeContainer)`:
   - `db_session`: Provider Callable para sesiones (configurable via config.from_dict())
   - Repositorios: profesor, zona, guardia, ausencia, configuracion, curso_escolar
   - `repository_factory`: RepositoryFactory para compatibilidad legacy
3. ✅ Exportado en `src/infrastructure/__init__.py`
4. ✅ Añadido a `requirements.txt`

**Uso (future wiring en main.py/api/main.py)**:
```python
from infrastructure.container import Container

# Inicializar
container = Container()
container.config.from_dict({"db_session_factory": SessionFactory})

# Obtener repos
profesor_repo = container.profesor_repository()
factory = container.repository_factory()
```

**Estado**:
- ✅ Container implementado y funcional (sin wiring automático en main.py — opt-in)
- 📝 Wiring en main.py/api/main.py es fase 2 opcional (no rompe código legacy actual)

---

### ARQ-05 — 7 archivos >800 líneas (P2) — ✅ COMPLETAMENTE RESUELTA v5.11.0

**Archivos y líneas — estado final**:

| Archivo original | L. original | L. final | Módulos extraídos |
|---|---|---|---|
| `src/presentation/widgets/progress_indicators.py` | 1006 | 714 | `progress_handlers.py`, `progress_worker.py` |
| `src/presentation/forms/profesor_form.py` | 848 | 778 | `profesor_table_helpers.py` |
| `src/presentation/widgets/vista_calendario.py` | 969 | 780 | `vista_calendario_helpers.py` |
| `src/presentation/widgets/gestionar_ausencias.py` | 814 | 615 | `dialogo_reasignacion.py` |
| `src/sync/data_exporter.py` | 828 | 564 | `data_exporter_helpers.py` |
| `src/services/asignador_guardias_cpsat.py` | 846 | 637 | `_asignador_cpsat_helpers.py` |
| `src/services/_pdf_individual_optimizado.py` | 827 | 589 | `_pdf_mini_calendario.py` |

**Todos los archivos ≤ 800 líneas. API pública preservada. Smoke test: ✅ limpio.**

---

### ~~ARQ-06 — `ui_styles.py` legacy centralizado (P2)~~ ✅ RESUELTO v5.5.0

**Problema**: `src/ui_styles.py` (351L) define constantes de color y estilos QSS. 40 archivos lo importan. Pero muchos widgets ignoran estas constantes y usan colores inline.

**Archivos que importan `ui_styles`**: 40 (usar `grep -rn "from src.ui_styles\|from src import ui_styles\|import ui_styles" src/` para listar).

**Cómo resolver** (depende de VIS-01 y VIS-02):
1. Primero resolver VIS-01 (design tokens) y VIS-02 (QSS global).
2. Migrar constantes de `ui_styles.py` a `src/presentation/theme/tokens.py`.
3. Reemplazar cada `from src.ui_styles import X` por `from src.presentation.theme.tokens import X`.
4. Una vez que todos los importadores estén migrados, eliminar `src/ui_styles.py`.

---

### ARQ-07 — Sin capa anticorrupción para sync (P3)

**Problema**: `src/sync/data_exporter.py` (825L) accede directamente a modelos ORM para serializar/deserializar datos de sincronización.

**Cómo resolver**: Crear DTOs específicos para sync en `src/sync/dtos.py`. El exporter convierte ORM → DTO, serializa DTO → JSON. El importer deserializa JSON → DTO, convierte DTO → ORM.

---

### ~~ARQ-08 — `pyproject.toml` incompleto (P2)~~ ✅ RESUELTO (pre-existente)

**Problema**: `pyproject.toml` solo tenía `[tool.ruff]` y `[tool.mypy]`. Falta toda la metadata del proyecto.

**Cómo resolver**: Añadir al inicio de `pyproject.toml`:

```toml
[project]
name = "guardias-de-patio"
version = "5.0.0"
description = "Sistema de gestión de guardias de patio para centros educativos"
requires-python = ">=3.11"
dependencies = [
    # Copiar de requirements.txt
]

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project.scripts]
guardias-gui = "src.main:main"
guardias-api = "src.api.main:app"
```

**Verificación**: `pip install -e .` debe funcionar sin error.

---

### ~~ARQ-09 — 5 feature flags huérfanos en settings.py (P3)~~ ✅ RESUELTO (pre-existente)

**Problema**: 5 flags en `src/config/settings.py` que NUNCA se consultan en el código:

| Flag | Línea aprox. | Valor default |
|---|---|---|
| `enable_query_optimization` | ~L80 | `True` |
| `enable_eager_loading` | ~L81 | `True` |
| `enable_profiling` | ~L82 | `False` |
| `enable_metrics` | ~L83 | `False` |
| `cache_enabled` | ~L84 | `True` |

**Nota**: `structured_logging` SÍ se usa en `src/core/logging.py` — NO eliminar.

**Cómo resolver**: Eliminar las 5 líneas de `src/config/settings.py`. Buscar con `grep -rn "enable_query_optimization\|enable_eager_loading\|enable_profiling\|enable_metrics\|cache_enabled" src/` para confirmar que no se usan.

---

## 2. Seguridad

### ~~SEC-12 — `users.json` sin permisos restrictivos (P2)~~ ✅ RESUELTO (pre-existente)

**Problema**: `data/users.json` contiene hashes bcrypt de contraseñas. No se aplican permisos 600 al crear/modificar.

**Dónde está la lógica**: `src/sync/sync_manager.py`, clase `UserAuth`. Buscar los métodos que escriben a `users.json` (probablemente `save_users()` o similar).

**Cómo resolver**: Después de cada escritura a `users.json`, añadir:
```python
import os
os.chmod(users_json_path, 0o600)
```

**Verificación**: `ls -la data/users.json` debe mostrar `-rw-------`.

---

### ~~SEC-14 — Username sin validación backend (P2)~~ ✅ RESUELTO v5.4.0

`crear_perfil.py`: añadida validación con `re.match(r"^[a-zA-Z0-9._-]{3,50}$", username)` — rechaza path traversal y caracteres especiales.

---

### ~~SEC-16 — 273 bloques `except Exception` (P1)~~ ✅ RESUELTO v5.13.0 (59→49, target <50 alcanzado)

**Problema**: 273 bloques capturan `Exception` genérica. Distribución:

| Directorio | Cantidad |
|---|---|
| `presentation/` | 111 |
| `services/` | 45 |
| `infrastructure/` | 44 |
| `sync/` | 23 |
| `core/` | 18 |
| `application/` | 15 |
| `api/` | 13 |
| `utils/` | 4 |

**El peor caso** (silencia completamente el error):
- `src/sync/sync_manager.py` L325: `except Exception: return None`

**Cómo resolver** (por fases):

**Fase 1 — Eliminar los silenciosos** (1 bloque):
- En `src/sync/sync_manager.py:325`: Reemplazar `except Exception: return None` por `except (ConnectionError, OSError) as e: logger.warning("..."); return None`.

**Fase 2 — Migrar los de `services/` (45 bloques)**:
- Para cada bloque, analizar qué operación se hace dentro del `try`.
- Si es query SQLAlchemy: `except SQLAlchemyError as e:`
- Si es I/O de archivos: `except (OSError, IOError) as e:`
- Si es serialización: `except (ValueError, KeyError) as e:`
- Siempre añadir `logger.exception("Descripción del contexto")` dentro del except.

**Fase 3 — Migrar `presentation/` (111 bloques)**: Mismo patrón pero con excepciones Qt.

**Verificación**: `grep -rn "except Exception" src/ | wc -l` debe reducirse progresivamente. Target: <50.

---

### ~~SEC-17 — ~30 `print()` en funciones diagnóstico (P2)~~ ✅ RESUELTO (pre-existente)

Verificado: todos los `print()` en `db_manager.py` y `cache.py` son ejemplos en docstrings (`>>> print(...)`). Las implementaciones reales ya usan `logger.debug()`.

---

### ~~SEC-18 — Sin security headers en API (P3)~~ ✅ RESUELTO v5.2.1

Implementado middleware de seguridad en `src/api/main.py` con `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Strict-Transport-Security`, `Referrer-Policy` y versionado de API por header.

---

## 3. Base de Datos

### ~~DB-05 — Sin CheckConstraints en ORM (P2)~~ ✅ RESUELTO (pre-existente)

**Problema**: `src/infrastructure/database/models.py` no tenía `CheckConstraint` para validar datos a nivel de BD.

**Campos que necesitan constraints**:
- `Guardia.turno` debe ser `'M'` o `'T'`
- `Guardia.recreo` debe ser `>= 1`
- `Ausencia.tipo` debe estar en lista de tipos válidos (buscar el enum/constantes en el código)
- `Profesor.turno` debe ser `'M'`, `'T'` o `'MT'` (verificar valores válidos)

**Cómo resolver**:
1. En `src/infrastructure/database/models.py`, añadir al `__table_args__` de cada modelo:
   ```python
   from sqlalchemy import CheckConstraint

   class Guardia(Base):
       __table_args__ = (
           CheckConstraint("turno IN ('M', 'T')", name="ck_guardia_turno"),
           CheckConstraint("recreo >= 1", name="ck_guardia_recreo_positivo"),
           # ... UniqueConstraints existentes ...
       )
   ```
2. Crear migración Alembic: `alembic revision --autogenerate -m "add_check_constraints"`
3. Aplicar: `alembic upgrade head`

**Verificación**: Insertar una guardia con `turno='X'` debe fallar con `IntegrityError`.

---

### ~~DB-09 — Sin threading locks en db_manager.py (P2)~~ ✅ RESUELTO (pre-existente)

**Problema**: `src/database/db_manager.py` (785L) usa variables globales `_current_engine` y `_current_session_factory` que se modifican sin lock. SQLite no soporta escritura concurrente.

**Nota**: Ya existe retry con backoff para `OperationalError` en `get_db_session()` (L700-720). Lo que falta es un lock explícito para proteger las variables globales.

**Cómo resolver**: Al inicio de `src/database/db_manager.py`:
```python
import threading
_db_lock = threading.Lock()
```
Envolver las funciones que modifican `_current_engine` / `_current_session_factory` con:
```python
with _db_lock:
    _current_engine = create_engine(...)
    _current_session_factory = sessionmaker(bind=_current_engine)
```

**Verificación**: Tests con acceso concurrente no deben producir `OperationalError: database is locked`.

---

### DB-10 — Campos JSON violan 1NF (P3)

**Problema**: Estos campos almacenan JSON como TEXT en SQLite:
- `dias_semana_permitidos` (lista de días)
- `recreos_permitidos` (lista de recreos)
- `recreos_config` (configuración de recreos)

Buscar estos campos en `src/infrastructure/database/models.py`.

**Cómo resolver** (solo si se migra a PostgreSQL): Crear tablas auxiliares:
- `profesor_dias_permitidos` (profesor_id, dia_semana)
- `profesor_recreos_permitidos` (profesor_id, recreo)
- `curso_recreos_config` (curso_id, turno, recreo, hora_inicio, hora_fin)

**Nota**: En SQLite esto es aceptable. Solo priorizar si se migra a PostgreSQL.

---

### ~~DB-11 — Triple estrategia de init de BD (P2)~~ ✅ RESUELTO v5.9.1

**Problema**: `src/database/db_manager.py` usa 3 mecanismos para inicializar la BD:

1. **Alembic** (L48-106): `_run_alembic_migrations()` — Intenta aplicar migraciones
2. **SQL directo** (L108-270): `_apply_direct_migrations()` — Fallback con `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ADD COLUMN` (crea tablas `cursos_escolares` L210, `ausencias` L251, y muchos ALTER TABLE)
3. **`create_all`** (L336, L342, L388): Se ejecuta SIEMPRE, tanto si Alembic funciona como si no

**Flujo actual**: Alembic → si falla → `create_all` + SQL directo. Si Alembic tiene éxito → `create_all` de todas formas.

**Cómo resolver**:
1. Asegurar que TODAS las tablas y columnas estén representadas en migraciones Alembic.
2. Eliminar `_apply_direct_migrations()` (las ~160 líneas de SQL directo, L108-270).
3. Eliminar las llamadas a `Base.metadata.create_all()` (L336, L342, L388).
4. El flujo debe ser: Solo Alembic. Si falla, error claro al usuario.

**Verificación**: Borrar BD de test, ejecutar app → debe crear BD solo con Alembic.

---

### DB-12 — Patrón SQLite per-user bloquea migración web (P1)

**Problema**: Cada usuario tiene su propia BD SQLite en `data/users/{hash}/guardias_patio.db`. Esto hace imposible:
- Queries cross-user
- Concurrencia de escritura
- Migración a servidor web compartido

**Cómo resolver** (diseño, no implementación inmediata):
1. Diseñar schema PostgreSQL multi-tenant con columna `tenant_id` (o `user_id`) en todas las tablas.
2. Script de migración: para cada BD SQLite, leer datos → insertar en PostgreSQL con `tenant_id`.
3. Configurar `DATABASE_URL` como variable de entorno.
4. Patrón: middleware que extrae `tenant_id` del JWT y lo inyecta en queries.

**Este ítem es de diseño/planificación**. No implementar hasta que la API esté completa (API-08).

---

### ~~DB-13 — Sin mecanismo de backup/restore (P2)~~ ✅ RESUELTO v5.9.3

**Problema**: No hay forma automatizada de hacer backup de la BD del usuario ni restaurarla.

**Cómo resolver**:
1. Crear `src/services/backup_service.py` con:
   - `crear_backup(db_path: Path) -> Path`: Copia el archivo `.db` con timestamp.
   - `restaurar_backup(backup_path: Path, db_path: Path)`: Reemplaza la BD actual.
   - `listar_backups(user_dir: Path) -> list[BackupInfo]`: Lista backups disponibles.
2. Almacenar backups en `data/users/{hash}/backups/`.
3. Añadir opción en UI (menú Ajustes o similar) para crear/restaurar backup.

---

## 4. Rendimiento

### ~~PERF-02 — Sin eager loading en queries ORM (P2)~~ ✅ RESUELTO (pre-existente)

**Problema**: Queries ORM cargaban relaciones con lazy loading por defecto.

**Cómo resolver**: En los repositorios/servicios que cargan profesores con sus guardias, o guardias con sus zonas, añadir:
```python
from sqlalchemy.orm import joinedload
session.query(Profesor).options(joinedload(Profesor.guardias)).all()
```
Buscar queries que acceden a relaciones en loops: `grep -rn "\.guardias\|\.zona\|\.profesor\|\.curso" src/services/ src/presentation/`.

---

### ~~PERF-03 — Filtro de disponibilidad en Python (P2)~~ ✅ RESUELTO v5.6.0

**Problema**: La disponibilidad de profesores se filtra en Python (carga todos, filtra en memoria) en vez de en SQL.

**Dónde buscar**: `src/services/disponibilidad_profesor_service.py` (L18) y `src/services/assignment/profesor_filter.py` (L17).

**Cómo resolver**: Mover la lógica de filtrado a una query SQL con `WHERE` y `JOIN`. Ejemplo:
```python
# En vez de:
profesores = session.query(Profesor).all()
disponibles = [p for p in profesores if p.esta_disponible(fecha, turno, recreo)]

# Hacer:
disponibles = session.query(Profesor).filter(
    Profesor.activo == True,
    Profesor.turno.in_([turno, "MT"]),
    ~Profesor.id.in_(
        session.query(Ausencia.profesor_id).filter(
            Ausencia.fecha == fecha
        )
    )
).all()
```

---

### ~~PERF-04 — `.count() > 0` en vez de `.exists()` (P3)~~ ✅ RESUELTO v5.4.0

`sync_manager.py:499`: cambiado `session.query(Profesor).count() == 0` por `session.query(Profesor).first() is None`.

---

### ~~PERF-05 — GUI se bloquea en operaciones pesadas (P2)~~ ✅ RESUELTO (pre-existente)

**Problema**: Generación de PDFs, export Excel y cálculo de guardias (OR-Tools CP-SAT) ejecutan en el hilo principal de Qt, congelando la interfaz.

**Dónde**: Buscar en `src/presentation/` las llamadas a servicios pesados (asignador, exportador_pdf, etc.).

**Cómo resolver**: Para cada operación pesada:
```python
from PyQt6.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            result = self.func(*self.args)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```
Usar con: `self.worker = WorkerThread(generar_guardias, params); self.worker.finished.connect(self.on_done); self.worker.start()`

**Nota**: `progress_indicators.py` (948L) ya tiene indicadores de progreso — conectar las señales.

---

### PERF-06 — 535 `setStyleSheet` inline (P3)

**Problema**: 535 llamadas a `setStyleSheet()` en widgets individuales. Cada una fuerza un repintado. No es cacheable.

**Cómo resolver**: Ver VIS-02 (migrar a QSS global). Una vez migrado, eliminar los `setStyleSheet` inline.

---

## 5. Caché

### ~~CACHE-01 — Sin caché para queries frecuentes (P2)~~ ✅ RESUELTO v5.4.0

**Problema**: Listados de profesores, configuración del curso y zonas se consultan en cada operación sin cachear.

**Cómo resolver**:
1. `pip install cachetools` (ya en requirements.txt, verificar).
2. Crear `src/utils/cache_decorators.py`:
   ```python
   from cachetools import TTLCache
   from functools import wraps

   _caches: dict[str, TTLCache] = {}

   def cached(ttl=60, maxsize=128):
       def decorator(func):
           cache = TTLCache(maxsize=maxsize, ttl=ttl)
           _caches[func.__qualname__] = cache
           @wraps(func)
           def wrapper(*args, **kwargs):
               key = str(args) + str(sorted(kwargs.items()))
               if key in cache:
                   return cache[key]
               result = func(*args, **kwargs)
               cache[key] = result
               return result
           wrapper.cache_clear = cache.clear
           return wrapper
       return decorator

   def invalidate_all():
       for cache in _caches.values():
           cache.clear()
   ```
3. Decorar queries frecuentes: `@cached(ttl=60)` en `obtener_configuracion`, listado de zonas, etc.
4. Invalidar caché en operaciones de escritura: llamar `cache.cache_clear()` después de cada insert/update/delete.

---

### ~~CACHE-02 — Configuración releída en cada operación (P2)~~ ✅ RESUELTO v5.4.0

**Problema**: El use case `src/application/use_cases/obtener_configuracion.py` (o servicio equivalente) ejecuta `session.query(Configuracion).first()` en cada llamada.

**Cómo resolver**: Aplicar `@cached(ttl=60)` de CACHE-01 al método que obtiene configuración. Invalidar al guardar configuración.

---

### ~~CACHE-03 — Sin caché de assets UI (P3)~~ ✅ RESUELTO v5.2.1

Implementado `QPixmapCache` en `src/utils/ui_helpers.py` para reutilizar el pixmap del logo corporativo y evitar cargas repetidas desde disco.

---

## 6. Async/Concurrencia

### ASYNC-01 — FastAPI endpoints síncronos (P2) — ⏸ Bloqueado por DB-12

**Problema**: Todos los endpoints en `src/api/` usan `def` síncrono. Con SQLAlchemy síncrono está bien para desktop, pero en producción web multi-usuario bloqueará el event loop de uvicorn.

**Cómo resolver** (solo cuando se migre a PostgreSQL):
1. Cambiar SQLAlchemy sync por async: `from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine`
2. Cambiar endpoints de `def` a `async def`
3. Usar `asyncpg` como driver de PostgreSQL

**No implementar ahora**. Este ítem se resuelve junto con DB-12 (migración a PostgreSQL).

---

### ~~ASYNC-02 — SFTP sin timeout robusto (P2)~~ ✅ RESUELTO v5.2.1

La conexión SFTP en `src/sync/sync_manager.py` ahora usa `timeout=30`, `banner_timeout=30`, `auth_timeout=30` y `transport.set_keepalive(30)`.

---

## 7. Resiliencia

### ~~RES-02 — Sin circuit breaker para servicios externos (P3)~~ ✅ RESUELTO v5.2.1

Integrado `pybreaker` en `src/sync/sync_manager.py` con circuit breaker para la conexión SFTP y dependencias actualizadas en `requirements.txt` y `pyproject.toml`.

---

### ~~RES-04 — Health check sin verificar dependencias (P3)~~ ✅ RESUELTO (pre-existente)

`/health` ya usa `get_health_checker()` de `src/core/observability/health.py` que verifica BD, caché, configuración y recursos del sistema.
```

---

### RES-05 — Sin graceful shutdown (P3)

**Problema**: La app no gestiona `SIGTERM`/`SIGINT` para cerrar conexiones.

**Cómo resolver**: En `src/main.py` (GUI):
```python
import signal
signal.signal(signal.SIGTERM, lambda s, f: app.quit())
signal.signal(signal.SIGINT, lambda s, f: app.quit())
```
En `src/api/main.py` (FastAPI): Ya gestionado por uvicorn.

---

## 8. API REST

### ~~API-08 — Solo endpoints GET, sin CRUD completo (P1)~~ ✅ RESUELTO v5.8.0

**Problema**: La API en `src/api/` solo tenía endpoints GET.
- `POST /api/v1/auth/token` (login)
- `GET /api/v1/profesores` (con paginación, `response_model=PaginatedProfesoresResponse`)
- `GET /api/v1/profesores/{id}` (`response_model=ProfesorResponse`)
- `GET /api/v1/guardias` (`response_model=List[GuardiaResponse]`)
- `GET /api/v1/guardias/count`
- `GET /api/v1/guardias/export/csv`
- `GET /api/v1/guardias/export/xlsx`
- `GET /api/v1/cuotas`
- `GET /api/v1/equidad`
- `GET /api/v1/estadisticas/resumen`
- `GET /api/v1/estadisticas/por-profesor`
- `GET /health`

**Faltan**: `POST`, `PUT`, `DELETE` para profesores, guardias, zonas, cursos, ausencias.

**Cómo resolver**: Para cada entidad, crear endpoints CRUD. Ejemplo para profesores (en `src/api/routers/profesores.py`):

```python
@router.post("/", response_model=ProfesorResponse, status_code=201)
def crear_profesor(profesor: ProfesorCreate, session: Session = Depends(get_db)):
    ...

@router.put("/{profesor_id}", response_model=ProfesorResponse)
def actualizar_profesor(profesor_id: int, profesor: ProfesorUpdate, ...):
    ...

@router.delete("/{profesor_id}", status_code=204)
def eliminar_profesor(profesor_id: int, ...):
    ...
```

Crear schemas Pydantic `ProfesorCreate` y `ProfesorUpdate` en `src/api/schemas/`. Repetir para: guardias, zonas, cursos, ausencias, configuración.

**Routers a crear/ampliar** (5):
1. `profesores.py` — POST, PUT, DELETE
2. `guardias.py` — POST (generar), DELETE
3. `zonas.py` — GET, POST, PUT, DELETE (router nuevo)
4. `cursos.py` — GET, POST, PUT, DELETE (router nuevo)
5. `ausencias.py` — GET, POST, PUT, DELETE (router nuevo)

---

### ~~API-09 — Sin paginación en otros endpoints (P1)~~ ✅ RESUELTO v5.5.0

**Problema**: Profesores YA tiene paginación (`PaginatedProfesoresResponse`). Pero guardias, estadísticas, cuotas y equidad NO.

**Cómo resolver**: Aplicar el mismo patrón de paginación de profesores a los demás endpoints que devuelven listas. Crear schema genérico:
```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int
```

---

### ~~API-10 — Versionado parcial (P2)~~ ✅ RESUELTO v5.2.1

Añadido header `API-Version: 1` en todas las respuestas HTTP desde `src/api/main.py`, complementando el prefijo `/api/v1` ya existente.

---

### ~~API-12 — Pocos `response_model` en endpoints (P2)~~ ✅ RESUELTO v5.2.1

Añadidos `response_model` en endpoints de cuotas, equidad, conteo de guardias, resumen estadístico y estadísticas por profesor, usando modelos Pydantic alineados con la respuesta real.

---

### ~~API-13 — Sin OpenAPI enrichment (P3)~~ ✅ RESUELTO v5.4.0

`summary=` añadido a todos los endpoints REST (`profesores`, `guardias`, `cuotas`, `equidad`, `estadísticas`). `/health` añadido a tag `sistema`. FastAPI ya tenía `title` y `description`.

---

### API-14 — Sin WebSocket para operaciones largas (P3)

**Problema**: Generación de guardias (OR-Tools CP-SAT) puede tardar minutos. Sin feedback real-time.

**Cómo resolver** (futuro):
```python
from fastapi import WebSocket

@app.websocket("/ws/guardias/generar")
async def generar_guardias_ws(websocket: WebSocket):
    await websocket.accept()
    # Ejecutar generación en background, enviar progreso
    await websocket.send_json({"progress": 50, "message": "Resolviendo..."})
```

---

### ~~API-15 — Sin middleware de logging estructurado (P2)~~ ✅ RESUELTO v5.2.1

Implementado middleware de logging en `src/api/main.py` con `request_id`, duración de petición, método, path, `status_code` y header `X-Request-ID`.

---

## 9. Testing

### TEST-03 — Coverage 47,81% (target: 70%) (P1)

**Coverage estimada por módulo**:
| Módulo | Estimación | Target |
|---|---|---|
| `domain/` | ~65% | 90% |
| `application/` | ~55% | 80% |
| `services/` | ~40% | 70% |
| `presentation/` | ~25% | 50% |
| `api/` | ~50% | 80% |
| `sync/` | ~10% | 60% |
| `infrastructure/` | ~45% | 70% |

**Cómo priorizar**: Ejecutar `pytest --cov=src --cov-report=html` y abrir `htmlcov/index.html`. Ordenar por coverage ascendente. Escribir tests para los archivos más críticos con menos coverage.

**Módulos más rentables** (más impacto por test):
1. `src/domain/` — lógica pura, fácil de testear sin mocks
2. `src/application/use_cases/` — mockear repos, testear lógica
3. `src/services/` que ya tengan repos (si se resuelve ARQ-01)

---

### ~~TEST-04 — 0 tests SFTP/SMTP (P2)~~ ✅ RESUELTO (pre-existente)

**Archivos a testear**: `src/sync/sync_manager.py`, `src/sync/data_exporter.py`, `src/services/email_service.py`

**Cómo resolver**: Crear `tests/test_sync/`:
```python
from unittest.mock import MagicMock, patch

@patch("src.sync.sync_manager.paramiko.SFTPClient")
def test_upload_file(mock_sftp):
    mock_sftp.put.return_value = None
    backend = SFTPSyncBackend(config=test_config)
    result = backend.upload("/local/path", "/remote/path")
    mock_sftp.put.assert_called_once()

@patch("src.services.email_service.smtplib.SMTP")
def test_send_email(mock_smtp):
    ...
```

---

### ~~TEST-05 — Sin tests de integración BD (P2)~~ ✅ RESUELTO (pre-existente)

**Cómo resolver**: Crear `tests/test_integration/` con SQLite in-memory:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database.models import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_crear_profesor(db_session):
    profesor = Profesor(nombre="Test", activo=True, turno="M")
    db_session.add(profesor)
    db_session.commit()
    assert db_session.query(Profesor).count() == 1
```

---

### ~~TEST-06 — Sin mutation testing (P3)~~ ✅ RESUELTO v5.9.7

**Cómo resolver**: `pip install mutmut && mutmut run --paths-to-mutate=src/domain/`

---

### TEST-07 — Sin tests de regresión UI (P3)

**Cómo resolver**: Usar `pytest-qt` para tests funcionales de widgets:
```python
def test_login_dialog(qtbot):
    dialog = LoginDialog()
    qtbot.addWidget(dialog)
    qtbot.keyClicks(dialog.username_input, "admin")
    qtbot.keyClicks(dialog.password_input, "pass")
    assert dialog.username_input.text() == "admin"
```

---

## 10. Observabilidad

### ~~OBS-03 — Sin métricas de negocio (P3)~~ ✅ RESUELTO v5.9.8

**Cómo resolver**: Añadir logs estructurados en operaciones clave:
```python
logger.info("guardias_generadas", extra={"curso_id": curso.id, "cantidad": len(guardias), "duracion_s": elapsed})
```

---

### ~~OBS-04 — Sin request tracing en API (P2)~~ ✅ RESUELTO v5.2.1

**Ya incluido en API-15** (middleware de logging con X-Request-ID).

---

### ~~OBS-05 — Logs sin rotación (P3)~~ ✅ RESUELTO (pre-existente)

`RotatingFileHandler` ya estaba implementado en `src/core/logging.py` (10 MB, 5 backups).

---

### OBS-06 — Sin alertas de error (P3)

**Cómo resolver** (futuro, para producción web): Integrar con servicio de alertas (Sentry, o webhook a email). No necesario para versión desktop.

---

## 11. UX/UI y Accesibilidad (1/4) 🔴

> **Área más débil del proyecto.** 59 archivos de presentación, solo 1 tiene accesibilidad (login_dialog.py).

### Métricas actuales

| Métrica | Actual | Target |
|---|---|---|
| `setAccessibleName` | 6 (1 archivo) | ~200+ (59 archivos) |
| `setAccessibleDescription` | 0 | ~100+ |
| `setTabOrder` | 9 (1 archivo) | ~50+ |
| `QValidator` | 2 (1 archivo) | ~30+ |
| `setToolTip` | 49 | ~100+ |
| `setFocusPolicy` | 1 | ~20+ |

### ~~A11Y-01 — Accessible names (P1)~~ ✅ RESUELTO v5.14.0

**Estado actual**: Solo en `src/presentation/forms/login_dialog.py`:
- L73: `username_input.setAccessibleName("Campo nombre de usuario")`
- L79: `email_input.setAccessibleName("Campo email")`
- L86: `password_input.setAccessibleName("Campo contraseña")`
- L93: `password_confirm_input.setAccessibleName("Campo confirmar contraseña")`
- L405: `username_combo.setAccessibleName("Campo selector de usuario")`
- L418: `password_input.setAccessibleName("Campo contraseña de acceso")`

**Cómo resolver**: En CADA archivo de `src/presentation/` que cree widgets interactivos (inputs, botones, combos, tablas, checkboxes), añadir `widget.setAccessibleName("Descripción")` después de crear el widget.

**Archivos prioritarios** (formularios con más inputs):
1. `profesor_form.py` (851L) — campos: nombre, apellidos, email, teléfono, turno, activo
2. `zona_form.py` — campos: nombre, capacidad, activa
3. `ajustes_form.py` — campos de configuración
4. `gestionar_ausencias.py` (814L) — campos: profesor, fecha, tipo, motivo
5. `asignacion_calculo_form.py` — campos de generación
6. `dashboard_form.py` — botones y controles principales
7. `conectividad_form.py` — campos SFTP/SMTP
8. `import_export_form.py` — botones de import/export
9. `reportes_form.py` — selectores de reportes
10. Todos los diálogos en `src/presentation/dialogs/`

**Convención de nombres accesibles**: Usar formato descriptivo en español: `"Nombre del profesor"`, `"Botón guardar profesor"`, `"Tabla de guardias asignadas"`, `"Selector de turno"`.

---

### ~~A11Y-02 — Tab order (P1)~~ ✅ RESUELTO v5.14.0

**Estado actual**: Solo en `login_dialog.py` L495-498.

**Cómo resolver**: En cada formulario, después de crear todos los widgets, definir el orden de tabulación:
```python
QWidget.setTabOrder(self.campo_nombre, self.campo_apellidos)
QWidget.setTabOrder(self.campo_apellidos, self.campo_email)
QWidget.setTabOrder(self.campo_email, self.combo_turno)
QWidget.setTabOrder(self.combo_turno, self.btn_guardar)
```

**Regla**: El tab order debe seguir el orden visual de arriba abajo, izquierda a derecha.

---

### ~~A11Y-03 — Validación de formularios (P1)~~ ✅ RESUELTO v5.3.0

`QRegularExpressionValidator` añadido en `datos_basicos_widget.py` (nombre, email), `datos_zona_widget.py` (nombre) y `ajustes_widget.py` (multiplicadores decimales).

---

### ~~A11Y-04 — Contraste de colores sin verificar (P2)~~ ✅ RESUELTO v5.10.0

**Problema**: 415 colores hexadecimales hardcodeados en `src/presentation/`. WCAG 2.1 exige ratio mínimo 4.5:1 para texto y 3:1 para componentes UI.

**Implementado**: Ajustados tokens semánticos en [src/presentation/theme/tokens.py](src/presentation/theme/tokens.py) (`SUCCESS`, `WARNING`, `INFO`) para cumplir AA en texto normal sobre blanco.

---

### ~~A11Y-05 — Soporte de teclado incompleto (P2)~~ ✅ RESUELTO v5.3.0

`zona_form.py` ãñadidos Ctrl+S (guardar), F5 (refrescar), Esc (limpiar). `ajustes_form.py` ãñadido Ctrl+S al botón Guardar. `profesor_form.py` ya tenía Ctrl+S, F5, Esc, Del, Ctrl+A.

---

### ~~A11Y-06 — Sin feedback para screen readers (P2)~~ ✅ RESUELTO v5.10.0

**Implementado**: Añadido helper `announce()` en [src/utils/ui_helpers.py](src/utils/ui_helpers.py) e integrado en `show_info`, `show_warning` y `show_error` para anunciar mensajes críticos de forma centralizada.

**Nota técnica**: En esta build de PyQt6 `QAccessible` puede no estar disponible; la implementación es defensiva y no rompe la UI si falta el backend de accesibilidad.
```python
from PyQt6.QtWidgets import QAccessibleEvent
from PyQt6.QtCore import QAccessible

# Anunciar un cambio
event = QAccessibleEvent(self.status_label, QAccessible.Event.NameChanged)
QAccessible.updateAccessibility(event)
```

---

### ~~A11Y-07 — Tamaños de fuente fijos (P2)~~ ✅ RESUELTO v5.10.0

**Estado**: Las fuentes activas ya usan tokens tipográficos (`FontSize`) o fuentes por defecto sin tamaño absoluto fijo en `presentation/`.

**Cómo resolver**: En vez de tamaños absolutos, usar escala relativa basada en la fuente del sistema:
```python
base_font = QApplication.font()
base_size = base_font.pointSize()  # Tamaño del sistema

heading_font = QFont(base_font)
heading_font.setPointSize(int(base_size * 1.5))  # 150% para headings
```

Se resuelve junto con VIS-05 (escala tipográfica).

---

### A11Y-08 — Sin tema de alto contraste (P3)

**Cómo resolver**: Crear `src/presentation/theme/high_contrast.qss` con colores blanco/negro puros y bordes gruesos. Cargar cuando el usuario lo seleccione en ajustes.

---

### A11Y-09 — Sin internacionalización (P3)

**Estado actual**: Solo 2 usos de `tr()` en todo el proyecto.

**Cómo resolver** (futuro): Wrappear todos los strings visibles con `self.tr("texto")`. Generar archivos `.ts` con `pylupdate6`. Compilar a `.qm` con `lrelease`.

---

### ~~A11Y-10 — Sin DPI awareness (P2)~~ ✅ RESUELTO (pre-existente)

**Problema**: 191 tamaños fijos. En pantallas HiDPI se veían diminutos.

**Cómo resolver**:
1. En `src/main.py`, ANTES de crear `QApplication`:
   ```python
   from PyQt6.QtCore import Qt
   # PyQt6 tiene HiDPI habilitado por defecto, pero verificar que no se desactive
   ```
2. Reemplazar progresivamente `setFixedSize(400, 300)` por `setMinimumSize(400, 300)` + `setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)`.
3. Buscar: `grep -rn "setFixedSize\|setGeometry\|setMinimumWidth\|setMinimumHeight\|setMaximumWidth\|setMaximumHeight" src/presentation/`

---

## 12. Diseño Visual y Consistencia

### Métricas actuales

| Métrica | Valor |
|---|---|
| `setStyleSheet` inline | 535 |
| Colores hex hardcodeados | 415 |
| Fuentes hardcodeadas | 269 |
| Imports de `ui_styles.py` | 40 |
| Tamaños fijos | 191 |

### ~~VIS-01 — Crear sistema de design tokens (P1)~~ ✅ RESUELTO v5.5.0 (parcial: tokens.py + light.qss creados)

**Problema**: 415 colores hardcodeados inline. No hay paleta centralizada.

**Cómo resolver**:
1. Crear `src/presentation/theme/__init__.py` (vacío).
2. Crear `src/presentation/theme/tokens.py`:
   ```python
   """Design tokens centralizados para toda la aplicación."""

   class Colors:
       # Primarios
       PRIMARY = "#1976D2"
       PRIMARY_LIGHT = "#42A5F5"
       PRIMARY_DARK = "#1565C0"
       # Semánticos
       SUCCESS = "#10B981"
       WARNING = "#F59E0B"
       ERROR = "#DC2626"
       INFO = "#3B82F6"
       # Superficies
       BACKGROUND = "#FFFFFF"
       SURFACE = "#F8FAFC"
       BORDER = "#E2E8F0"
       # Texto
       TEXT_PRIMARY = "#1E293B"
       TEXT_SECONDARY = "#64748B"
       TEXT_DISABLED = "#94A3B8"
       TEXT_ON_PRIMARY = "#FFFFFF"

   class Spacing:
       XS = 4
       SM = 8
       MD = 12
       LG = 16
       XL = 24
       XXL = 32

   class FontSize:
       CAPTION = 11
       BODY = 13
       SUBTITLE = 15
       TITLE = 18
       H2 = 22
       H1 = 28

   class BorderRadius:
       SM = 4
       MD = 8
       LG = 12
   ```
3. Reemplazar progresivamente los colores hardcodeados: `"#DC2626"` → `Colors.ERROR`, `"#1976D2"` → `Colors.PRIMARY`, etc.

**Verificación**: `grep -rn "#[0-9a-fA-F]\{6\}" src/presentation/ | wc -l` debe reducirse de 415 a 0 progresivamente.

---

### ~~VIS-02 — Migrar 535 `setStyleSheet` a QSS global (P1)~~ ✅ RESUELTO v5.12.0

**Cómo resolver**:
1. Crear `src/presentation/theme/light.qss`:
   ```css
   QPushButton {
       background-color: #1976D2;
       color: white;
       border-radius: 8px;
       padding: 8px 16px;
       font-size: 13px;
   }
   QPushButton:hover {
       background-color: #1565C0;
   }
   /* ... más estilos base para todos los widgets estándar */
   ```
2. En `src/main.py`, al crear `QApplication`:
   ```python
   with open("src/presentation/theme/light.qss") as f:
       app.setStyleSheet(f.read())
   ```
3. Eliminar progresivamente los `setStyleSheet(...)` inline de cada widget que ya esté cubierto por el QSS global.

**Buscar inline styles**: `grep -rn "setStyleSheet" src/presentation/ | wc -l` (objetivo: reducir de 535 a <50 para estilos truly custom).

---

### ~~VIS-03 — Deprecar `ui_styles.py` legacy (P2)~~ ✅ RESUELTO v5.5.0

**Archivo**: `src/ui_styles.py` (351L). Define constantes de color (L7-16), estilos QSS como strings (L18+), y función `wrap_terminal_html()` (L290).

**40 archivos lo importan** (`from src.ui_styles import ...` o `from src import ui_styles`).

**Cómo resolver** (después de VIS-01 y VIS-02):
1. Mover constantes de color a `tokens.py` (VIS-01).
2. Mover estilos a `light.qss` (VIS-02).
3. Mover `wrap_terminal_html()` a `src/utils/html_helpers.py`.
4. Actualizar los 40 imports.
5. Eliminar `src/ui_styles.py`.

---

### ~~VIS-04 — Iconografía inconsistente (P2)~~ ✅ RESUELTO v5.10.0

**Implementado**: Añadido helper `get_icon(name, fallback)` en [src/utils/ui_helpers.py](src/utils/ui_helpers.py) con carga desde `imagenes/icons/` y cache con `QPixmapCache`.

**Cómo resolver**: Elegir una familia de iconos (Material Design Icons, Feather, o similar). Descargar SVGs. Colocar en `src/presentation/assets/icons/`. Crear helper:
```python
def get_icon(name: str) -> QIcon:
    return QIcon(f"src/presentation/assets/icons/{name}.svg")
```

---

### ~~VIS-05 — Sin escala tipográfica (P2)~~ ✅ RESUELTO v5.5.0

**Cómo resolver**: Ya definida en VIS-01 (`FontSize`). Reemplazar fuentes hardcodeadas por los tokens:
```python
# En vez de: font.setPointSize(14)
from src.presentation.theme.tokens import FontSize
font.setPointSize(FontSize.BODY)
```

---

### ~~VIS-06 — Espaciado inconsistente (P2)~~ ✅ RESUELTO v5.5.0

**Cómo resolver**: Ya definido en VIS-01 (`Spacing`). Usar en layouts:
```python
from src.presentation.theme.tokens import Spacing
layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
layout.setSpacing(Spacing.MD)
```

---

### VIS-07 — Sin tema oscuro (P3)

**Cómo resolver** (después de VIS-01 y VIS-02):
1. Crear `src/presentation/theme/dark.qss` con colores invertidos.
2. Crear `src/presentation/theme/dark_tokens.py` con la paleta oscura.
3. Añadir selector de tema en ajustes.

---

### VIS-08 — Sin animaciones/transiciones (P3)

**Cómo resolver**: Usar `QPropertyAnimation` para transiciones clave:
```python
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

anim = QPropertyAnimation(widget, b"windowOpacity")
anim.setDuration(200)
anim.setStartValue(0)
anim.setEndValue(1)
anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
anim.start()
```

---

### ~~VIS-09 — Sin responsive layout (P2)~~ ✅ RESUELTO v5.10.0

**Implementado**: Eliminados `setFixedSize` en diálogos de cursos y selector de curso; sustituido tamaño rígido del logo de sidebar por rango mínimo/máximo en [src/presentation/components/ccleaner_sidebar.py](src/presentation/components/ccleaner_sidebar.py).

**Cómo resolver**: Reemplazar tamaños fijos por policies:
```python
# En vez de: widget.setFixedSize(400, 300)
widget.setMinimumSize(300, 200)
widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
```

---

### VIS-10 — Sin guía de estilo documentada (P3)

**Cómo resolver**: Crear `docs/DESIGN_SYSTEM.md` documentando tokens de color, tipografía, espaciado, y componentes.

---

## 13. Casos de Uso y Flujos

### ~~UXF-01 — Sustituciones incompletas (P2)~~ ✅ RESUELTO v5.7.0

**Problema**: Los campos ORM existen en `src/infrastructure/database/models.py` (`es_sustitucion`, `profesor_sustituido_id`, `notas` en el modelo `Guardia`) pero la UI en `src/presentation/widgets/gestor_sustituciones.py` estaba incompleta.

**Cómo resolver**: Completar el widget `gestor_sustituciones.py` con:
1. Selector de profesor a sustituir (QComboBox con profesores del mismo turno)
2. Campo de notas (QTextEdit)
3. Checkbox para marcar como sustitución
4. Lógica para crear guardia con `es_sustitucion=True` y `profesor_sustituido_id=X`

---

### ~~UXF-02 — Sin confirmación en acciones destructivas (P2)~~ ✅ RESUELTO v5.0.x

Todos los métodos de borrado (`eliminar_profesor`, `eliminar_zona`, `_eliminar_curso_seleccionado`, `_on_eliminar` perfiles, `eliminar_ausencia_seleccionada`) ya tienen `QMessageBox.question` o diálogo personalizado de confirmación.

---

### UXF-03 — Sin undo/redo (P3)

**Cómo resolver** (futuro): Implementar `QUndoStack` + `QUndoCommand` para las operaciones CRUD principales.

---

### UXF-04 — Sin onboarding wizard (P3)

**Cómo resolver**: Crear `src/presentation/dialogs/wizard_primer_uso.py` con `QWizard`:
- Página 1: Crear curso escolar
- Página 2: Importar/crear zonas
- Página 3: Importar/crear profesores
- Página 4: Configurar recreos
Mostrar solo si no hay cursos en la BD.

---

### ~~UXF-05 — Sin indicador de cambios sin guardar (P2)~~ ✅ RESUELTO v5.3.0

`ajustes_form.py`: añadido `_dirty` flag, label `● Cambios sin guardar` (visible/oculto), conexión de señales tras carga inicial, y reset en `guardar_configuracion` / `cargar_configuracion`.
---

## 14. Control de Acceso

### MT-04 — Sin roles/permisos (P3)

**Problema**: Todos los usuarios autenticados tienen acceso completo.

**Cómo resolver** (futuro, cuando sea necesario):
1. Añadir campo `role` a `users.json` (valores: `admin`, `editor`, `viewer`).
2. En API: verificar role en cada endpoint con dependency.
3. En GUI: deshabilitar botones según role.

---

## 15. Organización de Código

### ORG-01 — Archivos mal ubicados (P2) — ✅ Fase 1 RESUELTA v5.10.0

**Problema**: Servicios que deberían ser use cases, utils que son domain services.

**Avance v5.10.0**:
- Movido `cache_service` a [src/application/use_cases/configuracion/cache_service.py](src/application/use_cases/configuracion/cache_service.py).
- [src/services/cache_service.py](src/services/cache_service.py) queda como shim de compatibilidad para imports legacy.

**Cómo resolver**: Auditar `src/services/` y mover lo que sea lógica de aplicación a `src/application/use_cases/`. Auditar `src/utils/` y mover lo que sea lógica de dominio a `src/domain/services/`.

---

### ~~ORG-02 — Duplicación de estilos (P2)~~ ✅ RESUELTO v5.12.0

**Ya cubierto por VIS-01, VIS-02 y VIS-03.** Se resuelve con el sistema de temas.
Estado actual: VIS-01, VIS-02 y VIS-03 resueltos.

---

### ORG-03 — Archivos grandes (P3)

**Ya cubierto por ARQ-05.** Split de los 7 archivos >800L.

---

## 16. Sanitización

### ~~SAN-01 — 273 `except Exception` genéricos (P1)~~ ✅ RESUELTO (pre-existente)
Revisión manual confirma: todos los `except Exception` o bien hacen `raise` (re-lanzan), o loggean + re-lanzan. No hay `except Exception: pass` silenciosos en producción. Los 2 casos en `decorators.py` hacen `raise` explícito.
**Ya cubierto por SEC-16.** Mismo ítem.

---

### ~~SAN-03 — 1 TODO pendiente (P3)~~ ✅ RESUELTO v5.5.0

**Cómo encontrar**: `grep -rn "TODO\|FIXME\|HACK\|XXX" src/`

**Cómo resolver**: Leer el TODO, resolverlo o eliminarlo si ya no aplica.

---

## 17. Preparación Web (5/10)

| Aspecto | Estado | Bloqueador |
|---|---|---|
| API REST existe | ✅ | — |
| JWT + CORS + Rate Limit | ✅ | — |
| Error schema estándar | ✅ | — |
| Paginación (profesores) | ✅ | — |
| CRUD completo API | 🔴 | Solo GET → API-08 |
| Paginación (otros) | 🔴 | → API-09 |
| BD multi-tenant | 🔴 | SQLite per-user → DB-12 |
| Domain logic puro | ⚠️ | 28 servicios acoplados → ARQ-01 |
| Async endpoints | ⚠️ | → ASYNC-01 (con PostgreSQL) |
| Frontend desacoplado | 🔴 | UI = PyQt6 monolítica |

**Ruta de migración**:
1. **Fase 1**: CRUD completo API (API-08) + paginación (API-09) + response_model (API-12)
2. **Fase 2**: Desacoplar servicios de ORM (ARQ-01) + eliminar queries de presentation (ARQ-02)
3. **Fase 3**: Migrar SQLite → PostgreSQL (DB-12) + async (ASYNC-01)
4. **Fase 4**: Frontend web (SPA React/Vue consumiendo API)

---

## 18. Roadmap Priorizado

### P1 — 10 ítems críticos

| # | ID | Descripción | Esfuerzo |
|---|---|---|---|
| 1 | SEC-16 | ~~Reducir 273 `except Exception` a <50 con excepciones específicas~~ ✅ RESUELTO v5.1.1 | XL |
| 2 | ARQ-01 | ~~Migrar 5 servicios core de Session a repositorios inyectados~~ ✅ RESUELTO v5.14.1 | XL |
| 3 | API-08 | CRUD completo API (POST/PUT/DELETE) para 5 entidades | XL |
| 4 | TEST-03 | Subir coverage de 47,81% a 70% | XL |
| 5 | A11Y-01 | `setAccessibleName` en todos los widgets interactivos | L |
| 6 | A11Y-02 | `setTabOrder` en todos los formularios y diálogos | M |
| 7 | ~~A11Y-03~~ | ~~`QValidator` en todos los campos de formularios~~ ✅ RESUELTO v5.3.0 | L |
| 8 | VIS-01 | ~~Crear sistema de design tokens centralizado ~~ ✅ RESUELTO v5.1.0| M |
| 9 | VIS-02 | ~~QSS global, eliminar `setStyleSheet` inline ~~ ✅ RESUELTO v5.1.0| XL |
| 10 | DB-12 | Diseñar migración SQLite → PostgreSQL multi-tenant | L |

### P2 — 38 ítems

| # | ID | Descripción | Esfuerzo |
|---|---|---|---|
| 1 | ARQ-02 | Eliminar 3 queries directas + 22 imports Session de presentation/ | L |
| 2 | ARQ-04 | Implementar contenedor DI con dependency-injector | L |
| 3 | ARQ-05 | Split 7 archivos >800L | L |
| 4 | ~~ARQ-06~~ | ~~Migrar imports de ui_styles.py a nuevo sistema temas~~ ✅ RESUELTO v5.5.0 | M |
| 5 | ARQ-08 | ~~Completar pyproject.toml ([project], [build-system]) ~~ ✅ RESUELTO v5.1.0| S |
| 6 | SEC-12 | ~~chmod 600 en users.json al crear/modificar~~ ✅ RESUELTO v5.0.x | S |
| 7 | ~~SEC-14~~ | ~~Validar username con regex en backend (UserAuth)~~ ✅ RESUELTO v5.4.0 | S |
| 8 | SEC-17 | ~~Reemplazar ~30 print() por logger en db_manager.py y cache.py ~~ ✅ RESUELTO v5.1.0| S |
| 9 | DB-05 | ~~Añadir CheckConstraints + migración Alembic~~ ✅ RESUELTO v5.2.0 | S |
| 10 | DB-09 | ~~Añadir threading.Lock en db_manager.py~~ ✅ RESUELTO v5.1.2 | S |
| 11 | DB-11 | ~~Unificar init BD en Alembic (eliminar create_all + SQL directo)~~ ✅ RESUELTO v5.9.1 | M |
| 12 | DB-13 | ~~Implementar backup/restore automático~~ ✅ RESUELTO v5.9.3 | L |
| 13 | PERF-02 | ~~Eager loading (joinedload) en queries de listados~~ ✅ RESUELTO v5.2.0 | M |
| 14 | ~~PERF-03~~ | ~~Mover filtro disponibilidad de Python a SQL~~ ✅ RESUELTO v5.6.0 | M |
| 15 | PERF-05 | QThread para operaciones pesadas (PDF, Excel, CP-SAT) | L |
| 16 | ~~CACHE-01~~ | ~~Implementar cachetools.TTLCache para queries frecuentes~~ ✅ RESUELTO v5.4.0 | M |
| 17 | ~~CACHE-02~~ | ~~Cachear obtener_configuracion con TTL 60s~~ ✅ RESUELTO v5.4.0 | S |
| 18 | ASYNC-01 | FastAPI async (cuando se migre a PostgreSQL) | XL |
| 19 | ~~ASYNC-02~~ | ~~Timeout robusto en conexiones SFTP (transport.set_keepalive)~~ ✅ RESUELTO v5.2.1 | S |
| 20 | ~~API-09~~ | ~~Paginación en endpoints de guardias, estadísticas~~ ✅ RESUELTO v5.5.0 | M |
| 21 | ~~API-10~~ | ~~Documentar estrategia versionado + header API-Version~~ ✅ RESUELTO v5.2.1 | S |
| 22 | ~~API-12~~ | ~~response_model Pydantic en todos los endpoints~~ ✅ RESUELTO v5.2.1 | M |
| 23 | ~~API-15~~ | ~~Middleware logging estructurado con X-Request-ID~~ ✅ RESUELTO v5.2.1 | M |
| 24 | TEST-04 | Tests SFTP/SMTP con Paramiko/smtplib mockeado | L |
| 25 | TEST-05 | Tests integración BD con SQLite in-memory | L |
| 26 | ~~OBS-04~~ | ~~Request tracing (junto con API-15)~~ ✅ RESUELTO v5.2.1 | M |
| 27 | A11Y-04 | Auditar contraste colores WCAG 2.1 | M |
| 28 | ~~A11Y-05~~ | ~~Atajos de teclado para acciones principales~~ ✅ RESUELTO v5.3.0 | M |
| 29 | A11Y-06 | Feedback QAccessible para screen readers | M |
| 30 | A11Y-07 | Tamaños fuente relativos (no hardcoded) | M |
| 31 | A11Y-10 | DPI awareness + reemplazar setFixedSize por policies | M |
| 32 | VIS-03 | ~~Deprecar y eliminar ui_styles.py ~~ ✅ RESUELTO v5.1.0| M |
| 33 | VIS-04 | Iconografía consistente (Material Icons o similar) | M |
| 34 | ~~VIS-05~~ | ~~Escala tipográfica con FontSize tokens~~ ✅ RESUELTO v5.5.0 | S |
| 35 | ~~VIS-06~~ | ~~Escala de espaciado con Spacing tokens~~ ✅ RESUELTO v5.5.0 | S |
| 36 | VIS-09 | Responsive layouts (reemplazar tamaños fijos) | L |
| 37 | UXF-01 | Completar UI de sustituciones | M |
| 38 | ~~UXF-02~~ | ~~Confirmación en acciones destructivas~~ ✅ RESUELTO v5.0.x | S |
| 39 | ~~UXF-05~~ | ~~Indicador de cambios sin guardar~~ ✅ RESUELTO v5.3.0 | M |

### P3 — 26 ítems

| # | ID | Descripción | Esfuerzo |
|---|---|---|---|
| 1 | ARQ-07 | Capa anticorrupción para sync (DTOs) | M |
| 2 | ARQ-09 | ~~Eliminar 5 feature flags huérfanos de settings.py ~~ ✅ RESUELTO v5.1.0| S |
| 3 | ~~SEC-18~~ | ~~Security headers middleware en API~~ ✅ RESUELTO v5.2.1 | S |
| 4 | DB-10 | Normalizar campos JSON a tablas (si PostgreSQL) | L |
| 5 | ~~PERF-04~~ | ~~.exists() en vez de .count() > 0~~ ✅ RESUELTO v5.4.0 | S |
| 6 | PERF-06 | Reducir setStyleSheet inline (con VIS-02) | L |
| 7 | ~~CACHE-03~~ | ~~QPixmapCache para assets UI~~ ✅ RESUELTO v5.2.1 | S |
| 8 | ~~RES-02~~ | ~~Circuit breaker con pybreaker para SFTP/SMTP~~ ✅ RESUELTO v5.2.1 | M |
| 9 | ~~RES-04~~ | ~~Health check con verificación de BD/disco~~ ✅ RESUELTO (pre-existente) | S |
| 10 | RES-05 | ~~Graceful shutdown (signal handlers) ~~ ✅ RESUELTO v5.1.0| S |
| 11 | ~~API-13~~ | ~~OpenAPI enrichment (tags, descriptions, examples)~~ ✅ RESUELTO v5.4.0 | S |
| 12 | API-14 | WebSocket para progreso de generación guardias | L |
| 13 | TEST-06 | ~~Mutation testing con mutmut~~ ✅ RESUELTO v5.9.7 | M |
| 14 | TEST-07 | Tests regresión UI con pytest-qt | M |
| 15 | OBS-03 | ~~Métricas de negocio en logs~~ ✅ RESUELTO v5.9.8 | M |
| 16 | ~~OBS-05~~ | ~~RotatingFileHandler (10MB, 5 backups)~~ ✅ RESUELTO (pre-existente) | S |
| 17 | OBS-06 | Alertas de error (Sentry o webhook) | M |
| 18 | A11Y-08 | Tema alto contraste | L |
| 19 | A11Y-09 | Internacionalización con tr() | XL |
| 20 | VIS-07 | Tema oscuro | L |
| 21 | VIS-08 | Animaciones/transiciones (QPropertyAnimation) | M |
| 22 | VIS-10 | Guía de estilo documentada (DESIGN_SYSTEM.md) | M |
| 23 | MT-04 | Roles/permisos RBAC (admin/editor/viewer) | L |
| 24 | UXF-03 | Undo/redo con QUndoStack | L |
| 25 | UXF-04 | Onboarding wizard para primer uso | M |
| 26 | ~~SAN-03~~ | ~~Resolver/eliminar TODO pendiente~~ ✅ RESUELTO v5.5.0 | S |

### Escala de esfuerzo

| Escala | Horas estimadas |
|---|---|
| S (Small) | < 2h |
| M (Medium) | 2–6h |
| L (Large) | 6–16h |
| XL (Extra Large) | 16+h |

---

*Última actualización: 20 de abril de 2026 (v5.15.0) — Solo ítems pendientes, con instrucciones detalladas para implementación.*
# Auditoría Integral — Guardias de Patio v5.0.0

> **Fecha**: 19 de abril de 2026
> **Versión auditada**: v5.0.0 (commit `68b6a79`)
> **Autor**: Auditoría automatizada + revisión manual
> **Alcance**: Arquitectura, seguridad, BD, rendimiento, API, testing, UX/UI, accesibilidad, diseño visual, casos de uso, escalabilidad, preparación web

---

## Puntuación Global de Salud

| Dimensión | Puntuación (0-4) | Estado |
|---|---|---|
| Arquitectura | 2 | ⚠️ Aceptable |
| Seguridad | 3 | ✅ Bueno |
| Base de Datos | 2 | ⚠️ Aceptable |
| Rendimiento | 2 | ⚠️ Aceptable |
| Caché | 1 | 🔴 Deficiente |
| Async/Concurrencia | 1 | 🔴 Deficiente |
| Escalabilidad y Resiliencia | 1 | 🔴 Deficiente |
| API REST | 2 | ⚠️ Aceptable |
| Testing | 2 | ⚠️ Aceptable |
| Observabilidad | 2 | ⚠️ Aceptable |
| **UX/UI y Accesibilidad** | **1** | **🔴 Deficiente** |
| **Diseño Visual y Consistencia** | **2** | **⚠️ Aceptable** |
| **Casos de Uso y Flujos** | **3** | **✅ Bueno** |
| Control de Acceso | 3 | ✅ Bueno |
| Organización de Código | 2 | ⚠️ Aceptable |
| **TOTAL** | **29/60** | **⚠️ Aceptable** |

---

## Resumen Ejecutivo

**147 hallazgos** clasificados por severidad:

| Severidad | Cantidad | Descripción |
|---|---|---|
| P0 — Crítico | 0 | Bloqueantes de producción |
| P1 — Alto | 18 | Deben resolverse antes de próxima major |
| P2 — Medio | 34 | Planificar en próximos sprints |
| P3 — Bajo | 22 | Mejoras incrementales |
| ✅ Resuelto | 73 | Completados en v3.7.0–v5.0.0 |

**Fortalezas**: Autenticación JWT completa, política contraseñas robusta, 1.342 tests passing, error boundary GUI, benchmarks unificados, import/export CSV/Excel funcional.

**Debilidades principales**: Accesibilidad casi inexistente (6 `setAccessibleName` en 59 widgets), 28 servicios acoplados a ORM, 289 bloques `except Exception`, 415 colores hardcodeados, arquitectura SQLite per-user bloquea migración web.

---

## 1. Arquitectura (2/4)

### ARQ-01 — Servicios acoplados a ORM (P1)
**28 servicios** en `src/services/` importan `Session` de SQLAlchemy directamente, violando Clean Architecture. La capa de aplicación debería depender solo de interfaces de repositorio.

**Archivos afectados** (24 con `session.query`, 248 refs totales):
- `src/services/asignador_guardias_cpsat.py` (845L)
- `src/services/_pdf_individual_optimizado.py` (827L)
- `src/services/exportador_pdf.py`
- `src/services/calculador_guardias.py`
- `src/services/gestor_sustituciones_service.py`
- Y 19+ más

**Acción**: ~~Migrar 5 servicios core a repositorios/facades y eliminar imports `Session/joinedload` innecesarios~~ ✅ RESUELTO v5.14.1

**Pendiente**: Continuar la migración progresiva del resto de servicios legacy en `src/services/`.

### ARQ-02 — Widgets con queries SQLAlchemy (P2) — ✅ Fase 1 RESUELTA v5.6.0
**4 widgets** en `presentation/` ejecutan queries directas:
- Referencia: `session.query` encontrado en 4 archivos de presentación

**Acción**: Extraer a use cases en `application/`.

### ARQ-03 — Domain services contaminados (P1)
4 domain services importan infraestructura (SQLAlchemy, paths de BD), violando la regla de dependencia DDD.

**Acción**: Invertir dependencias con interfaces en `domain/repositories/`.

### ARQ-04 — Ausencia de contenedor DI (P2)
No hay framework de inyección de dependencias. Los servicios se instancian manualmente con `Session` hardcodeada.

**Acción**: Evaluar `dependency-injector` para gestión de lifecycle y wiring automático.

### ARQ-05 — Archivos grandes sin split (P2)
**8 archivos >800 líneas**:

| Archivo | Líneas |
|---|---|
| `presentation/widgets/vista_calendario.py` | 957 |
| `presentation/widgets/progress_indicators.py` | 948 |
| `presentation/forms/profesor_form.py` | 851 |
| `services/asignador_guardias_cpsat.py` | 845 |
| `services/_pdf_individual_optimizado.py` | 827 |
| `sync/data_exporter.py` | 825 |
| `presentation/widgets/gestionar_ausencias.py` | 814 |

**Acción**: Split por responsabilidad (ej: vista_calendario → calendario_view + calendario_controller).

### ~~ARQ-06 — `ui_styles.py` legacy centralizado (P2)~~ ✅ RESUELTO v5.5.0
40 archivos importan de `ui_styles.py`. Patrón monolítico que dificulta theming y tree-shaking.

**Acción**: Migrar a sistema de tokens de diseño (design tokens) con tema claro/oscuro.

### ARQ-07 — Sin capa anticorrupción para sync (P3)
`src/sync/` accede directamente a modelos ORM y construye SQL.

**Acción**: Abstraer con DTOs de sincronización.

### ~~ARQ-08 — `pyproject.toml` incompleto (P2)~~ ✅ RESUELTO (pre-existente)
Falta sección `[project]` y `[build-system]`. Sin metadata de dependencias formales.

**Acción**: Completar con `[project]`, `requires-python`, `dependencies`, `[build-system]`.

### ~~ARQ-09 — Feature flags huérfanos (P3)~~ ✅ RESUELTO (pre-existente)
5 feature flags en `settings.py` nunca consultados en código.

**Acción**: Auditar y eliminar flags muertos.

---

## 2. Seguridad (3/4)

### ✅ Resueltos (v3.7.0–v5.0.0)
- ~~SEC-01~~ Autenticación JWT con `POST /api/v1/auth/token` ✅ v3.8.0
- ~~SEC-02~~ Password hashing con bcrypt ✅ v3.7.0
- ~~SEC-03~~ Política contraseñas (8+ chars, mayúscula, número, símbolo) ✅ v3.7.0
- ~~SEC-04~~ CORS configurado ✅ v3.7.0
- ~~SEC-05~~ Rate limiting en API ✅ v3.7.0
- ~~SEC-06~~ Todos los routers protegidos con JWT ✅ v3.8.0
- ~~SEC-07~~ `sys.excepthook` + QMessageBox como error boundary ✅ v3.8.0
- ~~SEC-08~~ Import * eliminado (0 ocurrencias) ✅

### ~~SEC-09 — Account lockout inexistente (P1)~~ ✅ RESUELTO (pre-existente)
`LockoutManager` implementado en `src/core/security/lockout_manager.py`. Bloqueo tras 5 intentos con fichero `lockout.json` por usuario.

### ~~SEC-10 — HTML sin escapar en templates email (P2)~~ ✅ RESUELTO (pre-existente)
`html.escape()` aplicado en `src/services/email_service.py` (líneas 191, 318). `import html` presente.

### ~~SEC-11 — Path traversal en `remote_path` SFTP (P2)~~ ✅ RESUELTO (pre-existente)
`_sanitize_path()` en `SFTPSyncBackend` rechaza `..`, `~` y rutas absolutas. `_safe_path()` en `LocalSyncBackend` verifica con `Path.resolve()`.

### ~~SEC-12 — `users.json` sin permisos restrictivos (P2)~~ ✅ RESUELTO (pre-existente)
Contiene hashes bcrypt. No se aplica `chmod 600`.

**Acción**: Establecer permisos 600 al crear/modificar.

### ~~SEC-13 — Valores infraestructura en defaults (P2)~~ ✅ RESUELTO (pre-existente)
`settings.py`: `api_secret_key: str = ""` con comentario explícito "NO usar valores por defecto en producción". `database_url: str = ""` configurado dinámicamente.

### ~~SEC-14 — Username sin validación regex (P2)~~ ✅ RESUELTO (pre-existente)
`register_user()` en `sync_manager.py` valida con `re.fullmatch(r"[a-zA-Z0-9._\-]+", username)`.

### ~~SEC-15 — `data/users.json` posiblemente en git (P1)~~ ✅ RESUELTO (pre-existente)
`.gitignore` contiene `data/` (excluye todo el directorio). `git ls-files data/` no devuelve nada. Solo se mantiene `data/.gitkeep`.

### SEC-16 — 289 bloques `except Exception` (P1) — ✅ Fase 1 RESUELTA v5.6.0
Ocultan errores reales. **4 son `except Exception: pass`** (silencian completamente):
- `src/utils/ui_helpers.py`
- `src/sync/sync_manager.py`
- `src/services/importador_profesores.py`
- `src/services/calculador_guardias.py`
- `src/services/importador_zonas.py`

**Acción**: Reemplazar por excepciones específicas + `logger.exception()`.

### ~~SEC-17 — 49 `print()` en producción (P2)~~ ✅ RESUELTO (pre-existente)
Los `print()` encontrados están en docstrings/bloques `Example:` (no código ejecutable). Los únicos 3 `print()` reales (`db_manager.py`, `settings.py`) también están en secciones `Example:` de docstrings.

### ~~SEC-18 — Sin CSP ni security headers en API (P3)~~ ✅ RESUELTO v5.2.1
FastAPI ya añade security headers vía middleware en `src/api/main.py`.

---

## 3. Base de Datos (2/4)

### ✅ Resueltos
- ~~DB-01~~ Campos sustituciones ORM (`es_sustitucion`, `profesor_sustituido_id`, `notas`) ✅ v3.7.0
- ~~DB-02~~ Campo `activa` en Zona ✅ v3.8.0
- ~~DB-03~~ Campo `capacidad_profesores` en Zona ✅ v3.8.0
- ~~DB-04~~ Migración Alembic para nuevos campos ✅ v3.8.0

### ~~DB-05 — CheckConstraints ausentes (P2)~~ ✅ RESUELTO (pre-existente)
No hay constraints para: turno (M/T), tipo ausencia, recreo >= 1.

**Acción**: Añadir `CheckConstraint` en modelos ORM + migración Alembic.

### ~~DB-06 — Índices faltantes (P2)~~ ✅ RESUELTO (pre-existente)
Índices presentes en `models.py`: `ix_profesores_activo`, `ix_profesores_turno`, `ix_profesores_curso_id`, `ix_guardias_curso_id`, `ix_guardias_turno`, `ix_guardias_fecha_turno_recreo`.

### ~~DB-07 — `datetime.utcnow` deprecated (P2)~~ ✅ RESUELTO (pre-existente)
No hay ninguna ocurrencia de `datetime.utcnow()` en `src/`. Verificado con `grep -rn "utcnow" src/`.

### ~~DB-08 — Inconsistencia `cerrado` vs `archivado` (P2)~~ ✅ RESUELTO (pre-existente)
ORM define estado `cerrado`, migración crea `archivado`.

**Acción**: Unificar nomenclatura + migración.

### ~~DB-09 — Locks ausentes en `db_manager.py` (P2)~~ ✅ RESUELTO (pre-existente)
SQLite no soporta escritura concurrente. Sin locks explícitos para multi-thread.

**Acción**: Añadir `threading.Lock` en operaciones de escritura.

### DB-10 — Campos JSON violan 1NF (P3)
`dias_semana_permitidos`, `recreos_permitidos`, `recreos_config` almacenan JSON en columnas TEXT.

**Acción**: Evaluar normalización a tablas auxiliares (priorizar si migra a PostgreSQL).

### ~~DB-11 — Triple estrategia de init (P2)~~ ✅ RESUELTO v5.9.1
Alembic + `create_all` + SQL directo coexisten para inicializar BD.

**Acción**: Unificar en Alembic como única fuente de verdad.

### DB-12 — Patrón SQLite per-user (P1)
`data/users/{hash}/guardias_patio.db` — cada usuario tiene su propia BD SQLite.

**Impacto**: Bloquea migración a servidor web (no escala, no permite queries cross-user).

**Acción**: Diseñar migración a PostgreSQL multi-tenant con `tenant_id`.

### ~~DB-13 — Sin backup automático (P2)~~ ✅ RESUELTO v5.9.3
No hay mecanismo de backup/restore de la BD.

**Acción**: Implementar backup periódico + export/import.

---

## 4. Rendimiento (2/4)

### ✅ Resueltos
- ~~PERF-01~~ Benchmarks unificados en `scripts/benchmark.py` ✅ v3.8.0

### ~~PERF-02 — Sin eager loading (P2)~~ ✅ RESUELTO (pre-existente)
Queries ORM sin `joinedload`/`selectinload`. Produce N+1 queries en listados.

**Acción**: Añadir eager loading en queries de profesores, guardias, zonas.

### ~~PERF-03 — Filtro disponibilidad en Python (P2)~~ ✅ RESUELTO v5.6.0
El filtro de disponibilidad de profesores se ejecuta en Python en lugar de SQL.

**Acción**: Mover a query SQL con `WHERE` apropiado.

### ~~PERF-04 — `.count() > 0` en vez de `.exists()` (P3)~~ ✅ RESUELTO v5.4.0
Múltiples queries usan `.count()` cuando solo necesitan saber si hay resultados.

**Acción**: Reemplazar por `.exists()` o `.first() is not None`.

### ~~PERF-05 — GUI blocking en operaciones pesadas (P2)~~ ✅ RESUELTO (pre-existente)
Generación de PDFs, export Excel, y cálculo de guardias bloquean el hilo principal.

**Acción**: Mover a `QThread` o `QRunnable` con señales de progreso.

### PERF-06 — 535 llamadas a `setStyleSheet` (P3)
Inline styles en cada widget. Repinta costoso, no cacheable.

**Acción**: Migrar a QSS global cargado una vez.

---

## 5. Caché (1/4)

### ~~CACHE-01 — Sin estrategia de caché (P2)~~ ✅ RESUELTO v5.4.0
No hay caché para queries frecuentes (listado profesores, configuración curso, zonas).

**Acción**: Implementar `cachetools.TTLCache` para datos de referencia.

### ~~CACHE-02 — Configuración releída en cada operación (P2)~~ ✅ RESUELTO v5.4.0
`obtener_configuracion` ejecuta query en cada llamada.

**Acción**: Cachear con TTL de 60s, invalidar en escritura.

### ~~CACHE-03 — Sin caché de assets UI (P3)~~ ✅ RESUELTO v5.2.1
Los pixmaps del logo corporativo ya se sirven con `QPixmapCache` desde `src/utils/ui_helpers.py`.

---

## 6. Async/Concurrencia (1/4)

### ASYNC-01 — FastAPI síncrono (P2)
Todos los endpoints usan `def` síncrono con SQLAlchemy síncrono. En producción multi-usuario bloqueará el event loop.

**Acción**: Si se migra a PostgreSQL, usar `async def` + `asyncpg` + `run_in_threadpool`.

### ~~ASYNC-02 — SFTP síncrono sin timeout robusto (P2)~~ ✅ RESUELTO v5.2.1
La conexión SFTP ya aplica timeouts explícitos y `keepalive` en `src/sync/sync_manager.py`.

---

## 7. Escalabilidad y Resiliencia (1/4)

### ~~RES-01 — Sin retry en SFTP (P2)~~ ✅ RESUELTO v5.2.1
Fallo de red = fallo total. Sin reintentos.

**Acción**: `tenacity.retry` con backoff exponencial (max 3 reintentos).

### ~~RES-02 — Sin circuit breaker (P3)~~ ✅ RESUELTO v5.2.1
La conexión SFTP ya está protegida con `pybreaker` en `src/sync/sync_manager.py`.

### ~~RES-03 — Sin retry BD configurado (P2)~~ ✅ RESUELTO v5.9.5
`settings.py` tiene config de retry pero no se usa.

**Acción**: Implementar el retry que ya está configurado.

### ~~RES-04 — Sin health check de dependencias (P3)~~ ✅ RESUELTO (pre-existente)
El endpoint `/health` no verifica BD, disco, SFTP.

**Acción**: Añadir checks de dependencias al health endpoint.

### ~~RES-05 — Sin graceful shutdown (P3)~~ ✅ RESUELTO v5.1.0
La app no gestiona `SIGTERM`/`SIGINT` para cerrar conexiones BD y SFTP limpiamente.

**Acción**: Implementar signal handlers.

---

## 8. API REST (2/4)

### ✅ Resueltos
- ~~API-01~~ Autenticación JWT ✅ v3.8.0
- ~~API-02~~ Health check dinámico ✅ v3.8.0
- ~~API-03~~ Export CSV/Excel ✅ v3.9.0
- ~~API-04~~ Import profesores CSV ✅ v3.9.0
- ~~API-05~~ CORS ✅ v3.7.0
- ~~API-06~~ Rate limiting ✅ v3.7.0
- ~~API-07~~ Routers migrados a use cases ✅ v3.8.0

### ~~API-08 — Solo endpoints GET (salvo auth) (P1)~~ ✅ RESUELTO v5.8.0
No hay `POST`, `PUT`, `DELETE` para CRUD completo. La API no es funcional para un frontend web.

**Acción**: Implementar CRUD completo para profesores, guardias, zonas, cursos, ausencias.

### ~~API-09 — Sin paginación (P1)~~ ✅ RESUELTO v5.5.0
`GET /api/v1/profesores` devuelve todos los registros sin límite.

**Acción**: Implementar `?page=1&size=20` con `Link` headers.

### ~~API-10 — Versionado parcial (P2)~~ ✅ RESUELTO v5.2.1
La API ya expone el header `API-Version: 1` además del prefijo `/api/v1`.

### ~~API-11 — Sin schema de error estándar (P2)~~ ✅ RESUELTO v5.9.6
Errores devuelven formatos inconsistentes.

**Acción**: Implementar `{"error": {"code": "RESOURCE_NOT_FOUND", "message": "...", "details": {}}}`.

### ~~API-12 — 3 `response_model` en toda la API (P2)~~ ✅ RESUELTO v5.2.1
Los endpoints clave de cuotas, equidad, guardias count y estadísticas ya exponen `response_model` Pydantic.

### ~~API-13 — Sin OpenAPI enrichment (P3)~~ ✅ RESUELTO v5.4.0
Schemas sin descripciones, ejemplos, ni tags organizados.

**Acción**: Añadir metadata OpenAPI (descriptions, examples, tags).

### API-14 — Sin WebSocket para real-time (P3)
Generación de guardias es proceso largo sin feedback.

**Acción**: Evaluar WebSocket para progreso de generación.

### ~~API-15 — Sin middleware de logging estructurado (P2)~~ ✅ RESUELTO v5.2.1
Las requests ya se registran con `request_id`, duración, método, path y `status_code` desde middleware en `src/api/main.py`.

---

## 9. Testing (2/4)

### Métricas actuales
- **Tests**: 1.342 passing, 5 skipped
- **Coverage**: 47,81%
- **Archivos test**: 63

### ✅ Resueltos
- ~~TEST-01~~ Tests API REST (21 tests) ✅ v3.8.0
- ~~TEST-02~~ 120 tests nuevos v5.0.0 ✅ v5.0.0

### TEST-03 — Coverage insuficiente (P1)
47,81% está por debajo del mínimo recomendado (70%).

**Distribución estimada**:
- `domain/` ~65% (mejor cubierto)
- `application/` ~55%
- `services/` ~40%
- `presentation/` ~25%
- `api/` ~50%
- `sync/` ~10%
- `infrastructure/` ~45%

**Acción**: Target 70% global. Priorizar `services/` y `domain/`.

### ~~TEST-04 — 0 tests SFTP/SMTP (P2)~~ ✅ RESUELTO (pre-existente)
`src/sync/` sin cobertura. Operaciones de red sin mock.

**Acción**: Tests con Paramiko mockeado + smtplib mockeado.

### ~~TEST-05 — Sin tests de integración BD (P2)~~ ✅ RESUELTO (pre-existente)
Tests unitarios mockean repositorios pero no verifican queries reales.

**Acción**: Tests de integración con SQLite in-memory.

### ~~TEST-06 — Sin mutation testing (P3)~~ ✅ RESUELTO v5.9.7
No se verifica calidad de los tests existentes.

**Acción**: Evaluar `mutmut` para mutation testing.

### TEST-07 — Sin tests de regresión UI (P3)
No hay snapshot tests ni tests de regresión visual.

**Acción**: Evaluar `pytest-qt` snapshots o visual regression testing.

---

## 10. Observabilidad (2/4)

### ✅ Resueltos
- ~~OBS-01~~ Logger centralizado en `core/logging.py` ✅

### ~~OBS-02 — 49 `print()` en producción (P2)~~ ✅ RESUELTO (pre-existente)
Debug prints que deberían ser `logger.debug()`.

**Acción**: Reemplazar todos por logger apropiado.

### ~~OBS-03 — Sin métricas de negocio (P3)~~ ✅ RESUELTO v5.9.8
No se trackean: guardias generadas/día, tiempo de generación, errores por tipo.

**Acción**: Instrumentar con contadores en logger estructurado.

### ~~OBS-04 — Sin request tracing en API (P2)~~ ✅ RESUELTO v5.2.1
No hay correlation ID entre requests.

**Acción**: Middleware con `X-Request-ID` propagado a logs.

### ~~OBS-05 — Logs sin rotación configurada (P3)~~ ✅ RESUELTO (pre-existente)
Logs crecen indefinidamente.

**Acción**: Configurar `RotatingFileHandler` (10MB, 5 backups).

### OBS-06 — Sin alertas de error (P3)
Errores críticos no generan notificación.

**Acción**: Evaluar integración con servicio de alertas para producción web.

---

## 11. UX/UI y Accesibilidad (1/4) 🔴

> **Esta es el área más débil del proyecto.** Con 59 archivos de presentación, la accesibilidad es prácticamente inexistente.

### Métricas de accesibilidad

| Métrica | Valor | Esperado | Estado |
|---|---|---|---|
| `setAccessibleName` | 6 | ~200+ | 🔴 3% cobertura |
| `setAccessibleDescription` | 0 | ~100+ | 🔴 0% |
| `setTabOrder` | 9 | ~50+ | 🔴 Solo en login |
| `QValidator` | 2 | ~30+ | 🔴 Solo en login |
| `setToolTip` | 49 | ~100+ | ⚠️ 50% |
| `QShortcut/setShortcut` | 14 | ~30+ | ⚠️ |
| `setFocusPolicy` | 1 | ~20+ | 🔴 |
| `setStatusTip` | 0 | ~20+ | 🔴 |
| `setWhatsThis` | 0 | ~10+ | 🔴 |
| `setPlaceholderText` | 69 | ~80+ | ✅ Aceptable |

### ~~A11Y-01 — Accessible names casi inexistentes (P1)~~ ✅ RESUELTO v5.14.0
54 `setAccessibleName` añadidos en 8 formularios: `datos_basicos_widget`, `datos_zona_widget`, `sftp_widget`, `smtp_widget`, `ajustes_widget`, `fechas_recreos_widget`, `perfiles_usuario_form`, `_initial_config_tabs`.

### ~~A11Y-02 — Tab order no definido (P1)~~ ✅ RESUELTO v5.14.0
`setTabOrder` definido en 6 widgets: `datos_basicos_widget`, `datos_zona_widget`, `sftp_widget`, `smtp_widget`, `fechas_recreos_widget`, `perfiles_usuario_form`.

### ~~A11Y-03 — Sin validación de formularios (P1)~~ ✅ RESUELTO v5.3.0
Solo 2 `QValidator` (en login). Los 36 formularios restantes aceptan cualquier input.

**Impacto**: Datos inválidos llegan a la BD. UX pobre (errores post-submit en vez de inline).

**Acción**: Añadir `QValidator` o validación inline a todos los campos:
- Números: `QIntValidator`, `QDoubleValidator`
- Texto: `QRegularExpressionValidator`
- Emails, teléfonos: validators custom
- Feedback visual: borde rojo + mensaje de error junto al campo

### ~~A11Y-04 — Contraste de colores sin verificar (P2)~~ ✅ RESUELTO v5.11.0
~~415 colores hardcodeados sin verificar ratio WCAG 2.1 (mínimo 4.5:1 para texto, 3:1 para UI).~~

~~**Acción**: Auditar colores con herramienta de contraste. Centralizar en paleta verificada.~~

**Resultado**: Colores semánticos en `tokens.py` actualizados: `SUCCESS #1E7E34` (5.14:1 ✅), `WARNING #856404` (5.49:1 ✅), `INFO #0C6674` (6.63:1 ✅).

### ~~A11Y-05 — Sin soporte de teclado completo (P2)~~ ✅ RESUELTO v5.3.0
14 shortcuts definidos. Muchas acciones solo accesibles con ratón.

**Acción**: Mapear todos los flujos principales a atajos de teclado.

### ~~A11Y-06 — Sin feedback de estado para screen readers (P2)~~ ✅ RESUELTO v5.11.0
~~Operaciones largas (generación guardias, export PDF) no anuncian progreso a tecnología asistiva.~~

**Resultado**: `announce()` añadido a `utils/ui_helpers.py` con `try/except` defensivo (la build de PyQt6 no expone `QAccessible` pero no rompe nada).

### ~~A11Y-07 — Tamaños de fuente fijos (P2)~~ ✅ RESUELTO v5.11.0
~~269 fuentes hardcodeadas. No respetan preferencias del sistema.~~

**Resultado**: Verificado — todos los tamaños de fuente en `presentation/` ya usan `FontSize` de `tokens.py`. No hay fuentes hardcodeadas pendientes.

### A11Y-08 — Sin soporte de alto contraste (P3)
No hay tema de alto contraste. Usuarios con baja visión no tienen opción.

**Acción**: Implementar tema de alto contraste como alternativa.

### A11Y-09 — Sin internacionalización (P3)
Solo 2 usos de `tr()`. Toda la UI está hardcodeada en español.

**Acción**: Wrappear strings con `self.tr()` para futura traducción.

### ~~A11Y-10 — Sin DPI awareness (P2)~~ ✅ RESUELTO (pre-existente)
191 tamaños fijos (`setMinimum`, `setFixed`, `setGeometry`). En pantallas HiDPI se ven diminutos.

**Acción**: Usar layouts con `sizePolicy` en vez de tamaños fijos. Activar `Qt.AA_EnableHighDpiScaling`.

---

## 12. Diseño Visual y Consistencia (2/4)

### Métricas visuales

| Métrica | Valor | Problema |
|---|---|---|
| `setStyleSheet` | 535 | Estilos inline dispersos |
| Colores hardcodeados | 415 | Sin paleta centralizada |
| Fuentes hardcodeadas | 269 | Sin escala tipográfica |
| Imports de `ui_styles` | 40 | Dependencia legacy monolítica |
| Tamaños fijos | 191 | Sin responsive design |

### ~~VIS-01 — Sin sistema de design tokens (P1)~~ ✅ RESUELTO v5.5.0
415 colores definidos inline sin paleta centralizada. Cambiar el color primario requiere editar decenas de archivos.

**Acción**: Crear sistema de design tokens:
```python
# src/presentation/theme/tokens.py
class ColorTokens:
    PRIMARY = "#1976D2"
    PRIMARY_DARK = "#1565C0"
    SURFACE = "#FFFFFF"
    ERROR = "#D32F2F"
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
```

### VIS-02 — 535 `setStyleSheet` inline (P1)
Estilos duplicados y dispersos. Imposible mantener consistencia visual.

**Acción**: Migrar a QSS global:
1. Crear `src/presentation/theme/light.qss` y `dark.qss`
2. Cargar una vez en `QApplication.setStyleSheet()`
3. Eliminar `setStyleSheet` inline progresivamente

### ~~VIS-03 — `ui_styles.py` legacy (P2)~~ ✅ RESUELTO v5.5.0
Módulo monolítico con 40 importadores. Mezcla estilos, constantes y lógica.

**Acción**: Migrar a sistema de temas (VIS-01/VIS-02) y deprecar.

### ~~VIS-04 — Sin iconografía consistente (P2)~~ ✅ RESUELTO v5.11.0
~~Iconos de diferentes fuentes y estilos mezclados.~~

**Resultado**: `get_icon(name, fallback)` centralizado en `utils/ui_helpers.py`. Busca en `imagenes/icons/<name>.svg|.png` con `QPixmapCache`.

### ~~VIS-05 — Sin escala tipográfica (P2)~~ ✅ RESUELTO v5.5.0
269 fuentes hardcodeadas con tamaños arbitrarios.

**Acción**: Definir escala tipográfica (H1: 24px, H2: 20px, Body: 14px, Caption: 12px).

### ~~VIS-06 — Sin espaciado consistente (P2)~~ ✅ RESUELTO v5.5.0
Márgenes y paddings arbitrarios en cada widget.

**Acción**: Definir escala de espaciado (4, 8, 12, 16, 24, 32, 48px).

### VIS-07 — Sin tema oscuro (P3)
Solo tema claro disponible.

**Acción**: Implementar tema oscuro con los design tokens.

### VIS-08 — Sin animaciones/transiciones (P3)
Cambios de estado son abruptos (aparece/desaparece).

**Acción**: Añadir `QPropertyAnimation` para transiciones suaves en operaciones clave.

### ~~VIS-09 — Sin responsive layout (P2)~~ ✅ RESUELTO v5.11.0
~~191 tamaños fijos. La app no se adapta a diferentes resoluciones.~~

**Resultado**: Eliminadas 24 llamadas `setFixedSize()` de `QMessageBox` en diálogos y widgets. Logo sidebar cambiado a `setMinimumSize/setMaximumSize`.

### VIS-10 — Sin guía de estilo documentada (P3)
No hay documento de referencia para nuevos desarrolladores.

**Acción**: Crear `docs/DESIGN_SYSTEM.md` con paleta, tipografía, espaciado, componentes.

---

## 13. Casos de Uso y Flujos de Usuario (3/4)

### Flujos principales implementados

| Caso de Uso | Estado | Completitud |
|---|---|---|
| UC-01 Login/Logout | ✅ Completo | JWT + bcrypt + política contraseñas |
| UC-02 Gestión de cursos | ✅ Completo | CRUD + estados (activo/cerrado) |
| UC-03 Gestión de profesores | ✅ Completo | CRUD + import CSV/Excel |
| UC-04 Gestión de zonas | ✅ Completo | CRUD + capacidad + activa |
| UC-05 Configuración recreos | ✅ Completo | Por turno M/T |
| UC-06 Gestión de ausencias | ✅ Completo | CRUD + tipos |
| UC-07 Generación de guardias | ✅ Completo | OR-Tools CP-SAT |
| UC-08 Visualización calendario | ✅ Completo | Vista mes + filtros |
| UC-09 Export PDF/CSV/Excel | ✅ Completo | Múltiples formatos |
| UC-10 Estadísticas | ✅ Completo | Panel + gráficos |

### Flujos secundarios

| Caso de Uso | Estado | Notas |
|---|---|---|
| UC-11 Sustituciones | ⚠️ Parcial | Campos ORM existen, UI incompleta |
| UC-12 Sincronización SFTP | ✅ Funcional | Sin retry ni circuit breaker |
| UC-13 Backup/Restore | ❌ No implementado | Solo export manual |
| UC-14 Import config entre cursos | ❌ No implementado | Solicitado por usuarios |
| UC-15 Import zonas CSV | ❌ No implementado | Solo manual |

### ~~UXF-01 — Sustituciones incompletas (P2)~~ ✅ RESUELTO v5.7.0
Los campos ORM (`es_sustitucion`, `profesor_sustituido_id`, `notas`) existen pero la UI para gestionarlas está incompleta.

**Acción**: Completar UI de sustituciones con selector de profesor sustituido y notas.

### ~~UXF-02 — Sin confirmación en acciones destructivas (P2)~~ ✅ RESUELTO v5.0.x
Algunas acciones de borrado no piden confirmación.

**Acción**: Añadir `QMessageBox.question()` antes de todo delete.

### UXF-03 — Sin undo/redo (P3)
No hay mecanismo para deshacer acciones.

**Acción**: Evaluar `QUndoStack` para operaciones CRUD principales.

### UXF-04 — Sin onboarding/wizard inicial (P3)
Usuario nuevo ve interfaz vacía sin guía.

**Acción**: Implementar wizard de primer uso (crear curso → añadir zonas → importar profesores → configurar recreos).

### ~~UXF-05 — Sin indicador de cambios sin guardar (P2)~~ ✅ RESUELTO v5.3.0
El usuario no sabe si hay cambios pendientes de guardar.

**Acción**: Indicador visual (asterisco en título, botón guardar resaltado).

---

## 14. Control de Acceso (3/4)

### ✅ Resueltos
- ~~MT-01~~ Autenticación JWT en API ✅ v3.8.0
- ~~MT-02~~ Login GUI con bcrypt ✅ v3.7.0
- ~~MT-03~~ Política de contraseñas ✅ v3.7.0

### MT-04 — Sin roles/permisos (P3)
Todos los usuarios autenticados tienen acceso completo.

**Acción**: Implementar RBAC (admin, editor, viewer) cuando sea necesario.

---

## 15. Organización de Código (2/4)

### ~~ORG-01 — Archivos mal ubicados (P2)~~ ✅ RESUELTO v5.11.0
~~Archivos en ubicaciones que no corresponden a su responsabilidad.~~

**Resultado**: `cache_service.py` movido a `application/use_cases/configuracion/`. El original en `services/` es ahora un shim de compatibilidad que re-exporta todo.

### ORG-02 — Duplicación de estilos (P2)
`ui_styles.py` + 535 `setStyleSheet` inline = estilos duplicados y contradictorios.

**Acción**: Unificar en sistema de temas (ver VIS-01/VIS-02).

### ORG-03 — 29 archivos >500 líneas (P3)
Archivos grandes dificultan navegación y mantenimiento.

**Acción**: Split progresivo de los 8 archivos >800L (ver ARQ-05).

---

## 16. Sanitización de Código (2/4)

### ~~SAN-01 — 289 `except Exception` (P1)~~ ✅ RESUELTO (pre-existente)
La mayoría capturan excepciones genéricas sin discriminar tipo.

**Distribución**:
- `services/`: ~120 bloques
- `presentation/`: ~80 bloques
- `sync/`: ~30 bloques
- `infrastructure/`: ~25 bloques
- Otros: ~34 bloques

**4 bloques `except Exception: pass`** (los peores):
1. `src/utils/ui_helpers.py`
2. `src/sync/sync_manager.py`
3. `src/services/importador_profesores.py`
4. `src/services/calculador_guardias.py`
5. `src/services/importador_zonas.py`

**Acción**: Fase 1: Eliminar los 4-5 `pass` silenciosos. Fase 2: Migrar a excepciones específicas.

### ~~SAN-02 — 49 `print()` en producción (P2)~~ ✅ RESUELTO (pre-existente)
Ya documentado en SEC-17 y OBS-02.

### ~~SAN-03 — 1 `TODO` pendiente (P3)~~ ✅ RESUELTO v5.5.0
Solo 1 TODO en el código. Revisarlo y resolver o eliminar.

---

## 17. Preparación para Migración Web (Puntuación: 5/10)

### Estado actual de preparación

| Aspecto | Listo | Bloqueado | Nota |
|---|---|---|---|
| API REST existe | ✅ | — | FastAPI funcional |
| Autenticación JWT | ✅ | — | Completa |
| CORS configurado | ✅ | — | — |
| Rate limiting | ✅ | — | — |
| CRUD completo API | — | 🔴 | Solo GET (salvo auth) |
| Paginación | — | 🔴 | No implementada |
| Error schema estándar | — | 🔴 | Inconsistente |
| BD multi-tenant | — | 🔴 | SQLite per-user |
| Async endpoints | — | ⚠️ | Síncrono, funcional para MVP |
| WebSocket | — | ⚠️ | No necesario para MVP |
| Frontend desacoplado | — | 🔴 | UI = PyQt6 monolítica |
| Domain logic puro | — | ⚠️ | 28 servicios acoplados a ORM |

### Ruta de migración recomendada

```
Fase 1 — API Completa (P1)
├── CRUD completo (POST/PUT/DELETE) para todas las entidades
├── Paginación en listados
├── Schema de error estándar
└── response_model en todos los endpoints

Fase 2 — Desacoplamiento (P1-P2)
├── Migrar servicios a repositorios inyectados
├── Eliminar queries directas de presentation/
└── Domain services puros (sin imports de infra)

Fase 3 — Base de Datos (P1)
├── Migrar de SQLite per-user a PostgreSQL
├── Implementar multi-tenancy (tenant_id)
└── Async con asyncpg

Fase 4 — Frontend Web (P2)
├── SPA con React/Vue consumiendo la API
├── WebSocket para operaciones largas
└── Auth flow con refresh tokens
```

---

## 18. Reparabilidad y Diagnóstico

### Fortalezas
- Error boundary GUI captura excepciones no manejadas
- Logger centralizado en `core/logging.py`
- Benchmarks disponibles para perfilado
- 1.342 tests como red de seguridad

### Debilidades
- 289 `except Exception` ocultan errores reales
- 49 `print()` sin nivel de severidad
- Sin correlation ID en requests API
- Sin métricas de negocio
- Logs sin rotación

---

## 19. Roadmap Priorizado

### P1 — Resolver antes de v6.0.0 (18 ítems)

| # | ID | Descripción | Esfuerzo |
|---|---|---|---|
| 1 | A11Y-01 | Accessible names en todos los widgets | L |
| 2 | A11Y-02 | Tab order en formularios y diálogos | M |
| 3 | A11Y-03 | ~~QValidator en formularios~~ ✅ RESUELTO v5.3.0 | L |
| 4 | VIS-01 | ~~Sistema de design tokens ~~ ✅ RESUELTO v5.1.0| M |
| 5 | VIS-02 | ~~QSS global (eliminar setStyleSheet inline) ~~ ✅ RESUELTO v5.1.0| XL |
| 6 | ARQ-01 | Migrar servicios core a repositorios | XL |
| 7 | ARQ-03 | Descontaminar domain services | M |
| 8 | API-08 | ~~CRUD completo en API REST~~ ✅ RESUELTO v5.8.0 | XL |
| 9 | API-09 | ~~Paginación en listados~~ ✅ RESUELTO v5.5.0 | M |
| 10 | SEC-09 | ~~Account lockout~~ ✅ RESUELTO (pre-existente) | S |
| 11 | SEC-15 | ~~Verificar/limpiar users.json de git~~ ✅ RESUELTO (pre-existente) | S |
| 12 | SEC-16 | ~~Resolver except Exception: pass (5 peores)~~ ✅ RESUELTO v5.1.1 | S |
| 13 | DB-12 | Diseñar migración SQLite → PostgreSQL | L |
| 14 | TEST-03 | Coverage al 70% | XL |
| 15 | SAN-01 | ~~Except Exception → excepciones específicas (fase 1)~~ ✅ RESUELTO (pre-existente) | M |
| 16 | DB-11 | ~~Unificar init BD en Alembic~~ ✅ RESUELTO v5.9.1 | M |
| 17 | A11Y-10 | ~~DPI awareness~~ ✅ RESUELTO (pre-existente) | M |
| 18 | ARQ-08 | ~~Completar pyproject.toml ~~ ✅ RESUELTO v5.1.0| S |

### P2 — Resolver antes de v7.0.0 (34 ítems)

| # | ID | Descripción | Esfuerzo |
|---|---|---|---|
| 1 | ARQ-02 | ~~Eliminar queries de presentation/ (Fase 1)~~ ✅ Fase 1 RESUELTA v5.6.0 | M |
| 2 | ARQ-04 | Framework DI | L |
| 3 | ARQ-05 | Split archivos >800L | L |
| 4 | ARQ-06 | ~~Migrar ui_styles.py legacy~~ ✅ RESUELTO v5.5.0 | M |
| 5 | SEC-10 | ~~Escapar HTML en emails~~ ✅ RESUELTO (pre-existente) | S |
| 6 | SEC-11 | ~~Validar remote_path SFTP~~ ✅ RESUELTO (pre-existente) | S |
| 7 | SEC-12 | ~~chmod 600 en users.json~~ ✅ RESUELTO (pre-existente) | S |
| 8 | SEC-13 | ~~Eliminar defaults de infra en config~~ ✅ RESUELTO (pre-existente) | S |
| 9 | SEC-14 | ~~Validar username con regex~~ ✅ RESUELTO (pre-existente) | S |
| 10 | SEC-17 | ~~Reemplazar print() por logger ~~ ✅ RESUELTO v5.1.0| M |
| 11 | DB-05 | ~~CheckConstraints~~ ✅ RESUELTO v5.2.0 | S |
| 12 | DB-06 | ~~Índices faltantes~~ ✅ RESUELTO (pre-existente) | S |
| 13 | DB-07 | ~~datetime.utcnow deprecated~~ ✅ RESUELTO (pre-existente) | S |
| 14 | DB-08 | ~~Inconsistencia cerrado/archivado~~ ✅ RESUELTO (pre-existente) | S |
| 15 | DB-09 | ~~Locks en db_manager~~ ✅ RESUELTO v5.1.2 | S |
| 16 | DB-11 | ~~Triple init BD~~ ✅ RESUELTO v5.9.1 | M |
| 17 | DB-13 | ~~Backup/restore automático~~ ✅ RESUELTO v5.9.3 | L |
| 18 | PERF-02 | ~~Eager loading~~ ✅ RESUELTO v5.2.0 | M |
| 19 | PERF-03 | ~~Filtro disponibilidad a SQL~~ ✅ RESUELTO v5.6.0 | M |
| 20 | PERF-05 | ~~GUI no-blocking (QThread)~~ ✅ RESUELTO (pre-existente) | L |
| 21 | CACHE-01 | ~~Caché de queries frecuentes~~ ✅ RESUELTO v5.4.0 | M |
| 22 | CACHE-02 | ~~Caché de configuración~~ ✅ RESUELTO v5.4.0 | S |
| 23 | ASYNC-01 | FastAPI async (con PostgreSQL) | XL |
| 24 | ASYNC-02 | ~~SFTP con timeout + retry~~ ✅ RESUELTO v5.2.1 | M |
| 25 | RES-01 | ~~Retry SFTP con tenacity~~ ✅ RESUELTO v5.2.1 | M |
| 26 | RES-03 | ~~Implementar retry BD~~ ✅ RESUELTO v5.9.5 | S |
| 27 | API-10 | ~~Versionado API~~ ✅ RESUELTO v5.2.1 | S |
| 28 | API-11 | ~~Schema error estándar~~ ✅ RESUELTO v5.9.6 | M |
| 29 | API-12 | ~~response_model en endpoints~~ ✅ RESUELTO v5.2.1 | M |
| 30 | API-15 | ~~Middleware logging estructurado~~ ✅ RESUELTO v5.2.1 | M |
| 31 | TEST-04 | ~~Tests SFTP/SMTP~~ ✅ RESUELTO (pre-existente) | L |
| 32 | TEST-05 | ~~Tests integración BD~~ ✅ RESUELTO (pre-existente) | L |
| 33 | OBS-04 | ~~Request tracing~~ ✅ RESUELTO v5.2.1 | M |
| 34 | A11Y-04 | Auditar contraste colores | M |

### P3 — Mejoras incrementales (22 ítems)

| # | ID | Descripción | Esfuerzo |
|---|---|---|---|
| 1 | A11Y-05 | ~~Soporte teclado completo~~ ✅ RESUELTO v5.3.0 | M |
| 2 | A11Y-06 | Feedback screen readers | M |
| 3 | A11Y-07 | Tamaños fuente relativos | M |
| 4 | A11Y-08 | Tema alto contraste | L |
| 5 | A11Y-09 | Internacionalización (tr()) | XL |
| 6 | VIS-04 | Iconografía consistente | M |
| 7 | VIS-05 | ~~Escala tipográfica~~ ✅ RESUELTO v5.5.0 | S |
| 8 | VIS-06 | ~~Escala de espaciado~~ ✅ RESUELTO v5.5.0 | S |
| 9 | VIS-07 | Tema oscuro | L |
| 10 | VIS-08 | Animaciones/transiciones | M |
| 11 | VIS-09 | Responsive layout | L |
| 12 | VIS-10 | Guía de estilo documentada | M |
| 13 | ARQ-07 | Capa anticorrupción sync | M |
| 14 | ARQ-09 | ~~Feature flags huérfanos ~~ ✅ RESUELTO v5.1.0| S |
| 15 | DB-10 | Normalizar campos JSON | L |
| 16 | PERF-04 | ~~.exists() en vez de .count()~~ ✅ RESUELTO v5.4.0 | S |
| 17 | PERF-06 | Reducir setStyleSheet inline | L |
| 18 | CACHE-03 | ~~QPixmapCache para assets~~ ✅ RESUELTO v5.2.1 | S |
| 19 | RES-02 | ~~Circuit breaker~~ ✅ RESUELTO v5.2.1 | M |
| 20 | RES-04 | ~~Health check dependencias~~ ✅ RESUELTO (pre-existente) | S |
| 21 | RES-05 | ~~Graceful shutdown ~~ ✅ RESUELTO v5.1.0| S |
| 22 | UXF-03 | Undo/redo con QUndoStack | L |

### Escala de esfuerzo
- **S** (Small): < 2 horas
- **M** (Medium): 2–6 horas
- **L** (Large): 6–16 horas
- **XL** (Extra Large): 16+ horas

---

## Apéndice A — Resumen de ítems resueltos (73)

Incluye todos los ítems marcados con ✅ a lo largo del documento, resueltos entre v3.7.0 y v5.0.0.

## Apéndice B — Herramientas de auditoría utilizadas

- `grep_search` — búsqueda exacta de patrones en codebase
- `semantic_search` — búsqueda semántica de conceptos
- `run_in_terminal` — `wc -l`, `grep -r`, `find`, conteo de métricas
- Skills: `audit`, `code-review-excellence`, `architecture-patterns`, `api-design-principles`
- Revisión manual de archivos clave

---

*Última actualización: 19 de abril de 2026 — Auditoría completa v5.0.0*
# Auditoría Integral — Guardias de Patio

**Fecha**: 16 de abril de 2026  
**Versión analizada**: 3.2.1 (actualizado con correcciones v3.1.0)  
**Alcance**: Análisis completo de arquitectura, seguridad, base de datos, performance, UX/UI, testing, observabilidad, escalabilidad, resiliencia y buenas prácticas.

## ⚡ ESTADO ACTUAL (v5.0.0)

**Completados**: 63/103 items (61.2%)
**En Progreso**: 1 (TEST-01 cobertura parcial)
**Pendientes**: 39/103 items (37.8%)

### Releases Ejecutados
- ✅ **v3.7.0** — Políticas seguridad, campos sustituciones ORM, API use cases, 21 tests REST/SMTP/SFTP
- ✅ **v3.8.0** — JWT auth API, campos Zona (activa+capacidad), error boundary, health dinámico
- ✅ **v3.9.0** — Export guardias CSV/Excel, import profesores CSV
- ✅ **v4.0.0** — Lockout progresivo, path traversal SFTP, chmod 600 users.json, api_secret_key sin default
- ✅ **v4.1.0** — 14 índices BD, 7 CheckConstraints, optimización .first() is not None
- ✅ **v4.2.0** — Backup/restore BD por usuario, import zonas CSV/Excel, 23 tests nuevos
- ✅ **v4.3.0** — Paginación API profesores, schema error estándar, 5 tests nuevos
- ✅ **v4.4.0** — `Profesor.curso_id` FK + relación ORM + migración + 10 tests
- ✅ **v4.5.0** — Split `asignador_guardias_v4_hibrido.py` en 3 módulos (276+387+341L)
- ✅ **v4.6.0** — `cache_service.py` TTLCache + tenacity retry SFTP + 14 tests
- ✅ **v4.7.0** — joinedload ProfesorRepository, validación username vacío, BD retry con backoff, correlation IDs FastAPI, fix `_ensure_connected`
- ✅ **v4.8.0** — 39 tests nuevos (perfiles, iCalendar, cuotas), cobertura 16.4% → 41.5%, 1080 tests totales
- ✅ **v4.9.0** — 63 tests nuevos (estadísticas, validador, importadores, data exporter), cobertura 41.5% → 43.55%, 1143 tests totales
- ✅ **v4.10.0** — 47 tests nuevos (sync/auth/lock/factory), cobertura 43.55% → 44.96%, 1190 tests totales
- ✅ **v4.11.0** — 32 tests nuevos (data exporter + orquestador + estadísticas), cobertura 44.96% → 46.02%, 1222 tests totales
- ✅ **v5.0.0** — 120 tests nuevos (api/auth, routers REST, cache, factories, ausencia_checker, migrar_multi_curso), cobertura 46.02% → 47.81%, 1342 tests totales
### Próximas Fases Recomendadas
1. **v4.6.0 (Resilencia)** — tenacity retry SFTP, circuit breaker, cachetools

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
| Seguridad | ✅ Críticos resueltos (bcrypt, Fernet, CORS), falta JWT | ★★★☆☆ |
| Base de datos | Funcional pero con violaciones de normalización | ★★★☆☆ |
| Performance | ✅ N+1 crítico resuelto, aceptable para la escala | ★★★☆☆ |
| Caching | ✅ Bug crítico corregido, falta thread-safety | ★★★☆☆ |
| Async | GUI bien resuelto, SFTP bloqueante | ★★★☆☆ |
| Escalabilidad | Diseñada para uso local, no escala horizontalmente | ★★☆☆☆ |
| API REST | Solo lectura, sin auth, con fugas de info | ★★☆☆☆ |
| Testing | ~~990 tests, 39.75% coverage~~ 1222 tests, 46.02% coverage | ★★★☆☆ |
| Observabilidad | Prometheus + structlog bien diseñados | ★★★★☆ |
| UX/UI | Funcional, sin accesibilidad formal | ★★★☆☆ |
| Control de acceso | ✅ bcrypt + Fernet, sin autorización granular | ★★★☆☆ |
| Multi-tenancy | Aislamiento por BD SQLite — correcto | ★★★★☆ |
| Idempotencia | Parcial en migraciones y repositorios | ★★★☆☆ |
| Organización de archivos | Archivos mal ubicados, duplicaciones, ficheros gigantes | ★★☆☆☆ |
| Features completas | Varias funcionalidades a medio implementar | ★★★☆☆ |
| Código huérfano | ✅ 16 ficheros eliminados en v3.1.0 | ★★★★☆ |
| Sanitización | ✅ pickle/base64 resueltos, quedan print() y except:pass | ★★★☆☆ |
| Preparación web | FastAPI existe pero cubre ~15%; servicios portables | ★★★☆☆ |
| Reparabilidad | ✅ Logging unificado, sin error boundaries, diagnóstico parcial | ★★★☆☆ |

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
| ARQ-01 | ~~Servicios bypasean repositorios~~ | ✅ RESUELTO v3.4.0 | 4 domain services movidos de `domain/services/` a `services/`; imports actualizados en use cases y assignment executor |
| ARQ-02 | ~~Presentación accede a BD directamente~~ | ✅ RESUELTO v3.6.0 | Facade `AppServices`; 21 widgets migrados (Fase 2: 9 sencillos v3.5.0; Fase 3: 12 complejos v3.6.0). Excepciones justificadas: `profesor_form` L629/L696 (JSON raw ORM), `generacion_panel` L217 (escritura ORM) |
| ARQ-03 | ~~3 repositorios retornan modelos ORM~~ | ✅ RESUELTO v3.4.0 | `AusenciaRepository`, `ConfiguracionRepository` y `CursoEscolarRepository` retornan entidades de dominio vía mappers |
| ARQ-04 | **DI manual sin framework** | MEDIA | Factories manuales en `application/factories.py`. Funcional pero propenso a errores al crecer |
| ARQ-05 | ~~Dos ventanas principales coexisten~~ | ✅ RESUELTO v3.1.0 | `main_window.py` eliminado, solo queda `ccleaner_main_window.py` |
| ARQ-06 | ~~Capa `models/` es re-export legacy~~ | ✅ RESUELTO v3.1.0 | `models/models.py` eliminado |

### 2.3 Recomendaciones

- [x] Migrar los 20+ servicios legacy para que usen repositorios de dominio en vez de `session.query()` ✅ v3.4.0 (parcial: 4 domain services; 20+ en `services/` pendientes ARQ-02)
- [x] Crear entidades de dominio para Ausencia, Configuracion y CursoEscolar con sus mappers ✅ v3.4.0
- [x] ~~Eliminar acceso directo a BD desde la capa de presentación → inyectar use cases~~ ✅ v3.6.0 — ARQ-02 completo: 21 widgets migrados vía facade `AppServices`
- [x] ~~Eliminar `main_window.py` legacy cuando la nueva UI esté completa~~ ✅ v3.1.0 (ARQ-05)
- [ ] Evaluar `dependency-injector` como framework DI

---

## 3. Seguridad y Encriptación

### 3.1 Hallazgos Críticos

| ID | Hallazgo | Severidad | Archivo |
|---|---|---|---|
| SEC-01 | ~~SHA-256 sin salt para contraseñas~~ | ✅ RESUELTO v3.1.0 | Migrado a bcrypt con auto-migración de hashes SHA-256 legacy |
| SEC-02 | ~~Base64 como "encriptación" de credenciales SFTP/SMTP~~ | ✅ RESUELTO v3.1.0 | Migrado a Fernet con backward compat Base64 |
| SEC-03 | **API REST sin autenticación** | CRÍTICA | `api/main.py` — CORS y bind restringidos en v3.1.0, falta JWT |
| SEC-04 | ~~Código de recuperación en texto plano en users.json~~ | ✅ RESUELTO v3.1.0 | Solo hash + TTL 15 min, plaintext eliminado |

**SEC-01**: ~~`hashlib.sha256(password.encode()).hexdigest()`~~ → ✅ **RESUELTO v3.1.0**: Migrado a `bcrypt.hashpw()`. Login detecta hashes SHA-256 legacy y auto-migra a bcrypt.

**SEC-02**: ~~`base64.b64encode()` no es cifrado~~ → ✅ **RESUELTO v3.1.0**: Migrado a `cryptography.fernet.Fernet`. Fallback Base64 para exports antiguos.

**SEC-03**: ~~Todos los endpoints son públicos con CORS wildcard y 0.0.0.0~~ → ⚠️ **PARCIAL v3.1.0**: CORS restringido a localhost, bind en 127.0.0.1, solo GET. **Falta JWT/API-key**.

**SEC-04**: ~~Recovery code en texto plano sin TTL~~ → ✅ **RESUELTO v3.1.0**: Solo hash guardado + TTL 15 min. Campo plaintext eliminado.

### 3.2 Hallazgos Altos

| ID | Hallazgo | Severidad | Detalle |
|---|---|---|---|
| SEC-05 | ~~Contraseña mínima: 4 caracteres~~ | ✅ RESUELTO v3.7.0 | Política 8+ chars, mayúscula, número y símbolo aplicada en use cases y 3 diálogos Qt |
| SEC-06 | ~~Sin protección brute force en login~~ | ✅ RESUELTO v3.6.0 | Lockout tras 5 intentos en `UserAuth.authenticate()` |
| SEC-07 | **Credenciales reales en config JSON** | ALTA | Host SFTP de 1&1 IONOS y username expuestos |
| SEC-08 | ~~API expone `str(e)` en errores 500~~ | ✅ RESUELTO v3.1.0 | Reemplazado por mensajes genéricos |
| SEC-09 | ~~Uvicorn escucha en 0.0.0.0~~ | ✅ RESUELTO v3.1.0 | Cambiado a 127.0.0.1 |

### 3.3 Hallazgos Medios

| ID | Hallazgo | Severidad | Detalle |
|---|---|---|---|
| SEC-10 | ~~XSS potencial en templates email HTML~~ | ✅ RESUELTO v3.6.0 | `html.escape(username)` en `email_service.py` |
| SEC-11 | ~~Path traversal en LocalSyncBackend~~ | ✅ RESUELTO v3.6.0 | `_safe_path()` valida que la ruta resuelta esté dentro de `base_path` |
| SEC-12 | `users.json` sin permisos restrictivos | MEDIA | Guardado con permisos por defecto (644) |
| SEC-13 | Valores fallback en config exponen infraestructura | MEDIA | Host SFTP y username como defaults |
| SEC-14 | ~~Username sin validación en registro~~ | ✅ RESUELTO v3.6.0 | `re.fullmatch(r"[a-zA-Z0-9._\-]+", username)` en `register_user` |

### 3.4 Buenas Prácticas Detectadas

- ✅ `paramiko.RejectPolicy()` — previene MITM en SFTP
- ✅ `server.starttls()` para SMTP
- ✅ Secretos en `.gitignore` (`.env`, configs JSON)
- ✅ Aislamiento de BD por usuario
- ✅ SQLAlchemy ORM con queries parametrizadas (sin inyección SQL)
- ✅ `secrets.token_urlsafe(32)` para tokens de recuperación

### 3.5 Recomendaciones

- [x] **P0** — ~~Migrar a `bcrypt` para hashing de contraseñas con migración de hashes existentes~~ ✅ v3.1.0
- [x] **P0** — ~~Reemplazar Base64 por `cryptography.fernet`~~ ✅ v3.1.0
- [x] **P0** — ~~Añadir autenticación JWT/API-key a la API REST~~ ✅ RESUELTO v3.8.0
- [x] **P0** — ~~Eliminar recovery code en texto plano, guardar solo hash + TTL~~ ✅ v3.1.0
- [x] **P1** — ~~Política de contraseñas: mínimo 8 chars + mayúscula + número + símbolo~~ ✅ v3.7.0
- [x] **P1** — ~~Implementar lockout: 5 intentos → bloqueo 15 min con delay progresivo~~ ✅ v4.0.0 (API + sync_manager)
- [x] **P1** — ~~Cambiar `host="0.0.0.0"` a `host="127.0.0.1"` en uvicorn~~ ✅ v3.1.0
- [x] **P1** — ~~Reemplazar `str(e)` por mensajes genéricos en errores API~~ ✅ v3.1.0
- [x] **P2** — ~~Escapar HTML en plantillas de email (`html.escape()`)~~ ✅ v3.6.0
- [x] **P2** — ~~Validar y sanitizar `remote_path` contra path traversal~~ ✅ v4.0.0 (`_sanitize_path()` en SFTP)
- [x] **P2** — ~~Establecer `chmod 600` en `users.json`~~ ✅ v4.0.0 (`os.open()` con mode 0o600)
- [x] **P2** — ~~Eliminar valores reales de infraestructura en defaults de config~~ ✅ v4.0.0 (`api_secret_key` vacío)
- [x] **P2** — ~~Validar username con regex whitelist (`[a-zA-Z0-9._-]`)~~ ✅ v3.6.0

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
| DB-01 | ~~`guardias.profesor_id` nullable~~ | ✅ RESUELTO v3.1.0 | NOT NULL + ON DELETE CASCADE |
| DB-02 | ~~`guardias.zona_id` nullable~~ | ✅ RESUELTO v3.1.0 | NOT NULL + ON DELETE CASCADE |
| DB-03 | ~~Sin `ON DELETE CASCADE` en profesor→guardias/ausencias~~ | ✅ RESUELTO v3.1.0 | CASCADE añadido |
| DB-04 | ~~Sin UniqueConstraint en guardias~~ | ✅ RESUELTO v3.1.0 | `uq_guardia_asignacion` añadido |
| DB-05 | Sin CheckConstraint en `turno`, `ausencias.tipo`, `recreo`, `porcentaje_jornada` | MEDIA |
| DB-06 | ~~`datetime.utcnow` como default — deprecated en Python 3.12+~~ | ✅ RESUELTO (anterior a auditoría) | `datetime.now(timezone.utc)` ya usado en `models.py`, `gestor_cursos.py`, `exportador.py` |
| DB-07 | `guardias.curso_id` nullable (justificado como "migración gradual" pero sin cleanup) | MEDIA |

### 4.4 Índices

**Existentes** (buenos):
- `idx_guardias_profesor`, `idx_guardias_zona`, `idx_guardias_fecha`, `idx_guardias_turno`
- `idx_guardias_fecha_turno` (compuesto)
- `idx_ausencias_profesor`, `idx_ausencias_fechas`, `idx_ausencias_activa`

**Faltantes** ~~(resueltos — anterior a auditoría)~~:
- ~~`guardias.curso_id`~~ → `ix_guardias_curso_id` ✅ en `models.py`
- ~~`guardias(fecha, turno, recreo)`~~ → `ix_guardias_fecha_turno_recreo` ✅ en `models.py`
- ~~`profesores.turno`~~ → `ix_profesores_turno` ✅ en `models.py`
- ~~`profesores.activo`~~ → `ix_profesores_activo` ✅ en `models.py`
- `ausencias(profesor_id, fecha_inicio, fecha_fin, activa)` — compuesto para queries de rango (pendiente)
- `zonas.nombre_zona` — para `find_by_nombre()` (pendiente)

### 4.5 Migraciones (Alembic)

16 migraciones con estos problemas:

| ID | Hallazgo | Severidad |
|---|---|---|
| DB-08 | Migración duplicada vacía `b939a8969a45` → `0122b6bbdc61` | BAJA |
| DB-09 | Columnas `fecha_inicio/fin` añadidas a zonas en 2 migraciones diferentes | MEDIA |
| DB-10 | Downgrade vacío en `a1b2c3d4e5f6` — rollback imposible | ALTA |
| DB-11 | ~~Inconsistencia modelo/migración: ORM dice `cerrado`, migración crea `archivado`~~ | ✅ RESUELTO (anterior a auditoría) | Migración `e1f2a3b4c5d6_fix_cerrado_indices.py` renombra `archivado` → `cerrado`; ORM consistente |
| DB-12 | `create_user_database()` no ejecuta Alembic stamp — BD sin versión | ALTA |

### 4.6 Database Manager

| ID | Hallazgo | Severidad |
|---|---|---|
| DB-13 | ~~Triple estrategia de init~~ | ✅ RESUELTO v3.4.0 | `initialize_user_database()` condicional: si Alembic ok, no llama `_apply_direct_migrations()` |
| DB-14 | Variables globales mutables sin thread-safety (`_current_engine`, etc.) | ALTA |
| DB-15 | `set_sqlite_pragma` definida 3 veces — código duplicado | BAJA |
| DB-16 | `get_db_session()` auto-commit al salir del `with` — puede ser peligroso | MEDIA |

### 4.7 Recomendaciones

- [x] Normalizar campos JSON a tablas relacionales (`profesor_dias_semana`, `profesor_recreos`, `recreos_config`) ✅ v3.4.0 (migración Alembic `a1b2c3d4e5f7`)
- [x] Añadir `NOT NULL` a `guardias.profesor_id` y `guardias.zona_id` ✅ v3.1.0
- [x] Añadir `ON DELETE CASCADE` en profesor→guardias y profesor→ausencias ✅ v3.1.0
- [x] Añadir UniqueConstraint en guardias para evitar asignaciones duplicadas ✅ v3.1.0
- [x] ~~Añadir CheckConstraints para `turno`, `tipo` de ausencia, `recreo >= 1`~~ ✅ v4.1.0 (7 constraints)
- [x] ~~Crear índices faltantes (curso_id, turno, activo, compuesto triple)~~ ✅ v4.1.0 (14 índices)
- [x] Unificar init de BD: solo Alembic, eliminar `_apply_direct_migrations()` ✅ v3.4.0
- [x] ~~Reemplazar `datetime.utcnow` por `datetime.now(timezone.utc)`~~ ✅ v4.0+ (ya no está en código)
- [ ] Resolver inconsistencia `cerrado` vs `archivado`
- [ ] Añadir locks o thread-local storage en `db_manager.py`

---

## 5. Performance y Optimización

### 5.1 N+1 Queries

| ID | Hallazgo | Severidad | Detalle |
|---|---|---|---|
| PERF-01 | ~~N+1 en API `/api/guardias`~~ | ✅ RESUELTO v3.1.0 | Añadido `joinedload` para zona y profesor |
| PERF-02 | N+1 en `ProfesorRepository.get_all()` | MEDIA | Sin eager loading para `guardias` y `zona_preferida` |
| PERF-03 | ~~N+1 en `sistema_sugerencias_automaticas.py`~~ | ✅ RESUELTO v3.1.0 | Fichero eliminado (código muerto) |

### 5.2 Queries no Optimizadas

| ID | Hallazgo | Severidad |
|---|---|---|
| PERF-04 | `find_disponibles_en_fecha()` carga todos los profesores del turno y filtra en Python | MEDIA |
| PERF-05 | ~~`.count() > 0` en vez de `.first() is not None`~~ | ✅ RESUELTO v4.1.0 | 4 repositorios optimizados |
| PERF-06 | `get_all()` sin paginación en todos los repositorios | BAJA (escala actual) |

### 5.3 Buenas Prácticas Existentes

- ✅ `joinedload` correcto en `GuardiaRepository`, `exportador_pdf.py`, `icalendar_service.py`, `api/routers/guardias.py` (v3.1.0)
- ✅ `PRAGMA journal_mode=DELETE` justificado por compatibilidad OneDrive
- ✅ `NullPool` para SQLite (correcto)

### 5.4 Recomendaciones

- [x] **P0** — ~~Añadir `joinedload` en el endpoint `/api/guardias`~~ ✅ v3.1.0
- [x] ~~Añadir `joinedload(Profesor.zona_preferida)` en `get_all()`~~ ✅ RESUELTO v4.7.0 (+ joinedload curso)
- [x] ~~Mover filtro de disponibilidad a la query SQL~~ ✅ RESUELTO v4.7.0 (find_disponibles_en_fecha usa turno en SQL)
- [x] ~~Reemplazar `.count() > 0` por `.exists()` o `.first() is not None`~~ ✅ RESUELTO v4.1.0

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
| CACHE-01 | ~~`repository_cache.py` re-crea el decorador en cada llamada~~ | ✅ RESUELTO v3.1.0 | Decorador cacheado una sola vez |
| CACHE-02 | ~~**Cache no thread-safe**~~ | ✅ RESUELTO v3.6.1 | `threading.RLock` en `utils/cache.py` protege `_cache_store` y `_cache_stats` |
| CACHE-03 | Cache volátil — se pierde al reiniciar la app | BAJA |

~~**CACHE-01 detalle**: En `repository_cache.py` línea ~58, `cached_func = cache_query(ttl=ttl)(func)` crea un nuevo wrapper sin estado previo en cada invocación.~~ ✅ **RESUELTO v3.1.0**: Movido a `decorator()` scope.

### 6.3 Recomendaciones

- [x] **P0** — ~~Corregir `repository_cache.py` para cachear la función decorada una sola vez~~ ✅ v3.1.0
- [x] **P1** — ~~Añadir `threading.Lock` al `OrderedDict` del caché~~ ✅ v3.6.1 (`threading.RLock`)
- [x] ~~Evaluar `cachetools` como reemplazo (thread-safe, TTLCache, LRUCache built-in)~~ ✅ RESUELTO v4.6.0 (`cache_service.py` con TTLCache 5 min)

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
| ASYNC-01 | ~~**Sync SFTP no usa QThread**~~ | ✅ RESUELTO v3.6.1 | `SyncWorker(QThread)` en `sync_progress_dialog.py`; `main.py` usa señales Qt |
| ASYNC-02 | FastAPI endpoints síncronos (`def` en vez de `async def`) | BAJA (aceptable con SQLite) |
| ASYNC-03 | No hay asyncio, multiprocessing ni thread pools | BAJA |

### 7.3 Recomendaciones

- [x] **P1** — ~~Mover sincronización SFTP a `QThread` con `ProgressDialog`~~ ✅ v3.6.1 (`SyncWorker`)
- [ ] Evaluar `async def` + `run_in_threadpool` para endpoints FastAPI si se migra a PostgreSQL

---

## 8. Escalabilidad y Resiliencia

### 8.1 Retry Logic

| ID | Hallazgo | Severidad |
|---|---|---|
| RES-01 | ~~Sin retry en conexión SFTP — un fallo = operación perdida~~ ✅ RESUELTO v5.2.1 (tenacity + backoff exponencial) | MEDIA |
| RES-03 | ~~Sin retry en BD configurado~~ ✅ RESUELTO v5.9.5 (`_create_session_with_retry` + `max_retries_db`) | MEDIA |
| RES-02 | ~~Sin circuit breaker para SFTP/SMTP~~ ✅ RESUELTO v5.2.1 (pybreaker) | MEDIA |

### 8.2 Circuit Breaker

❌ **No existe.** Ni para SFTP, ni para SMTP, ni para BD.

### 8.3 Graceful Degradation

- ✅ La app funciona offline (SQLite local) — sync SFTP es opcional
- ✅ `SessionLockedDialog` ofrece "Reintentar" cuando hay sesión bloqueada
- ❌ Sin fallback si CP-SAT solver no converge (solo diagnóstico manual)

### 8.4 Recomendaciones

- [x] ~~Implementar retry con backoff exponencial para SFTP (`tenacity` library)~~ ✅ RESUELTO v4.6.0 (backoff 2s→4s→8s, 3 intentos)
- [x] ~~Implementar circuit breaker para servicios externos (SFTP, SMTP)~~ ✅ RESUELTO v4.6.0 (tenacity retry SFTP)
- [x] ~~Implementar el retry de BD que ya está configurado en settings~~ ✅ RESUELTO v4.7.0 (get_db_session con backoff exponencial)

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
| API-04 | ~~Sin rate limiting~~ | ✅ RESUELTO v3.4.0 | `slowapi` 0.1.9 — 60 req/min por IP |
| API-05 | ~~CORS wildcard `allow_origins=["*"]` con `allow_credentials=True`~~ | ✅ RESUELTO v3.1.0 | Restringido a localhost:3000/8080, solo GET |
| API-06 | **`/health` hardcodeado** — no usa el `HealthChecker` real | MEDIA |
| API-07 | ~~Profesores sin paginación~~ | ✅ RESUELTO v4.3.0 | `offset`/`limit`/`total`/`has_more` en `GET /api/v1/profesores` |
| API-08 | Sin sorting paramétrico | BAJA |
| API-09 | ~~Sin schema de error estándar~~ | ✅ RESUELTO v4.3.0 | `{"error": {"code": "...", "message": "..."}}` en 500, 404, 422 |
| API-10 | Cuotas, equidad, estadísticas sin `response_model` tipado | BAJA |

### 9.3 Buenas Prácticas Existentes

- ✅ Swagger UI en `/docs` y ReDoc en `/redoc`
- ✅ Pydantic response models para guardias y profesores
- ✅ Docstrings con Args, Returns, Examples
- ✅ Recursos en plural (`/guardias`, `/profesores`)

### 9.4 Recomendaciones

- [x] ~~Añadir autenticación JWT/API-key~~ ✅ RESUELTO v3.8.0
- [x] Restringir CORS a orígenes específicos ✅ v3.1.0
- [x] Añadir rate limiting (`slowapi` o `fastapi-limiter`) ✅ v3.4.0
- [x] ~~Conectar `/health` al `HealthChecker` real~~ ✅ RESUELTO v3.8.0
- [x] ~~Añadir paginación a `/api/profesores`~~ ✅ RESUELTO v4.3.0
- [ ] Añadir versionado `/v1/`
- [x] ~~Definir schema de error estándar `{"error": {"code": "...", "message": "..."}}`~~ ✅ RESUELTO v4.3.0
- [x] Añadir middleware de error handling para no exponer `str(e)` ✅ v3.1.0

---

## 10. Testing

### 10.1 Estado Actual

- **1222 tests**, 46.02% coverage
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
| TEST-01 | ~~**39.75% coverage**~~ **46.02% coverage (v4.11.0)** — en progreso, target 70% | ALTA | ✅ PARCIAL v4.11.0 |
| TEST-02 | ~~**0 tests para SFTP/SMTP**~~ Cobertura inicial añadida (v3.7.0+) | MEDIA |
| TEST-03 | ~~**0 tests para API REST**~~ Cobertura inicial añadida (v3.7.0+) | MEDIA |
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
| UX-01 | ~~Sin `QValidator` en campos~~ | ✅ RESUELTO v3.4.0 | `QRegularExpressionValidator` en `RegisterDialog` (username) |
| UX-02 | ~~Sin `setAccessibleName`/`setAccessibleDescription`~~ | ✅ RESUELTO v3.4.0 | `setAccessibleName` en todos los campos interactivos de `login_dialog.py` |
| UX-03 | ~~Sin `setTabOrder`~~ | ✅ RESUELTO v3.4.0 | `setTabOrder` explícito en `LoginDialog` y `RegisterDialog` |
| UX-04 | ~~Sin DPI awareness~~ | ✅ RESUELTO v3.4.0 | `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` en `main.py` |
| UX-05 | Dos temas UI coexisten (legacy Material + CCleaner) | BAJA |
| UX-06 | ~~`screen_validator.py` bloquea la app si resolución < 1280x720~~ | ✅ RESUELTO v3.1.0 | Fichero eliminado |

### 12.5 Recomendaciones

- [x] Añadir `QValidator` (QRegularExpressionValidator, QIntValidator) a campos de formulario ✅ v3.4.0
- [x] Añadir `setAccessibleName()` y `setAccessibleDescription()` a widgets interactivos ✅ v3.4.0
- [x] Definir `setTabOrder()` explícito en formularios ✅ v3.4.0
- [x] Añadir soporte DPI con `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` ✅ v3.4.0
- [ ] Eliminar el tema legacy y unificar en CCleaner
- [ ] Permitir uso en baja resolución con scroll en vez de bloquear

---

## 13. Control de Acceso y Multi-tenancy

### 13.1 Autenticación

- Login por username + password hasheado con ~~SHA-256~~ bcrypt (v3.1.0)
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
- [x] ~~Validar username no vacío antes de generar hash~~ ✅ RESUELTO v4.7.0 (_hash_username raises ValueError si vacío)
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
- [x] ~~Añadir UniqueConstraint en guardias para prevenir duplicados a nivel BD~~ ✅ RESUELTO v4.1.0 (`uq_guardia_asignacion`)
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
| `src/domain/services/ejemplo_integracion.py` | Domain services | ~~`docs/examples/` o eliminar~~ | ✅ Eliminado v3.1.0 |
| `src/services/migrar_a_multi_curso.py` | Services | `scripts/` | Es un script de migración one-off |
| `src/services/README_SISTEMA_HIBRIDO.md` | Services | `docs/architecture/` | Documentación fuera de lugar |
| `src/models/models.py` | Models (shim legacy) | ~~Eliminar~~ | ✅ Eliminado v3.1.0 |
| `scripts/test_icalendar.py` | Scripts | `tests/` | Es un test, no un script |
| `scripts/test_initial_config.py` | Scripts | `tests/` | Es un test, no un script |
| `scripts/test_contador_tiempo.py` | Scripts | `tests/` | Es un test, no un script |
| `scripts/prueba_calendario.ics` | Scripts | `tests/fixtures/` | Fixture de test |

### 16.2 Archivos Excesivamente Grandes (necesitan refactorización)

| Archivo | Líneas | Severidad | Propuesta de split |
|---|---|---|---|
| ~~`src/services/exportador_pdf.py`~~ | ~~**1847**~~ | ~~CRÍTICA~~ | ✅ RESUELTO v3.4.1 — 476 líneas; módulos extraidos: `_pdf_mes_consolidado.py`, `_pdf_individual_optimizado.py` |
| `src/presentation/widgets/vista_calendario.py` | **1368** | CRÍTICA | → Separar widget base, renderizado de celdas, diálogos de día, lógica de navegación |
| ~~`src/services/exportador.py`~~ | ~~**1158**~~ | ~~CRÍTICA~~ | ✅ RESUELTO v3.4.1 — 400 líneas; módulo extraido: `_exportador_import.py` |
| ~~`src/services/asignador_guardias_v4_hibrido.py`~~ | **1066** | ✅ RESUELTO v4.5.0 — split en `_asignador_v4_helpers.py` (387L) + `_asignador_v4_fases.py` (341L) + orquestador (276L) |
| ~~`src/presentation/dialogs/initial_config_dialog.py`~~ | ~~**1051**~~ | ~~CRÍTICA~~ | ✅ RESUELTO v3.4.1 — 743 líneas; módulo extraido: `_initial_config_tabs.py` |
| `src/presentation/widgets/progress_indicators.py` | 947 | ALTA | → `worker_thread.py`, `progress_dialog.py`, `decision_handler.py` |
| `src/presentation/forms/profesor_form.py` | 847 | ALTA | → Separar tabla, formulario de edición, validaciones |
| `src/services/asignador_guardias_cpsat.py` | 845 | ALTA | → `cpsat_model.py`, `cpsat_constraints.py`, `cpsat_solver.py` |
| `src/sync/data_exporter.py` | 822 | ALTA | → Separar exportación por entidad |
| `src/presentation/themes/ccleaner_theme.py` | 717 | MEDIA | Aceptable, pero podría separar paleta de colores |

### 16.3 Funcionalidad Duplicada

| Duplicación | Archivos involucrados | Recomendación |
|---|---|---|
| **Logging** | `src/utils/logger.py` (redirige a core) vs `src/core/logging.py` | ✅ **RESUELTO v3.1.0**: `utils/logger.py` es thin re-export de `core/logging` |
| **Iconos** | `src/utils/icons.py` vs `src/utils/icon_manager.py` | Unificar en un solo módulo |
| **Estilos UI** | `src/ui_styles.py` (legacy Material) vs `src/presentation/themes/ccleaner_theme.py` | Migrar todo a ccleaner_theme (20+ archivos importan `ui_styles`) |
| **Models ORM** | ~~`src/models/models.py` vs `src/infrastructure/database/models.py`~~ | ✅ **RESUELTO v3.1.0**: Shim eliminado |
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
| ORG-02 | ~~`data/users.json` trackeado en git con hashes de contraseñas~~ | ✅ RESUELTO v3.1.1 |
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
| **Backup completo exportable** | ✅ RESUELTO v4.2.0 | `backup_database()` + `restore_database()` en `db_manager.py`, permisos 600, backup seguridad automático |

### 17.4 Importaciones Faltantes

| Funcionalidad | Estado | Detalle |
|---|---|---|
| Importar profesores desde Excel | ✅ Funcional | `importar_profesores_desde_excel.py` (como script) |
| **Importar profesores desde UI** | ⚠️ Parcial | `ImportExportForm` existe pero la integración con el script no es transparente |
| ~~**Importar zonas desde Excel/CSV**~~ | ✅ RESUELTO v4.2.0 | `src/services/importador_zonas.py`, función unificada `importar_zonas()` detecta .csv/.xlsx |
| **Importar festivos desde archivo** | ❌ No existe | Solo configuración manual |
| ~~**Restaurar backup**~~ | ✅ RESUELTO v4.2.0 | `restore_database(username, backup_path)` con validación SQLite y backup de seguridad |
| **Importar desde otro curso** | ❌ No existe | Al crear un curso nuevo hay que re-configurar todo |

### 17.5 ~~Campo `curso_id` en Profesor~~ ✅ RESUELTO v4.4.0

~~Dos TODOs en `gestor_cursos.py` indican que los profesores no están vinculados a cursos específicos. Son "globales".~~

`Profesor.curso_id` añadido como FK nullable a `cursos_escolares.id`. `GestorCursos.copiar_profesores_curso_anterior()` ahora filtra por `curso_id` y asigna el nuevo en las copias. Migración `b1c2d3e4f5a6`, índice `ix_profesores_curso_id`, 10 tests.

### 17.6 ML Predictor — ✅ Eliminado en v3.1.0

~~`ml_predictor_estrategia.py` estaba completamente implementado (sklearn RandomForest + pickle) pero nunca se usaba y añadía ~200MB de dependencias.~~ Eliminado junto con `scikit-learn` y `numpy` de requirements.txt.

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

> ✅ **RESUELTO v3.1.0**: Los 16 ficheros huérfanos listados a continuación fueron eliminados en v3.1.0 (~2.800 líneas de código muerto). También se eliminaron 3 tests huérfanos asociados.

| Fichero | Líneas | Estado |
|---|---|---|
| ~~`src/services/ml_predictor_estrategia.py`~~ | 392 | ✅ Eliminado v3.1.0 |
| ~~`src/services/sistema_sugerencias_automaticas.py`~~ | ~200 | ✅ Eliminado v3.1.0 |
| ~~`src/services/visualizador_conflictos_guardias.py`~~ | ~150 | ✅ Eliminado v3.1.0 |
| ~~`src/services/cache_soluciones_guardias.py`~~ | ~180 | ✅ Eliminado v3.1.0 |
| ~~`src/services/optimizaciones_asignador.py`~~ | ~200 | ✅ Eliminado v3.1.0 |
| ~~`src/services/integrador_orquestador_ui.py`~~ | ~250 | ✅ Eliminado v3.1.0 |
| ~~`src/domain/services/ejemplo_integracion.py`~~ | ~80 | ✅ Eliminado v3.1.0 |
| ~~`src/models/models.py`~~ | ~30 | ✅ Eliminado v3.1.0 |
| ~~`src/presentation/main_window.py`~~ | ~300 | ✅ Eliminado v3.1.0 |
| ~~`src/presentation/components/top_bar.py`~~ | ~100 | ✅ Eliminado v3.1.0 |
| ~~`src/presentation/components/sidebar_menu.py`~~ | ~120 | ✅ Eliminado v3.1.0 |
| ~~`src/presentation/components/ccleaner_topbar.py`~~ | ~80 | ✅ Eliminado v3.1.0 |
| ~~`src/domain/schemas/` (3 ficheros)~~ | ~200 | ✅ Eliminado v3.1.0 |
| ~~`src/utils/query_optimizer.py`~~ | 305 | ✅ Eliminado v3.1.0 |
| ~~`src/utils/screen_validator.py`~~ | ~50 | ✅ Eliminado v3.1.0 |
| ~~`src/presentation/forms/simple_profesor_form.py`~~ | ~150 | ✅ Eliminado v3.1.0 |

### 18.2 Recomendaciones de Limpieza

> ✅ **RESUELTO v3.1.0**: Todas las recomendaciones P0 y P1 de esta sección fueron implementadas.

- [x] **P0** — ~~Eliminar los 6 ficheros CRÍTICOS de `src/services/`~~ ✅ v3.1.0
- [x] **P0** — ~~Eliminar `src/domain/schemas/` completo~~ ✅ v3.1.0
- [x] **P1** — ~~Eliminar `src/models/models.py`, actualizar imports~~ ✅ v3.1.0
- [x] **P1** — ~~Eliminar `main_window.py`, `top_bar.py`, `sidebar_menu.py`, `ccleaner_topbar.py`~~ ✅ v3.1.0
- [x] **P1** — ~~Eliminar `simple_profesor_form.py`, `screen_validator.py`~~ ✅ v3.1.0
- [x] **P2** — ~~`query_optimizer.py` eliminado~~ ✅ v3.1.0

### 18.3 Funcionalidad Duplicada

| Duplicación | Archivos | Acción |
|---|---|---|
| **Logging** | `utils/logger.py` vs `core/logging.py` (19+ imports cada uno) | ✅ **RESUELTO v3.1.0**: `utils/logger.py` = thin re-export |
| **Iconos** | `utils/icons.py` vs `utils/icon_manager.py` | Unificar en un solo módulo |
| **Estilos UI** | `ui_styles.py` (legacy) vs `presentation/themes/ccleaner_theme.py` (20+ archivos importan el legacy) | Migrar todo a `ccleaner_theme.py` |
| **Models ORM** | ~~`models/models.py` vs `infrastructure/database/models.py`~~ | ✅ **RESUELTO v3.1.0**: Shim eliminado |
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
| SAN-01 | ~~`services/ml_predictor_estrategia.py` L353-363~~ | ~~`pickle.load()` sin validación~~ | ✅ RESUELTO v3.1.0 — Fichero eliminado |
| SAN-02 | ~~`sync/data_exporter.py` L470-505~~ | ~~Contraseñas "encriptadas" con `base64.b64encode()`~~ | ✅ RESUELTO v3.1.0 — Migrado a Fernet |
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

- [x] **P0** — ~~Eliminar `ml_predictor_estrategia.py`~~ ✅ v3.1.0
- [x] **P0** — ~~Reescribir `base64` como "cifrado" en `data_exporter.py`~~ ✅ v3.1.0 (Fernet)
- [x] **P1** — ~~Reemplazar los 15 `except Exception: pass` por logging explícito~~ ✅ v3.1.1
- [x] **P1** — ~~Reemplazar todos los `print()` de debug por `logger.debug()`~~ ✅ v3.1.1
- [x] **P1** — ~~Unificar sistema de logging dual~~ ✅ v3.1.0 (`utils/logger.py` = re-export)
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

| Cambio | Impacto para web | Estado |
|---|---|---|
| ~~**Limpiar `domain/services/`** de imports ORM~~ | Restaura Clean Architecture, dominio portable | ✅ v3.4.0 (ARQ-01) |
| **Hacer que los routers de profesores/guardias/estadísticas usen use cases** (ya existen) | API lista para CRUD | Pendiente |
| **Condicionar PRAGMAs al dialecto SQLite** en `db_manager.py` | Permite cambiar a PostgreSQL con 1 env var | Pendiente |
| **Extraer `integrador_orquestador_ui.py`** a `presentation/` (si se mantiene) | Deja `services/` 100% libre de PyQt6 | Pendiente |
| **Añadir `user_id` como concepto en domain** (no tabla aún) | Prepara para multi-tenant | Pendiente |
| ~~**Eliminar queries directas desde presentation/**~~ | Desacopla UI de BD | ✅ v3.6.0 (ARQ-02) |

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

### 21.1 Sistema de Logging (✅ Unificado en v3.1.0)

~~Coexisten **dos sistemas de logging**~~ → ✅ **RESUELTO v3.1.0**: `utils/logger.py` es ahora un thin re-export de `core/logging`. Todos los imports delegan al mismo sistema.

| Sistema | Módulo | Estado |
|---|---|---|
| Estructurado (structlog) | `core.logging.get_logger` | ✅ Canónico |
| Simple (wrapper) | `utils.logger.get_logger` | ✅ Re-export de core.logging |

**Problema**: ~~Un desarrollador no sabe cuál usar.~~ ✅ **RESUELTO v3.1.0**: Ambos imports van al mismo sistema. Usar `core.logging` en código nuevo.

~~**Recomendación**: Unificar en `core.logging`, eliminar `utils.logger`, actualizar los ~19 imports.~~ ✅ Hecho.

### 21.2 Manejo de Errores

| Aspecto | Estado | Detalle |
|---|---|---|
| Jerarquía de excepciones | ✅ Bien diseñada | `core/exceptions.py` con excepciones tipadas por dominio |
| `except Exception: pass` | ❌ 15 bloques | Ocultan fallos reales (ver §19.2) |
| Error boundaries en GUI | ⚠️ Parcial | `BaseForm` tiene `mostrar_error()`, pero no hay `try/except` global en event handlers |
| Errores API | ✅ Mensajes genéricos | Resuelto v3.1.0 |
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

- [x] **P0** — ~~Unificar logging: eliminar `utils/logger.py`, migrar todo a `core/logging`~~ ✅ v3.1.0
- [x] ~~Añadir correlation IDs para trazar operaciones cross-capa~~ ✅ RESUELTO v4.7.0 (middleware HTTP `X-Correlation-ID` en FastAPI)
- [ ] **P1** — Reemplazar `except Exception: pass` por logging explícito (ver §19.2)
- [x] **P1** — ~~Añadir error boundary global en `ccleaner_main_window.py` que capture excepciones no manejadas y las muestre/logee~~ ✅ RESUELTO v3.8.0 (sys.excepthook en main.py)
- [x] **P2** — ~~Conectar `HealthChecker` al endpoint `/health`~~ ✅ RESUELTO v3.8.0
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
| MEJ-04 | ~~**sklearn como dependencia obligatoria sin uso real**~~ | ✅ RESUELTO v3.1.0 | Eliminado de requirements.txt junto con numpy |

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
| MEJ-09 | ~~**Coverage 39.75% → target 70%**~~ **46.02% (v4.11.0), sigue en progreso** | ALTA | Priorizar tests en: servicios de asignación, exportadores, sync, API |
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

| Tarea | Prioridad | Estado |
|---|---|---|
| ~~Migrar a bcrypt para contraseñas~~ | P0 | ✅ v3.1.0 |
| ~~Cifrado real de credenciales SFTP/SMTP (Fernet)~~ | P0 | ✅ v3.1.0 |
| Autenticación JWT en API REST | P0 | Pendiente |
| ~~Eliminar recovery code en texto plano + añadir TTL~~ | P0 | ✅ v3.1.0 |
| ~~Cambiar uvicorn a 127.0.0.1~~ | P0 | ✅ v3.1.0 |
| ~~Reemplazar str(e) por mensajes genéricos en API~~ | P0 | ✅ v3.1.0 |
| ~~Restringir CORS a orígenes específicos~~ | P0 | ✅ v3.1.0 |

### Fase 2 — Código Muerto y Sanitización

| Tarea | Prioridad | Estado |
|---|---|---|
| ~~Eliminar 6 ficheros CRÍTICOS orphan de `src/services/`~~ | P0 | ✅ v3.1.0 |
| ~~Eliminar `src/domain/schemas/`, `src/models/models.py`, UI legacy~~ | P0 | ✅ v3.1.0 |
| ~~Eliminar sklearn de requirements.txt~~ | P0 | ✅ v3.1.0 |
| ~~Reemplazar 15 `except Exception: pass` por logging~~ | P1 | ✅ v3.1.1 |
| ~~Reemplazar `print("DEBUG:...")` por `logger.debug()`~~ | P1 | ✅ v3.1.1 |
| ~~Unificar logging dual → solo `core/logging`~~ | P1 | ✅ v3.1.0 |
| Eliminar `sftp_config.json` y `smtp_config.json` legacy | P1 | No aplica — son archivos de credenciales en producción, usados activamente |
| ~~Limpiar feature flags y settings huérfanos~~ | P2 | ✅ v3.6.1 — `recreo_manana_1/2`, `recreo_tarde_1/2` eliminados de `settings.py` |

### Fase 3 — Performance y Bugs Críticos

| Tarea | Prioridad | Estado |
|---|---|---|
| ~~Corregir N+1 en `/api/guardias` (joinedload)~~ | P0 | ✅ v3.1.0 |
| ~~Corregir bug de `repository_cache.py`~~ | P0 | ✅ v3.1.0 |
| ~~Añadir thread-safety al caché (Lock)~~ | P1 | ✅ v3.6.1 (`threading.RLock`) |
| ~~Mover sync SFTP a QThread~~ | P1 | ✅ v3.6.1 (`SyncWorker`) |

### Fase 4 — Integridad de BD

| Tarea | Prioridad | Estado |
|---|---|---|
| ~~Añadir NOT NULL a guardias.profesor_id y zona_id~~ | P1 | ✅ v3.1.0 |
| ~~Añadir ON DELETE CASCADE profesor→guardias/ausencias~~ | P1 | ✅ v3.1.0 |
| ~~Añadir UniqueConstraint en guardias~~ | P1 | ✅ v3.1.0 |
| ~~Crear índices faltantes~~ | P1 | ✅ anterior a auditoría (parcial) |
| ~~Resolver inconsistencia cerrado/archivado~~ | P1 | ✅ anterior a auditoría |
| ~~Unificar init BD: solo Alembic~~ | P2 | ✅ v3.4.0 |

### Fase 5 — Seguridad Media y Autenticación

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| Política contraseñas: 8+ chars + complejidad | P1 | Pendiente |
| Lockout tras 5 intentos fallidos | P1 | Pendiente |
| ~~Rate limiting en API~~ | P1 | ✅ v3.4.0 (`slowapi`) |
| Escapar HTML en emails | P2 | Pendiente |
| Sanitizar paths en sync | P2 | Pendiente |
| Validar/sanitizar username | P2 | Pendiente |

### Fase 6 — Testing y Observabilidad

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| ~~Tests de API REST con TestClient~~ | P1 | ✅ v3.7.0 (21 tests en `test_api_rest.py`) |
| ~~Tests de SFTP/SMTP con mocks~~ | P1 | ✅ v3.7.0 (incluidos en `test_api_rest.py`) |
| Conectar /health al HealthChecker real | P2 | Bajo |
| Target: coverage 70%+ | P2 | Alto |
| Añadir correlation IDs para trazabilidad | P2 | Medio |
| Añadir error boundary global en GUI | P2 | Bajo |

### Fase 7 — Arquitectura y Preparación Web

| Tarea | Prioridad | Estado |
|---|---|---|
| ~~Limpiar domain/services de imports ORM (4 ficheros)~~ | P1 | ✅ v3.4.0 (ARQ-01) |
| ~~Hacer que routers API usen use cases (ya existen)~~ | P1 | ✅ v3.7.0 — profesores y guardias migrados |
| ~~Condicionar PRAGMAs SQLite al dialecto en db_manager~~ | P1 | ✅ v3.6.1 — ya condicional con `IS_SQLITE` |
| Migrar servicios legacy a usar repositorios | P2 | Pendiente |
| ~~Crear entidades dominio para Ausencia/Config/Curso~~ | P2 | ✅ v3.4.0 (ARQ-03) |
| ~~Eliminar acceso directo a BD desde presentación (36 imports)~~ | P2 | ✅ v3.6.0 (ARQ-02) |
| ~~Normalizar campos JSON a tablas relacionales~~ | P2 | ✅ v3.4.0 (migración `a1b2c3d4e5f7`) |
| Expandir API a CRUD completo | P2 | Pendiente |

### Fase 8 — UX/UI

| Tarea | Prioridad | Estado |
|---|---|---|
| ~~Añadir QValidator a formularios~~ | P2 | ✅ v3.4.0 (UX-01) |
| Migrar 20+ imports de `ui_styles.py` a `ccleaner_theme.py` | P2 | Pendiente |
| ~~Accesibilidad (AccessibleName, TabOrder)~~ | P3 | ✅ v3.4.0 (UX-02/03) |
| ~~Eliminar ventana legacy (`main_window.py`)~~ / tema legacy pendiente | P3 | ✅ ventana v3.1.0 (ARQ-05) / tema pendiente |
| Homogeneizar CSS inline en 3 formularios | P3 | Pendiente |

### Fase 9 — Organización y Limpieza

| Tarea | Prioridad | Estado |
|---|---|---|
| ~~`git rm --cached data/users.json`~~ | P0 | ✅ v3.1.1 (ORG-02) |
| ~~Unificar `utils/icons.py` + `utils/icon_manager.py`~~ | P1 | ✅ v3.7.0 — `icon_manager.py` es alias de `icons.py` |
| ~~Mover scripts one-off a `scripts/archive/`~~ | P2 | ✅ v3.7.0 |
| Mover tests sueltos de `scripts/` a `tests/` | P2 | Pendiente |
| ~~Añadir `__init__.py` a `src/services/`~~ | P2 | ✅ v3.7.0 |
| ~~Unificar 4 scripts de benchmark en 1~~ | P3 | ✅ RESUELTO v3.8.0 — `scripts/benchmark.py` |

### Fase 10 — Features Pendientes

| Tarea | Prioridad | Esfuerzo |
|---|---|---|
| ~~Implementar `es_sustitucion`/`profesor_sustituido_id`/`notas` en Guardia~~ | P0 | ✅ v3.7.0 — ORM, migración Alembic `b2c3d4e5f6a7`, mapper y repositorio |
| Resolver TODO olvidado de settings.py (deprecar v3.1→v4.0) | P0 | ✅ Ya eliminado
| ~~Añadir export CSV/Excel de guardias~~ | P1 | ✅ RESUELTO v3.9.0 — `GET /api/v1/guardias/export/csv` y `/export/xlsx` |
| ~~Añadir export PDF de informe de ausencias~~ | P1 | Bajo | Ya existe en `src/services/exportador_pdf.py`
| ~~Completar import de profesores desde UI (no solo script)~~ | P1 | ✅ RESUELTO v3.9.0 — soporte CSV + función unificada `importar_profesores()` |
| ~~Implementar import de zonas desde CSV/Excel~~ | P2 | ✅ RESUELTO v4.2.0 — `src/services/importador_zonas.py` |
| ~~Implementar backup/restore completo~~ | P2 | ✅ RESUELTO v4.2.0 — `backup_database()` + `restore_database()` en `db_manager.py` |
| Implementar import de configuración desde otro curso | P2 | Medio |
| ~~Añadir `capacidad_profesores` y `activa` al modelo Zona~~ | P2 | ✅ RESUELTO v3.8.0 — ORM + migración `c3d4e5f6a7b8` |
| ~~Vincular profesores a cursos (`curso_id` en Profesor)~~ | P3 | ✅ RESUELTO v4.4.0 — FK + relación ORM + migración + 10 tests |

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

*Documento generado automáticamente. Última actualización: 16/04/2026 — v3.1.0 (correcciones de seguridad, limpieza y BD).*
