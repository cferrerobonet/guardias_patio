# 🔨 Guía de Compilación y Distribución

![Status](https://img.shields.io/badge/Status-Consolidado-success.svg)
![Plataformas](https://img.shields.io/badge/Plataformas-macOS_|_Windows-blue.svg)
![Tipo](https://img.shields.io/badge/Tipo-Guía_Build-orange.svg)
![Última Actualización](https://img.shields.io/badge/Última_Actualización-Nov_2025-green.svg)

> 📦 **Documento Consolidado**: Este archivo reemplaza 3 documentos de compilación

Esta guía consolida toda la información necesaria para compilar y distribuir la aplicación Guardias de Patio.

**Documentos originales archivados:**
- `COMPILACION_RAPIDA.md`
- `SOLUCION_COMPILACION.md`
- `CHECKLIST_COMPILACION.md`

---

## 📋 Índice

1. [Compilación Rápida](#compilación-rápida)
2. [Compilación Detallada](#compilación-detallada)
3. [Distribución](#distribución)
4. [Solución de Problemas](#solución-de-problemas)
5. [Checklist Pre-Release](#checklist-pre-release)

---

## 1. Compilación Rápida

### macOS (DMG)

```bash
# 1. Activar entorno virtual
source .venv/bin/activate

# 2. Compilar app
./scripts/build/build_simple.sh

# 3. Crear DMG
./scripts/build/create_dmg.sh
```

**Resultado:** `GuardiasPatio_vX.X.X_macOS.dmg` en la raíz del proyecto

### Windows (Instalador)

```batch
# 1. Activar entorno virtual
.venv\Scripts\activate

# 2. Compilar ejecutable
.\scripts\build\build_windows.bat

# 3. Crear instalador (requiere Inno Setup)
iscc installer_windows.iss
```

**Resultado:** `GuardiasPatio_Setup_vX.X.X.exe` en `Output/`

---

## 2. Compilación Detallada

### Requisitos Previos

#### macOS
```bash
# Sistema
- macOS 11.0 (Big Sur) o superior
- Xcode Command Line Tools
- Python 3.11+

# Dependencias
brew install create-dmg  # Para crear DMG
```

#### Windows
```powershell
# Sistema
- Windows 10/11 (64-bit)
- Python 3.11+ (desde python.org)
- Visual C++ Redistributable

# Herramientas
- Inno Setup 6.x (para instalador)
```

### Preparación del Entorno

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd "Guardias de patio"

# 2. Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# o .venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar versión en version_info.txt
cat version_info.txt
```

### Compilación macOS

#### Script Automático (Recomendado)

```bash
#!/bin/bash
# scripts/build/build_simple.sh

# Limpiar builds anteriores
rm -rf build/ dist/

# Compilar con PyInstaller
pyinstaller \
    --name="Guardias de Patio" \
    --windowed \
    --onedir \
    --icon=imagenes/icons/app_icon.icns \
    --add-data="imagenes:imagenes" \
    --add-data="version_info.txt:." \
    --osx-bundle-identifier=com.guardias.patio \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=sqlalchemy \
    --collect-all=PyQt6 \
    src/main.py

# Resultado en: dist/Guardias de Patio.app/
```

#### Crear DMG

```bash
#!/bin/bash
# scripts/build/create_dmg.sh

VERSION=$(cat version_info.txt | grep "VERSION" | cut -d'=' -f2 | tr -d ' "')
APP_NAME="Guardias de Patio"
DMG_NAME="GuardiasPatio_v${VERSION}_macOS.dmg"

# Crear DMG con create-dmg
create-dmg \
    --volname "$APP_NAME" \
    --volicon "imagenes/icons/app_icon.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 200 190 \
    --hide-extension "$APP_NAME.app" \
    --app-drop-link 600 185 \
    "$DMG_NAME" \
    "dist/$APP_NAME.app"

echo "✅ DMG creado: $DMG_NAME"
```

### Compilación Windows

#### Script Automático

```batch
@echo off
REM scripts/build/build_windows.bat

REM Limpiar builds anteriores
rmdir /s /q build dist

REM Compilar con PyInstaller
pyinstaller ^
    --name="Guardias de Patio" ^
    --windowed ^
    --onedir ^
    --icon=imagenes\icons\app_icon.ico ^
    --add-data="imagenes;imagenes" ^
    --add-data="version_info.txt;." ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=sqlalchemy ^
    --collect-all=PyQt6 ^
    src\main.py

echo Build completado: dist\Guardias de Patio\
```

#### Crear Instalador (Inno Setup)

```iss
; installer_windows.iss
[Setup]
AppName=Guardias de Patio
AppVersion=2.9.1
DefaultDirName={autopf}\Guardias de Patio
DefaultGroupName=Guardias de Patio
OutputDir=Output
OutputBaseFilename=GuardiasPatio_Setup_v2.9.1

[Files]
Source: "dist\Guardias de Patio\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Guardias de Patio"; Filename: "{app}\Guardias de Patio.exe"
Name: "{commondesktop}\Guardias de Patio"; Filename: "{app}\Guardias de Patio.exe"
```

---

## 3. Distribución

### Generar Checksums

```bash
# macOS/Linux
shasum -a 256 GuardiasPatio_v2.9.1_macOS.dmg > checksums_v2.9.1.txt

# Windows
certutil -hashfile GuardiasPatio_Setup_v2.9.1.exe SHA256 >> checksums_v2.9.1.txt
```

### Publicar en GitHub Releases

1. **Crear Tag:**
   ```bash
   git tag -a v2.9.1 -m "Release v2.9.1"
   git push origin v2.9.1
   ```

2. **Crear Release en GitHub:**
   - Ir a: `Releases` → `Draft a new release`
   - Seleccionar tag: `v2.9.1`
   - Título: `v2.9.1 - Descripción corta`
   - Descripción: Copiar desde `CHANGELOG_v2.9.1.md`

3. **Subir Archivos:**
   - `GuardiasPatio_v2.9.1_macOS.dmg`
   - `GuardiasPatio_Setup_v2.9.1.exe`
   - `checksums_v2.9.1.txt`

4. **Publicar:**
   - Marcar "Set as latest release" si corresponde
   - Click en "Publish release"

### Estructura de Release

```
v2.9.1/
├── GuardiasPatio_v2.9.1_macOS.dmg       (macOS installer)
├── GuardiasPatio_Setup_v2.9.1.exe       (Windows installer)
├── checksums_v2.9.1.txt                 (SHA-256 hashes)
└── Source code (zip/tar.gz)             (auto-generated by GitHub)
```

---

## 4. Solución de Problemas

### Error: "Cannot find PyQt6"

**Problema:** PyInstaller no encuentra módulos de PyQt6

**Solución:**
```bash
# Añadir hooks de PyQt6 explícitamente
pyinstaller \
    --collect-all PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=PyQt6.QtGui \
    ...
```

### Error: "Symlink bug" en macOS

**Problema:** Bug conocido de PyQt6 con symlinks en macOS

**Solución:**
```bash
# NO usar archivos .spec
# Usar comandos directos de PyInstaller con --onedir

# ❌ MAL:
pyinstaller guardias_patio.spec

# ✅ BIEN:
pyinstaller --onedir ... src/main.py
```

### Error: "DLL not found" en Windows

**Problema:** Faltan DLLs de Visual C++

**Solución:**
1. Instalar [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Añadir a instalador:
   ```iss
   [Files]
   Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
   
   [Run]
   Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/quiet /norestart"
   ```

### App no arranca en macOS

**Problema:** Gatekeeper bloquea app sin firmar

**Solución (usuario final):**
```bash
# Permitir app sin verificar
sudo xattr -rd com.apple.quarantine "/Applications/Guardias de Patio.app"
```

**Solución (desarrollador - opcional):**
```bash
# Firmar app con certificado de desarrollador
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: TU NOMBRE" \
    "dist/Guardias de Patio.app"
```

### Base de datos no se crea

**Problema:** Permisos de escritura en directorio de usuario

**Solución:**
```python
# En src/database/db_manager.py
# Asegurar que el directorio existe y tiene permisos
os.makedirs(data_dir, mode=0o755, exist_ok=True)
```

---

## 5. Checklist Pre-Release

### Antes de Compilar

- [ ] Actualizar `version_info.txt`
- [ ] Actualizar `CHANGELOG_vX.X.X.md`
- [ ] Ejecutar tests: `pytest tests/`
- [ ] Verificar no hay errores: `ruff check src/`
- [ ] Formatear código: `ruff format src/`
- [ ] Commit y push de cambios

### Durante Compilación

- [ ] Limpiar builds anteriores: `rm -rf build/ dist/`
- [ ] Compilar en entorno limpio (`.venv` fresh)
- [ ] Verificar que app arranca correctamente
- [ ] Probar funcionalidades críticas:
  - [ ] Crear/editar profesores
  - [ ] Generar guardias
  - [ ] Exportar/importar datos
  - [ ] Crear PDF

### Después de Compilar

- [ ] Generar checksums SHA-256
- [ ] Probar instaladores en sistemas limpios
- [ ] Crear tag de git: `git tag -a vX.X.X -m "..."`
- [ ] Push tag: `git push origin vX.X.X`
- [ ] Crear GitHub Release
- [ ] Subir instaladores y checksums
- [ ] Publicar release notes

### Validación Final

- [ ] Descargar instaladores desde GitHub
- [ ] Verificar checksums
- [ ] Instalar en máquinas de prueba
- [ ] Ejecutar smoke tests
- [ ] Notificar a usuarios (si aplica)

---

## 📊 Tamaños Esperados

| Plataforma | Tamaño App | Tamaño Instalador |
|------------|------------|-------------------|
| macOS      | ~180 MB    | ~60 MB (DMG)      |
| Windows    | ~150 MB    | ~50 MB (Setup)    |

---

## 🔗 Referencias

- **PyInstaller:** https://pyinstaller.org/
- **create-dmg:** https://github.com/create-dmg/create-dmg
- **Inno Setup:** https://jrsoftware.org/isinfo.php
- **GitHub Releases:** https://docs.github.com/en/repositories/releasing-projects-on-github

---

**Última actualización:** 1 de Noviembre de 2025  
**Versión actual:** v2.9.1
