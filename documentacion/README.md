# 📚 Documentación - Guardias de Patio

Sistema de gestión de guardias de recreo para centros educativos.

## 📖 Índice Principal

### 🚀 Inicio Rápido
- [README Principal](../README.md) - Información general del proyecto
- [Requisitos del Sistema](REQUISITOS_SISTEMA.md) - Requisitos mínimos y recomendados
- [Configuración de Email](CONFIGURACION_EMAIL.md) - Configurar servidor SMTP

### 🏗️ Arquitectura y Desarrollo
- [Patrones de Arquitectura](ARCHITECTURE_PATTERNS.md) - Patrones y esquemas Pydantic
- [Guía para Contribuir](CONTRIBUIR.md) - Cómo contribuir al proyecto

### 🔄 Sincronización y Multi-usuario
- [Guía de Sincronización](GUIA_SINCRONIZACION.md) - Sistema multi-usuario, bloqueo de sesión, SFTP y JSON
- **Documentación SFTP Detallada**: Ver [sftp/](sftp/)
  - Guías de integración SFTP
  - Configuración de servidor
  - Resolución de problemas

### 🎨 Interfaz de Usuario
- [Guía de Características UI](GUIA_UI_FEATURES.md) - Fluent Design y validación de resolución

### 📦 Build y Distribución
- **Guías de Build**: Ver [build/](build/)
  - BUILD.md - Construcción general
  - BUILD_DMG.md - Construcción para macOS
  - BUILD_WINDOWS.md - Construcción para Windows

### 🔧 Funcionalidades
- Ver [funcionalidades/](funcionalidades/) - Funcionalidades implementadas

### 📋 Guías Específicas
- Ver [guias/](guias/) - Guías detalladas de uso

### 🛣️ Roadmap y Planificación
- Ver [roadmap/](roadmap/) - Planes futuros del proyecto

### 🔍 Documentación Técnica
- Ver [tecnico/](tecnico/) - Detalles técnicos de implementación

### ✅ Validaciones
- Ver [validaciones/](validaciones/) - Sistema de validaciones

### 📜 Historial de Versiones
- [Changelog v2.8](CHANGELOG_v2.8.md) - Cambios de la versión 2.8
- [Historia de Sprints](HISTORIA_SPRINTS.md) - Resumen de todos los sprints
- Ver más en [versiones/](versiones/)

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
