# Plan de Homogeneización Visual de Formularios

**Fecha:** 28 de octubre de 2025  
**Objetivo:** Igualar el patrón estético y visual de todos los formularios de la aplicación sin modificar su distribución ni lógica de negocio.

---

## 📊 Análisis del Estado Actual

### Formularios con Patrón Estándar (Correcto)
Los siguientes formularios **SÍ** siguen el patrón corporativo establecido:

1. **`profesor_form.py`** ✅
   - Usa `ui_styles.py` y `ccleaner_theme.py`
   - Títulos con `STYLE_TITLE_MAIN`
   - GroupBox con `STYLE_GROUPBOX`
   - Botones con `STYLE_BUTTON_PRIMARY`, `STYLE_BUTTON_DANGER`, etc.
   - Inputs con `STYLE_INPUT`
   - Labels con `STYLE_LABEL_FIELD`
   - Layout responsivo con Splitter
   - Tabla con estilos consistentes

2. **`zona_form.py`** ✅
   - Mismos patrones que profesor_form
   - Uso correcto de constantes de tema CCleaner

3. **`configuracion_form.py`** ✅
   - Uso correcto de estilos globales
   - Paleta de colores consistente

4. **`gestionar_ausencias.py`** ✅ (widget)
   - Patrón similar a los forms estándar

### Formularios con Estilos Inline (Inconsistentes) ❌

Los siguientes formularios **NO** siguen el patrón estándar y tienen estilos CSS inline:

1. **`import_export_form.py`** ❌
   - **Problema:** Estilos CSS inline en cada GroupBox y componente
   - **Colores custom:** `#3498db`, `#e67e22`, `#27ae60`, `#e74c3c`
   - **Sin usar:** `ui_styles.py` ni `ccleaner_theme.py`
   - **Emojis inconsistentes:** Uso excesivo en títulos

2. **`gestor_sustituciones.py`** ❌
   - **Problema:** Estilos CSS inline mezclados
   - **Colores custom:** `#3498db`, `#27ae60`, `#e74c3c`, `#ecf0f1`
   - **Mezcla de patrones:** Usa `QFont` directamente y estilos inline
   - **Emojis inconsistentes**

3. **`panel_estadisticas.py`** ❌
   - **Problema:** Estilos CSS inline básicos
   - **Uso limitado de tema:** No aprovecha el tema CCleaner
   - **Colores custom:** `#4CAF50`, `#e3f2fd`, `#90caf9`
   - **Emojis inconsistentes**

---

## 🎨 Patrón Estándar Definido

### Paleta de Colores Oficial
**Basada en:** `ccleaner_theme.py` y `ui_styles.py`

```python
# Colores principales
PRIMARY_BLUE = "#007ACC"       # Azul principal (botones, acentos)
SUCCESS_GREEN = "#28A745"      # Verde (éxito)
WARNING_ORANGE = "#FFC107"     # Naranja (advertencia)
ERROR_RED = "#DC3545"          # Rojo (peligro)

# Fondos
CONTENT_BG = "#FFFFFF"         # Fondo blanco
CONTENT_BG_ALT = "#F8F9FA"     # Fondo alternativo
BORDER_LIGHT = "#E1E4E8"       # Bordes claros
BORDER_MEDIUM = "#D1D5DB"      # Bordes normales

# Textos
TEXT_PRIMARY = "#1F2937"       # Texto principal
TEXT_SECONDARY = "#6B7280"     # Texto secundario
```

### Componentes Estandarizados

#### 1. Títulos Principales
```python
from ui_styles import STYLE_TITLE_MAIN

titulo = QLabel("📋 TÍTULO DEL FORMULARIO")
titulo.setStyleSheet(STYLE_TITLE_MAIN)
```

#### 2. GroupBox
```python
from ui_styles import STYLE_GROUPBOX

grupo = QGroupBox("📤 Título del Grupo")
grupo.setStyleSheet(STYLE_GROUPBOX)
```

