# CLAUDE.md — Guardias de Patio

Las instrucciones del proyecto están en `AGENTS.md` (importado abajo); las de cada zona del código, en `.claude/rules/`. No añadir aquí reglas del proyecto: van allí.

@AGENTS.md

## Propio de este asistente

- **Abrir la sesión en esta carpeta**, no en la raíz de la bóveda: solo así se aplican `.claude/settings.json` (gancho y exclusión de los CLAUDE.md de Obsidian) y se cargan las reglas por zona.
- **Subagentes con el modelo justo** (parámetro `model`): Haiku para búsquedas y comprobaciones mecánicas; Sonnet para ediciones acotadas, tests y tareas con patrón establecido; Opus para planificación o depuración sin causa evidente. Ante la duda, el inferior.
- Salidas largas (suite completa, cobertura, greps amplios, lecturas de `auditoria/`) en un subagente o filtradas con `tail`/`grep`: lo que entra en el contexto se paga en cada turno.
- **Una versión publicada cierra la tarea**: al terminar, recordar en una línea que conviene `/clear` antes de la siguiente.
