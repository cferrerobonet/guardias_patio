# Módulo Domain (Dominio)

**Ruta:** `src/domain/`  
**Responsabilidad:** Capa central con entidades, reglas de negocio y abstracciones

---

## 📋 Contenido

```
domain/
├── __init__.py
├── entities/              # Entidades del dominio
│   ├── __init__.py
│   ├── guardia_entity.py
│   ├── profesor_entity.py
│   └── zona_entity.py
├── repositories/          # Interfaces de repositories (abstracciones)
│   ├── __init__.py
│   ├── base_repository.py
│   ├── guardia_repository.py
│   ├── profesor_repository.py
│   └── zona_repository.py
├── schemas/               # Schemas Pydantic para validación
│   ├── __init__.py
│   ├── guardia_schema.py
│   ├── profesor_schema.py
│   ├── zona_schema.py
│   └── configuracion_schema.py
└── services/              # Servicios de dominio (lógica compleja)
    ├── __init__.py
    └── generador_guardias_service.py
```

---

## 🎯 Propósito

El **módulo de dominio** es el **corazón** de la aplicación. Contiene:

1. **Entities**: Objetos con identidad y lógica de negocio
2. **Value Objects**: Objetos inmutables sin identidad (ej: `Turno`, `Disponibilidad`)
3. **Repository Interfaces**: Contratos para acceso a datos
4. **Schemas**: Validación de datos con Pydantic
5. **Domain Services**: Lógica que no pertenece a una sola entity

---

## 📦 Componentes Principales

### 1. Entities (Entidades)

**¿Qué son?**  
Objetos con **identidad única** (ID) y **lógica de negocio**.

**Ejemplo: GuardiaEntity**

```python
from datetime import date
from domain.entities import GuardiaEntity

# Crear guardia
guardia = GuardiaEntity(
    fecha=date(2025, 10, 23),
    turno="MAÑANA",
    recreo=1,
    profesor_id=5,
    zona_id=2
)

# Lógica de negocio en la entity
if guardia.es_conflictiva():
    print("Guardia tiene conflictos")

# Validaciones de dominio
guardia.validar_asignacion()  # Lanza exception si inválida
```

**Características:**
- ✅ **Identidad única** (ID)
- ✅ **Lógica de negocio** (métodos de validación, cálculos)
- ✅ **Mutables** (pueden cambiar de estado)
- ✅ **Independientes** de infraestructura (no conocen BD)

**Entities en el proyecto:**
- `GuardiaEntity`: Representa una guardia de patio
- `ProfesorEntity`: Representa un profesor
- `ZonaEntity`: Representa una zona de vigilancia
- `ConfiguracionEntity`: Configuración del sistema

---

### 2. Repository Interfaces (Abstracciones)

**¿Qué son?**  
Interfaces abstractas que definen **cómo acceder** a las entidades sin acoplarse a la implementación.

**Ejemplo: IGuardiaRepository**

```python
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from domain.entities import GuardiaEntity


class IGuardiaRepository(ABC):
    """Interfaz del repositorio de Guardia."""
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[GuardiaEntity]:
        """Obtiene una guardia por ID."""
        pass
    
    @abstractmethod
    def find_by_fecha(self, fecha: date) -> list[GuardiaEntity]:
        """Obtiene guardias de una fecha."""
        pass
    
    @abstractmethod
    def save(self, entity: GuardiaEntity) -> GuardiaEntity:
        """Guarda una guardia."""
        pass
```

**Beneficios:**
- ✅ **Desacoplamiento**: Domain no depende de SQLAlchemy
- ✅ **Testability**: Fácil mockear en tests
- ✅ **Flexibility**: Cambiar DB sin tocar dominio

**Implementaciones:**  
Las implementaciones están en `src/infrastructure/repositories/`

---

### 3. Schemas (Validación Pydantic)

**¿Qué son?**  
Clases Pydantic para **validar y serializar** datos.

**Ejemplo: GuardiaCreateSchema**

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date as date_type


class GuardiaCreateSchema(BaseModel):
    """Schema para crear una guardia."""
    
    fecha: date_type = Field(..., description="Fecha de la guardia")
    turno: str = Field(..., pattern="^(MAÑANA|TARDE)$")
    recreo: int = Field(..., ge=1, le=3)
    profesor_id: int = Field(..., gt=0)
    zona_id: int = Field(..., gt=0)
    
    @field_validator('fecha')
    @classmethod
    def fecha_no_pasada(cls, v: date_type) -> date_type:
        """Valida que no sea fecha pasada."""
        from datetime import date as today
        if v < today.today():
            raise ValueError("No se pueden crear guardias pasadas")
        return v
```

**Uso:**
```python
# Validación automática
try:
    schema = GuardiaCreateSchema(
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=5,
        zona_id=2
    )
    print("✅ Datos válidos")
except ValidationError as e:
    print(f"❌ Error: {e}")
```

**Ver más:** `documentacion/SCHEMAS_USAGE_GUIDE.md`

---

### 4. Domain Services

**¿Qué son?**  
Servicios que contienen **lógica de negocio** que no pertenece a una sola entity.

**Ejemplo: GeneradorGuardiasService**

```python
class GeneradorGuardiasService:
    """
    Servicio de dominio para generar guardias.
    
    Lógica compleja que involucra múltiples entities
    (Guardia, Profesor, Zona, Configuración).
    """
    
    def generar(
        self,
        fecha: date,
        turno: str,
        profesores_disponibles: list[ProfesorEntity],
        zonas: list[ZonaEntity],
        config: ConfiguracionEntity
    ) -> list[GuardiaEntity]:
        """
        Genera guardias según reglas de negocio.
        
        Reglas:
        - Distribuir profesores equitativamente
        - Respetar capacidad de zonas
        - No exceder máximo de guardias por día
        - Priorizar profesores con menos guardias
        """
        guardias = []
        
        # Algoritmo de generación
        for zona in zonas:
            profesores_asignados = self._seleccionar_profesores(
                zona=zona,
                profesores=profesores_disponibles,
                config=config
            )
            
            for profesor in profesores_asignados:
                guardia = GuardiaEntity(
                    fecha=fecha,
                    turno=turno,
                    recreo=1,
                    profesor_id=profesor.id,
                    zona_id=zona.id
                )
                guardias.append(guardia)
        
        return guardias
