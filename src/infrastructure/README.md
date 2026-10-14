# Módulo Infrastructure (Infraestructura)

**Ruta:** `src/infrastructure/`  
**Responsabilidad:** Implementaciones concretas de persistencia y servicios externos

---

## 📋 Contenido

```
infrastructure/
├── __init__.py
├── repositories/          # Implementaciones de repositories con SQLAlchemy
│   ├── __init__.py
│   ├── sqlalchemy_guardia_repository.py
│   ├── sqlalchemy_profesor_repository.py
│   ├── sqlalchemy_zona_repository.py
│   └── sqlalchemy_configuracion_repository.py
└── mappers/               # Conversión Model ↔ Entity
    ├── __init__.py
    ├── guardia_mapper.py
    ├── profesor_mapper.py
    ├── zona_mapper.py
    └── configuracion_mapper.py
```

---

## 🎯 Propósito

El **módulo de infraestructura** implementa los **detalles técnicos** de persistencia y acceso a datos. Su responsabilidad es:

1. **Implementar interfaces** definidas en Domain
2. **Traducir entre capas** (Model ORM ↔ Entity Domain)
3. **Optimizar acceso a BD** (queries, eager loading, caching)
4. **Manejar transacciones** y conexiones a BD

**Principio clave:** Domain **NO conoce** Infrastructure, pero Infrastructure **SÍ conoce** Domain.

---

## 📦 Componentes Principales

### 1. Repositories (Implementaciones)

**¿Qué son?**  
Implementaciones **concretas** de las interfaces `IRepository` definidas en Domain, usando **SQLAlchemy**.

#### Ejemplo: SQLAlchemyGuardiaRepository

```python
# src/infrastructure/repositories/sqlalchemy_guardia_repository.py
from sqlalchemy.orm import Session, joinedload
from domain.repositories import IGuardiaRepository  # ✨ Implementa interfaz de Domain
from domain.entities import GuardiaEntity
from models.models import Guardia  # SQLAlchemy Model
from infrastructure.mappers import GuardiaMapper


class SQLAlchemyGuardiaRepository(IGuardiaRepository):
    """
    Implementación de IGuardiaRepository usando SQLAlchemy.
    
    Responsabilidades:
    - Ejecutar queries con SQLAlchemy ORM
    - Optimizar con eager loading (evitar N+1)
    - Convertir Model ↔ Entity con Mapper
    - Manejar excepciones de BD
    """
    
    def __init__(self, session: Session):
        """
        Args:
            session: Sesión de SQLAlchemy (gestiona transacciones)
        """
        self.session = session
        self.mapper = GuardiaMapper()
    
    def get_all(self) -> list[GuardiaEntity]:
        """
        Obtiene todas las guardias con eager loading.
        
        Optimización: Usa joinedload para evitar N+1 queries.
        Sin eager loading: 1 query + N queries (cada guardia carga profesor/zona)
        Con eager loading: 1 query con JOINs
        """
        models = (
            self.session.query(Guardia)
            .options(
                joinedload(Guardia.profesor),  # ✨ Carga eager
                joinedload(Guardia.zona)       # ✨ Carga eager
            )
            .all()
        )
        # Convertir Model → Entity
        return self.mapper.to_entities(models)
    
    def find_by_fecha(self, fecha: date) -> list[GuardiaEntity]:
        """
        Busca guardias por fecha (query específica del dominio).
        
        Args:
            fecha: Fecha a buscar
            
        Returns:
            Lista de guardias (entities)
        """
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
    
    def save(self, entity: GuardiaEntity) -> GuardiaEntity:
        """
        Guarda guardia (create o update).
        
        Lógica:
        - Si entity.id existe → UPDATE
        - Si entity.id es None → INSERT
        
        Args:
            entity: Entidad del dominio
            
        Returns:
            Entidad guardada (con ID asignado si es nuevo)
        """
        try:
            if entity.id:
                # UPDATE: buscar modelo existente
                model = self.session.query(Guardia).filter(Guardia.id == entity.id).first()
                if not model:
                    raise NotFoundError(entity_type="Guardia", entity_id=entity.id)
                model = self.mapper.to_model(entity, existing_model=model)
            else:
                # INSERT: crear nuevo modelo
                model = self.mapper.to_model(entity)
                self.session.add(model)
            
            self.session.flush()  # Obtener ID sin commit
            return self.mapper.to_entity(model)
            
        except Exception as e:
            logger.error("Error al guardar guardia", error=str(e))
            raise DatabaseError(f"Error al guardar guardia: {e}") from e
```

