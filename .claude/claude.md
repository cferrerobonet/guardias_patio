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
- **Tests**: pytest + pytest-qt (~2100 tests). Ejecutar con `make test` o `pytest tests/ -v`
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
├── services/         # Servicios de aplicación — polimórficos (Session | RepositoryFactory)
├── sync/             # SFTP sync (Paramiko) a 1&1 IONOS
├── utils/            # Helpers, constantes, validadores
```

## Patrón polimórfico (Session | RepositoryFactory)

Todos los servicios en `src/services/` y clases en `src/presentation/` aceptan indistintamente una `Session` de SQLAlchemy o un `RepositoryFactory`. Normalizar siempre en `__init__`:

```python
from infrastructure.repositories.repository_factory import RepositoryFactory

def __init__(self, session_or_factory):
    self.session = (
        session_or_factory.session
        if isinstance(session_or_factory, RepositoryFactory)
        else session_or_factory
    )
```

Para funciones standalone (sin clase), eliminar la anotación de tipo `: Session` del parámetro.

## Versionado

- Versión en `src/config/settings.py` → campo `app_version`
- Semantic Versioning: MAJOR.MINOR.PATCH
  - fix → patch (+0.0.1)
  - feat → minor (+0.1.0)
  - breaking change → major (+1.0.0)
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

1. **Tests** — `pytest tests/ --tb=no -q`. Si hay fallos nuevos, corregirlos antes de continuar.
2. **Bump versión** — Editar `app_version` en `src/config/settings.py`
3. **CHANGELOG.md** — Añadir entrada con fecha actual bajo la nueva versión
4. **Commit + tag + push** (sin pedir confirmación):
   ```bash
   git add -A
   git commit -m "tipo(scope): descripción"
   git tag v{nueva_versión}
   git push && git push --tags
   ```

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
- Usar Grep para búsquedas exactas, Agent/Explore solo para búsquedas abiertas.
- No explorar directorios ya conocidos de esta sesión.
- Antes de editar, confirmar que se tiene contexto suficiente; no buscar de más.
- Agrupar ediciones múltiples en paralelo cuando no haya dependencias entre ellas.
- No repetir información que el usuario ya sabe.
