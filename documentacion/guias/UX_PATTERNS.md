# 🎨 Patrones UX - Guardias de Patio

**Fecha**: 8 de noviembre de 2025  
**Versión**: 3.0.2  
**Propósito**: Guía de patrones y convenciones UX para desarrollo futuro

---

## 📐 Filosofía UX

### Principios Fundamentales

1. **Feedback Inmediato** 🎯
   - Toda acción del usuario debe tener respuesta visual instantánea
   - Botones cambian de estado (hover, pressed, disabled)
   - Mensajes de éxito/error claros y visibles

2. **Minimalismo Funcional** ✨
   - Solo mostrar opciones relevantes en cada contexto
   - Evitar sobrecarga de información
   - Agrupar funcionalidades relacionadas

3. **Confirmaciones Inteligentes** 🤔
   - Solo confirmar acciones destructivas o irreversibles
   - No molestar innecesariamente al usuario
   - Botón seguro por defecto (NO, Cancelar)

4. **Guía Contextual** 📖
   - Tooltips informativos con contexto + ejemplo
   - Placeholders con formato esperado
   - Mensajes de error con solución sugerida

---

## 🎯 Patrones Implementados

### 1. Tooltips Informativos

#### Formato Estándar

```python
# Tooltip simple
campo.setToolTip("Descripción clara y concisa")

# Tooltip con contexto
campo.setToolTip(
    "Descripción del campo\n"
    "Información adicional o rango válido"
)

# Tooltip con emoji (opcional)
boton.setToolTip("📋 Copiar al portapapeles")
```

#### Mejores Prácticas

✅ **HACER**:
- Descripción en 1-2 líneas
- Incluir rango válido si aplica
- Usar formato: "Acción (Atajo)" para botones
- Ejemplos: "Recargar lista (F5)"

❌ **NO HACER**:
- Tooltips vacíos o genéricos ("Campo de texto")
- Instrucciones complejas (usar diálogos de ayuda)
- Texto excesivamente largo (>3 líneas)

#### Ejemplos Reales

```python
# ✅ Excelente
self.horas_input.setToolTip(
    "Horas semanales de contrato\n"
    "Rango típico: 18-25 horas"
)

# ✅ Bueno
self.refresh_btn.setToolTip("Recargar la lista de profesores (F5)")

# ⚠️ Mejorable
self.nombre_input.setToolTip("Nombre del profesor")  # Demasiado obvio

# ❌ Malo
self.campo.setToolTip("Campo")  # No aporta información
```

---

### 2. Placeholders con Ejemplos

#### Formato Estándar

```python
# Placeholder con ejemplo de formato
campo.setPlaceholderText("APELLIDOS, NOMBRE")

# Placeholder con ejemplo de valor
campo.setPlaceholderText("Ej: 25.0")

# Placeholder con instrucción
campo.setPlaceholderText("Buscar por nombre o email...")
```

#### Mejores Prácticas

✅ **HACER**:
- Mostrar ejemplo real del formato esperado
- Usar "Ej: " para valores numéricos
- Capitalización según formato esperado
- Texto en gris sutil (automático en PyQt6)

❌ **NO HACER**:
- Placeholders demasiado largos
- Instrucciones complejas (usar labels)
- Valores por defecto (usar setValue)

#### Ejemplos Reales

```python
# ✅ Excelente - Muestra formato exacto
self.nombre_completo_input.setPlaceholderText("GARCÍA LÓPEZ, JUAN")

# ✅ Bueno - Indica tipo de valor
self.email_input.setPlaceholderText("profesor@colegio.edu")
self.horas_input.setPlaceholderText("Ej: 30.0")

# ✅ Bueno - Instrucción de búsqueda
self.busqueda_input.setPlaceholderText("Buscar por nombre o email...")

# ⚠️ Mejorable - Demasiado genérico
self.campo.setPlaceholderText("Introduce un valor")
```

---

### 3. Confirmaciones Inteligentes

#### ¿Cuándo Confirmar?