#### Características Clave

| Aspecto | Implementación |
|---------|----------------|
| **Hereda de** | `IGuardiaRepository` (interfaz abstracta) |
| **Dependencias** | SQLAlchemy Session, Mapper, Model |
| **Retorna** | **Entities** (no models) |
| **Optimizaciones** | Eager loading, bulk operations |
| **Excepciones** | Traduce SQLAlchemy → Domain exceptions |

---

### 2. Mappers (Traducción Model ↔ Entity)

**¿Qué son?**  
Clases que **convierten** entre:
- **Model** (SQLAlchemy ORM, tabla BD)
- **Entity** (Domain, lógica de negocio)

#### ¿Por qué Mappers?

**Problema:** Domain no debe conocer SQLAlchemy.

```python
# ❌ MALO: Entity acoplada a SQLAlchemy
class GuardiaEntity(Base):  # ❌ Hereda de SQLAlchemy Base
    __tablename__ = "guardias"
    id = Column(Integer, primary_key=True)
    ...
```

**Solución:** Separar Model (BD) y Entity (Domain), usar Mapper para traducir.

```python
# ✅ BUENO: Model (BD) separado de Entity (Domain)

# Model (SQLAlchemy)
class Guardia(Base):
    __tablename__ = "guardias"
    id = Column(Integer, primary_key=True)
    fecha = Column(Date)
    ...

# Entity (Domain)
class GuardiaEntity:
    def __init__(self, id, fecha, ...):
        self.id = id
        self.fecha = fecha
        ...

# Mapper (Infrastructure)
class GuardiaMapper:
    def to_entity(self, model: Guardia) -> GuardiaEntity:
        """Model → Entity"""
        return GuardiaEntity(id=model.id, fecha=model.fecha, ...)
    
    def to_model(self, entity: GuardiaEntity) -> Guardia:
        """Entity → Model"""
        return Guardia(id=entity.id, fecha=entity.fecha, ...)
```

#### Ejemplo Completo: GuardiaMapper

```python
# src/infrastructure/mappers/guardia_mapper.py
from models.models import Guardia  # SQLAlchemy Model (BD)
from domain.entities import GuardiaEntity  # Domain Entity


class GuardiaMapper:
    """
    Mapper bidireccional: Model ↔ Entity.
    
    Responsabilidades:
    - Traducir tipos (Date de BD → date de Python)
    - Manejar relaciones (profesor_id vs profesor object)
    - Crear nuevos models o actualizar existentes
    """
    
    def to_entity(self, model: Guardia) -> GuardiaEntity:
        """
        Convierte SQLAlchemy Model → Domain Entity.
        
        Args:
            model: Modelo de SQLAlchemy (tabla guardias)
            
        Returns:
            Entidad del dominio
            
        Nota:
            No carga relaciones automáticamente.
            Usar eager loading en repository si necesitas profesor/zona.
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
            existing_model: Modelo existente (para UPDATE)
            
        Returns:
            Modelo de SQLAlchemy listo para persistir
            
        Uso:
            # CREATE (nuevo)
            model = mapper.to_model(entity)
            session.add(model)
            
            # UPDATE (existente)
            model = session.query(Guardia).get(id)
            model = mapper.to_model(entity, existing_model=model)
        """
        if existing_model:
            # UPDATE: modificar modelo existente
            existing_model.fecha = entity.fecha
            existing_model.turno = entity.turno
            existing_model.recreo = entity.recreo
            existing_model.profesor_id = entity.profesor_id
            existing_model.zona_id = entity.zona_id
            existing_model.es_sustitucion = entity.es_sustitucion
            existing_model.observaciones = entity.observaciones
            return existing_model
        else:
            # CREATE: nuevo modelo
            return Guardia(
                id=entity.id,  # None para nuevos
                fecha=entity.fecha,
                turno=entity.turno,
                recreo=entity.recreo,
                profesor_id=entity.profesor_id,
                zona_id=entity.zona_id,
                es_sustitucion=entity.es_sustitucion,
                observaciones=entity.observaciones
            )
```

