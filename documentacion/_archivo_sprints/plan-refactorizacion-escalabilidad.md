# Plan de Refactorización y Escalabilidad v3.0

**Fecha:** 19 de octubre de 2025  
**Objetivo:** Optimizar, refactorizar y hacer el código más escalable y mantenible  
**Estado Actual:** Arquitectura Clean Architecture v2.7.0 con tests comprehensivos

---

## 📊 Análisis del Estado Actual (Post-Sprint 9)

### ✅ Logros Conseguidos

#### � Arquitectura y Testing (Sprints 4-9)
1. **Clean Architecture Implementada** ✅
   - Separación en 4 capas: Presentation, Application, Domain, Infrastructure
   - Inyección de dependencias establecida
   - Patrón Repository implementado (repositories con tests)
   
2. **Suite de Tests Comprehensiva** ✅ (77,541 líneas, ratio 32:1)
   - Infrastructure: Mappers (3,866 líneas), Repositories (13,899 líneas)
   - Domain: Value Objects (1,722 líneas)
   - Application: Use Cases con métricas (2,591 líneas)
   - Presentation: UI Validators (15,741 líneas), Progress Indicators (12,840 líneas)
   - Cross-cutting: Observabilidad (26,882 líneas)
   - Total: ~200+ test methods en ~50+ test classes
   
3. **CI/CD Profesional** ✅
   - GitHub Actions con matrix Python 3.9-3.12
   - Coverage tracking (Codecov)
   - Linting (ruff, black, isort)
   - Security scanning (safety, bandit)

4. **Observabilidad y Monitoring** ✅
   - Sistema de métricas (counters, gauges, histograms)
   - Performance monitoring con detección de degradación
   - Health checks
   - Dashboard UI (4 tabs, auto-refresh)
   - Export Prometheus

5. **Sistema de Caché Avanzado** ✅
   - LRU eviction con OrderedDict
   - Métricas por función
   - Invalidación por regex
   - Access count tracking

6. **Indicadores de Progreso** ✅
   - Pattern consistente: `progress_callback(porcentaje, mensaje)`
   - Implementado en: AsignadorGuardias, ExportadorPDF, ImportadorProfesores
   - UI helper: `ejecutar_con_progreso()`

### 🟡 Áreas en Progreso

#### Moderadas (Necesitan Atención)
1. **Cobertura de Tests Desigual**
   - Utils: 77.65% ✅
   - Cache: Mejorado con tests ✅
   - Services: 6-9% ⚠️ (asignador, calculador)
   - **Objetivo Sprint 10**: Aumentar coverage en services layer

2. **Type Safety Parcial**
   - Type hints en algunos módulos
   - Sin validación mypy strict mode
   - Schemas Pydantic no implementados aún
   - **Objetivo Sprint 10**: mypy strict + Pydantic

3. **4 Tests E2E Pendientes**
   - API mismatches documentados
   - Necesitan actualización de generador
   - No crítico para funcionalidad

#### Menores (Mejoras Incrementales)
4. **Configuración Parcialmente Centralizada**
   - constants.py existe
   - Podría mejorarse con Pydantic Settings
   - Considerar .env file

5. **Documentation Scattered**
   - 73 archivos .md en documentacion/
   - Bien organizado pero podría consolidarse
   - Índice central sería útil

---

## 🎯 Estado de Objetivos de Refactorización

### Fase 1: Arquitectura y Estructura ✅ COMPLETADO (Sprints 4-5)
- ✅ Separar main.py en módulos por responsabilidad
- ✅ Implementar arquitectura Clean Architecture
- ✅ Crear capas: Presentation, Application, Domain, Infrastructure
- ✅ Implementar patrón Repository para datos

### Fase 2: Manejo de Errores y Logging ✅ COMPLETADO (Sprint 6)
- ✅ Sistema centralizado de excepciones (utils/exceptions.py)
- ✅ Logging estructurado con contexto (utils/logger.py)
- ✅ Error boundaries en forms
- ✅ Decoradores para observabilidad

### Fase 3: Type Safety y Validaciones 🟡 PARCIAL (Sprint 7-9)
- ✅ Validadores centralizados (utils/validators.py - 77.65% coverage)
- ✅ Value Objects en domain layer (Email, Turno, HorasContrato)
- ⬜ Type hints completos (mypy strict) - **SPRINT 10**
- ⬜ Schemas con Pydantic - **SPRINT 10**
- ⬜ DTOs completos para transferencia de datos

