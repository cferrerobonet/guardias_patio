# 📚 Documentación - Guardias de Patio

Sistema de gestión de guardias de recreo para centros educativos.

**Versión actual:** 2.9.1  
**Última actualización:** Noviembre 2025

---

## 📖 Índice Principal

### 🚀 Inicio Rápido
- [README Principal](../README.md) - Información general del proyecto
- [Requisitos del Sistema](tecnico/REQUISITOS_SISTEMA.md) - Requisitos mínimos y recomendados

### 🏗️ Desarrollo
- [Contribuir al Proyecto](desarrollo/CONTRIBUIR.md) - Guía para contribuir
- [Historia de Sprints](desarrollo/HISTORIA_SPRINTS.md) - Historial de desarrollo
- [Plan de Consolidación](desarrollo/PLAN_CONSOLIDACION_DOCS_DIC2025.md) - Organización de docs
- [Limpieza y Reorganización](desarrollo/LIMPIEZA_REORGANIZACION_OCT2025.md) - Mejoras Oct 2025

### 📦 Build y Distribución
- [Compilación Rápida](build/COMPILACION_RAPIDA.md) - Guía rápida
- [Build General](build/BUILD.md) - Construcción multiplataforma
- [Build macOS (DMG)](build/BUILD_DMG.md) - Crear instalador para macOS
- [Build Windows](build/BUILD_WINDOWS.md) - Crear instalador para Windows
- [Checklist de Compilación](build/CHECKLIST_COMPILACION.md) - Lista de verificación
- [Guía de Distribución v2.9.1](build/GUIA_DISTRIBUCION_v2.9.1.md) - Distribución actual

### 🔧 Técnico
- **Algoritmos:**
  - [Algoritmo Pasada 6](tecnico/ALGORITMO_PASADA_6.md) - Detalle del algoritmo v2.9
  - [Propuesta Algoritmo Simple](tecnico/PROPUESTA_ALGORITMO_SIMPLE.md) - Base para v3.0
  - [Integración Algoritmo v3](tecnico/INTEGRACION_ALGORITMO_V3.md) - Integración del v3.0
  - [Resumen Ejecutivo v3](tecnico/RESUMEN_EJECUTIVO_ALGORITMO_V3.md) - Resumen del v3.0

- **Especificaciones:**
  - [Cálculo de Guardias](tecnico/ESPECIFICACION_CALCULO_GUARDIAS.md) - Distribución de cuotas
  - [Validaciones de Negocio](tecnico/VALIDACIONES_NEGOCIO.md) - Reglas de negocio
  - [Patrones de Arquitectura](tecnico/ARCHITECTURE_PATTERNS.md) - Arquitectura del sistema

- **Configuración:**
  - [Email SMTP](tecnico/CONFIGURACION_EMAIL_SMTP.md) - Configurar notificaciones
  - [Sincronización Multi-usuario](tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md) - Sistema SFTP

- **Rendimiento:**
  - [Optimizaciones de Rendimiento](tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md) - Mejoras de velocidad

### 🎨 Guías de Uso
- [Características de UI](guias/GUIA_UI_FEATURES.md) - Interfaz Fluent Design
- [Probar Algoritmo v3](guias/GUIA_PROBAR_ALGORITMO_V3.md) - Testing del nuevo algoritmo
- [Atajos de Teclado](guias/atajos-teclado.md) - Shortcuts del sistema

### � Funcionalidades
- [Funcionalidades Completas](funcionalidades/FUNCIONALIDADES_COMPLETAS.md) - Lista completa de features

### �️ Roadmap
- [Roadmap v3.0](roadmap/roadmap-v3.0.md) - Planificación de la versión 3.0

### 📜 Historial de Versiones
- [v2.9.1](versiones/CHANGELOG_v2.9.1.md) - Versión actual
- [v2.9.0](versiones/CHANGELOG_v2.9.md) - Mejoras de calendario
- [Corrección de Equidad v2.9](versiones/CORRECCION_EQUIDAD_v2.9.md) - Fix importante
- [Resumen Corrección v2.9](versiones/RESUMEN_CORRECCION_v2.9.md) - Detalles técnicos
- [Mejoras Calendario v2.9](versiones/MEJORAS_CALENDARIO_v2.9.md) - Features de calendario

