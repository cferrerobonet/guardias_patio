---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-06
estado: activo
prioridad: 3-media
tipo: referencia
---

# Limpieza del repositorio y del equipo

> [!NOTE] Criterio
> Se borra lo que **no puede contener datos de nadie** y lo que **nadie referencia**. Antes de cada borrado se comprobó con `git ls-files`, `grep` de referencias y, en los scripts, que sus imports resolvieran. Lo que tenía datos reales se ha **movido**, no destruido.

## 1. Hecho el 2026-09-06

### Fuera del repositorio (no versionado): 281 MB liberados

| Qué | Por qué se podía |
| --- | --- |
| `dist/` (92 MB), `Output/` (89 MB) | Artefactos de compilación; se regeneran con `make dmg` o el flujo de GitHub |
| `.mypy_cache/` (97 MB), `.hypothesis/`, `.benchmarks/` (vacía) | Cachés |
| `guardias_patio.db` en la raíz | Base de desarrollo con **0 profesores**; la real está en `data/users/<hash>/` |
| 6 × `.DS_Store` | Basura de Finder |
| `logs/app_*.log` de más de 7 días | Ninguno cumplía; quedan 74 ficheros de esta semana (15 MB) con rotación de 10 MB × 5 |

### Movido fuera del repositorio

| Qué | A dónde | Por qué |
| --- | --- | --- |
| `docs/examples/datos ejemplo/` (2 PDF y 4 Excel con listados reales del claustro, más un volcado local con 67 correos) | `../DATOS DE EJEMPLO (fuera del repositorio)/`, en la bóveda | Estaban en un repositorio **público** desde 2025-11-15 (SEC-004). Los datos de ejemplo para pruebas se inventan |

### Retirado del repositorio (versionado, en este commit)

| Qué | Por qué |
| --- | --- |
| `Guardias de Patio.spec` | Duplicado de abril; el build de macOS lo usaba mientras los cambios se hacían en `GuardiasDePatio.spec` (BLD-008). `Makefile`, `build_dmg.sh` y la skill apuntan ya al único |
| `scripts/regenerar_guardias.py`, `scripts/regenerar_guardias_v3.py`, `scripts/verificar_sistema_hibrido.py` | Importan `services.asignador_guardias`, `…_v3_simple` y `…_ilp`, que no existen desde 2025-12 |
| `.agents/rules/reglas.md`, `.agents/workflows/post-cambios.md` | Sólo decían «lee el fichero de instrucciones» |
| `.claude/agents.md` | Una regla sobre un fallo preexistente que ya no existe; lo útil pasa al fichero de instrucciones |

### Fuera del proyecto

| Qué | Dónde |
| --- | --- |
| Hooks globales de `impeccable` (`PostToolUse` y `Stop`) | `~/.claude/settings.local.json`, con copia `.antes-de-quitar-impeccable` |

## 2. Se conserva a propósito

| Qué | Por qué |
| --- | --- |
| `scripts/build/` (`build_dmg.sh`, `create_icon.sh`) | Los usa el `Makefile` (`make dmg`, `make icon`). La skill decía que se eliminaron en 5.50.0: era falso |
| `scripts/add_activo_column.py`, `migrate_multi_curso.py`, `migrar_recreos_*.py` | Migraciones de una vez, ya aplicadas, pero un equipo con una base muy antigua podría necesitarlas. Candidatas a borrar cuando ningún equipo tenga bases anteriores a 5.0 |
| `scripts/test_v3_quick.sh` | Importa `services.calculador_guardias`, que existe |
| `.agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md` | Referencia genérica; no se carga en sesión |
| `imagenes/` (11 MB, 56 ficheros) | `logo.png` y `Jefatura_FpBach.png` pesan 3,5 MB cada uno: convendría reducirlos a 512 px, pero es cosmético |
| `logs/` | Los escribe la app en desarrollo; rotan solos |
| `.vscode/` | Configuraciones de ejecución y tareas compartidas |

## 3. Pendiente y sólo puede decidirlo CarlosFB

| Qué | Por qué importa |
| --- | --- |
| **Reescribir el historial de git** (`git filter-repo`) para sacar la contraseña SFTP (3 commits en claro, 1 en base64) y los listados del claustro (desde `eb51456`) | El repositorio es público. Reescribir limpia GitHub; no limpia clones ni cachés ajenos. **Lo que cierra la puerta es rotar la contraseña**, que sigue pendiente |
| **Hacer el repositorio privado** | Elimina la exposición futura sin coste: la compilación en GitHub sigue funcionando (con minutos de pago, ~10 min por release) |
| Borrar en el servidor `guardias_patio_data.json.1/.2/.3` | Verificado el 2026-09-06: **no existen**; nada que hacer |
| Reducir `logo.png` y `Jefatura_FpBach.png` | 7 MB del repositorio para dos imágenes que se muestran a 100 px |
| Vaciar `docs/` de PDF (`Configuración inicial - Guardias de Patio.pdf`, no versionado) | Sin datos personales; es sólo orden |

## 4. Cómo repetir la limpieza del equipo (cualquier persona)

macOS:

```bash
cd "<carpeta del repositorio>"
rm -rf dist Output .mypy_cache .hypothesis .benchmarks
find . -name .DS_Store -not -path "./.git/*" -delete
find logs -name "app_*.log" -mtime +7 -delete
```

Windows (PowerShell):

```powershell
Remove-Item -Recurse -Force dist, Output, .mypy_cache, .hypothesis, .benchmarks -ErrorAction SilentlyContinue
Get-ChildItem logs -Filter "app_*.log" | Where-Object LastWriteTime -lt (Get-Date).AddDays(-7) | Remove-Item
```

Los rastros de versiones anteriores (`.env` con contraseñas, carpetas heredadas, volcados con credenciales) **los limpia la propia aplicación al arrancar** desde v5.96.0; no hace falta hacer nada a mano.
