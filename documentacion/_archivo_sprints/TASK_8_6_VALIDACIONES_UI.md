# Task 8.6: Validaciones UI en Tiempo Real

**Sprint**: 8  
**Fecha**: 19 de octubre de 2025  
**Estado**: ✅ COMPLETADO  
**Tests**: 29/29 pasando (100%)

---

## 📋 Objetivo

Implementar sistema completo de validación de formularios con **feedback visual inmediato** para mejorar la experiencia de usuario y reducir errores de entrada de datos.

---

## ✨ Características Implementadas

### 1. Sistema de Validación Base

#### **ValidadorCampo** (Clase Base)
- ✅ Validación en tiempo real con debouncing configurable
- ✅ 3 estados visuales: neutro (gris), válido (verde), inválido (rojo)
- ✅ Mensajes de error/éxito debajo del campo
- ✅ Timer para evitar validar en cada tecla (default 500ms)
- ✅ Métodos: `validar_inmediato()`, `reset()`, `_set_estado_*()`

**Flujo de Validación**:
```
Usuario escribe → Wait debounce_ms → Ejecutar validador → Actualizar UI
                                                              ↓
                                       Verde ✓ / Rojo ⚠️ / Gris (neutro)
```

---

### 2. Validadores Específicos

#### **ValidadorEmail**
```python
validador = ValidadorEmail(campo_email, label_error)
```
- ✅ Valida formato de email (patron@dominio.ext)
- ✅ Debouncing: 500ms
- ✅ Mensajes:
  - Éxito: "✓ Email válido"
  - Error: "⚠️ Formato de email inválido"

#### **ValidadorNombreCompleto**
```python
validador = ValidadorNombreCompleto(campo_nombre, label_error)
```
- ✅ Valida formato "APELLIDOS, NOMBRE" (con coma)
- ✅ Debouncing: 500ms
- ✅ Mensajes:
  - Éxito: "✓ Nombre válido"
  - Error: "⚠️ Formato incorrecto. Use: APELLIDOS, NOMBRE (con coma)"

#### **ValidadorHorasContrato**
```python
validador = ValidadorHorasContrato(campo_horas, label_error)
```
- ✅ Valida rango 0 < horas <= 40
- ✅ Acepta decimales (20.5)
- ✅ Debouncing: 300ms (más rápido para números)
- ✅ Mensajes:
  - Éxito: "✓ Horas válidas"
  - Error: "⚠️ Las horas deben ser un número positivo" / "... no pueden superar 40..."

#### **ValidadorRequerido**
```python
validador = ValidadorRequerido(campo, label_error, "Nombre del Campo")
```
- ✅ Valida que el campo no esté vacío
- ✅ Ignora espacios (`.strip()`)
- ✅ Mensaje de error personalizable
- ✅ Debouncing: 300ms

---

### 3. Validador de Formulario Completo

#### **ValidadorFormulario**
```python
formulario = ValidadorFormulario()
formulario.agregar_validador(validador_nombre)
formulario.agregar_validador(validador_email)
formulario.agregar_validador(validador_horas)

# Validar todos antes de guardar
es_valido, errores = formulario.validar_todo()
if es_valido:
    guardar_datos()
else:
    mostrar_errores(errores)
```

**Métodos**:
- ✅ `agregar_validador(validador)`: Agregar validador al formulario
- ✅ `validar_todo()`: Retorna `(bool, list[str])` con validez y lista de errores
- ✅ `reset_todo()`: Resetea todos los validadores
- ✅ `son_todos_validos()`: Verifica estado actual sin validar

---

### 4. Helpers para Aplicación Rápida

```python
from widgets.validadores_ui import (
    aplicar_validacion_email,
    aplicar_validacion_nombre,
    aplicar_validacion_horas,
    aplicar_validacion_requerido,
)

# Uso
campo_email = QLineEdit()
validador_email, label_error_email = aplicar_validacion_email(campo_email)

# Agregar label_error al layout
layout.addWidget(campo_email)
layout.addWidget(label_error_email)  # Mensaje de error debajo
```

---

## 🎨 Estilos CSS

### Estados Visuales

#### **Estado Neutral** (sin validar)
```css
QLineEdit {
    border: 2px solid #CCCCCC;  /* Gris */
    background-color: #FFFFFF;
    padding: 8px;
    border-radius: 4px;
}
```

#### **Estado Válido** (verde)
```css
QLineEdit {
    border: 2px solid #4CAF50;  /* Verde */
    background-color: #E8F5E9;  /* Verde claro */
    padding: 8px;
    border-radius: 4px;
}
```

#### **Estado Inválido** (rojo)
```css
QLineEdit {
    border: 2px solid #F44336;  /* Rojo */
    background-color: #FFEBEE;  /* Rojo claro */
    padding: 8px;
    border-radius: 4px;
}
```

### Labels de Mensaje

#### **Mensaje de Error**
```css
QLabel {
    color: #D32F2F;           /* Rojo oscuro */
    font-size: 11px;
    font-weight: bold;
    padding: 2px 4px;
}
```

