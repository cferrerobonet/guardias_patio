---
name: build-windows-exe
description: Compilar Guardias de Patio para Windows (exe + instalador Inno Setup) desde un PC Windows, incluida la variante de diagnóstico con consola. Usar cuando se pida generar el exe, el instalador de Windows o depurar un cierre en Windows.
---

# Build Windows: exe + instalador

Script canónico: `scripts/build_windows.ps1` (lee la versión de `src/config/settings.py`). Ignorar `scripts/build/build_windows.ps1` y `.bat` (obsoletos, referencian un spec inexistente).

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

Hasta que el script incorpore `-Debug`, ejecutar PyInstaller a mano con consola y faulthandler:

```powershell
$env:PYTHONFAULTHANDLER = "1"
python -m PyInstaller --noconfirm --clean --console --name GuardiasDePatio-debug `
  --icon=imagenes/logo.ico --add-data "imagenes;imagenes" --add-data "alembic;alembic" --add-data "alembic.ini;." `
  --collect-all ortools --collect-all dependency_injector `
  --hidden-import=logging.config --hidden-import=logging.handlers --hidden-import=ortools.sat.python.cp_model_helper `
  --hidden-import=matplotlib --hidden-import=matplotlib.backends.backend_qtagg --hidden-import=reportlab `
  --exclude-module tkinter --exclude-module email_validator src\main.py
.\dist\GuardiasDePatio-debug\GuardiasDePatio-debug.exe 2>&1 | Tee-Object -FilePath crash.txt
```

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
| `ISCC.exe` no encontrado | Inno Setup no instalado | instalar o `-SkipInstaller` |
