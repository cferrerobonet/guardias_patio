# Guía de Uso de Pydantic Schemas

**Proyecto:** Guardias de Patio  
**Versión:** 2.7+  
**Fecha:** 23 Octubre 2025

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [¿Qué son los Schemas?](#qué-son-los-schemas)
3. [Schemas vs DTOs vs Entities](#schemas-vs-dtos-vs-entities)
4. [Schemas en el Proyecto](#schemas-en-el-proyecto)
5. [Validaciones con Pydantic](#validaciones-con-pydantic)
6. [Patrones de Uso](#patrones-de-uso)
7. [Conversiones](#conversiones)
8. [Testing con Schemas](#testing-con-schemas)
9. [Best Practices](#best-practices)

---

## 🎯 Introducción

Este documento describe cómo utilizar **Pydantic Schemas** en el proyecto Guardias de Patio. Los schemas proporcionan **validación automática**, **serialización** y **documentación** de tipos de datos.

### ¿Por qué Pydantic?

- ✅ **Validación automática** con tipos Python
- ✅ **Serialización** JSON automática
- ✅ **Type hints** nativos
- ✅ **Documentación** auto-generada
- ✅ **Performance** (validación en C con Rust backend)

---

## 📦 ¿Qué son los Schemas?

Los **Schemas** son clases Pydantic que definen la **estructura y validación** de datos. Son especialmente útiles para:

1. **APIs REST**: Request/Response validation
2. **DTOs**: Data Transfer entre capas
3. **Configuración**: Validar archivos config
4. **Formularios**: Validar input de usuarios

### Ejemplo Básico

```python
from pydantic import BaseModel, Field


class ProfesorSchema(BaseModel):
    """Schema para datos de un profesor."""
    
    nombre: str = Field(..., min_length=2, max_length=50)
    apellidos: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    activo: bool = Field(default=True)


# Uso: Validación automática
try:
    profesor = ProfesorSchema(
        nombre="Juan",
        apellidos="Pérez García",
        email="juan.perez@example.com"
    )
    print(profesor.nombre)  # "Juan"
except ValidationError as e:
    print(e.errors())
```

---

## 🔄 Schemas vs DTOs vs Entities

| Aspecto | Schema (Pydantic) | DTO | Entity (Domain) |
|---------|-------------------|-----|-----------------|
| **Propósito** | Validación + Serialización | Transferir datos | Lógica de negocio |
| **Capa** | Application | Application | Domain |
| **Validación** | Automática (Pydantic) | Manual o Schema | Reglas de negocio |
| **Mutabilidad** | Inmutable | Inmutable | Mutable |
| **Serialización** | JSON nativo | Manual | No directa |
| **Ejemplo** | `ProfesorCreateSchema` | `CrearProfesorInputDTO` | `ProfesorEntity` |

### Relación Conceptual

```
┌─────────────────┐
│  Schema         │  Validación de datos crudos (input)
│  (Pydantic)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  DTO            │  Transferencia entre capas
│  (Application)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Entity         │  Lógica de negocio
│  (Domain)       │
└─────────────────┘
```

### En Guardias de Patio

**Actualmente usamos DTOs que son schemas Pydantic**, combinando ambos conceptos:

```python
# src/application/dtos/profesor_input_dto.py
from pydantic import BaseModel  # ✨ DTO es un Schema

class CrearProfesorInputDTO(BaseModel):
    """DTO con validación Pydantic integrada."""
    nombre: str
    apellidos: str
```

**Beneficio:** Menos código, validación automática en DTOs.

---

## 📂 Schemas en el Proyecto

### Ubicación

```
src/
├── domain/
│   └── schemas/           # ✨ Schemas de dominio
│       ├── __init__.py
│       ├── profesor_schema.py
│       ├── guardia_schema.py
│       ├── zona_schema.py
│       └── configuracion_schema.py
│
└── application/
    └── dtos/              # DTOs (también son schemas)
        ├── profesor_input_dto.py
        ├── guardia_dto.py
        └── ...
```

### Estructura de un Schema

```python
# src/domain/schemas/profesor_schema.py
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ProfesorBaseSchema(BaseModel):
    """
    Schema base con campos comunes.
    
    Usado como base para Create/Update/Response schemas.
    """
    nombre: str = Field(..., min_length=2, max_length=50)
    apellidos: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    telefono: Optional[str] = Field(None, pattern=r'^\+?[0-9]{9,15}$')


class ProfesorCreateSchema(ProfesorBaseSchema):
    """
    Schema para CREAR un profesor.
    
    No incluye ID (auto-generado).
    """
    activo: bool = Field(default=True)
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Normaliza email a minúsculas."""
        return v.lower().strip()


class ProfesorUpdateSchema(BaseModel):
    """
    Schema para ACTUALIZAR un profesor.
    
    Todos los campos opcionales (partial update).
    """
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    telefono: Optional[str] = None
    activo: Optional[bool] = None


class ProfesorResponseSchema(ProfesorBaseSchema):
    """
    Schema para RESPUESTA (read).
    
    Incluye ID y campos calculados.
    """
    id: int
    activo: bool
    nombre_completo: str  # Campo calculado
    numero_guardias: int = Field(default=0)
    
    model_config = ConfigDict(
        from_attributes=True  # Para SQLAlchemy models
    )
    
    @classmethod
    def from_entity(cls, entity: ProfesorEntity) -> "ProfesorResponseSchema":
        """Factory method: Entity → Schema."""
        return cls(
            id=entity.id,
            nombre=entity.nombre,
            apellidos=entity.apellidos,
            email=entity.email,
            telefono=entity.telefono,
            activo=entity.activo,
            nombre_completo=entity.nombre_completo,
            numero_guardias=entity.numero_guardias
        )
```

### Patrón de 4 Schemas

Para cada recurso principal, creamos **4 schemas**:

1. **BaseSchema**: Campos comunes
2. **CreateSchema**: Para POST (sin ID)
3. **UpdateSchema**: Para PUT/PATCH (campos opcionales)
4. **ResponseSchema**: Para GET (con ID + calculados)

---

## ✅ Validaciones con Pydantic

### 1. Validaciones de Campo (Field)

```python
from pydantic import BaseModel, Field


class GuardiaCreateSchema(BaseModel):
    """Validaciones con Field constraints."""
    
    fecha: date = Field(
        ...,  # Requerido
        description="Fecha de la guardia"
    )
    
    turno: str = Field(
        ...,
        pattern="^(MAÑANA|TARDE)$",  # Regex
        description="Turno: MAÑANA o TARDE"
    )
    
    recreo: int = Field(
        ...,
        ge=1,  # Greater or Equal
        le=3,  # Less or Equal
        description="Número de recreo (1-3)"
    )
    
    profesor_id: int = Field(..., gt=0)  # Greater Than
    zona_id: int = Field(..., gt=0)
    
    observaciones: Optional[str] = Field(
        None,
        max_length=500,
        description="Observaciones opcionales"
    )
```

### 2. Validadores Personalizados (field_validator)

```python
from pydantic import field_validator
from datetime import date as date_type


class GuardiaCreateSchema(BaseModel):
    fecha: date_type
    turno: str
    
    @field_validator('fecha')
    @classmethod
    def fecha_no_pasada(cls, v: date_type) -> date_type:
        """Valida que la fecha no sea del pasado."""
        from datetime import date as today
        if v < today.today():
            raise ValueError('No se pueden crear guardias en fechas pasadas')
        return v
    
    @field_validator('fecha')
    @classmethod
    def fecha_no_fin_semana(cls, v: date_type) -> date_type:
        """Valida que no sea sábado o domingo."""
        if v.weekday() >= 5:  # 5=Sábado, 6=Domingo
            raise ValueError('No se pueden crear guardias en fin de semana')
        return v
    
    @field_validator('turno')
    @classmethod
    def turno_uppercase(cls, v: str) -> str:
        """Normaliza turno a mayúsculas."""
        return v.upper().strip()
```

### 3. Validación de Modelo Completo (model_validator)

```python
from pydantic import model_validator


class GuardiaCreateSchema(BaseModel):
    fecha: date_type
    turno: str
    recreo: int
    
    @model_validator(mode='after')
    def validar_coherencia(self) -> 'GuardiaCreateSchema':
        """
        Valida coherencia entre campos.
        
        Ejecutado DESPUÉS de validar campos individuales.
        """
        # Turno TARDE solo tiene 2 recreos
        if self.turno == 'TARDE' and self.recreo > 2:
            raise ValueError('Turno TARDE solo tiene 2 recreos (1 y 2)')
        
        # Turno MAÑANA tiene 3 recreos
        if self.turno == 'MAÑANA' and self.recreo > 3:
            raise ValueError('Turno MAÑANA solo tiene 3 recreos (1, 2 y 3)')
        
        return self
```

### 4. Validaciones Complejas (Dependen de BD)

Para validaciones que requieren acceso a BD, **NO usar validators**. Validar en Use Case:

```python
class CrearGuardiaUseCase:
    def execute(self, input_dto: GuardiaCreateSchema):
        # ✅ Validaciones de Pydantic ya ejecutadas
        
        # ✅ Validaciones con BD (en use case)
        if not self.profesor_repository.exists(input_dto.profesor_id):
            raise NotFoundError(f"Profesor {input_dto.profesor_id} no existe")
        
        if self.guardia_repository.existe_en_momento(...):
            raise ConflictError("Ya existe guardia en ese momento")
```

---

## 🔄 Patrones de Uso

### Patrón 1: Input Validation (UI → Application)

```python
# En UI (PyQt6)
def on_crear_guardia_clicked(self):
    """Handler del botón Crear Guardia."""
    try:
        # 1. Recoger datos del formulario
        input_dto = GuardiaCreateSchema(
            fecha=self.fecha_edit.date().toPyDate(),
            turno=self.turno_combo.currentText(),
            recreo=self.recreo_spinbox.value(),
            profesor_id=self.profesor_combo.currentData(),
            zona_id=self.zona_combo.currentData()
        )
        
        # 2. Si llegamos aquí, datos válidos
        use_case = self._create_use_case()
        result = use_case.execute(input_dto)
        
        # 3. Mostrar éxito
        QMessageBox.information(self, "Éxito", "Guardia creada correctamente")
        
    except ValidationError as e:
        # ❌ Error de validación Pydantic
        errors = "\n".join([f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
        QMessageBox.warning(self, "Datos inválidos", errors)
    
    except BusinessLogicError as e:
        # ❌ Error de lógica de negocio
        QMessageBox.critical(self, "Error", str(e))
```

### Patrón 2: Output Serialization (Application → UI)

```python
class ListarGuardiasUseCase:
    def execute(self, fecha: date) -> list[GuardiaResponseSchema]:
        """Retorna schemas listos para UI."""
        entities = self.guardia_repository.find_by_fecha(fecha)
        
        # Convertir entities → schemas
        return [
            GuardiaResponseSchema.from_entity(e) for e in entities
        ]


# En UI
def cargar_guardias(self, fecha: date):
    """Carga guardias en la tabla."""
    use_case = self._create_use_case()
    guardias = use_case.execute(fecha)
    
    # guardias es list[GuardiaResponseSchema]
    for guardia in guardias:
        # Acceso type-safe
        print(guardia.profesor_nombre)
        print(guardia.zona_nombre)
        
        # JSON automático
        print(guardia.model_dump_json())
```

### Patrón 3: Partial Update

```python
class ActualizarProfesorUseCase:
    def execute(
        self,
        profesor_id: int,
        update_dto: ProfesorUpdateSchema
    ) -> ProfesorResponseSchema:
        """Actualiza solo campos proporcionados."""
        
        # Obtener entity existente
        entity = self.profesor_repository.get_by_id(profesor_id)
        if not entity:
            raise NotFoundError(f"Profesor {profesor_id} no existe")
        
        # Actualizar solo campos no-None
        update_data = update_dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entity, field, value)
        
        # Persistir
        updated = self.profesor_repository.save(entity)
        return ProfesorResponseSchema.from_entity(updated)


# Uso
update_dto = ProfesorUpdateSchema(
    email="nuevo@example.com"  # Solo actualizar email
)
result = use_case.execute(profesor_id=5, update_dto=update_dto)
```

---

## 🔄 Conversiones

### Entity → Schema

```python
class GuardiaResponseSchema(BaseModel):
    id: int
    fecha: date
    turno: str
    profesor_nombre: str
    
    @classmethod
    def from_entity(cls, entity: GuardiaEntity) -> "GuardiaResponseSchema":
        """Factory method: Entity → Schema."""
        return cls(
            id=entity.id,
            fecha=entity.fecha,
            turno=entity.turno,
            profesor_nombre=entity.profesor.nombre_completo if entity.profesor else "N/A"
        )
```

### Schema → Entity

```python
class CrearGuardiaUseCase:
    def execute(self, input_dto: GuardiaCreateSchema) -> GuardiaResponseSchema:
        """Convierte schema → entity → schema."""
        
        # Schema → Entity
        entity = GuardiaEntity(
            fecha=input_dto.fecha,
            turno=input_dto.turno,
            recreo=input_dto.recreo,
            profesor_id=input_dto.profesor_id,
            zona_id=input_dto.zona_id
        )
        
        # Persistir
        saved = self.guardia_repository.save(entity)
        
        # Entity → Schema (output)
        return GuardiaResponseSchema.from_entity(saved)
```

### Schema → JSON

```python
# Serialización
guardia_schema = GuardiaResponseSchema(...)
json_str = guardia_schema.model_dump_json()  # → JSON string
dict_data = guardia_schema.model_dump()      # → Python dict

# Deserialización
json_data = '{"id": 1, "fecha": "2025-10-23", ...}'
guardia = GuardiaResponseSchema.model_validate_json(json_data)
```

---

## 🧪 Testing con Schemas

### Test 1: Validación Básica

```python
import pytest
from pydantic import ValidationError
from domain.schemas import ProfesorCreateSchema


def test_profesor_create_schema_valido():
    """Schema válido debe pasar validación."""
    schema = ProfesorCreateSchema(
        nombre="Juan",
        apellidos="Pérez García",
        email="juan@example.com"
    )
    
    assert schema.nombre == "Juan"
    assert schema.email == "juan@example.com"


def test_profesor_create_schema_email_invalido():
    """Email inválido debe lanzar ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ProfesorCreateSchema(
            nombre="Juan",
            apellidos="Pérez",
            email="email-sin-arroba"
        )
    
    errors = exc_info.value.errors()
    assert any(err['loc'] == ('email',) for err in errors)
```

### Test 2: Validadores Personalizados

```python
from datetime import date, timedelta


def test_guardia_fecha_pasada():
    """Fecha pasada debe fallar."""
    ayer = date.today() - timedelta(days=1)
    
    with pytest.raises(ValidationError) as exc_info:
        GuardiaCreateSchema(
            fecha=ayer,
            turno="MAÑANA",
            recreo=1,
            profesor_id=1,
            zona_id=1
        )
    
    error = exc_info.value.errors()[0]
    assert 'fecha' in error['loc']
    assert 'pasada' in error['msg'].lower()
```

### Test 3: Conversión Entity → Schema

```python
def test_from_entity():
    """Conversión correcta de entity a schema."""
    # Arrange
    entity = GuardiaEntity(
        id=1,
        fecha=date(2025, 10, 23),
        turno="MAÑANA",
        recreo=1,
        profesor_id=5,
        zona_id=2
    )
    entity.profesor = ProfesorEntity(id=5, nombre="Juan", apellidos="Pérez")
    
    # Act
    schema = GuardiaResponseSchema.from_entity(entity)
    
    # Assert
    assert schema.id == 1
    assert schema.profesor_nombre == "Juan Pérez"
```

---

## ✅ Best Practices

### 1. Organización de Schemas

```python
# ✅ BUENO: Herencia para reutilizar código
class ProfesorBaseSchema(BaseModel):
    nombre: str
    apellidos: str

class ProfesorCreateSchema(ProfesorBaseSchema):
    email: str

class ProfesorResponseSchema(ProfesorBaseSchema):
    id: int
    email: str


# ❌ MALO: Duplicar código
class ProfesorCreateSchema(BaseModel):
    nombre: str
    apellidos: str
    email: str

class ProfesorResponseSchema(BaseModel):
    nombre: str  # ❌ Duplicado
    apellidos: str  # ❌ Duplicado
    id: int
    email: str
```

### 2. Validaciones

```python
# ✅ BUENO: Validaciones simples en schema
@field_validator('email')
@classmethod
def email_lowercase(cls, v: str) -> str:
    return v.lower()


# ❌ MALO: Validaciones con BD en schema
@field_validator('profesor_id')
@classmethod
def profesor_existe(cls, v: int) -> int:
    # ❌ NO acceder a BD desde validator
    if not db.query(Profesor).filter_by(id=v).first():
        raise ValueError("Profesor no existe")
    return v

# ✅ BUENO: Validaciones con BD en use case
class CrearGuardiaUseCase:
    def execute(self, dto: GuardiaCreateSchema):
        if not self.profesor_repo.exists(dto.profesor_id):
            raise NotFoundError("Profesor no existe")
```

### 3. Documentación

```python
# ✅ BUENO: Schemas documentados
class GuardiaCreateSchema(BaseModel):
    """
    Schema para crear una guardia.
    
    Validaciones:
    - fecha: No puede ser pasada ni fin de semana
    - turno: Solo MAÑANA o TARDE
    - recreo: 1-3 para MAÑANA, 1-2 para TARDE
    """
    fecha: date = Field(..., description="Fecha de la guardia")
    turno: str = Field(..., pattern="^(MAÑANA|TARDE)$")
    recreo: int = Field(..., ge=1, le=3)
    
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [{
                'fecha': '2025-10-25',
                'turno': 'MAÑANA',
                'recreo': 1,
                'profesor_id': 5,
                'zona_id': 2
            }]
        }
    )
```

### 4. Naming Conventions

```python
# ✅ BUENO: Sufijos claros
ProfesorCreateSchema   # Para POST
ProfesorUpdateSchema   # Para PUT/PATCH
ProfesorResponseSchema # Para GET
ProfesorBaseSchema     # Base compartida


# ❌ MALO: Nombres ambiguos
ProfesorSchema         # ¿Qué operación?
ProfesorInput          # ¿Create o Update?
ProfesorOutput         # Poco específico
```

---

## 📚 Referencias

- **Pydantic V2 Docs**: https://docs.pydantic.dev/latest/
- **Field Validators**: https://docs.pydantic.dev/latest/concepts/validators/
- **Model Config**: https://docs.pydantic.dev/latest/api/config/
- **JSON Schema**: https://docs.pydantic.dev/latest/concepts/json_schema/

---

**Documento vivo:** Actualizar cuando se agreguen nuevos schemas o patrones de validación.