### Fase 4: Optimización de Performance 🟡 PARCIAL (Sprint 8-9)
- ✅ Sistema de caché avanzado (LRU, métricas, regex invalidation)
- ✅ Metrics tracking por función
- ✅ Query optimizer implementado (utils/query_optimizer.py)
- ⬜ Eager loading sistemático en queries críticas - **SPRINT 10**
- ⬜ Connection pooling mejorado
- ⬜ Async operations donde sea posible (PyQt + asyncio)

### Fase 5: Testing y Quality ✅ MAYORMENTE COMPLETADO (Sprint 9)
- ✅ Tests unitarios comprehensivos (77,541 líneas, ratio 32:1) 🏆
- ✅ Tests E2E (34 tests, 88% passing)
- ✅ Coverage tracking en CI/CD
- ✅ CI/CD pipeline profesional (GitHub Actions, matrix 3.9-3.12)
- ✅ Linting automático (ruff, black, isort)
- ✅ Security scanning (safety, bandit)
- ⬜ Aumentar coverage en services layer (6-9% → >70%) - **SPRINT 10**
- ⬜ Property-based testing (Hypothesis) - **FUTURO**

### Fase 6: Observabilidad ✅ COMPLETADO (Sprint 9)
- ✅ Métricas de performance (counters, gauges, histograms)
- ✅ Health checks
- ✅ Performance monitoring con degradation detection
- ✅ Dashboard UI (4 tabs, auto-refresh, 700 líneas)
- ✅ Structured logging con contexto
- ✅ Export Prometheus format
- ⬜ Error tracking externo (Sentry integration) - **OPCIONAL FUTURO**

---

## 📊 Resumen de Progreso General

| Fase | Estado | Completitud | Sprint |
|------|--------|-------------|--------|
| Fase 1: Arquitectura | ✅ Completado | 100% | 4-5 |
| Fase 2: Errores/Logging | ✅ Completado | 100% | 6 |
| Fase 3: Type Safety | 🟡 Parcial | 60% | 7-9 |
| Fase 4: Performance | 🟡 Parcial | 70% | 8-9 |
| Fase 5: Testing | ✅ Mayormente | 95% | 9 |
| Fase 6: Observabilidad | ✅ Completado | 100% | 9 |

**Progreso total**: ~87% completado 🎉

---

## 🏗️ Nueva Arquitectura Propuesta

