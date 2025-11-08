# 📚 Documentación - Guardias de Patio

**Versión**: 3.0.2  
**Última actualización**: 8 de noviembre de 2025

Sistema de gestión de guardias de patio para centros educativos. Documentación completa organizada por audiencia y tema.

---

## 📖 Índice Principal

### 🌟 Guías Principales (Consolidadas)

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| **[USER_GUIDE.md](USER_GUIDE.md)** | Guía completa de usuario | 👤 Usuarios finales |
| **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)** | Documentación técnica completa | 👨‍💻 Desarrolladores |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Compilación y distribución | 🚀 DevOps |
| **[CI_CD.md](CI_CD.md)** | Integración y despliegue continuos | 🔄 DevOps |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Cómo contribuir al proyecto | 🤝 Colaboradores |
| **[CHANGELOG.md](CHANGELOG.md)** | Historial de versiones (v1.0-v3.0.2) | 📋 Todos |
| **[SECURITY.md](SECURITY.md)** | Política de seguridad | 🔒 Seguridad |
| **[MAINTENANCE.md](MAINTENANCE.md)** | Guía de mantenimiento | 🛠️ Mantenedores |

### 🎨 UX y Experiencia de Usuario (v3.0.2)

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| **[UX_AUDIT.md](UX_AUDIT.md)** | Auditoría completa de UX (8.2/10) | 🎨 Diseñadores UX |
| **[guias/UX_PATTERNS.md](guias/UX_PATTERNS.md)** | Patrones y convenciones UX | 👨‍💻 Desarrolladores |
| **[guias/KEYBOARD_SHORTCUTS.md](guias/KEYBOARD_SHORTCUTS.md)** | 50+ atajos de teclado | 👤 Usuarios avanzados |
| **[auditoria/UX_CONFIRMACIONES_AUDITORIA.md](auditoria/UX_CONFIRMACIONES_AUDITORIA.md)** | Auditoría de confirmaciones (100% apropiadas) | 🎨 UX/Desarrolladores |

---

## 🎯 Navegación por Rol

### 👤 Usuarios Finales

**Empezar aquí**: [USER_GUIDE.md](USER_GUIDE.md)

**Contenido**:
- ✅ Instalación y primer uso
- ✅ Gestión de profesores, zonas y ausencias
- ✅ Generación de guardias
- ✅ Calendario interactivo
- ✅ Exportación de PDFs e iCalendar
- ✅ Atajos de teclado
- ✅ Troubleshooting

### 👨‍💻 Desarrolladores

**Empezar aquí**: [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)

**Contenido**:
- ✅ Arquitectura Clean Architecture (4 capas)
- ✅ Algoritmo de asignación v3.0
- ✅ Validaciones de negocio con Pydantic
- ✅ Sistema de widgets reutilizables
- ✅ Optimizaciones de rendimiento
- ✅ Sistema de PDFs corporativos
- ✅ Configuraciones (email SMTP, base de datos)
- ✅ Especificaciones técnicas

**Contribuir**: [CONTRIBUTING.md](CONTRIBUTING.md)
- Configuración del entorno
- Workflow de Git
- Estándares de código (PEP 8, type hints)
- **NUEVO**: Guías UX (tooltips, confirmaciones, shortcuts)
- Testing (990 tests, 46.31% coverage)
- Proceso de Pull Request

### 🎨 Diseñadores UX

**Empezar aquí**: [UX_AUDIT.md](UX_AUDIT.md)

**Contenido**:
- ✅ Auditoría completa de 9 formularios
- ✅ Puntuación global: 8.2/10 (MUY BUENO)
- ✅ Métricas: 85% tooltips, 100% confirmaciones
- ✅ Análisis por formulario con recomendaciones
- ✅ Anti-patrones a evitar

**Desarrollar UX**: [guias/UX_PATTERNS.md](guias/UX_PATTERNS.md)
- Filosofía UX (4 principios fundamentales)
- 8 patrones implementados (tooltips, placeholders, confirmaciones, etc.)
- Ejemplos de código real
- Checklist para nuevos formularios
- Plantilla de formulario

**Atajos**: [guias/KEYBOARD_SHORTCUTS.md](guias/KEYBOARD_SHORTCUTS.md)
- 50+ atajos documentados
- Organizados por contexto (global, profesores, zonas, calendario, etc.)
- Priorización: esenciales, útiles, avanzados

