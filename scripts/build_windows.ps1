# Script de compilación automática para Windows

param(
    [string]$Version = "",
    [switch]$SkipClean = $false,
    [switch]$SkipInstaller = $false,
    # Compila una variante con consola visible y faulthandler activo, para
    # diagnosticar cierres silenciosos. No genera instalador.
    # Uso: powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Diagnostico
    [switch]$Diagnostico = $false
)

$WorkspacePath = $PSScriptRoot | Split-Path -Parent
$DistPath = Join-Path $WorkspacePath "dist"
$BuildPath = Join-Path $WorkspacePath "build"
$OutputPath = Join-Path $WorkspacePath "Output"
$SettingsPath = Join-Path $WorkspacePath "src\config\settings.py"
$InstallerScript = Join-Path $WorkspacePath "installer_windows.iss"

function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-ErrorMsg { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Step { Write-Host "`n=== $args ===" -ForegroundColor Yellow }

function Resolve-PythonPath {
    $Candidates = @(
        (Join-Path $WorkspacePath ".venv-win\Scripts\python.exe"),
        (Join-Path $WorkspacePath ".venv\Scripts\python.exe")
    )

    foreach ($candidate in $Candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    return $null
}

function Resolve-AppVersion {
    if ($Version) {
        return $Version
    }

    if (-not (Test-Path $SettingsPath)) {
        return "0.0.0"
    }

    $settingsContent = Get-Content $SettingsPath -Raw
    $match = [regex]::Match($settingsContent, 'app_version\s*:\s*str\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"')
    if ($match.Success) {
        return $match.Groups[1].Value
    }

    return "0.0.0"
}

Set-Location $WorkspacePath

$ResolvedVersion = Resolve-AppVersion
$PythonPath = Resolve-PythonPath

if (-not $PythonPath) {
    Write-ErrorMsg "No se encontró Python. Crea .venv-win o instala Python en PATH."
    exit 1
}

Write-Step "PASO 1: Preparar entorno"
Write-Info "Python seleccionado: $PythonPath"
Write-Info "Versión de app: $ResolvedVersion"

& $PythonPath -m pip install --upgrade pip | Out-Null
& $PythonPath -m pip install -r "requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Falló instalación de requirements.txt"
    exit 1
}

& $PythonPath -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Falló instalación de PyInstaller"
    exit 1
}

Write-Step "PASO 2: Limpiar directorios de compilación"
if (-not $SkipClean) {
    if (Test-Path $BuildPath) {
        Remove-Item -Path $BuildPath -Recurse -Force
        Write-Success "Limpiado $BuildPath"
    }
    if (Test-Path (Join-Path $DistPath "GuardiasDePatio")) {
        Remove-Item -Path (Join-Path $DistPath "GuardiasDePatio") -Recurse -Force
        Write-Success "Limpiado dist\\GuardiasDePatio"
    }
    if (Test-Path $OutputPath) {
        Remove-Item -Path $OutputPath -Recurse -Force
        Write-Success "Limpiado $OutputPath"
    }
}

New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

Write-Step "PASO 3: Compilar ejecutable con PyInstaller"

$AppName = if ($Diagnostico) { "GuardiasDePatio-debug" } else { "GuardiasDePatio" }
$ModoVentana = if ($Diagnostico) { "--console" } else { "--windowed" }
if ($Diagnostico) {
    Write-Info "Modo diagnostico: consola visible, nombre $AppName, sin instalador"
    $env:PYTHONFAULTHANDLER = "1"
}

$PyInstallerArgs = @(
    $ModoVentana,
    "--noconfirm",
    "--clean",
    "--icon=imagenes/logo.ico",
    "--add-data", "imagenes;imagenes",
    "--add-data", "alembic;alembic",
    "--add-data", "alembic.ini;.",
    "--exclude-module", "tkinter",
    "--exclude-module", "email_validator",
    "--collect-all", "dependency_injector",
    "--collect-all", "ortools",
    "--collect-binaries", "ortools",
    "--collect-data", "ortools",
    "--collect-submodules", "ortools",
    "--hidden-import=logging.config",
    "--hidden-import=logging.handlers",
    "--hidden-import=dependency_injector.errors",
    "--hidden-import=ortools.sat.python.cp_model_helper",
    "--hidden-import=matplotlib",
    "--hidden-import=matplotlib.backends.backend_qtagg",
    "--hidden-import=reportlab",
    "--distpath", $DistPath,
    "--workpath", $BuildPath,
    "--name", $AppName,
    "src/main.py"
)

& $PythonPath -m PyInstaller @PyInstallerArgs
$ExeGenerado = Join-Path $DistPath "$AppName\$AppName.exe"
if (-not (Test-Path $ExeGenerado)) {
    Write-ErrorMsg "PyInstaller fallo: no se genero $ExeGenerado"
    exit 1
}
Write-Success "Ejecutable generado: $ExeGenerado"

if ($Diagnostico) {
    Write-Info "Lanza el exe desde cmd y reproduce el fallo:"
    Write-Info "  $ExeGenerado 2>&1 | Tee-Object -FilePath crash.txt"
    Write-Info "Revisa tambien %APPDATA%\GuardiasDePatio\logs\faulthandler.log"
    exit 0
}

if ($SkipInstaller) {
    Write-Success "Compilación completa sin instalador (--SkipInstaller)"
    exit 0
}

Write-Step "PASO 4: Compilar instalador con Inno Setup"

if (-not (Test-Path $InstallerScript)) {
    Write-ErrorMsg "No existe $InstallerScript"
    exit 1
}

$InnoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetup)) {
    $InnoSetup = Get-ChildItem -Path "C:\Program Files*" -Recurse -Filter "ISCC.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
}

if (-not $InnoSetup) {
    Write-ErrorMsg "Inno Setup no encontrado"
    exit 1
}

& $InnoSetup "/DMyAppVersion=$ResolvedVersion" $InstallerScript
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Inno Setup falló con código $LASTEXITCODE"
    exit 1
}

$InstallerPath = Join-Path $OutputPath "GuardiasDePatio-$ResolvedVersion-Windows-Setup.exe"
if (-not (Test-Path $InstallerPath)) {
    Write-ErrorMsg "Instalador no generado en $InstallerPath"
    exit 1
}

$InstallerInfo = Get-Item $InstallerPath
Write-Step "COMPILACIÓN COMPLETADA"
Write-Success "Instalador creado"
Write-Info "Archivo: $($InstallerInfo.Name)"
Write-Info "Tamaño: $([math]::Round($InstallerInfo.Length / 1MB, 2)) MB"
Write-Info "Ruta: $InstallerPath"
