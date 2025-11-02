# 📚 Documentación - Guardias de Patio# 📚 Documentación - Guardias de Patio# 📚 Documentación - Guardias de Patio



Sistema de gestión de guardias de recreo para centros educativos.



**Versión actual:** 3.0.0  Sistema de gestión de guardias de recreo para centros educativos.Sistema de gestión de guardias de recreo para centros educativos.

**Última actualización:** 2 de Noviembre de 2025



---

**Versión actual:** 3.0.0  **Versión actual:** 2.9.1  

## 🚀 Inicio Rápido

**Última actualización:** 1 de Noviembre de 2025**Última actualización:** Noviembre 2025

### Documentación Esencial

- [README Principal del Proyecto](../README.md) - Información general

- [Requisitos del Sistema](tecnico/REQUISITOS_SISTEMA.md) - Hardware y software necesarios

- [Premisas del Algoritmo](PREMISAS_ASIGNACION_GUARDIAS.md) - Cómo funciona la asignación------



### Para Usuarios

- [Funcionalidades](funcionalidades/FUNCIONALIDADES_COMPLETAS.md) - Lista completa de características

- [Guía de UI](guias/GUIA_UI_FEATURES.md) - Interfaz y navegación## 📖 Índice Principal## 📖 Índice Principal

- [Atajos de Teclado](guias/atajos-teclado.md) - Shortcuts disponibles



### Para Desarrolladores

- [Contribuir](desarrollo/CONTRIBUIR.md) - Cómo contribuir al proyecto### 🚀 Inicio Rápido### 🚀 Inicio Rápido

- [Arquitectura](tecnico/ARCHITECTURE_PATTERNS.md) - Patrones arquitectónicos

- [Historia del Proyecto](desarrollo/HISTORIA_SPRINTS.md) - Evolución del desarrollo- [README Principal](../README.md) - Información general del proyecto- [README Principal](../README.md) - Información general del proyecto



---- [INDICE_RAPIDO.md](INDICE_RAPIDO.md) - Acceso rápido por tema- [Requisitos del Sistema](tecnico/REQUISITOS_SISTEMA.md) - Requisitos mínimos y recomendados



## 📂 Estructura de Carpetas- [Requisitos del Sistema](tecnico/REQUISITOS_SISTEMA.md) - Requisitos mínimos y recomendados