```
src/
├── main.py                    # Solo entry point (50 líneas)
├── config/                    # Configuración centralizada
│   ├── __init__.py
│   ├── settings.py           # Settings con Pydantic
│   └── database.py           # Config DB
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── exceptions.py         # Custom exceptions
│   ├── logging.py            # Structured logging
│   └── decorators.py         # Retry, cache, etc.
├── domain/                    # Domain layer (DDD)
│   ├── __init__.py
│   ├── entities/             # Domain entities
│   ├── repositories/         # Repository interfaces
│   └── services/             # Domain services
├── infrastructure/            # Infrastructure layer
│   ├── __init__.py
│   ├── database/             # DB implementation
│   ├── cache/                # Cache implementation
│   └── logging/              # Logging implementation
├── application/               # Application layer
│   ├── __init__.py
│   ├── controllers/          # Controllers
│   ├── dto/                  # Data Transfer Objects
│   └── use_cases/            # Use cases
├── presentation/              # Presentation layer
│   ├── __init__.py
│   ├── views/                # PyQt6 views
│   │   ├── profesor_view.py
│   │   ├── zona_view.py
│   │   ├── guardia_view.py
│   │   └── calendario_view.py
│   ├── widgets/              # Widgets reutilizables
│   └── styles/               # UI styles
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 📝 Plan de Implementación

### Sprint 1: Fundamentos (2-3 días)
**Objetivo:** Establecer bases sin romper funcionalidad

1. **Crear nueva estructura de carpetas**
2. **Implementar config/ con Pydantic Settings**
3. **Crear core/exceptions.py con jerarquía completa**
4. **Implementar core/logging.py con structured logging**
5. **Migrar constants.py a config/settings.py**

### Sprint 2: Domain Layer (3-4 días)
**Objetivo:** Separar lógica de negocio

1. **Crear domain/entities/ (Profesor, Zona, Guardia)**
2. **Implementar domain/repositories/ (interfaces)**
3. **Mover services/ a domain/services/**
4. **Implementar infrastructure/database/ (Repository pattern)**

### Sprint 3: Application Layer (3-4 días)
**Objetivo:** Crear capa de aplicación

1. **Crear application/controllers/**
2. **Implementar application/dto/ (Pydantic models)**
3. **Crear application/use_cases/ (casos de uso)**
4. **Migrar lógica de main.py a controllers**

### Sprint 4: Presentation Layer (4-5 días)
**Objetivo:** Refactorizar UI

1. **Separar las 12 clases de main.py**
2. **Crear presentation/views/ (una por formulario)**
3. **Implementar base classes para widgets comunes**
4. **Refactorizar widgets/ existentes**
5. **main.py queda como entry point mínimo**

### Sprint 5: Testing (3-4 días)
**Objetivo:** Cobertura completa

1. **Setup pytest + fixtures**
2. **Tests unitarios para domain/**
3. **Tests de integración para repositories**
4. **Tests E2E para use cases críticos**
5. **Coverage >80%**

### Sprint 6: Performance (2-3 días)
**Objetivo:** Optimizar queries y cache

1. **Implementar eager loading**
2. **Mejorar cache strategy**
3. **Profiling y benchmarks**
4. **Optimizar queries N+1**

### Sprint 7: Observabilidad (2-3 días)
**Objetivo:** Monitoreo y métricas

1. **Implementar health checks**
2. **Métricas de performance**
3. **Error tracking**
4. **Dashboard de monitoreo**

---

## 🔍 Patrones a Implementar

### Design Patterns
- **Repository Pattern**: Abstracción de acceso a datos
- **Factory Pattern**: Creación de objetos complejos
- **Strategy Pattern**: Algoritmos de asignación
- **Observer Pattern**: Actualización de UI
- **Dependency Injection**: Desacoplamiento

### Architectural Patterns
- **Clean Architecture**: Separación en capas
- **CQRS**: Command Query Responsibility Segregation
- **Unit of Work**: Transacciones
- **DTO Pattern**: Transferencia de datos

---

## 📈 Métricas de Éxito

### Code Quality
- [ ] Complejidad ciclomática < 10 por función
- [ ] main.py < 100 líneas
- [ ] Ningún archivo > 500 líneas
- [ ] Cobertura de tests > 80%
- [ ] mypy strict mode sin errores

### Performance
- [ ] Carga inicial < 2 segundos
- [ ] Queries optimizadas (< 50ms)
- [ ] Sin N+1 queries
- [ ] Cache hit rate > 70%

### Mantenibilidad
- [ ] Documentación completa
- [ ] Type hints 100%
- [ ] Error handling consistente
- [ ] Logging estructurado

---

## 🚀 Quick Wins (Implementar Ya)

### Paso 1: Configuración Centralizada
```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///guardias_patio.db"
    log_level: str = "INFO"
    cache_ttl: int = 300
    max_guardias_por_dia: int = 1
    
    class Config:
        env_file = ".env"
```

### Paso 2: Excepciones Personalizadas
```python
# core/exceptions.py
class GuardiasBaseException(Exception):
    """Base exception"""
    
class ProfesorNotFoundError(GuardiasBaseException):
    """Profesor no encontrado"""
    
class ValidationError(GuardiasBaseException):
    """Error de validación"""
```

### Paso 3: Logging Estructurado
```python
# core/logging.py
import structlog

logger = structlog.get_logger()
logger.info("profesor_created", profesor_id=1, nombre="Juan")
```

### Paso 4: Separar Primera Vista
```python
# presentation/views/profesor_view.py
from application.controllers.profesor_controller import ProfesorController

class ProfesorView(QWidget):
    def __init__(self):
        self.controller = ProfesorController()
```

---

## ⚠️ Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Romper funcionalidad existente | Alto | Tests de regresión antes de cada cambio |
| Tiempo de desarrollo largo | Medio | Implementación incremental por sprints |
| Resistencia al cambio | Bajo | Documentación clara de beneficios |
| Bugs introducidos | Alto | Code review + tests automatizados |

---

## 📚 Referencias y Recursos

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)
- [Python Type Checking - mypy](https://mypy.readthedocs.io/)
- [Pydantic Best Practices](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)

---

## 🎯 Próximos Pasos Inmediatos

1. ✅ Crear este documento de planificación
2. ⬜ Crear estructura de carpetas nueva
3. ⬜ Implementar config/settings.py
4. ⬜ Implementar core/exceptions.py
5. ⬜ Implementar core/logging.py
6. ⬜ Escribir tests para funcionalidad actual (baseline)
7. ⬜ Comenzar migración incremental

---

**Nota:** Esta refactorización se hará de forma **incremental y no disruptiva**. 
El código actual seguirá funcionando mientras migramos módulo por módulo.
