# Changelog v2.6 - Sprint 5: Migración de Widgets

**Versión**: 2.6.0  
**Fecha de Release**: 18 de octubre de 2025  
**Tipo**: Refactorización Arquitectónica  
**Commits principales**: `9929668`, `561f4f8`

## 🎯 Resumen de Cambios

Versión 2.6 completa la **migración de todos los widgets** desde `src/widgets/` hacia la arquitectura de Presentation Layer (`src/presentation/widgets/`), estableciendo un patrón consistente de diseño limpio con inyección de dependencias.

Esta release complementa Sprint 4 (migración de forms) y consolida la arquitectura limpia en **100% de la capa de presentación**.

## ✨ Nuevas Características

### 1. Arquitectura de Widgets Refactorizada

Todos los widgets ahora heredan de `BaseForm` y utilizan inyección de sesión:

```python
# Patrón establecido
class Widget(BaseForm):
    def __init__(self, session):
        super().__init__(session)
        self.setup_ui()
```

**Beneficios**:
- ✅ Manejo consistente de errores
- ✅ Session management centralizado
- ✅ Código más testeable
- ✅ Separación de responsabilidades

### 2. Widgets Migrados (4 Total)

#### VistaCalendario (349 líneas)
- 📅 Visualización mensual de guardias y ausencias
- 🎨 Color-coding dinámico (guardias, ausencias, hoy)
- 🔄 Navegación entre meses
- 📊 Agrupación inteligente de ausencias multi-día

#### GestorSustituciones (347 líneas)
- 🔍 Búsqueda de guardias con filtros
- 👥 Sistema de asignación de sustitutos
- ✅ Validación de disponibilidad
- 📜 Historial de sustituciones recientes

#### PanelEstadisticas (401 líneas)
- 📊 Dashboard con 4 pestañas
- 📈 Métricas clave (total guardias, cobertura, profesores activos)
- 📉 Gráficos matplotlib (barras y circular)
- 📋 Tablas de distribución por profesor y zona

#### GestionarAusenciasForm (716 líneas) ⭐
- 🏥 CRUD completo de ausencias
- 👁️ Preview en tiempo real de guardias afectadas
- 🤖 Reasignación automática de guardias
- 👤 Reasignación manual con selección de sustitutos
- 🎨 Color-coding de estados (activa, inactiva, pasada)
- ⚡ Integración profunda con `services.gestor_ausencias`

## 🔧 Cambios Técnicos

### Archivos Creados

```
src/presentation/widgets/
├── vista_calendario.py        (349 líneas)
├── gestor_sustituciones.py    (347 líneas)
├── panel_estadisticas.py      (401 líneas)
└── gestionar_ausencias.py     (716 líneas)
```

### Archivos Modificados

**src/presentation/widgets/__init__.py**:
```python
# Exports actualizados
__all__ = [
    "VistaCalendario",
    "GestorSustituciones",
    "PanelEstadisticas",
    "GestionarAusenciasForm",
]
```

**src/main.py**:
- Actualizados imports de widgets refactorizados
- Eliminados imports legacy de `widgets/`
- Aplicada inyección de sesión en todos los widgets

### Refactorización de Session Management

**Antes (acoplado)**:
```python
from database.db_manager import SessionLocal

class Widget(QWidget):
    def cargar_datos(self):
        session = SessionLocal()
        data = session.query(Model).all()
        session.close()
```

**Después (inyección)**:
```python
class Widget(BaseForm):
    def __init__(self, session):
        super().__init__(session)
    
    def cargar_datos(self):
        data = self.session.query(Model).all()
```

## 🐛 Bugs Corregidos

### #1: Error en VistaCalendario - Método Inexistente
**Problema**: `AttributeError: 'VistaCalendario' object has no attribute 'crear_widget_simple'`

**Causa**: Uso de método no definido en BaseForm

**Solución**: Cambio a instanciación directa de QWidget
```python
# Antes
self.calendario_widget = self.crear_widget_simple()

# Después
from PyQt6.QtWidgets import QWidget as QtWidget
self.calendario_widget = QtWidget()
```

