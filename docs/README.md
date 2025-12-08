# 📚 Documentación del Proyecto

Bienvenido a la documentación del sistema de gestión de guardias de patio.

## 📂 Estructura de la Documentación

### 👤 Usuario (`user/`)
Documentación para usuarios finales del sistema.

- **[USER_GUIDE.md](user/USER_GUIDE.md)** - Guía completa de usuario

### 💻 Desarrollo (`dev/`)
Documentación técnica para desarrolladores.

- **[TECHNICAL_GUIDE.md](dev/TECHNICAL_GUIDE.md)** - Guía técnica del sistema
- **[TESTING.md](dev/TESTING.md)** - Estrategia y guía de testing
- **[DEPLOYMENT.md](dev/DEPLOYMENT.md)** - Guía de despliegue
- **[MAINTENANCE.md](dev/MAINTENANCE.md)** - Mantenimiento del sistema
- **[SECURITY.md](dev/SECURITY.md)** - Seguridad y buenas prácticas
- **[CI_CD.md](dev/CI_CD.md)** - Integración y entrega continua
- **[CONTRIBUTING.md](dev/CONTRIBUTING.md)** - Guía para contribuidores
- **[REPOSITORY_PATTERN_GUIDE.md](dev/REPOSITORY_PATTERN_GUIDE.md)** - Patrón Repository
- **[BUILD_WINDOWS_QUICK.md](dev/BUILD_WINDOWS_QUICK.md)** - Compilación Windows
- **[.build-checklist.md](dev/.build-checklist.md)** - Checklist de compilación

### 🏗️ Arquitectura (`architecture/`)
Documentación de diseño y arquitectura del sistema.

- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Arquitectura general del sistema
- **[CLEAN_ARCHITECTURE_PHASE3.md](architecture/CLEAN_ARCHITECTURE_PHASE3.md)** - Clean Architecture implementada
- **[API_REST.md](architecture/API_REST.md)** - Documentación de la API REST
- **[PREMISAS_ASIGNACION_GUARDIAS.md](architecture/PREMISAS_ASIGNACION_GUARDIAS.md)** - **Algoritmo CP-SAT y reglas de negocio** ⭐

### 📋 Información General

- **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios del proyecto

### 📦 Archivo (`archive/`)
Documentación histórica, planes completados y análisis previos. 

Se mantiene por referencia histórica, pero no refleja el estado actual del proyecto.

---

## 🚀 Inicio Rápido

### Para Usuarios
1. Lee la [Guía de Usuario](user/USER_GUIDE.md)
2. Revisa el [CHANGELOG](CHANGELOG.md) para conocer las últimas novedades

### Para Desarrolladores
1. Comienza con la [Guía Técnica](dev/TECHNICAL_GUIDE.md)
2. Revisa la [Arquitectura](architecture/ARCHITECTURE.md)
3. **Lee las [Premisas del Algoritmo](architecture/PREMISAS_ASIGNACION_GUARDIAS.md)** ⭐
4. Consulta [CONTRIBUTING](dev/CONTRIBUTING.md) antes de contribuir

---

## 📊 Estado del Proyecto

- **Versión actual**: 3.2.0
- **Última actualización**: Diciembre 2025
- **Features principales**:
  - ✅ **Algoritmo CP-SAT con equidad perfecta (IE=100%)**
  - ✅ Optimización de consecutividad de guardias
  - ✅ Preferencia de zona (~85% en zona principal)
  - ✅ Dashboard de equidad con visualizaciones matplotlib
  - ✅ API REST con FastAPI (8 endpoints)
  - ✅ Clean Architecture (Phase 3)
  - ✅ Multi-usuario con sincronización
  - ✅ Exportación a PDF e iCalendar
  - ✅ Tests automatizados (990 pasando, 36 skipped)
  - ✅ Cobertura de código: 39.75%

---

**Proyecto**: Guardias de Patio  
**Licencia**: Escuelas Profesionales Luis Amigó  
**Última revisión documental**: 8 de Diciembre 2025
