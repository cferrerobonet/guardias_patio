# Resumen de Arquitectura - Versión 2.6

**Fecha**: 18 de octubre de 2025  
**Versión**: 2.6.0  
**Estado**: Arquitectura Limpia Consolidada

## 📐 Vista General de la Arquitectura

### Estructura del Proyecto (Post Sprint 5)

```
guardias_patio/
├── src/
│   ├── main.py                    # Punto de entrada (MainWindow)
│   ├── ui_styles.py               # Estilos globales PyQt6
│   │
│   ├── presentation/              # 🆕 CAPA DE PRESENTACIÓN
│   │   ├── forms/                 # Formularios (Sprint 4)
│   │   │   ├── base_form.py       # ⭐ Clase base compartida
│   │   │   ├── profesor_form.py
│   │   │   ├── zona_form.py
│   │   │   ├── configuracion_form.py
│   │   │   ├── asignacion_guardias_form.py
│   │   │   ├── calendario_guardias_form.py
│   │   │   └── import_export_form.py
│   │   │
│   │   └── widgets/               # Widgets (Sprint 5) 🆕
│   │       ├── __init__.py
│   │       ├── vista_calendario.py
│   │       ├── gestor_sustituciones.py
│   │       ├── panel_estadisticas.py
│   │       └── gestionar_ausencias.py
│   │
│   ├── services/                  # CAPA DE SERVICIOS
│   │   ├── asignador_guardias.py
│   │   ├── calculador_guardias.py
│   │   ├── exportador_pdf.py
│   │   ├── exportador.py
│   │   └── gestor_ausencias.py    # ⭐ Usado por GestionarAusenciasForm
│   │
│   ├── models/                    # CAPA DE DOMINIO
│   │   └── models.py              # Profesor, Zona, Guardia, Ausencia, etc.
│   │
│   ├── database/                  # CAPA DE DATOS
│   │   └── db_manager.py          # SessionLocal, engine
│   │
│   ├── utils/                     # UTILIDADES
│   │   ├── cache.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── logger.py
│   │   ├── query_optimizer.py
│   │   └── validators.py
│   │
│   └── widgets/                   # ⚠️ LEGACY (deprecado)
│       └── ...                    # Archivos antiguos
│
├── tests/                         # TESTING
│   ├── test_asignador.py
│   ├── test_calculador.py
│   └── ...
│
├── alembic/                       # MIGRACIONES DB
│   └── versions/
│
└── documentacion/                 # DOCUMENTACIÓN
    ├── SPRINT_5_WIDGETS.md        # 🆕
    ├── CHANGELOG_v2.6.md          # 🆕
    └── ...
```

## 🏛️ Capas de la Arquitectura

### 1. Presentation Layer (UI)

**Responsabilidad**: Interacción con usuario, visualización de datos

**Componentes**:
- **BaseForm** (`presentation/forms/base_form.py`)
  - Clase base abstracta
  - Manejo de errores centralizado
  - Métodos de mensajes (éxito, error, advertencia, confirmación)
  - Logger integrado
  - Session management

- **Forms** (`presentation/forms/`)
  - 6 formularios CRUD
  - Heredan de `BaseForm`
  - Inyección de sesión
  
- **Widgets** (`presentation/widgets/`)
  - 4 widgets de visualización/gestión
  - Heredan de `BaseForm`
  - Inyección de sesión

**Patrón de diseño**:
```python
class ComponenteUI(BaseForm):
    def __init__(self, session):
        super().__init__(session)
        self.setup_ui()
    
    def setup_ui(self):
        """Construcción modular de UI"""
        pass
    
    def refrescar(self):
        """Actualización de datos"""
        pass
```

### 2. Service Layer (Lógica de Negocio)

**Responsabilidad**: Operaciones de negocio, validaciones, cálculos

**Componentes**:
- `asignador_guardias.py`: Algoritmo de asignación
- `calculador_guardias.py`: Cálculos de distribución
- `gestor_ausencias.py`: CRUD de ausencias + reasignación
- `exportador.py` / `exportador_pdf.py`: Generación de reportes

**Principios**:
- ✅ No conocen la UI (PyQt6)
- ✅ Reciben session como parámetro
- ✅ Retornan datos puros o excepciones
- ✅ Reutilizables desde cualquier capa

**Ejemplo**:
```python
# services/gestor_ausencias.py
def registrar_ausencia(session, profesor_id, fecha_inicio, fecha_fin, tipo, motivo):
    """Registrar nueva ausencia."""
    # Validaciones
    # Operaciones DB
    # Retornar resultado
```

### 3. Domain Layer (Modelos)

**Responsabilidad**: Definición de entidades del dominio

**Modelos** (`models/models.py`):
- `Profesor`: Profesores del centro
- `Zona`: Zonas de vigilancia
- `Guardia`: Asignaciones de guardias
- `Ausencia`: Registro de ausencias
- `ConfigProfesor`: Configuración individual
- `DiaNonLectivo`: Días no lectivos

