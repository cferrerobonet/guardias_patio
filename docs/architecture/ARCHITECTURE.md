# 🏗️ Arquitectura de Guardias de Patio

**Versión**: 4.0.0  
**Última actualización**: Enero 2025  
**Patrón**: Clean Architecture + Domain-Driven Design + Domain Services

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Capas de la Arquitectura](#capas-de-la-arquitectura)
3. [Domain Services](#domain-services)
4. [Clean Architecture Phase 3](#clean-architecture-phase-3)
5. [Estructura de Directorios](#estructura-de-directorios)
6. [Flujo de Datos](#flujo-de-datos)
7. [Patrones y Principios](#patrones-y-principios)
8. [Dependencias entre Capas](#dependencias-entre-capas)

---

## 🎯 Visión General

**Guardias de Patio** implementa una arquitectura limpia (Clean Architecture) que separa las responsabilidades en capas concéntricas, donde las capas internas no conocen las externas. En la Fase 3, hemos completado la integración de **Domain Services**, **DTOs**, **Use Cases** y **UI Widgets** especializados.

### Principios Fundamentales

1. **Independencia de Frameworks**: La lógica de negocio no depende de PyQt6 ni SQLAlchemy
2. **Testeable**: Lógica de negocio testeada sin UI ni BD (11/12 tests passing)
3. **Independencia de UI**: UI puede cambiar sin afectar lógica (Widgets consumen Use Cases)
4. **Independencia de BD**: SQLite puede reemplazarse por PostgreSQL
5. **Independencia de agentes externos**: Lógica no depende de servicios externos
6. **Domain Services**: Lógica compleja encapsulada en servicios de dominio reutilizables

---

## 🏛️ Capas de la Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION                             │
│                  (PyQt6 UI, Forms, Widgets)                  │
├─────────────────────────────────────────────────────────────┤
│                     APPLICATION                              │
│              (Use Cases, DTOs, Services)                     │
├─────────────────────────────────────────────────────────────┤
│                     INFRASTRUCTURE                           │
│         (SQLAlchemy Repos, Mappers, Database)                │
├─────────────────────────────────────────────────────────────┤
│                       DOMAIN                                 │
│        (Entities, Value Objects, Interfaces)                 │
└─────────────────────────────────────────────────────────────┘
```

### 1. Domain (Núcleo)

**Propósito**: Lógica de negocio pura, reglas del dominio

**Contenido**:
- `entities/`: Entidades con identidad (ProfesorEntity, GuardiaEntity, etc.)
- `value_objects/`: Objetos de valor inmutables (Email, Turno, etc.)
- `repositories/`: Interfaces de repositorios (abstracciones)
- `services/`: Servicios de dominio con lógica compleja
- `schemas/`: Esquemas Pydantic para validación

**Reglas**:
- ✅ NO depende de ninguna otra capa
- ✅ Solo tipos primitivos, dataclasses, y Pydantic
- ✅ Lógica de negocio pura
- ❌ NO importa de infrastructure, application, presentation

**Ejemplo**:
```python
# src/domain/entities/profesor_entity.py
from dataclasses import dataclass
from domain.value_objects import Email, Turno, HorasContrato

@dataclass
class ProfesorEntity:
    id: int
    nombre_completo: str
    email: Email | None
    horas_contrato: HorasContrato
    turno: Turno
    tutor: bool
```

### 2. Application (Casos de Uso)

**Propósito**: Orquestar la lógica de negocio mediante Use Cases

**Contenido**:
- `use_cases/`: Casos de uso (crear, actualizar, eliminar, listar)
- `dtos/`: Data Transfer Objects (input/output de use cases)
- `controllers/`: Controladores legacy (en desuso)

**Reglas**:
- ✅ Depende de domain (interfaces)
- ✅ Define DTOs para comunicación con presentation
- ✅ Coordina repositorios y servicios
- ❌ NO depende de infrastructure (solo interfaces)
- ❌ NO depende de presentation

**Ejemplo**:
```python
# src/application/use_cases/profesor/crear_profesor.py
from application.dtos import CrearProfesorDTO, ProfesorDTO
from domain.repositories import IProfesorRepository

class CrearProfesorUseCase:
    def __init__(self, session: Session):
        self.repo: IProfesorRepository = SQLAlchemyProfesorRepository(session)
    
    def execute(self, dto: CrearProfesorDTO) -> ProfesorDTO:
        # Validar, crear entidad, guardar
        pass
```

### 3. Infrastructure (Detalles Técnicos)

**Propósito**: Implementaciones concretas de interfaces

**Contenido**:
- `repositories/`: Implementaciones de repositorios con SQLAlchemy
- `mappers/`: Conversión entre entidades y modelos ORM
- `database/`: Configuración de BD

**Reglas**:
- ✅ Implementa interfaces de domain
- ✅ Depende de domain
- ✅ Usa SQLAlchemy, conexiones, etc.
- ❌ NO depende de presentation
- ❌ NO contiene lógica de negocio

**Ejemplo**:
```python
# src/infrastructure/repositories/sqlalchemy_profesor_repository.py
from domain.repositories import IProfesorRepository
from domain.entities import ProfesorEntity

class SQLAlchemyProfesorRepository(IProfesorRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, entity: ProfesorEntity) -> ProfesorEntity:
        # Convertir entidad → modelo ORM → guardar
        pass
```

### 4. Presentation (UI)

**Propósito**: Interfaz de usuario con PyQt6

**Contenido**:
- `forms/`: Formularios CRUD
- `widgets/`: Widgets reutilizables
- `dialogs/`: Diálogos modales
- `components/`: Componentes UI (topbar, etc.)
- `themes/`: Estilos y temas

**Reglas**:
- ✅ Depende de application (use cases)
- ✅ Usa DTOs para comunicarse con use cases
- ✅ PyQt6, eventos, UI
- ❌ NO accede directamente a domain o infrastructure
- ❌ NO contiene lógica de negocio

**Ejemplo**:
```python
# src/presentation/forms/profesor_form.py
from application.use_cases.profesor import CrearProfesorUseCase
from application.dtos import CrearProfesorDTO

class ProfesorForm(QWidget):
    def guardar(self):
        dto = CrearProfesorDTO(nombre=self.input.text(), ...)
        use_case = CrearProfesorUseCase(self.session)
        resultado = use_case.execute(dto)
        # Actualizar UI con resultado
```

### 5. Services (Servicios de Aplicación)

**Propósito**: Servicios complejos que coordinan múltiples operaciones

**Contenido**:
- `asignador_guardias.py`: Algoritmo de asignación de guardias
- `exportador_pdf.py`: Generación de reportes PDF
- `email_service.py`: Envío de emails
- `icalendar_service.py`: Generación de calendarios iCal
- `exportador.py`: Exportación de datos

**Reglas**:
- ✅ Pueden depender de domain y application
- ✅ Coordinan lógica compleja
- ✅ Servicios técnicos (PDF, email, etc.)
- ❌ NO son use cases (no son acciones del usuario)

---

## 📁 Estructura de Directorios

```
src/
├── domain/                      # 🟢 Núcleo - Lógica de Negocio
│   ├── entities/                # Entidades con identidad
│   │   ├── profesor_entity.py
│   │   ├── guardia_entity.py
│   │   └── zona_entity.py
│   ├── value_objects/           # Objetos de valor inmutables
│   │   ├── email.py
│   │   ├── turno.py
│   │   └── horas_contrato.py
│   ├── repositories/            # Interfaces de repositorios
│   │   ├── i_profesor_repository.py
│   │   └── i_guardia_repository.py
│   ├── services/                # Servicios de dominio
│   │   └── validacion_service.py
│   └── schemas/                 # Esquemas Pydantic
│       └── profesor_schema.py
│
├── application/                 # 🔵 Casos de Uso
│   ├── use_cases/               # 12 Use Cases
│   │   ├── profesor/            # CRUD Profesores
│   │   │   ├── crear_profesor.py
│   │   │   ├── actualizar_profesor.py
│   │   │   ├── eliminar_profesor.py
│   │   │   ├── obtener_profesor.py
│   │   │   ├── listar_profesores.py
│   │   │   └── buscar_profesores.py
│   │   ├── zona/                # CRUD Zonas
│   │   ├── guardia/             # Gestión Guardias
│   │   ├── configuracion/       # Configuración
│   │   └── asignacion_guardias/ # Asignación automática
│   └── dtos/                    # Data Transfer Objects
│       ├── profesor_dto.py
│       └── guardia_dto.py
│
├── infrastructure/              # 🟠 Implementaciones
│   ├── repositories/            # Repositorios SQLAlchemy
│   │   ├── sqlalchemy_profesor_repository.py
│   │   └── sqlalchemy_guardia_repository.py
│   ├── mappers/                 # Entidad ↔ ORM
│   │   ├── profesor_mapper.py
│   │   └── guardia_mapper.py
│   └── database/                # Configuración BD
│       └── session_manager.py
│
├── presentation/                # 🟣 Interfaz Usuario (PyQt6)
│   ├── forms/                   # Formularios CRUD
│   │   ├── profesor_form.py
│   │   ├── zona_form.py
│   │   └── profesor_widgets/    # Widgets específicos
│   ├── widgets/                 # Widgets reutilizables
│   │   ├── vista_calendario.py
│   │   ├── table_manager.py
│   │   └── progress_indicators.py
│   ├── dialogs/                 # Diálogos modales
│   │   ├── initial_config_dialog.py
│   │   └── session_locked_dialog.py
│   └── components/              # Componentes UI
│       └── ccleaner_topbar.py
│
├── services/                    # 🟤 Servicios de Aplicación
│   ├── asignador_guardias.py   # Algoritmo asignación
│   ├── exportador_pdf.py        # Reportes PDF
│   ├── email_service.py         # Envío emails
│   └── icalendar_service.py     # Calendarios iCal
│
├── core/                        # 🔴 Core (Logging, Observabilidad)
│   ├── logging.py               # Logging estructurado (structlog)
│   ├── exceptions.py            # Jerarquía de excepciones
│   └── observability/           # Métricas y monitoring
│       ├── metrics.py
│       └── decorators.py
│
├── config/                      # ⚙️ Configuración
│   └── settings.py              # Pydantic Settings
│
├── sync/                        # 🔄 Sincronización SFTP
│   ├── sync_manager.py
│   └── data_exporter.py
│
├── utils/                       # 🛠️ Utilidades
│   ├── ui_helpers.py
│   └── repository_cache.py
│
├── models/                      # 📊 Modelos ORM (Legacy)
│   └── models.py                # SQLAlchemy models
│
└── database/                    # 💾 Base de Datos
    └── db_manager.py
```

---

## 🔄 Flujo de Datos

### Ejemplo: Crear un Profesor

```
1. USER ACTION (Presentation)
   └─> ProfesorForm.guardar() clicked
       └─> Crea CrearProfesorDTO con datos del form

2. USE CASE (Application)
   └─> CrearProfesorUseCase.execute(dto)
       ├─> Valida DTO
       ├─> Crea ProfesorEntity (domain)
       └─> Llama a repository.save(entity)

3. REPOSITORY (Infrastructure)
   └─> SQLAlchemyProfesorRepository.save(entity)
       ├─> Convierte Entity → ORM Model (mapper)
       ├─> session.add(model)
       ├─> session.commit()
       └─> Convierte ORM Model → Entity

4. RETURN (Application → Presentation)
   └─> Use Case retorna ProfesorDTO
       └─> Form actualiza tabla con nuevo profesor
```

### Diagrama de Dependencias

```
┌──────────────┐
│ PRESENTATION │ ───┐
└──────────────┘    │
                    ▼
┌──────────────┐    ┌──────────────┐
│   SERVICES   │◄───│ APPLICATION  │
└──────────────┘    └──────────────┘
        │                   │
        ▼                   ▼
┌──────────────────────────────────┐
│       INFRASTRUCTURE              │
└──────────────────────────────────┘
                    │
                    ▼
            ┌──────────────┐
            │    DOMAIN    │
            └──────────────┘
                  (Core)
```

---

## 🎨 Patrones y Principios

### Patrones Implementados

1. **Repository Pattern**: Abstracción de acceso a datos
   - Interfaces en `domain/repositories/`
   - Implementaciones en `infrastructure/repositories/`

2. **Use Case Pattern**: Cada acción del usuario es un use case
   - `CrearProfesorUseCase`, `AsignarGuardiaUseCase`, etc.

3. **DTO Pattern**: Transferencia de datos entre capas
   - `CrearProfesorDTO`, `ProfesorDTO`, etc.

4. **Mapper Pattern**: Conversión entre entidades y modelos
   - `ProfesorMapper`, `GuardiaMapper`

5. **Dependency Injection**: Inyección manual de dependencias
   - Use cases reciben session en __init__
   - Repositories inyectados en use cases

6. **Value Objects**: Objetos inmutables para conceptos del dominio
   - `Email`, `Turno`, `HorasContrato`

### Principios SOLID

- **S**ingle Responsibility: Cada clase tiene una responsabilidad
- **O**pen/Closed: Extensible sin modificar código existente
- **L**iskov Substitution: Interfaces intercambiables
- **I**nterface Segregation: Interfaces específicas
- **D**ependency Inversion: Dependencia de abstracciones

---

## 🔗 Dependencias entre Capas

### ✅ Reglas de Dependencia (OBLIGATORIAS)

```python
# ✅ PERMITIDO
# Presentation → Application
from application.use_cases.profesor import CrearProfesorUseCase

# Application → Domain (interfaces)
from domain.repositories import IProfesorRepository

# Infrastructure → Domain
from domain.entities import ProfesorEntity

# Application → Infrastructure (solo para crear instancias)
from infrastructure.repositories import SQLAlchemyProfesorRepository
```

```python
# ❌ PROHIBIDO
# Domain → Infrastructure
from infrastructure.repositories import SQLAlchemyProfesorRepository  # ❌

# Domain → Application
from application.use_cases import CrearProfesorUseCase  # ❌

# Domain → Presentation
from presentation.forms import ProfesorForm  # ❌

# Infrastructure → Presentation
from presentation.widgets import TableManager  # ❌
```

### Verificación de Arquitectura

```bash
# Verificar que domain no depende de otras capas
grep -r "from infrastructure" src/domain/ --include="*.py"  # Debe estar vacío
grep -r "from application" src/domain/ --include="*.py"     # Debe estar vacío
grep -r "from presentation" src/domain/ --include="*.py"    # Debe estar vacío

# ✅ Salida esperada: Sin resultados (limpio)
```

---

## 📊 Estadísticas

| Capa             | Archivos | Líneas de Código | Cobertura Tests |
|------------------|----------|------------------|-----------------|
| Domain           | ~30      | ~3,000          | ~95%            |
| Application      | ~40      | ~5,000          | ~90%            |
| Infrastructure   | ~25      | ~3,500          | ~85%            |
| Presentation     | ~60      | ~18,000         | ~60%            |
| Services         | ~10      | ~8,000          | ~70%            |
| **TOTAL**        | **~165** | **~41,000**     | **~75%**        |

---

## 🚀 Próximos Pasos

### Mejoras Arquitectónicas Pendientes

1. **Eliminar carpeta `/models` legacy**
   - Migrar modelos ORM a `infrastructure/database/models.py`
   - Deprecar imports de `models.models`

2. **Consolidar `/services` en `/application`**
   - Evaluar si algunos servicios son use cases
   - Documentar claramente cuándo usar services vs use cases

3. **Mejorar separación UI/Lógica**
   - Algunos widgets tienen lógica de negocio
   - Extraer a use cases cuando corresponda

---

## 📚 Referencias

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)

---

## ⚠️ Deuda Técnica Arquitectónica

### Violaciones Conocidas (Auditoría FASE 2 - 12 nov 2025)

#### 1. Application → Infrastructure (Imports Directos)

**Cantidad**: 6 violaciones en use cases  
**Severidad**: Media  
**Impacto**: Dificulta testing, rompe Dependency Inversion Principle (DIP)

**Archivos afectados**:
1. `application/use_cases/guardia/obtener_guardias.py`
2. `application/use_cases/guardia/asignar_guardia.py`
3. `application/use_cases/profesor/listar_profesores.py`
4. `application/use_cases/profesor/obtener_profesor.py`
5. `application/use_cases/profesor/crear_profesor.py` (2 imports)

**Patrón actual** ❌:
```python
from infrastructure.repositories import SQLAlchemyProfesorRepository

class ListarProfesores:
    def __init__(self, session: Session):
        self.repo = SQLAlchemyProfesorRepository(session)
```

**Patrón esperado** ✅:
```python
from domain.repositories import ProfesorRepositoryProtocol

class ListarProfesores:
    def __init__(self, repo: ProfesorRepositoryProtocol):
        self.repo = repo
```

**Esfuerzo de corrección**: 2-4 horas  
**Prioridad**: Media (no urgente, funciona correctamente)  
**Roadmap**: Corregir en fase futura de refinamiento arquitectónico

**Beneficios de corregir**:
- ✅ Testing simplificado (mockear interfaces es fácil)
- ✅ Cumplimiento DIP (depender de abstracciones)
- ✅ Facilita cambio de backend (SQLite → PostgreSQL)

#### 2. Ubicación de `/services`

**Estado actual**: `src/services/` (raíz de src)  
**Ubicación ideal**: `src/application/services/`  
**Decisión**: **Mantener como está** (pragmatismo)

**Justificación**:
- ✅ Cohesión: 13 archivos (361KB) bien organizados
- ✅ Separación clara: Distintos de use cases
- ✅ Funcionan correctamente
- ⚠️ Mover requiere actualizar 100+ imports sin beneficio inmediato

**Recomendación**: Documentar como "Application Services Layer" y mantener ubicación actual.

---

## 📐 Diagrama de Dependencias Reales

Ver diagrama completo en: `documentacion/diagramas/arquitectura_dependencias.md`

**Conformidad por capa**:

| Capa | Conformidad | Detalle |
|------|-------------|---------|
| **Domain** | ✅ 100% | Puro, sin dependencias externas |
| **Application** | ⚠️ 85% | 6 imports directos a infrastructure |
| **Infrastructure** | ✅ 95% | Correctamente separada |
| **Presentation** | ✅ 100% | Solo usa Use Cases |
| **Services** | ⚠️ N/A | Ubicación pragmática (src/services/) |

**Puntuación Global**: ⭐⭐⭐⭐ (4/5) - **Muy Bueno**

---

**Última revisión**: 12 de noviembre de 2025  
**Fase**: 4 - Consolidación de Documentación  
**Estado**: ✅ Arquitectura auditada, violaciones documentadas  
**Auditoría**: Ver `documentacion/auditoria/consolidacion_fase2.md`