#### **Mensaje de Éxito**
```css
QLabel {
    color: #388E3C;           /* Verde oscuro */
    font-size: 11px;
    font-weight: bold;
    padding: 2px 4px;
}
```

---

## 📊 Tests Implementados

### Cobertura
- **Total tests**: 29
- **Pasando**: 29 (100%)
- **Cobertura**: 71.72% en `validadores_ui.py`

### Categorías de Tests

#### **1. Tests por Validador** (4 clases)
```
TestValidadorEmail           (5 tests)
TestValidadorNombreCompleto  (4 tests)
TestValidadorHorasContrato   (5 tests)
TestValidadorRequerido       (4 tests)
```

#### **2. Tests de Formulario** (4 tests)
```
test_formulario_todos_validos       ✅
test_formulario_con_errores         ✅
test_formulario_reset               ✅
test_son_todos_validos              ✅
```

#### **3. Tests de Helpers** (5 tests)
```
test_crear_label_error              ✅
test_aplicar_validacion_email       ✅
test_aplicar_validacion_nombre      ✅
test_aplicar_validacion_horas       ✅
test_aplicar_validacion_requerido   ✅
```

#### **4. Tests de Integración** (2 tests)
```
test_flujo_completo_validacion      ✅
test_corregir_errores_en_tiempo_real ✅
```

---

## 📁 Archivos Creados

### Código

#### **src/widgets/validadores_ui.py** (429 líneas)
```
Estructura:
- Estilos CSS (60 líneas)
- ValidadorCampo (clase base, 120 líneas)
- Validadores específicos (4 clases, 100 líneas)
- ValidadorFormulario (50 líneas)
- Helper functions (100 líneas)
```

#### **tests/test_validadores_ui.py** (450 líneas)
```
Estructura:
- Fixtures (20 líneas)
- 4 clases de test por validador (200 líneas)
- 1 clase de test de formulario (80 líneas)
- 1 clase de test de helpers (80 líneas)
- 1 clase de test de integración (70 líneas)
```

---

## 🚀 Uso en Producción

### Ejemplo: Formulario de Profesor

```python
from PyQt6.QtWidgets import QVBoxLayout, QLineEdit, QPushButton
from widgets.validadores_ui import (
    aplicar_validacion_nombre,
    aplicar_validacion_email,
    aplicar_validacion_horas,
    ValidadorFormulario,
)

class ProfesorForm(QWidget):
    def __init__(self):
        super().__init__()
        
        # Crear campos
        self.campo_nombre = QLineEdit()
        self.campo_email = QLineEdit()
        self.campo_horas = QLineEdit()
        
        # Aplicar validadores
        val_nombre, label_nombre = aplicar_validacion_nombre(self.campo_nombre)
        val_email, label_email = aplicar_validacion_email(self.campo_email)
        val_horas, label_horas = aplicar_validacion_horas(self.campo_horas)
        
        # Crear formulario completo
        self.formulario = ValidadorFormulario()
        self.formulario.agregar_validador(val_nombre)
        self.formulario.agregar_validador(val_email)
        self.formulario.agregar_validador(val_horas)
        
        # Layout
        layout = QVBoxLayout()
        
        # Nombre
        layout.addWidget(QLabel("Nombre Completo:"))
        layout.addWidget(self.campo_nombre)
        layout.addWidget(label_nombre)  # Mensaje de validación
        
        # Email
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.campo_email)
        layout.addWidget(label_email)
        
        # Horas
        layout.addWidget(QLabel("Horas Contrato:"))
        layout.addWidget(self.campo_horas)
        layout.addWidget(label_horas)
        
        # Botón guardar
        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(btn_guardar)
        
        self.setLayout(layout)
    
    def guardar(self):
        # Validar todo antes de guardar
        es_valido, errores = self.formulario.validar_todo()
        
        if not es_valido:
            QMessageBox.warning(
                self,
                "Errores de Validación",
                "Por favor corrija los siguientes errores:\n\n" + "\n".join(errores)
            )
            return
        
        # Guardar datos
        nombre = self.campo_nombre.text()
        email = self.campo_email.text()
        horas = float(self.campo_horas.text())
        
        # ... guardar en BD ...
        
        QMessageBox.information(self, "Éxito", "Profesor guardado correctamente")
```

---

## 📈 Beneficios

### Para Usuarios
- ✅ **Feedback Inmediato**: Saben si hay errores mientras escriben
- ✅ **Menos Frustración**: No esperan hasta hacer click en "Guardar" para ver errores
- ✅ **Guías Visuales**: Colores y mensajes claros sobre qué está mal
- ✅ **Menos Errores**: Validación antes de enviar evita datos incorrectos

### Para Desarrolladores
- ✅ **Reutilizable**: Validadores se aplican con 1 línea
- ✅ **Consistente**: Misma UX en todos los formularios
- ✅ **Testeable**: 29 tests garantizan funcionamiento
- ✅ **Extensible**: Fácil crear nuevos validadores heredando de `ValidadorCampo`

### Para el Sistema
- ✅ **Menos Queries Inválidos**: Datos validados antes de llegar a BD
- ✅ **Mejor Performance**: Validación cliente-side vs server-side
- ✅ **Logs Más Limpios**: Menos excepciones por datos inválidos

