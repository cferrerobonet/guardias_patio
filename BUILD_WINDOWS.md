# 📦 Construcción de Instalador para Windows

Este directorio contiene los scripts necesarios para crear un instalador EXE profesional de **Guardias de Patio** para Windows.

## 🚀 Inicio Rápido

### Opción 1: Script Batch (Recomendado para principiantes)

```batch
build_windows.bat
```

### Opción 2: Script PowerShell (Instalador completo)

```powershell
.\build_windows.ps1
```

El instalador estará en `dist/GuardiasDePatio-2.7.0-Windows-Setup.exe`

## 📋 Requisitos

### Software Necesario

1. **Python 3.11 o superior**
   - Descargar de: https://www.python.org/downloads/
   - ✅ Marcar "Add Python to PATH" durante instalación

2. **PyInstaller** (se instala automáticamente)
   ```bash
   pip install pyinstaller
   ```

3. **Inno Setup 6** (para crear instalador)
   - Descargar de: https://jrsoftware.org/isdl.php
   - Instalar con opciones predeterminadas

### Espacio en Disco

- Aproximadamente 500 MB libres durante el proceso
- El instalador final: ~50-80 MB

## 🛠️ Proceso de Construcción

### Paso 1: Crear el ejecutable

```batch
# Con batch
build_windows.bat

# O con PowerShell
.\build_windows.ps1
```

Esto creará:
- `dist/GuardiasDePatio/GuardiasDePatio.exe` - Ejecutable principal
- `dist/GuardiasDePatio/*` - Archivos de soporte

### Paso 2: Crear el instalador (si tienes Inno Setup)

**Opción A - Automático (PowerShell):**
```powershell
.\build_windows.ps1
```

**Opción B - Manual:**
1. Abre `installer_windows.iss` con Inno Setup
2. Click en menú: **Build** → **Compile**
3. El instalador se creará en `dist/`

## 📁 Archivos Importantes

### Scripts de Build

- **`build_windows.bat`** - Script batch simple (solo ejecutable)
- **`build_windows.ps1`** - Script PowerShell completo (ejecutable + instalador)
- **`guardias_patio_windows.spec`** - Configuración de PyInstaller
- **`installer_windows.iss`** - Script de Inno Setup
- **`version_info.txt`** - Información de versión del EXE

### Configuración

#### guardias_patio_windows.spec

Configuración de PyInstaller para Windows:

```python
# Icono de Windows
icon='imagenes/logo.ico'

# Sin consola
console=False

# Archivos incluidos
datas=[
    ('imagenes', 'imagenes'),
    ('alembic.ini', '.'),
    ('alembic', 'alembic'),
]
```

#### installer_windows.iss

Configuración del instalador:

```ini
AppName=Guardias de Patio
AppVersion=2.7.0
DefaultDirName={autopf}\Guardias de Patio
OutputBaseFilename=GuardiasDePatio-2.7.0-Windows-Setup
```

## 🎯 Características del Instalador

### Lo que incluye:

✅ **Instalación visual** - Wizard profesional en español/inglés  
✅ **Icono en escritorio** - Opcional durante instalación  
✅ **Menú inicio** - Acceso directo automático  
✅ **Desinstalador** - Incluido automáticamente  
✅ **Base de datos** - SQLite embebido  
✅ **Sin dependencias** - Incluye Python y librerías  

### Opciones de instalación:

- Instalación por usuario (no requiere admin)
- Crear icono en escritorio (opcional)
- Crear acceso rápido (opcional)
- Idioma: Español o Inglés

## 📦 Distribución

### Tamaños Esperados

- **Ejecutable portable**: ~120 MB (carpeta dist/GuardiasDePatio/)
- **Instalador comprimido**: ~50-80 MB (.exe)

### Métodos de Distribución

1. **GitHub Releases** (Recomendado)
   ```bash
   # Crear release y subir instalador
   ```

2. **Descarga directa**
   - Subir a servidor web
   - Compartir link de descarga

3. **USB/Red local**
   - Copiar instalador directamente

### Firma Digital (Opcional)

Para evitar advertencias de Windows SmartScreen:

1. **Obtener certificado de código**
   - Comprar de: DigiCert, Sectigo, etc. (~$150-400/año)
   
2. **Firmar el ejecutable**
   ```bash
   signtool sign /f certificado.pfx /p password /t http://timestamp.digicert.com GuardiasDePatio.exe
   ```

3. **Firmar el instalador**
   ```bash
   signtool sign /f certificado.pfx /p password GuardiasDePatio-2.7.0-Windows-Setup.exe
   ```

## 🐛 Troubleshooting

### Error: "Python no encontrado"

**Solución:**
1. Instala Python desde python.org
2. Marca "Add Python to PATH"
3. Reinicia PowerShell/CMD

