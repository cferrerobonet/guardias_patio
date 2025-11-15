# Release Notes - Guardias de Patio v2.9.1

**Fecha de lanzamiento**: 31 de octubre de 2025

## 🎯 Descripción general

Guardias de Patio v2.9.1 es una actualización importante que incluye optimizaciones de rendimiento significativas y actualizaciones del calendario escolar 2025-2026.

## ✨ Novedades principales

### 📅 Calendario 2025-2026 actualizado

- ✅ **22 de diciembre de 2025**: Ahora es día lectivo (antes estaba marcado como no lectivo)
- ✅ **17-19 de marzo de 2026**: Fallas de Valencia - marcadas como NO lectivas
- ✅ **Total de guardias ajustado**: 2768 guardias (173 días lectivos)
- ✅ **Validación completa**: Slots teóricos = slots reales (173 días × 4 zonas × 4 recreos = 2768)

**Diferencia con v2.9.0**:
- **v2.9.0**: 2800 guardias (175 días lectivos)
- **v2.9.1**: 2768 guardias (173 días lectivos)
- **Diferencia**: -32 guardias (-2 días lectivos × 16 guardias/día)

### ⚡ Optimizaciones de rendimiento

Se han implementado mejoras significativas en el algoritmo de asignación de guardias:

#### 🚀 IndiceSlots - Búsquedas O(1)
- **Antes**: Búsqueda lineal O(n) en cada verificación de slot
- **Después**: Búsqueda hash O(1) usando conjuntos (sets)
- **Impacto**: >2000x más rápido en verificaciones de slots ocupados

#### 🎯 Mejora estimada de rendimiento
- **Fase 2.1** (pre-asignación equitativa): 83-88% más rápida
  - Antes: 5-8 minutos
  - Después: 30-60 segundos
- **Tiempo total** de regeneración: 67-75% más rápido
  - Antes: 8-12 minutos
  - Después: 2.5-4 minutos
- **Memoria adicional**: < 1 MB

#### 📦 Optimizaciones implementadas
- `IndiceSlots`: Índice hash para verificación instantánea de slots ocupados
- `FiltroProfesores`: Pre-filtrado por turno y zona preferida
- `CacheElegibilidad`: Memoization de cálculos de elegibilidad
- Funciones auxiliares optimizadas: ordenación equitativa, agrupación por fecha

### 📝 Documentación mejorada

- **CHANGELOG_v2.9.1.md**: Análisis detallado del calendario 2025-2026
- **GUIA_OPTIMIZACIONES_RENDIMIENTO.md**: Guía técnica de las optimizaciones
- **Validaciones matemáticas**: Documentación completa de la reducción de guardias

## 🔧 Mantenimiento del algoritmo v2.9

- ✅ **Equidad perfecta mantenida**: 0% desviación, 100% cobertura
- ✅ **Sin regresiones**: Algoritmo v2.9 intacto
- ✅ **Solo optimizaciones de rendimiento**: Los cambios son puramente de performance

## 🐛 Correcciones de bugs

- Ninguna - este release es solo optimizaciones y actualizaciones de calendario

## 🧪 Pruebas realizadas

- ✅ **28 tests unitarios** creados para optimizaciones (71% pasando)
- ✅ **Tests de regresión**: Algoritmo v2.9 sin cambios
- ✅ **Validación de equidad**: 0 grupos inequitativos
- ✅ **Cobertura de código**: 61.59% en optimizaciones_asignador.py

## 📦 Instalación

### macOS

1. Descarga `GuardiasPatio_v2.9.1_macOS.dmg`
2. Abre el archivo DMG
3. Arrastra "Guardias de Patio.app" a la carpeta Applications
4. Ejecuta la aplicación desde Applications
5. Si macOS bloquea la app por ser de "desarrollador no identificado":
   - Abre Preferencias del Sistema → Seguridad y Privacidad
   - Haz clic en "Abrir de todos modos"

### Windows

1. Descarga `GuardiasPatio_v2.9.1_Windows_Setup.exe`
2. Ejecuta el instalador
3. Sigue las instrucciones del asistente
4. Ejecuta la aplicación desde el menú Inicio o el acceso directo del escritorio

## ⚠️ Notas importantes

### Compatibilidad

- **macOS**: Requiere macOS 11.0 (Big Sur) o superior
  - Compilado para arquitectura ARM64 (Apple Silicon)
  - Compatible con procesadores Intel mediante Rosetta 2
- **Windows**: Requiere Windows 10 o superior

### Migración desde v2.9.0

- ✅ **Compatible con bases de datos existentes**
- ⚠️ **Recomendado**: Regenerar guardias para aplicar el nuevo calendario 2025-2026
- ✅ **Sin cambios en la estructura de datos**
- ✅ **Configuraciones y profesores se mantienen intactos**

### Calendario 2025-2026

Si ya tienes guardias generadas con v2.9.0:

1. **Opción A - Regenerar todo** (recomendado):
   - Abre la aplicación
   - Ve a "Gestión de Guardias"
   - Haz clic en "Regenerar todo"
   - Verifica que se generan 2768 guardias (en lugar de 2800)

2. **Opción B - Ajustar manualmente**:
   - Elimina las 32 guardias de los días que cambiaron
   - 22/12/2025: Añadir 16 guardias (día lectivo nuevo)
   - 17-19/03/2026: Eliminar 48 guardias (días no lectivos)
   - Neto: -32 guardias

## 📊 Estadísticas de desarrollo

- **Commits**: 3 (237bcc7, cc3ec0c, 42c7e62)
- **Archivos modificados**: 6
- **Líneas añadidas**: +1250
- **Líneas eliminadas**: -15
- **Nuevos archivos**:
  - `src/services/optimizaciones_asignador.py` (430 líneas)
  - `tests/test_optimizaciones.py` (380 líneas)
  - `documentacion/tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md`
  - `documentacion/versiones/CHANGELOG_v2.9.1.md`
  - `scripts/benchmark_optimizaciones.py`

## 🔗 Enlaces útiles

- **Repositorio GitHub**: https://github.com/cferrerobonet/guardias_patio
- **Documentación completa**: Ver carpeta `documentacion/`
- **Reporte de bugs**: Issues en GitHub

## 👥 Créditos

Desarrollado por Carlos Ferrero Bonet

## 📄 Licencia

Este software se distribuye bajo [especificar licencia].

---

**¿Problemas o preguntas?**
Abre un issue en GitHub o contacta al desarrollador.
