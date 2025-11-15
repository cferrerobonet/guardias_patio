# Patrón de Widgets - Guardias de Patio

**Versión**: 1.0  
**Fecha**: 1 de noviembre de 2025  
**Aplicable a**: PyQt6, Guardias de Patio v3.0+

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Filosofía del Patrón](#filosofía-del-patrón)
3. [Estructura del Widget](#estructura-del-widget)
4. [Ejemplo Completo](#ejemplo-completo)
5. [API Estándar](#api-estándar)
6. [Integración con Formularios](#integración-con-formularios)
7. [Mejores Prácticas](#mejores-prácticas)
8. [Anti-patrones](#anti-patrones)
9. [Casos de Uso](#casos-de-uso)
10. [Checklist de Implementación](#checklist-de-implementación)

---

## 📖 Introducción

Este documento define el **patrón de widgets** establecido en la versión 3.0 del proyecto Guardias de Patio. El patrón ha sido aplicado exitosamente en 4 formularios, resultando en:

- ✅ **12 widgets** reutilizables creados
- ✅ **-2,757 líneas** de código reducidas
- ✅ **-40.3%** reducción promedio en formularios
- ✅ **100% compatibilidad** retroactiva

### Objetivo

Crear widgets **autocontenidos**, **reutilizables** y **testables** que encapsulen:
- Una responsabilidad única y clara
- Su propia interfaz visual
- Su lógica de validación
- Su gestión de estado

---

## 🎯 Filosofía del Patrón

### Principios Fundamentales

1. **Single Responsibility Principle (SRP)**
   - Cada widget tiene UNA responsabilidad
   - Ejemplo: `DatosBasicosWidget` solo gestiona nombre y email

2. **Encapsulación**
   - Estado interno privado (`_` prefix)
   - API pública clara y documentada
   - Señales para comunicación externa

3. **Autocontenimiento**
   - Hereda de `QGroupBox` para tener título y borde visual
   - No depende del formulario padre para su funcionamiento
   - Puede usarse standalone para testing

4. **Reutilización**
   - Diseñado para usarse en múltiples contextos
   - Sin acoplamientos a formularios específicos
   - Configurable mediante parámetros de inicialización

5. **Testabilidad**
   - API pública facilita tests unitarios
   - Estado observable mediante señales
   - Validación independiente del UI

---

## 🏗️ Estructura del Widget

### Anatomía de un Widget

```python
"""
Módulo: nombre_widget.py
Ubicación: src/presentation/forms/<dominio>_widgets/
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit
from typing import Tuple

class NombreWidget(QGroupBox):
    """Descripción breve del widget (una línea).
    
    Descripción extendida explicando:
    - Qué gestiona este widget
    - Cuándo usarlo
    - Ejemplo de uso si es complejo
    
    Señales:
        datos_changed: Emitida cuando cambian los datos del widget.
        error_validacion: Emitida cuando hay un error de validación.
    
    Ejemplo:
        >>> widget = NombreWidget()
        >>> widget.set_datos({"campo": "valor"})
        >>> if widget.validar()[0]:
        ...     datos = widget.get_datos()
    """
    
    # ========== SEÑALES ==========
    datos_changed = pyqtSignal()
    error_validacion = pyqtSignal(str)  # mensaje de error
    
    # ========== INICIALIZACIÓN ==========
    
    def __init__(self, parent=None, config: dict = None):
        """Inicializa el widget.
        
        Args:
            parent: Widget padre (opcional).
            config: Configuración adicional (opcional).
        """
        super().__init__("Título del Widget", parent)
        self._config = config or {}
        self._setup_ui()
        self._conectar_senales()
    
    # ========== MÉTODOS PRIVADOS (Setup) ==========
    
    def _setup_ui(self):
        """Crea y configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Crear componentes
        self.label_campo = QLabel("Campo:")
        self.input_campo = QLineEdit()
        
        # Añadir al layout
        layout.addWidget(self.label_campo)
        layout.addWidget(self.input_campo)
        
        self.setLayout(layout)
    
    def _conectar_senales(self):
        """Conecta las señales internas del widget."""
        self.input_campo.textChanged.connect(self._on_campo_changed)
    
    # ========== MÉTODOS PRIVADOS (Handlers) ==========
    
    def _on_campo_changed(self):
        """Handler cuando cambia el campo."""
        self.datos_changed.emit()
    
    # ========== API PÚBLICA ==========
    
    def get_datos(self) -> dict:
        """Obtiene los datos actuales del widget.
        
        Returns:
            Diccionario con los datos del widget.
            
        Ejemplo:
            >>> datos = widget.get_datos()
            >>> print(datos["campo"])
            "valor"
        """
        return {
            "campo": self.input_campo.text().strip()
        }
    
    def set_datos(self, datos: dict):
        """Establece los datos del widget.
        
        Args:
            datos: Diccionario con los datos a establecer.
                  Claves esperadas: "campo"
                  
        Ejemplo:
            >>> widget.set_datos({"campo": "nuevo valor"})
        """
        if "campo" in datos:
            self.input_campo.setText(datos["campo"])
    
    def validar(self) -> Tuple[bool, str]:
        """Valida los datos del widget.
        
        Returns:
            Tupla (es_válido, mensaje_error).
            Si es_válido=True, mensaje_error será cadena vacía.
            
        Ejemplo:
            >>> es_valido, error = widget.validar()
            >>> if not es_valido:
            ...     print(f"Error: {error}")
        """
        campo = self.input_campo.text().strip()
        
        if not campo:
            return False, "El campo es obligatorio"
        
        if len(campo) < 3:
            return False, "El campo debe tener al menos 3 caracteres"
        
        return True, ""
    
    def limpiar(self):
        """Limpia todos los campos del widget.
        
        Restaura el widget a su estado inicial.
        """
        self.input_campo.clear()
```

### Secciones Obligatorias

Todo widget DEBE tener estas secciones en este orden:

1. **Docstring del módulo**
2. **Imports**
3. **Docstring de la clase**
4. **Señales** (`pyqtSignal`)
5. **`__init__`**
6. **Métodos privados de setup** (`_setup_ui`, `_conectar_senales`)
7. **Métodos privados handlers** (`_on_*`)
8. **API pública** (`get_datos`, `set_datos`, `validar`, `limpiar`)

---

## 💡 Ejemplo Completo

### Ejemplo Real: DatosBasicosWidget

Este es un ejemplo real del proyecto (simplificado):

```python
"""Widget para gestionar datos básicos de un profesor.

Ubicación: src/presentation/forms/profesor_widgets/datos_basicos_widget.py
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QCheckBox
)
from typing import Tuple
import re

class DatosBasicosWidget(QGroupBox):
    """Widget para gestionar datos básicos de un profesor.
    
    Gestiona:
    - Nombre completo del profesor
    - Email corporativo
    - Flag de si es tutor
    
    Señales:
        datos_changed: Emitida cuando cambia algún dato.
    """
    
    # ========== SEÑALES ==========
    datos_changed = pyqtSignal()
    
    # ========== INICIALIZACIÓN ==========
    
    def __init__(self, parent=None):
        """Inicializa el widget de datos básicos."""
        super().__init__("Datos Básicos", parent)
        self._setup_ui()
        self._conectar_senales()
    
    # ========== MÉTODOS PRIVADOS (Setup) ==========
    
    def _setup_ui(self):
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Nombre completo
        self.nombre_completo_input = QLineEdit()
        self.nombre_completo_input.setPlaceholderText("Ej: Juan Pérez García")
        form_layout.addRow("Nombre completo:", self.nombre_completo_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ej: juan.perez@centro.edu")
        form_layout.addRow("Email:", self.email_input)
        
        # Es tutor
        self.es_tutor_checkbox = QCheckBox("Es tutor de un grupo")
        form_layout.addRow("", self.es_tutor_checkbox)
        
        layout.addLayout(form_layout)
        self.setLayout(layout)
    
    def _conectar_senales(self):
        """Conecta las señales del widget."""
        self.nombre_completo_input.textChanged.connect(self.datos_changed)
        self.email_input.textChanged.connect(self.datos_changed)
        self.es_tutor_checkbox.stateChanged.connect(self.datos_changed)
    
    # ========== API PÚBLICA ==========
    
    def get_datos(self) -> dict:
        """Obtiene los datos del widget.
        
        Returns:
            dict: {
                "nombre_completo": str,
                "email": str,
                "es_tutor": bool
            }
        """
        return {
            "nombre_completo": self.nombre_completo_input.text().strip(),
            "email": self.email_input.text().strip(),
            "es_tutor": self.es_tutor_checkbox.isChecked()
        }
    
    def set_datos(self, datos: dict):
        """Establece los datos del widget.
        
        Args:
            datos: Diccionario con claves:
                - nombre_completo (str)
                - email (str)
                - es_tutor (bool)
        """
        self.nombre_completo_input.setText(datos.get("nombre_completo", ""))
        self.email_input.setText(datos.get("email", ""))
        self.es_tutor_checkbox.setChecked(datos.get("es_tutor", False))
    
    def validar(self) -> Tuple[bool, str]:
        """Valida los datos del widget.
        
        Returns:
            (True, "") si válido
            (False, "mensaje de error") si inválido
        """
        nombre = self.nombre_completo_input.text().strip()
        email = self.email_input.text().strip()
        
        # Validar nombre
        if not nombre:
            return False, "El nombre completo es obligatorio"
        
        if len(nombre) < 3:
            return False, "El nombre debe tener al menos 3 caracteres"
        
        # Validar email
        if not email:
            return False, "El email es obligatorio"
        
        patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(patron_email, email):
            return False, "El formato del email no es válido"
        
        return True, ""
    
    def limpiar(self):
        """Limpia todos los campos."""
        self.nombre_completo_input.clear()
        self.email_input.clear()
        self.es_tutor_checkbox.setChecked(False)
```

---

## 🔌 API Estándar

### Métodos Obligatorios

Todo widget DEBE implementar estos 4 métodos:

#### 1. `get_datos() -> dict`

**Propósito**: Obtener el estado actual del widget.

**Firma**:
```python
def get_datos(self) -> dict:
    """Obtiene los datos actuales del widget."""
    pass
```

**Características**:
- ✅ Retorna SIEMPRE un diccionario
- ✅ Claves descriptivas y consistentes
- ✅ Valores "limpios" (`.strip()` en strings)
- ✅ Sin efectos secundarios (no modifica estado)
- ✅ Documentar claves en docstring

**Ejemplo**:
```python
def get_datos(self) -> dict:
    """Obtiene los datos del widget.
    
    Returns:
        dict: {
            "nombre": str,
            "activo": bool,
            "fecha": date | None
        }
    """
    fecha_text = self.fecha_input.text()
    return {
        "nombre": self.nombre_input.text().strip(),
        "activo": self.activo_checkbox.isChecked(),
        "fecha": date.fromisoformat(fecha_text) if fecha_text else None
    }
```

---

#### 2. `set_datos(datos: dict)`

**Propósito**: Establecer el estado del widget desde un diccionario.

**Firma**:
```python
def set_datos(self, datos: dict):
    """Establece los datos del widget."""
    pass
```

**Características**:
- ✅ Acepta diccionario con claves opcionales
- ✅ Usa `.get()` con valores por defecto
- ✅ Robusto ante claves faltantes
- ✅ Maneja conversiones de tipos necesarias
- ✅ Documentar claves esperadas

**Ejemplo**:
```python
def set_datos(self, datos: dict):
    """Establece los datos del widget.
    
    Args:
        datos: Diccionario con claves opcionales:
            - nombre (str): Nombre del elemento
            - activo (bool): Si está activo
            - fecha (date): Fecha asociada
    """
    self.nombre_input.setText(datos.get("nombre", ""))
    self.activo_checkbox.setChecked(datos.get("activo", False))
    
    fecha = datos.get("fecha")
    if fecha:
        self.fecha_input.setText(fecha.isoformat())
    else:
        self.fecha_input.clear()
```

---

#### 3. `validar() -> Tuple[bool, str]`

**Propósito**: Validar que los datos del widget son correctos.

**Firma**:
```python
def validar(self) -> Tuple[bool, str]:
    """Valida los datos del widget."""
    pass
```

**Características**:
- ✅ Retorna tupla `(es_válido: bool, mensaje_error: str)`
- ✅ Si válido: `(True, "")`
- ✅ Si inválido: `(False, "Descripción del error")`
- ✅ Validaciones en orden de importancia
- ✅ Retornar en el PRIMER error encontrado
- ✅ Mensajes claros y accionables

**Ejemplo**:
```python
def validar(self) -> Tuple[bool, str]:
    """Valida los datos del widget.
    
    Returns:
        (True, "") si todo es válido
        (False, mensaje) si hay error
    """
    nombre = self.nombre_input.text().strip()
    
    # Validación 1: Campo obligatorio
    if not nombre:
        return False, "El nombre es obligatorio"
    
    # Validación 2: Longitud mínima
    if len(nombre) < 3:
        return False, "El nombre debe tener al menos 3 caracteres"
    
    # Validación 3: Caracteres válidos
    if not nombre.replace(" ", "").isalpha():
        return False, "El nombre solo puede contener letras"
    
    # Validación de fecha (si aplica)
    fecha_text = self.fecha_input.text()
    if fecha_text:
        try:
            date.fromisoformat(fecha_text)
        except ValueError:
            return False, "Formato de fecha inválido (use YYYY-MM-DD)"
    
    return True, ""
```

---

#### 4. `limpiar()`

**Propósito**: Resetear el widget a su estado inicial.

**Firma**:
```python
def limpiar(self):
    """Limpia todos los campos del widget."""
    pass
```

**Características**:
- ✅ Vacía todos los inputs de texto
- ✅ Desmarca checkboxes
- ✅ Resetea combos a índice 0 o vacío
- ✅ Restaura valores por defecto si los hay
- ✅ NO emite señales (bloquear temporalmente si necesario)

**Ejemplo**:
```python
def limpiar(self):
    """Limpia todos los campos del widget."""
    # Bloquear señales durante limpieza
    self.blockSignals(True)
    
    self.nombre_input.clear()
    self.activo_checkbox.setChecked(False)
    self.fecha_input.clear()
    self.tipo_combo.setCurrentIndex(0)
    
    # Reactivar señales
    self.blockSignals(False)
```

---

### Señales Recomendadas

#### 1. `datos_changed = pyqtSignal()`

**Propósito**: Notificar cuando cambia cualquier dato del widget.

**Uso**:
```python
class MiWidget(QGroupBox):
    datos_changed = pyqtSignal()
    
    def _conectar_senales(self):
        self.nombre_input.textChanged.connect(self.datos_changed)
        self.activo_checkbox.stateChanged.connect(self.datos_changed)

# En el formulario padre
widget.datos_changed.connect(self._on_datos_changed)
```

**Cuándo emitirla**:
- Conectarla a `textChanged`, `stateChanged`, `currentIndexChanged`, etc.
- CADA vez que el usuario modifique algo
- NO emitirla en `set_datos()` (usar `blockSignals(True)`)

---

## 🎨 Integración con Formularios

### Patrón de Uso en Formularios

```python
class ProfesorForm(QDialog):
    """Formulario para gestionar profesores."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._conectar_senales()
    
    def _setup_ui(self):
        """Crea la interfaz usando widgets."""
        layout = QVBoxLayout(self)
        
        # Crear widgets
        self.datos_basicos_widget = DatosBasicosWidget()
        self.horario_widget = HorarioWidget()
        self.restricciones_widget = RestriccionesWidget()
        
        # Añadir al layout
        layout.addWidget(self.datos_basicos_widget)
        layout.addWidget(self.horario_widget)
        layout.addWidget(self.restricciones_widget)
        
        # Botones
        self.guardar_btn = QPushButton("Guardar")
        layout.addWidget(self.guardar_btn)
    
    def _conectar_senales(self):
        """Conecta las señales."""
        self.guardar_btn.clicked.connect(self._on_guardar)
        
        # Opcional: reaccionar a cambios en widgets
        self.datos_basicos_widget.datos_changed.connect(
            self._on_datos_changed
        )
    
    def _on_guardar(self):
        """Handler del botón guardar."""
        # 1. Validar todos los widgets
        if not self._validar_formulario():
            return
        
        # 2. Recopilar datos
        datos = self._get_datos_completos()
        
        # 3. Guardar (Use Case, etc.)
        self._guardar_profesor(datos)
    
    def _validar_formulario(self) -> bool:
        """Valida todos los widgets del formulario."""
        # Validar datos básicos
        es_valido, error = self.datos_basicos_widget.validar()
        if not es_valido:
            QMessageBox.warning(self, "Error", error)
            return False
        
        # Validar horario
        es_valido, error = self.horario_widget.validar()
        if not es_valido:
            QMessageBox.warning(self, "Error", error)
            return False
        
        # Validar restricciones
        es_valido, error = self.restricciones_widget.validar()
        if not es_valido:
            QMessageBox.warning(self, "Error", error)
            return False
        
        return True
    
    def _get_datos_completos(self) -> dict:
        """Recopila datos de todos los widgets."""
        datos = {}
        datos.update(self.datos_basicos_widget.get_datos())
        datos.update(self.horario_widget.get_datos())
        datos.update(self.restricciones_widget.get_datos())
        return datos
    
    def cargar_profesor(self, profesor_id: int):
        """Carga un profesor existente en el formulario."""
        # 1. Obtener datos (Use Case, repository, etc.)
        datos = self._obtener_profesor(profesor_id)
        
        # 2. Distribuir datos a widgets
        self.datos_basicos_widget.set_datos(datos)
        self.horario_widget.set_datos(datos)
        self.restricciones_widget.set_datos(datos)
```

### Propiedades de Compatibilidad (Opcional)

Para mantener compatibilidad con código existente:

```python
class ProfesorForm(QDialog):
    # ... código anterior ...
    
    # Propiedades de compatibilidad
    @property
    def nombre_completo_input(self):
        """Compatibilidad: acceso directo al campo nombre."""
        return self.datos_basicos_widget.nombre_completo_input
    
    @property
    def email_input(self):
        """Compatibilidad: acceso directo al campo email."""
        return self.datos_basicos_widget.email_input
```

**Cuándo usar**:
- ✅ Cuando hay código legacy que accede directamente a campos
- ✅ Cuando los tests existentes no pueden modificarse fácilmente
- ⚠️ NO crear en formularios nuevos
- ⚠️ Marcar como deprecated para futura eliminación

---

## ✅ Mejores Prácticas

### 1. Naming Conventions

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| **Clase del widget** | `<Concepto>Widget` | `DatosBasicosWidget` |
| **Archivo** | `<concepto>_widget.py` | `datos_basicos_widget.py` |
| **Directorio** | `<dominio>_widgets/` | `profesor_widgets/` |
| **Inputs** | `<nombre>_input` | `nombre_completo_input` |
| **Checkboxes** | `<nombre>_checkbox` | `es_tutor_checkbox` |
| **Combos** | `<nombre>_combo` | `turno_combo` |
| **Botones** | `<accion>_btn` | `guardar_btn` |
| **Labels** | `label_<nombre>` | `label_nombre` |
| **Métodos privados** | `_<nombre>` | `_setup_ui()` |
| **Handlers** | `_on_<evento>` | `_on_guardar()` |

### 2. Organización de Código

```python
class MiWidget(QGroupBox):
    # 1. Docstring de clase
    """..."""
    
    # 2. Señales (clase level)
    datos_changed = pyqtSignal()
    
    # 3. __init__
    def __init__(self, parent=None):
        ...
    
    # 4. Métodos privados de setup (alfabético)
    def _conectar_senales(self):
        ...
    
    def _setup_ui(self):
        ...
    
    # 5. Métodos privados handlers (alfabético)
    def _on_campo_changed(self):
        ...
    
    # 6. API pública (orden estándar)
    def get_datos(self) -> dict:
        ...
    
    def set_datos(self, datos: dict):
        ...
    
    def validar(self) -> Tuple[bool, str]:
        ...
    
    def limpiar(self):
        ...
    
    # 7. Métodos adicionales públicos (alfabético)
    def calcular_algo(self):
        ...
```

### 3. Validaciones

**Orden de validaciones**:
1. Campos obligatorios
2. Formatos válidos
3. Rangos permitidos
4. Lógica de negocio
5. Relaciones entre campos

**Mensajes de error**:
- ✅ Claros y específicos
- ✅ Accionables (indicar qué hacer)
- ✅ Sin jerga técnica
- ❌ Evitar "Error" o "Inválido" sin contexto

```python
# ✅ BUENO
return False, "El email es obligatorio"
return False, "El nombre debe tener al menos 3 caracteres"
return False, "La fecha de fin debe ser posterior a la fecha de inicio"

# ❌ MALO
return False, "Error en email"
return False, "Nombre inválido"
return False, "Fechas incorrectas"
```

### 4. Señales

**Conectar señales en `_conectar_senales()`**:
```python
def _conectar_senales(self):
    """Conecta las señales del widget."""
    self.nombre_input.textChanged.connect(self.datos_changed)
    self.email_input.textChanged.connect(self._on_email_changed)
    self.guardar_btn.clicked.connect(self._on_guardar)
```

**Bloquear señales durante operaciones masivas**:
```python
def set_datos(self, datos: dict):
    """Establece los datos del widget."""
    self.blockSignals(True)
    
    # Establecer todos los campos
    self.nombre_input.setText(datos.get("nombre", ""))
    self.email_input.setText(datos.get("email", ""))
    
    self.blockSignals(False)
```

### 5. Documentación

**Docstring de clase**:
```python
class MiWidget(QGroupBox):
    """Descripción breve en una línea.
    
    Descripción extendida:
    - Qué gestiona
    - Cuándo usarlo
    - Consideraciones especiales
    
    Señales:
        datos_changed: Emitida cuando cambian los datos.
        error: Emitida cuando hay un error (mensaje: str).
    
    Ejemplo:
        >>> widget = MiWidget()
        >>> widget.set_datos({"nombre": "Juan"})
        >>> if widget.validar()[0]:
        ...     datos = widget.get_datos()
    """
```

**Docstring de métodos**:
```python
def get_datos(self) -> dict:
    """Obtiene los datos actuales del widget.
    
    Returns:
        Diccionario con claves:
            - nombre (str): Nombre completo
            - email (str): Email corporativo
            - activo (bool): Si está activo
    
    Ejemplo:
        >>> datos = widget.get_datos()
        >>> print(datos["nombre"])
        "Juan Pérez"
    """
```

---

## ❌ Anti-patrones

### 1. Widget con Múltiples Responsabilidades

```python
# ❌ MALO - Widget que hace demasiado
class ProfesorCompleto Widget(QGroupBox):
    """Widget que gestiona TODO un profesor."""
    
    def __init__(self, parent=None):
        # Gestiona datos básicos
        self.nombre_input = QLineEdit()
        self.email_input = QLineEdit()
        
        # Y horario
        self.horas_input = QSpinBox()
        self.turno_combo = QComboBox()
        
        # Y restricciones
        self.dias_widgets = [...]
        
        # Y guardias asignadas
        self.guardias_table = QTableWidget()
        
        # ¡DEMASIADO!
```

```python
# ✅ BUENO - Widgets especializados
class DatosBasicosWidget(QGroupBox):
    """Solo gestiona nombre y email."""
    pass

class HorarioWidget(QGroupBox):
    """Solo gestiona horas y turno."""
    pass

class RestriccionesWidget(QGroupBox):
    """Solo gestiona restricciones."""
    pass
```

### 2. Acoplamiento al Formulario Padre

```python
# ❌ MALO - Widget acoplado al formulario
class MiWidget(QGroupBox):
    def validar(self):
        # Accede al formulario padre directamente
        if self.parent().modo == "edicion":
            # Lógica diferente según el padre
            pass

# ✅ BUENO - Widget independiente
class MiWidget(QGroupBox):
    def __init__(self, parent=None, modo="creacion"):
        # Modo pasado como parámetro
        self.modo = modo
    
    def validar(self):
        # Lógica basada en configuración interna
        if self.modo == "edicion":
            pass
```

### 3. Validación Solo en el Formulario

```python
# ❌ MALO - Validación fuera del widget
class ProfesorForm(QDialog):
    def _validar(self):
        # Accede directamente a los campos del widget
        nombre = self.datos_widget.nombre_input.text()
        if not nombre:
            QMessageBox.warning("Error", "Nombre obligatorio")
            return False

# ✅ BUENO - Validación en el widget
class DatosWidget(QGroupBox):
    def validar(self) -> Tuple[bool, str]:
        nombre = self.nombre_input.text().strip()
        if not nombre:
            return False, "El nombre es obligatorio"
        return True, ""

class ProfesorForm(QDialog):
    def _validar(self):
        es_valido, error = self.datos_widget.validar()
        if not es_valido:
            QMessageBox.warning("Error", error)
            return False
        return True
```

### 4. get_datos() con Efectos Secundarios

```python
# ❌ MALO - Modifica estado al obtener datos
class MiWidget(QGroupBox):
    def get_datos(self) -> dict:
        # ¡NO HACER ESTO!
        self._ultimo_acceso = datetime.now()  # Efecto secundario
        self._contador += 1  # Efecto secundario
        
        return {"nombre": self.nombre_input.text()}

# ✅ BUENO - get_datos() es puro
class MiWidget(QGroupBox):
    def get_datos(self) -> dict:
        # Solo retorna datos, sin efectos secundarios
        return {"nombre": self.nombre_input.text().strip()}
```

### 5. Señales No Documentadas

```python
# ❌ MALO - Señales sin documentar
class MiWidget(QGroupBox):
    signal1 = pyqtSignal()
    signal2 = pyqtSignal(str)
    something_happened = pyqtSignal(int, bool)

# ✅ BUENO - Señales documentadas
class MiWidget(QGroupBox):
    """Widget para X.
    
    Señales:
        datos_changed: Emitida cuando cambia algún dato.
        validacion_error: Emitida cuando hay error de validación.
            Args:
                mensaje (str): Descripción del error.
        guardado_completo: Emitida cuando se completa el guardado.
            Args:
                id (int): ID del elemento guardado.
                exitoso (bool): Si fue exitoso.
    """
    datos_changed = pyqtSignal()
    validacion_error = pyqtSignal(str)
    guardado_completo = pyqtSignal(int, bool)
```

---

## 📚 Casos de Uso

### Caso 1: Widget Simple (Entrada de Texto)

**Escenario**: Campo de nombre con validación básica.

```python
class NombreWidget(QGroupBox):
    """Widget para ingresar un nombre."""
    
    datos_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Nombre", parent)
        self._setup_ui()
        self._conectar_senales()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ingrese el nombre")
        layout.addWidget(self.nombre_input)
    
    def _conectar_senales(self):
        self.nombre_input.textChanged.connect(self.datos_changed)
    
    def get_datos(self) -> dict:
        return {"nombre": self.nombre_input.text().strip()}
    
    def set_datos(self, datos: dict):
        self.nombre_input.setText(datos.get("nombre", ""))
    
    def validar(self) -> Tuple[bool, str]:
        nombre = self.nombre_input.text().strip()
        if not nombre:
            return False, "El nombre es obligatorio"
        if len(nombre) < 3:
            return False, "El nombre debe tener al menos 3 caracteres"
        return True, ""
    
    def limpiar(self):
        self.nombre_input.clear()
```

### Caso 2: Widget con Múltiples Campos Relacionados

**Escenario**: Rango de fechas (inicio y fin) con validación de coherencia.

```python
class RangoFechasWidget(QGroupBox):
    """Widget para seleccionar un rango de fechas."""
    
    datos_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Rango de Fechas", parent)
        self._setup_ui()
        self._conectar_senales()
    
    def _setup_ui(self):
        layout = QFormLayout(self)
        
        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        layout.addRow("Fecha inicio:", self.fecha_inicio_input)
        
        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        layout.addRow("Fecha fin:", self.fecha_fin_input)
    
    def _conectar_senales(self):
        self.fecha_inicio_input.dateChanged.connect(self.datos_changed)
        self.fecha_fin_input.dateChanged.connect(self.datos_changed)
    
    def get_datos(self) -> dict:
        return {
            "fecha_inicio": self.fecha_inicio_input.date().toPyDate(),
            "fecha_fin": self.fecha_fin_input.date().toPyDate()
        }
    
    def set_datos(self, datos: dict):
        if "fecha_inicio" in datos:
            fecha_inicio = QDate(datos["fecha_inicio"])
            self.fecha_inicio_input.setDate(fecha_inicio)
        
        if "fecha_fin" in datos:
            fecha_fin = QDate(datos["fecha_fin"])
            self.fecha_fin_input.setDate(fecha_fin)
    
    def validar(self) -> Tuple[bool, str]:
        fecha_inicio = self.fecha_inicio_input.date().toPyDate()
        fecha_fin = self.fecha_fin_input.date().toPyDate()
        
        # Validar que fin >= inicio
        if fecha_fin < fecha_inicio:
            return False, "La fecha de fin debe ser posterior a la de inicio"
        
        # Validar que el rango no sea excesivo (ej: máx 1 año)
        diferencia = (fecha_fin - fecha_inicio).days
        if diferencia > 365:
            return False, "El rango no puede exceder 1 año"
        
        return True, ""
    
    def limpiar(self):
        hoy = QDate.currentDate()
        self.fecha_inicio_input.setDate(hoy)
        self.fecha_fin_input.setDate(hoy)
```

### Caso 3: Widget con Lista Dinámica

**Escenario**: Lista de emails con botones añadir/eliminar.

```python
class ListaEmailsWidget(QGroupBox):
    """Widget para gestionar una lista de emails."""
    
    datos_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Emails", parent)
        self._setup_ui()
        self._conectar_senales()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Lista
        self.emails_list = QListWidget()
        layout.addWidget(self.emails_list)
        
        # Input + botón añadir
        add_layout = QHBoxLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("nuevo@email.com")
        self.add_btn = QPushButton("Añadir")
        add_layout.addWidget(self.email_input)
        add_layout.addWidget(self.add_btn)
        layout.addLayout(add_layout)
        
        # Botón eliminar
        self.remove_btn = QPushButton("Eliminar seleccionado")
        layout.addWidget(self.remove_btn)
    
    def _conectar_senales(self):
        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
    
    def _on_add(self):
        email = self.email_input.text().strip()
        if email and self._validar_email(email):
            self.emails_list.addItem(email)
            self.email_input.clear()
            self.datos_changed.emit()
    
    def _on_remove(self):
        current_row = self.emails_list.currentRow()
        if current_row >= 0:
            self.emails_list.takeItem(current_row)
            self.datos_changed.emit()
    
    def _validar_email(self, email: str) -> bool:
        import re
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    def get_datos(self) -> dict:
        emails = []
        for i in range(self.emails_list.count()):
            emails.append(self.emails_list.item(i).text())
        return {"emails": emails}
    
    def set_datos(self, datos: dict):
        self.emails_list.clear()
        for email in datos.get("emails", []):
            self.emails_list.addItem(email)
    
    def validar(self) -> Tuple[bool, str]:
        if self.emails_list.count() == 0:
            return False, "Debe añadir al menos un email"
        return True, ""
    
    def limpiar(self):
        self.emails_list.clear()
        self.email_input.clear()
```

---

## ☑️ Checklist de Implementación

### Fase 1: Diseño

- [ ] **Definir responsabilidad única** del widget
- [ ] **Identificar campos** que gestionará
- [ ] **Diseñar API pública** (get_datos, set_datos, validar, limpiar)
- [ ] **Definir señales** necesarias
- [ ] **Diseñar validaciones** y mensajes de error

### Fase 2: Implementación

- [ ] **Crear estructura** del archivo y clase
- [ ] **Documentar clase** con docstring completo
- [ ] **Declarar señales** con documentación
- [ ] **Implementar `__init__`**
- [ ] **Implementar `_setup_ui()`**
  - [ ] Crear layout principal
  - [ ] Crear widgets internos
  - [ ] Configurar propiedades (placeholders, tooltips)
  - [ ] Añadir widgets al layout
- [ ] **Implementar `_conectar_senales()`**
  - [ ] Conectar señales internas
  - [ ] Conectar handlers privados
- [ ] **Implementar handlers** (`_on_*`)
- [ ] **Implementar `get_datos()`**
  - [ ] Retornar diccionario
  - [ ] Limpiar strings con `.strip()`
  - [ ] Documentar claves retornadas
- [ ] **Implementar `set_datos()`**
  - [ ] Usar `.get()` con defaults
  - [ ] Manejar None y valores faltantes
  - [ ] Documentar claves esperadas
- [ ] **Implementar `validar()`**
  - [ ] Validar campos obligatorios
  - [ ] Validar formatos
  - [ ] Validar rangos
  - [ ] Validar lógica de negocio
  - [ ] Retornar tupla `(bool, str)`
  - [ ] Mensajes claros y accionables
- [ ] **Implementar `limpiar()`**
  - [ ] Vaciar todos los campos
  - [ ] Restaurar valores por defecto
  - [ ] Bloquear señales si necesario

### Fase 3: Integración

- [ ] **Crear `__init__.py`** en directorio de widgets
- [ ] **Importar widget** en formulario
- [ ] **Instanciar widget** en `_setup_ui()`
- [ ] **Conectar señales** en formulario
- [ ] **Usar en validación** del formulario
- [ ] **Usar en get/set** de datos del formulario
- [ ] **Crear propiedades de compatibilidad** (si necesario)

### Fase 4: Documentación

- [ ] **Docstring de módulo** completo
- [ ] **Docstring de clase** completo
- [ ] **Docstrings de métodos** completos
- [ ] **Ejemplos de uso** en docstrings
- [ ] **Señales documentadas** en docstring de clase

### Fase 5: Testing

- [ ] **Test: get_datos()** retorna datos correctos
- [ ] **Test: set_datos()** establece datos correctos
- [ ] **Test: validar()** con datos válidos retorna True
- [ ] **Test: validar()** con datos inválidos retorna False
- [ ] **Test: limpiar()** resetea todos los campos
- [ ] **Test: señales** se emiten correctamente

### Fase 6: Calidad

- [ ] **Ejecutar ruff format** (formato)
- [ ] **Ejecutar ruff check** (linting)
- [ ] **Verificar type hints** en API pública
- [ ] **Revisar nombres** (convenciones)
- [ ] **Sin errores de compilación**

---

## 📖 Referencias

### Widgets Implementados en el Proyecto

**configuracion_widgets/** (6 widgets):
- `datos_generales_widget.py`
- `configuracion_recreo_widget.py`
- `zonas_profesor_config_widget.py`
- `tolerancia_equidad_widget.py`
- `configuracion_email_widget.py`
- `guardar_cancelar_widget.py`

**profesor_widgets/** (3 widgets):
- `datos_basicos_widget.py`
- `horario_widget.py`
- `restricciones_widget.py`

**zona_widgets/** (1 widget):
- `datos_zona_widget.py`

**import_export_widgets/** (2 widgets):
- `json_operations_widget.py`
- `pdf_export_widget.py`

### Documentación Relacionada

- **CHANGELOG v3.0**: `documentacion/versiones/CHANGELOG_v3.0.md`
- **Resumen de Sesión**: `documentacion/RESUMEN_SESION_01NOV2025_PARTE2.md`
- **Arquitectura**: `documentacion/ARCHITECTURE_PATTERNS.md`

---

## 🏁 Conclusión

Este patrón de widgets ha demostrado ser altamente efectivo en el proyecto Guardias de Patio:

✅ **Reducción de código**: -40.3% promedio en formularios  
✅ **Reutilización**: 12 widgets extraídos y reutilizables  
✅ **Mantenibilidad**: Responsabilidades claras y código organizado  
✅ **Testabilidad**: API pública facilita tests unitarios  
✅ **Escalabilidad**: Patrón repetible para nuevos formularios  

Siguiendo este patrón, cualquier desarrollador puede crear widgets consistentes, mantenibles y de alta calidad.

---

*Versión 1.0 - 1 de noviembre de 2025*  
*Autor: Refactorización Guardias de Patio v3.0*
