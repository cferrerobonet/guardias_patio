---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-06
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Recursos de IA: qué hay instalado, qué sirve aquí y qué usar en cada momento

> [!NOTE] Conclusión en una frase
> De las 20 skills globales instaladas, **17 son para desarrollo web** (React, CSS, animaciones, landing pages) y esta es una aplicación de escritorio en PyQt6. La sensación de «no las uso» es correcta: no podían disparar nunca. Lo que sí aporta aquí son las 4 skills del proyecto, tres skills genéricas de arquitectura y revisión, y las herramientas de análisis que faltaban y que se han instalado hoy.

## 1. Inventario y veredicto de las skills globales (`~/.claude/skills/`)

| Skill | Para qué está hecha | ¿Aplica a PyQt6? | Veredicto |
| --- | --- | --- | --- |
| `impeccable` (148 ficheros, 3,4 MB) | Diseñar y auditar interfaces **web**: 22 comandos (`critique`, `audit`, `polish`, `adapt`…). Sus «native» son iOS/Android. Su detector (`detect.mjs`) sólo mira `.js/.tsx/.css/.html/.vue/.svelte/.astro` | **No** al escritorio. **Sí, acotado**, a las páginas HTML que publica `services/publicador_web.py` y a la documentación web de la API | Conservar. Usar `critique` y `adapt` sobre `publicador_web._pagina()` cuando se toque la página del profesorado. **Sus hooks globales se han retirado** (ver §3) |
| `taste-skill` (design-taste-frontend) | Landing pages, portfolios, «anti-slop»; dicta stack React/Tailwind, iconos, emojis, sombras | No: todo el documento es web; no menciona Qt | **Desinstalar**. Lo único transferible (jerarquía tipográfica, calibración de color) ya está en [[05_CONTRATO_SISTEMA_DE_DISENO]] |
| `emil-design-eng` | Filosofía de Emil Kowalski: animación, muelles, «perceived performance», botones que responden | No como skill (todo es CSS/JS). Dos secciones son ideas válidas para cualquier UI: «Perceived performance» y «Buttons must feel responsive» | **Conservar como lectura**, no como skill que dispare. Consultarla al tocar barras de progreso o feedback de botones. No instalar hooks |
| `animate`, `animation-vocabulary`, `find-animation-opportunities`, `improve-animations`, `review-animations` | Motion web | No. Qt tiene `QPropertyAnimation`, pero esta app no necesita animación y el terminal retro es decisión de producto | **Desinstalar** las cinco |
| `apple-design` | Gestos, muelles, materiales translúcidos, tipografía óptica, para web | Parcial: «feedback, spatial consistency, restraint» son principios | Desinstalar; los principios ya están en el contrato de diseño |
| `prototype`, `pick-ui-library` | Variantes de UI web tras un selector; elegir librerías npm | No | **Desinstalar** |
| `audit` | Checks técnicos a11y/perf/theming para web con puntuación P0–P3 | No directamente; el formato de informe es el que ya usa [[30_REGISTRO_HALLAZGOS]] | Desinstalar |
| `auditing-wcag`, `reviewing-a11y`, `planning-wcag-audit`, `planning-a11y-improvement` (~400 KB) | Auditoría WCAG 2.2 formal para **web** con guías WAIC | Parcial: los criterios (contraste, foco, nombre accesible, orden de tabulación) valen para escritorio; el tooling (navegador, axe) no | Conservar **una**: `reviewing-a11y`, para la sesión humana de CHK-P-03. Desinstalar las otras tres |
| `architecture-patterns` | Clean/Hexagonal/DDD, ciclos de dependencia | **Sí**: la app es Clean Architecture híbrida con deuda en capas (COD-003) | Conservar. Usar al revisar `application/`↔`services/`↔`presentation/` |
| `api-design-principles` | Diseño REST | **Sí**, para `src/api/` | Conservar. Usar al tocar routers |
| `code-review-excellence` | Cómo revisar un cambio | **Sí**, genérica | Conservar. Usar al cerrar un lote antes del commit |

Resumen: **conservar 6** (`impeccable`, `emil-design-eng`, `reviewing-a11y`, `architecture-patterns`, `api-design-principles`, `code-review-excellence`), **desinstalar 14**. Desinstalar es borrar la carpeta en `~/.claude/skills/`; no afecta a nada más.

## 2. Skills del proyecto (`.claude/skills/`)

| Skill | Estado | Cuándo invocarla |
| --- | --- | --- |
| `/tests-locales` | Correcta | Antes de cualquier commit; explica intérprete, barreras y marcadores |
| `/build-windows-exe` | Correcta (actualizada hoy: spec único) | Al compilar Windows o perseguir un cierre |
| `/build-macos-dmg` | Corregida hoy: decía que el spec estaba ignorado y que `make clean` lo borraba; ninguna de las dos cosas es cierta ya | Al compilar macOS o publicar |
| `/auditoria-desktop` | Ampliada hoy con los gates de las dimensiones H–O | Al cerrar un lote o reauditar |

Faltaba, y se propone crear en el siguiente lote: `/seguridad-y-privacidad` (los 14 + 8 checks de H e I como un solo comando) y `/limpieza-del-entorno` (lo de [[23_LIMPIEZA]] §3).

## 3. Hooks, agentes y reglas

