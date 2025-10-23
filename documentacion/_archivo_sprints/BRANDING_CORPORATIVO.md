# Branding Corporativo - Logo en Modales

## 📋 Resumen

Se ha implementado de forma **discreta** el logo corporativo en todas las ventanas modales y diálogos de la aplicación, reemplazando el icono de Python por el logo corporativo ubicado en `imagenes/logo.png`.

## 🎯 Objetivo

Aplicar marca corporativa consistente en todos los `QMessageBox` (información, advertencias, errores, confirmaciones) sin necesidad de modificar cada archivo individualmente.

## 🔧 Implementación

### 1. **Módulo de Utilidades UI** (`src/utils/ui_helpers.py`)

Funciones helper para aplicar el logo corporativo:

```python
def get_corporate_icon() -> QIcon:
    """Obtiene el icono corporativo desde imagenes/logo.png"""

def show_info(parent, title, message)
def show_warning(parent, title, message)
def show_error(parent, title, message)
def show_question(parent, title, message, default_no=True) -> int
```

**Características:**
- ✅ Manejo de errores silencioso (fallback a icono por defecto si falla)
- ✅ Ruta relativa robusta desde cualquier ubicación
- ✅ API simple y consistente

### 2. **Monkey Patching Automático** (`src/utils/corporate_branding.py`)

Sistema de patching que aplica el logo corporativo a **TODOS** los `QMessageBox` de la aplicación automáticamente:

```python
def apply_corporate_branding():
    """Aplica branding corporativo interceptando exec() de QMessageBox"""
```

**Ventajas:**
- ✅ Un solo punto de configuración
- ✅ No requiere modificar archivos individuales
- ✅ Funciona con métodos estáticos (.information, .warning, .critical, .question)
- ✅ Aplicación transparente y discreta

### 3. **Actualización de BaseForm** (`src/presentation/forms/base_form.py`)

Los métodos de la clase base ahora aplican el logo corporativo:

```python
def mostrar_exito(titulo, mensaje)    # Usa get_corporate_icon()
def mostrar_error(titulo, mensaje)     # Usa get_corporate_icon()
def mostrar_advertencia(titulo, mensaje) # Usa get_corporate_icon()
def confirmar_accion(titulo, mensaje)  # Usa get_corporate_icon()
```

**Beneficios:**
- ✅ Todos los formularios que heredan de `BaseForm` obtienen el branding automáticamente
- ✅ Consistencia en toda la aplicación
- ✅ Mantenimiento centralizado

### 4. **Logo en Ventana Principal** (`src/main.py`)

La ventana principal también muestra el logo corporativo:

```python
class MainWindow(QWidget):
    def __init__(self):
        self.setWindowIcon(get_corporate_icon())
```

**Activación:**
```python
def main():
    app = QApplication(sys.argv)
    apply_corporate_branding()  # ← Activación global del branding
    window = MainWindow()
    window.show()
```

## 📊 Cobertura

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `src/utils/ui_helpers.py` | **NUEVO** - Funciones helper para UI |
| `src/utils/corporate_branding.py` | **NUEVO** - Sistema de monkey patching |
| `src/presentation/forms/base_form.py` | Actualizado - Usa `get_corporate_icon()` |
| `src/main.py` | Actualizado - Aplica branding en inicio |

### Archivos Beneficiados (sin modificar)

Gracias al monkey patching, **TODOS** estos archivos obtienen el branding automáticamente:

- ✅ `src/presentation/forms/profesor_form.py`
- ✅ `src/presentation/forms/asignacion_guardias_form.py`
- ✅ `src/presentation/forms/import_export_form.py`
- ✅ `src/presentation/widgets/gestionar_ausencias.py`
- ✅ `src/presentation/widgets/gestor_sustituciones.py`
- ✅ `src/widgets/gestionar_ausencias.py` (versión antigua)
- ✅ `src/widgets/gestionar_sustituciones.py` (versión antigua)
- ✅ Y cualquier archivo futuro que use `QMessageBox`

## 🎨 Diseño Discreto

La implementación es **discreta** porque:

1. **No invasiva**: No modifica código existente masivamente
2. **Silenciosa**: Fallos no interrumpen funcionalidad
3. **Transparente**: Los desarrolladores no necesitan cambiar su flujo de trabajo
4. **Escalable**: Nuevos diálogos obtienen branding automáticamente
5. **Profesional**: Logo aparece en barra de título, no en contenido del mensaje

## 🧪 Testing

Para probar el branding:

1. Ejecutar la aplicación: `./run_app.sh`
2. Abrir cualquier modal (ej: "Asignación de Guardias" → botón "Asignar")
3. Verificar que el icono de la ventana modal muestra el logo corporativo
4. Verificar que la ventana principal también muestra el logo

## 🔄 Mantenimiento

### Cambiar Logo

Para cambiar el logo corporativo:
1. Reemplazar `imagenes/logo.png` con el nuevo logo
2. Reiniciar la aplicación
3. ✅ Listo - se aplica automáticamente

### Desactivar Branding (temporal)

En `src/main.py`, comentar la línea:

```python
# apply_corporate_branding()  # Comentar para desactivar
```

### Restaurar Métodos Originales (para testing)

```python
from utils.corporate_branding import restore_original_methods
restore_original_methods()
```

## 📝 Notas Técnicas

- **Compatibilidad**: PyQt6
- **Formato logo**: PNG (también disponible .ico en `imagenes/`)
- **Ruta logo**: `imagenes/logo.png` (relativa a raíz del proyecto)
- **Tamaño recomendado**: 64x64 o 128x128 px
- **Transparencia**: Soportada (PNG con canal alpha)

## ✅ Resultado

Antes de esta implementación:
- 🔴 Modales mostraban icono de Python (cohete)

Después de esta implementación:
- ✅ Modales muestran logo corporativo
- ✅ Ventana principal muestra logo corporativo
- ✅ Marca corporativa consistente en toda la aplicación
- ✅ Implementación discreta y profesional

---

**Fecha de implementación:** 2024  
**Versión:** v2.6  
**Responsable:** Sistema de Guardias de Patio