```### 🏗️ Desarrollo

documentacion/

├── README.md                           # Este archivo---- [Contribuir al Proyecto](desarrollo/CONTRIBUIR.md) - Guía para contribuir

├── PREMISAS_ASIGNACION_GUARDIAS.md     # Documentación del algoritmo

├── CALENDARIO_MEJORADO_v3.md           # Features del calendario- [Historia de Sprints](desarrollo/HISTORIA_SPRINTS.md) - Historial de desarrollo

│

├── archivo/                            # 📦 Documentos históricos## 📂 Categorías de Documentación- [Plan de Consolidación](desarrollo/PLAN_CONSOLIDACION_DOCS_DIC2025.md) - Organización de docs

│   ├── Planes completados

│   ├── Limpiezas anteriores- [Limpieza y Reorganización](desarrollo/LIMPIEZA_REORGANIZACION_OCT2025.md) - Mejoras Oct 2025

│   └── Versiones antiguas consolidadas

│### 🔧 Desarrollo

├── build/                              # 🏗️ Compilación y distribución

│   └── (Documentación de build en scripts/build/)### 📦 Build y Distribución

│

├── datos ejemplo/                      # 📊 Datos de prueba> Documentación del proceso de desarrollo, planificación y contribución- [Compilación Rápida](build/COMPILACION_RAPIDA.md) - Guía rápida

│   └── Ejemplos de configuración

│- [Build General](build/BUILD.md) - Construcción multiplataforma

├── desarrollo/                         # 🔧 Desarrollo

│   ├── CONTRIBUIR.md#### 📦 Documentos Consolidados- [Build macOS (DMG)](build/BUILD_DMG.md) - Crear instalador para macOS

│   ├── HISTORIA_SPRINTS.md

│   ├── HISTORIAL_LIMPIEZAS.md          # Historial de reorganizaciones- [Build Windows](build/BUILD_WINDOWS.md) - Crear instalador para Windows

│   └── ARCHIVO_HISTORICO_INFO.md       # Info sobre sprints archivados

│- [**HISTORIAL_LIMPIEZAS.md**](desarrollo/HISTORIAL_LIMPIEZAS.md) ✨ **NUEVO**- [Checklist de Compilación](build/CHECKLIST_COMPILACION.md) - Lista de verificación

├── funcionalidades/                    # 🎯 Features

│   ├── CALENDARIO_ICALENDAR.md  - Historial completo de limpiezas del proyecto- [Guía de Distribución v2.9.1](build/GUIA_DISTRIBUCION_v2.9.1.md) - Distribución actual

│   ├── CONFIGURACION_INICIAL.md

│   ├── FUNCIONALIDADES_COMPLETAS.md  - Nov 2025: Post-refactorización (21 eliminados, 13 archivados, 10→3 consolidados)

│   ├── guardias/                       # Gestión de guardias

│   └── profesores/                     # Gestión de profesores  - Nov 2025: Limpieza usuarios/BD (~70 MB liberados)### 🔧 Técnico

│

├── guias/                              # 📖 Guías de uso  - Oct 2025: Reorganización completa (25+ eliminados)- **Algoritmos:**

│   ├── GUIA_UI_FEATURES.md

│   ├── GUIA_PROBAR_ALGORITMO_V3.md  - [Algoritmo Pasada 6](tecnico/ALGORITMO_PASADA_6.md) - Detalle del algoritmo v2.9

│   └── atajos-teclado.md

│#### Otros Documentos  - [Propuesta Algoritmo Simple](tecnico/PROPUESTA_ALGORITMO_SIMPLE.md) - Base para v3.0

├── roadmap/                            # 🗺️ Planificación

│   └── roadmap-v3.0.md                 # Roadmap versión 3.0  - [Integración Algoritmo v3](tecnico/INTEGRACION_ALGORITMO_V3.md) - Integración del v3.0

│

├── sftp/                               # ☁️ Sincronización (Legacy)- [Resumen Ejecutivo Refactorización](desarrollo/RESUMEN_EJECUTIVO_REFACTORIZACION.md)  - [Resumen Ejecutivo v3](tecnico/RESUMEN_EJECUTIVO_ALGORITMO_V3.md) - Resumen del v3.0

│   └── Configuración SFTP histórica

│- [Sprint 1.2 - Plan Detallado](desarrollo/SPRINT_1.2_PLAN_DETALLADO.md)

├── tecnico/                            # ⚙️ Documentación técnica

│   ├── ALGORITMO_ASIGNACION_GUARDIAS.md- [Guía para Contribuir](desarrollo/CONTRIBUIR.md)- **Especificaciones:**

│   ├── ARCHITECTURE_PATTERNS.md

│   ├── CONFIGURACION_EMAIL_SMTP.md- [Historia de Sprints](desarrollo/HISTORIA_SPRINTS.md)  - [Cálculo de Guardias](tecnico/ESPECIFICACION_CALCULO_GUARDIAS.md) - Distribución de cuotas

│   ├── ESPECIFICACION_CALCULO_GUARDIAS.md

│   ├── GUIA_OPTIMIZACIONES_RENDIMIENTO.md- [Plan de Homogeneización de Formularios](desarrollo/PLAN_HOMOGENEIZACION_FORMULARIOS.md)  - [Validaciones de Negocio](tecnico/VALIDACIONES_NEGOCIO.md) - Reglas de negocio

│   ├── GUIA_SINCRONIZACION_MULTIUSUARIO.md

│   ├── MEJORAS_UX_TABLAS_v3.0.md- [Errores v3 Encontrados](desarrollo/ERRORES_V3_ENCONTRADOS.md)  - [Patrones de Arquitectura](tecnico/ARCHITECTURE_PATTERNS.md) - Arquitectura del sistema

│   ├── PATRON_WIDGETS.md

│   ├── PLAN_MIGRACION_SOLO_BD.md

│   ├── REQUISITOS_SISTEMA.md

│   ├── SISTEMA_PDF_CORPORATIVO.md      # ✨ NUEVO - Sistema de PDFs---- **Configuración:**

│   ├── UBICACION_BASE_DATOS.md

│   ├── VALIDACIONES_NEGOCIO.md  - [Email SMTP](tecnico/CONFIGURACION_EMAIL_SMTP.md) - Configurar notificaciones

│   └── ejemplo-exportacion.json

│### ⚙️ Técnico  - [Sincronización Multi-usuario](tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md) - Sistema SFTP

└── versiones/                          # 📜 Changelogs

    ├── CHANGELOG_v3.0.md               # ⭐ Versión actual

    ├── CHANGELOG_v2.9.1.md

    ├── CHANGELOG_v2.9.md> Documentación técnica: algoritmos, arquitectura, configuración- **Rendimiento:**

    ├── RELEASE_NOTES_v2.9.1.md

    └── README.md  - [Optimizaciones de Rendimiento](tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md) - Mejoras de velocidad

```

