# 📦 Construcción de DMG para macOS

Este directorio contiene los scripts necesarios para crear un instalador DMG de **Guardias de Patio** para macOS.

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias de build
make install

# 2. Crear el DMG completo
make dmg
```

El archivo DMG estará en `dist/GuardiasDePatio-2.7.0-macOS.dmg`

## 📋 Requisitos

- macOS 10.14 (Mojave) o superior
- Python 3.11
- Xcode Command Line Tools (para `iconutil`)
- Aproximadamente 500 MB de espacio libre

## 🛠️ Comandos Disponibles

### Instalación de herramientas

```bash
make install
```

Instala PyInstaller y otras dependencias necesarias.

### Crear solo el icono

```bash
make icon
```

Convierte `imagenes/logo.png` a `imagenes/icono.icns` con todos los tamaños requeridos por macOS.

### Crear solo la aplicación .app

```bash
make app
```

Genera `dist/Guardias de Patio.app` sin crear el DMG.

### Crear el DMG completo

```bash
make dmg
```

Crea el instalador DMG completo con:
- Aplicación empaquetada
- Link a /Applications
- README con instrucciones
- Interfaz visual mejorada

### Limpiar archivos de build

```bash
make clean
```

Elimina todos los archivos generados (`build/`, `dist/`, etc.)

## 📁 Archivos Importantes

### Scripts

- **`build_dmg.sh`** - Script principal que crea el DMG
- **`create_icon.sh`** - Convierte PNG a ICNS
- **`guardias_patio.spec`** - Configuración de PyInstaller
- **`Makefile`** - Automatización de comandos

### Configuración

El archivo `guardias_patio.spec` contiene la configuración de PyInstaller:

- **Hidden imports**: Módulos que PyInstaller no detecta automáticamente
- **Data files**: Archivos adicionales (imágenes, alembic, etc.)
- **Bundle info**: Metadatos de la aplicación (versión, nombre, icono)
- **Exclusiones**: Paquetes innecesarios (matplotlib, numpy, etc.)

## 🔧 Personalización

### Cambiar versión

Edita en `guardias_patio.spec`:

```python
version='2.7.0',  # Cambiar aquí
```

Y en `build_dmg.sh`:

```bash
VERSION="2.7.0"  # Cambiar aquí
```

### Cambiar icono

Reemplaza `imagenes/logo.png` con tu propio logo (recomendado 1024x1024 px) y ejecuta:

```bash
make icon
```

### Agregar archivos adicionales

Edita `guardias_patio.spec` en la sección `added_files`:

```python
added_files = [
    ('imagenes', 'imagenes'),
    ('nuevo_archivo.txt', '.'),  # Agregar aquí
]
```

## 📦 Distribución

### Sin firma digital

El DMG se puede distribuir directamente, pero los usuarios verán una advertencia de seguridad la primera vez que lo abran.

Instrucciones para usuarios:
1. Descargar el DMG
2. Abrir el DMG
3. Arrastrar "Guardias de Patio.app" a Applications
4. Al intentar abrir, ir a **Preferencias del Sistema > Privacidad y Seguridad**
5. Hacer click en "Abrir de todas formas"

### Con firma digital (Opcional)

Para evitar advertencias de seguridad, necesitas:

1. **Cuenta de Apple Developer** ($99/año)
2. **Certificado de desarrollador**

```bash
# Firmar la aplicación
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Tu Nombre" \
  "dist/Guardias de Patio.app"

# Firmar el DMG
codesign --force --verify --verbose \
  --sign "Developer ID Application: Tu Nombre" \
  "dist/GuardiasDePatio-2.7.0-macOS.dmg"

# Notarizar con Apple
xcrun notarytool submit \
  "dist/GuardiasDePatio-2.7.0-macOS.dmg" \
  --apple-id "tu@email.com" \
  --team-id "TU_TEAM_ID" \
  --password "app-specific-password"
```

## 🐛 Troubleshooting

### Error: "PyInstaller not found"

```bash
make install
```

### Error: "iconutil: command not found"

Instala Xcode Command Line Tools:

```bash
xcode-select --install
```

### La aplicación no abre

Verifica los logs:

```bash
open dist/Guardias\ de\ Patio.app
# Revisa Console.app para ver errores
```

### Falta algún módulo

Agrega el import oculto en `guardias_patio.spec`:

```python
hidden_imports = [
    'modulo_faltante',
]
```

### El DMG es muy grande

Revisa las exclusiones en `guardias_patio.spec`:

```python
excludes=[
    'matplotlib',  # ~50 MB
    'numpy',       # ~20 MB
    'pandas',      # ~30 MB
]
```

## 📊 Tamaño Estimado

- **Aplicación .app**: ~150-200 MB
- **DMG comprimido**: ~80-100 MB

## ⚡ Optimización

Para reducir el tamaño:

1. Usa `--onefile` en PyInstaller (ya incluido)
2. Excluye paquetes innecesarios
3. Comprime el DMG con máxima compresión (ya incluido)
4. Usa UPX para comprimir binarios (ya incluido)

## 🎯 Próximos pasos

Después de crear el DMG:

1. ✅ Prueba el DMG en un Mac limpio
2. ✅ Verifica que la aplicación funciona correctamente
3. ✅ Prueba la instalación arrastrando a Applications
4. 📝 Crea release notes
5. 🚀 Distribuye a través de GitHub Releases
6. 💬 Comunica a usuarios

## 📚 Referencias

- [PyInstaller Documentation](https://pyinstaller.org/)
- [macOS App Bundle](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html)
- [Code Signing Guide](https://developer.apple.com/support/code-signing/)
- [Notarization for macOS](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