#### 3. Botones
```python
from ui_styles import (
    STYLE_BUTTON_PRIMARY,
    STYLE_BUTTON_SUCCESS,
    STYLE_BUTTON_WARNING,
    STYLE_BUTTON_DANGER,
    STYLE_BUTTON_SECONDARY
)

# Botón principal
btn_principal = QPushButton("💾 Acción Principal")
btn_principal.setStyleSheet(STYLE_BUTTON_PRIMARY)

# Botón éxito
btn_exito = QPushButton("✅ Confirmar")
btn_exito.setStyleSheet(STYLE_BUTTON_SUCCESS)

# Botón peligro
btn_peligro = QPushButton("❌ Eliminar")
btn_peligro.setStyleSheet(STYLE_BUTTON_DANGER)
```

#### 4. Inputs
```python
from ui_styles import STYLE_INPUT, STYLE_LABEL_FIELD

label = QLabel("📅 Campo:")
label.setStyleSheet(STYLE_LABEL_FIELD)

input_field = QLineEdit()
input_field.setStyleSheet(STYLE_INPUT)
```

#### 5. Tablas
```python
from presentation.themes.ccleaner_theme import get_table_style

tabla = QTableWidget()
tabla.setStyleSheet(get_table_style())
```

---

## 🔧 Plan de Refactorización

### Fase 1: `import_export_form.py`

**Archivos a modificar:** `src/presentation/forms/import_export_form.py`

#### Cambios Específicos:

1. **Importar estilos globales**
   ```python
   import ui_styles as styles
   from presentation.themes.ccleaner_theme import (
       PRIMARY_BLUE, SUCCESS_GREEN, WARNING_ORANGE, ERROR_RED,
       CONTENT_BG_ALT, TEXT_SECONDARY
   )
   ```

2. **Reemplazar título principal**
   ```python
   # ANTES:
   titulo.setStyleSheet("""
       QLabel {
           font-size: 20px;
           font-weight: bold;
           color: #2c3e50;
           padding: 15px;
           background-color: #ecf0f1;
           border-radius: 8px;
       }
   """)
   
   # DESPUÉS:
   titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
   ```

3. **Reemplazar GroupBox de Exportar**
   ```python
   # ANTES: CSS inline con color #3498db
   grupo.setStyleSheet("""
       QGroupBox {
           font-weight: bold;
           font-size: 13px;
           border: 2px solid #3498db;
           border-radius: 8px;
           margin-top: 10px;
           padding-top: 15px;
           background-color: #ebf5fb;
       }
       ...
   """)
   
   # DESPUÉS:
   grupo.setStyleSheet(styles.STYLE_GROUPBOX)
   ```

4. **Reemplazar botones**
   ```python
   # ANTES: CSS inline para cada botón
   self.exportar_btn.setStyleSheet("""
       QPushButton {
           background-color: #3498db;
           color: white;
           ...
       }
   """)
   
   # DESPUÉS:
   self.exportar_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
   self.importar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
   self.importar_profesores_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
   self.exportar_pdf_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
   ```

5. **Reemplazar inputs (QComboBox, QTextEdit)**
   ```python
   # ANTES: CSS inline
   self.pdf_mes_combo.setStyleSheet("""
       QComboBox {
           padding: 6px;
           border: 1px solid #bdc3c7;
           ...
       }
   """)
   
   # DESPUÉS:
   self.pdf_mes_combo.setStyleSheet(styles.STYLE_INPUT)
   ```

6. **Estandarizar descripciones**
   ```python
   # DESPUÉS:
   desc.setStyleSheet(f"""
       color: {TEXT_SECONDARY};
       padding: 10px;
       font-size: 12px;
   """)
   ```

7. **Mantener distribución exacta**
   - ✅ No cambiar la estructura de layouts
   - ✅ No mover componentes de posición
   - ✅ Solo reemplazar estilos inline por constantes globales

---

### Fase 2: `gestor_sustituciones.py`

**Archivos a modificar:** `src/presentation/widgets/gestor_sustituciones.py`

#### Cambios Específicos:

