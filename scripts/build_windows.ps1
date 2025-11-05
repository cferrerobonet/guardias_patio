# Script de compilación automática para Windows
# Versión: 1.0
# Fecha: 2025-11-05
# 
# Este script automatiza la compilación del ejecutable y del instalador
# asegurando que todas las dependencias estén incluidas correctamente

param(
    [string]$Version = "3.0.0",
    [switch]$SkipClean = $false,
    [switch]$SkipInstaller = $false
)

# Configuración de rutas
$VenvPath = "C:\dev\guardias-patio\.venv"
$DistPath = "C:\dev\gdp_dist"
$BuildPath = "C:\dev\gdp_build"
$OutputPath = "C:\dev\gdp_out"
$WorkspacePath = $PSScriptRoot | Split-Path -Parent

# Colores para output
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Step { Write-Host "`n=== $args ===" -ForegroundColor Yellow }

# Verificar que el venv existe
if (-not (Test-Path "$VenvPath\Scripts\python.exe")) {
    Write-Error "Virtual environment no encontrado en $VenvPath"
    Write-Info "Ejecuta primero: python -m venv $VenvPath"
    exit 1
}

Write-Step "PASO 1: Verificar dependencias críticas"

# Dependencias que DEBEN estar instaladas en el venv
$RequiredPackages = @(
    "matplotlib",
    "reportlab",
    "PyQt6",
    "sqlalchemy",
    "alembic",
    "pydantic",
    "structlog",
    "python-dotenv",
    "paramiko",
    "psutil",
    "bcrypt",
    "cryptography"
)

$MissingPackages = @()
foreach ($package in $RequiredPackages) {
    $installed = & "$VenvPath\Scripts\pip.exe" show $package 2>$null
    if (-not $installed) {
        $MissingPackages += $package
        Write-Error "Falta $package"
    } else {
        Write-Success "$package instalado"
    }
}

if ($MissingPackages.Count -gt 0) {
    Write-Error "Faltan paquetes. Instalar con:"
    Write-Host "  & '$VenvPath\Scripts\pip.exe' install $($MissingPackages -join ' ')"
    exit 1
}

# Verificar que email_validator NO está instalado (causa conflictos con pydantic)
$emailValidator = & "$VenvPath\Scripts\pip.exe" show email_validator 2>$null
if ($emailValidator) {
    Write-Error "email_validator está instalado y debe eliminarse"
    Write-Info "Ejecutando: pip uninstall -y email_validator"
    & "$VenvPath\Scripts\pip.exe" uninstall -y email_validator
    Write-Success "email_validator eliminado"
}

Write-Step "PASO 2: Limpiar directorios de compilación"

if (-not $SkipClean) {
    if (Test-Path $DistPath) {
        Remove-Item -Path $DistPath -Recurse -Force
        Write-Success "Limpiado $DistPath"
    }
    if (Test-Path $BuildPath) {
        Remove-Item -Path $BuildPath -Recurse -Force
        Write-Success "Limpiado $BuildPath"
    }
    if (Test-Path "$WorkspacePath\GuardiasDePatio.spec") {
        Remove-Item "$WorkspacePath\GuardiasDePatio.spec" -Force
        Write-Success "Eliminado spec anterior"
    }
} else {
    Write-Info "Omitiendo limpieza (--SkipClean)"
}

Write-Step "PASO 3: Compilar ejecutable con PyInstaller"

Set-Location $WorkspacePath

# Argumentos críticos para PyInstaller
$PyInstallerArgs = @(
    "--windowed",                                           # Sin consola
    "--noconfirm",                                         # No pedir confirmación
    "--clean",                                             # Limpiar cache
    "--icon=imagenes/logo.ico",                           # Icono
    "--add-data", "imagenes;imagenes",                    # Incluir imágenes
    "--add-data", "alembic;alembic",                      # Incluir migraciones
    "--exclude-module", "tkinter",                        # Excluir tkinter (no usado)
    "--exclude-module", "email_validator",                # Excluir email_validator
    "--hidden-import=matplotlib",                         # CRÍTICO: matplotlib
    "--hidden-import=matplotlib.backends.backend_qtagg",  # CRÍTICO: backend Qt6
    "--hidden-import=reportlab",                          # CRÍTICO: reportlab
    "--distpath", $DistPath,
    "--workpath", $BuildPath,
    "--name", "GuardiasDePatio",
    "src/main.py"
)

