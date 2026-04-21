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

## Optimización de tokens

- Leer archivos en bloques grandes, no línea a línea.
- No releer archivos ya leídos en la misma conversación.
- Usar Grep para búsquedas exactas; exploración abierta solo con Agent/Explore.
- No explorar directorios ya conocidos de esta sesión.
- Antes de editar, confirmar que se tiene contexto suficiente; no buscar de más.
- Agrupar ediciones independientes en paralelo.
- No repetir información que el usuario ya sabe.

## Referencia

Stack, arquitectura, versionado, commits, CHANGELOG, workflow post-cambios y archivos protegidos: ver `.claude/CLAUDE.md`.
