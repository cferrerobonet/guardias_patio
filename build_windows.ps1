# Script PowerShell para crear instalador de Guardias de Patio para Windows
# Requiere PyInstaller e Inno Setup instalados

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Guardias de Patio - Build Windows    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Variables
$AppName = "Guardias de Patio"
$Version = "2.7.0"
$OutputName = "GuardiasDePatio-$Version-Windows-Setup.exe"

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python no encontrado en PATH" -ForegroundColor Red
    exit 1
}
Write-Host "  Python encontrado" -ForegroundColor Green

# Verificar PyInstaller
Write-Host "Verificando PyInstaller..." -ForegroundColor Yellow
try {
    python -m PyInstaller --version | Out-Null
    Write-Host "  PyInstaller encontrado" -ForegroundColor Green
} catch {
    Write-Host "  PyInstaller no encontrado. Instalando..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

# Limpiar builds anteriores
Write-Host ""
Write-Host "Limpiando builds anteriores..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\GuardiasDePatio") { Remove-Item -Recurse -Force "dist\GuardiasDePatio" }
Write-Host "  Limpieza completada" -ForegroundColor Green

# Crear ejecutable con PyInstaller
Write-Host ""
Write-Host "Creando ejecutable con PyInstaller..." -ForegroundColor Yellow
Write-Host "  Esto puede tardar varios minutos..." -ForegroundColor Gray
python -m PyInstaller --noconfirm --clean guardias_patio_windows.spec

if (-not (Test-Path "dist\GuardiasDePatio\GuardiasDePatio.exe")) {
    Write-Host "ERROR: No se pudo crear el ejecutable" -ForegroundColor Red
    exit 1
}
Write-Host "  Ejecutable creado exitosamente" -ForegroundColor Green

# Verificar Inno Setup
Write-Host ""
Write-Host "Verificando Inno Setup..." -ForegroundColor Yellow
$InnoSetupPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetupPath)) {
    Write-Host "  Inno Setup no encontrado en la ubicación predeterminada" -ForegroundColor Yellow
    Write-Host "  Buscando en otras ubicaciones..." -ForegroundColor Yellow
    
    # Buscar en Program Files
    $InnoSetupPath = Get-ChildItem -Path "C:\Program Files*" -Recurse -Filter "ISCC.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
    
    if (-not $InnoSetupPath) {
        Write-Host ""
        Write-Host "ADVERTENCIA: Inno Setup no encontrado" -ForegroundColor Red
        Write-Host ""
        Write-Host "El ejecutable está listo en: dist\GuardiasDePatio\" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Para crear el instalador:" -ForegroundColor Yellow
        Write-Host "  1. Descarga Inno Setup: https://jrsoftware.org/isdl.php" -ForegroundColor White
        Write-Host "  2. Instálalo" -ForegroundColor White
        Write-Host "  3. Ejecuta: ISCC.exe installer_windows.iss" -ForegroundColor White
        Write-Host ""
        exit 0
    }
}

Write-Host "  Inno Setup encontrado: $InnoSetupPath" -ForegroundColor Green

# Crear instalador con Inno Setup
Write-Host ""
Write-Host "Creando instalador con Inno Setup..." -ForegroundColor Yellow
& $InnoSetupPath "installer_windows.iss"

if (-not (Test-Path "dist\$OutputName")) {
    Write-Host "ERROR: No se pudo crear el instalador" -ForegroundColor Red
    exit 1
}

# Obtener tamaño del instalador
$InstallerSize = (Get-Item "dist\$OutputName").Length / 1MB
$InstallerSizeMB = [math]::Round($InstallerSize, 2)

# Resumen
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETADO EXITOSAMENTE        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Archivos generados:" -ForegroundColor Cyan
Write-Host "  Ejecutable: dist\GuardiasDePatio\GuardiasDePatio.exe" -ForegroundColor White
Write-Host "  Instalador: dist\$OutputName" -ForegroundColor White
Write-Host "  Tamaño: $InstallerSizeMB MB" -ForegroundColor White
Write-Host ""
Write-Host "Para probar el instalador:" -ForegroundColor Yellow
Write-Host "  .\dist\$OutputName" -ForegroundColor White
Write-Host ""
Write-Host "Para distribuir:" -ForegroundColor Yellow
Write-Host "  - Sube el instalador a GitHub Releases" -ForegroundColor White
Write-Host "  - Compártelo por email o web" -ForegroundColor White
Write-Host "  - Los usuarios solo necesitan ejecutar el instalador" -ForegroundColor White
Write-Host ""