Write-Info "Ejecutando PyInstaller..."
& "$VenvPath\Scripts\pyinstaller.exe" @PyInstallerArgs

if (-not (Test-Path "$DistPath\GuardiasDePatio\GuardiasDePatio.exe")) {
    Write-Error "PyInstaller falló - ejecutable no generado"
    exit 1
}

Write-Success "Ejecutable generado"

Write-Step "PASO 4: Verificar dependencias en el ejecutable"

$HasMatplotlib = Test-Path "$DistPath\GuardiasDePatio\_internal\matplotlib"
$HasReportlab = Test-Path "$DistPath\GuardiasDePatio\_internal\reportlab"
$HasEmailValidator = Get-ChildItem "$DistPath\GuardiasDePatio\_internal" -Filter "*email_validator*" -Directory -ErrorAction SilentlyContinue

if (-not $HasMatplotlib) {
    Write-Error "matplotlib NO incluido en el ejecutable"
    exit 1
}
Write-Success "matplotlib incluido"

if (-not $HasReportlab) {
    Write-Error "reportlab NO incluido - copiando manualmente..."
    Copy-Item -Path "$VenvPath\Lib\site-packages\reportlab" `
              -Destination "$DistPath\GuardiasDePatio\_internal\reportlab" `
              -Recurse -Force
    if (Test-Path "$DistPath\GuardiasDePatio\_internal\reportlab") {
        Write-Success "reportlab copiado manualmente"
    } else {
        Write-Error "Falló la copia de reportlab"
        exit 1
    }
} else {
    Write-Success "reportlab incluido"
}

if ($HasEmailValidator) {
    Write-Error "email_validator presente - eliminando..."
    Get-ChildItem "$DistPath\GuardiasDePatio\_internal" -Recurse -Filter "*email_validator*" | Remove-Item -Recurse -Force
    Write-Success "email_validator eliminado"
} else {
    Write-Success "email_validator NO presente (correcto)"
}

Write-Step "PASO 5: Compilar instalador con Inno Setup"

if ($SkipInstaller) {
    Write-Info "Omitiendo compilación de instalador (--SkipInstaller)"
    Write-Success "Ejecutable listo en: $DistPath\GuardiasDePatio\GuardiasDePatio.exe"
    exit 0
}

# Verificar Inno Setup
$InnoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetup)) {
    Write-Error "Inno Setup no encontrado en: $InnoSetup"
    Write-Info "Descarga desde: https://jrsoftware.org/isdl.php"
    exit 1
}

Write-Info "Compilando instalador con Inno Setup..."
& $InnoSetup "$WorkspacePath\installer_windows.iss"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Inno Setup falló con código de salida: $LASTEXITCODE"
    exit 1
}

# Verificar que se creó el instalador
$InstallerPath = "$OutputPath\GuardiasDePatio-$Version-Windows-Setup.exe"
if (-not (Test-Path $InstallerPath)) {
    Write-Error "Instalador no generado en: $InstallerPath"
    exit 1
}

$InstallerInfo = Get-Item $InstallerPath
Write-Success "Instalador creado"
Write-Info "  Archivo: $($InstallerInfo.Name)"
Write-Info "  Tamaño: $([math]::Round($InstallerInfo.Length / 1MB, 2)) MB"
Write-Info "  Ruta: $InstallerPath"

Write-Step "✅ COMPILACIÓN COMPLETADA EXITOSAMENTE"
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "  1. Desinstala versiones anteriores de Guardias de Patio"
Write-Host "  2. Ejecuta el instalador: $InstallerPath"
Write-Host "  3. Prueba la aplicación"
Write-Host ""