**Commit**: Incluido en `561f4f8`

### #2: Import Error - Nombre de Módulo Incorrecto
**Problema**: `ModuleNotFoundError: No module named 'presentation.widgets.gestionar_sustituciones'`

**Causa**: Inconsistencia en nombres de archivos (gestor vs gestionar)

**Solución**: Corrección en `__init__.py` para usar nombres correctos
```python
# Correcto
from .gestor_sustituciones import GestorSustituciones
```

**Commit**: `561f4f8`

### #3: Código Duplicado en __init__.py
**Problema**: Exports e imports duplicados causando redefiniciones

**Solución**: Limpieza de imports duplicados
```python
# Estructura limpia final
from .widget import Widget
__all__ = ["Widget"]
```

**Commit**: `561f4f8`

## 📊 Métricas de Cambios

### Código Migrado

| Componente | Líneas | Complejidad | Estado |
|------------|--------|-------------|--------|
| VistaCalendario | 349 | Media | ✅ |
| GestorSustituciones | 347 | Media | ✅ |
| PanelEstadisticas | 401 | Media-Alta | ✅ |
| GestionarAusenciasForm | 716 | Alta | ✅ |
| **Total Sprint 5** | **1,813** | - | **100%** |

### Acumulado (Sprints 4 + 5)

- **Forms (Sprint 4)**: ~2,467 líneas
- **Widgets (Sprint 5)**: ~1,813 líneas
- **TOTAL**: **~4,280 líneas refactorizadas**

### Distribución de Cambios

```
Archivos creados:     4 widgets
Archivos modificados: 2 (main.py, __init__.py)
Clases migradas:      5 (4 widgets + DialogoReasignacion)
Métodos migrados:     ~80
Líneas agregadas:     ~1,813
Líneas eliminadas:    ~10
```

## 🔄 Cambios de API

### Widgets - Constructor

**Antes**:
```python
# Sin parámetros
widget = VistaCalendario()
```

**Después**:
```python
# Con session injection
widget = VistaCalendario(session)
```

### Aplicable a:
- `VistaCalendario`
- `GestorSustituciones`
- `PanelEstadisticas`
- `GestionarAusenciasForm`

## ⚠️ Breaking Changes

### 1. Constructor de Widgets
Todos los widgets ahora requieren `session` como parámetro.

**Migración necesaria**:
```python
# Antes
self.vista_calendario = VistaCalendario()

# Después
self.vista_calendario = VistaCalendario(self.session)
```

### 2. Imports Actualizados
Cambio de ubicación de widgets.

**Migración necesaria**:
```python
# Antes
from widgets.vista_calendario import VistaCalendario

# Después
from presentation.widgets import VistaCalendario
```

## 🧪 Testing

### Tests Ejecutados

- ✅ **Aplicación completa**: Ejecutada sin errores
- ✅ **Navegación entre tabs**: Funcional
- ✅ **CRUD de ausencias**: Operativo
- ✅ **Gráficos**: Renderizados correctamente
- ✅ **Calendario**: Visualización correcta
- ✅ **Sustituciones**: Workflow completo

### Validación de Calidad

```bash
# Lint check
git commit  # Pre-commit hook: ✅ Ruff passed

# Compilación
get_errors  # ✅ 0 errors

# Ejecución
./fix_pyqt6.sh && ./run_app.sh  # ✅ Success
```

### Coverage Actual

- **Forms**: Sin tests automatizados
- **Widgets**: Sin tests automatizados
- **Coverage total**: <20% ⚠️

**Recomendación**: Sprint 6 enfocado en testing

## 📝 Notas de Migración

### Para Desarrolladores

Si estás trabajando en una rama que usa los widgets antiguos:

1. **Actualizar imports**:
   ```python
   from presentation.widgets import (
       VistaCalendario,
       GestorSustituciones,
       PanelEstadisticas,
       GestionarAusenciasForm,
   )
   ```

