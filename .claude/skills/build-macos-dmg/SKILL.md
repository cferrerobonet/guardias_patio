---
name: build-macos-dmg
description: Compilar Guardias de Patio para macOS (.app firmado ad-hoc y DMG) y publicar la release en GitHub. Usar cuando se pida generar el DMG, la app de macOS o publicar una versión.
---

# Build macOS: .app + DMG + release

## Vía rápida: compilar en GitHub

```bash
gh workflow run compilar.yml -f publicar=false   # solo probar
git tag vX.Y.Z && git push --tags                # compilar y publicar
```

Compila a la vez el DMG de macOS y el instalador de Windows. El paso de macOS
usa `SKIP_RELEASE=1` para no publicar por su cuenta: de adjuntar los dos
instaladores se encarga el paso final del flujo.

## Dónde acaban los instaladores

| Cómo se compila | Dónde queda | Cuánto dura |
| --- | --- | --- |
| Flujo de GitHub, a mano | Artefacto del run, pestaña Actions | 90 días |
| Flujo de GitHub, al publicar etiqueta | Adjunto al release, junto al otro instalador | Permanente |
| En local | `dist/` y `Output/` del proyecto | Hasta `make clean`; no se versionan |

Descargar los de un run sin pasar por el navegador:

```bash
gh run download <id-del-run> --dir /tmp/instaladores
```

El resto describe la compilación en local.


Scripts canónicos: `Makefile` (`make icon`, `make app`, `make dmg`, `make release`) y `scripts/build/build_dmg.sh`. Ignorar `scripts/build/create_dmg.sh` y `build_simple.sh` (obsoletos, versión fija).

## Requisitos

- macOS 12+, Xcode Command Line Tools (`xcode-select --install`).
- Python 3.11 de Homebrew: `/opt/homebrew/bin/python3.11` con `pip install -r requirements.txt pyinstaller`.
- `gh` autenticado para publicar.
- El spec `Guardias de Patio.spec` en la raíz. Está ignorado por git: si falta, regenerarlo con `make app` no funciona; copiar el bloque de `auditoria/09_BUILD_Y_RELEASE.md` o restaurarlo desde una copia local. **No ejecutar `make clean` sin copia del spec** (lo borra).

## Pasos

```bash
cd "<raíz del repo>"
export PATH="/opt/homebrew/bin:$PATH"
python3.11 -m pytest tests/audit -q --no-cov          # comprobación rápida
make dmg                                              # icono + app + firma + DMG + release
# Sólo app:        make app
# Sólo publicar:   make release  (usa el DMG existente)
```

`build_dmg.sh` copia la app a un directorio temporal fuera de iCloud, elimina atributos extendidos (`xattr -cr`), firma ad-hoc con `codesign --deep`, verifica con `--strict` y crea `GuardiasPatio_v<versión>_macOS.dmg`.

## Verificación

1. Montar el DMG, arrastrar a Aplicaciones, abrir desde Finder (primera vez: clic derecho → Abrir, por firma ad-hoc).
2. Flujo mínimo: login, curso, zonas, profesores, cuotas, generar (CP-SAT), exportar PDF, cerrar con sync.
3. Logs en `~/Library/Application Support/GuardiasDePatio/logs`.

## Notarización (cuando exista cuenta Apple Developer)

```bash
codesign --deep --force --options runtime --sign "Developer ID Application: <nombre>" "dist/Guardias de Patio.app"
xcrun notarytool submit GuardiasPatio_v<versión>_macOS.dmg --keychain-profile "AC_PASSWORD" --wait
xcrun stapler staple GuardiasPatio_v<versión>_macOS.dmg
```

## Errores conocidos

| Síntoma | Causa | Solución |
| --- | --- | --- |
| `codesign` falla con "resource fork, Finder information" | atributos de iCloud | `build_dmg.sh` ya copia fuera de iCloud |
| PyInstaller se cuelga | ruta en iCloud/OneDrive con ficheros bloqueados | clonar en `~/dev` y compilar allí |
| App abre y cierra | ver `auditoria/06` | ejecutar `dist/Guardias de Patio.app/Contents/MacOS/Guardias\ de\ Patio` desde Terminal para ver la traza |
