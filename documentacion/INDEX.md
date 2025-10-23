# 📚 Documentación del Proyecto Guardias de Patio

**Versión:** 2.7+  
**Estado:** ✅ Producción (100% completado)  
**Fecha:** Octubre 2025

---

## 🎯 Índice Principal

### 1. [Inicio Rápido](#inicio-rápido)
### 2. [Arquitectura](#arquitectura)
### 3. [Desarrollo](#desarrollo)
### 4. [Sprints Completados](#sprints-completados)
### 5. [Guías Técnicas](#guías-técnicas)
### 6. [Referencias](#referencias)

---

## 🚀 Inicio Rápido

### ¿Qué es Guardias de Patio?

Sistema de gestión automatizada de guardias de recreo para centros educativos. Permite:
- ✅ Generar guardias automáticamente
- ✅ Gestionar profesores, zonas y configuración
- ✅ Manejar ausencias y sustituciones
- ✅ Exportar/importar datos (Excel, JSON, PDF)
- ✅ Visualizar calendario y estadísticas

### Instalación y Uso

```bash
# Clonar repositorio
git clone https://github.com/cferrerobonet/guardias_patio.git
cd guardias_patio

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python main.py
```

### Documentación Esencial

- **Usuario Final**: `guias/ejemplos-uso.md` - Cómo usar la aplicación
- **Desarrollador**: `ARCHITECTURE_PATTERNS.md` - Arquitectura del código
- **Contribuidor**: `CONTRIBUIR.md` - Cómo contribuir al proyecto

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

## 📊 Sprints Completados

### Evolución del Proyecto (0% → 100%)

El proyecto se completó en **12 sprints principales** + **3 mini-sprints**:

| Sprint | Objetivo | Progreso | Documento |
|--------|----------|----------|-----------|
| **1-4** | Features core | 0% → 40% | `desarrollo/` |
| **5** | Widgets avanzados | 40% → 50% | `SPRINT_5_WIDGETS.md` |
| **6** | Testing inicial | 50% → 60% | `RESUMEN_FINAL_SPRINT_6.md` |
| **7-8** | Observabilidad | 60% → 70% | `RESUMEN_SPRINT_7_Y_8.md` |
| **9** | Clean Architecture | 70% → 80% | `RESUMEN_SPRINT_9.md` |
| **10** | Testing consolidation | 80% → 85% | `RESUMEN_SPRINT_10.2_4.md` |
| **11** | Cleanup & refactor | 85% → 87% | `RESUMEN_SPRINT_11_COMPLETO.md` |
| **11.5** | Mini-sprints | 87% → 94% | `SPRINT_11_5_RESUMEN.md` |
| **12** | Finalización | 94% → **100%** 🎉 | `SPRINT_12_FINALIZACION.md` |

### Mini-Sprints (Sprint 11.5)

| Mini-Sprint | Foco | Tiempo | Logro |
|-------------|------|--------|-------|
| **A** | Type Safety | 2h | 789 líneas Pydantic schemas |
| **B** | Services Testing | 1.5h | 857 líneas tests, 94.17% coverage |
| **C** | Performance | 4h | -98.6% queries N+1 |

### Sprint 12 - Finalización (100%)

| Tarea | Resultado |
|-------|-----------|
| **12.1** Eager loading | -99% queries con joinedload |
| **12.2** Caching | Sistema inteligente con TTL |
| **12.3** Type Safety | Errores mypy corregidos |
| **12.4** Documentación | 1,650+ líneas técnicas |

**Ver detalles completos:** [SPRINT_12_FINALIZACION.md](SPRINT_12_FINALIZACION.md)

---

## 📖 Guías Técnicas

### Patrones de Arquitectura

**[ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md)** (400 líneas)

Guía completa de patrones implementados:
- Repository Pattern (interfaz + implementación)
- Use Case Pattern (orquestación)
- Mapper Pattern (Model ↔ Entity)
- DTO Pattern (transferencia de datos)
- Dependency Injection
- Observabilidad con decoradores

**Incluye:**
- ✅ 15 ejemplos de código completos
- ✅ 2 diagramas arquitectónicos
- ✅ Best practices (✅ BUENO / ❌ MALO)

### Schemas con Pydantic

**[SCHEMAS_USAGE_GUIDE.md](SCHEMAS_USAGE_GUIDE.md)** (450 líneas)