**Características**:
- ORM SQLAlchemy
- Relationships definidas
- Validaciones a nivel modelo

### 4. Data Layer (Acceso a Datos)

**Responsabilidad**: Gestión de conexiones y sesiones DB

**Componente**: `database/db_manager.py`
- Engine SQLAlchemy
- `SessionLocal` factory
- Configuración de conexión

**Patrón de uso**:
```python
# En MainWindow
self.session = SessionLocal()

# En componentes UI
component = Component(self.session)

# Cierre al salir
self.session.close()
```

### 5. Utils Layer (Utilidades)

**Responsabilidad**: Funciones auxiliares transversales

**Módulos**:
- `logger.py`: Sistema de logging
- `cache.py`: Caching de datos
- `validators.py`: Validaciones comunes
- `exceptions.py`: Excepciones personalizadas
- `constants.py`: Constantes globales
- `query_optimizer.py`: Optimización de queries

## 🔄 Flujo de Datos

### Ejemplo: Crear Ausencia

```
┌─────────────┐
│   Usuario   │
└──────┬──────┘
       │ 1. Rellena formulario
       ▼
┌──────────────────────────┐
│ GestionarAusenciasForm   │ ◄── Presentation Layer
│ (presentation/widgets)   │
└──────┬───────────────────┘
       │ 2. Valida datos UI
       │ 3. Llama servicio
       ▼
┌──────────────────────────┐
│ gestor_ausencias.py      │ ◄── Service Layer
│ registrar_ausencia()     │
└──────┬───────────────────┘
       │ 4. Validaciones negocio
       │ 5. Crea objeto Ausencia
       ▼
┌──────────────────────────┐
│ models.py                │ ◄── Domain Layer
│ Ausencia(...)            │
└──────┬───────────────────┘
       │ 6. session.add()
       │ 7. session.commit()
       ▼
┌──────────────────────────┐
│ SQLite Database          │ ◄── Data Layer
│ ausencias.db             │
└──────────────────────────┘
```

## 🎨 Patrones de Diseño Aplicados

### 1. Dependency Injection

**Problema**: Acoplamiento directo con `SessionLocal()`

**Solución**: Inyectar sesión en constructor

```python
# ❌ Antes (acoplado)
class Widget(QWidget):
    def __init__(self):
        self.session = SessionLocal()

# ✅ Después (inyectado)
class Widget(BaseForm):
    def __init__(self, session):
        super().__init__(session)
```

**Beneficios**:
- Facilita testing (mock de sesión)
- Control centralizado de ciclo de vida
- Reducción de acoplamiento

### 2. Template Method (BaseForm)

**Problema**: Duplicación de código en forms/widgets

**Solución**: Clase base con métodos comunes

```python
class BaseForm(QWidget):
    def manejar_excepcion(self, e, contexto):
        """Template para manejo de errores"""
        self.logger.error(f"{contexto}: {e}")
        QMessageBox.critical(self, "Error", str(e))
    
    def mostrar_exito(self, titulo, mensaje):
        """Template para mensajes de éxito"""
        QMessageBox.information(self, titulo, mensaje)
```

**Beneficios**:
- Comportamiento consistente
- Reducción de duplicación
- Fácil mantenimiento

### 3. Service Layer Pattern

**Problema**: Lógica de negocio mezclada con UI

**Solución**: Capa de servicios independiente

```python
# Servicio puro (sin PyQt6)
def calcular_guardias_necesarias(session, fecha_inicio, fecha_fin):
    # Lógica de cálculo
    return resultado

# Usado desde UI
resultado = calcular_guardias_necesarias(self.session, inicio, fin)
self.mostrar_resultado(resultado)
```

**Beneficios**:
- Reutilización desde CLI/API/UI
- Testeable sin UI
- Separación de responsabilidades

### 4. Repository Pattern (Implícito)

**Implementación**: A través de SQLAlchemy ORM

```python
# Queries en servicios, no en UI
profesores = session.query(Profesor).filter_by(activo=True).all()
```

**Beneficios**:
- Abstracción de acceso a datos
- Cambio de DB sin afectar servicios

## 📊 Métricas de Arquitectura

### Distribución de Código

```
Presentation Layer:  ~4,280 líneas (40%)
Service Layer:       ~2,500 líneas (23%)
Domain Layer:        ~800 líneas (7%)
Data Layer:          ~200 líneas (2%)
Utils:               ~1,500 líneas (14%)
Tests:               ~1,500 líneas (14%)
─────────────────────────────────────
TOTAL:               ~10,780 líneas
```

### Acoplamiento

| Capa | Depende de | Acoplamiento |
|------|------------|--------------|
| Presentation | Services, Models, Utils | Medio ✅ |
| Services | Models, Utils | Bajo ✅ |
| Models | - | Ninguno ✅ |
| Data | - | Ninguno ✅ |
| Utils | - | Ninguno ✅ |

### Cohesión