1. **Importar estilos globales**
   ```python
   import ui_styles as styles
   from presentation.themes.ccleaner_theme import (
       PRIMARY_BLUE, SUCCESS_GREEN, ERROR_RED, TEXT_SECONDARY
   )
   ```

2. **Reemplazar título con QFont**
   ```python
   # ANTES:
   titulo = QLabel("🔄 Gestión de Sustituciones")
   titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
   titulo.setStyleSheet("""...""")
   
   # DESPUÉS:
   titulo = QLabel("🔄 GESTIÓN DE SUSTITUCIONES")
   titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
   ```

3. **Reemplazar GroupBox "Buscar Guardia"**
   ```python
   # ANTES: CSS inline con #3498db
   grupo_buscar.setStyleSheet("""...""")
   
   # DESPUÉS:
   grupo_buscar.setStyleSheet(styles.STYLE_GROUPBOX)
   ```

4. **Reemplazar botones**
   ```python
   # DESPUÉS:
   self.btn_buscar.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
   self.btn_confirmar_sustitucion.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
   self.btn_cancelar.setStyleSheet(styles.STYLE_BUTTON_DANGER)
   self.btn_buscar_disponibles.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
   ```

5. **Reemplazar inputs**
   ```python
   # DESPUÉS:
   self.fecha_buscar.setStyleSheet(styles.STYLE_INPUT)
   self.combo_profesor_original.setStyleSheet(styles.STYLE_INPUT)
   self.combo_profesor_sustituto.setStyleSheet(styles.STYLE_INPUT)
   self.text_observaciones.setStyleSheet(styles.STYLE_INPUT)
   ```

6. **Estandarizar labels de campo**
   ```python
   # DESPUÉS:
   fecha_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
   profesor_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
   ```

7. **Usar estilo de tabla estándar**
   ```python
   from presentation.themes.ccleaner_theme import get_table_style
   
   self.tabla_guardias.setStyleSheet(get_table_style())
   self.tabla_historial.setStyleSheet(get_table_style())
   ```

---

### Fase 3: `panel_estadisticas.py`

**Archivos a modificar:** `src/presentation/widgets/panel_estadisticas.py`

#### Cambios Específicos:

1. **Importar estilos globales**
   ```python
   import ui_styles as styles
   from presentation.themes.ccleaner_theme import (
       PRIMARY_BLUE, SUCCESS_GREEN, CONTENT_BG_ALT, TEXT_PRIMARY
   )
   ```

2. **Reemplazar título con QFont**
   ```python
   # ANTES:
   titulo = QLabel("📊 Estadísticas de Guardias")
   titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
   
   # DESPUÉS:
   titulo = QLabel("📊 ESTADÍSTICAS DE GUARDIAS")
   titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
   ```

3. **Reemplazar botón refrescar**
   ```python
   # ANTES: CSS inline con #4CAF50
   btn_refrescar.setStyleSheet("""
       QPushButton {
           background-color: #4CAF50;
           ...
       }
   """)
   
   # DESPUÉS:
   btn_refrescar.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
   ```

4. **Estandarizar tarjetas de métricas**
   ```python
   # ANTES:
   estilo_metrica = """
       background-color: #e3f2fd;
       padding: 15px;
       border-radius: 8px;
       border: 1px solid #90caf9;
   """
   
   # DESPUÉS:
   estilo_metrica = f"""
       QLabel {{
           background-color: {CONTENT_BG_ALT};
           padding: 15px;
           border-radius: 8px;
           border: 2px solid {PRIMARY_BLUE};
           font-size: 13px;
           font-weight: bold;
           color: {TEXT_PRIMARY};
       }}
   """
   ```

5. **Usar estilo de tabla estándar**
   ```python
   from presentation.themes.ccleaner_theme import get_table_style
   
   self.tabla_profesores.setStyleSheet(get_table_style())
   self.tabla_zonas.setStyleSheet(get_table_style())
   ```

