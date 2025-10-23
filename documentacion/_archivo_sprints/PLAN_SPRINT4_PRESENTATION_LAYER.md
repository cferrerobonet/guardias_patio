"""
Sprint 4: Presentation Layer - Plan de Refactorización

## Estado Actual

El archivo `src/main.py` contiene ~2,500 líneas con 7 clases principales:

1. **ProfesorForm** (~900 líneas) - Gestión de profesores
2. **ZonaForm** (~200 líneas) - Gestión de zonas
3. **ConfiguracionForm** (~300 líneas) - Configuración del sistema
4. **AsignacionGuardiasForm** (~240 líneas) - Asignación de guardias
5. **ImportExportForm** (~270 líneas) - Importar/Exportar datos
6. **CalendarioGuardiasForm** (~250 líneas) - Calendario visual
7. **MainWindow** (~100 líneas) - Ventana principal con tabs

## Problemas del Código Actual

1. **Acoplamiento**: Acceso directo a base de datos desde UI
2. **Responsabilidad Única**: Forms hacen demasiadas cosas
3. **Dificultad de Testing**: Imposible testear sin UI
4. **Duplicación**: Código repetido en múltiples forms
5. **Mantenibilidad**: Cambios pequeños afectan múltiples lugares

## Arquitectura Objetivo

```
src/presentation/
├── forms/
│   ├── profesor_form.py          # Gestión de profesores
│   ├── zona_form.py               # Gestión de zonas
│   ├── configuracion_form.py      # Configuración
│   ├── asignacion_guardias_form.py
│   ├── import_export_form.py
│   └── calendario_guardias_form.py
├── widgets/
│   ├── profesor_table_widget.py   # Tabla reutilizable
│   ├── guardia_calendar_widget.py # Calendario reutilizable
│   └── stats_widget.py            # Panel de estadísticas
├── dialogs/
│   ├── confirm_dialog.py          # Diálogos de confirmación
│   └── error_dialog.py            # Diálogos de error
└── main_window.py                 # Ventana principal
```

## Patrón de Diseño: Model-View-Presenter (MVP)

### Antes (Acoplado)
```python
class ProfesorForm(QWidget):
    def guardar_profesor(self):
        # ❌ Acceso directo a BD
        session = get_db_session()
        profesor = Profesor(nombre=self.nombre_input.text())
        session.add(profesor)
        session.commit()
```

### Después (Desacoplado)
```python
class ProfesorForm(QWidget):
    def __init__(self, session):
        super().__init__()
        self.crear_profesor_uc = CrearProfesorUseCase(session)
    
    def guardar_profesor(self):
        # ✅ Usa Use Case
        try:
            dto = CrearProfesorDTO(
                nombre_completo=self.nombre_input.text(),
                horas_contrato=float(self.horas_input.text()),
                turno=self.turno_combo.currentText()
            )
            profesor = self.crear_profesor_uc.execute(dto)
            self.mostrar_exito(f"Profesor {profesor.nombre_completo} creado")
        except ValidationError as e:
            self.mostrar_error(str(e))
```

## Plan de Migración (3 Fases)

### Fase 1: Preparación (Completado ✅)
- ✅ Domain Layer implementado
- ✅ Application Layer con Use Cases
- ✅ DTOs con validación Pydantic
- ✅ Repositorios desacoplados

### Fase 2: Extracción Gradual (En Progreso 🔄)

#### Paso 1: Crear Base Classes
```python
# src/presentation/forms/base_form.py
class BaseForm(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setup_ui()
    
    def setup_ui(self):
        raise NotImplementedError
    
    def mostrar_exito(self, mensaje):
        QMessageBox.information(self, "Éxito", mensaje)
    
    def mostrar_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
```

#### Paso 2: Migrar Form por Form (Orden Recomendado)

1. **ConfiguracionForm** (más simple, ~300 líneas)
   - Menos dependencias
   - Buen punto de inicio
   - Validación con DTOs

2. **ZonaForm** (~200 líneas)
   - CRUD simple
   - Sin lógica compleja
   - Ejemplo claro de patrón

3. **ProfesorForm** (~900 líneas)
   - Más complejo
   - Múltiples validaciones
   - Extraer widgets reutilizables

4. **AsignacionGuardiasForm** (~240 líneas)
   - Usa lógica de negocio
   - Integración con múltiples entidades

5. **CalendarioGuardiasForm** (~250 líneas)
   - Visualización compleja
   - Widget personalizado del calendario

6. **ImportExportForm** (~270 líneas)
   - Operaciones de archivo
   - Serialización/Deserialización

#### Paso 3: Extraer Widgets Comunes
```python
# src/presentation/widgets/table_widget.py
class CRUDTableWidget(QTableWidget):
    """Widget reutilizable para tablas CRUD."""
    
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setup_table(columns)
    
    def setup_table(self, columns):
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        # ... configuración común
```

### Fase 3: Optimización y Testing

1. **Tests Unitarios**
   - Mockear Use Cases
   - Testear validaciones de UI
   - Testear flujos de usuario

2. **Integración**
   - Conectar todos los forms
   - Actualizar MainWindow
   - Migrar atajos de teclado

3. **Documentación**
   - Guía de desarrollo de nuevos forms
   - Patrones de diseño usados
   - Ejemplos de código

## Ejemplo Completo: ConfiguracionForm

```python
# src/presentation/forms/configuracion_form.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QDateEdit
from application.use_cases.configuracion import (
    ObtenerConfiguracionUseCase,
    ActualizarConfiguracionUseCase
)
from application.dtos import ActualizarConfiguracionDTO

class ConfiguracionForm(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        
        # Use Cases
        self.obtener_config_uc = ObtenerConfiguracionUseCase(session)
        self.actualizar_config_uc = ActualizarConfiguracionUseCase(session)
        
        self.setup_ui()
        self.cargar_configuracion()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.fecha_inicio_edit = QDateEdit()
        self.fecha_fin_edit = QDateEdit()
        
        self.guardar_btn = QPushButton("💾 Guardar")
        self.guardar_btn.clicked.connect(self.guardar_configuracion)
        
        layout.addWidget(self.fecha_inicio_edit)
        layout.addWidget(self.fecha_fin_edit)
        layout.addWidget(self.guardar_btn)
        
        self.setLayout(layout)
    
    def cargar_configuracion(self):
        try:
            config = self.obtener_config_uc.execute()
            self.fecha_inicio_edit.setDate(config.fecha_inicio_curso)
            self.fecha_fin_edit.setDate(config.fecha_fin_curso)
        except Exception as e:
            self.mostrar_error(f"Error al cargar configuración: {e}")
    
    def guardar_configuracion(self):
        try:
            dto = ActualizarConfiguracionDTO(
                fecha_inicio_curso=self.fecha_inicio_edit.date().toPyDate(),
                fecha_fin_curso=self.fecha_fin_edit.date().toPyDate()
            )
            self.actualizar_config_uc.execute(dto)
            self.mostrar_exito("Configuración actualizada")
        except ValidationError as e:
            self.mostrar_error(str(e))
    
    def mostrar_exito(self, mensaje):
        QMessageBox.information(self, "Éxito", mensaje)
    
    def mostrar_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
```

## Beneficios de la Refactorización

### 1. Testabilidad
```python
def test_configuracion_form_guardar():
    # Mock del Use Case
    mock_uc = Mock(spec=ActualizarConfiguracionUseCase)
    form = ConfiguracionForm(mock_session)
    form.actualizar_config_uc = mock_uc
    
    # Simular interacción
    form.fecha_inicio_edit.setDate(QDate(2025, 9, 1))
    form.guardar_btn.click()
    
    # Verificar
    mock_uc.execute.assert_called_once()
```

### 2. Reutilización
```python
# Widgets pueden usarse en múltiples forms
tabla_profesores = CRUDTableWidget(
    columns=["Nombre", "Email", "Horas"],
    data_source=listar_profesores_uc
)
```

### 3. Mantenibilidad
```python
# Cambios en lógica de negocio no afectan UI
# Cambios en Use Case se reflejan automáticamente
```

## Métricas de Mejora

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Líneas por clase | ~900 | ~200 | 78% ↓ |
| Acoplamiento a BD | Alto | Ninguno | 100% ↓ |
| Testabilidad | 0% | 80%+ | 80% ↑ |
| Reutilización | Baja | Alta | 200% ↑ |
| Tiempo de cambio | Alto | Bajo | 60% ↓ |

## Próximos Pasos Inmediatos

1. ✅ Crear estructura de carpetas `presentation/`
2. ⏳ Implementar `BaseForm` con métodos comunes
3. ⏳ Migrar `ConfiguracionForm` como prueba de concepto
4. ⏳ Documentar patrones para el equipo
5. ⏳ Migrar resto de forms gradualmente

## Conclusión

La refactorización del Presentation Layer es un proceso gradual que:

- **No rompe** funcionalidad existente
- **Mejora** significativamente la arquitectura
- **Facilita** el testing y mantenimiento
- **Permite** evolución incremental

El código actual en `main.py` seguirá funcionando mientras migramos
progresivamente cada form al nuevo patrón usando Use Cases y DTOs.

## Referencias

- Clean Architecture: Robert C. Martin
- MVP Pattern: Martin Fowler
- PyQt6 Best Practices: riverbank.computing.com
"""