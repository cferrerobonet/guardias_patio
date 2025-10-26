# 🎨 Guía de Características de Interfaz de Usuario

**Versión:** 2.8+  
**Última actualización:** Octubre 2025

---

## 📋 Tabla de Contenidos

1. [Microsoft Fluent Design System](#microsoft-fluent-design-system)
2. [Validación de Resolución de Pantalla](#validación-de-resolución-de-pantalla)
3. [Comparativa UI Clásica vs Fluent](#comparativa-ui-clásica-vs-fluent)
4. [Guía de Personalización](#guía-de-personalización)
5. [Próximos Pasos](#próximos-pasos)

---

## 🎨 Microsoft Fluent Design System

La aplicación ha sido completamente rediseñada con un enfoque moderno inspirado en **Microsoft Fluent Design System**, similar a aplicaciones como Microsoft 365, Azure Portal, y Visual Studio Code.

### Arquitectura de la Nueva UI

#### **Antes** (Sistema de Pestañas)
```
┌────────────────────────────────────────┐
│ [Profesores] [Zonas] [Config] [...más]│ ← Pestañas horizontales
├────────────────────────────────────────┤
│                                        │
│          Contenido                     │
│                                        │
└────────────────────────────────────────┘
```

#### **Después** (Menú Lateral + Canvas)
```
┌─────────────────────────────────────────┐
│ 🏫 Guardias de Patio         [👤][⚙][❓]│  ← Barra superior
├─────────┬───────────────────────────────┤
│ GESTIÓN │ Gestión › Profesores          │  ← Breadcrumbs
│ 👨‍🏫 Prof.│                               │
│ 🏫 Zonas│   📝 Canvas de trabajo        │
│ ⚙️ Config                               │
│         │   (Contenido dinámico)        │
│ GUARDIAS│                               │
│ 🎯 Asig.│                               │
│ 📆 Cal. │                               │
│ 📊 Est. │                               │
└─────────┴───────────────────────────────┘
```

### Ventajas del Nuevo Diseño

| Aspecto | UI Clásica | UI Fluent |
|---------|-----------|-----------|
| **Navegación** | Pestañas horizontales | Menú lateral vertical |
| **Espacio vertical** | Limitado | Maximizado |
| **Breadcrumbs** | ❌ | ✅ |
| **Colapsable** | ❌ | ✅ |
| **Categorías** | ❌ | ✅ |
| **Iconos visuales** | Emojis simples | Emojis + texto |
| **Escalabilidad** | Baja (pestañas se saturan) | Alta (scroll en sidebar) |
| **Look moderno** | Básico | Microsoft 365 style |

---

## 🎨 Sistema de Diseño

### Paleta de Colores Microsoft Fluent

**Colores Primarios:**
```python
FLUENT_BLUE = "#0078D4"        # Acciones principales, enlaces
FLUENT_BLUE_HOVER = "#106EBE"  # Estado hover
FLUENT_BLUE_PRESSED = "#005A9E" # Estado pressed
```

**Colores Semánticos:**
```python
SUCCESS_GREEN = "#107C10"      # Éxito (verde Microsoft)
WARNING_ORANGE = "#CA5010"     # Advertencia
ERROR_RED = "#D13438"          # Error
```

**Escala de Grises Neutral:**
```python
NEUTRAL_LIGHT = "#F3F2F1"      # Fondo principal
NEUTRAL_WHITE = "#FFFFFF"      # Fondo cards
NEUTRAL_PRIMARY = "#201F1E"    # Texto principal
NEUTRAL_SECONDARY = "#605E5C"  # Texto secundario
```

### Tipografía Unificada

**Familia de fuente:**
```python
Segoe UI (Windows/macOS System Font)
Fallback: -apple-system, BlinkMacSystemFont, Roboto
```

**Jerarquía de tamaños:**
- **Display**: 32px (títulos grandes)
- **Title**: 20-24px (títulos de sección)
- **Subtitle**: 16-18px (subtítulos)
- **Body**: 14px (texto normal)
- **Caption**: 12px (texto pequeño, metadata)

**Pesos:**
- Regular: 400
- Semibold: 600
- Bold: 700

### Sistema de Espaciado (Grid de 8px)

```python
XS  = 4px   # Espacios muy pequeños
S   = 8px   # Espacios pequeños
M   = 12px  # Espacios medianos
L   = 16px  # Espacios grandes
XL  = 20px  # Espacios muy grandes
XXL = 24px  # Secciones
```

### Efectos Visuales

**Sombras (Depth):**
```css
/* Card normal */
box-shadow: 0 1px 3px rgba(0,0,0,0.12);

/* Card hover */
box-shadow: 0 3px 6px rgba(0,0,0,0.15);

/* Modal */
box-shadow: 0 6px 16px rgba(0,0,0,0.15);
```

**Border Radius:**
- Pequeño: 2px (checkboxes)
- Medio: 4px (botones, inputs)
- Grande: 8px (cards, panels)

**Scrollbars:**
- Estilo moderno delgado (12px)
- Color gris suave
- Hover más oscuro

---

## 🧩 Componentes Modernos

### 1. SidebarMenu - Menú Lateral

**Características:**
- Navegación por categorías
- Iconos + texto descriptivo
- Estado activo visual claro
- Colapsable (icono solo)
- Smooth hover/active states

**Ejemplo:**
```
┌───────────────────┐
│ 🏫 Guardias       │
│                   │
│ GESTIÓN           │
│ 👨‍🏫 Profesores    │  ← Hover: fondo gris claro
│ 🏫 Zonas          │  ← Activo: fondo azul claro
│ ⚙️ Configuración  │
│                   │
│ GUARDIAS          │
│ 🎯 Asignación     │
│ 📆 Calendario     │
│ 📊 Estadísticas   │
└───────────────────┘
```

**Archivo:** `src/presentation/components/sidebar_menu.py`

### 2. TopBar - Barra Superior

**Características:**
- Breadcrumbs dinámicos
- Acciones rápidas (usuario, config, ayuda)
- Diseño limpio y minimalista

**Ejemplo:**
```
┌──────────────────────────────────────┐
│ Gestión › Profesores    [👤] [⚙] [❓]│
└──────────────────────────────────────┘
```

**Archivo:** `src/presentation/components/top_bar.py`

### 3. Cards/Panels

**Características:**
- Fondos blancos con bordes sutiles
- Sombras suaves (depth effect)
- Border radius consistente (8px)
- Hover states elegantes

### 4. Botones

**Tipos:**
- **Primario**: Azul sólido (#0078D4)
- **Secundario**: Blanco con borde
- **Éxito**: Verde (#107C10)
- **Peligro**: Rojo (#D13438)
- Estados hover/pressed suaves

### 5. Inputs

**Características:**
- Bordes sutiles (#bdbdbd)
- Focus con borde azul (2px)
- Placeholder text con color secundario
- Height consistente (32px min)

---

## 📏 Validación de Resolución de Pantalla

La aplicación implementa un **sistema automático de validación** que previene la ejecución en pantallas que no cumplan con los requisitos mínimos.

### Requisitos de Resolución

```python
MIN_WIDTH = 1280          # Ancho mínimo requerido
MIN_HEIGHT = 720          # Alto mínimo requerido
RECOMMENDED_WIDTH = 1920  # Ancho recomendado
RECOMMENDED_HEIGHT = 1080 # Alto recomendado
```

### Comportamiento por Niveles

#### 🔴 Nivel Crítico: Resolución < 1280x720

**Comportamiento:**
- ❌ **La aplicación NO se ejecuta**
- Modal de error crítico con icono ⚠️
- Mensaje claro explicando el problema
- Botón "OK" que cierra la aplicación
- `sys.exit(1)` automático

**Ejemplo de pantalla afectada:**
- 1024x768 (XGA)
- 800x600 (SVGA)

**Mensaje mostrado:**
```
⚠️ Resolución de Pantalla Insuficiente

La resolución actual de tu pantalla es 1024x768 píxeles.

Para una correcta visualización de la aplicación, se requiere:

• Mínimo requerido: 1280x720 píxeles
• Recomendado: 1920x1080 píxeles o superior

La aplicación no se ejecutará para evitar una mala experiencia
de usuario con campos y textos que no se visualizan correctamente.

Por favor, ajusta la resolución de tu pantalla e intenta de nuevo.
```

#### ⚠️ Nivel Advertencia: 1280x720 ≤ Resolución < 1920x1080

**Comportamiento:**
- ⚠️ **La aplicación se puede ejecutar**
- Modal de advertencia con icono ℹ️
- Opción de continuar o cancelar
- Si usuario acepta (Yes) → continúa
- Si usuario cancela (No) → `sys.exit(0)`

**Ejemplo de pantalla afectada:**
- 1280x720 (HD 720p)
- 1366x768 (HD común en laptops)
- 1440x900 (WXGA+)

**Mensaje mostrado:**
```
ℹ️ Resolución por debajo de lo recomendado

Tu resolución actual es 1366x768 píxeles.

Aunque cumples con el mínimo requerido de 1280x720,
se recomienda una resolución de 1920x1080 o superior
para una mejor experiencia.

Algunos elementos de la interfaz podrían verse reducidos
o apretados.

¿Deseas continuar de todos modos?

[Sí] [No]
```

#### ✅ Nivel Óptimo: Resolución ≥ 1920x1080

**Comportamiento:**
- ✅ **La aplicación se ejecuta sin advertencias**
- No se muestra ningún modal
- Experiencia de usuario óptima garantizada

**Ejemplo de pantalla soportada:**
- 1920x1080 (Full HD) ✅
- 2560x1440 (2K QHD) ✅
- 3840x2160 (4K UHD) ✅

### Integración en la Aplicación

La validación se ejecuta **automáticamente al inicio** en `src/main.py`:

```python
def main() -> NoReturn:
    """Función principal de la aplicación."""
    # Smoke test para validación
    run_smoke_test()

    # Inicializar aplicación
    app = initialize_application()
    if not app:
        sys.exit(1)

    # ✨ VALIDACIÓN DE RESOLUCIÓN
    # Bloquea ejecución si resolución < 1280x720
    if not ScreenValidator.validate_resolution():
        ScreenValidator.show_resolution_warning()
        sys.exit(1)

    # Muestra advertencia si está por debajo de lo recomendado
    if not ScreenValidator.show_resolution_warning():
        sys.exit(0)

    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### Clase ScreenValidator

**Archivo:** `src/utils/screen_validator.py`

**Métodos principales:**
- `get_screen_resolution()` → Obtiene (ancho, alto) de la pantalla principal
- `validate_resolution()` → Valida si cumple requisitos mínimos
- `show_resolution_warning()` → Muestra modal apropiado
- `get_resolution_info()` → Info legible de la resolución actual

**Tests:** 14/14 passed (100%) - Cobertura 94%

---

## 🚀 Cómo Usar las UIs

### Ejecutar con UI Moderna Fluent:
```bash
python src/main_fluent.py
```

### Ejecutar con UI Clásica (pestañas):
```bash
python src/main.py
```

---

## 📦 Archivos Clave

### Sistema de Diseño Fluent

1. **`src/presentation/themes/fluent_theme.py`**
   - Sistema completo de colores Microsoft Fluent
   - Paletas, tipografía, espaciado
   - Funciones para generar stylesheets
   
2. **`src/presentation/components/sidebar_menu.py`**
   - Menú lateral moderno
   - Categorías, items, estados activos
   - Colapsable
   
3. **`src/presentation/components/top_bar.py`**
   - Barra superior con breadcrumbs
   - Botones de acciones rápidas
   
4. **`src/presentation/fluent_main_window.py`**
   - Ventana principal moderna
   - Integración de sidebar + topbar + content
   - Navegación por secciones (no pestañas)
   
5. **`src/main_fluent.py`**
   - Entry point para la UI moderna

### Validación de Resolución

1. **`src/utils/screen_validator.py`**
   - Clase ScreenValidator
   - Validación automática
   - Modales informativos

2. **`tests/utils/test_screen_validator.py`**
   - 14 tests unitarios
   - 94% cobertura
   - Casos críticos y edge cases

3. **`documentacion/REQUISITOS_SISTEMA.md`**
   - Requisitos completos de hardware
   - Sistemas operativos soportados
   - Solución de problemas

---

## 🎯 Guía de Personalización

### Cambiar Colores del Tema

Editar `src/presentation/themes/fluent_theme.py`:

```python
# Cambiar el azul Microsoft por tu color corporativo
FLUENT_BLUE = "#FF5733"  # Ejemplo: naranja corporativo
```

### Añadir Nueva Sección al Menú

En `src/presentation/fluent_main_window.py`:

```python
MenuItem(
    "mi_seccion",
    "Mi Sección",
    "🎨",
    lambda: self.show_widget("mi_seccion", ["Categoría", "Mi Sección"])
)
```

### Modificar Tipografía Base

```python
FONT_FAMILY_BASE = "Arial, sans-serif"  # Cambiar fuente
FONT_SIZE_14 = 16  # Aumentar tamaño base
```

### Ajustar Umbrales de Resolución

Si necesitas cambiar los requisitos mínimos:

```python
class ScreenValidator:
    MIN_WIDTH = 1024          # Bajar mínimo requerido
    MIN_HEIGHT = 768          # Bajar mínimo requerido
    RECOMMENDED_WIDTH = 1920  # Mantener recomendado
    RECOMMENDED_HEIGHT = 1080 # Mantener recomendado
```

### Deshabilitar Validación de Resolución

⚠️ **NO RECOMENDADO** - Puede causar mala experiencia de usuario

```python
# En src/main.py, comentar estas líneas:
# if not ScreenValidator.validate_resolution():
#     ScreenValidator.show_resolution_warning()
#     sys.exit(1)
```

---

## 📊 Métricas de Calidad UI

### Sistema Fluent Design

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Componentes creados** | 5 | ✅ |
| **Archivos de tema** | 1 | ✅ |
| **Paleta de colores** | 15+ colores | ✅ |
| **Sistema de espaciado** | Grid 8px | ✅ |
| **Compatibilidad** | macOS, Windows, Linux | ✅ |

### Validación de Resolución

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Tests escritos** | 14 | ✅ |
| **Tests pasados** | 14/14 (100%) | ✅ |
| **Cobertura de código** | 94.34% | ✅ |
| **Niveles de validación** | 3 (crítico, advertencia, óptimo) | ✅ |
| **Documentación** | 300+ líneas | ✅ |

---

## 🎯 Beneficios de las Características UI

### Para el Usuario Final

**Fluent Design:**
1. ✅ Navegación más clara e intuitiva
2. ✅ Breadcrumbs muestran ubicación actual
3. ✅ Más espacio vertical para formularios largos
4. ✅ Scroll independiente del menú
5. ✅ Look profesional Microsoft 365

**Validación de Resolución:**
1. ✅ No verá la app con campos cortados
2. ✅ Mensaje claro sobre qué hacer
3. ✅ Puede decidir continuar con resoluciones bajas

### Para el Desarrollador

**Fluent Design:**
1. ✅ Sistema de temas modular y reutilizable
2. ✅ Componentes bien documentados
3. ✅ Fácil personalización de colores
4. ✅ Escalable para nuevas secciones

**Validación de Resolución:**
1. ✅ Código limpio y testeable
2. ✅ 94% cobertura de tests
3. ✅ Fácil modificar umbrales
4. ✅ Integración sencilla (2 líneas)

### Para Soporte/Mantenimiento

**Fluent Design:**
1. ✅ Aspecto profesional reduce críticas
2. ✅ Componentes reutilizables facilitan cambios
3. ✅ Sistema consistente en toda la app

**Validación de Resolución:**
1. ✅ Reducción de tickets "la app se ve mal"
2. ✅ Mensajes claros reducen confusión
3. ✅ Documentación lista para compartir

---

## 🚀 Próximos Pasos

### Fluent Design

1. ✅ **Sistema de temas completo** - HECHO
2. ✅ **Menú lateral moderno** - HECHO
3. ✅ **Barra superior con breadcrumbs** - HECHO
4. ✅ **Nueva ventana principal** - HECHO
5. 🔄 **Adaptar formularios con nuevo estilo** - En progreso
6. ⏳ **Dark mode** - Planificado
7. ⏳ **Animaciones suaves** - Planificado
8. ⏳ **Iconos SVG personalizados** - Planificado

### Validación de Resolución

1. ✅ **Validación básica** - HECHO
2. ✅ **Tests completos** - HECHO
3. ✅ **Documentación** - HECHO
4. ⏳ **Validación de DPI/Scaling** - Planificado
5. ⏳ **Soporte Multi-Monitor** - Planificado
6. ⏳ **Modo Compacto** - Planificado

---

## 📚 Documentación Relacionada

- **[REQUISITOS_SISTEMA.md](REQUISITOS_SISTEMA.md)** - Requisitos completos de hardware y software
- **[ARQUITECTURA.md](ARQUITECTURA.md)** - Arquitectura general de la aplicación
- **[README.md](../README.md)** - Documentación principal del proyecto

---

**Creado con** 💙 **Microsoft Fluent Design System**  
**Última actualización:** 26 de Octubre de 2025  
**Versión:** 2.8+  
**Estado:** ✅ Producción - Estable