6. **Mantener gráficos de matplotlib**
   - ✅ Los gráficos de matplotlib son funcionales
   - ✅ Solo ajustar colores a la paleta corporativa si es necesario
   ```python
   # Usar colores corporativos en gráficos
   self.canvas_profesores.axes.bar(nombres, cantidades, color=SUCCESS_GREEN)
   ```

---

## 📋 Checklist de Implementación

### Para cada archivo:

- [ ] **Importar módulos de estilos**
  ```python
  import ui_styles as styles
  from presentation.themes.ccleaner_theme import (...)
  ```

- [ ] **Reemplazar títulos principales**
  - [ ] Cambiar a `STYLE_TITLE_MAIN`
  - [ ] Texto en MAYÚSCULAS
  
- [ ] **Reemplazar GroupBox**
  - [ ] Cambiar a `STYLE_GROUPBOX`
  - [ ] Mantener emojis para claridad visual
  
- [ ] **Reemplazar botones**
  - [ ] Primarios → `STYLE_BUTTON_PRIMARY`
  - [ ] Éxito → `STYLE_BUTTON_SUCCESS`
  - [ ] Advertencia → `STYLE_BUTTON_WARNING`
  - [ ] Peligro → `STYLE_BUTTON_DANGER`
  - [ ] Secundarios → `STYLE_BUTTON_SECONDARY`
  
- [ ] **Reemplazar inputs**
  - [ ] QLineEdit → `STYLE_INPUT`
  - [ ] QDateEdit → `STYLE_INPUT`
  - [ ] QTimeEdit → `STYLE_INPUT`
  - [ ] QComboBox → `STYLE_INPUT`
  - [ ] QTextEdit → `STYLE_INPUT`
  
- [ ] **Reemplazar labels de campo**
  - [ ] Cambiar a `STYLE_LABEL_FIELD`
  
- [ ] **Reemplazar tablas**
  - [ ] Usar `get_table_style()`
  
- [ ] **Verificar responsividad**
  - [ ] No cambiar layouts
  - [ ] No mover componentes
  - [ ] Mantener distribución original

---

## 🎯 Resultado Esperado

### Beneficios:

1. **Homogeneidad Visual** ✨
   - Todos los formularios tendrán la misma apariencia
   - Colores consistentes en toda la aplicación
   - Tipografía uniforme

2. **Mantenibilidad** 🔧
   - Cambios globales desde un solo archivo (`ui_styles.py`)
   - Sin duplicación de código CSS
   - Fácil actualización de tema

3. **Profesionalismo** 💼
   - Apariencia corporativa moderna
   - Experiencia de usuario coherente
   - Identidad visual fuerte

4. **Sin Regresiones** ✅
   - Layout original intacto
   - Funcionalidad sin cambios
   - Lógica de negocio preservada

---

## 📝 Orden de Implementación Sugerido

1. **Primero:** `import_export_form.py` (más cambios, mayor impacto)
2. **Segundo:** `gestor_sustituciones.py` (impacto medio)
3. **Tercero:** `panel_estadisticas.py` (menor complejidad)

---

## 🧪 Testing Post-Implementación

### Pruebas Visuales:
- [ ] Verificar que todos los formularios se ven uniformes
- [ ] Comprobar que los colores coinciden con la paleta
- [ ] Validar que los tamaños de fuente son consistentes

### Pruebas Funcionales:
- [ ] Todas las operaciones CRUD funcionan
- [ ] Los botones responden correctamente
- [ ] Las tablas se actualizan
- [ ] Los inputs validan datos

### Pruebas de Responsividad:
- [ ] Redimensionar ventanas
- [ ] Verificar scrolls
- [ ] Comprobar splitters

---

## 📚 Referencias

- **Archivo de estilos:** `src/ui_styles.py`
- **Tema corporativo:** `src/presentation/themes/ccleaner_theme.py`
- **Formulario de referencia:** `src/presentation/forms/profesor_form.py`

---

**Última actualización:** 28 de octubre de 2025  
**Autor:** Asistente de Desarrollo  
**Estado:** Pendiente de implementación
