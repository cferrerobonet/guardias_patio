---
name: build-windows-exe
description: Compilar Guardias de Patio para Windows (exe + instalador Inno Setup) desde un PC Windows, incluida la variante de diagnóstico con consola. Usar cuando se pida generar el exe, el instalador de Windows o depurar un cierre en Windows.
---

# Build Windows: exe + instalador

## Lo primero: no hace falta un PC con Windows

El flujo `.github/workflows/compilar.yml` compila en un Windows real de GitHub.
El repositorio es público, así que no consume minutos de pago.

```bash
# Compilar sin publicar nada, para probar los instaladores
gh workflow run compilar.yml -f publicar=false

# Compilar y adjuntar los dos instaladores al release
git tag vX.Y.Z && git push --tags
```

> [!WARNING] Publicar avisa a todo el mundo
> Adjuntar al release hace que a los usuarios les aparezca el aviso de nueva
> versión. Para solo probar, usar la primera forma.

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

El resto de este documento describe la compilación **en un PC con Windows**, que
sigue haciendo falta para *probar* el ejecutable y para perseguir el cierre
durante el cálculo de guardias.


Script canónico: `scripts/build_windows.ps1`, que lee la versión de `src/config/settings.py`. Los scripts obsoletos de `scripts/build/` se eliminaron en la versión 5.50.0.

> [!IMPORTANT] El script debe guardarse en UTF-8 **con** marca de orden de bytes
> Windows PowerShell 5.1 lee los ficheros sin marca con la codificación ANSI del
> sistema. Entonces la «Ó» de «COMPILACIÓN» se convierte en dos caracteres, y el
> segundo es una comilla tipográfica que PowerShell toma como delimitador de
> cadena: el análisis se descuadra y falla con «missing the terminator», señalando
> además una línea que no tiene nada que ver. Un test lo vigila.

## Requisitos en el PC Windows

- Python 3.11 x64 (`py -3.11 --version`).
- Inno Setup 6 en `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`.
- Git y el repositorio clonado fuera de OneDrive/iCloud (rutas sincronizadas bloquean ficheros durante el build).

## Pasos

```powershell
# 1. Entorno
py -3.11 -m venv .venv-win
.\.venv-win\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt pyinstaller

# 2. Comprobación rápida antes de compilar
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/audit -q --no-cov
python -c "import ortools, PyQt6.QtCore; print('ok')"

# 3. Build (exe + instalador)
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
#    Opciones: -SkipInstaller (sólo exe) · -SkipClean · -Version 5.43.0

# 4. Artefactos
#    dist\GuardiasDePatio\GuardiasDePatio.exe
#    Output\GuardiasDePatio-<versión>-Windows-Setup.exe
```

## Variante de diagnóstico (cierres silenciosos)

Disponible en el script desde la versión 5.44.0:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Diagnostico
.\dist\GuardiasDePatio-debug\GuardiasDePatio-debug.exe 2>&1 | Tee-Object -FilePath crash.txt
```

Compila con consola visible, activa `PYTHONFAULTHANDLER`, nombra el artefacto `GuardiasDePatio-debug` y no genera instalador. La aplicación además escribe `%APPDATA%\GuardiasDePatio\logs\faulthandler.log` con la pila de todos los hilos si se produce un fallo nativo.

Las dos variantes salen del **mismo** `GuardiasDePatio.spec` (BLD-016): la de diagnóstico es el spec con `GUARDIAS_BUILD_DIAGNOSTICO=1` en el entorno, que pone `console=True` y añade `-debug` al nombre. Equivalente manual, si hiciera falta ajustar algo:

```powershell
$env:PYTHONFAULTHANDLER = "1"
$env:GUARDIAS_BUILD_DIAGNOSTICO = "1"
python -m PyInstaller --noconfirm --clean GuardiasDePatio.spec
.\dist\GuardiasDePatio-debug\GuardiasDePatio-debug.exe 2>&1 | Tee-Object -FilePath crash.txt
```

> [!WARNING] Nunca pasar `src\main.py` ni argumentos `--add-data`/`--collect-all` a PyInstaller
> Con argumentos sueltos PyInstaller **genera su propio spec encima** de `GuardiasDePatio.spec` y el exe sale sin lo que se arregla ahí (hoja de estilos, `upx=False`, migraciones sin acentos). Así se compilaron las versiones 6.1.1 a 6.3.0 en GitHub: el log decía «wrote …GuardiasDePatio.spec». Un test lo vigila.

## Si al hacer doble clic no aparece nada

Primero mirar si existe un `app_*.log` nuevo en `%APPDATA%\GuardiasDePatio\logs`. Se crea antes de cargar Qt, así que separa dos casos que se ven igual:

| Hay `app_*.log` nuevo | Qué significa | Qué hacer |
| --- | --- | --- |
| No | El proceso no llega a ejecutar Python: bloqueo por directiva (AppLocker/SRP contra `%LOCALAPPDATA%\Programs` o la carpeta del portable), antivirus, o SmartScreen sin aceptar | Visor de eventos → Windows → Aplicación (evento 1000 o 8004 AppLocker); probar el portable en otra carpeta; «Más información → Ejecutar de todas formas» |
| Sí, acaba en «Conectando con el servidor…» | El puerto 22 está cortado; hasta v6.3.0 no se pintaba nada durante los ~35 s de espera | Esperar el aviso «Sin sincronización» o revisar el cortafuegos del centro |
| Sí, con traza | Fallo de Python o nativo (`faulthandler.log`) | Build de diagnóstico y protocolo de `auditoria/06` |

Después de reproducir el cierre: adjuntar `crash.txt`, las últimas 200 líneas de `%APPDATA%\GuardiasDePatio\logs\app_*.log` y el evento 1000 del Visor de eventos (módulo y código de excepción). Protocolo completo en `auditoria/06_CRASH_WINDOWS_GENERACION.md` §5.

## Verificación mínima del artefacto

1. Instalar en una máquina o cuenta limpia.
2. Login, crear curso, 2 zonas, 5 profesores, calcular cuotas, generar con CP-SAT y con v4.
3. Exportar un PDF y cerrar con sincronización.
4. Revisar `%APPDATA%\GuardiasDePatio\logs` sin `ERROR`.

## Publicar

```powershell
gh release upload v<versión> Output\GuardiasDePatio-<versión>-Windows-Setup.exe --clobber
```

## Errores conocidos

| Síntoma | Causa | Solución |
| --- | --- | --- |
| `ModuleNotFoundError: ortools...` al arrancar | faltó `--collect-all ortools` | usar el script canónico |
| Ventana sin controles nativos | `showFullScreen` | ya corregido (5.42.1) |
| El exe cierra sin mensaje | fallo nativo; ver `auditoria/06` | build de diagnóstico |
| Doble clic y nada, sin `app_*.log` nuevo | el proceso no arranca: directiva, antivirus o SmartScreen | ver «Si al hacer doble clic no aparece nada» |
| El portable avisa «Windows protegió su PC» | marca de la web en el zip descargado; el exe no va firmado | «Más información → Ejecutar de todas formas», o desbloquear el zip antes de descomprimir |
| La app sale sin tema, o en GitHub el log dice «wrote …GuardiasDePatio.spec» | PyInstaller recibió argumentos sueltos y regeneró el spec | compilar siempre `GuardiasDePatio.spec` (BLD-016) |
| `ISCC.exe` no encontrado | Inno Setup no instalado | instalar o `-SkipInstaller` |
