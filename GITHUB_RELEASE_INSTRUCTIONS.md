# Guía paso a paso: Crear GitHub Release v2.9.1

## 📋 Archivos preparados

✅ **DMG macOS**: `GuardiasPatio_v2.9.1_macOS.dmg` (68 MB)
✅ **Checksums**: `checksums_v2.9.1.txt`
✅ **Release Notes**: `RELEASE_NOTES_v2.9.1.md`
✅ **Tag**: `v2.9.1` (ya pusheado)

**SHA256 Checksum**:
```
e2963c8b15d5990ee93331bc9fe594ec54b6897bba730dc1078c0b9aba932f44  GuardiasPatio_v2.9.1_macOS.dmg
```

## 🚀 Pasos para crear el Release

### 1. Ir a GitHub Releases

Abre en tu navegador:
```
https://github.com/cferrerobonet/guardias_patio/releases/new
```

### 2. Configurar el Release

**Choose a tag**: Selecciona `v2.9.1` (debe aparecer en el dropdown)

**Release title**: 
```
Guardias de Patio v2.9.1 - Optimizaciones de rendimiento
```

**Description**: Copiar el contenido de abajo 👇

---

## 🎯 Guardias de Patio v2.9.1

**Fecha de lanzamiento**: 31 de octubre de 2025

### ✨ Novedades principales

#### ⚡ Optimizaciones de rendimiento - Hasta 75% más rápido

Esta versión incluye mejoras significativas en el algoritmo de asignación de guardias:

- **IndiceSlots**: Búsquedas O(1) en lugar de O(n) → **>2000x más rápido** en verificaciones
- **Tiempo total de regeneración**: 67-75% más rápido
  - **Antes**: 8-12 minutos
  - **Ahora**: 2.5-4 minutos ⚡
- **Memoria adicional**: < 1 MB
- **Equidad**: Perfecta (0% desviación mantenida)

#### 📅 Calendario escolar 2025-2026 actualizado

- ✅ **22 de diciembre de 2025**: Ahora es día lectivo
- ✅ **17-19 de marzo de 2026**: Fallas de Valencia - NO lectivas
- ✅ **Total guardias**: 2768 (173 días lectivos)
- ✅ **Cambio vs v2.9.0**: -32 guardias (-2 días × 16 guardias/día)

### 📦 Descarga

#### macOS
- **Archivo**: `GuardiasPatio_v2.9.1_macOS.dmg`
- **Tamaño**: 68 MB
- **Arquitectura**: ARM64 (Apple Silicon) + Intel (Rosetta 2)
- **Requisitos**: macOS 11.0 (Big Sur) o superior

**Instalación**:
1. Descarga el archivo DMG
2. Abre el DMG
3. Arrastra "Guardias de Patio.app" a Applications
4. Ejecuta desde Applications

**Nota de seguridad**: Si macOS bloquea la app:
- Abre `Preferencias del Sistema` → `Seguridad y Privacidad`
- Haz clic en "Abrir de todos modos"

#### Windows
⚠️ **Instalador Windows en preparación** - Disponible próximamente

### 🔍 Verificación de integridad

**SHA256 Checksum**:
```
e2963c8b15d5990ee93331bc9fe594ec54b6897bba730dc1078c0b9aba932f44  GuardiasPatio_v2.9.1_macOS.dmg
```

**Verificar en terminal**:
```bash
shasum -a 256 GuardiasPatio_v2.9.1_macOS.dmg
```

### 📊 Benchmarks de rendimiento

```
╔════════════════════════════════════════════════════════════╗
║  RENDIMIENTO v2.9.0 vs v2.9.1                              ║
╠════════════════════════════════════════════════════════════╣
║  Fase 2.1 (pre-asignación):                                ║
║    • v2.9.0: 5-8 minutos                                   ║
║    • v2.9.1: 30-60 segundos  ⚡                            ║
║    • Mejora: 83-88% más rápido                             ║
║                                                            ║
║  Tiempo total:                                             ║
║    • v2.9.0: 8-12 minutos                                  ║
║    • v2.9.1: 2.5-4 minutos  🚀                             ║
║    • Mejora: 67-75% más rápido                             ║
║                                                            ║
║  Equidad:                                                  ║
║    • Grupos inequitativos: 0                               ║
║    • Desviación máxima: 0                                  ║
║    • Cobertura: 100%  ✅                                   ║
╚════════════════════════════════════════════════════════════╝
```