### 🚀 DevOps / Build Engineers

**Empezar aquí**: [DEPLOYMENT.md](DEPLOYMENT.md) + [CI_CD.md](CI_CD.md)

**Contenido**:
- ✅ **DEPLOYMENT.md**:
  - Requisitos de compilación (macOS/Windows)
  - Entorno de desarrollo
  - Build de producción con PyInstaller
  - Creación de instaladores (DMG/InnoSetup)
  - Testing de ejecutables
  - Distribución vía GitHub Releases
  - Troubleshooting de compilación
  - Checklist completo

- ✅ **CI_CD.md**:
  - Workflows de GitHub Actions
  - Tests automatizados en múltiples plataformas
  - Configuración de Codecov
  - Releases automatizados
  - Branch protection rules
  - Troubleshooting de CI/CD

### 🛠️ Mantenedores

**Empezar aquí**: [MAINTENANCE.md](MAINTENANCE.md)

**Contenido**:
- ✅ Tareas regulares (diarias/semanales/mensuales)
- ✅ Gestión de base de datos
- ✅ Limpieza de archivos y logs
- ✅ Actualizaciones de dependencias
- ✅ Monitoreo y análisis de logs
- ✅ Estrategia de backups
- ✅ Optimización de rendimiento
- ✅ Checklists de mantenimiento

**Seguridad**: [SECURITY.md](SECURITY.md)
- Versiones soportadas
- Reporte de vulnerabilidades
- Gestión de secretos
- Auditoría de dependencias
- Buenas prácticas

---

## 📂 Estructura de Carpetas

```
documentacion/
├── README.md                    # Este archivo (índice)
│
├── USER_GUIDE.md                # 👤 Guía de usuario completa
├── TECHNICAL_GUIDE.md           # 👨‍💻 Documentación técnica
├── DEPLOYMENT.md                # 🚀 Compilación y distribución
├── CONTRIBUTING.md              # 🤝 Guía de contribución
├── CHANGELOG.md                 # 📋 Historial de versiones
├── SECURITY.md                  # 🔒 Política de seguridad
├── MAINTENANCE.md               # 🛠️ Guía de mantenimiento
│
├── PREMISAS_ASIGNACION_GUARDIAS.md   # Reglas del algoritmo
├── CALENDARIO_MEJORADO_v3.md         # Features calendario v3.0
│
├── auditoria/                   # Auditorías UX y testing
│   ├── UX_TESTING_MANUAL.md
│   └── UX_CONFIRMACIONES_AUDITORIA.md
│
└── archivo/                     # 📦 Documentación histórica
    ├── tecnico/                 # 14 archivos técnicos archivados
    ├── build/                   # 7 archivos de build archivados
    ├── roadmap/                 # 2 archivos de roadmap archivados (v3.0 lanzado)
    ├── funcionalidades/         # 4 archivos de features archivados
    ├── guias/                   # 4 guías archivadas
    ├── versiones/               # 5 changelogs archivados
    └── desarrollo/              # 5 archivos de desarrollo archivados
```

---

## 🔍 Búsqueda Rápida por Tema

| Tema | Documento | Sección |
|------|-----------|---------|
| **Instalación** | USER_GUIDE.md | Instalación y Configuración |
| **Algoritmo** | TECHNICAL_GUIDE.md | Algoritmo de Asignación v3.0 |
| **Arquitectura** | TECHNICAL_GUIDE.md | Arquitectura Clean Architecture |
| **Testing** | CONTRIBUTING.md | Testing |
| **Build macOS** | DEPLOYMENT.md | Build de Producción (macOS) |
| **Build Windows** | DEPLOYMENT.md | Build de Producción (Windows) |
| **Widgets** | TECHNICAL_GUIDE.md | Sistema de Widgets |
| **PDFs** | TECHNICAL_GUIDE.md | Sistema de PDFs Corporativos |
| **Seguridad** | SECURITY.md | Todo el documento |
| **Backups** | MAINTENANCE.md | Backups y Recuperación |
| **Versiones** | CHANGELOG.md | Todo el documento |

---

## 📊 Estadísticas de Documentación

### Fase 4 - Consolidación Completada (Nov 2025)

**Antes**:
- 75 archivos markdown dispersos
- Información duplicada
- Difícil navegación