---

## 🔧 Configuración Avanzada

### Crear Validador Personalizado

```python
from widgets.validadores_ui import ValidadorCampo
from typing import Tuple, Optional

class ValidadorDNI(ValidadorCampo):
    """Validador personalizado para DNI español."""
    
    def __init__(self, campo: QLineEdit, label_error: QLabel):
        super().__init__(
            campo=campo,
            label_error=label_error,
            validador=self._validar_dni,
            mensaje_exito="✓ DNI válido",
            debounce_ms=400
        )
    
    @staticmethod
    def _validar_dni(dni: str) -> Tuple[bool, Optional[str]]:
        """Validar formato DNI (8 dígitos + letra)."""
        import re
        
        if not re.match(r'^\d{8}[A-Z]$', dni):
            return False, "Formato inválido. Use: 12345678A"
        
        # Validar letra
        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        numero = int(dni[:8])
        letra_correcta = letras[numero % 23]
        
        if dni[8] != letra_correcta:
            return False, f"Letra incorrecta. Debería ser {letra_correcta}"
        
        return True, None

# Uso
campo_dni = QLineEdit()
label_dni = QLabel()
validador_dni = ValidadorDNI(campo_dni, label_dni)
```

### Ajustar Debouncing

```python
# Validación más rápida (200ms)
validador = ValidadorEmail(
    campo=campo_email,
    label_error=label_error
)
validador.debounce_ms = 200
validador.timer.setInterval(200)

# Validación más lenta (1000ms)
validador.debounce_ms = 1000
validador.timer.setInterval(1000)
```

---

## 🐛 Troubleshooting

### Problema: Validación no se ejecuta
**Causa**: Timer no conectado correctamente  
**Solución**: Verificar que `textChanged.connect()` esté llamado

### Problema: Labels de error no se ven
**Causa**: `maximumHeight` muy pequeño o layout comprimido  
**Solución**: Usar `crear_label_error()` helper o `setMaximumHeight(30)`

### Problema: Validación demasiado lenta
**Causa**: Debouncing muy alto  
**Solución**: Reducir `debounce_ms` a 200-300ms

### Problema: Tests fallan en CI
**Causa**: PyQt6 no disponible en headless  
**Solución**: Usar `QT_QPA_PLATFORM=offscreen` o marcar tests con `@pytest.mark.ui`

---

## 📊 Métricas de Calidad

### Coverage
```
validadores_ui.py:  71.72% (34 líneas sin cubrir de 129)
```

**Líneas No Cubiertas**:
- Algunos edge cases de timer
- Código de debug (no crítico)

### Performance
```
Tiempo ejecución tests: 1.99s (29 tests)
Promedio por test:      68ms
```

### Complejidad
```
ValidadorCampo:         Complejidad 5 (Baja)
ValidadorFormulario:    Complejidad 3 (Muy Baja)
Helpers:                Complejidad 1 (Trivial)
```

---

## 🎯 Próximos Pasos

### Inmediato (Task 8.7)
- [ ] Aplicar validadores a `ProfesorForm`
- [ ] Aplicar validadores a `ZonaForm`
- [ ] Aplicar validadores a `ConfiguracionForm`

### Corto Plazo
- [ ] Crear más validadores específicos:
  - `ValidadorTelefono`
  - `ValidadorCodigoPostal`
  - `ValidadorURL`
- [ ] Añadir tooltips con ayuda contextual
- [ ] Implementar validación asíncrona (check email duplicado en BD)

### Largo Plazo (v2.5+)
- [ ] Validación cruzada (campo A depende de campo B)
- [ ] Sugerencias de corrección automática
- [ ] Internacionalización de mensajes

---

## 📚 Referencias

### Patrones de Diseño Utilizados
- **Strategy Pattern**: Validadores intercambiables
- **Template Method**: `ValidadorCampo` define flujo, subclases implementan lógica
- **Composite**: `ValidadorFormulario` agrupa validadores

### Tecnologías
- **PyQt6**: Framework UI
- **QTimer**: Debouncing automático
- **Signals/Slots**: Reactividad en tiempo real
- **CSS Styling**: Feedback visual

### Documentación Relacionada
- `tests/README.md` - Guía de testing
- `utils/validators.py` - Validadores de negocio
- Sprint 8 Planning - `SPRINT_8_PLANIFICACION.md`

---

## ✅ Checklist de Implementación

- [x] Crear clase base `ValidadorCampo`
- [x] Implementar debouncing con QTimer
- [x] Crear estilos CSS para 3 estados
- [x] Implementar 4 validadores específicos
- [x] Crear `ValidadorFormulario` para validación completa
- [x] Crear helper functions
- [x] Escribir 29 tests (100% pasando)
- [x] Documentar uso y ejemplos
- [x] Verificar coverage >70%
- [ ] Aplicar a formularios existentes (Próximo: Task 8.7)

---

**Desarrollado por**: Equipo Guardias de Patio  
**Versión**: 1.0  
**Última actualización**: 19 de octubre de 2025  
**Estado**: ✅ COMPLETADO Y TESTEADO