```

**Cuándo usar Domain Services:**
- ✅ Lógica que involucra **múltiples entities**
- ✅ Algoritmos complejos de negocio
- ✅ Validaciones que requieren **coordinación** entre entities
- ❌ NO usar para lógica simple de una sola entity (poner en la entity)

---

## 🔄 Flujo de Datos

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (UI llama Use Case con DTO/Schema)     │
└──────────────────┬──────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────┐
│        Application Layer (Use Case)     │
│  Recibe Schema → Usa Repositories       │
└──────────────────┬──────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────┐
│         Domain Layer (ESTE MÓDULO)      │
│  ┌─────────────────────────────────┐   │
│  │  Repository Interface           │   │
│  │  (IGuardiaRepository)           │   │
│  └─────────────────────────────────┘   │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │  Entity (GuardiaEntity)         │   │
│  │  - Lógica de negocio            │   │
│  │  - Validaciones                 │   │
│  └─────────────────────────────────┘   │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │  Schema (GuardiaCreateSchema)   │   │
│  │  - Validación Pydantic          │   │
│  └─────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   ↑
                   │ implementa
┌─────────────────────────────────────────┐
│      Infrastructure Layer               │
│  (SQLAlchemyGuardiaRepository)          │
│  - Implementa IGuardiaRepository        │
│  - Usa Mapper para Model ↔ Entity      │
└─────────────────────────────────────────┘
```

---

## 📚 Reglas de Dependencias

### ✅ Domain PUEDE:
- Definir interfaces (abstracciones)
- Contener lógica de negocio
- Usar Pydantic para schemas
- Definir excepciones de negocio

### ❌ Domain NO PUEDE:
- Importar de `infrastructure` (SQLAlchemy, mappers)
- Importar de `application` (use cases, DTOs)
- Importar de `presentation` (UI, widgets)
- Depender de librerías de BD (psycopg2, pymongo, etc.)

### Ejemplo de Dependencias Válidas

```python
# ✅ BUENO
from domain.entities import GuardiaEntity
from domain.repositories import IGuardiaRepository
from pydantic import BaseModel
from datetime import date

# ❌ MALO
from infrastructure.repositories import SQLAlchemyGuardiaRepository  # ❌
from models.models import Guardia  # ❌ (SQLAlchemy model)
from application.use_cases import CrearGuardiaUseCase  # ❌
```

---

## 🧪 Testing

### Test de Entities

```python
# tests/test_entities/test_guardia_entity.py
import pytest
from datetime import date
from domain.entities import GuardiaEntity


def test_guardia_entity_creacion():
    """Crear guardia válida."""
    guardia = GuardiaEntity(
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=5,
        zona_id=2
    )
    
    assert guardia.fecha == date(2025, 10, 23)
    assert guardia.turno == "MAÑANA"


def test_guardia_entity_validacion():
    """Validación de reglas de negocio."""
    guardia = GuardiaEntity(
        fecha=date(2025, 10, 23),
        turno="TARDE",
        recreo=4,  # ❌ Inválido: TARDE solo tiene 2 recreos
        profesor_id=5,
        zona_id=2
    )
    
    with pytest.raises(ValidationError):
        guardia.validar()
```

### Test de Schemas

```python
# tests/test_schemas/test_guardia_schema.py
from pydantic import ValidationError
import pytest


def test_guardia_create_schema_valido():
    """Schema válido pasa validación."""
    schema = GuardiaCreateSchema(
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=5,
        zona_id=2
    )
    assert schema.turno == "MAÑANA"


def test_guardia_create_schema_fecha_pasada():
    """Fecha pasada debe fallar."""
    with pytest.raises(ValidationError):
        GuardiaCreateSchema(
            fecha=date(2020, 1, 1),  # ❌ Fecha pasada
            turno="MAÑANA",
            recreo=1,
            profesor_id=5,
            zona_id=2
        )
```

---

## 📖 Guías Adicionales

- **Arquitectura General**: `documentacion/ARCHITECTURE_PATTERNS.md`
- **Uso de Schemas**: `documentacion/SCHEMAS_USAGE_GUIDE.md`
- **Testing**: `documentacion/guias/TESTING.md`

---

## 🎓 Conceptos Clave

### Entity vs Value Object

| Aspecto | Entity | Value Object |
|---------|--------|--------------|
| **Identidad** | Sí (ID único) | No (comparación por valor) |
| **Mutabilidad** | Mutable | Inmutable |
| **Ejemplo** | `GuardiaEntity` | `TurnoVO`, `DisponibilidadVO` |

### Repository Interface vs Implementation

| Aspecto | Interface (Domain) | Implementation (Infrastructure) |
|---------|-------------------|--------------------------------|
| **Ubicación** | `domain/repositories/` | `infrastructure/repositories/` |
| **Contenido** | Métodos abstractos | Implementación con SQLAlchemy |
| **Dependencias** | Solo domain entities | SQLAlchemy, mappers |

---

**Mantenedor:** Actualizar al agregar nuevas entities, schemas o services.
