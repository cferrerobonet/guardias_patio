---
tags:
  - gestion-centro
  - auditoria
  - herramientas
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 3-media
tipo: referencia
---

# Skills recomendados (GitHub) y skills del proyecto

## 1. Repositorios de skills con más estrellas (consultados 2026-09-04)

| Repositorio | Estrellas aprox. | Para qué sirve aquí | Cómo usar |
| --- | --- | --- | --- |
| [obra/superpowers](https://github.com/obra/superpowers) | ~170 k | Metodología: `test-driven-development`, `systematic-debugging` (obliga a entender antes de corregir; ideal para CRW-001), `verification-before-completion`, `brainstorming` | Plugin del marketplace o `npx skills add obra/superpowers` |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | ~124 k | Sistema de diseño, paletas, tipografía, `/review` de anti-patrones UX; útil para validar el contrato de [[05_CONTRATO_SISTEMA_DE_DISENO]] (orientado a web, aplicar criterios, no código) | `npx skills add nextlevelbuilder/ui-ux-pro-max-skill` |
| [anthropics/skills](https://github.com/anthropics/skills) | oficial | `webapp-testing` (Playwright con gestión de servidor), `pdf`, `xlsx`, `docx`: útil para verificar PDFs exportados e importaciones Excel | `npx skills add https://github.com/anthropics/skills --skill webapp-testing` |
| [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) | ~42 k | Catálogo de 1.800+ skills instalables: `python-testing`, `security-review`, `performance-profiling`, `release-management` | CLI `npx antigravity-awesome-skills` |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | ~13 k | Índice curado por proveedores oficiales; buscar `pytest`, `playwright`, `pyinstaller`, `qt` | Navegar e instalar por skill |
| [pytest-dev/pytest-qt](https://github.com/pytest-dev/pytest-qt) | biblioteca | No es skill, pero es la base de todos los tests de UI: `qtbot.waitSignal`, `waitUntil`, captura de `qWarning` (permite detectar "cannot be called from a different thread") | Ya instalado |
| [pyinstaller/pyinstaller](https://github.com/pyinstaller/pyinstaller) | biblioteca | Hooks para OR-Tools/PyQt6; `--debug=imports` para diagnosticar módulos faltantes | Ya instalado |

Ninguno de los catálogos contiene un skill específico para PyQt6 + PyInstaller + OR-Tools; por eso se han creado skills propios del proyecto (sección 2). Los skills externos aportan método (TDD, depuración sistemática) y criterios de diseño, no procedimientos de este stack.

> [!WARNING] Instalación
> Instalar skills externos sólo en el ámbito de usuario (directorio de skills del usuario o marketplace), no en el repositorio, para no incrementar el contexto cargado en cada sesión (ver [[11_EFICIENCIA_AGENTES_Y_TOKENS]]).

## 2. Skills del proyecto (creados en esta entrega)

| Skill | Invocación | Contenido |
| --- | --- | --- |
| `build-windows-exe` | `/build-windows-exe` | Requisitos, venv Windows, PyInstaller con OR-Tools, Inno Setup, variante debug, verificación, publicación |
| `build-macos-dmg` | `/build-macos-dmg` | Icono, spec versionado, firma fuera de iCloud, DMG, verificación, release |
| `tests-locales` | `/tests-locales` | Intérprete, dependencias, comandos, BD en fichero, Playwright, cómo interpretar xfail |
| `auditoria-desktop` | `/auditoria-desktop` | Gates reproducibles, cómo actualizar registro y plan, criterios de cierre |

Los skills viven en `.claude/skills/<nombre>/SKILL.md`, se cargan bajo demanda y no consumen tokens hasta invocarse.

## 3. Herramientas de análisis recomendadas (no skills)

| Herramienta | Uso | Estado |
| --- | --- | --- |
| `ruff` | lint/format | instalado; 355 avisos |
| `mypy` | tipos | instalado |
| `bandit` | seguridad estática | instalado; 3 medios |
| `pip-audit` | CVE en dependencias | **instalar** |
| `vulture` | código muerto | **instalar** |
| `import-linter` | contratos de capas | **instalar** |
| `pytest-timeout` | evita suites colgadas (detectado un cuelgue en `tests/test_config_widgets_extra.py`) | **instalar** |
| `pytest-xdist` | paralelo | **instalar** |
| `hypothesis` | propiedades en dominio | **instalar** (tests existentes lo requieren) |
| `playwright` + `pytest-playwright` | E2E web | **instalar** |
