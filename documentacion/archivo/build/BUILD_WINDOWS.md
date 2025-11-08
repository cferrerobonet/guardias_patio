# Guía de Compilación para Windows

## Versión: 3.0.0
**Última actualización:** 5 de noviembre de 2025

---

## 📋 Requisitos Previos

### Software Necesario

1. **Python 3.13.3** (o superior)
   - Descargar de: https://www.python.org/downloads/

2. **Inno Setup 6.5.4** (o superior)
   - Descargar de: https://jrsoftware.org/isdl.php
   - **IMPORTANTE**: Instalar en `C:\Program Files (x86)\Inno Setup 6\`

3. **Git** (opcional, para control de versiones)
   - Configuración recomendada:
     ```bash
     git config --global core.autocrlf input
     git config --global core.longpaths true
     ```

### Estructura de Directorios

```
C:\dev\
├── guardias-patio\.venv\      # Virtual environment Python
├── gdp_dist\                   # Output de PyInstaller (generado)
├── gdp_build\                  # Archivos temporales (generado)
└── gdp_out\                    # Instaladores finales (generado)
```

**⚠️ IMPORTANTE**: Usar rutas cortas fuera de OneDrive para evitar problemas de sincronización y límites de longitud de ruta.

---

## 🚀 Compilación Automática (RECOMENDADO)

### Uso Básico

```powershell
# Desde el directorio del proyecto
.\scripts\build_windows.ps1
```

### Opciones Avanzadas

```powershell
# Compilar solo el ejecutable (sin instalador)
.\scripts\build_windows.ps1 -SkipInstaller

# Compilar sin limpiar archivos anteriores
.\scripts\build_windows.ps1 -SkipClean

# Especificar versión personalizada
.\scripts\build_windows.ps1 -Version "3.1.0"
```

### ¿Qué hace el script automático?

1. ✅ Verifica que todas las dependencias estén instaladas
2. ✅ Confirma que `email_validator` NO esté presente
3. ✅ Limpia directorios de compilaciones anteriores
4. ✅ Ejecuta PyInstaller con todos los parámetros correctos
5. ✅ Verifica que matplotlib y reportlab estén incluidos
6. ✅ Elimina email_validator si se filtró
7. ✅ Compila el instalador con Inno Setup
8. ✅ Valida que el instalador se creó correctamente

---

## 🔧 Compilación Manual (Solo si es necesario)

### Paso 1: Configurar Virtual Environment

```powershell
# Crear venv en ubicación externa
python -m venv C:\dev\guardias-patio\.venv

# Activar (solo para verificación)
C:\dev\guardias-patio\.venv\Scripts\Activate.ps1

# Instalar dependencias
C:\dev\guardias-patio\.venv\Scripts\pip.exe install -r requirements.txt

# CRÍTICO: Desinstalar email_validator si existe
C:\dev\guardias-patio\.venv\Scripts\pip.exe uninstall -y email_validator
```

### Paso 2: Limpiar Compilaciones Anteriores

```powershell
Remove-Item -Path "C:\dev\gdp_dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "C:\dev\gdp_build" -Recurse -Force -ErrorAction SilentlyContinue
```

### Paso 3: Compilar con PyInstaller

```powershell
cd "ruta\al\proyecto"

C:\dev\guardias-patio\.venv\Scripts\pyinstaller.exe `
    --windowed `
    --noconfirm `
    --clean `
    --icon="imagenes/logo.ico" `
    --add-data "imagenes;imagenes" `
    --add-data "alembic;alembic" `
    --exclude-module tkinter `
    --exclude-module email_validator `
    --hidden-import=matplotlib `
    --hidden-import=matplotlib.backends.backend_qtagg `
    --hidden-import=reportlab `
    --distpath "C:\dev\gdp_dist" `
    --workpath "C:\dev\gdp_build" `
    --name "GuardiasDePatio" `
    src/main.py
```

### Paso 4: Verificar Dependencias Críticas

```powershell
# Verificar matplotlib
Test-Path "C:\dev\gdp_dist\GuardiasDePatio\_internal\matplotlib"

# Verificar reportlab (si no está, copiar manualmente)
if (-not (Test-Path "C:\dev\gdp_dist\GuardiasDePatio\_internal\reportlab")) {
    Copy-Item -Path "C:\dev\guardias-patio\.venv\Lib\site-packages\reportlab" `
              -Destination "C:\dev\gdp_dist\GuardiasDePatio\_internal\reportlab" `
              -Recurse -Force
}

# Eliminar email_validator si existe
Get-ChildItem "C:\dev\gdp_dist\GuardiasDePatio\_internal" -Recurse -Filter "*email_validator*" | Remove-Item -Recurse -Force
```

### Paso 5: Compilar Instalador

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer_windows.iss"
```

**Resultado:** `C:\dev\gdp_out\GuardiasDePatio-3.0.0-Windows-Setup.exe`

---

## ⚠️ Problemas Comunes y Soluciones

### 1. Error: "No module named 'matplotlib'"

**Causa:** matplotlib no está en el venv correcto

**Solución:**
```powershell
C:\dev\guardias-patio\.venv\Scripts\pip.exe install matplotlib>=3.7.0
```

### 2. Error: "No module named 'reportlab'"

**Causa:** reportlab no incluido por PyInstaller

**Solución:**
```powershell
# Instalar en venv
C:\dev\guardias-patio\.venv\Scripts\pip.exe install reportlab>=4.0.0