### � Archivo Histórico
- [Sprints Anteriores](_archivo_sprints/) - Documentación archivada de sprints pasados

---

## 🗂️ Estructura de Carpetas

```
documentacion/
├── README.md                    # Este archivo
├── build/                       # Compilación y distribución
├── desarrollo/                  # Desarrollo y contribución
├── funcionalidades/             # Features implementadas
├── guias/                       # Guías de usuario
├── roadmap/                     # Planificación futura
├── tecnico/                     # Documentación técnica
├── validaciones/                # Sistema de validaciones
├── versiones/                   # Changelogs y releases
├── sftp/                        # Configuración SFTP (legacy)
├── datos ejemplo/               # Datos de prueba
└── _archivo_sprints/            # Histórico archivado
```

---

## 🔍 Buscar Documentación

**Por tema:**
- **Algoritmos**: `tecnico/ALGORITMO_*.md`
- **Build**: `build/BUILD*.md`
- **Versiones**: `versiones/CHANGELOG_*.md`
- **Guías**: `guias/*.md`

**Por versión:**
- **v2.9.1 (actual)**: `versiones/CHANGELOG_v2.9.1.md`
- **v3.0 (desarrollo)**: `roadmap/roadmap-v3.0.md`, `tecnico/INTEGRACION_ALGORITMO_V3.md`

---

## 📝 Notas

- Los archivos en `_archivo_sprints/` son históricos y pueden no estar actualizados
- La documentación de SFTP en `sftp/` es legacy (sistema implementado en v2.8)
- Para crear nuevos builds, consultar `build/COMPILACION_RAPIDA.md`

### 📁 Datos de Ejemplo
- Ver [datos ejemplo/](datos%20ejemplo/) - Datos para pruebas

### 🗂️ Mantenimiento del Proyecto
- [Limpieza del Proyecto](LIMPIEZA_PROYECTO.md) - Resumen de limpieza realizada
- [Plan de Consolidación](PLAN_CONSOLIDACION.md) - Estrategia de consolidación de docs

---

## 🎯 Navegación Rápida

| Tema | Enlaces |
|------|---------|
| **Instalación** | [Requisitos](REQUISITOS_SISTEMA.md) |
| **Configuración** | [Email SMTP](CONFIGURACION_EMAIL.md) |
| **Desarrollo** | [Arquitectura](ARCHITECTURE_PATTERNS.md) \| [Contribuir](CONTRIBUIR.md) |
| **Sincronización** | [Guía Completa](GUIA_SINCRONIZACION.md) \| [SFTP](sftp/) |
| **Interfaz** | [UI Features](GUIA_UI_FEATURES.md) |
| **Build** | [General](build/BUILD.md) \| [macOS](build/BUILD_DMG.md) \| [Windows](build/BUILD_WINDOWS.md) |
| **Versiones** | [v2.8](CHANGELOG_v2.8.md) \| [Historial](versiones/) |

---

## 📊 Estructura Consolidada (Octubre 2025)

Este directorio ha sido reorganizado para eliminar redundancia y mejorar la navegación:

**Archivos Consolidados:**
- ✅ **GUIA_SINCRONIZACION.md** - Combina:
  - Sistema Multi-usuario
  - Sistema de Bloqueo de Sesión
  - Lógica de Sincronización
  - Sincronización JSON
  
- ✅ **GUIA_UI_FEATURES.md** - Combina:
  - UI Fluent Redesign
  - Validación de Resolución de Pantalla
  
- ✅ **ARCHITECTURE_PATTERNS.md** - Incluye ahora:
  - Patrones arquitectónicos
  - Guía de Pydantic Schemas (integrada)

**Archivos Preservados:**
- 📋 README.md (este archivo)
- 📋 REQUISITOS_SISTEMA.md
- 📋 CONFIGURACION_EMAIL.md
- 📋 CONTRIBUIR.md
- 📋 CHANGELOG_v2.8.md
- 📋 HISTORIA_SPRINTS.md
- 📋 LIMPIEZA_PROYECTO.md
- 📋 PLAN_CONSOLIDACION.md
- 📋 ARCHITECTURE_PATTERNS.md

**Resultado:** De 17 archivos MD a 11 archivos, sin pérdida de información.

---

**Proyecto:** Guardias de Patio  
**Versión:** 2.8+  
**Última actualización:** 26 de Octubre de 2025