#### 📦 Documentos Consolidados

---

### 🎨 Guías de Uso

## 🔍 Buscar Documentación

- [**ALGORITMO_ASIGNACION_GUARDIAS.md**](tecnico/ALGORITMO_ASIGNACION_GUARDIAS.md) ✨ **NUEVO**- [Características de UI](guias/GUIA_UI_FEATURES.md) - Interfaz Fluent Design

### Por Tema

  - Documentación completa del algoritmo Pasada 6- [Probar Algoritmo v3](guias/GUIA_PROBAR_ALGORITMO_V3.md) - Testing del nuevo algoritmo

| Tema | Documento Principal |

|------|---------------------|  - 6 iteraciones detalladas con ejemplos de código- [Atajos de Teclado](guias/atajos-teclado.md) - Shortcuts del sistema

| **Algoritmo de Asignación** | [tecnico/ALGORITMO_ASIGNACION_GUARDIAS.md](tecnico/ALGORITMO_ASIGNACION_GUARDIAS.md) |

| **Premisas y Reglas** | [PREMISAS_ASIGNACION_GUARDIAS.md](PREMISAS_ASIGNACION_GUARDIAS.md) |  - Validaciones y reglas de negocio

| **Arquitectura** | [tecnico/ARCHITECTURE_PATTERNS.md](tecnico/ARCHITECTURE_PATTERNS.md) |

| **Patrones de Widgets** | [tecnico/PATRON_WIDGETS.md](tecnico/PATRON_WIDGETS.md) |  - Optimizaciones de rendimiento (cache, bulk inserts, índices)### � Funcionalidades

| **PDFs Corporativos** | [tecnico/SISTEMA_PDF_CORPORATIVO.md](tecnico/SISTEMA_PDF_CORPORATIVO.md) ✨ |

| **Validaciones** | [tecnico/VALIDACIONES_NEGOCIO.md](tecnico/VALIDACIONES_NEGOCIO.md) |  - Métricas de calidad (cobertura ≥95%, equidad ≥85%)- [Funcionalidades Completas](funcionalidades/FUNCIONALIDADES_COMPLETAS.md) - Lista completa de features

| **Configuración Email** | [tecnico/CONFIGURACION_EMAIL_SMTP.md](tecnico/CONFIGURACION_EMAIL_SMTP.md) |

| **Sincronización** | [tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md](tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md) |  - Integración en la aplicación

| **Optimizaciones** | [tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md](tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md) |

| **Interfaz UI** | [guias/GUIA_UI_FEATURES.md](guias/GUIA_UI_FEATURES.md) |  - Propuestas alternativas (archivadas)### �️ Roadmap

| **Funcionalidades** | [funcionalidades/FUNCIONALIDADES_COMPLETAS.md](funcionalidades/FUNCIONALIDADES_COMPLETAS.md) |

- [Roadmap v3.0](roadmap/roadmap-v3.0.md) - Planificación de la versión 3.0

### Por Versión

#### Arquitectura y Patrones

| Versión | Changelog |

|---------|-----------|### 📜 Historial de Versiones

| **v3.0 (actual)** ⭐ | [versiones/CHANGELOG_v3.0.md](versiones/CHANGELOG_v3.0.md) |

| **v2.9.1** | [versiones/CHANGELOG_v2.9.1.md](versiones/CHANGELOG_v2.9.1.md) |- [Patrón de Widgets](tecnico/PATRON_WIDGETS.md)- [v2.9.1](versiones/CHANGELOG_v2.9.1.md) - Versión actual

| **v2.9** | [versiones/CHANGELOG_v2.9.md](versiones/CHANGELOG_v2.9.md) |

- [Mejoras UX Tablas v3.0](tecnico/MEJORAS_UX_TABLAS_v3.0.md)- [v2.9.0](versiones/CHANGELOG_v2.9.md) - Mejoras de calendario

### Por Actividad

- [Patrones de Arquitectura](tecnico/ARCHITECTURE_PATTERNS.md)- [Corrección de Equidad v2.9](versiones/CORRECCION_EQUIDAD_v2.9.md) - Fix importante

| ¿Qué necesitas hacer? | Ve a... |

|-----------------------|---------|- [Resumen Corrección v2.9](versiones/RESUMEN_CORRECCION_v2.9.md) - Detalles técnicos

