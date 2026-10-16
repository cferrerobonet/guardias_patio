---
name: build-windows-exe
description: Compilar Guardias de Patio para Windows (instalador Inno Setup y portable) en GitHub y diagnosticar un exe que no arranca. Usar cuando se pida generar el exe, el instalador de Windows o depurar un cierre en Windows.
---

# Build Windows: instalador + portable

## Compilar en GitHub

El flujo `.github/workflows/compilar.yml` compila en un Windows real de GitHub.
El repositorio es público, así que no consume minutos de pago.

```bash
gh workflow run compilar.yml -f publicar=false   # solo probar
git tag vX.Y.Z && git push --tags                # compilar y publicar
```

> [!WARNING] Publicar avisa a todo el mundo
> Adjuntar al release hace que a los usuarios les aparezca el aviso de nueva
> versión. Para solo probar, usar la primera forma.

Compilar en local está prohibido (`.claude/rules/empaquetado.md`): ni `scripts/build_windows.ps1`, ni `pyinstaller`, ni `make`. Los fallos de la compilación se corrigen y se mueve la etiqueta.

## Dónde acaban los instaladores

| Cómo se compila | Dónde queda | Cuánto dura |
| --- | --- | --- |
| Flujo de GitHub, a mano | Artefacto del run, pestaña Actions | 90 días |
| Flujo de GitHub, al publicar etiqueta | Adjunto al release, junto al DMG | Permanente |

Descargar los de un run sin pasar por el navegador:

```bash
gh run download <id-del-run> --dir /tmp/instaladores
```

## Saber si el exe arranca sin tener Windows

Subir una rama `diag/…` (o lanzar «Arranque en Windows» a mano). `.github/workflows/arranque-windows.yml` compila, arranca
el exe con `GUARDIAS_PRUEBA_DE_ARRANQUE=ventana` (acepta los avisos solo y cierra al ver
la ventana principal), instala con el instalador y repite, y al final contra un SFTP falso
local. Los registros quedan como artefacto: `gh run download <id>`. `compilar.yml` hace
la misma prueba antes de publicar y no adjunta nada si falla (BLD-020).

`scripts/build_windows.ps1` (lo usa el flujo) debe guardarse en UTF-8 **con** marca de orden de bytes: Windows PowerShell 5.1 lee los ficheros sin marca como ANSI, la «Ó» de «COMPILACIÓN» se parte en una comilla tipográfica y el análisis falla con «missing the terminator». Un test lo vigila.

> [!WARNING] Nunca pasar `src\main.py` ni argumentos `--add-data`/`--collect-all` a PyInstaller
> Con argumentos sueltos PyInstaller **genera su propio spec encima** de `GuardiasDePatio.spec` y el exe sale sin lo que se arregla ahí (hoja de estilos, `upx=False`, migraciones sin acentos). Así se compilaron las versiones 6.1.1 a 6.3.0 en GitHub: el log decía «wrote …GuardiasDePatio.spec». Un test lo vigila.

## Si al hacer doble clic no aparece nada

Primero mirar si existe un `app_*.log` nuevo en `%APPDATA%\GuardiasDePatio\logs`. Se crea antes de cargar Qt, así que separa dos casos que se ven igual:

| Hay `app_*.log` nuevo | Qué significa | Qué hacer |
| --- | --- | --- |
| No | El proceso no llega a ejecutar Python: bloqueo por directiva (AppLocker/SRP contra `%LOCALAPPDATA%\Programs` o la carpeta del portable), antivirus, o SmartScreen sin aceptar | Visor de eventos → Windows → Aplicación (evento 1000 o 8004 AppLocker); probar el portable en otra carpeta; «Más información → Ejecutar de todas formas» |
| Sí, acaba en «Conectando con el servidor…» | El puerto 22 está cortado; hasta v6.3.0 no se pintaba nada durante los ~35 s de espera | Esperar el aviso «Sin sincronización» o revisar el cortafuegos del centro |
| Sí, con traza | Fallo de Python o nativo | Pedir `%APPDATA%\GuardiasDePatio\logs\faulthandler.log` (pila de todos los hilos) |

Para un cierre: pedir las últimas 200 líneas de `%APPDATA%\GuardiasDePatio\logs\app_*.log`, `faulthandler.log` y el evento 1000 del Visor de eventos (módulo y código de excepción). Protocolo completo (§5), retirado del árbol: `git show c0f1f0a:auditoria/06_CRASH_WINDOWS_GENERACION.md`.

## Verificación mínima del artefacto

1. Instalar en una máquina o cuenta limpia (y probar también el portable).
2. Login, crear curso, 2 zonas, 5 profesores, calcular cuotas y generar.
3. Exportar un PDF y cerrar con sincronización.
4. Revisar `%APPDATA%\GuardiasDePatio\logs` sin `ERROR`.

## Errores conocidos

| Síntoma | Causa | Solución |
| --- | --- | --- |
| `ModuleNotFoundError: ortools...` al arrancar | faltó `--collect-all ortools` | compilar siempre `GuardiasDePatio.spec` |
| Ventana sin controles nativos | `showFullScreen` | ya corregido (5.42.1) |
| El exe cierra sin mensaje | fallo nativo | `faulthandler.log` y protocolo de cierre (arriba) |
| Se cierra a los 2 s, con la pantalla de arranque; evento 1000 en `PyQt6\Qt6\bin\MSVCP140.dll`, `0xc0000005` | el runtime de C++ 14.26 de PyQt6 con OR-Tools compilado para 14.40+ | el spec lo sustituye por el más reciente (`scripts/build/runtime_msvc.py`, BLD-020); mirar las líneas `[runtime_msvc]` del log de PyInstaller en el run |
| Doble clic y nada, sin `app_*.log` nuevo | el proceso no arranca: directiva, antivirus o SmartScreen | ver «Si al hacer doble clic no aparece nada» |
| El portable avisa «Windows protegió su PC» | marca de la web en el zip descargado; el exe no va firmado | «Más información → Ejecutar de todas formas», o desbloquear el zip antes de descomprimir |
| La app sale sin tema, o el log del run dice «wrote …GuardiasDePatio.spec» | PyInstaller recibió argumentos sueltos y regeneró el spec | compilar siempre `GuardiasDePatio.spec` (BLD-016) |