| Acción | ¿Confirmar? | Motivo |
|--------|-------------|---------|
| Eliminar registro | ✅ SÍ | Destructiva e irreversible |
| Limpiar formulario | ✅ SÍ (si hay datos) | Pérdida de trabajo |
| Cerrar con cambios | ✅ SÍ | Pérdida de trabajo |
| Guardar | ❌ NO | Operación esperada |
| Cancelar sin cambios | ❌ NO | No hay pérdida |
| Refrescar datos | ❌ NO | No destructiva |
| Exportar | ❌ NO | No destructiva |

#### Implementación con BaseForm

```python
# Eliminación - SIEMPRE confirmar
def _eliminar_clicked(self):
    if not self.tiene_seleccion():
        return
    
    if self.confirmar_accion(
        "Confirmar eliminación",
        "¿Está seguro de eliminar este registro?\n"
        "Esta acción no se puede deshacer."
    ):
        self._do_delete()

# Cancelar - Solo si hay cambios
def _cancelar_clicked(self):
    if self._form_has_changes():
        if not self.confirmar_accion(
            "Cambios sin guardar",
            "Hay cambios sin guardar. ¿Descartar cambios?"
        ):
            return  # Usuario canceló
    
    self._clear_form()
```

#### Configuración de Botones

```python
# Botón por defecto: El SEGURO (NO, Cancelar)
msg_box.setDefaultButton(QMessageBox.StandardButton.No)

# Ejemplo completo
respuesta = QMessageBox.question(
    self,
    "Título",
    "Mensaje claro",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    QMessageBox.StandardButton.No  # Por defecto NO (seguro)
)
```

---

### 4. Feedback Visual

#### Estilos de Botones

La aplicación usa estilos definidos en `styles.py`:

```python
from presentation.styles import styles

# Botón primario (acción principal)
self.guardar_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)  # Azul

# Botón de advertencia (acción que requiere atención)
self.limpiar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)  # Naranja

# Botón de éxito (confirmación)
self.confirmar_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)  # Verde

# Botón de peligro (eliminación)
self.eliminar_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)  # Rojo
```

#### Colores por Estado

