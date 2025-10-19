# Task 5: Tests de Integración - Sprint 6

**Estado**: 🔄 **40% EN PROGRESO**  
**Fecha**: 19 de octubre de 2025  
**Objetivo**: Testear flujos End-to-End que cruzan todas las capas arquitectónicas

---

## 📋 Índice

1. [Estado Actual](#estado-actual)
2. [Task 5.1: Análisis Arquitectura](#51-análisis-arquitectura-✅)
3. [Task 5.2: Tests Integración CRUD](#52-tests-integración-crud-✅)
4. [Task 5.3: Tests Integración Guardias](#53-tests-integración-guardias-⬜)
5. [Task 5.4: Tests Integración Import/Export](#54-tests-integración-importexport-⬜)
6. [Task 5.5: Documentar y Ejecutar](#55-documentar-y-ejecutar-⬜)
7. [Descubrimientos Clave](#descubrimientos-clave)

---

## Estado Actual

**Progreso**: 40% (2/5 subtareas completadas)

- ✅ **Task 5.1**: Análisis de arquitectura - **COMPLETADO**
- ✅ **Task 5.2**: Tests integración CRUD - **COMPLETADO** 🎉
- ⬜ **Task 5.3**: Tests integración guardias - Pendiente
- ⬜ **Task 5.4**: Tests integración import/export - Pendiente
- ⬜ **Task 5.5**: Ejecutar y documentar - Pendiente

**Archivos creados**:
- `tests/test_integration_crud.py` (625 líneas, 12 tests) ✅

**Tests**:
- Total: 12 tests
- Pasando: 12 ✅ **100%** 🎉
- Fallando: 0 ❌

**Tiempo ejecución**: 1.55s  
**Coverage**: 23.69% (solo este archivo)

---

## 5.1. Análisis Arquitectura ✅

### Descubrimiento: Clean Architecture con DTOs

Durante el análisis se descubrió que el proyecto sigue **Clean Architecture** con **patrón DTO** de forma consistente.

**Patrón identificado**:
```python
# Todos los Use Cases siguen este patrón:
class SomeUseCase:
    def execute(self, dto: InputDTO) -> OutputDTO:
        """
        @param dto: Data Transfer Object con todos los parámetros
        @return: DTO con resultado de la operación
        """
        # Business logic
        return result_dto
```

### DTOs Principales Identificados

#### Configuración
```python
from application.dtos.configuracion_dto import (
    ActualizarConfiguracionDTO,
    ConfiguracionDTO
)

# Uso:
dto = ActualizarConfiguracionDTO(
    fecha_inicio_curso=date(2024, 9, 1),
    fecha_fin_curso=date(2025, 6, 30),
    hora_recreo1_manana=time(10, 30),
    hora_recreo2_tarde=time(16, 45),
    # ... más campos
)
resultado = actualizar_config_uc.execute(dto)
```

#### Profesores
```python
from application.dtos.profesor_dto import (
    CrearProfesorDTO,
    ActualizarProfesorDTO,
    ProfesorDTO
)

# Uso:
dto = CrearProfesorDTO(
    nombre_completo="Juan Pérez",
    email="juan.perez@colegio.es",
    horas_contrato=25.0,
    turno="mañana",
    # ... más campos
)
resultado = crear_profesor_uc.execute(dto)
```

#### Zonas
```python
from application.dtos.zona_dto import (
    CrearZonaDTO,
    ZonaDTO
)

# Uso:
dto = CrearZonaDTO(
    nombre_zona="Patio Principal",
    descripcion="Zona central del recreo"
)
resultado = crear_zona_uc.execute(dto)
```

#### Guardias
```python
from application.dtos.guardia_dto import (
    CrearGuardiaDTO,
    GuardiaDTO
)

# Uso:
dto = CrearGuardiaDTO(
    profesor_id=1,
    zona_id=2,
    fecha=date(2024, 10, 15),
    recreo=1  # 1=mañana, 2=tarde
)
resultado = asignar_guardia_uc.execute(dto)
```

#### Asignación y Estadísticas
```python
from application.dtos.asignacion_guardias_dto import (
    ResumenGeneracionDTO,
    ResumenDistribucionDTO,
    EstadisticasDTO
)

# Uso:
resultado = generar_guardias_uc.execute(GenerarGuardiasDTO(...))
# resultado es ResumenGeneracionDTO

distribucion = calcular_distribucion_uc.execute()
# distribucion es ResumenDistribucionDTO

estadisticas = obtener_estadisticas_uc.execute()
# estadisticas es EstadisticasDTO
```

### Capas Arquitectónicas

```
┌─────────────────────────────────────────────────┐
│         PRESENTATION LAYER                      │
│  Forms, Widgets (PyQt6)                        │
│  - ProfesorForm, ZonaForm, etc.                │
│  - VistaCalendario, PanelEstadisticas          │
└──────────────────┬──────────────────────────────┘
                   │ Calls
┌──────────────────▼──────────────────────────────┐
│         APPLICATION LAYER                       │
│  Use Cases with DTOs                           │
│  - CrearProfesorUseCase(dto) → ProfesorDTO     │
│  - AsignarGuardiaUseCase(dto) → GuardiaDTO     │
└──────────────────┬──────────────────────────────┘
                   │ Uses
┌──────────────────▼──────────────────────────────┐
│         DOMAIN LAYER                            │
│  Entities, Value Objects, Repository Interfaces│
│  - Profesor, Zona, Guardia (entities)          │
│  - Email, HorasContrato (value objects)        │
│  - IProfesorRepository (interface)             │
└──────────────────┬──────────────────────────────┘
                   │ Implemented by
┌──────────────────▼──────────────────────────────┐
│         INFRASTRUCTURE LAYER                    │
│  SQLAlchemy Repositories                       │
│  - SQLAlchemyProfesorRepository                │
│  - SQLAlchemyZonaRepository                    │
└──────────────────┬──────────────────────────────┘
                   │ Persists to
┌──────────────────▼──────────────────────────────┐
│         DATA LAYER                              │
│  Database, ORM Models                          │
│  - SQLite database                             │
│  - Profesor, Zona, Guardia (ORM models)        │
└─────────────────────────────────────────────────┘
```

### Implicaciones para Tests de Integración

**❌ Enfoque INCORRECTO** (como están los tests ahora):
```python
def test_crear_configuracion():
    # Llamar Use Case con kwargs directos
    resultado = actualizar_config_uc.execute(
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        # ...
    )
    # TypeError: execute() got an unexpected keyword argument 'fecha_inicio_curso'
```

**✅ Enfoque CORRECTO** (cómo deben ser):
```python
from application.dtos.configuracion_dto import ActualizarConfiguracionDTO

def test_crear_configuracion():
    # 1. Crear DTO con parámetros
    dto = ActualizarConfiguracionDTO(
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(10, 30),
        # ... todos los campos necesarios
    )
    
    # 2. Llamar Use Case con DTO
    resultado = actualizar_config_uc.execute(dto)
    
    # 3. Verificar resultado (también es un DTO)
    assert isinstance(resultado, ConfiguracionDTO)
    assert resultado.fecha_inicio_curso == date(2024, 9, 1)
```

---

## 5.2. Tests Integración CRUD ✅

**Archivo**: `tests/test_integration_crud.py` (625 líneas)

**Estado**: 
- ✅ **12/12 tests PASSING** 🎉
- ⏱️ Tiempo: 1.55s
- 📊 Coverage: 23.69% (solo este archivo)

### Refactorización Completada ✅

Todos los tests fueron exitosamente refactorizados para usar el patrón DTO correctamente.

**Cambio principal aplicado**:
```python
# ❌ ANTES (incorrecto - kwargs directos):
config_uc.execute(
    fecha_inicio_curso=date(2024, 9, 1),
    fecha_fin_curso=date(2025, 6, 30),
    # ...
)

# ✅ DESPUÉS (correcto - usando DTO):
from application.dtos.configuracion_dto import ActualizarConfiguracionDTO

dto = ActualizarConfiguracionDTO(
    fecha_inicio_curso=date(2024, 9, 1),
    fecha_fin_curso=date(2025, 6, 30),
    hora_recreo1_manana=time(10, 30),
    hora_recreo2_tarde=time(16, 45),
)
resultado = config_uc.execute(dto)
```

### Descubrimientos Durante la Refactorización

#### 1. Campo `es_tutor` → `tutor` ✅
```python
# ❌ Incorrecto (nombre antiguo):
CrearProfesorDTO(nombre_completo="...", es_tutor=True, ...)

# ✅ Correcto (nombre actual):
CrearProfesorDTO(nombre_completo="...", tutor=True, ...)
```

#### 2. Campo `recreo` → `numero_recreo` ✅
```python
# ❌ Incorrecto:
CrearGuardiaDTO(profesor_id=..., zona_id=..., recreo=1)

# ✅ Correcto:
CrearGuardiaDTO(profesor_id=..., zona_id=..., numero_recreo=1)
```

#### 3. Firma Especial: ActualizarProfesorUseCase ✅
```python
# ⚠️ DIFERENTE a otros Use Cases:
# La mayoría: execute(dto)
# Este: execute(id, dto)

from application.use_cases.profesor.actualizar_profesor import ActualizarProfesorUseCase

actualizar_uc = ActualizarProfesorUseCase(repo)
dto = ActualizarProfesorDTO(nombre_completo="...", turno="...")
resultado = actualizar_uc.execute(profesor_id, dto)  # ID separado del DTO
```

### Tests Implementados (12/12 ✅)

#### 1. TestIntegrationSetupInicial (2 tests) ✅

**test_setup_sistema_desde_cero** ✅
- Flujo: Config → Profesores → Zonas
- DTOs: `ActualizarConfiguracionDTO`, `CrearProfesorDTO`, `CrearZonaDTO`
- Valida: Setup completo del sistema
    profesor_id=profesor.profesor_id,
    nombre_completo="Nuevo Nombre",
    email="nuevo@email.com"
)

# Solución:
from application.dtos.profesor_dto import ActualizarProfesorDTO

dto = ActualizarProfesorDTO(
    profesor_id=profesor.profesor_id,
    nombre_completo="Nuevo Nombre",
    email="nuevo@email.com",
    # ... otros campos del profesor
)
resultado = actualizar_uc.execute(dto)
```

#### 6. test_calcular_estadisticas_sistema_completo ❌
```python
# Este puede no necesitar DTO si el Use Case no requiere parámetros
# Verificar firma del Use Case
```

#### 7. test_calcular_distribucion_con_datos_reales ❌
```python
# Similar a estadísticas
# Verificar si CalcularDistribucionUseCase requiere DTO
```

#### 8. test_relaciones_orm_bidireccionales ❌
```python
# Puede necesitar CrearGuardiaDTO para asignar guardias
```

### Estructura de Tests Diseñada

```python
# tests/test_integration_crud.py

class TestIntegrationSetupInicial:
    """Tests de setup inicial del sistema"""
    
    def test_setup_sistema_desde_cero(self, session):
        """
        Flujo: Configuración → Profesores → Zonas
        Valida: Sistema se puede inicializar desde cero
        """
        
    def test_modificar_configuracion_existente(self, session):
        """
        Flujo: Crear config → Actualizar config
        Valida: Patrón upsert (crear o actualizar)
        """


class TestIntegrationAsignacionGuardias:
    """Tests de asignación de guardias"""
    
    def test_flujo_completo_asignar_guardia(self, session):
        """
        Flujo: Crear profesor → Crear zona → Asignar guardia
        Valida: Asignación exitosa con validaciones
        """
        
    def test_flujo_multiples_guardias_mismo_dia(self, session):
        """
        Flujo: Múltiples asignaciones mismo día
        Valida: Regla max 1 guardia por profesor al día
        """


class TestIntegrationModificacionEliminacion:
    """Tests de modificación y eliminación con relaciones"""
    
    def test_eliminar_profesor_sin_guardias(self, session):
        """Eliminar profesor sin dependencias - OK"""
        
    def test_eliminar_zona_sin_guardias(self, session):
        """Eliminar zona sin guardias - OK"""
        
    def test_actualizar_profesor_con_guardias(self, session):
        """
        Flujo: Crear profesor → Asignar guardias → Actualizar profesor
        Valida: Actualización no afecta guardias existentes
        """


class TestIntegrationConServicios:
    """Tests de integración con servicios de negocio"""
    
    def test_calcular_estadisticas_sistema_completo(self, session):
        """
        Flujo: Setup completo → Calcular estadísticas
        Valida: EstadisticasDTO correcto
        """
        
    def test_calcular_distribucion_con_datos_reales(self, session):
        """
        Flujo: Setup → Calcular distribución
        Valida: ResumenDistribucionDTO correcto
        """


class TestIntegrationConsistenciaDatos:
    """Tests de consistencia de datos entre capas"""
    
    def test_profesor_factory_crea_en_bd(self, session):
        """Factory crea en BD correctamente"""
        
    def test_zona_factory_crea_en_bd(self, session):
        """Factory crea zona correctamente"""
        
    def test_relaciones_orm_bidireccionales(self, session):
        """
        Flujo: Crear profesor/zona → Asignar guardia → Verificar relaciones
        Valida: ORM relationships bidireccionales
        """
```

### Plan de Refactoring

**Pasos para arreglar los 8 tests**:

1. **Importar DTOs necesarios** (al inicio del archivo):
```python
from application.dtos.configuracion_dto import ActualizarConfiguracionDTO, ConfiguracionDTO
from application.dtos.profesor_dto import CrearProfesorDTO, ActualizarProfesorDTO, ProfesorDTO
from application.dtos.zona_dto import CrearZonaDTO, ZonaDTO
from application.dtos.guardia_dto import CrearGuardiaDTO, GuardiaDTO
from application.dtos.asignacion_guardias_dto import EstadisticasDTO, ResumenDistribucionDTO
```

2. **Refactorizar cada test fallando**:
   - Identificar qué Use Case se llama
   - Crear DTO correspondiente con los parámetros
   - Pasar DTO al `execute()`
   - Verificar resultado (también es DTO)

3. **Ejecutar tests y verificar 12/12 passing**

**Estimación**: 30-45 minutos

---

## 5.3. Tests Integración Guardias ⬜

**Archivo planificado**: `tests/test_integration_guardias.py`

**Objetivo**: Testear flujo completo de generación de calendario de guardias

### Flujos a Testear

#### 1. Generación Calendario Completo
```python
def test_generar_calendario_desde_configuracion(session):
    """
    Flujo: Configuración → Profesores → Zonas → Generar Calendario
    
    Setup:
    - Configuración: curso 2024-2025, 2 recreos
    - 10 profesores activos con diferentes cuotas
    - 5 zonas
    
    Acción:
    - GenerarGuardiasUseCase.execute()
    
    Validaciones:
    - Todas las zonas cubiertas
    - Distribución equitativa según cuotas
    - 9 restricciones del asignador respetadas:
      1. ✅ Cuota de guardias (no exceder)
      2. ✅ Turno del recreo (mañana/tarde/mixto)
      3. ✅ Fecha inicio guardias
      4. ✅ Fecha fin guardias
      5. ✅ Días de la semana permitidos
      6. ✅ Matriz horario permitido (día × recreo)
      7. ✅ Ausencias del profesor
      8. ✅ No simultaneidad (misma zona, mismo slot)
      9. ✅ Máximo 1 guardia al día
    """
```

#### 2. Validar Distribución Equitativa
```python
def test_distribucion_equitativa_segun_cuotas(session):
    """
    Validar que el algoritmo distribuye guardias proporcionalmente
    
    Setup:
    - Profesor A: cuota 10
    - Profesor B: cuota 5
    - Profesor C: cuota 20
    - Total: 35 guardias a asignar
    
    Resultado esperado:
    - Profesor A: ~10 guardias (±2)
    - Profesor B: ~5 guardias (±2)
    - Profesor C: ~20 guardias (±2)
    """
```

#### 3. Validar Restricción Días Permitidos
```python
def test_respetar_dias_semana_permitidos(session):
    """
    Validar que profesores solo reciben guardias en días permitidos
    
    Setup:
    - Profesor A: dias_permitidos = "0,1,2" (Lun, Mar, Mié)
    - Profesor B: dias_permitidos = "3,4" (Jue, Vie)
    - Profesor C: dias_permitidos = None (todos los días)
    
    Validaciones:
    - Profesor A solo guardias Lun-Mié
    - Profesor B solo guardias Jue-Vie
    - Profesor C cualquier día
    """
```

#### 4. Manejo de Ausencias en Generación
```python
def test_excluir_profesores_con_ausencias(session):
    """
    Validar que profesores con ausencias no reciben guardias
    
    Setup:
    - Profesor A: ausencia 15-20 Oct
    - Calendario: generar Octubre completo
    
    Validación:
    - Profesor A sin guardias del 15-20 Oct
    - Profesor A puede recibir guardias otros días
    """
```

#### 5. Regenerar Calendario
```python
def test_regenerar_calendario_elimina_previas(session):
    """
    Validar opción de eliminar guardias existentes
    
    Flujo:
    - Generar calendario (100 guardias creadas)
    - Cambiar configuración (modificar cuotas)
    - Regenerar con eliminar=True
    
    Validación:
    - Guardias anteriores eliminadas
    - Nuevas guardias con distribución actualizada
    """
```

**Estimación**: 20-30 tests, 2-3 horas de desarrollo

---

## 5.4. Tests Integración Import/Export ⬜

**Archivo planificado**: `tests/test_integration_import_export.py`

**Objetivo**: Testear flujos completos de importación/exportación

### Flujos a Testear

#### 1. Exportar → Importar → Verificar
```python
def test_ciclo_completo_exportar_importar(session, tmp_path):
    """
    Flujo: Exportar datos → Limpiar BD → Importar → Verificar integridad
    
    Setup:
    - 5 profesores con guardias
    - 3 zonas
    - 50 guardias asignadas
    
    Flujo:
    1. Exportar todo a JSON (tmp_path/export.json)
    2. Limpiar BD (eliminar todo)
    3. Importar desde JSON
    4. Verificar: 5 profesores, 3 zonas, 50 guardias
    5. Verificar: relaciones correctas (profesor ↔ guardia ↔ zona)
    """
```

#### 2. Exportar PDF Calendario Completo
```python
def test_exportar_pdf_calendario_mes(session, tmp_path):
    """
    Exportar calendario de un mes a PDF
    
    Setup:
    - Calendario generado Octubre 2024
    - 100 guardias distribuidas
    
    Flujo:
    1. ExportarPDFUseCase(mes=10, año=2024)
    2. Verificar PDF creado (tmp_path/guardias_oct_2024.pdf)
    3. Verificar PDF no vacío (size > 10KB)
    """
```

#### 3. Manejo de Datos Vacíos
```python
def test_exportar_sin_datos_no_falla(session, tmp_path):
    """
    Validar que exportar sin datos no lanza excepción
    
    Setup:
    - BD vacía (sin profesores, zonas, guardias)
    
    Flujo:
    1. Exportar a JSON
    2. Verificar archivo creado con estructura válida
    3. Verificar listas vacías: profesores=[], zonas=[], guardias=[]
    """
```

#### 4. Errores de Formato en Importación
```python
def test_importar_json_invalido_lanza_error(session, tmp_path):
    """
    Validar manejo de errores en formato incorrecto
    
    Setup:
    - JSON con estructura incorrecta
    
    Casos:
    - JSON malformado (syntax error)
    - JSON sin campo 'profesores'
    - Profesor sin campo 'nombre_completo'
    
    Validación:
    - Lanza ValidationError con mensaje claro
    - BD no modificada (rollback)
    """
```

**Estimación**: 15-20 tests, 1-2 horas de desarrollo

---

## 5.5. Documentar y Ejecutar ⬜

**Tareas finales**:

1. ✅ Ejecutar suite completa de tests de integración
2. ✅ Medir impacto en coverage
3. ✅ Documentar flujos E2E en README
4. ✅ Actualizar RESUMEN_SPRINT_6_TESTING.md
5. ✅ Commit final Task 5

**Estimación**: 1 hora

---

## Descubrimientos Clave

### 1. Clean Architecture Estricta

El proyecto sigue Clean Architecture de forma rigurosa:
- **Separation of Concerns**: Cada capa tiene responsabilidad clara
- **Dependency Inversion**: Capas externas dependen de interfaces internas
- **DTOs**: Transferencia de datos entre capas sin exponer entidades

**Beneficios para testing**:
- Tests pueden enfocarse en una capa sin afectar otras
- Mocking más fácil (interfaces bien definidas)
- Tests de integración validan flujo completo entre capas

### 2. Patrón DTO Consistente

Todos los Use Cases siguen el mismo patrón:
```python
UseCase.execute(dto: InputDTO) -> OutputDTO
```

**Beneficios**:
- API consistente y predecible
- Validación centralizada (Pydantic DTOs)
- Fácil de testear (crear DTO, verificar DTO)

**Desafío inicial**:
- Tests escritos asumiendo kwargs directos
- Necesidad de refactoring para usar DTOs

### 3. Validaciones en Múltiples Capas

**Validaciones encontradas**:
- **DTO Layer**: Tipos, rangos, formatos (Pydantic)
- **Use Case Layer**: Lógica de negocio (duplicados, relaciones)
- **Service Layer**: Algoritmos complejos (asignador, calculador)
- **Repository Layer**: Integridad referencial (foreign keys)

**Implicación para tests**:
- Tests deben cubrir validaciones en cada capa
- Tests de integración validan que validaciones cooperan correctamente

### 4. Factory Pattern para Tests

**Factories creadas en conftest.py**:
```python
profesor_factory(session)
zona_factory(session)
guardia_factory(session)
ausencia_factory(session)
```

**Ventajas**:
- Crear datos de prueba con defaults sensatos
- Override solo campos necesarios para el test
- Consistencia entre tests

**Uso en tests de integración**:
```python
def test_algo(session, profesor_factory, zona_factory):
    # Crear datos con factories
    prof1 = profesor_factory(nombre_completo="Juan", cuota_guardias=10)
    prof2 = profesor_factory(nombre_completo="Ana", cuota_guardias=5)
    zona = zona_factory(nombre_zona="Patio")
    
    # Test flujo E2E
    # ...
```

---

## Resumen Task 5

**Estado actual**:
- ✅ Arquitectura analizada y documentada
- ✅ Tests de integración creados (12 tests)
- 🔄 Refactoring DTO pendiente (8 tests)
- ⬜ Tests guardias pendientes (~20-30 tests)
- ⬜ Tests import/export pendientes (~15-20 tests)

**Estimación total**:
- Tests totales Task 5: ~60-80 tests
- Tiempo restante: ~5-7 horas
- Coverage estimado: +10-15pp (52% → 62-67%)

**Próximos pasos**:
1. Refactorizar test_integration_crud.py (30-45 min)
2. Crear test_integration_guardias.py (2-3 horas)
3. Crear test_integration_import_export.py (1-2 horas)
4. Ejecutar suite completa y documentar (1 hora)
5. Commit y push Task 5 completa

---

**Fecha última actualización**: 19 de octubre de 2025  
**Documento**: TASK_5_INTEGRATION_TESTS.md  
**Sprint**: Sprint 6 - Testing