#### Patrones de Mapeo

**1. Mapeo Simple (Campos 1:1)**

```python
# Model y Entity tienen mismos campos
entity.nombre = model.nombre
entity.email = model.email
```

**2. Mapeo con Transformación**

```python
# Convertir tipos
entity.fecha = model.fecha.date()  # datetime → date
entity.turno = model.turno.upper()  # normalizar
```

**3. Mapeo de Relaciones**

```python
# Relación Many-to-One
def to_entity(self, model: Guardia) -> GuardiaEntity:
    entity = GuardiaEntity(...)
    
    # Copiar solo IDs (no cargar objetos completos)
    entity.profesor_id = model.profesor_id
    entity.zona_id = model.zona_id
    
    # Si usaste eager loading, puedes cargar objetos
    if model.profesor:
        entity.profesor = self.profesor_mapper.to_entity(model.profesor)
    
    return entity
```

**4. Mapeo Bidireccional (Update)**

```python
def to_model(self, entity, existing_model=None):
    if existing_model:
        # UPDATE: solo actualizar campos modificables
        existing_model.nombre = entity.nombre
        existing_model.email = entity.email
        # NO actualizar: id, fecha_creacion, etc.
        return existing_model
    else:
        # CREATE: todos los campos
        return Guardia(**entity.__dict__)
```

---

## 🚀 Optimizaciones de Performance

### 1. Eager Loading (Evitar N+1 Queries)

**Problema: N+1 Queries**

```python
# ❌ MALO: N+1 queries
guardias = session.query(Guardia).all()  # 1 query
for guardia in guardias:
    print(guardia.profesor.nombre)  # +N queries (uno por guardia)
# Total: 1 + N queries = 101 queries para 100 guardias
```

**Solución: Eager Loading**

```python
# ✅ BUENO: 1 query con JOINs
guardias = (
    session.query(Guardia)
    .options(
        joinedload(Guardia.profesor),  # LEFT JOIN profesores
        joinedload(Guardia.zona)       # LEFT JOIN zonas
    )
    .all()
)
# Total: 1 query (con 2 JOINs)
```

**Tipos de Eager Loading:**

| Método | Uso | Query Generada |
|--------|-----|----------------|
| `joinedload()` | Many-to-One, One-to-One | LEFT JOIN |
| `selectinload()` | One-to-Many | SELECT IN (subquery) |
| `subqueryload()` | One-to-Many | SELECT con subquery |

### 2. Bulk Operations

```python
# ✅ BUENO: Bulk insert
guardias = [Guardia(...), Guardia(...), ...]
session.bulk_save_objects(guardias)
# 1 query para N inserts
```

### 3. Query Optimization

```python
# Solo cargar campos necesarios
session.query(Guardia.id, Guardia.fecha).all()

# Usar count() eficiente
session.query(Guardia).count()  # SELECT COUNT(*)

# Limitar resultados
session.query(Guardia).limit(100).all()
```

---

## 🔄 Flujo de Datos

```
┌─────────────────────────────────────────┐
│      Use Case (Application)             │
│  use_case.execute(input_dto)            │
└──────────────────┬──────────────────────┘
                   │
                   ↓ llama
┌─────────────────────────────────────────┐
│   Repository (Infrastructure)           │
│  guardia_repo.find_by_fecha(fecha)      │
│                                          │
│  1. Query SQLAlchemy                    │
│  2. models = session.query(...).all()   │
│  3. entities = mapper.to_entities(...)  │
│  4. return entities                     │
└──────────────────┬──────────────────────┘
                   │
                   ↓ usa
┌─────────────────────────────────────────┐
│   Mapper (Infrastructure)               │
│  mapper.to_entities(models)             │
│                                          │
│  for model in models:                   │
│      entity = GuardiaEntity(...)        │
│  return entities                        │
└──────────────────┬──────────────────────┘
                   │
                   ↓ retorna
┌─────────────────────────────────────────┐
│   Entity (Domain)                       │
│  GuardiaEntity(id=1, fecha=...)         │
└─────────────────────────────────────────┘
```

---

## 🧪 Testing

### Test de Repository (Integración)