| **Instalar** | [tecnico/REQUISITOS_SISTEMA.md](tecnico/REQUISITOS_SISTEMA.md) |

| **Compilar** | `../scripts/build/` (scripts de build) |#### Configuración y Despliegue- [Mejoras Calendario v2.9](versiones/MEJORAS_CALENDARIO_v2.9.md) - Features de calendario

| **Contribuir** | [desarrollo/CONTRIBUIR.md](desarrollo/CONTRIBUIR.md) |

| **Entender el algoritmo** | [PREMISAS_ASIGNACION_GUARDIAS.md](PREMISAS_ASIGNACION_GUARDIAS.md) |

| **Configurar Email** | [tecnico/CONFIGURACION_EMAIL_SMTP.md](tecnico/CONFIGURACION_EMAIL_SMTP.md) |

| **Configurar SFTP** | [tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md](tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md) |- [Configuración Email SMTP](tecnico/CONFIGURACION_EMAIL_SMTP.md)### 📦 Archivo Histórico

| **Crear widgets** | [tecnico/PATRON_WIDGETS.md](tecnico/PATRON_WIDGETS.md) |

| **Generar PDFs** | [tecnico/SISTEMA_PDF_CORPORATIVO.md](tecnico/SISTEMA_PDF_CORPORATIVO.md) ✨ |- [Plan de Migración Solo BD](tecnico/PLAN_MIGRACION_SOLO_BD.md)- [Información sobre Archivo Histórico](desarrollo/ARCHIVO_HISTORICO_INFO.md) - Sprints 1-12 comprimidos

| **Probar algoritmo v3** | [guias/GUIA_PROBAR_ALGORITMO_V3.md](guias/GUIA_PROBAR_ALGORITMO_V3.md) |

- [Ubicación Base de Datos](tecnico/UBICACION_BASE_DATOS.md)  - **Ubicación**: `ARCHIVO_HISTORICO_SPRINTS.tar.gz` (raíz del proyecto)

---

  - **Contenido**: 57 documentos de sprints históricos (1 MB → 266 KB)

## 📊 Novedades de la Versión 3.0

#### Especificaciones  - **Razón**: Mantener documentación activa limpia y enfocada

### 🎨 Sistema de PDFs Corporativos

- **NUEVO**: [SISTEMA_PDF_CORPORATIVO.md](tecnico/SISTEMA_PDF_CORPORATIVO.md)

- Paleta de colores estandarizada

- Estilos reutilizables- [Especificación Cálculo de Guardias](tecnico/ESPECIFICACION_CALCULO_GUARDIAS.md)---

- Separación visual por meses

- Colores diferenciados por zona y recreo- [Validaciones de Negocio](tecnico/VALIDACIONES_NEGOCIO.md)



### 🧮 Algoritmo Mejorado v3.0## 🗂️ Estructura de Carpetas

- **Fechas consecutivas/agrupadas** (Prioridad alta)

- El profesor termina sus guardias antes#### Optimización

- Períodos libres más largos

- Ver: [PREMISAS_ASIGNACION_GUARDIAS.md](PREMISAS_ASIGNACION_GUARDIAS.md)```



### 🏗️ Refactorización Arquitectónica- [Guía de Optimizaciones de Rendimiento](tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md)documentacion/

- Formularios homogeneizados

- Widgets modernizados- [Guía de Sincronización Multiusuario](tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md)├── README.md                    # Este archivo

- Mejor rendimiento

- Ver: [versiones/CHANGELOG_v3.0.md](versiones/CHANGELOG_v3.0.md)├── build/                       # Compilación y distribución



------├── desarrollo/                  # Desarrollo y contribución



## 📦 Archivo Histórico├── funcionalidades/             # Features implementadas



### Documentos Archivados### 🏗️ Build y Distribución├── guias/                       # Guías de usuario



Los siguientes documentos han sido completados y archivados en `archivo/`:├── roadmap/                     # Planificación futura



**Planes Completados:**> Guías de compilación y distribución de la aplicación├── tecnico/                     # Documentación técnica

- `PLAN_REFACTORIZACION_V3.0.md` - Refactorización completada ✅

- `PLAN_HOMOGENEIZACION_FORMULARIOS.md` - Homogeneización completada ✅├── validaciones/                # Sistema de validaciones

- `QUICK_WINS_COMPLETADOS.md` - Quick wins aplicados ✅

#### 📦 Documentos Consolidados├── versiones/                   # Changelogs y releases

**Limpiezas Históricas:**

- `LIMPIEZA_PROYECTO_NOV2025.md` - Post-refactorización├── sftp/                        # Configuración SFTP (legacy)

- `LIMPIEZA_REORGANIZACION_OCT2025.md` - Reorganización completa

- `PLAN_CONSOLIDACION_DOCS_DIC2025.md` - Plan de consolidación- [**GUIA_COMPILACION.md**](build/GUIA_COMPILACION.md) ✨ **NUEVO**└── datos ejemplo/               # Datos de prueba



**Algoritmos Históricos:**  - Compilación rápida (macOS DMG + Windows Setup)

- `ALGORITMO_PASADA_6.md` - Algoritmo v2.9 (consolidado en ALGORITMO_ASIGNACION_GUARDIAS.md)

- `PROPUESTA_ALGORITMO_SIMPLE.md` - Base para v3.0 (consolidado)  - Procesos detallados de buildArchivo histórico (comprimido en raíz):

- `RESUMEN_EJECUTIVO_ALGORITMO_V3.md` - Resumen v3.0 (consolidado)

- `INTEGRACION_ALGORITMO_V3.md` - Integración v3.0 (consolidado)  - Distribución vía GitHub Releases└── ARCHIVO_HISTORICO_SPRINTS.tar.gz  # Sprints 1-12 (266 KB)



**Versiones Antiguas:**  - Troubleshooting (5 problemas comunes)```

