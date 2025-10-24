# 📚 Documentación del Proyecto Guardias de Patio

**Versión:** 2.8.0  
**Estado:** ✅ Producción - Estable  
**Fecha:** Octubre 2025  
**Última Actualización:** 24 Octubre 2025

> 🎉 **v2.8.0 Released** - Aplicación estable con 7 bugs corregidos y logo corporativo  
> 📚 [Ver Release Notes](../RELEASE_NOTES_v2.8.0.md) | [Changelog v2.8](CHANGELOG_v2.8.md)

---

## 🎯 Índice Principal

### 1. [Inicio Rápido](#inicio-rápido)
### 2. [Arquitectura](#arquitectura)
### 3. [Desarrollo](#desarrollo)
### 4. [Historial de Desarrollo](#historial-de-desarrollo)
### 5. [Guías de Usuario](#guías-de-usuario)
### 6. [Documentación Técnica](#documentación-técnica)
### 7. [Referencias](#referencias)

---

## 🚀 Inicio Rápido

### ¿Qué es Guardias de Patio?

Sistema de gestión automatizada de guardias de recreo para centros educativos con **Clean Architecture** y **Type Safety**.

**Características principales**:
- ✅ **Asignación automática equitativa** de guardias
- ✅ **Gestión de ausencias y sustituciones**
- ✅ **Vista de calendario interactiva**
- ✅ **Panel de estadísticas** en tiempo real
- ✅ **Importar/Exportar** datos en JSON
- ✅ **Dashboard de observabilidad**
- ✅ **Logo corporativo** en todos los diálogos
- ✅ **Validaciones robustas** con Pydantic

### Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/cferrerobonet/guardias_patio.git
cd guardias_patio

# Crear entorno virtual (Python 3.11+ requerido)
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
alembic upgrade head

# Ejecutar aplicación
python src/main.py
```

### Documentación Esencial

- **Usuario Final**: [Vista de Calendario](guias/vista_calendario.md) - Visualización de guardias
- **Importar/Exportar**: [Guía de Portabilidad](guias/importar_exportar.md) - Backup y migración
- **Desarrollador**: [ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md) - Patrones de arquitectura
- **Contribuidor**: [CONTRIBUIR.md](CONTRIBUIR.md) - Cómo contribuir

---

## 🏗️ Arquitectura

### Visión General

El proyecto sigue **Clean Architecture** con 4 capas:

```
src/
├── domain/              # Lógica de negocio (entities, interfaces)
├── application/         # Casos de uso (orquestación)
├── infrastructure/      # Persistencia (SQLAlchemy, mappers)
└── presentation/        # UI (PyQt6, widgets)
```

### Documentos Clave

| Documento | Descripción | Líneas |
|-----------|-------------|--------|
| **[ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md)** | Patrones arquitectónicos completos | 400 |
| **[SCHEMAS_USAGE_GUIDE.md](SCHEMAS_USAGE_GUIDE.md)** | Uso de Pydantic schemas | 450 |
| **[src/domain/README.md](../src/domain/README.md)** | Módulo de dominio | 350 |
| **[src/infrastructure/README.md](../src/infrastructure/README.md)** | Módulo de infraestructura | 450 |

### Principios Aplicados

- ✅ **SOLID** - Diseño orientado a objetos
- ✅ **DRY** - No repetir código
- ✅ **Clean Architecture** - Separación de capas
- ✅ **Repository Pattern** - Abstracción de persistencia
- ✅ **Use Case Pattern** - Lógica de aplicación

---

## 👨‍💻 Desarrollo

### Estructura del Proyecto

```
guardias_patio/
├── src/                      # Código fuente
│   ├── domain/              # Lógica de negocio
│   ├── application/         # Casos de uso
│   ├── infrastructure/      # Persistencia
│   ├── presentation/        # UI
│   ├── core/                # Utilidades compartidas
│   ├── models/              # Modelos SQLAlchemy
│   └── utils/               # Helpers
├── tests/                    # Tests (831 tests)
├── documentacion/           # Esta carpeta
├── scripts/                 # Scripts de utilidad
├── alembic/                 # Migraciones de BD
└── logs/                    # Logs de aplicación
```

### Stack Tecnológico

| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Python** | 3.11.14 | Lenguaje principal |
| **PyQt6** | 6.7.0 | Interfaz gráfica |
| **SQLAlchemy** | 2.0+ | ORM para BD |
| **Pydantic** | 2.9.2 | Validación de datos |
| **pytest** | 8.4.2 | Testing |
| **mypy** | 1.18.2 | Type checking |
| **structlog** | 24.4.0 | Logging estructurado |

### Comandos Útiles

```bash
# Tests
pytest tests/ -v                 # Todos los tests
pytest tests/ --cov=src          # Con coverage
pytest tests/ -k "test_guardia"  # Tests específicos