| Recurso | Qué hacía | Decisión |
| --- | --- | --- |
| Hooks globales de `impeccable` en `~/.claude/settings.local.json` (`PostToolUse` tras cada edición, `Stop` al terminar) | Ejecutaban `node hook.mjs` con 5 y 30 s de tiempo máximo, en **cada** edición de **cualquier** proyecto. Para ficheros `.py`/`.qss` no producen nada: puro coste | **Retirados hoy**, con copia en `~/.claude/settings.local.json.antes-de-quitar-impeccable` |
| `.agents/rules/reglas.md` y `.agents/workflows/post-cambios.md` | Sólo enlazaban al fichero de instrucciones | **Eliminados hoy** |
| `.agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md` (41 KB) | Agente genérico de auditoría en seis olas | Conservar como referencia; **no cargarlo**: [[21_PLAN_DE_AUDITORIA_AMPLIADO]] es su instancia corta para este proyecto |
| `.claude/agents.md` | Una regla sobre un fallo preexistente que ya no existe | **Fusionado** en el fichero de instrucciones y eliminado |
| Agentes globales (`~/.claude/agents/`) | Ninguno | — |
| Plugins | Ninguno instalado | — |

## 4. MCP y settings globales

- `~/.claude/settings.json` define un único MCP de Obsidian que apunta a la bóveda **TERRENO SIMERIA**, con la clave de la API en texto plano y `NODE_TLS_REJECT_UNAUTHORIZED=0`. El fichero de instrucciones raíz de las bóvedas dice que cada bóveda tiene su `.mcp.json`; **no existe ninguno** en la jerarquía. Consecuencia: desde este proyecto el asistente sólo puede escribir en la bóveda equivocada.
- Propuesta (decisión de CarlosFB, no se ha tocado): un `.mcp.json` en `02 EPLA/` apuntando a esa bóveda, con la clave leída de una variable de entorno (`${OBSIDIAN_API_KEY}`) y sin desactivar TLS; retirar el servidor del fichero global.
- `.claude/settings.local.json` del proyecto está **versionado**. Sólo contiene la lista de permisos, que es útil compartir; el nombre `local` sugiere lo contrario. Renombrar a `settings.json` y añadir `settings.local.json` al `.gitignore`.

## 5. Herramientas de análisis: instaladas hoy y recomendadas

| Herramienta | Estado | Para qué | Comando |
| --- | --- | --- | --- |
| `pip-audit` | **Instalada** | CVE en dependencias (J-01) | `$PY -m pip_audit --progress-spinner off` |
| `vulture` | **Instalada** | Código muerto (E) | `$PY -m vulture src --min-confidence 80` |
| `radon` | **Instalada** | Complejidad y mantenibilidad (E) | `$PY -m radon cc src -s -n C` · `$PY -m radon mi src -s` |
| `bandit` | Ya estaba | Seguridad estática (H-06) | `$PY -m bandit -r src -q -ll` |
| `mutmut`, `hypothesis` | Ya estaban | Mutación y propiedades | `make mutation` |
| `gitleaks` | **Recomendada** (`brew install gitleaks`) | Secretos en historial (H-02) sin tener que conocer el valor | `gitleaks detect --source . --log-opts="--all"` |
| `pre-commit` | **Recomendada** | ruff + bandit + `detect-private-key` + test de datos reales antes de cada commit | `.pre-commit-config.yaml` |
| `pip-licenses` | Recomendada | Licencias (J-04) | `$PY -m piplicenses --summary` |
| `import-linter` | Recomendada | Contratos de capas (COD-003, E-04) | `.importlinter` con `presentation` sin importar `sqlalchemy` |
| `semgrep` | Opcional | Reglas propias (p. ej. `open()` sin encoding) | — |

## 6. Recursos externos que sí merecen instalarse para este stack

| Recurso | Por qué aquí | Cómo |
| --- | --- | --- |
| `obra/superpowers` → `systematic-debugging`, `verification-before-completion`, `test-driven-development` | Metodología, no stack. `verification-before-completion` habría evitado hoy tres tests que tocaron cosas reales | `npx skills add obra/superpowers` y quedarse sólo con esas tres |
| `anthropics/skills` → `pdf`, `xlsx` | Verificar los PDF exportados y las importaciones Excel con herramientas, no a ojo | `npx skills add https://github.com/anthropics/skills --skill pdf --skill xlsx` |
| Una skill propia `pyqt6-testing` | No existe en los catálogos: `pytest-qt`, `qtbot.waitSignal`, afinidad de hilos, `QT_QPA_PLATFORM=offscreen`, las cuatro barreras | Escribirla a partir de `/tests-locales` y de `tests/audit/test_crash_windows_regresion.py` |

## 7. Cuándo usar qué (para pegar en el fichero de instrucciones)

| Situación | Recurso |
| --- | --- |
| Tocar cualquier vista PyQt | Contrato de diseño [[05_CONTRATO_SISTEMA_DE_DISENO]] + ratchets. **No** `impeccable` |
| Tocar `publicador_web._pagina()` o la documentación de la API | `impeccable critique` / `adapt` |
| Barras de progreso, feedback de botones | Leer `emil-design-eng` §«Perceived performance» |
| Sesión humana con lector de pantalla | `reviewing-a11y` |
| Mover código entre capas | `architecture-patterns` + `import-linter` |
| Tocar `src/api/` | `api-design-principles` |
| Antes del commit de un lote | `code-review-excellence` + `/tests-locales` |
| Cerrar un lote de auditoría | `/auditoria-desktop` |
| Cualquier test que toque red, llavero, `.env` o servidor | **Barrera primero** en `tests/conftest.py` |