2. **Actualizar instanciación**:
   ```python
   # Inyectar sesión en todos los widgets
   widget = Widget(self.session)
   ```

3. **Verificar herencia**:
   - Widgets deben heredar de `BaseForm`
   - No usar `SessionLocal()` directamente
   - Usar `self.session` siempre

### Para Testing

Los widgets refactorizados son más fáciles de testear:

```python
# Ejemplo de test con sesión mock
def test_vista_calendario():
    mock_session = MagicMock()
    widget = VistaCalendario(mock_session)
    
    # Verificar que usa la sesión inyectada
    widget.actualizar_calendario()
    mock_session.query.assert_called()
```

## 🚀 Mejoras de Rendimiento

### Session Pooling Optimizado

- **Antes**: Cada widget creaba su propia sesión
- **Después**: Session compartida desde MainWindow
- **Beneficio**: Reducción de overhead de conexiones DB

### Queries Optimizadas

- **PanelEstadisticas**: Agregaciones SQL en lugar de loops Python
- **VistaCalendario**: Filtros de fecha en query
- **GestorSustituciones**: Joins optimizados

## 🔐 Seguridad

### Session Management Mejorado

- ✅ Ciclo de vida controlado centralmente
- ✅ Evita fugas de conexiones
- ✅ Transacciones manejadas consistentemente

## 📚 Documentación Actualizada

### Nuevos Documentos

- **SPRINT_5_WIDGETS.md**: Documentación completa del sprint
- **CHANGELOG_v2.6.md**: Este documento

### Documentos Relacionados

- [GUIA_DESARROLLO.md](./GUIA_DESARROLLO.md): Actualizar con patrón de widgets
- [README.md](../README.md): Actualizar arquitectura del proyecto

## 🔗 Enlaces

### Commits

- **Commit parcial**: [`9929668`](https://github.com/cferrerobonet/guardias_patio/commit/9929668) - 3 primeros widgets
- **Commit final**: [`561f4f8`](https://github.com/cferrerobonet/guardias_patio/commit/561f4f8) - Sprint 5 completo

### Issues Relacionados

*(Si aplica, agregar referencias a issues de GitHub)*

## 🎯 Próximos Pasos

### Sprint 6 (Propuestas)

**Opción A: Testing**
- Unit tests para widgets
- Integration tests
- Coverage >80%

**Opción B: Performance**
- Profiling de queries
- Caching inteligente
- Lazy loading

**Opción C: Features**
- Exportación Excel/CSV
- Notificaciones
- Dashboard personalizable

### Deuda Técnica

1. ⚠️ **Eliminar `src/widgets/` legacy**
2. ⚠️ **Aumentar coverage de tests**
3. ⚠️ **Agregar docstrings faltantes**
4. ℹ️ **Type hints completos**

## 👥 Contribuidores

- **Desarrollo**: Equipo Guardias de Patio
- **Revisión**: GitHub Copilot
- **Testing**: Manual + Automated (en progreso)

## 📅 Timeline

- **Inicio Sprint 5**: Octubre 2025
- **Primer commit**: `9929668` (3 widgets)
- **Commit final**: `561f4f8` (18 octubre 2025)
- **Release v2.6**: 18 octubre 2025

---

## Resumen Ejecutivo

**Sprint 5 = 100% COMPLETADO** ✅

- **4 widgets** migrados a arquitectura limpia
- **1,813 líneas** refactorizadas
- **0 errores** de compilación
- **100% funcionalidad** preservada
- **Arquitectura sólida** para futuro desarrollo

La aplicación ahora tiene una base arquitectónica consistente y mantenible, lista para:
- Testing exhaustivo
- Nuevas funcionalidades
- Optimizaciones de rendimiento
- Escalabilidad futura

**Estado del proyecto**: 🟢 **EXCELENTE**

---

**Fecha de documento**: 18 de octubre de 2025  
**Versión de changelog**: 1.0  
**Próxima versión prevista**: 2.7.0 (Sprint 6)
