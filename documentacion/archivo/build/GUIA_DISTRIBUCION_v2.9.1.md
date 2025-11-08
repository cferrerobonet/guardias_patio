# Guía de Distribución - Guardias de Patio v2.9.1

Esta guía documenta los pasos para compilar y distribuir la versión 2.9.1 de Guardias de Patio.

## 📦 Archivos de distribución generados

### macOS
- **Archivo**: `GuardiasPatio_v2.9.1_macOS.dmg`
- **Tamaño**: 68 MB
- **Ubicación**: Raíz del proyecto
- **Arquitectura**: ARM64 (Apple Silicon) + compatibilidad Intel vía Rosetta 2

### Windows
- **Archivo**: `GuardiasPatio_v2.9.1_Windows_Setup.exe`
- **Estado**: ⚠️ Pendiente de compilación
- **Requiere**: PC con Windows o VM

## 🔨 Proceso de compilación (macOS)

### Prerrequisitos
```bash
# Instalar PyInstaller (si no está instalado)
pip install pyinstaller
```

### Compilación
```bash
# Ejecutar el script de build
chmod +x build_dmg.sh
./build_dmg.sh
```

### Resultado
```bash
# Verificar el DMG generado
ls -lh GuardiasPatio_v2.9.1_macOS.dmg

# Resultado esperado:
# -rw-r--r--  1 user  staff   68M Oct 31 16:45 GuardiasPatio_v2.9.1_macOS.dmg
```

### Firma de código (opcional pero recomendado)

Para evitar warnings de seguridad en macOS:

```bash
# 1. Obtener un certificado de desarrollador de Apple
#    https://developer.apple.com/account/

# 2. Firmar la aplicación
codesign --force --deep --sign "Developer ID Application: TU NOMBRE" \
  "dist/Guardias de Patio.app"

# 3. Verificar la firma
codesign --verify --deep --strict --verbose=2 \
  "dist/Guardias de Patio.app"

# 4. Notarizar con Apple (requiere cuenta de desarrollador)
xcrun notarytool submit GuardiasPatio_v2.9.1_macOS.dmg \
  --apple-id "tu@email.com" \
  --password "app-specific-password" \
  --team-id "TU_TEAM_ID" \
  --wait
```

## 🪟 Compilación para Windows

### Desde Windows (recomendado)

```powershell
# Ejecutar en PowerShell
.\build_windows.ps1
```

### Desde macOS usando Wine (alternativa)

```bash
# Instalar Wine
brew install wine-stable

# Configurar entorno Windows
# ... (documentar pasos completos si es necesario)
```

## 📤 Distribución en GitHub

### 1. Crear tag de versión

```bash
git tag -a v2.9.1 -m "Release v2.9.1: Optimizaciones de rendimiento + calendario 2025-2026"
git push origin v2.9.1
```

### 2. Crear GitHub Release

1. Ve a: https://github.com/cferrerobonet/guardias_patio/releases/new
2. Selecciona el tag: `v2.9.1`
3. Título: `Guardias de Patio v2.9.1`
4. Descripción: Copiar de `RELEASE_NOTES_v2.9.1.md`
5. Subir archivos:
   - `GuardiasPatio_v2.9.1_macOS.dmg`
   - `GuardiasPatio_v2.9.1_Windows_Setup.exe` (cuando esté disponible)
   - `RELEASE_NOTES_v2.9.1.md`
6. Marcar como "Latest release"
7. Publicar

### 3. Checksums (seguridad)

Generar checksums para verificación de integridad:

```bash
# SHA256 checksums
shasum -a 256 GuardiasPatio_v2.9.1_macOS.dmg > checksums.txt

# Añadir Windows cuando esté disponible
shasum -a 256 GuardiasPatio_v2.9.1_Windows_Setup.exe >> checksums.txt

# Subir checksums.txt al release
```

## ✅ Checklist de release

### Antes de compilar
- [x] Actualizar número de versión en código
- [x] Actualizar CHANGELOG
- [x] Ejecutar tests
- [x] Verificar que no hay errores de linting
- [x] Commit y push de todos los cambios

### Durante compilación
- [x] Compilar macOS: ✅ DMG creado (68 MB)
- [ ] Compilar Windows: ⚠️ Pendiente
- [ ] Firmar aplicaciones (opcional)
- [ ] Probar instaladores en sistemas limpios

### Post-compilación
- [ ] Probar DMG en macOS limpio
- [ ] Probar instalador Windows en Windows limpio
- [ ] Verificar que la app se ejecuta correctamente
- [ ] Verificar que se pueden cargar bases de datos existentes
- [ ] Verificar que se pueden regenerar guardias

### GitHub Release
- [ ] Crear tag v2.9.1
- [ ] Crear GitHub Release
- [ ] Subir archivos de distribución
- [ ] Subir checksums
- [ ] Publicar release notes
- [ ] Actualizar README con link al release

### Comunicación
- [ ] Anunciar en redes sociales (si aplica)
- [ ] Notificar a usuarios existentes
- [ ] Actualizar sitio web (si aplica)

## 🧪 Pruebas de distribución

### macOS - Pruebas mínimas

```bash
# 1. Montar el DMG
open GuardiasPatio_v2.9.1_macOS.dmg

# 2. Arrastrar a Applications

# 3. Ejecutar la aplicación
open "/Applications/Guardias de Patio.app"

# 4. Verificar funcionalidades:
#    - Login
#    - Cargar BD existente
#    - Ver guardias
#    - Regenerar guardias (verificar 2768 guardias)
#    - Exportar PDF
```

### Windows - Pruebas mínimas

```powershell
# 1. Ejecutar instalador
.\GuardiasPatio_v2.9.1_Windows_Setup.exe

# 2. Seguir asistente de instalación

# 3. Ejecutar desde menú Inicio

# 4. Verificar mismas funcionalidades que macOS
```

## 📊 Métricas de rendimiento

Documentar resultados de benchmark:

```bash
# Ejecutar benchmark
python scripts/benchmark_optimizaciones.py --db-id 66f06c9433d74e80

# Resultados esperados:
# - Tiempo total: 2.5-4 min (vs 8-12 min en v2.9.0)
# - Guardias generadas: 2768
# - Cobertura: 100%
# - Equidad: 0 grupos inequitativos
```

## 🔄 Rollback (si es necesario)

Si se encuentra un problema crítico después del release:

```bash
# 1. Marcar el release como "Pre-release"
# 2. Añadir nota de warning
# 3. Investigar y corregir
# 4. Compilar v2.9.2 con el fix
# 5. Distribuir v2.9.2
```

## 📝 Notas adicionales

### Tamaño de los instaladores

- **macOS DMG**: ~68 MB
  - Incluye: Python runtime, PyQt6, SQLAlchemy, ReportLab, etc.
  - Comprimido con UDZO (zlib)
  
- **Windows EXE**: ~50-70 MB (estimado)
  - Incluye: Similar al macOS

### Compatibilidad

- **macOS**: 
  - Mínimo: macOS 11.0 (Big Sur)
  - Arquitectura: ARM64 (Apple Silicon) nativo
  - Intel: Funciona vía Rosetta 2

- **Windows**:
  - Mínimo: Windows 10
  - Arquitectura: x64

### Soporte post-release

- **Issues de GitHub**: Responder en < 48 horas
- **Bugs críticos**: Hotfix en < 1 semana
- **Bugs menores**: Incluir en próximo release

---

**Última actualización**: 31 de octubre de 2025
**Responsable**: Carlos Ferrero Bonet