- Documentación detallada de v2.9 (correcciones, mejoras calendario)

- Sprints históricos (1-12) comprimidos en `ARCHIVO_HISTORICO_SPRINTS.tar.gz` (raíz del proyecto)  - Checklist pre-release completo



### Acceder al Archivo---



- **Ubicación física**: `documentacion/archivo/`#### Guías Específicas por Plataforma

- **Info de sprints**: `desarrollo/ARCHIVO_HISTORICO_INFO.md`

- **Historial de limpiezas**: `desarrollo/HISTORIAL_LIMPIEZAS.md`## 🔍 Buscar Documentación



---- [Build General](build/BUILD.md) - Construcción multiplataforma



## 🔄 Mantenimiento- [Build macOS (DMG)](build/BUILD_DMG.md) - Crear instalador para macOS**Por tema:**



### Última Reorganización- [Build Windows](build/BUILD_WINDOWS.md) - Crear instalador para Windows- **Algoritmos**: `tecnico/ALGORITMO_*.md`



**Fecha:** 2 de Noviembre de 2025  - **Build**: `build/BUILD*.md`

**Cambios:**

- ✅ Eliminados archivos `.DS_Store`#### Distribución- **Versiones**: `versiones/CHANGELOG_*.md`

- ✅ Eliminado `INDICE_RAPIDO.md` (obsoleto, info en README)

- ✅ Eliminada carpeta `validaciones/` (vacía)- **Guías**: `guias/*.md`

- ✅ Movidos 9 documentos históricos a `archivo/`

- ✅ README actualizado a v3.0- [Instrucciones GitHub Release](build/GITHUB_RELEASE_INSTRUCTIONS.md)



**Ver detalles:** [desarrollo/HISTORIAL_LIMPIEZAS.md](desarrollo/HISTORIAL_LIMPIEZAS.md)- [Guía de Distribución v2.9.1](build/GUIA_DISTRIBUCION_v2.9.1.md)**Por versión:**



### Documentos Consolidados- **v2.9.1 (actual)**: `versiones/CHANGELOG_v2.9.1.md`



Algunos documentos han sido consolidados para reducir fragmentación:---- **v3.0 (desarrollo)**: `roadmap/roadmap-v3.0.md`, `tecnico/INTEGRACION_ALGORITMO_V3.md`



1. **HISTORIAL_LIMPIEZAS.md** (desarrollo/)

   - Reemplaza: 3 documentos de limpiezas

### 🎯 Funcionalidades---

2. **ALGORITMO_ASIGNACION_GUARDIAS.md** (tecnico/)

   - Reemplaza: 4 documentos de algoritmos



3. **SISTEMA_PDF_CORPORATIVO.md** (tecnico/) ✨> Documentación de features implementadas## 📝 Notas

   - Centraliza: Estilos, colores y patrones de PDFs



---

- [Funcionalidades Completas](funcionalidades/FUNCIONALIDADES_COMPLETAS.md)- La documentación de SFTP en `sftp/` es legacy (sistema implementado en v2.8)

## 📝 Convenciones

- Para crear nuevos builds, consultar `build/COMPILACION_RAPIDA.md`

### Iconos Utilizados

