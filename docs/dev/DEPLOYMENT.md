# 🚀 Guía de Despliegue - Guardias de Patio

**Versión**: 3.0.0  
**Última actualización**: 8 de noviembre de 2025  
**Plataformas**: macOS | Windows

---

## 📚 Tabla de Contenidos

1. [Requisitos Previos](#1-requisitos-previos)
2. [Configuración del Entorno](#2-configuración-del-entorno)
3. [Build para Desarrollo](#3-build-para-desarrollo)
4. [Build para Producción](#4-build-para-producción)
   - [4.1 macOS (DMG)](#41-macos-dmg)
   - [4.2 Windows (EXE/MSI)](#42-windows-exemsi)
5. [Testing Pre-Release](#5-testing-pre-release)
6. [Distribución](#6-distribución)
   - [6.1 GitHub Releases](#61-github-releases)
   - [6.2 Instalación Manual](#62-instalación-manual)
7. [Troubleshooting](#7-troubleshooting)
8. [Checklist de Release](#8-checklist-de-release)
9. [Referencias](#9-referencias)

---

## 1. Requisitos Previos

### 💻 Hardware Mínimo

- **Procesador**: Intel i5 o equivalente
- **RAM**: 8 GB
- **Espacio**: 5 GB libres (incluye dependencias y builds)

### 🖥️ macOS

| Componente | Requisito |
|------------|-----------|
| **Sistema** | macOS 11.0 (Big Sur) o superior |
| **Xcode CLI** | `xcode-select --install` |
| **Python** | 3.11.14 (desde python.org o brew) |
| **Homebrew** | Para dependencias adicionales |
| **create-dmg** | `brew install create-dmg` |

### 🪟 Windows

| Componente | Requisito |
|------------|-----------|
| **Sistema** | Windows 10/11 (64-bit) |
| **Python** | 3.11.14 desde [python.org](https://www.python.org/downloads/) |
| **Visual C++** | [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
| **Inno Setup** | 6.x para crear instalador ([download](https://jrsoftware.org/isdl.php)) |

### 📦 Herramientas de Build

```bash
# PyInstaller (todas las plataformas)
pip install pyinstaller==6.3.0

# Verificar instalación
pyinstaller --version
```

---

## 2. Configuración del Entorno

### Clonar Repositorio

```bash
git clone https://github.com/cferrerobonet/guardias_patio.git
cd "guardias_patio"
```

### Crear Entorno Virtual

**macOS/Linux**:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Windows**:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Instalar Dependencias

```bash
# Instalar requirements
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalaciones críticas
python -c "import PyQt6; print('PyQt6:', PyQt6.QtCore.PYQT_VERSION_STR)"
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
```

### Verificar Versión

```bash
# Leer versión actual
cat version_info.txt

# Actualizar versión (si es necesario)
# Editar VERSION= en version_info.txt
```

**Formato version_info.txt**:
```ini
VERSION="3.0.0"
BUILD_NUMBER="250"
RELEASE_DATE="2025-11-08"
```

---

## 3. Build para Desarrollo

### Ejecutar desde Código Fuente

**macOS/Linux**:
```bash
source .venv/bin/activate
python src/main.py
```

**Windows**:
```powershell
.venv\Scripts\activate
python src/main.py
```

### Build Rápido (Testing)

**macOS**:
```bash
# Build sin optimizaciones
pyinstaller --onefile --windowed src/main.py

# Ejecutar
./dist/main.app/Contents/MacOS/main
```

**Windows**:
```powershell
# Build sin optimizaciones
pyinstaller --onefile --windowed src/main.py

# Ejecutar
.\dist\main.exe
```

### Hot Reload para Desarrollo

```bash
# Instalar watchdog
pip install watchdog

# Script de auto-reload (opcional)
# Ver: scripts/dev/watch_and_reload.py
```

---

## 4. Build para Producción

### 4.1 macOS (DMG)

#### Paso 1: Limpiar Builds Anteriores

```bash
rm -rf build/ dist/ *.spec
```

#### Paso 2: Compilar Aplicación

**Usando script automatizado** (recomendado):
```bash
./scripts/build/build_simple.sh
```

**Comando manual**:
```bash
pyinstaller \
    --name="Guardias de Patio" \
    --windowed \
    --onedir \
    --icon=imagenes/icons/app_icon.icns \
    --add-data="imagenes:imagenes" \
    --add-data="version_info.txt:." \
    --osx-bundle-identifier=com.guardias.patio \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=sqlalchemy \
    --hidden-import=sqlalchemy.orm \
    --collect-all=PyQt6 \
    --noconfirm \
    src/main.py
```

**Resultado**: `dist/Guardias de Patio.app/`

#### Paso 3: Crear DMG

**Usando script automatizado**:
```bash
./scripts/build/create_dmg.sh
```

**Comando manual**:
```bash
VERSION=$(cat version_info.txt | grep "VERSION" | cut -d'=' -f2 | tr -d ' "')
APP_NAME="Guardias de Patio"
DMG_NAME="GuardiasPatio_v${VERSION}_macOS.dmg"

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
```

**Resultado**: `GuardiasPatio_v3.0.0_macOS.dmg`

#### Paso 4: Firmar App (Opcional - Requiere Developer ID)

```bash
# Firmar aplicación
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Tu Nombre" \
    "dist/Guardias de Patio.app"

# Verificar firma
codesign --verify --deep --strict --verbose=2 \
    "dist/Guardias de Patio.app"

# Notarizar con Apple (requiere Apple ID de desarrollador)
xcrun notarytool submit "GuardiasPatio_v3.0.0_macOS.dmg" \
    --apple-id "tu@email.com" \
    --team-id "TEAM_ID" \
    --password "app-specific-password" \
    --wait
```

---

### 4.2 Windows (EXE/MSI)

#### Paso 1: Limpiar Builds Anteriores

```powershell
Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue
```

#### Paso 2: Compilar Ejecutable

**Usando script automatizado** (recomendado):
```powershell
.\scripts\build\build_windows.bat
```

**Comando manual**:
```powershell
pyinstaller `
    --name="Guardias de Patio" `
    --windowed `
    --onefile `
    --icon=imagenes\icons\app_icon.ico `
    --add-data="imagenes;imagenes" `
    --add-data="version_info.txt;." `
    --hidden-import=PyQt6.QtCore `
    --hidden-import=PyQt6.QtGui `
    --hidden-import=PyQt6.QtWidgets `
    --hidden-import=sqlalchemy `
    --hidden-import=sqlalchemy.orm `
    --collect-all=PyQt6 `
    --noconfirm `
    --version-file=version_info.txt `
    src\main.py
```

**Resultado**: `dist\Guardias de Patio.exe`

#### Paso 3: Crear Instalador con Inno Setup

**Archivo**: `installer_windows.iss`

```inno
; Guardias de Patio - Windows Installer Script
[Setup]
AppName=Guardias de Patio
AppVersion=3.0.0
DefaultDirName={autopf}\GuardiasPatio
DefaultGroupName=Guardias de Patio
OutputDir=Output
OutputBaseFilename=GuardiasPatio_Setup_v3.0.0
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\Guardias de Patio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "imagenes\*"; DestDir: "{app}\imagenes"; Flags: ignoreversion recursesubdirs
Source: "version_info.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Guardias de Patio"; Filename: "{app}\Guardias de Patio.exe"
Name: "{autodesktop}\Guardias de Patio"; Filename: "{app}\Guardias de Patio.exe"

[Run]
Filename: "{app}\Guardias de Patio.exe"; Description: "Ejecutar Guardias de Patio"; Flags: nowait postinstall skipifsilent
```

**Compilar instalador**:
```powershell
# Usando Inno Setup Compiler
iscc installer_windows.iss
```

**Resultado**: `Output\GuardiasPatio_Setup_v3.0.0.exe`

#### Paso 4: Firmar Ejecutable (Opcional - Requiere Certificado)

```powershell
# Firmar EXE con certificado de código
signtool sign /f "tu_certificado.pfx" /p "contraseña" /t "http://timestamp.digicert.com" "dist\Guardias de Patio.exe"

# Verificar firma
signtool verify /pa "dist\Guardias de Patio.exe"
```

---

## 5. Testing Pre-Release

### Checklist de Testing Manual

#### Funcionalidad Básica
- [ ] La aplicación inicia correctamente
- [ ] Ventana principal se muestra completa
- [ ] Base de datos se crea automáticamente
- [ ] Login/configuración inicial funciona

#### Formularios Principales
- [ ] Alta de profesores
- [ ] Alta de zonas
- [ ] Registro de ausencias
- [ ] Generación de guardias

#### Exportación y Reportes
- [ ] Exportar a PDF funciona
- [ ] Exportar a Excel funciona
- [ ] Calendario iCalendar se genera
- [ ] Envío de emails (si configurado)

#### Rendimiento
- [ ] Carga inicial < 3 segundos
- [ ] Generación de guardias < 5 segundos (100 guardias)
- [ ] Búsquedas en tablas instantáneas
- [ ] No hay memory leaks (uso de RAM estable)

### Testing Automatizado

```bash
# Ejecutar suite de tests
pytest tests/ -v --cov=src --cov-report=term

# Tests de integración
pytest tests/integration/ -v

# Tests de UI (si disponibles)
pytest tests/ui/ -v --qt-api=pyqt6
```

### Testing en Máquinas Limpias

**macOS**:
1. Máquina virtual con macOS limpio
2. Instalar DMG como usuario final
3. Verificar que no requiere dependencias externas
4. Probar todas las funcionalidades

**Windows**:
1. Máquina virtual con Windows limpio
2. Instalar Setup.exe como usuario final
3. Verificar instalación de VC++ Redistributable
4. Probar todas las funcionalidades

---

## 6. Distribución

### 6.1 GitHub Releases

#### Crear Release

1. **Tag de versión**:
```bash
git tag -a v3.0.0 -m "Release v3.0.0 - Refactorización arquitectónica"
git push origin v3.0.0
```

2. **Crear release en GitHub**:
   - Ir a: https://github.com/cferrerobonet/guardias_patio/releases/new
   - Seleccionar tag: `v3.0.0`
   - Título: `v3.0.0 - Refactorización Arquitectónica`
   - Descripción: Ver [CHANGELOG.md](../CHANGELOG.md)

3. **Subir assets**:
   - `GuardiasPatio_v3.0.0_macOS.dmg` (macOS)
   - `GuardiasPatio_Setup_v3.0.0.exe` (Windows)
   - `SHA256SUMS.txt` (checksums)

#### Generar Checksums

```bash
# macOS
shasum -a 256 GuardiasPatio_v3.0.0_macOS.dmg > SHA256SUMS.txt

# Windows
certutil -hashfile GuardiasPatio_Setup_v3.0.0.exe SHA256 >> SHA256SUMS.txt
```

#### Release Notes Template

```markdown
## 🎉 Guardias de Patio v3.0.0

### ✨ Novedades Principales

- Refactorización completa con Clean Architecture
- Nuevo algoritmo de asignación con fechas consecutivas
- Mejoras de rendimiento (3x más rápido)
- Sistema de testing con 46% de cobertura

### 📦 Descargas

- **macOS**: GuardiasPatio_v3.0.0_macOS.dmg (15 MB)
- **Windows**: GuardiasPatio_Setup_v3.0.0.exe (18 MB)

### 📋 Requisitos del Sistema

- **macOS**: 11.0+ (Big Sur o superior)
- **Windows**: 10/11 (64-bit)
- **Resolución**: Mínimo 1280x720, recomendado 1920x1080

### 🔧 Instalación

**macOS**: Abrir DMG y arrastrar a Aplicaciones  
**Windows**: Ejecutar Setup.exe y seguir el asistente

Ver documentación completa: [DEPLOYMENT.md](documentacion/DEPLOYMENT.md)

### ✅ Checksums (SHA256)

```
[copiar contenido de SHA256SUMS.txt]
```

### 🐛 Issues Conocidos

- Ninguno en esta versión

### 📝 Changelog Completo

Ver: [CHANGELOG.md](documentacion/CHANGELOG.md#300---2025-11-08)
```

---

### 6.2 Instalación Manual

#### macOS

**Para usuarios**:
```bash
# 1. Descargar DMG
curl -L -O https://github.com/.../GuardiasPatio_v3.0.0_macOS.dmg

# 2. Verificar checksum (opcional)
shasum -a 256 GuardiasPatio_v3.0.0_macOS.dmg

# 3. Montar DMG
hdiutil attach GuardiasPatio_v3.0.0_macOS.dmg

# 4. Copiar a Aplicaciones
cp -R "/Volumes/Guardias de Patio/Guardias de Patio.app" /Applications/

# 5. Desmontar DMG
hdiutil detach "/Volumes/Guardias de Patio"

# 6. Ejecutar
open "/Applications/Guardias de Patio.app"
```

**Primera ejecución**:
- macOS puede mostrar advertencia de seguridad (app no firmada)
- Ir a: Preferencias del Sistema → Seguridad → "Abrir de todos modos"

#### Windows

**Para usuarios**:
```powershell
# 1. Descargar instalador
# (usar navegador o curl)

# 2. Verificar checksum (opcional)
certutil -hashfile GuardiasPatio_Setup_v3.0.0.exe SHA256

# 3. Ejecutar instalador
.\GuardiasPatio_Setup_v3.0.0.exe

# 4. Seguir asistente de instalación

# 5. Ejecutar desde escritorio o menú inicio
```

**Primera ejecución**:
- Windows Defender puede mostrar advertencia (SmartScreen)
- Hacer clic en "Más información" → "Ejecutar de todos modos"

---

## 7. Troubleshooting

### 🔴 Problemas Comunes

#### Error: "PyInstaller no encuentra módulos"

**Síntomas**:
```
ModuleNotFoundError: No module named 'PyQt6.QtCore'
```

**Solución**:
```bash
# Reinstalar PyQt6
pip uninstall PyQt6
pip install PyQt6==6.7.0

# Limpiar caché de PyInstaller
rm -rf build/ dist/ *.spec
rm -rf ~/.pyinstaller_cache/

# Recompilar con --collect-all
pyinstaller --collect-all=PyQt6 ...
```

#### Error: "App no se ejecuta en macOS"

**Síntomas**:
- App se abre y cierra inmediatamente
- No aparece error visible

**Solución**:
```bash
# Ver logs de crash
Console.app → Informes de fallos

# Ejecutar desde terminal para ver errores
./dist/Guardias\ de\ Patio.app/Contents/MacOS/Guardias\ de\ Patio

# Verificar permisos
chmod +x ./dist/Guardias\ de\ Patio.app/Contents/MacOS/Guardias\ de\ Patio
```

#### Error: "Falta VCRUNTIME140.dll en Windows"

**Síntomas**:
```
Error: VCRUNTIME140.dll not found
```

**Solución**:
```powershell
# Instalar Visual C++ Redistributable
# Descargar de: https://aka.ms/vs/17/release/vc_redist.x64.exe

# O incluir en instalador (Inno Setup)
[Files]
Source: "C:\Windows\System32\vcruntime140.dll"; DestDir: "{app}"
```

#### Error: "DMG no se monta en macOS"

**Síntomas**:
```
hdiutil: attach failed - Resource busy
```

**Solución**:
```bash
# Desmontar todos los volúmenes relacionados
hdiutil detach "/Volumes/Guardias de Patio" -force

# Verificar integridad del DMG
hdiutil verify GuardiasPatio_v3.0.0_macOS.dmg

# Recrear DMG si está corrupto
```

#### Error: "App muy lenta al iniciar"

**Síntomas**:
- Inicio > 10 segundos
- Alto uso de CPU

**Solución**:
```bash
# Usar --onedir en lugar de --onefile
# onefile es más lento porque descomprime en cada inicio

# macOS/Linux
pyinstaller --onedir ...  # Más rápido

# Optimizar imports
# Usar lazy imports donde sea posible
```

---

## 8. Checklist de Release

### Pre-Release (1-2 días antes)

- [ ] **Código**
  - [ ] Todos los tests pasan (`pytest -v`)
  - [ ] Cobertura ≥ 46% (`pytest --cov`)
  - [ ] No hay errores de linting (`ruff check src/`)
  - [ ] No hay warnings de mypy (`mypy src/`)

- [ ] **Versión**
  - [ ] Actualizar `version_info.txt`
  - [ ] Actualizar `CHANGELOG.md` con cambios
  - [ ] Actualizar fecha de release

- [ ] **Documentación**
  - [ ] README.md actualizado
  - [ ] CHANGELOG.md completo
  - [ ] Capturas de pantalla actualizadas (si cambió UI)
  - [ ] Enlaces funcionando

- [ ] **Testing**
  - [ ] Tests automatizados pasan
  - [ ] Testing manual completado
  - [ ] Probado en macOS limpio
  - [ ] Probado en Windows limpio

### Build Day (día de release)

- [ ] **Builds**
  - [ ] Build macOS completado
  - [ ] DMG creado y verificado
  - [ ] Build Windows completado
  - [ ] Instalador creado y verificado

- [ ] **Verificaciones**
  - [ ] Checksums generados
  - [ ] Apps firmadas (si aplica)
  - [ ] Tamaño de archivos razonable (<25MB cada uno)
  - [ ] Instalación limpia exitosa

### Post-Release (mismo día)

- [ ] **Git**
  - [ ] Commit final con versión
  - [ ] Tag creado y pusheado
  - [ ] Branch main actualizado

- [ ] **GitHub**
  - [ ] Release creado en GitHub
  - [ ] Assets subidos
  - [ ] Release notes publicadas
  - [ ] Checksums en descripción

- [ ] **Notificaciones**
  - [ ] Email a usuarios (si aplica)
  - [ ] Anuncio en redes (si aplica)
  - [ ] Documentación de instalación enviada

### Post-Release Follow-up (1-3 días después)

- [ ] **Monitoreo**
  - [ ] Verificar descargas
  - [ ] Revisar issues reportados
  - [ ] Responder preguntas de usuarios

- [ ] **Hotfixes**
  - [ ] Preparar parche si se encuentran bugs críticos
  - [ ] Documentar issues conocidos

---

## 9. Referencias

### 📁 Archivos Relacionados

**En el Proyecto**:
- `version_info.txt` - Versión actual
- `requirements.txt` - Dependencias Python
- `pyproject.toml` - Configuración del proyecto
- `installer_windows.iss` - Script de Inno Setup
- `scripts/build/` - Scripts de build automatizados

**Documentación**:
- [CHANGELOG.md](../CHANGELOG.md) - Historial de cambios
- [TECHNICAL_GUIDE.md](../TECHNICAL_GUIDE.md) - Documentación técnica
- [README.md](../../README.md) - Introducción al proyecto

### 🔗 Enlaces Externos

**Herramientas**:
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [create-dmg GitHub](https://github.com/create-dmg/create-dmg)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)

**Firma de Código**:
- [Apple Developer - Code Signing](https://developer.apple.com/support/code-signing/)
- [Microsoft - Sign Tool](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool)

**Distribución**:
- [GitHub Releases Guide](https://docs.github.com/en/repositories/releasing-projects-on-github)

### 📚 Documentación Archivada

Los siguientes documentos fueron consolidados en esta guía y se mantienen en `documentacion/archivo/build/`:

- `BUILD.md` (4.9 KB)
- `BUILD_DMG.md` (5.1 KB)
- `BUILD_WINDOWS.md` (8.0 KB)
- `GITHUB_RELEASE_INSTRUCTIONS.md` (7.0 KB)
- `GUIA_COMPILACION.md` (9.0 KB)
- `GUIA_DISTRIBUCION_v2.9.1.md` (5.8 KB)
- `README.md` (3.4 KB)

---

## 📝 Notas Finales

### Mejores Prácticas

1. **Siempre testear en máquinas limpias** antes de release público
2. **Generar checksums** para verificar integridad de descargas
3. **Mantener builds reproducibles** (mismas versiones de dependencias)
4. **Documentar cada release** con changelog detallado
5. **Firmar aplicaciones** cuando sea posible (mejora confianza)

### Automatización Futura

Considerar implementar:
- GitHub Actions para builds automáticos en cada tag
- CI/CD completo con testing y distribución automatizada
- Notarización automática para macOS
- Firma automática de Windows con certificado

### Soporte

Para problemas con el proceso de build:
1. Revisar esta documentación completamente
2. Verificar logs de PyInstaller en `build/`
3. Consultar [Issues en GitHub](https://github.com/cferrerobonet/guardias_patio/issues)
4. Crear nuevo issue con detalles completos

---

**Última actualización**: 8 de noviembre de 2025  
**Versión de la guía**: 1.0.0  
**Mantenedor**: Equipo de desarrollo
