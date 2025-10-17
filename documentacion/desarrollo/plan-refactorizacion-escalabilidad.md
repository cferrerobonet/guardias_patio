# Plan de Refactorización y Escalabilidad v3.0

**Fecha:** 17 de octubre de 2025  
**Objetivo:** Optimizar, refactorizar y hacer el código más escalable y mantenible  
**Estado Actual:** main.py tiene 2488 líneas (GOD CLASS antipatrón)

---

## 📊 Análisis del Estado Actual

### Problemas Identificados

#### 🔴 Críticos
1. **God Class en main.py** (2488 líneas)
   - 12 clases en un solo archivo
   - Violación de Single Responsibility Principle
   - Difícil de testear y mantener
   
2. **Falta de Separación de Concerns**
   - Lógica de negocio mezclada con UI
   - Sin capa de controladores
   - Acceso directo a BD desde widgets

3. **Manejo de Errores Inconsistente**
   - Try-except dispersos sin patrón
   - Errores genéricos sin contexto
   - No hay logging estructurado de errores

#### 🟡 Moderados
4. **Type Safety Débil**
   - Type hints incompletos
   - Sin validación con Pydantic
   - Datos sin schemas definidos

5. **Queries No Optimizadas**
   - N+1 queries en algunos lugares
   - Sin eager loading
   - Cache básico pero mejorable

6. **Tests Insuficientes**
   - Solo 2 tests manuales
   - Sin tests unitarios automatizados
   - Sin coverage tracking

#### 🟢 Menores
7. **Duplicación de Código**
   - Patrones repetidos en formularios
   - Sin base classes para widgets comunes

8. **Configuración Hardcodeada**
   - Constantes en código
   - Sin archivo de configuración centralizado

---

## 🎯 Objetivos de Refactorización

### Fase 1: Arquitectura y Estructura ⭐ PRIORIDAD
- [ ] Separar main.py en módulos por responsabilidad
- [ ] Implementar arquitectura MVC/MVVM
- [ ] Crear capa de controladores
- [ ] Implementar patrón Repository para datos

### Fase 2: Manejo de Errores y Logging
- [ ] Sistema centralizado de excepciones
- [ ] Logging estructurado con contexto
- [ ] Error boundaries y recovery
- [ ] Decoradores para retry logic

### Fase 3: Type Safety y Validaciones
- [ ] Type hints completos (mypy strict)
- [ ] Schemas con Pydantic
- [ ] Validadores centralizados
- [ ] DTOs para transferencia de datos

### Fase 4: Optimización de Performance
- [ ] Eager loading en queries críticas
- [ ] Connection pooling mejorado
- [ ] Cache L1/L2 strategy
- [ ] Async operations donde sea posible

### Fase 5: Testing y Quality
- [ ] Tests unitarios (>80% coverage)
- [ ] Tests de integración
- [ ] Property-based testing
- [ ] CI/CD pipeline

### Fase 6: Observabilidad
- [ ] Métricas de performance
- [ ] Health checks
- [ ] Error tracking (Sentry-like)
- [ ] Structured logging

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
