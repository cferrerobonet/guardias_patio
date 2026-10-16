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

Descargar los de un run sin pasar por el navegador:

```bash
gh run download <id-del-run> --dir /tmp/instaladores
```

Compilar en local está prohibido (`.claude/rules/empaquetado.md`): ni `make dmg`, que además publica el release por su cuenta, ni `make app` ni `pyinstaller`. Los fallos de la compilación se corrigen y se mueve la etiqueta.

## Verificación

1. Montar el DMG, arrastrar a Aplicaciones, abrir desde Finder (primera vez: clic derecho → Abrir, por firma ad-hoc).
2. Flujo mínimo: login, curso, zonas, profesores, cuotas, generar (CP-SAT), exportar PDF, cerrar con sync.
3. Logs en `~/Library/Application Support/GuardiasDePatio/logs`.


## Errores conocidos

| Síntoma | Causa | Solución |
| --- | --- | --- |
| App abre y cierra | protocolo de cierre en `build-windows-exe` | abrir el binario del `.app` desde Terminal para ver la traza |
