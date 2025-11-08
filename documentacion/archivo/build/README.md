# 🏗️ Build y Distribución - Guardias de Patio

Documentación para compilación y distribución de la aplicación.

**Versión:** 3.0.0  
**Última actualización:** 2 de Noviembre de 2025

---

## 📚 Guías de Compilación

### 🚀 Guía Principal
- **[GUIA_COMPILACION.md](GUIA_COMPILACION.md)** - Guía completa consolidada
  - ✅ Compilación rápida (macOS DMG + Windows Setup)
  - ✅ Procesos detallados de build
  - ✅ Troubleshooting (5 problemas comunes)
  - ✅ Checklist pre-release completo

### 📦 Guías Específicas por Plataforma
- **[BUILD.md](BUILD.md)** - Construcción multiplataforma general
- **[BUILD_DMG.md](BUILD_DMG.md)** - Crear instalador DMG para macOS
- **[BUILD_WINDOWS.md](BUILD_WINDOWS.md)** - Crear instalador Setup.exe para Windows

### 🚢 Distribución
- **[GITHUB_RELEASE_INSTRUCTIONS.md](GITHUB_RELEASE_INSTRUCTIONS.md)** - Publicar releases en GitHub
- **[GUIA_DISTRIBUCION_v2.9.1.md](GUIA_DISTRIBUCION_v2.9.1.md)** - Guía de distribución (referencia histórica)

---

## 🛠️ Scripts de Build

Los scripts de compilación están en la raíz del proyecto:

```
scripts/build/
├── build_dmg.sh            # Crear DMG para macOS
├── build_windows.bat       # Crear Setup.exe para Windows  
├── create_dmg.sh           # Script alternativo DMG
└── fix_pyqt6.sh            # Arreglar problemas de PyQt6 en macOS
```

**Uso:**
```bash
# macOS
cd scripts/build
./build_dmg.sh

# Windows
cd scripts\build
build_windows.bat
```

---

## 📋 Checklist Pre-Release

Antes de compilar para distribución:

### 1. Código
- [ ] Todos los tests pasan (`pytest`)
- [ ] No hay errores de linting (`ruff check`)
- [ ] Type checking limpio (`mypy src/`)
- [ ] Version actualizada en `version_info.txt`

### 2. Base de Datos
- [ ] Migraciones de Alembic aplicadas
- [ ] BD de ejemplo limpia
- [ ] Esquema validado

### 3. Configuración
- [ ] `.env.example` actualizado
- [ ] Configuración SMTP validada
- [ ] Configuración SFTP validada

### 4. Documentación
- [ ] README.md actualizado
- [ ] CHANGELOG actualizado
- [ ] Notas de release preparadas

### 5. Compilación
- [ ] Build de macOS funciona
- [ ] Build de Windows funciona
- [ ] Instaladores probados
- [ ] Iconos correctos

---

## 🚨 Problemas Comunes

### macOS: Error de symlinks con PyQt6

**Problema:** PyInstaller falla con error de symlinks en PyQt6

**Solución:**
```bash
cd scripts/build
./fix_pyqt6.sh
```

### Windows: Falta vcredist

**Problema:** App no inicia en Windows sin Visual C++ Redistributable

**Solución:** Incluir en el instalador o instruir usuarios a instalar:
```
https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### macOS: Firma de código

**Problema:** macOS Gatekeeper bloquea la app

**Solución (temporal):**
```bash
xattr -cr "Guardias de Patio.app"
```

**Solución (permanente):** Firmar con certificado de desarrollador Apple

---

## 📊 Tamaños Típicos de Build

| Plataforma | Tamaño DMG/Setup | Tamaño Instalado |
|------------|------------------|------------------|
| macOS (DMG) | ~100 MB | ~250 MB |
| Windows (Setup.exe) | ~80 MB | ~200 MB |

---

## 🔗 Ver También

- [Documentación Principal](../README.md)
- [Requisitos del Sistema](../tecnico/REQUISITOS_SISTEMA.md)
- [Changelog v3.0](../versiones/CHANGELOG_v3.0.md)

---

**Nota:** Para desarrollo y debug, NO uses estos scripts. Solo para distribución.

**Proyecto:** Guardias de Patio  
**Versión:** 3.0.0  
**Última actualización:** 2 de Noviembre de 2025
