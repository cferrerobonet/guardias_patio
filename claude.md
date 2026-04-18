# Guardias de Patio — Instrucciones para Claude

## Reglas de comunicación

- Respuestas mínimas. Sin explicaciones innecesarias, sin código de ejemplo no solicitado.
- No añadir docstrings, comentarios, type annotations ni error handling a código no modificado.
- No refactorizar ni "mejorar" código que no se haya pedido tocar.
- No crear archivos nuevos salvo que sea estrictamente necesario.
- No crear archivos markdown para documentar cambios salvo petición explícita.
- Responder siempre en español.

## Stack y convenciones

- **Python 3.11+**, PyQt6 6.7.0, SQLAlchemy 2.0, FastAPI, OR-Tools CP-SAT, Pydantic v2
- **Arquitectura**: Clean Architecture híbrida + DDD táctico (entities, VOs, repo pattern)
- **Linter/Formatter**: Ruff (line-length=100, quote-style=double)
- **Types**: mypy strict progresivo — obligatorio en `domain/`, relajado en `presentation/`
- **Tests**: pytest + pytest-qt (~990 tests). Ejecutar con `make test` o `pytest tests/ -v`
- **DB**: SQLite por usuario (`data/users/{hash}/guardias_patio.db`), migraciones con Alembic
- **Entry points**: GUI (`src/main.py`), API REST (`src/api/main.py`)

## Estructura src/

```
src/
├── api/              # FastAPI REST
├── application/      # Use cases, DTOs, factories
├── config/           # Pydantic BaseSettings (settings.py)
├── core/             # Cross-cutting: exceptions, logging, paths
├── database/         # SQLAlchemy db_manager
├── domain/           # Entities, VOs, repo interfaces, domain services
├── infrastructure/   # Repos concretos, mappers, DB
├── models/           # ORM SQLAlchemy (models.py)
├── presentation/     # PyQt6 UI (ventanas, diálogos, componentes)
├── services/         # Servicios aplicación (legacy, importa ORM directo)
├── sync/             # SFTP sync (Paramiko) a 1&1 IONOS
├── utils/            # Helpers, constantes, validadores
```

## Versionado

- Versión en `src/config/settings.py` → campo `app_version` (actualmente `"3.0.0"`, tag git `v3.2.1`)
- Semantic Versioning: MAJOR.MINOR.PATCH
- Bump manual: editar `app_version` en settings.py

## Commits

Conventional Commits en español, minúscula tras los dos puntos:
```
tipo(scope): descripción breve en español
```
Tipos: `feat`, `fix`, `refactor`, `style`, `perf`, `test`, `chore`, `docs`
Scope opcional: `ui`, `api`, `domain`, `sync`, `db`, `algo`, `config`

## CHANGELOG.md

Formato Keep a Changelog (español) + SemVer. Secciones:
- `🎯 Resumen` — una línea resumen
- `✨ Added` — nuevas funcionalidades
- `Changed` — cambios en funcionalidades existentes
- `Fixed` — correcciones de bugs
- `🧹 Housekeeping` — limpieza, refactors internos

## Workflow post-modificaciones (OBLIGATORIO)

Después de CADA conjunto de modificaciones, ejecutar en este orden:

1. **Bump versión** — Editar `app_version` en `src/config/settings.py` según SemVer:
   - fix → patch (+0.0.1)
   - feat → minor (+0.1.0)
   - breaking change → major (+1.0.0)
2. **CHANGELOG.md** — Añadir entrada con fecha actual bajo la nueva versión
3. **Commit + Push**:
   ```bash
   git add -A
   git commit -m "tipo(scope): descripción"
   git tag v{nueva_versión}
   git push && git push --tags
   ```
4. **Verificar** — Abrir CHANGELOG.md para revisión

> Preguntar al usuario antes de ejecutar `git push` y `git push --tags`.

## Seguimiento de auditorías/guiones (OBLIGATORIO)

Cuando se implementen cambios a partir de un documento de auditoría, guion técnico o lista de tareas estructurada:
- Al completar cada ítem, actualizar el documento fuente marcándolo como resuelto (`~~texto~~` + `✅ RESUELTO vX.Y.Z`) antes de pasar al siguiente.
- Hacer commit del documento actualizado junto con los cambios de código (o inmediatamente después).

## Archivos protegidos (NO MODIFICAR)

- `sftp_config.json`, `smtp_config.json` — credenciales, gitignored
- `data/` — datos de usuario, gitignored
- `alembic/versions/` — migraciones existentes (solo crear nuevas)

## Optimización de tokens

- Leer archivos en bloques grandes, no línea a línea.
- No releer archivos ya leídos en la misma conversación.
- Usar `grep_search` para búsquedas exactas, `semantic_search` solo cuando sea necesario.
- No explorar directorios ya conocidos de esta sesión.
- Antes de editar, confirmar que se tiene contexto suficiente; no buscar de más.
- Agrupar ediciones múltiples con `multi_replace_string_in_file`.
- No repetir información que el usuario ya sabe.

## Deuda técnica conocida (auditoría 16/04/2026)

### Crítico — Resolver YA

- **BD**: `data/users.json` posiblemente trackeado en git con hashes de contraseñas (ORG-02)

### Alto — Prioridad siguiente

- **Arquitectura**: 20+ servicios en `src/services/` importan ORM directamente (ARQ-01)
- **Arquitectura**: 15+ widgets en `presentation/` ejecutan queries SQLAlchemy directas (ARQ-02)
- **Arquitectura**: 4 domain services importan infraestructura, violando Clean Architecture
- **Sanitización**: 15 bloques `except Exception: pass` ocultan fallos reales
- **Sanitización**: 8+ `print("DEBUG:...")` en producción → reemplazar por logger
- **BD**: Triple estrategia de init (Alembic + create_all + SQL directo) (DB-13)
- **Testing**: 39.75% coverage, 0 tests API REST, 0 tests SFTP/SMTP
- **Features**: Sistema de sustituciones incompleto (`es_sustitucion`, `profesor_sustituido_id`, `notas` hardcodeados)
- **Archivos grandes**: 5 ficheros >1000 líneas necesitan split (exportador_pdf 1847, vista_calendario 1368, exportador 1158, asignador_v4 1140, initial_config_dialog 1051)
- **Duplicación**: iconos, estilos UI — duplicados

### Medio — Planificado

- **BD**: Campos JSON violan 1NF (dias_semana_permitidos, recreos_permitidos, recreos_config)
- **BD**: Inconsistencia modelo/migración: ORM dice `cerrado`, migración crea `archivado`
- **BD**: Índices faltantes (curso_id, turno, activo, compuesto triple)
- **BD**: `datetime.utcnow` deprecated en Python 3.12+
- **API**: Solo GET, sin versionado, sin rate limiting, sin schema de error estándar
- **UX**: Sin QValidator, sin accesibilidad, sin TabOrder, sin DPI awareness
- **Organización**: 9 archivos mal ubicados, `ui_styles.py` legacy con 20+ imports
- **Config**: 5 feature flags huérfanos nunca consultados en código
- **Config**: `pyproject.toml` incompleto (falta [project], [build-system], dependencias)
- **Preparación web**: Cobertura API ~15%, domain services contaminados, patrón per-user SQLite bloqueante

## Actualización de este archivo

Este `claude.md` debe actualizarse cuando:
- Cambie la estructura del proyecto (nuevos módulos, renombramientos)
- Se adopten nuevas convenciones (formateo, testing, CI/CD)
- Se resuelva deuda técnica documentada aquí
- Se añadan nuevas herramientas o dependencias relevantes
