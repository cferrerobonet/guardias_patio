---
tags:
  - gestion-centro
  - auditoria
  - herramientas
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Eficiencia de agentes: instrucciones, agentes, skills y tokens

## 1. Qué se carga hoy en cada sesión

| Fuente | Tamaño aprox. | Relevancia para trabajar en el código |
| --- | --- | --- |
| instrucciones globales de las bóvedas | 1,2 k tokens | Baja: reglas de Obsidian, plugins, wikilinks |
| instrucciones de la bóveda 02 EPLA | 1,3 k tokens | Baja: estructura de la bóveda, tags |
| fichero de instrucciones del proyecto (`.claude/`) | 1,1 k tokens | Alta, pero duplica `.agents/rules/reglas.md` y `.agents/workflows/post-cambios.md` |
| fichero de reglas de agentes (`.claude/`) | 0,1 k | Media |
| Memoria del asistente (`MEMORY.md`) | variable | Alta si contiene mapa y comandos |
| Skills disponibles (solo nombres) | pequeño | – |

Los tres ficheros de instrucciones se concatenan: ~3,6 k tokens fijos por turno, dos tercios sin uso para tareas de código. No se pueden desactivar los de la bóveda desde el repo, pero sí evitar que el del proyecto repita lo que ya dicen y añadir lo que ahorra exploración.

## 2. Coste observado en esta sesión

Para llegar a contexto suficiente hicieron falta ~45 lecturas de ficheros y ~20 búsquedas: estructura de `src`, entry points reales, flujo de generación, scripts de build, entorno Python válido, comandos de test que funcionan. Casi todo es estable y debería estar en un **mapa rápido** de 40 líneas en el fichero de instrucciones, en la memoria persistente o en un skill.

## 3. Hallazgos (DEV)

| ID | Sev. | Hallazgo | Recomendación |
| --- | --- | --- | --- |
| DEV-001 | P2 | El fichero de instrucciones duplica reglas de `.agents/rules` y `.agents/workflows`; todas se cargan | Una sola fuente: el fichero de instrucciones; `.agents/*` sólo enlazan |
| DEV-002 | P2 | Falta mapa rápido: dónde está cada flujo, qué formularios están registrados, qué scripts son canónicos | Sección "Mapa rápido" en el fichero de instrucciones (añadida) |
| DEV-003 | P3 | Comandos incorrectos o lentos: `make test` con cov, intérprete no documentado, `make test-fast` roto, `make windows` obsoleto | Sección "Comandos que funcionan" (añadida) y arreglar `Makefile` (BLD-002) |
| DEV-004 | P3 | Sin skills de proyecto: cada compilación/test se reexplica | 4 skills creados |
| DEV-005 | P3 | `settings.local.json` con permisos mínimos → prompts por cada comando de lectura | Ampliar allowlist de lecturas y tests (`/fewer-permission-prompts`) |
| DEV-006 | P3 | `.agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md` (41 KB) se lee entero cuando se audita | Referenciar por secciones; usar `auditoria/02` como instancia corta |

## 4. Cambios aplicados a el fichero de instrucciones del asistente (`.claude/`)

- Se conservan todas las reglas vigentes (comunicación, stack, patrón polimórfico, versionado, commits, changelog, workflow post-cambios, seguimiento de auditorías, archivos protegidos).
- Se eliminan repeticiones y texto explicativo.
- Se añade **Mapa rápido** (vistas registradas, flujo de generación, scripts canónicos, ficheros muertos a no tocar).
- Se añade **Comandos que funcionan** (intérprete, tests rápidos, auditoría, build).
- Se añade **Skills del proyecto** y la regla de no cargar el agente portable completo.
- Se retira la palabra prohibida por la bóveda del título.

`.agents/rules/reglas.md` y `.agents/workflows/post-cambios.md` pasan a ser un enlace al fichero de instrucciones para agentes que no lo lean automáticamente.

## 5. Hábitos que ahorran tokens en este repo

1. Empezar por el fichero de instrucciones → Mapa rápido; no listar `src/` de nuevo.
2. Buscar con `grep -n` y leer rangos, no ficheros completos > 300 líneas.
3. Ejecutar tests con `--no-cov -q -x` y sólo el fichero afectado; la suite completa al final.
4. Usar `tests/audit` como oráculo de regresión antes de tocar hilos, estilos o build.
5. Para el crash de Windows, seguir el protocolo de `auditoria/06` en vez de reexplorar.
6. Documentar en CHANGELOG, no en nuevos `.md` sueltos (regla ya existente).
