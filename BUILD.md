# 📦 Guía de Construcción de Instaladores

**Guardias de Patio** puede empaquetarse como instalador nativo para **macOS** y **Windows**.

## 🍎 macOS - Instalador DMG

### Construcción rápida

```bash
make dmg
```

### Resultado

- **Archivo:** `dist/GuardiasDePatio-2.7.0-macOS.dmg`
- **Tamaño:** ~82 MB
- **Compatibilidad:** macOS 10.14 (Mojave) o superior

### Características

✅ Aplicación .app nativa  
✅ Instalación drag & drop  
✅ Icono personalizado  
✅ Link a carpeta Applications  
✅ README incluido  

### Documentación completa

👉 **[BUILD_DMG.md](BUILD_DMG.md)**

---

## 🪟 Windows - Instalador EXE

### Construcción

**Desde Windows:**

```batch
REM Opción 1: Solo ejecutable
build_windows.bat

REM Opción 2: Instalador completo
build_windows.ps1
```

### Resultado

- **Ejecutable:** `dist/GuardiasDePatio/GuardiasDePatio.exe`
- **Instalador:** `dist/GuardiasDePatio-2.7.0-Windows-Setup.exe`
- **Tamaño:** ~50-80 MB (instalador comprimido)
- **Compatibilidad:** Windows 10/11

### Características

✅ Instalador profesional con Inno Setup  
✅ Wizard en español/inglés  
✅ Icono en escritorio (opcional)  
✅ Menú inicio  
✅ Desinstalador incluido  
✅ Sin dependencias externas  

### Requisitos

- Python 3.11+
- PyInstaller (se instala automáticamente)
- Inno Setup 6 (para crear instalador)

### Documentación completa

👉 **[BUILD_WINDOWS.md](BUILD_WINDOWS.md)**

---

## 🐧 Linux - AppImage (Futuro)

En desarrollo. Puedes ejecutar directamente con:

```bash
python3 src/main.py
```

---

## 📋 Comparación de Instaladores

| Característica | macOS DMG | Windows EXE |
|---|---|---|
| **Tamaño comprimido** | ~82 MB | ~50-80 MB |
| **Instalación** | Drag & drop | Wizard |
| **Desinstalación** | Arrastrar a papelera | Panel de control |
| **Firma digital** | Apple Developer ($99/año) | Certificado código (~$300/año) |
| **Distribución** | GitHub Releases, web | GitHub Releases, web |

---

## 🚀 Comandos Rápidos

### macOS

```bash
make install    # Instalar dependencias
make dmg        # Crear DMG completo
make clean      # Limpiar builds
```

### Windows

```batch
build_windows.bat     :: Solo ejecutable
build_windows.ps1     :: Instalador completo
```

---

## 📤 Distribución

### 1. GitHub Releases (Recomendado)

```bash
# Crear tag
git tag v2.7.0
git push origin v2.7.0

# En GitHub:
# - Ir a Releases
# - Create new release
# - Subir archivos DMG/EXE como assets
```

### 2. Servidor web

Sube los instaladores a tu servidor y comparte el link.

### 3. Email/USB

Los instaladores son autocontenidos, puedes compartirlos directamente.

---

## 🔒 Firma Digital (Opcional)

### macOS

**Requisitos:**
- Cuenta Apple Developer ($99/año)
- Certificado "Developer ID Application"

**Proceso:**
```bash
# Firmar
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Tu Nombre" \
  "dist/Guardias de Patio.app"

# Notarizar
xcrun notarytool submit dist/GuardiasDePatio-2.7.0-macOS.dmg \
  --apple-id "tu@email.com" \
  --team-id "TEAM_ID" \
  --password "app-password"
```

### Windows

**Requisitos:**
- Certificado de código (~$150-400/año)
- SignTool (incluido en Windows SDK)

**Proceso:**
```batch
signtool sign /f certificado.pfx /p password /t http://timestamp.digicert.com GuardiasDePatio.exe
```

---

## 🐛 Troubleshooting

### macOS

**Error: "PyInstaller not found"**
```bash
make install
```

**El DMG no se monta**
- Verificar permisos de Gatekeeper
- Sistema > Privacidad y Seguridad

### Windows

**Error: "Python no encontrado"**
- Instalar Python desde python.org
- Marcar "Add to PATH"

**Antivirus bloquea el EXE**
- Agregar excepción temporal
- O firmar con certificado

---

## 📚 Documentación Completa

- 🍎 **[BUILD_DMG.md](BUILD_DMG.md)** - Construcción para macOS
- 🪟 **[BUILD_WINDOWS.md](BUILD_WINDOWS.md)** - Construcción para Windows
- 🛠️ **Makefile** - Comandos automatizados (macOS)

---

## 💡 Consejos

### Para desarrollo

Usa el código fuente directamente:
```bash
python3 src/main.py
```

### Para distribución

Crea los instaladores nativos para mejor experiencia de usuario.

### Para pruebas

Prueba los instaladores en máquinas limpias antes de distribuir.

---

## 📊 Tamaños Aproximados

```
Código fuente:         ~5 MB
Dependencias:         ~100 MB
────────────────────────────
DMG comprimido:       ~82 MB
EXE instalador:       ~50-80 MB
App portable (Win):   ~120 MB
```

---

## ✨ Próximos Pasos

1. ✅ Crear instaladores
2. 🧪 Probar en máquinas limpias
3. 📝 Crear release en GitHub
4. 📤 Distribuir a usuarios
5. 💬 Recopilar feedback
6. 🔄 Iterar y mejorar

---

## 🆘 Soporte

Para problemas o preguntas:

- 📖 Lee la documentación completa
- 🐛 Abre un issue en GitHub
- 💬 Consulta en el repositorio

---

**¡Buena suerte con la distribución de Guardias de Patio!** 🎉
