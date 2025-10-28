# 🚀 Compilación Rápida - Guardias de Patio

## Instrucciones para Compilar

### 1. Compilar la aplicación:

```bash
./scripts/build/build_simple.sh
```

### 2. Crear el instalador DMG:

```bash
./scripts/build/create_dmg.sh
```

### 3. Probar el DMG:

```bash
open "dist/GuardiasDePatio-2.9.0-macOS.dmg"
```

**Resultado:**
- ✅ App compilada: `dist/Guardias de Patio.app` (~250 MB)
- ✅ Instalador DMG: `dist/GuardiasDePatio-2.9.0-macOS.dmg` (~87 MB)

---

## ⚠️ Si hay problemas

**Consulta primero:** [`SOLUCION_COMPILACION.md`](SOLUCION_COMPILACION.md)

Este documento contiene:
- ✅ Todos los problemas conocidos y sus soluciones
- ✅ Checklist de verificación pre-compilación
- ✅ Pruebas post-compilación
- ✅ Debugging avanzado

---

## 📋 Checklist Rápido

Antes de compilar, verifica:

- [ ] Python 3.11 instalado
- [ ] PyInstaller instalado: `python3.11 -m pip install pyinstaller`
- [ ] Directorio limpio: `rm -rf dist build`
- [ ] **NO usar archivos .spec** (causarán que se cuelgue)

---

## ✅ La App Está Lista Cuando

1. Abre con `open "dist/Guardias de Patio.app"` ✅
2. Muestra la pantalla de login sin errores ✅
3. No hay advertencias de "Icono no encontrado" ✅
4. El proceso aparece en: `ps aux | grep Guardias` ✅

---

## 🐛 Problemas Comunes

### La app no abre con `open`:
- **Causa**: Rutas relativas en lugar de absolutas
- **Solución**: Ver `SOLUCION_COMPILACION.md` → Sección 2

### Iconos no se ven:
- **Causa**: `icon_manager.py` no usa `get_resources_directory()`
- **Solución**: Ver `SOLUCION_COMPILACION.md` → Sección 1

### Compilación se cuelga en "Building PKG":
- **Causa**: Usando archivo `.spec` con PyQt6
- **Solución**: Usar `scripts/build/build_simple.sh` en su lugar

---

## 📚 Documentación Completa

- **Solución de problemas**: [`SOLUCION_COMPILACION.md`](SOLUCION_COMPILACION.md)
- **Checklist de compilación**: [`CHECKLIST_COMPILACION.md`](CHECKLIST_COMPILACION.md)
- **Build DMG**: [`BUILD_DMG.md`](BUILD_DMG.md)
- **Build Windows**: [`BUILD_WINDOWS.md`](BUILD_WINDOWS.md)
- **Arquitectura**: [`../tecnico/ARCHITECTURE_PATTERNS.md`](../tecnico/ARCHITECTURE_PATTERNS.md)

---

**Última actualización:** 28 de Octubre de 2025  
**Versión funcional:** PyInstaller 6.16.0 + Python 3.11.14 + PyQt6