```python
# tests/test_repositories/test_guardia_repository.py
import pytest
from datetime import date
from infrastructure.repositories import SQLAlchemyGuardiaRepository
from domain.entities import GuardiaEntity


@pytest.fixture
def guardia_repository(db_session):
    """Fixture que crea repository con sesión de test."""
    return SQLAlchemyGuardiaRepository(db_session)


def test_get_all_con_eager_loading(guardia_repository, db_session):
    """get_all debe cargar relaciones sin N+1."""
    # Arrange: crear guardias de prueba
    from models.models import Guardia, Profesor, Zona
    
    profesor = Profesor(nombre="Juan", apellidos="Pérez")
    zona = Zona(nombre_zona="Patio A")
    db_session.add_all([profesor, zona])
    db_session.flush()
    
    guardia = Guardia(
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=profesor.id,
        zona_id=zona.id
    )
    db_session.add(guardia)
    db_session.commit()
    
    # Act
    entities = guardia_repository.get_all()
    
    # Assert
    assert len(entities) == 1
    assert isinstance(entities[0], GuardiaEntity)
    assert entities[0].profesor_id == profesor.id


def test_save_create(guardia_repository, db_session):
    """save debe crear nueva guardia."""
    # Arrange
    entity = GuardiaEntity(
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=1,
        zona_id=1
    )
    
    # Act
    saved = guardia_repository.save(entity)
    db_session.commit()
    
    # Assert
    assert saved.id is not None
    assert saved.fecha == date(2025, 10, 23)
```

### Test de Mapper (Unitario)

```python
# tests/test_mappers/test_guardia_mapper.py
from infrastructure.mappers import GuardiaMapper
from models.models import Guardia
from domain.entities import GuardiaEntity


def test_to_entity():
    """Conversión Model → Entity."""
    # Arrange
    model = Guardia(
        id=1,
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=5,
        zona_id=2
    )
    mapper = GuardiaMapper()
    
    # Act
    entity = mapper.to_entity(model)
    
    # Assert
    assert isinstance(entity, GuardiaEntity)
    assert entity.id == 1
    assert entity.fecha == date(2025, 10, 23)


def test_to_model_create():
    """Conversión Entity → Model (nuevo)."""
    # Arrange
    entity = GuardiaEntity(
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=5,
        zona_id=2
    )
    mapper = GuardiaMapper()
    
    # Act
    model = mapper.to_model(entity)
    
    # Assert
    assert isinstance(model, Guardia)
    assert model.fecha == date(2025, 10, 23)
```

---

## 📚 Reglas de Dependencias

### ✅ Infrastructure PUEDE:
- Importar de `domain` (interfaces, entities)
- Usar SQLAlchemy, psycopg2, etc.
- Implementar interfaces de Domain
- Optimizar queries

### ❌ Infrastructure NO PUEDE:
- Importar de `application` (use cases)
- Importar de `presentation` (UI)
- Contener lógica de negocio (va en Domain)

### Ejemplo de Imports Válidos

```python
# ✅ BUENO
from domain.repositories import IGuardiaRepository  # Interfaz de Domain
from domain.entities import GuardiaEntity
from sqlalchemy.orm import Session, joinedload
from models.models import Guardia

# ❌ MALO
from application.use_cases import CrearGuardiaUseCase  # ❌
from presentation.widgets import GuardiaWidget  # ❌
```

---

## 🎓 Conceptos Clave

### Repository Pattern

**Abstracción:** Domain define **qué** hacer (interfaz)  
**Implementación:** Infrastructure define **cómo** hacerlo (SQLAlchemy)

```
Domain: "Dame todas las guardias de una fecha"
Infrastructure: "SELECT * FROM guardias WHERE fecha = ?"
```

### Mapper Pattern

**Propósito:** Traducir entre representaciones diferentes de los mismos datos.

**Beneficios:**
- ✅ Domain desacoplado de BD
- ✅ Cambiar schema de BD sin tocar Domain
- ✅ Entities más simples (sin decoradores ORM)

---

## 📖 Guías Adicionales

- **Arquitectura General**: `documentacion/ARCHITECTURE_PATTERNS.md`
- **Testing Repositories**: `documentacion/guias/TESTING.md`
- **SQLAlchemy Best Practices**: https://docs.sqlalchemy.org/en/20/orm/

---

**Mantenedor:** Actualizar al agregar nuevas optimizaciones o patrones de mapeo.