| Estado | Color | Uso |
|--------|-------|-----|
| Success | Verde (#28a745) | Operación exitosa |
| Error | Rojo (#dc3545) | Error o eliminación |
| Warning | Naranja (#ffc107) | Advertencia o atención |
| Info | Azul (#007bff) | Información o primario |
| Disabled | Gris (#6c757d) | Deshabilitado |

#### Mensajes de Feedback

```python
# Éxito
self.mostrar_exito("Profesor guardado correctamente")

# Error
self.mostrar_error("Error al guardar", "Verifique los datos ingresados")

# Advertencia
self.mostrar_advertencia("Campo obligatorio", "El nombre no puede estar vacío")

# Información
self.mostrar_info("Datos cargados", "Se cargaron 50 profesores")
```

---

### 5. Navegación y Atajos

#### Atajos Estándar

| Atajo | Acción | Contexto |
|-------|--------|----------|
| **F5** | Refrescar | Todas las listas |
| **Ctrl+S** | Guardar | Formularios de edición |
| **Ctrl+N** | Nuevo | Formularios CRUD |
| **Ctrl+F** | Buscar | Listas con búsqueda |
| **Enter** | Confirmar/Guardar | Formularios |
| **Esc** | Cancelar/Cerrar | Diálogos |
| **Del** | Eliminar | Listas con selección |
| **Ctrl+Q** | Salir | Ventana principal |

#### Implementación

```python
# En __init__ del formulario
self.setup_shortcuts()

def setup_shortcuts(self):
    """Configurar atajos de teclado."""
    # F5 - Refrescar
    QShortcut(QKeySequence("F5"), self, self._refrescar_clicked)
    
    # Ctrl+S - Guardar
    QShortcut(QKeySequence.StandardKey.Save, self, self._guardar_clicked)
    
    # Ctrl+N - Nuevo
    QShortcut(QKeySequence.StandardKey.New, self, self._nuevo_clicked)
    
    # Del - Eliminar
    QShortcut(QKeySequence.StandardKey.Delete, self, self._eliminar_clicked)
```

#### Documentar Atajos

```python
# Siempre documentar atajos en tooltips
self.guardar_btn.setToolTip("Guardar cambios (Ctrl+S)")
self.refresh_btn.setToolTip("Recargar lista (F5)")
```

---

### 6. Validación de Formularios

#### Validación en Tiempo Real

```python
# Validar al perder foco
self.nombre_input.editingFinished.connect(self._validar_nombre)

def _validar_nombre(self):
    """Validar formato de nombre."""
    texto = self.nombre_input.text().strip()
    
    if not texto:
        self.nombre_input.setStyleSheet("border: 2px solid red;")
        self.status_label.setText("⚠️ El nombre es obligatorio")
        return False
    
    if "," not in texto:
        self.nombre_input.setStyleSheet("border: 2px solid orange;")
        self.status_label.setText("⚠️ Formato: APELLIDOS, NOMBRE")
        return False
    
    # Válido
    self.nombre_input.setStyleSheet("")
    self.status_label.setText("")
    return True
```

#### Validación Pre-Guardado

```python
def _guardar_clicked(self):
    """Guardar con validación completa."""
    # 1. Validar todos los campos
    if not self._validar_formulario():
        self.mostrar_error(
            "Datos incompletos",
            "Por favor, complete todos los campos obligatorios"
        )
        return
    
    # 2. Confirmar si es necesario
    # 3. Guardar
    # 4. Feedback
```

---

### 7. Tablas Interactivas

#### Patrón Estándar

```python
# Configuración de tabla
self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

# Señales
self.table.itemSelectionChanged.connect(self._on_selection_changed)
self.table.itemDoubleClicked.connect(self._editar_clicked)

# Ordenamiento
self.table.setSortingEnabled(True)
self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
```

#### Interacciones

| Acción | Comportamiento |
|--------|----------------|
| Click | Seleccionar fila |
| Doble-click | Editar registro |
| Del | Eliminar registro (con confirmación) |
| Enter | Editar registro |
| Click en header | Ordenar columna |

---

### 8. Progress Indicators

#### Para Operaciones Largas

```python
from presentation.widgets.progress_indicators import ProgressIndicator

# Crear indicador
self.progress = ProgressIndicator(self)

# Iniciar operación
self.progress.start()
self.setEnabled(False)  # Deshabilitar formulario

# Ejecutar en background
worker = Worker(self._generar_guardias_heavy)
worker.signals.finished.connect(self._on_finished)
worker.signals.error.connect(self._on_error)
thread_pool.start(worker)

# Terminar
def _on_finished(self):
    self.progress.stop()
    self.setEnabled(True)
    self.mostrar_exito("Operación completada")
```

---

## 📋 Checklist para Nuevos Formularios

Al crear un nuevo formulario, verificar:

### Campos de Entrada
- [ ] Todos los campos tienen `placeholder` o `label` claro
- [ ] Campos complejos tienen `tooltip` explicativo
- [ ] Campos obligatorios están marcados (ej: asterisco)
- [ ] Validación en tiempo real implementada
- [ ] Mensajes de error claros y útiles

### Botones
- [ ] Botones con íconos (opcional pero recomendado)
- [ ] Tooltips con descripción + atajo (si aplica)
- [ ] Estilos apropiados (PRIMARY, WARNING, etc.)
- [ ] Estados deshabilitados manejados correctamente

### Navegación
- [ ] Atajos de teclado implementados (F5, Ctrl+S, etc.)
- [ ] Atajos documentados en tooltips
- [ ] Tab order lógico configurado
- [ ] Enter/Esc funcionan apropiadamente

### Feedback
- [ ] Confirmaciones solo para acciones destructivas
- [ ] Mensajes de éxito/error claros
- [ ] Progress indicators para operaciones largas (>2 segundos)
- [ ] Status bar con hints contextuales (opcional)

### Accesibilidad
- [ ] Focus visible en campos activos
- [ ] Contraste de colores adecuado
- [ ] Tamaños de fuente legibles
- [ ] Textos claros y concisos

---

## 🚫 Anti-Patrones (Evitar)

### ❌ Confirmaciones Excesivas

```python
# ❌ MALO - Confirmar refrescar
def _refrescar_clicked(self):
    if self.confirmar_accion("¿Refrescar lista?"):
        self._load_data()

# ✅ BUENO - Refrescar directamente
def _refrescar_clicked(self):
    self._load_data()
    self.mostrar_info("Lista actualizada")
```

### ❌ Tooltips Inútiles

```python
# ❌ MALO
self.nombre_input.setToolTip("Nombre")  # Obvio

# ✅ BUENO
self.nombre_input.setToolTip("Formato: APELLIDOS, NOMBRE (mayúsculas)")
```

### ❌ Botones Redundantes

```python
# ❌ MALO - Demasiados botones para lo mismo
self.aplicar_fila_btn = QPushButton("Aplicar a fila")
self.aplicar_columna_btn = QPushButton("Aplicar a columna")
self.aplicar_dia_btn = QPushButton("Aplicar a día")
self.aplicar_recreo_btn = QPushButton("Aplicar a recreo")
self.aplicar_todos_btn = QPushButton("Aplicar a todos")

# ✅ BUENO - Simplificar
self.aplicar_todos_btn = QPushButton("Aplicar a todos")
self.limpiar_btn = QPushButton("Restaurar defecto")
```

### ❌ Mensajes de Error Vagos

```python
# ❌ MALO
self.mostrar_error("Error")

# ✅ BUENO
self.mostrar_error(
    "Error al guardar",
    "El email ya existe en la base de datos. Use otro email."
)
```

---

## 🎨 Plantilla de Formulario

```python
from PyQt6.QtWidgets import QWidget, QPushButton, QLineEdit
from PyQt6.QtGui import QShortcut, QKeySequence
from presentation.styles import styles
from presentation.forms.base_form import BaseForm

class MiFormulario(BaseForm):
    """Formulario para [descripción]."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shortcuts()
        self.load_data()
    
    def setup_ui(self):
        """Configurar interfaz."""
        # Campos con placeholder y tooltip
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("APELLIDOS, NOMBRE")
        self.nombre_input.setToolTip("Formato: APELLIDOS, NOMBRE (mayúsculas)")
        
        # Botones con estilo y tooltip
        self.guardar_btn = QPushButton("Guardar")
        self.guardar_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.guardar_btn.setToolTip("Guardar cambios (Ctrl+S)")
        self.guardar_btn.clicked.connect(self._guardar_clicked)
        
        # Layout...
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado."""
        QShortcut(QKeySequence.StandardKey.Save, self, self._guardar_clicked)
        QShortcut(QKeySequence("F5"), self, self._refrescar_clicked)
    
    def _guardar_clicked(self):
        """Guardar con validación."""
        if not self._validar_formulario():
            self.mostrar_error(
                "Datos incompletos",
                "Complete todos los campos obligatorios"
            )
            return
        
        try:
            # Guardar...
            self.mostrar_exito("Guardado correctamente")
        except Exception as e:
            self.mostrar_error("Error al guardar", str(e))
    
    def _eliminar_clicked(self):
        """Eliminar con confirmación."""
        if self.confirmar_accion(
            "Confirmar eliminación",
            "¿Está seguro de eliminar este registro?"
        ):
            # Eliminar...
            self.mostrar_exito("Eliminado correctamente")
```

---

## 📚 Referencias

- **BaseForm**: `src/presentation/forms/base_form.py` - Clase base con métodos de utilidad
- **Styles**: `src/presentation/styles/styles.py` - Constantes de estilos
- **Progress Indicators**: `src/presentation/widgets/progress_indicators.py` - Indicadores de progreso
- **Auditoría UX**: `documentacion/UX_AUDIT.md` - Estado actual de UX
- **Atajos**: `documentacion/guias/KEYBOARD_SHORTCUTS.md` - Lista completa de atajos

---

**Última actualización**: 8 de noviembre de 2025  
**Versión**: 3.0.2  
**Mantenedor**: Equipo de Desarrollo
