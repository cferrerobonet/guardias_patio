# 🧹 Historial de Limpiezas del Proyecto

![Status](https://img.shields.io/badge/Status-Consolidado-success.svg)
![Tipo](https://img.shields.io/badge/Tipo-Historial-blue.svg)
![Última Actualización](https://img.shields.io/badge/Última_Actualización-Nov_2025-green.svg)

> 📦 **Documento Consolidado**: Este archivo reemplaza 3 documentos históricos de limpiezas

Este documento consolida el historial de todas las limpiezas y reorganizaciones realizadas en el proyecto Guardias de Patio.

**Documentos originales archivados:**
- `LIMPIEZA_PROYECTO_NOV2025.md`
- `LIMPIEZA_REORGANIZACION_OCT2025.md`
- `PLAN_CONSOLIDACION_DOCS_DIC2025.md`

---

## 📅 Noviembre 2025 - Limpieza de Documentación (Parte 2)

**Fecha:** 2 de Noviembre de 2025  
**Contexto:** Consolidación de documentación MD después de v3.0

### Eliminado
- **Archivos de sistema:**
  - 2 archivos `.DS_Store`
- **Documentación obsoleta:**
  - `INDICE_RAPIDO.md` (obsoleto, información en README.md)
- **Carpetas vacías:**
  - `validaciones/` (carpeta vacía)

### Archivado (9 documentos → `archivo/`)
- **Desarrollo:**
  - `PLAN_HOMOGENEIZACION_FORMULARIOS.md` ✅ Completado
  - `ERRORES_V3_ENCONTRADOS.md` ✅ Resueltos
  - `SPRINT_1.2_PLAN_DETALLADO.md` ✅ Completado
  - `RESUMEN_EJECUTIVO_REFACTORIZACION.md` ✅ Completado
  - `IMPLEMENTACION_ICALENDAR_EMAIL.md` ✅ Completado
  - `CORRECCIONES_ALGORITMO_v3.md` ✅ Aplicadas

- **Versiones:**
  - `CORRECCION_EQUIDAD_v2.9.md` (consolidado en CHANGELOG_v2.9)
  - `RESUMEN_CORRECCION_v2.9.md` (consolidado en CHANGELOG_v2.9)
  - `MEJORAS_CALENDARIO_v2.9.md` (consolidado en CHANGELOG_v2.9)

### Documentos Actualizados
- **README.md principal** (documentacion/)
  - Actualizado a v3.0.0
  - Estructura reorganizada
  - Referencias corregidas
  - Novedades de v3.0 destacadas

- **versiones/README.md**
  - Actualizado con v3.0.0 como versión actual
  - Añadido Sistema de PDFs Corporativos
  - Añadido Algoritmo v3.0 con fechas consecutivas
  - Referencias actualizadas a archivo/

- **desarrollo/README.md**
  - Actualizado a v3.0.0
  - Estructura de proyecto actualizada
  - Enlaces corregidos
  - Eliminadas referencias a archivos movidos

- **build/README.md** (NUEVO)
  - Índice de documentación de build
  - Enlaces a guías consolidadas
  - Checklist pre-release
  - Troubleshooting común

### Resultado
- **-12 archivos** (eliminados/archivados)
- **+1 archivo nuevo** (build/README.md)
- **4 README actualizados** con información correcta
- Todas las referencias actualizadas a v3.0.0
- Estructura más clara y mantenible

---

## 📅 Noviembre 2025 - Limpieza Post-Refactorización

**Fecha:** 1 de Noviembre de 2025  
**Contexto:** Después de completar la refactorización de formularios v3.0

### Eliminado
- **21 archivos obsoletos:**
  - 2 resúmenes de sesión temporal
  - 18 scripts de migración/debug antiguos
  - 1 archivo `.spec` obsoleto

### Archivado
- 3 documentos completados → `documentacion/archivo/`

### Reorganizado
- 4 documentos técnicos → `documentacion/tecnico/`
- 2 documentos de desarrollo → `documentacion/desarrollo/`
- 3 scripts de compilación → `scripts/build/`

### Resultado
- **~30 archivos** mejor organizados
- Reducción del **40%** en archivos innecesarios
- Estructura más clara y mantenible

---

## 📅 Noviembre 2025 - Limpieza de Usuarios y BD

**Fecha:** 1 de Noviembre de 2025  
**Espacio liberado:** ~70 MB  
**Archivos eliminados:** 28

### Usuarios Eliminados
- ❌ Usuario: `cferrerobonet` (hash: `66f06c9433d74e80`)
- ❌ Base de datos completa + 10 backups

### Usuario Activo
- ✅ Usuario: `Jefatura_FpBach` (hash: `0db13e2857239ed8`)
  - 67 profesores (33 mañana, 6 mixto, 28 tarde)
  - 169 días lectivos
  - 4 recreos, 4 zonas

### Archivos Eliminados
- 7 logs de desarrollo
- Builds temporales (~68 MB)
- 10 backups de BD

---

## 📅 Octubre 2025 - Reorganización Completa

**Fecha:** 28 de octubre de 2025  
**Versión:** v2.9.0  
**Commits:** `2af31a0`, `e7b413f`, `1eb37d1`

### Estadísticas
- **Archivos eliminados:** 25+
- **Archivos reubicados:** 19
- **Líneas eliminadas:** 4,544
- **Líneas añadidas:** 231

### Archivos .spec Eliminados (4)
```
Guardias de Patio.spec
Guardias de Patio 2.spec
Guardias de Patio OneFile.spec
guardias_patio_windows.spec
```
**Razón:** No usamos .spec por bug de symlinks PyQt6 en macOS

### Scripts Obsoletos Eliminados (4)
```
build_dmg.sh              # Duplicado de create_dmg.sh
build_app_debug.sh        # Script temporal de debug
create_icon.sh            # Movido a scripts/build/
fix_pyqt6.sh              # Movido a scripts/build/
```

### Reorganización de Scripts
**19 scripts** movidos a estructura organizada:
```
scripts/
├── build/          # Compilación y distribución (6)
├── dev/            # Desarrollo y debugging (4)
├── maintenance/    # Mantenimiento BD (9)
```

### Documentación Reorganizada
```
documentacion/
├── build/          # Compilación y distribución
├── funcionalidades/
├── guias/
├── roadmap/
├── sftp/          # Sincronización SFTP
├── tecnico/       # Arquitectura y algoritmos
├── validaciones/  # Reglas de negocio
├── versiones/     # Changelogs y releases
```

---

## 📊 Resumen Acumulado

### Total Eliminado
- **~70 archivos** obsoletos/temporales
- **~140 MB** de espacio liberado
- **~5,000 líneas** de código obsoleto

### Mejoras Conseguidas
✅ Estructura de directorios clara y lógica  
✅ Scripts organizados por función  
✅ Documentación categorizada  
✅ Raíz del proyecto limpia  
✅ Sin archivos duplicados  
✅ Mejor mantenibilidad  
✅ Onboarding más fácil para nuevos desarrolladores

---

## 🎯 Buenas Prácticas Establecidas

1. **Logs**: No commitear archivos `.log`
2. **Builds**: No commitear carpetas `build/`, `dist/`
3. **Backups**: No commitear `.backup_*` de BD
4. **Usuarios**: Usar solo `Jefatura_FpBach` como ejemplo
5. **Scripts**: Organizar en `scripts/{build,dev,maintenance}/`
6. **Docs**: Categorizar en subdirectorios temáticos
7. **Archivos temporales**: Archivar o eliminar después de cada sesión
8. **Consolidación**: Unir docs relacionados en lugar de multiplicarlos

---

**Última actualización:** 1 de Noviembre de 2025
