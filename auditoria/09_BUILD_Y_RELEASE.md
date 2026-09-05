---
tags:
  - gestion-centro
  - auditoria
  - build
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Build, release y actualización (exe Windows · dmg macOS)

## 1. Inventario de artefactos de build

| Fichero | Plataforma | Estado | Observación |
| --- | --- | --- | --- |
| `Makefile` (`app`, `dmg`, `release`, `windows`, `clean`) | macOS | Parcial | `windows` apunta a `build_windows.bat/ps1` en raíz y a `BUILD_WINDOWS.md`, que no existen; `clean` borra `*.spec` |
| `Guardias de Patio.spec` | macOS | **No versionado** (`*.spec` en `.gitignore`) | `make app/dmg` lo requieren |
| `GuardiasDePatio.spec` | Windows | **No versionado** | Incluye `collect_all('ortools')`; es la referencia buena para Windows |
| `scripts/build_windows.ps1` | Windows | **Canónico** | Lee la versión de `settings.py`, usa `--collect-all ortools`, `--windowed`, genera exe + instalador Inno con `/DMyAppVersion` |
| `scripts/build/build_windows.ps1` y `.bat` | Windows | Obsoletos | Referencian `guardias_patio_windows.spec` (inexistente) y versión fija 2.7.0 |
| `scripts/build/build_dmg.sh` | macOS | Canónico | Copia fuera de iCloud, `xattr -cr`, firma ad-hoc, `hdiutil`; publica release |
| `scripts/build/create_dmg.sh`, `build_simple.sh` | macOS | Obsoletos | Versión fija 5.31.11; sin spec |
| `installer_windows.iss` | Windows | Correcto | `PrivilegesRequired=admin`, sin `CloseApplications` |
| `Output/GuardiasDePatio-5.42.1-Windows-Setup.exe` | Windows | Artefacto local | Generado 2026-05-19 |
| `.github/workflows/compilar.yml` | CI | ✅ **v5.50.0** | Pruebas en Linux, instalador de Windows, DMG de macOS y publicación de ambos al etiquetar |

## 2. Hallazgos (BLD)

| ID | Sev. | Hallazgo | Evidencia | Recomendación |
| --- | --- | --- | --- | --- |
| BLD-001 | P1 | Los `.spec` están ignorados por git y `make clean` los borra: el build de macOS no es reproducible desde un clon y un `make clean` destruye la entrada del build | `.gitignore` (`*.spec`), `Makefile:57-60` | Versionar `build/macos.spec` y `build/windows.spec` en `scripts/build/`; `make clean` sólo borra `build/` y `dist/` |
| BLD-002 | P1 | Tres scripts de Windows divergentes; el `Makefile` y el README documentan los obsoletos | `scripts/build/build_windows.ps1:12,44`, `scripts/build/build_windows.bat:156`, `Makefile:82-97` | Dejar sólo `scripts/build_windows.ps1`; borrar los otros dos; `make windows` imprime la invocación real |
| BLD-003 | P2 | Cuatro versiones distintas: settings 5.42.3, `pyproject.toml` 5.9.8, README 3.2.1, `create_dmg.sh` 5.31.11 | ficheros citados | Única fuente `settings.app_version`; test `tests/audit/test_calidad_estatica.py::test_version_unica` (pyproject sincronizado o dinámico) |
| BLD-004 | P2 | Sin CI ni firma: no hay verificación automática de tests/lint/build; macOS sólo firma ad-hoc (Gatekeeper avisa), Windows sin firma (SmartScreen) | ausencia de `.github/` | Workflow con matriz `macos-latest`/`windows-latest`: tests → build → artefactos → release al etiquetar; notarización con Apple ID cuando haya cuenta de desarrollador; firma Windows con certificado o al menos hash publicado |
| BLD-005 | P2 | El actualizador sólo busca `.dmg`; Windows nunca recibe actualizaciones; `make release` sólo sube el DMG | `src/utils/update_checker.py:26-30`, `Makefile:39-51` | Buscar asset por plataforma (`.dmg`/`-Setup.exe`); subir ambos al release |
| BLD-006 | P3 | Instalador exige admin e instala en Program Files; no cierra la app en ejecución al actualizar | `installer_windows.iss:13-18` | `PrivilegesRequired=lowest`, `DefaultDirName={localappdata}\Programs\Guardias de Patio`, `CloseApplications=yes` |
| BLD-007 | ~~P2~~ | ~~No hay variante de build con consola~~ ✅ **RESUELTO v5.44.0** | `scripts/build_windows.ps1` | `-Diagnostico` compila con `--console`, activa `PYTHONFAULTHANDLER`, nombra el artefacto `GuardiasDePatio-debug` y omite el instalador |

## 3. Skills creados

| Skill | Ruta | Qué hace |
| --- | --- | --- |
| `build-windows-exe` | `.claude/skills/build-windows-exe/SKILL.md` | Procedimiento completo en Windows: venv, deps, PyInstaller con `collect-all ortools`, Inno Setup, verificación de arranque, publicación del asset; variante `-Debug` |
| `build-macos-dmg` | `.claude/skills/build-macos-dmg/SKILL.md` | Icono, `.app` con spec, firma fuera de iCloud, DMG, verificación y release |
| `tests-locales` | `.claude/skills/tests-locales/SKILL.md` | Intérprete correcto, deps, comandos rápidos, BD en fichero, Playwright |
| `auditoria-desktop` | `.claude/skills/auditoria-desktop/SKILL.md` | Cómo re-ejecutar los gates de esta auditoría y actualizar el registro |

## 4. Pipeline objetivo

```
tag vX.Y.Z ──► CI
   ├─ lint (ruff) + mypy(domain, application)
   ├─ tests (ubuntu, offscreen) + tests/audit
   ├─ build macOS  → GuardiasPatio_vX.Y.Z_macOS.dmg   (firmado, notarizado)
   ├─ build Windows → GuardiasDePatio-X.Y.Z-Windows-Setup.exe (firmado)
   ├─ smoke: cada artefacto arranca con --version y sale 0
   └─ release GitHub con ambos assets + notas desde CHANGELOG
```

## 5. Checklist de release manual (mientras no haya CI)

- [ ] `app_version` actualizado y CHANGELOG con la fecha.
- [ ] `pytest tests/ --no-cov -q` verde (incluido `tests/audit`).
- [ ] macOS: `make dmg`; abrir el DMG en otra cuenta de usuario; arrancar; generar guardias.
- [ ] Windows: `powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1`; instalar en máquina limpia; generar guardias ×3; revisar `%APPDATA%\GuardiasDePatio\logs`.
- [ ] Subir ambos assets al release del tag.
- [ ] Comprobar que el banner de actualización aparece en la versión anterior (macOS y Windows).