Todo sobre validación de datos con Pydantic:
- Schemas vs DTOs vs Entities
- Patrón de 4 schemas (Base/Create/Update/Response)
- Validaciones (Field, field_validator, model_validator)
- Conversiones (Entity ↔ Schema ↔ JSON)
- Testing de schemas

**Incluye:**
- ✅ 20 ejemplos de validadores
- ✅ Patrón CRUD completo
- ✅ Tests de ejemplo

### Módulos del Sistema

#### Domain (Lógica de Negocio)

**[src/domain/README.md](../src/domain/README.md)** (350 líneas)

- Entities (GuardiaEntity, ProfesorEntity, ZonaEntity)
- Repository Interfaces (abstracciones)
- Schemas Pydantic
- Domain Services
- Reglas de dependencias

#### Infrastructure (Persistencia)

**[src/infrastructure/README.md](../src/infrastructure/README.md)** (450 líneas)

- Repository Implementations (SQLAlchemy)
- Mappers (Model ↔ Entity)
- Optimizaciones de performance
- Eager loading (evitar N+1)
- Bulk operations

### Otras Guías

| Guía | Contenido |
|------|-----------|
| **guias/ejemplos-uso.md** | Uso de la aplicación (usuario final) |
| **guias/atajos-teclado.md** | Atajos de teclado |
| **CONTRIBUIR.md** | Guía para contribuir |
| **tecnico/caracteristicas-sistema.md** | Características técnicas |
| **validaciones/reglas-completas.md** | Reglas de negocio |

---

## 🎯 Referencias

### Estado Actual del Proyecto

**Versión:** 2.7+  
**Progreso:** 100% ✅  
**Estado:** Listo para producción 🚀

### Métricas Finales

| Métrica | Valor |
|---------|-------|
| **Tests** | 831 passing |
| **Coverage Crítico** | 98% |
| **Coverage Global** | 90.4% |
| **Performance** | <0.1s response time |
| **Queries Optimizadas** | -99% |
| **Type Safety** | 80% |
| **Documentación** | 5,150+ líneas |
| **Líneas de Código** | ~15,000 |

### Logros del Proyecto

✅ Clean Architecture implementada  
✅ Performance optimizada (-99% queries)  
✅ Testing exhaustivo (831 tests)  
✅ Observabilidad completa (métricas + logs)  
✅ Type Safety mejorado (mypy + Pydantic)  
✅ Documentación exhaustiva (5,150+ líneas)  

### Próximos Pasos

El proyecto está **completo al 100%**. Los siguientes pasos son:

1. **Mantenimiento continuo**
   - Actualizar dependencias
   - Monitorear performance
   - Revisar logs y métricas

2. **Evolución basada en feedback**
   - Nuevas features según necesidades
   - Mejoras de UX
   - Optimizaciones adicionales

3. **Integración con sistemas externos** (si aplica)
   - APIs de otros sistemas
   - Exportación a formatos adicionales
   - Sincronización de datos

---

## 📝 Changelog

### Versión 2.7 (Octubre 2025) - ACTUAL

- ✅ Sprint 12 completado (100%)
- ✅ Eager loading en repositories
- ✅ Sistema de caching inteligente
- ✅ Type safety mejorado
- ✅ Documentación técnica completa

Ver detalles: [SPRINT_12_FINALIZACION.md](SPRINT_12_FINALIZACION.md)

### Versión 2.6

- ✅ Clean Architecture implementada
- ✅ Testing consolidado (90%+ coverage)
- ✅ Observabilidad completa

Ver detalles: [CHANGELOG_v2.6.md](CHANGELOG_v2.6.md)

---

## 🤝 Contribuir

¿Quieres contribuir al proyecto? Lee la guía completa:

**[CONTRIBUIR.md](CONTRIBUIR.md)**

Incluye:
- Guía de estilo de código
- Proceso de pull requests
- Convenciones de commits
- Cómo reportar bugs

---

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](../LICENSE)

---

## 🎉 Celebración del 100%

**¡El proyecto está completado al 100%!** 🎉

Ver celebración completa: [PROYECTO_100_COMPLETADO.md](PROYECTO_100_COMPLETADO.md)

---

**Última actualización:** 23 Octubre 2025  
**Mantenedor:** @cferrerobonet  
**Estado:** ✅ Producción