**Después**:
- ✅ **8 guías principales consolidadas** (CI_CD.md añadida)
- ✅ **41 archivos originales preservados** en `archivo/`
- ✅ **100% de información preservada**
- ✅ **Navegación clara por rol**
- ✅ **CI/CD documentado y operativo**

### Documentos Consolidados

| Guía | Archivos Consolidados | Líneas | Commit |
|------|----------------------|--------|--------|
| TECHNICAL_GUIDE.md | 14 archivos técnicos | 819 | 8ef5aef |
| DEPLOYMENT.md | 7 archivos build | 779 | 1b3a78a |
| USER_GUIDE.md | 8 archivos usuario | 1,047 | 15d4f07 |
| CHANGELOG.md | 5 changelogs | 520 | 70b4edb |
| CONTRIBUTING.md | 5 archivos desarrollo | 748 | 5b6ba28 |
| SECURITY.md | Documento nuevo | 431 | 6b5544b |
| MAINTENANCE.md | Documento nuevo | 718 | 6b5544b |
| CI_CD.md | Documento nuevo | 700+ | Fase 5 |

---

## 🎯 Casos de Uso Comunes

### "Quiero instalar la aplicación"
→ [USER_GUIDE.md](USER_GUIDE.md) - Sección "Instalación y Configuración"

### "Quiero entender cómo funciona el algoritmo"
→ [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - Sección "Algoritmo de Asignación v3.0"  
→ [PREMISAS_ASIGNACION_GUARDIAS.md](PREMISAS_ASIGNACION_GUARDIAS.md)

### "Quiero compilar la aplicación"
→ [DEPLOYMENT.md](DEPLOYMENT.md) - Sección "Build de Producción"

### "Quiero configurar CI/CD o entender los workflows"
→ [CI_CD.md](CI_CD.md) - Todo el documento

### "Quiero contribuir al proyecto"
→ [CONTRIBUTING.md](CONTRIBUTING.md) - Todo el documento

### "Quiero ver qué cambió en v3.0"
→ [CHANGELOG.md](CHANGELOG.md) - Sección "v3.0.0 - 2025-11-01"

### "Quiero reportar una vulnerabilidad"
→ [SECURITY.md](SECURITY.md) - Sección "Reporte de Vulnerabilidades"

### "Quiero hacer un backup de la base de datos"
→ [MAINTENANCE.md](MAINTENANCE.md) - Sección "Backups y Recuperación"

---

## 📦 Archivo Histórico

La carpeta `archivo/` contiene **41 archivos originales** preservados para referencia histórica:

| Categoría | Archivos | Descripción |
|-----------|----------|-------------|
| `archivo/tecnico/` | 14 | Documentación técnica original |
| `archivo/build/` | 7 | Guías de compilación originales |
| `archivo/funcionalidades/` | 4 | Documentación de features |
| `archivo/guias/` | 4 | Guías de usuario originales |
| `archivo/versiones/` | 5 | Changelogs originales |
| `archivo/desarrollo/` | 5 | Docs de desarrollo originales |
| `archivo/roadmap/` | 2 | Roadmaps v3.0 (completados) |

**Razón**: Mantener histórico completo mientras se mejora la navegación.

---

## 📝 Convenciones

### Íconos Utilizados

- ✅ = Completado/Implementado
- 🚀 = Nuevo en v3.0
- 📦 = Archivado/Histórico
- ⚠️ = Importante/Advertencia
- 💡 = Tip/Sugerencia

### Formato de Documentos

- **MAYUSCULAS.md**: Documentos principales consolidados
- **minusculas.md**: Documentos secundarios o específicos

---

## 🤝 Contribuir a la Documentación

Si encuentras:
- **Información desactualizada** → Crea un issue
- **Enlaces rotos** → Crea un PR
- **Falta de claridad** → Sugiere mejoras en un issue
- **Documentación faltante** → Proponla en un issue

**Guía completa**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🔗 Enlaces Útiles

- 📦 [Repositorio GitHub](https://github.com/cferrerobonet/guardias_patio)
- 🐛 [Issues](https://github.com/cferrerobonet/guardias_patio/issues)
- 📝 [Releases](https://github.com/cferrerobonet/guardias_patio/releases)
- 📧 **Soporte**: cferrerobonet@gmail.com

---

**Proyecto**: Guardias de Patio  
**Versión**: 3.0.0  
**Última actualización**: 8 de noviembre de 2025  
**Mantenido por**: Carlos Ferrero Bonet