| Módulo | Cohesión | Evaluación |
|--------|----------|------------|
| BaseForm | Alta | ✅ Excelente |
| Forms | Alta | ✅ Excelente |
| Widgets | Alta | ✅ Excelente |
| Services | Alta | ✅ Excelente |
| Models | Media | ⚠️ Mejorar separación |

## 🔧 Principios SOLID

### Single Responsibility Principle ✅

Cada clase tiene una responsabilidad clara:
- `ProfesorForm`: CRUD de profesores
- `VistaCalendario`: Visualización de calendario
- `AsignadorGuardias`: Algoritmo de asignación

### Open/Closed Principle ✅

`BaseForm` extensible sin modificación:
```python
class NuevoWidget(BaseForm):  # Extensión
    def setup_ui(self):       # Sin modificar BaseForm
        pass
```

### Liskov Substitution Principle ✅

Todos los widgets pueden sustituir a `BaseForm`:
```python
def agregar_tab(widget: BaseForm):
    tabs.addTab(widget, "Título")

# Funciona con cualquier widget
agregar_tab(VistaCalendario(session))
agregar_tab(PanelEstadisticas(session))
```

### Interface Segregation Principle ⚠️

**Mejora pendiente**: Algunos widgets no usan todos los métodos de `BaseForm`

### Dependency Inversion Principle ✅

Dependencias apuntan a abstracciones (session interface), no implementaciones concretas.

## 🚀 Ventajas de la Arquitectura Actual

### 1. Mantenibilidad ✅
- Código organizado por capas
- Responsabilidades claras
- Fácil localización de bugs

### 2. Testabilidad ✅
- Services sin dependencias de UI
- Session inyectable (mockeable)
- Separación lógica/presentación

### 3. Escalabilidad ✅
- Fácil agregar nuevos widgets/forms
- Patrón establecido y documentado
- Arquitectura soporta crecimiento

### 4. Reutilización ✅
- `BaseForm` compartido
- Services reutilizables
- Utils transversales

### 5. Consistencia ✅
- Patrón uniforme en toda la UI
- Manejo de errores centralizado
- Estilos globales (`ui_styles.py`)

## ⚠️ Áreas de Mejora

### 1. Testing (Crítico)
**Problema**: Coverage <20%

**Solución propuesta**:
- Sprint 6: Unit tests para services
- Integration tests para workflows
- UI tests con pytest-qt

### 2. Type Hints (Importante)
**Problema**: Annotations incompletas

**Solución propuesta**:
```python
def registrar_ausencia(
    session: Session,
    profesor_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    tipo: str,
    motivo: Optional[str] = None
) -> Ausencia:
    ...
```

### 3. Use Cases Pattern (Opcional)
**Problema**: Services hacen demasiadas cosas

**Solución propuesta**:
```
services/
└── use_cases/
    ├── crear_ausencia_use_case.py
    ├── asignar_guardia_use_case.py
    └── ...
```

### 4. Repository Pattern (Opcional)
**Problema**: Queries SQLAlchemy dispersas

**Solución propuesta**:
```python
class ProfesorRepository:
    def find_all_activos(self) -> List[Profesor]:
        return self.session.query(Profesor).filter_by(activo=True).all()
```

## 📈 Roadmap Arquitectónico

### Corto Plazo (Sprint 6)
1. ✅ Documentar arquitectura (este documento)
2. 🎯 Implementar testing (>80% coverage)
3. 🎯 Agregar type hints completos
4. 🎯 Eliminar `src/widgets/` legacy

### Medio Plazo (Sprints 7-8)
1. Implementar Use Cases pattern
2. Migrar a Repository pattern
3. API REST para integraciones externas
4. CLI para operaciones batch

### Largo Plazo (v3.0)
1. Microservicios (asignador independiente)
2. Frontend web (React/Vue)
3. Notificaciones en tiempo real
4. Sistema de plugins

## 🔗 Referencias

### Documentos Relacionados
- [Sprint 5: Migración de Widgets](./SPRINT_5_WIDGETS.md)
- [Changelog v2.6](./CHANGELOG_v2.6.md)
- [Guía de Desarrollo](./GUIA_DESARROLLO.md)

### Patrones de Diseño
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

### SOLID Principles
- [SOLID en Python](https://realpython.com/solid-principles-python/)

## ✅ Conclusión

La arquitectura de Guardias de Patio v2.6 representa un **excelente fundamento** para el crecimiento futuro del proyecto:

- ✅ **Limpia**: Separación clara de responsabilidades
- ✅ **Mantenible**: Código organizado y documentado
- ✅ **Escalable**: Fácil agregar funcionalidades
- ✅ **Testeable**: Diseño facilita pruebas
- ✅ **Consistente**: Patrones uniformes

**Estado arquitectónico**: 🟢 **SALUDABLE**

Con algunas mejoras menores (testing, type hints), el proyecto estará en posición óptima para:
- Soportar miles de usuarios
- Integración con otros sistemas
- Evolución continua sin deuda técnica

---

**Documento creado**: 18 de octubre de 2025  
**Versión**: 1.0  
**Próxima revisión**: Sprint 6 (testing)