### Error: "PyInstaller not found"

**Solución:**
```bash
pip install pyinstaller
```

### Error: "No se puede importar PyQt6"

**Solución:**
```bash
pip install PyQt6
pip install -r requirements.txt
```

### El ejecutable no abre

**Posibles causas:**

1. **Antivirus bloqueando**
   - Agregar excepción en Windows Defender
   - Temporal: Desactivar antivirus durante prueba

2. **Falta Visual C++ Redistributable**
   - Descargar de: https://aka.ms/vs/17/release/vc_redist.x64.exe

3. **Logs de error**
   - Ejecutar desde CMD para ver errores:
     ```bash
     cd dist\GuardiasDePatio
     GuardiasDePatio.exe
     ```

### El instalador marca "No es seguro"

**Causa:** Instalador sin firma digital

**Solución temporal:**
1. Click en "Más información"
2. Click en "Ejecutar de todas formas"

**Solución permanente:**
- Firmar con certificado de código (ver sección Firma Digital)

### El instalador es muy grande

**Optimizaciones:**

1. **Excluir paquetes innecesarios** en `guardias_patio_windows.spec`:
   ```python
   excludes=[
       'matplotlib',
       'numpy', 
       'pandas',
       'tkinter',
   ]
   ```

2. **Usar UPX** (ya incluido):
   ```python
   upx=True
   ```

3. **Comprimir más en Inno Setup** en `installer_windows.iss`:
   ```ini
   Compression=lzma2/ultra64
   ```

## 🔧 Personalización

### Cambiar versión

Editar en 3 archivos:

1. **guardias_patio_windows.spec:**
   ```python
   version='version_info.txt'
   ```

2. **version_info.txt:**
   ```python
   filevers=(2, 7, 0, 0),
   prodvers=(2, 7, 0, 0),
   ```

3. **installer_windows.iss:**
   ```ini
   #define MyAppVersion "2.7.0"
   ```

### Cambiar icono

Reemplazar `imagenes/logo.ico` con tu propio icono:

- Formato: ICO
- Tamaños recomendados: 16x16, 32x32, 48x48, 256x256
- Herramienta: IcoFX, GIMP, o convertidores online

### Agregar archivos al instalador

Editar `installer_windows.iss`:

```ini
[Files]
Source: "dist\GuardiasDePatio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "mi_archivo.txt"; DestDir: "{app}"; Flags: ignoreversion
```

## 📊 Comparación: Ejecutable vs Instalador

| Característica | Ejecutable Portable | Instalador EXE |
|---|---|---|
| **Tamaño** | ~120 MB (carpeta) | ~50-80 MB (comprimido) |
| **Instalación** | Copiar carpeta | Wizard profesional |
| **Desinstalar** | Borrar carpeta | Panel de control |
| **Usuarios** | Técnicos | Usuarios finales |
| **Actualizaciones** | Manual | Puede ser automático |
| **Registro Windows** | No | Sí |

## 🎓 Guía de Uso para Usuarios

### Instalación

1. Descargar `GuardiasDePatio-2.7.0-Windows-Setup.exe`
2. Hacer doble clic
3. Seguir el asistente de instalación
4. Elegir carpeta de destino (predeterminada: `C:\Program Files\Guardias de Patio`)
5. Marcar opciones (icono escritorio, etc.)
6. Click en "Instalar"
7. Al finalizar, marcar "Ejecutar Guardias de Patio"

### Primer uso

1. La aplicación creará la base de datos automáticamente
2. Configurar datos iniciales
3. Comenzar a usar

### Desinstalación

**Opción 1 - Panel de Control:**
1. Ir a Panel de Control → Programas
2. Buscar "Guardias de Patio"
3. Click en "Desinstalar"

**Opción 2 - Desde el menú inicio:**
1. Buscar "Guardias de Patio" en el menú inicio
2. Click en "Desinstalar Guardias de Patio"

## 📚 Referencias

- [PyInstaller Documentation](https://pyinstaller.org/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [Windows Code Signing](https://learn.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [PyQt6 Deployment](https://www.riverbankcomputing.com/static/Docs/PyQt6/deployment.html)

## ⚡ Script Rápido de Prueba

Para probar solo el ejecutable sin crear instalador:

```batch
@echo off
python -m PyInstaller --noconfirm --clean ^
  --name "GuardiasDePatio" ^
  --windowed ^
  --icon "imagenes/logo.ico" ^
  --add-data "imagenes;imagenes" ^
  --add-data "alembic.ini;." ^
  --add-data "alembic;alembic" ^
  src/main.py

echo.
echo Ejecutable creado en: dist\GuardiasDePatio\
echo.
pause
```

Guardar como `quick_build.bat` y ejecutar.