# Si aún falla, copiar manualmente después de compilar
Copy-Item -Path "C:\dev\guardias-patio\.venv\Lib\site-packages\reportlab" `
          -Destination "C:\dev\gdp_dist\GuardiasDePatio\_internal\reportlab" `
          -Recurse -Force
```

### 3. Error: "email-validator is not installed"

**Causa:** Pydantic intenta usar EmailStr pero email_validator está excluido

**Solución:**
- ✅ **CORRECTO**: Eliminar email_validator del venv
- ✅ **CORRECTO**: Usar `str` en lugar de `EmailStr` en DTOs y schemas
- ❌ **INCORRECTO**: Instalar email_validator (causa conflictos)

```powershell
# Verificar y eliminar
C:\dev\guardias-patio\.venv\Scripts\pip.exe uninstall -y email_validator
```

### 4. Proceso se "Cuelga" Durante Compilación

**Causa:** Uso de `Start-Sleep` u otros comandos que bloquean terminal

**Solución:**
- Nunca usar `Start-Sleep` después de comandos largos
- Usar `isBackground: true` para procesos largos
- Monitorear con `get_terminal_output` en lugar de esperas

### 5. Rutas Demasiado Largas en OneDrive

**Causa:** Windows tiene límite de 260 caracteres; OneDrive empeora esto

**Solución:**
- Usar `C:\dev\` para builds
- Nunca compilar directamente en carpetas de OneDrive
- Habilitar rutas largas: `git config --global core.longpaths true`

### 6. Inno Setup: "Error on line X"

**Causas comunes:**
- Sintaxis incorrecta en `AppId={{...}}`
- Tareas obsoletas (quicklaunchicon)
- Archivos de imagen faltantes

**Solución:**
```ini
; Correcto
AppId={{8B5C9D4E-3F2A-4A1B-9E6D-7C8A5B2F1E3D}}

; Usar imágenes clásicas
WizardImageFile={#SourcePath}\WizClassicImage-IS.bmp
WizardSmallImageFile={#SourcePath}\WizClassicSmallImage-IS.bmp

; No usar quicklaunchicon (obsoleto en Windows 10+)
```

---

## 📦 Dependencias Críticas

### DEBEN estar en requirements.txt:

```txt
matplotlib>=3.7.0
reportlab>=4.0.0
PyQt6==6.7.0
PyQt6-Qt6==6.7.3
pydantic>=2.0.0  # SIN [email]
pydantic-settings>=2.0.0
sqlalchemy
alembic
structlog>=23.0.0
python-dotenv>=1.0.0
paramiko>=4.0.0
psutil>=5.9.0
bcrypt
cryptography
```

### NO DEBEN estar:

```txt
❌ email-validator
❌ pydantic[email]  # Usar pydantic sin extras
❌ tkinter  # Excluido en PyInstaller
```

---

## 🔍 Verificación Post-Compilación

### Verificar Ejecutable

```powershell
# Tamaño esperado: ~18-20 MB
Get-Item "C:\dev\gdp_dist\GuardiasDePatio\GuardiasDePatio.exe" | Select-Object Length

# Dependencias incluidas
Test-Path "C:\dev\gdp_dist\GuardiasDePatio\_internal\matplotlib"    # Debe ser True
Test-Path "C:\dev\gdp_dist\GuardiasDePatio\_internal\reportlab"     # Debe ser True
Get-ChildItem "C:\dev\gdp_dist\GuardiasDePatio\_internal" -Filter "*email_validator*"  # Debe estar vacío
```

### Verificar Instalador

```powershell
# Tamaño esperado: ~60-70 MB
Get-Item "C:\dev\gdp_out\GuardiasDePatio-3.0.0-Windows-Setup.exe" | Select-Object Length, LastWriteTime
```

### Prueba de Instalación

1. Desinstalar versiones anteriores
2. Ejecutar instalador como administrador
3. Verificar instalación en: `C:\Program Files\Guardias de Patio\`
4. Ejecutar app y verificar:
   - ✅ Se abre sin errores
   - ✅ No hay errores de matplotlib
   - ✅ No hay errores de reportlab
   - ✅ No hay errores de email_validator

---

## 📝 Checklist Pre-Compilación

- [ ] Virtual environment configurado en `C:\dev\guardias-patio\.venv`
- [ ] Todas las dependencias instaladas (sin email_validator)
- [ ] `version_info.txt` actualizado con versión correcta
- [ ] `installer_windows.iss` actualizado con versión correcta
- [ ] Git commit de cambios pendientes
- [ ] Directorios de compilación limpios

---

## 🎯 Resumen de Comandos Rápidos

```powershell
# Compilación completa automatizada
.\scripts\build_windows.ps1

# Solo actualizar dependencias
C:\dev\guardias-patio\.venv\Scripts\pip.exe install -r requirements.txt

# Limpiar y recompilar desde cero
Remove-Item C:\dev\gdp_dist, C:\dev\gdp_build -Recurse -Force
.\scripts\build_windows.ps1
```

---

## 📞 Soporte

Si encuentras errores no documentados aquí:

1. Verifica que todas las dependencias estén en el venv correcto
2. Confirma que no hay `Start-Sleep` interrumpiendo procesos
3. Revisa los logs de PyInstaller en: `C:\dev\gdp_build\`
4. Consulta la documentación de Inno Setup para errores de instalador

**Fecha de última compilación exitosa:** 5 de noviembre de 2025, 22:01:24