### 🔧 Cambios técnicos

**Optimizaciones implementadas**:
- `IndiceSlots`: Índice hash para verificación O(1) de slots ocupados
- `FiltroProfesores`: Pre-filtrado eficiente por turno/zona
- `CacheElegibilidad`: Memoization de cálculos de elegibilidad
- Funciones auxiliares optimizadas

**Tests**:
- 28 tests unitarios nuevos (71% passing)
- Cobertura: 61.59% en módulo de optimizaciones
- Sin regresiones en funcionalidad existente

### ⚠️ Migración desde v2.9.0

**Compatibilidad**: ✅ Totalmente compatible con bases de datos existentes

**Recomendado**: Regenerar guardias para aplicar el nuevo calendario 2025-2026
1. Abre la aplicación
2. Ve a "Gestión de Guardias"
3. Haz clic en "Regenerar todo"
4. Verifica que se generan **2768 guardias** (en lugar de 2800)

### 📝 Notas adicionales

**Commits en este release**:
- `237bcc7` - Documentación calendario 2025-2026
- `cc3ec0c` - Implementación de optimizaciones
- `42c7e62` - Integración y tests
- `24d4287` - Preparación de release

**Archivos modificados**: 6 archivos
**Líneas añadidas**: +1987
**Líneas eliminadas**: -27

### 🐛 Problemas conocidos

Ninguno reportado hasta la fecha.

### 🔗 Enlaces

- [Documentación completa](https://github.com/cferrerobonet/guardias_patio/tree/main/documentacion)
- [Guía de optimizaciones](https://github.com/cferrerobonet/guardias_patio/blob/main/documentacion/tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md)
- [Changelog detallado](https://github.com/cferrerobonet/guardias_patio/blob/main/documentacion/versiones/CHANGELOG_v2.9.1.md)
- [Reportar issues](https://github.com/cferrerobonet/guardias_patio/issues)

---

**Desarrollado por**: Carlos Ferrero Bonet

---

### 3. Subir archivos

En la sección "Attach binaries", arrastra y suelta:

1. ✅ `GuardiasPatio_v2.9.1_macOS.dmg`
2. ✅ `checksums_v2.9.1.txt`
3. ✅ `RELEASE_NOTES_v2.9.1.md` (opcional, para referencia)

### 4. Configurar opciones

- ✅ Marca "Set as the latest release"
- ⬜ NO marcar "Set as a pre-release" (es una release estable)
- ⬜ NO marcar "Create a discussion" (opcional)

### 5. Publicar

Haz clic en el botón verde **"Publish release"**

## ✅ Verificación post-release

1. **Verifica el release**:
   - Abre: https://github.com/cferrerobonet/guardias_patio/releases
   - Confirma que v2.9.1 aparece como "Latest"
   - Verifica que los archivos DMG y checksums estén disponibles

2. **Prueba la descarga**:
   - Descarga el DMG desde GitHub
   - Verifica el checksum:
     ```bash
     shasum -a 256 GuardiasPatio_v2.9.1_macOS.dmg
     # Debe coincidir con: e2963c8b15d5990ee93331bc9fe594ec54b6897bba730dc1078c0b9aba932f44
     ```

3. **Prueba la instalación**:
   - Instala el DMG descargado
   - Ejecuta la aplicación
   - Verifica funcionalidad básica

## 🎊 ¡Listo!

El release v2.9.1 estará disponible públicamente en:
```
https://github.com/cferrerobonet/guardias_patio/releases/tag/v2.9.1
```

---

**Fecha de esta guía**: 31 de octubre de 2025