---- El historial de sprints está comprimido en `ARCHIVO_HISTORICO_SPRINTS.tar.gz` (raíz del proyecto)

- ⭐ = Versión/documento actual

- ✨ = Nuevo/recientemente añadido  - Ver `desarrollo/ARCHIVO_HISTORICO_INFO.md` para más información

- ✅ = Completado

- 🔴 = Obsoleto/deprecated### 📖 Guías de Uso

- 📦 = Archivado

- 🔧 = En desarrollo### 📁 Datos de Ejemplo



### Estructura de Archivos> Guías para usuarios finales y desarrolladores- Ver [datos ejemplo/](datos%20ejemplo/) - Datos para pruebas



- `MAYUSCULAS_CON_UNDERSCORES.md` - Documentos principales

- `minusculas-con-guiones.md` - Documentos secundarios

- `README.md` - Índices de carpeta- [Guía UI Features](guias/GUIA_UI_FEATURES.md) - Interfaz Fluent Design### 🗂️ Mantenimiento del Proyecto



---- [Guía para Probar Algoritmo v3](guias/GUIA_PROBAR_ALGORITMO_V3.md) - Testing del algoritmo- [Limpieza del Proyecto](LIMPIEZA_PROYECTO.md) - Resumen de limpieza realizada



## 🤝 Contribuir a la Documentación- [Atajos de Teclado](guias/atajos-teclado.md) - Shortcuts del sistema- [Plan de Consolidación](PLAN_CONSOLIDACION.md) - Estrategia de consolidación de docs



Si encuentras:

- **Información desactualizada** → Crea un issue

- **Enlaces rotos** → Crea un PR------

- **Falta de claridad** → Sugiere mejoras

- **Documentación útil faltante** → Proponla



**Guía:** [desarrollo/CONTRIBUIR.md](desarrollo/CONTRIBUIR.md)### 🗺️ Roadmap## 🎯 Navegación Rápida



---



## 📞 Soporte> Planificación de futuras versiones| Tema | Enlaces |



- **Issues:** GitHub Issues del proyecto|------|---------|

- **Documentación técnica:** `tecnico/`

- **Historial:** `desarrollo/HISTORIA_SPRINTS.md`- [Roadmap v3.0](roadmap/roadmap-v3.0.md) - Planificación de la versión 3.0| **Instalación** | [Requisitos](REQUISITOS_SISTEMA.md) |



---| **Configuración** | [Email SMTP](CONFIGURACION_EMAIL.md) |



**Proyecto:** Guardias de Patio  ---| **Desarrollo** | [Arquitectura](ARCHITECTURE_PATTERNS.md) \| [Contribuir](CONTRIBUIR.md) |

**Versión:** 3.0.0  

**Mantenido por:** Equipo de desarrollo  | **Sincronización** | [Guía Completa](GUIA_SINCRONIZACION.md) \| [SFTP](sftp/) |

**Última actualización:** 2 de Noviembre de 2025

### 📜 Versiones y Changelogs| **Interfaz** | [UI Features](GUIA_UI_FEATURES.md) |

| **Build** | [General](build/BUILD.md) \| [macOS](build/BUILD_DMG.md) \| [Windows](build/BUILD_WINDOWS.md) |

> Historial de versiones y cambios| **Versiones** | [v2.8](CHANGELOG_v2.8.md) \| [Historial](versiones/) |



- [CHANGELOG v3.0](versiones/CHANGELOG_v3.0.md) - Refactorización arquitectónica---

- [CHANGELOG v2.9.1](versiones/CHANGELOG_v2.9.1.md) - Actualización calendario 2025-2026

- [CHANGELOG v2.9](versiones/CHANGELOG_v2.9.md) - Mejoras de calendario## 📊 Estructura Consolidada (Octubre 2025)

- [Release Notes v2.9.1](versiones/RELEASE_NOTES_v2.9.1.md)

- [Corrección de Equidad v2.9](versiones/CORRECCION_EQUIDAD_v2.9.md)Este directorio ha sido reorganizado para eliminar redundancia y mejorar la navegación:

- [Resumen Corrección v2.9](versiones/RESUMEN_CORRECCION_v2.9.md)

- [Mejoras Calendario v2.9](versiones/MEJORAS_CALENDARIO_v2.9.md)**Archivos Consolidados:**

- ✅ **GUIA_SINCRONIZACION.md** - Combina:

---  - Sistema Multi-usuario

  - Sistema de Bloqueo de Sesión

### 📦 Archivo Histórico  - Lógica de Sincronización

  - Sincronización JSON