# Type checking
mypy src/ --config-file pyproject.toml

# Linting
ruff check src/

# Ejecutar aplicación
python main.py
./run_app.sh  # Script con logs
```

---

## 📊 Historial de Desarrollo

### Evolución del Proyecto

El proyecto se ha desarrollado a través de múltiples sprints, alcanzando actualmente la **versión 2.8.0** estable.

**Documentación de desarrollo**:
- **[HISTORIA_SPRINTS.md](HISTORIA_SPRINTS.md)** - Historia completa de todos los sprints
- **[CHANGELOG_v2.8.md](CHANGELOG_v2.8.md)** - Cambios y correcciones de v2.8.0

### Hitos Principales

| Versión | Fecha | Hitos |
|---------|-------|-------|
| **v2.8.0** | Oct 2025 | 7 bugs corregidos, logo corporativo, actualización automática |
| **v2.7.x** | Sep 2025 | Dashboard observabilidad, sistema de cache |
| **v2.6.x** | Ago 2025 | Clean Architecture, refactorización completa |
| **v2.5.x** | Jul 2025 | Vista calendario, gestión ausencias |
| **v2.0-2.4** | 2025 | Features core, CRUD, generación guardias |

### Estado Actual (v2.8.0)

✅ **Funcionalidades Implementadas**:
- CRUD completo de Profesores y Zonas
- Generación automática de guardias
- Vista de calendario interactiva
- Gestión de ausencias y sustituciones
- Panel de estadísticas
- Importar/Exportar JSON
- Dashboard de observabilidad
- Logo corporativo en todos los diálogos
- Sistema de validaciones robusto

🔄 **En Desarrollo** (Sprint 9):
- Exportación a Excel
- Exportación a PDF por profesor
- Gráficos de estadísticas

📋 **Planificado** (Sprint 10+):
- Preferencias de zonas por profesor
- Sistema de notificaciones
- API REST

---

## 📚 Guías de Usuario

### Gestión Básica

- **[Importar/Exportar](guias/importar_exportar.md)** - Backup y migración de datos
- **[Vista de Calendario](guias/vista_calendario.md)** - Visualización de guardias
- **[Tutorial Importar/Exportar](guias/tutorial_importar_exportar.md)** - Paso a paso con capturas

### Funcionalidades Avanzadas

- **Gestión de Ausencias** - Registro de ausencias y sustituciones
- **Panel de Estadísticas** - Métricas de carga y distribución
- **Dashboard Observabilidad** - Monitoreo del sistema

---

## � Documentación Técnica

## 🔧 Documentación Técnica

### Patrones de Arquitectura

**[ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md)** (400+ líneas)

Guía completa de patrones implementados:
- **Repository Pattern** - Abstracción de persistencia
- **Use Case Pattern** - Orquestación de lógica de negocio
- **Mapper Pattern** - Conversión Model ↔ Entity
- **DTO Pattern** - Transferencia segura de datos
- **Dependency Injection** - Inyección de sesiones
- **Observabilidad** - Sistema de logging y métricas

**Incluye**:
- ✅ 15+ ejemplos de código completos
- ✅ Diagramas arquitectónicos
- ✅ Best practices con ejemplos ✅ BUENO / ❌ MALO

### Schemas con Pydantic

**[SCHEMAS_USAGE_GUIDE.md](SCHEMAS_USAGE_GUIDE.md)** (450+ líneas)

Todo sobre validación de datos con Pydantic 2.0:
- Diferencias: Schemas vs DTOs vs Entities
- Patrón de 4 schemas (Base/Create/Update/Response)
- Validaciones (Field, field_validator, model_validator)
- Conversiones bidireccionales
- Testing de schemas

**Incluye**:
- ✅ 20+ ejemplos de validadores
- ✅ Patrón CRUD completo
- ✅ Tests de ejemplo con pytest

### Validaciones de Negocio

**[validaciones/](validaciones/)**

- **[condiciones_generales_asignacion.md](validaciones/condiciones_generales_asignacion.md)** - Reglas globales
- **[condiciones_particulares_profesores.md](validaciones/condiciones_particulares_profesores.md)** - Restricciones individuales

### Testing

**[tecnico/testing_guide.md](tecnico/testing_guide.md)**

- Estructura de tests
- Fixtures compartidas
- Mocking de base de datos
- Coverage y reportes

---

## 📌 Referencias

### Documentos Clave

| Documento | Descripción | Ubicación |
|-----------|-------------|-----------|
| **README.md** | Documentación principal del proyecto | Raíz del repositorio |
| **RELEASE_NOTES_v2.8.0.md** | Notas del release v2.8.0 | Raíz del repositorio |
| **INDEX.md** | Este documento - Índice completo | documentacion/ |
| **CHANGELOG_v2.8.md** | Changelog detallado v2.8.0 | documentacion/ |
| **CONTRIBUIR.md** | Guía para contribuidores | documentacion/ |
| **HISTORIA_SPRINTS.md** | Historia completa del desarrollo | documentacion/ |

### Stack Tecnológico Completo

| Categoría | Tecnología | Versión | Uso |
|-----------|------------|---------|-----|
| **Lenguaje** | Python | 3.11+ | Backend y lógica |
| **UI** | PyQt6 | 6.7.0 | Interfaz gráfica |
| **ORM** | SQLAlchemy | 2.0+ | Persistencia |
| **Validación** | Pydantic | 2.0+ | Schemas y DTOs |
| **Migraciones** | Alembic | Latest | Versionado de BD |
| **Testing** | pytest | Latest | Tests unitarios |
| **Type Checking** | mypy | Latest | Verificación de tipos |
| **Logging** | structlog | 24.4.0 | Logs estructurados |
| **Linting** | ruff | Latest | Code quality |

### Enlaces Externos

- **GitHub**: https://github.com/cferrerobonet/guardias_patio
- **Releases**: https://github.com/cferrerobonet/guardias_patio/releases
- **Release v2.8.0**: https://github.com/cferrerobonet/guardias_patio/releases/tag/v2.8.0
- **Issues**: https://github.com/cferrerobonet/guardias_patio/issues

---

## 🤝 Contribuir

¿Quieres contribuir al proyecto? Lee la guía completa:

👉 **[CONTRIBUIR.md](CONTRIBUIR.md)**

### Áreas de Contribución

- 🐛 **Bugs** - Reportar o corregir errores
- ✨ **Features** - Proponer nuevas funcionalidades
- 📚 **Documentación** - Mejorar guías y ejemplos
- 🧪 **Tests** - Ampliar cobertura de tests
- 🎨 **UI/UX** - Mejorar interfaz

### Proceso Rápido

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: descripción'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📊 Estadísticas del Proyecto

- **Líneas de código**: ~15,000+
- **Tests**: 124+ unitarios
- **Archivos Python**: 80+
- **Documentación**: 1,650+ líneas técnicas
- **Sprints completados**: 8
- **Versión actual**: 2.8.0
- **Estado**: ✅ Producción - Estable

---

<div align="center">

**📚 Documentación actualizada el 24 de Octubre de 2025**

Made with ❤️ by [Carlos Ferrero Bonet](https://github.com/cferrerobonet)
