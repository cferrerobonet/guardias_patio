# Guía de Patrones de Arquitectura

**Proyecto:** Guardias de Patio  
**Versión:** 2.7+  
**Fecha:** 23 Octubre 2025

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Clean Architecture Overview](#clean-architecture-overview)
3. [Repository Pattern](#repository-pattern)
4. [Use Case Pattern](#use-case-pattern)
5. [Mapper Pattern](#mapper-pattern)
6. [DTO Pattern](#dto-pattern)
7. [Dependency Injection](#dependency-injection)
8. [Patrones de Observabilidad](#patrones-de-observabilidad)
9. [Ejemplos Completos](#ejemplos-completos)
10. [Best Practices](#best-practices)

---

## 🎯 Introducción

Este documento describe los **patrones arquitectónicos** utilizados en el proyecto Guardias de Patio. El objetivo es mantener una arquitectura **limpia, escalable y testeable** basada en **Clean Architecture** de Robert C. Martin.

### Principios Fundamentales

1. **Separación de Concerns**: Cada capa tiene una responsabilidad única
2. **Dependency Inversion**: Las dependencias apuntan hacia el dominio
3. **Testability**: Código fácil de probar con mocks
4. **Mantenibilidad**: Cambios localizados, bajo acoplamiento
5. **Type Safety**: Tipado estricto con mypy y Pydantic

---

## 🏗️ Clean Architecture Overview

### Estructura de Capas

```
┌─────────────────────────────────────────────────┐
│         Presentation Layer (UI/PyQt6)           │
│  - Widgets, Vistas, Formularios                │
│  - Validadores UI, Progress Indicators          │
└─────────────────────────────────────────────────┘
                     ↓ usa
┌─────────────────────────────────────────────────┐
│        Application Layer (Use Cases)            │
│  - Lógica de aplicación                        │
│  - Orquestación de dominio                     │
│  - DTOs para input/output                       │
└─────────────────────────────────────────────────┘
                     ↓ usa
┌─────────────────────────────────────────────────┐
│         Domain Layer (Entities + Rules)         │
│  - Entities: GuardiaEntity, ProfesorEntity      │
│  - Value Objects: TurnoVO, DisponibilidadVO     │
│  - Repository Interfaces (abstracciones)        │
│  - Business Rules (validaciones de dominio)     │
└─────────────────────────────────────────────────┘
                     ↑ implementa
┌─────────────────────────────────────────────────┐
│    Infrastructure Layer (Persistence/External)  │
│  - Repository Implementations (SQLAlchemy)      │
│  - Mappers (Model ↔ Entity)                    │
│  - Database Models (ORM)                        │
│  - External Services                            │
└─────────────────────────────────────────────────┘
```

### Regla de Dependencias

**Las dependencias fluyen hacia adentro:**

- ❌ **Domain NO puede** depender de Application, Presentation o Infrastructure
- ✅ **Infrastructure depende** de Domain (implementa interfaces)
- ✅ **Application depende** de Domain (usa entities + repositories)
- ✅ **Presentation depende** de Application (llama use cases)

---

## 📦 Repository Pattern

### Concepto

El **Repository Pattern** abstrae la lógica de acceso a datos, proporcionando una interfaz tipo "colección en memoria" para las entidades del dominio.

### Beneficios

- ✅ **Testability**: Mock fácil del repository en tests
- ✅ **Separation**: Dominio desacoplado de BD
- ✅ **Flexibility**: Cambiar DB sin tocar dominio
- ✅ **SOLID**: Dependency Inversion Principle

### Estructura

#### 1. Interfaz en Domain (IRepository)

```python
# src/domain/repositories/guardia_repository.py
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from domain.entities import GuardiaEntity


class IGuardiaRepository(ABC):
    """
    Interfaz del repositorio de Guardia.
    
    Define operaciones de acceso a datos sin acoplarse
    a una implementación específica (SQLAlchemy, MongoDB, etc.)
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[GuardiaEntity]:
        """Obtiene una guardia por ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> list[GuardiaEntity]:
        """Obtiene todas las guardias."""
        pass
    
    @abstractmethod
    def save(self, entity: GuardiaEntity) -> GuardiaEntity:
        """Guarda una guardia (crear o actualizar)."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Elimina una guardia por ID."""
        pass
    
    @abstractmethod
    def find_by_fecha(self, fecha: date) -> list[GuardiaEntity]:
        """Busca guardias por fecha (query específica del dominio)."""
        pass
```

**Características:**
- Define el **contrato** (interfaz abstracta)
- Usa **entidades del dominio** (GuardiaEntity)
- **NO menciona** SQLAlchemy, tablas, queries SQL

#### 2. Implementación en Infrastructure

```python
# src/infrastructure/repositories/sqlalchemy_guardia_repository.py
from sqlalchemy.orm import Session, joinedload
from domain.repositories import IGuardiaRepository
from domain.entities import GuardiaEntity
from models.models import Guardia
from infrastructure.mappers import GuardiaMapper


class SQLAlchemyGuardiaRepository(IGuardiaRepository):
    """Implementación de IGuardiaRepository usando SQLAlchemy."""
    
    def __init__(self, session: Session):
        self.session = session
        self.mapper = GuardiaMapper()
    
    def get_all(self) -> list[GuardiaEntity]:
        """
        Obtiene todas las guardias con eager loading.
        
        Nota: Usa joinedload para evitar N+1 queries.
        """
        models = (
            self.session.query(Guardia)
            .options(
                joinedload(Guardia.profesor),
                joinedload(Guardia.zona)
            )
            .all()
        )
        return self.mapper.to_entities(models)
    
    def find_by_fecha(self, fecha: date) -> list[GuardiaEntity]:
        """Busca guardias por fecha con eager loading."""
        models = (
            self.session.query(Guardia)
            .options(
                joinedload(Guardia.profesor),
                joinedload(Guardia.zona)
            )
            .filter(Guardia.fecha == fecha)
            .all()
        )
        return self.mapper.to_entities(models)
```

**Características:**
- **Implementa** la interfaz IGuardiaRepository
- Usa **SQLAlchemy** (Query, Session, joinedload)
- Convierte **Model → Entity** con Mapper
- **Optimizaciones** (eager loading) están aquí

#### 3. Uso en Use Case

```python
# src/application/use_cases/guardias/listar_guardias_fecha.py
from datetime import date
from domain.repositories import IGuardiaRepository


class ListarGuardiasFechaUseCase:
    """Use case para listar guardias de una fecha."""
    
    def __init__(self, guardia_repository: IGuardiaRepository):
        # ✅ Recibe INTERFAZ, no implementación concreta
        self.guardia_repository = guardia_repository
    
    def execute(self, fecha: date) -> list[GuardiaEntity]:
        """Ejecuta el caso de uso."""
        return self.guardia_repository.find_by_fecha(fecha)
```

**Beneficios:**
- Use case **NO conoce** SQLAlchemy
- Fácil de **testear** con mock:

```python
# En tests
mock_repo = Mock(spec=IGuardiaRepository)
mock_repo.find_by_fecha.return_value = [guardia1, guardia2]
use_case = ListarGuardiasFechaUseCase(mock_repo)
```

---

## 🎬 Use Case Pattern

### Concepto

Cada **Use Case** representa una **acción del usuario** o un **flujo de negocio** completo. Orquesta el dominio sin contener lógica de negocio compleja.

### Estructura

```python
# src/application/use_cases/guardias/generar_guardias.py
from datetime import date
from domain.repositories import IGuardiaRepository, IProfesorRepository
from domain.services import GeneradorGuardiasService
from application.dtos import GenerarGuardiasInputDTO, GuardiaDTO


class GenerarGuardiasUseCase:
    """
    Use Case: Generar guardias para una fecha.
    
    Responsabilidades:
    - Validar input (DTO)
    - Coordinar repositories y services
    - Manejar transacciones
    - Retornar DTOs (output)
    """
    
    def __init__(
        self,
        guardia_repository: IGuardiaRepository,
        profesor_repository: IProfesorRepository,
        generador_service: GeneradorGuardiasService
    ):
        self.guardia_repository = guardia_repository
        self.profesor_repository = profesor_repository
        self.generador_service = generador_service
    
    def execute(self, input_dto: GenerarGuardiasInputDTO) -> list[GuardiaDTO]:
        """
        Ejecuta el caso de uso.
        
        Args:
            input_dto: Datos de entrada validados con Pydantic
            
        Returns:
            Lista de guardias generadas (DTOs)
        """
        # 1. Validar que no existan guardias para esa fecha
        existentes = self.guardia_repository.find_by_fecha(input_dto.fecha)
        if existentes:
            raise ValidationError("Ya existen guardias para esa fecha")
        
        # 2. Obtener profesores disponibles
        profesores = self.profesor_repository.find_disponibles(
            fecha=input_dto.fecha,
            turno=input_dto.turno
        )
        
        # 3. Generar guardias (lógica de negocio en service)
        guardias_entities = self.generador_service.generar(
            fecha=input_dto.fecha,
            turno=input_dto.turno,
            profesores_disponibles=profesores
        )
        
        # 4. Persistir
        guardias_guardadas = [
            self.guardia_repository.save(g) for g in guardias_entities
        ]
        
        # 5. Retornar DTOs
        return [GuardiaDTO.from_entity(g) for g in guardias_guardadas]
```

### Características Clave

| Aspecto | Responsabilidad |
|---------|-----------------|
| **Input** | Recibe DTOs validados con Pydantic |
| **Orquestación** | Coordina repositories + services |
| **Transacciones** | Maneja commit/rollback (con session) |
| **Lógica Negocio** | Delega a domain services o entities |
| **Output** | Retorna DTOs (no entities directamente) |
| **Observabilidad** | Decorado con `@with_metrics` |

---

## 🔄 Mapper Pattern

### Concepto

Los **Mappers** convierten entre **Models (ORM)** y **Entities (Domain)**. Mantienen el dominio desacoplado de la BD.

### Estructura

```python
# src/infrastructure/mappers/guardia_mapper.py
from models.models import Guardia  # SQLAlchemy Model
from domain.entities import GuardiaEntity  # Domain Entity


class GuardiaMapper:
    """Mapper bidireccional: Model ↔ Entity"""
    
    def to_entity(self, model: Guardia) -> GuardiaEntity:
        """
        Convierte SQLAlchemy Model → Domain Entity.
        
        Args:
            model: Modelo de SQLAlchemy (tabla guardias)
            
        Returns:
            Entidad del dominio
        """
        return GuardiaEntity(
            id=model.id,
            fecha=model.fecha,
            turno=model.turno,
            recreo=model.recreo,
            profesor_id=model.profesor_id,
            zona_id=model.zona_id,
            es_sustitucion=model.es_sustitucion,
            observaciones=model.observaciones
        )
    
    def to_entities(self, models: list[Guardia]) -> list[GuardiaEntity]:
        """Convierte lista de models a entities."""
        return [self.to_entity(m) for m in models]
    
    def to_model(
        self,
        entity: GuardiaEntity,
        existing_model: Guardia | None = None
    ) -> Guardia:
        """
        Convierte Domain Entity → SQLAlchemy Model.
        
        Args:
            entity: Entidad del dominio
            existing_model: Modelo existente (para updates)
            
        Returns:
            Modelo de SQLAlchemy listo para persistir
        """
        if existing_model:
            # Update: modificar modelo existente
            existing_model.fecha = entity.fecha
            existing_model.turno = entity.turno
            existing_model.recreo = entity.recreo
            existing_model.profesor_id = entity.profesor_id
            existing_model.zona_id = entity.zona_id
            existing_model.es_sustitucion = entity.es_sustitucion
            existing_model.observaciones = entity.observaciones
            return existing_model
        else:
            # Create: nuevo modelo
            return Guardia(
                id=entity.id,
                fecha=entity.fecha,
                turno=entity.turno,
                recreo=entity.recreo,
                profesor_id=entity.profesor_id,
                zona_id=entity.zona_id,
                es_sustitucion=entity.es_sustitucion,
                observaciones=entity.observaciones
            )
```

### Beneficios

- ✅ **Separation**: Domain no conoce SQLAlchemy
- ✅ **Evolution**: Cambiar DB schema sin tocar domain
- ✅ **Testing**: Entities sin necesitar BD
- ✅ **Type Safety**: Conversión explícita y tipada

---

## 📦 DTO Pattern

### Concepto

**Data Transfer Objects** son objetos inmutables validados con **Pydantic** para transferir datos entre capas.

### Tipos de DTOs

#### 1. Input DTO (Request)

```python
# src/application/dtos/guardia_input_dto.py
from datetime import date
from pydantic import BaseModel, Field, field_validator


class CrearGuardiaInputDTO(BaseModel):
    """
    DTO de entrada para crear una guardia.
    
    Validaciones con Pydantic.
    """
    fecha: date = Field(..., description="Fecha de la guardia")
    turno: str = Field(..., pattern="^(MAÑANA|TARDE)$")
    recreo: int = Field(..., ge=1, le=3, description="Número de recreo (1-3)")
    profesor_id: int = Field(..., gt=0)
    zona_id: int = Field(..., gt=0)
    
    @field_validator('fecha')
    @classmethod
    def fecha_no_pasada(cls, v: date) -> date:
        """Valida que la fecha no sea pasada."""
        from datetime import date as date_today
        if v < date_today.today():
            raise ValueError("No se pueden crear guardias en fechas pasadas")
        return v
    
    model_config = {
        'json_schema_extra': {
            'examples': [{
                'fecha': '2025-10-25',
                'turno': 'MAÑANA',
                'recreo': 1,
                'profesor_id': 5,
                'zona_id': 2
            }]
        }
    }
```

#### 2. Output DTO (Response)

```python
# src/application/dtos/guardia_dto.py
from datetime import date
from pydantic import BaseModel, Field


class GuardiaDTO(BaseModel):
    """
    DTO de salida para una guardia.
    
    Incluye datos calculados y relaciones.
    """
    id: int
    fecha: date
    turno: str
    recreo: int
    profesor_nombre: str  # ✨ Relación resuelta
    zona_nombre: str      # ✨ Relación resuelta
    es_sustitucion: bool = False
    observaciones: str | None = None
    
    @classmethod
    def from_entity(cls, entity: GuardiaEntity) -> "GuardiaDTO":
        """
        Factory method: Entity → DTO.
        
        Nota: Requiere que entity tenga profesor y zona cargados.
        """
        return cls(
            id=entity.id,
            fecha=entity.fecha,
            turno=entity.turno,
            recreo=entity.recreo,
            profesor_nombre=entity.profesor.nombre_completo if entity.profesor else "N/A",
            zona_nombre=entity.zona.nombre_zona if entity.zona else "N/A",
            es_sustitucion=entity.es_sustitucion,
            observaciones=entity.observaciones
        )
    
    model_config = {
        'from_attributes': True  # Para trabajar con SQLAlchemy models
    }
```

### DTO vs Entity vs Model

| Aspecto | DTO | Entity | Model |
|---------|-----|--------|-------|
| **Capa** | Application | Domain | Infrastructure |
| **Propósito** | Transferir datos | Lógica de negocio | Persistencia |
| **Validación** | Pydantic | Manual/Property | SQLAlchemy |
| **Mutabilidad** | Inmutable | Mutable (con reglas) | Mutable (ORM) |
| **Serialización** | JSON/API | No directa | BD |
| **Ejemplo** | `CrearGuardiaInputDTO` | `GuardiaEntity` | `Guardia` (ORM) |

---

## 💉 Dependency Injection

### Concepto

**Dependency Injection** invierte el control: en lugar de que el objeto cree sus dependencias, las recibe del exterior.

### Implementación Manual (Sin Framework)

```python
# src/main.py
from sqlalchemy.orm import Session
from infrastructure.repositories import (
    SQLAlchemyGuardiaRepository,
    SQLAlchemyProfesorRepository
)
from application.use_cases import GenerarGuardiasUseCase
from domain.services import GeneradorGuardiasService


def create_use_case(session: Session) -> GenerarGuardiasUseCase:
    """
    Factory function para crear use case con dependencias.
    
    Este patrón facilita testing y configuración.
    """
    # 1. Crear repositories (Infrastructure)
    guardia_repo = SQLAlchemyGuardiaRepository(session)
    profesor_repo = SQLAlchemyProfesorRepository(session)
    
    # 2. Crear services (Domain)
    generador_service = GeneradorGuardiasService()
    
    # 3. Inyectar en use case (Application)
    use_case = GenerarGuardiasUseCase(
        guardia_repository=guardia_repo,
        profesor_repository=profesor_repo,
        generador_service=generador_service
    )
    
    return use_case


# Uso en UI
def on_generar_button_clicked():
    """Handler del botón Generar en la UI."""
    with get_db_session() as session:
        use_case = create_use_case(session)
        
        input_dto = CrearGuardiaInputDTO(
            fecha=date.today(),
            turno="MAÑANA",
            recreo=1,
            profesor_id=5,
            zona_id=2
        )
        
        result = use_case.execute(input_dto)
```

### Testing con DI

```python
# tests/test_generar_guardias_use_case.py
from unittest.mock import Mock
import pytest


def test_generar_guardias_success():
    """Test con mocks gracias a DI."""
    # Arrange: Crear mocks
    mock_guardia_repo = Mock(spec=IGuardiaRepository)
    mock_profesor_repo = Mock(spec=IProfesorRepository)
    mock_service = Mock(spec=GeneradorGuardiasService)
    
    # Configurar comportamiento
    mock_profesor_repo.find_disponibles.return_value = [profesor1, profesor2]
    mock_service.generar.return_value = [guardia1, guardia2]
    
    # Act: Inyectar mocks
    use_case = GenerarGuardiasUseCase(
        guardia_repository=mock_guardia_repo,
        profesor_repository=mock_profesor_repo,
        generador_service=mock_service
    )
    
    result = use_case.execute(input_dto)
    
    # Assert
    assert len(result) == 2
    mock_service.generar.assert_called_once()
```

---

## 📊 Patrones de Observabilidad

### Decorador @with_metrics

```python
# src/core/decorators.py
from functools import wraps
from core.metrics import Metrics


def with_metrics(operation_name: str):
    """
    Decorador para tracking de operaciones.
    
    Registra:
    - Tiempo de ejecución
    - Éxito/fallo
    - Excepciones
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Incrementar contador
            Metrics.increment_counter(f"{operation_name}_calls")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Registrar éxito
                Metrics.increment_counter(f"{operation_name}_success")
                return result
                
            except Exception as e:
                # Registrar fallo
                Metrics.increment_counter(f"{operation_name}_errors")
                raise
                
            finally:
                # Registrar latencia
                duration = time.time() - start_time
                Metrics.record_latency(operation_name, duration)
        
        return wrapper
    return decorator
```

### Uso en Use Cases

```python
class GenerarGuardiasUseCase:
    @with_metrics("generar_guardias")
    def execute(self, input_dto: GenerarGuardiasInputDTO):
        """Métricas registradas automáticamente."""
        ...
```

---

## 📚 Ejemplos Completos

### Ejemplo 1: Crear Profesor (CRUD Simple)

```python
# 1. INPUT DTO
class CrearProfesorInputDTO(BaseModel):
    nombre: str = Field(..., min_length=2)
    apellidos: str = Field(..., min_length=2)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')


# 2. USE CASE
class CrearProfesorUseCase:
    def __init__(self, profesor_repository: IProfesorRepository):
        self.profesor_repository = profesor_repository
    
    @with_metrics("crear_profesor")
    def execute(self, input_dto: CrearProfesorInputDTO) -> ProfesorDTO:
        # Validar email único
        if self.profesor_repository.existe_email(input_dto.email):
            raise ValidationError("Email ya registrado")
        
        # Crear entity
        entity = ProfesorEntity(
            nombre=input_dto.nombre,
            apellidos=input_dto.apellidos,
            email=input_dto.email
        )
        
        # Persistir
        saved_entity = self.profesor_repository.save(entity)
        
        # Retornar DTO
        return ProfesorDTO.from_entity(saved_entity)


# 3. USO EN UI
def on_guardar_profesor_clicked():
    """Handler del formulario de crear profesor."""
    try:
        input_dto = CrearProfesorInputDTO(
            nombre=nombre_input.text(),
            apellidos=apellidos_input.text(),
            email=email_input.text()
        )
        
        with get_db_session() as session:
            use_case = CrearProfesorUseCase(
                SQLAlchemyProfesorRepository(session)
            )
            result = use_case.execute(input_dto)
            session.commit()
        
        QMessageBox.information(self, "Éxito", f"Profesor creado: {result.nombre_completo}")
        
    except ValidationError as e:
        QMessageBox.warning(self, "Error de Validación", str(e))
```

---

## ✅ Best Practices

### 1. Repositories

- ✅ **Interfaz en Domain**, implementación en Infrastructure
- ✅ **Retornar entities**, no models
- ✅ **Eager loading** para relaciones frecuentes
- ✅ **Métodos específicos** del dominio (`find_by_fecha`, no `find_by_condition`)
- ❌ **No exponer** query builders o SQLAlchemy a capas superiores

### 2. Use Cases

- ✅ **Un caso de uso** = una acción del usuario
- ✅ **DTOs para input/output**
- ✅ **Decorar con** `@with_metrics`
- ✅ **Delegar lógica** a domain services
- ❌ **No poner** lógica de negocio compleja en use case

### 3. Entities

- ✅ **Lógica de negocio** en entities (validaciones, cálculos)
- ✅ **Inmutabilidad** cuando sea posible
- ✅ **Value Objects** para conceptos complejos
- ❌ **No importar** SQLAlchemy o ORM

### 4. DTOs

- ✅ **Pydantic** para validación automática
- ✅ **Factory methods** para conversión (`from_entity`)
- ✅ **Ejemplos en** `json_schema_extra`
- ❌ **No reutilizar** DTOs entre use cases diferentes

### 5. Testing

- ✅ **Mocks para repositories** (fácil con interfaces)
- ✅ **Tests de integración** con DB real (usar fixtures)
- ✅ **Test DTOs** con Pydantic validation
- ✅ **Fixtures de entities** para reutilizar

---

## 🎓 Referencias

- **Clean Architecture** - Robert C. Martin (Uncle Bob)
- **Domain-Driven Design** - Eric Evans
- **Patterns of Enterprise Application Architecture** - Martin Fowler
- **Pydantic Documentation** - https://docs.pydantic.dev/
- **SQLAlchemy ORM** - https://www.sqlalchemy.org/

---

**Documento vivo:** Actualizar cuando se agreguen nuevos patrones o evolucione la arquitectura.