> Documentos completados y archivados para referencia histórica  

- ✅ **GUIA_UI_FEATURES.md** - Combina:

**Ubicación**: [`documentacion/archivo/`](archivo/)  - UI Fluent Redesign

  - Validación de Resolución de Pantalla

**Contenido** (13 documentos):  

- ✅ **ARCHITECTURE_PATTERNS.md** - Incluye ahora:

#### Planes Completados  - Patrones arquitectónicos

- PLAN_REFACTORIZACION_V3.0.md  - Guía de Pydantic Schemas (integrada)

- SCRIPTS_REFACTORIZACION.md

- QUICK_WINS_COMPLETADOS.md**Archivos Preservados:**

- 📋 README.md (este archivo)

#### Limpiezas Históricas- 📋 REQUISITOS_SISTEMA.md

- LIMPIEZA_PROYECTO_NOV2025.md- 📋 CONFIGURACION_EMAIL.md

- LIMPIEZA_REORGANIZACION_OCT2025.md- 📋 CONTRIBUIR.md

- PLAN_CONSOLIDACION_DOCS_DIC2025.md- 📋 CHANGELOG_v2.8.md

- 📋 HISTORIA_SPRINTS.md

#### Documentación de Algoritmos (Consolidada)- 📋 LIMPIEZA_PROYECTO.md

- ALGORITMO_PASADA_6.md- 📋 PLAN_CONSOLIDACION.md

- INTEGRACION_ALGORITMO_V3.md- 📋 ARCHITECTURE_PATTERNS.md

- RESUMEN_EJECUTIVO_ALGORITMO_V3.md

- PROPUESTA_ALGORITMO_SIMPLE.md**Resultado:** De 17 archivos MD a 11 archivos, sin pérdida de información.



#### Documentación de Build (Consolidada)---

- COMPILACION_RAPIDA.md

- SOLUCION_COMPILACION.md**Proyecto:** Guardias de Patio  

- CHECKLIST_COMPILACION.md**Versión:** 2.8+  

**Última actualización:** 26 de Octubre de 2025

> **Nota**: Estos documentos han sido consolidados en versiones master (marcadas con ✨ NUEVO) pero se preservan aquí para referencia histórica.

---

## 🗂️ Estructura de Carpetas

```
documentacion/
├── README.md                    # Este archivo
├── INDICE_RAPIDO.md             # Acceso rápido por tema
│
├── desarrollo/                  # 🔧 Desarrollo y contribución
│   ├── HISTORIAL_LIMPIEZAS.md   ✨ Consolidado
│   ├── CONTRIBUIR.md
│   ├── HISTORIA_SPRINTS.md
│   └── ...
│
├── tecnico/                     # ⚙️ Documentación técnica
│   ├── ALGORITMO_ASIGNACION_GUARDIAS.md  ✨ Consolidado
│   ├── PATRON_WIDGETS.md
│   ├── ARCHITECTURE_PATTERNS.md
│   └── ...
│
├── build/                       # 🏗️ Compilación y distribución
│   ├── GUIA_COMPILACION.md      ✨ Consolidado
│   ├── BUILD_DMG.md
│   ├── BUILD_WINDOWS.md
│   └── ...
│
├── funcionalidades/             # 🎯 Features implementadas
│   └── FUNCIONALIDADES_COMPLETAS.md
│
├── guias/                       # 📖 Guías de uso
│   ├── GUIA_UI_FEATURES.md
│   ├── atajos-teclado.md
│   └── ...
│
├── roadmap/                     # 🗺️ Planificación futura
│   └── roadmap-v3.0.md
│
├── versiones/                   # 📜 Changelogs y releases
│   ├── CHANGELOG_v3.0.md
│   ├── CHANGELOG_v2.9.1.md
│   └── ...
│
└── archivo/                     # 📦 Documentos históricos
    ├── PLAN_REFACTORIZACION_V3.0.md
    ├── ALGORITMO_PASADA_6.md
    ├── COMPILACION_RAPIDA.md
    └── ... (13 documentos archivados)
```

---

## 🔍 Buscar Documentación

### Por Tema

| Tema | Ubicación |
|------|-----------|
| **Algoritmos** | `tecnico/ALGORITMO_ASIGNACION_GUARDIAS.md` ✨ |
| **Build** | `build/GUIA_COMPILACION.md` ✨ |
| **Limpiezas** | `desarrollo/HISTORIAL_LIMPIEZAS.md` ✨ |
| **Arquitectura** | `tecnico/ARCHITECTURE_PATTERNS.md` |
| **Widgets** | `tecnico/PATRON_WIDGETS.md` |
| **Versiones** | `versiones/CHANGELOG_*.md` |
| **Guías de Usuario** | `guias/*.md` |

