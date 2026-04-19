---
trigger: always_on
---

## Reglas de comunicación

- Respuestas mínimas. Sin explicaciones innecesarias, sin código de ejemplo no solicitado.
- No añadir docstrings, comentarios, type annotations ni error handling a código no modificado.
- No refactorizar ni "mejorar" código que no se haya pedido tocar.
- No crear archivos nuevos salvo que sea estrictamente necesario.
- No crear archivos markdown para documentar cambios salvo petición explícita.
- Responder siempre en español.

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

## Optimización de tokens

- Leer archivos en bloques grandes, no línea a línea.
- No releer archivos ya leídos en la misma conversación.
- Usar `grep_search` para búsquedas exactas, `semantic_search` solo cuando sea necesario.
- No explorar directorios ya conocidos de esta sesión.
- Antes de editar, confirmar que se tiene contexto suficiente; no buscar de más.
- Agrupar ediciones múltiples con `multi_replace_string_in_file`.
- No repetir información que el usuario ya sabe.

