@echo off
REM Script batch para crear instalador de Guardias de Patio para Windows
REM Ejecutar desde el directorio raíz del proyecto

echo ========================================
echo   Guardias de Patio - Build Windows
echo ========================================
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    echo Instala Python desde https://www.python.org/
    pause
    exit /b 1
)
echo   Python encontrado

REM Instalar PyInstaller si no está
echo.
echo Verificando PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo   Instalando PyInstaller...
    python -m pip install pyinstaller
)
echo   PyInstaller listo

REM Limpiar builds anteriores
echo.
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist\GuardiasDePatio rmdir /s /q dist\GuardiasDePatio
echo   Limpieza completada

REM Crear ejecutable
echo.
echo Creando ejecutable con PyInstaller...
echo   (Esto puede tardar varios minutos...)
python -m PyInstaller --noconfirm --clean guardias_patio_windows.spec

if not exist dist\GuardiasDePatio\GuardiasDePatio.exe (
    echo ERROR: No se pudo crear el ejecutable
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD COMPLETADO EXITOSAMENTE
echo ========================================
echo.
echo Ejecutable creado en: dist\GuardiasDePatio\
echo.
echo Para crear el instalador:
echo   1. Descarga Inno Setup: https://jrsoftware.org/isdl.php
echo   2. Instalalo
echo   3. Clic derecho en installer_windows.iss ^> Compile
echo.
echo O ejecuta: build_windows.ps1 (PowerShell)
echo.
pause