### Por Versión

| Versión | Changelog |
|---------|-----------|
| **v3.0 (actual)** | `versiones/CHANGELOG_v3.0.md` |
| **v2.9.1** | `versiones/CHANGELOG_v2.9.1.md` |
| **v2.9** | `versiones/CHANGELOG_v2.9.md` |

---

## 📊 Métricas de Documentación

### Estado Actual (Nov 2025)

- **Documentos activos**: 50 (-34% desde antes de limpieza)
- **Documentos archivados**: 13
- **Documentos consolidados**: 3 (reemplazan 10 documentos)
- **Categorías**: 8 (desarrollo, tecnico, build, funcionalidades, guias, roadmap, versiones, archivo)

### Documentos Consolidados ✨

1. **HISTORIAL_LIMPIEZAS.md** (desarrollo/)
   - Reemplaza: 3 documentos de limpiezas
   - Contenido: Nov 2025 + Nov 2025 + Oct 2025

2. **ALGORITMO_ASIGNACION_GUARDIAS.md** (tecnico/)
   - Reemplaza: 4 documentos de algoritmos
   - Contenido: Pasada 6 + Integración v3 + Resumen + Propuesta simple

3. **GUIA_COMPILACION.md** (build/)
   - Reemplaza: 3 documentos de compilación
   - Contenido: Compilación rápida + Soluciones + Checklist

### Beneficios de la Consolidación

- ✅ **Menos fragmentación**: Toda la información relacionada en un solo lugar
- ✅ **Más fácil de mantener**: Actualizar 1 archivo en lugar de 3-4
- ✅ **Mejor onboarding**: Nuevos desarrolladores encuentran info más rápido
- ✅ **Sin pérdida de información**: Todo el contenido se preserva
- ✅ **Histórico preservado**: Versiones originales en `archivo/`

---

## 🎯 Navegación Rápida

| ¿Qué necesitas? | Ve a... |
|-----------------|---------|
| **Instalar la app** | [Requisitos del Sistema](tecnico/REQUISITOS_SISTEMA.md) |
| **Compilar** | [GUIA_COMPILACION.md](build/GUIA_COMPILACION.md) ✨ |
| **Contribuir** | [CONTRIBUIR.md](desarrollo/CONTRIBUIR.md) |
| **Entender el algoritmo** | [ALGORITMO_ASIGNACION_GUARDIAS.md](tecnico/ALGORITMO_ASIGNACION_GUARDIAS.md) ✨ |
| **Ver cambios** | [CHANGELOG v3.0](versiones/CHANGELOG_v3.0.md) |
| **Crear widgets** | [PATRON_WIDGETS.md](tecnico/PATRON_WIDGETS.md) |
| **Troubleshooting** | [GUIA_COMPILACION.md](build/GUIA_COMPILACION.md) ✨ |
| **Historial de limpiezas** | [HISTORIAL_LIMPIEZAS.md](desarrollo/HISTORIAL_LIMPIEZAS.md) ✨ |

---

## 📝 Notas Importantes

### Archivos Consolidados (✨)

Los archivos marcados con ✨ son **documentos consolidados** que reemplazan múltiples archivos anteriores. Los archivos originales se preservan en `archivo/` para referencia histórica.

### Organización de Scripts

Los scripts de build (`build_dmg.sh`, `build_windows.bat`, etc.) están en [`scripts/build/`](../scripts/build/) en la raíz del proyecto.

### Datos de Ejemplo

Los datos de ejemplo para pruebas están en la raíz: [`datos ejemplo/`](../datos%20ejemplo/)

---

## 🔄 Historial de Reorganizaciones

### Noviembre 2025 - Post-Refactorización
- ✅ 21 archivos obsoletos eliminados
- ✅ 13 documentos archivados
- ✅ 10 documentos consolidados en 3
- ✅ Reducción: -34% documentos activos

### Octubre 2025 - Reorganización Completa
- ✅ 25+ archivos eliminados/consolidados
- ✅ 19 archivos reubicados
- ✅ Estructura por categorías establecida

Ver [HISTORIAL_LIMPIEZAS.md](desarrollo/HISTORIAL_LIMPIEZAS.md) ✨ para detalles completos.

---

**Proyecto:** Guardias de Patio  
**Versión:** 3.0.0  
**Última actualización:** 1 de Noviembre de 2025
