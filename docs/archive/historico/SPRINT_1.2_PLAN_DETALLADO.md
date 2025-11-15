# Sprint 1.2: División de Archivos Gigantes
## Plan Detallado de Ejecución

---

## 📊 ESTADO ACTUAL

- **Fecha inicio:** 1 de Noviembre de 2025
- **Progreso:** 20% (Análisis completado)
- **Archivos identificados:** 19 archivos >500 líneas
- **Prioridad:** configuracion_form.py (1935 líneas) y profesor_form.py (1389 líneas)

---

## 🎯 OBJETIVO DEL SPRINT

Dividir los 2 archivos de formularios más grandes para mejorar:
- ✅ Mantenibilidad (SRP)
- ✅ Testabilidad (widgets aislados)
- ✅ Reutilización (componentes independientes)
- ✅ Complejidad cognitiva (archivos <500 líneas)

**Meta:** Reducir ~3300 líneas en archivos gigantes

---

## 📦 TAREA 1: Dividir configuracion_form.py (1935 líneas)

### Análisis Completado ✅

**Estructura actual:**
```
configuracion_form.py (1935 líneas)
├─ Imports y setup (100 líneas)
├─ UI Widgets
│  ├─ Grupo Fechas (32 líneas)
│  ├─ Grupo Recreos Mañana (36 líneas)
│  ├─ Grupo Recreos Tarde (36 líneas)
│  ├─ Grupo Ajustes (49 líneas)
│  ├─ Grupo Festivos (28 líneas)
│  ├─ Grupo Perfil Usuario (56 líneas)
│  ├─ Grupo SMTP (138 líneas)
│  └─ Grupo SFTP (161 líneas)
├─ Métodos de negocio
│  ├─ Métodos SMTP (~300 líneas)
│  ├─ Métodos SFTP (~600 líneas)
│  └─ Métodos generales (~400 líneas)
└─ Total: 1935 líneas
```

### Plan de División

#### Paso 1.1: Crear estructura de directorios

```bash
mkdir -p src/presentation/forms/config_widgets
touch src/presentation/forms/config_widgets/__init__.py
```

#### Paso 1.2: Crear smtp_widget.py (~400 líneas)

**Archivo:** `src/presentation/forms/config_widgets/smtp_widget.py`

**Contenido a extraer de configuracion_form.py:**
- Líneas 411-549: `_crear_grupo_smtp()`
- Líneas 900-1100: Métodos SMTP
  - `cargar_smtp()`
  - `guardar_smtp()`
  - `probar_smtp()`
  - `_mostrar_advertencia_smtp_global()`

**Estructura del archivo:**
```python
"""
Widget de configuración SMTP para envío de emails.
"""

from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QCheckBox
)
from PyQt6.QtCore import pyqtSignal
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SMTPConfigWidget(QGroupBox):
    """
    Widget para configurar el servidor SMTP.
    
    Señales:
        config_changed: Emitida cuando cambia la configuración
        test_requested: Emitida cuando se solicita probar conexión
    """
    
    config_changed = pyqtSignal()
    test_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Configuración SMTP", parent)
        self._setup_ui()
        self.load_config()
    
    def _setup_ui(self):
        """Crea la interfaz del widget."""
        # ... código extraído de _crear_grupo_smtp()
    
    def load_config(self):
        """Carga configuración SMTP desde Settings."""
        # ... código extraído de cargar_smtp()
    
    def save_config(self) -> bool:
        """Guarda configuración SMTP en Settings."""
        # ... código extraído de guardar_smtp()
    
    def test_connection(self):
        """Prueba la conexión SMTP."""
        # ... código extraído de probar_smtp()
    
    def get_config_dict(self) -> dict:
        """Retorna configuración como diccionario."""
        return {
            'smtp_server': self.smtp_server_input.text(),
            'smtp_port': int(self.smtp_port_input.text()),
            'smtp_usuario': self.smtp_usuario_input.text(),
            'smtp_password': self.smtp_password_input.text(),
            'smtp_use_tls': self.smtp_tls_check.isChecked(),
        }
    
    def set_config_dict(self, config: dict):
        """Establece configuración desde diccionario."""
        # ... setear valores en inputs
```

**Comando para crear:**
```bash
# 1. Extraer código
# 2. Crear archivo
# 3. Importar en configuracion_form.py
# 4. Reemplazar código con widget
```

#### Paso 1.3: Crear sftp_widget.py (~650 líneas)

**Archivo:** `src/presentation/forms/config_widgets/sftp_widget.py`

**Contenido a extraer:**
- Líneas 550-711: `_crear_grupo_sftp()`
- Líneas 1100-1800: Métodos SFTP
  - `cargar_sftp()`
  - `guardar_sftp()`
  - `probar_sftp()`
  - `toggle_sftp_editable()`
  - `_mostrar_advertencia_sftp_global()`
  - `sincronizar_subida_sftp()`
  - `sincronizar_bajada_sftp()`

**Estructura:**
```python
"""
Widget de configuración y sincronización SFTP.
"""

from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QPushButton, 
    QLineEdit, QLabel, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, QThread
from sync.sync_manager import SyncManager
from utils.logger import get_logger

logger = get_logger(__name__)


class SFTPConfigWidget(QGroupBox):
    """
    Widget para configurar SFTP y sincronización.
    
    Señales:
        sync_started: Emitida cuando inicia sincronización
        sync_completed: Emitida cuando completa sincronización
        config_changed: Emitida cuando cambia configuración
    """
    
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(bool, str)  # success, message
    config_changed = pyqtSignal()
    
    def __init__(self, session, parent=None):
        super().__init__("Configuración SFTP", parent)
        self.session = session
        self._setup_ui()
        self.load_config()
    
    # ... métodos similares a SMTP
    # ... métodos de sincronización
```

#### Paso 1.4: Crear dates_recreos_widget.py (~250 líneas)

**Archivo:** `src/presentation/forms/config_widgets/dates_recreos_widget.py`

**Contenido a extraer:**
- Líneas 168-200: `_crear_grupo_fechas()`
- Líneas 201-237: `_crear_grupo_recreos_manana()`
- Líneas 238-274: `_crear_grupo_recreos_tarde()`
- Líneas 325-353: `_crear_grupo_festivos()`

**Estructura:**
```python
"""
Widget para configuración de fechas, recreos y festivos.
"""

class DatesRecreosWidget(QWidget):
    """
    Widget combinado para fechas del curso y configuración de recreos.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout()
        
        # Columna 1: Fechas y Festivos
        layout.addWidget(self._create_dates_group())
        
        # Columna 2: Recreos Mañana
        layout.addWidget(self._create_recreos_manana_group())
        
        # Columna 3: Recreos Tarde
        layout.addWidget(self._create_recreos_tarde_group())
        
        self.setLayout(layout)
    
    def get_config_dict(self) -> dict:
        """Retorna configuración como diccionario."""
        return {
            'fecha_inicio_curso': self.fecha_inicio.date().toPyDate(),
            'fecha_fin_curso': self.fecha_fin.date().toPyDate(),
            'hora_recreo1_manana': self.hora_recreo1_manana.time().toString(),
            # ... etc
        }
```

#### Paso 1.5: Crear ajustes_widget.py (~100 líneas)

**Archivo:** `src/presentation/forms/config_widgets/ajustes_widget.py`

**Contenido:**
- Líneas 275-324: `_crear_grupo_ajustes()`
- Selector de algoritmo

```python
"""
Widget para ajustes del sistema de guardias.
"""

class AjustesWidget(QGroupBox):
    """Widget para configuración de ajustes y algoritmo."""
    
    def __init__(self, parent=None):
        super().__init__("Ajustes del Sistema", parent)
        self._setup_ui()
    
    def get_config_dict(self) -> dict:
        return {
            'ajuste_tutores': float(self.ajuste_tutores.text()),
            'ajuste_no_tutores': float(self.ajuste_no_tutores.text()),
            'algoritmo_asignacion': self.algoritmo_combo.currentText(),
        }
```

#### Paso 1.6: Crear __init__.py

**Archivo:** `src/presentation/forms/config_widgets/__init__.py`

```python
"""
Widgets de configuración del sistema.
"""

from .smtp_widget import SMTPConfigWidget
from .sftp_widget import SFTPConfigWidget
from .dates_recreos_widget import DatesRecreosWidget
from .ajustes_widget import AjustesWidget

__all__ = [
    'SMTPConfigWidget',
    'SFTPConfigWidget',
    'DatesRecreosWidget',
    'AjustesWidget',
]
```

#### Paso 1.7: Refactorizar configuracion_form.py

**Reducir a ~400 líneas:**

```python
"""
Formulario principal de configuración.
Orquesta los widgets especializados.
"""

from presentation.forms.config_widgets import (
    SMTPConfigWidget,
    SFTPConfigWidget,
    DatesRecreosWidget,
    AjustesWidget,
)

class ConfiguracionForm(BaseForm):
    
    def __init__(self, session, parent=None):
        super().__init__(session, parent)
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        # Layout principal
        layout = QVBoxLayout()
        
        # Fila 1: Fechas y Recreos
        self.dates_recreos_widget = DatesRecreosWidget()
        layout.addWidget(self.dates_recreos_widget)
        
        # Fila 2: Ajustes y Perfil
        row2 = QHBoxLayout()
        self.ajustes_widget = AjustesWidget()
        row2.addWidget(self.ajustes_widget)
        row2.addWidget(self._create_perfil_group())
        layout.addLayout(row2)
        
        # Fila 3: SMTP y SFTP
        row3 = QHBoxLayout()
        self.smtp_widget = SMTPConfigWidget()
        self.sftp_widget = SFTPConfigWidget(self.session)
        row3.addWidget(self.smtp_widget)
        row3.addWidget(self.sftp_widget)
        layout.addLayout(row3)
        
        # Botones
        layout.addWidget(self._create_buttons())
        
        self.setLayout(layout)
    
    def load_config(self):
        """Carga configuración en todos los widgets."""
        config = self.obtener_config_uc.execute()
        
        if config:
            self.dates_recreos_widget.set_config_dict(config)
            self.ajustes_widget.set_config_dict(config)
    
    def save_config(self):
        """Guarda configuración de todos los widgets."""
        # Combinar configuración de todos los widgets
        config_dict = {
            **self.dates_recreos_widget.get_config_dict(),
            **self.ajustes_widget.get_config_dict(),
        }
        
        # Guardar SMTP y SFTP separadamente
        self.smtp_widget.save_config()
        self.sftp_widget.save_config()
        
        # Guardar configuración principal
        dto = ActualizarConfiguracionDTO(**config_dict)
        self.actualizar_config_uc.execute(dto)
```

### Comandos de Ejecución (Paso a Paso)

```bash
# 1. Crear estructura
mkdir -p src/presentation/forms/config_widgets
cd src/presentation/forms/config_widgets

# 2. Crear archivos vacíos
touch __init__.py smtp_widget.py sftp_widget.py \
      dates_recreos_widget.py ajustes_widget.py

# 3. Extraer código (manual o con scripts)
# Copiar secciones de configuracion_form.py a widgets correspondientes

# 4. Actualizar imports en configuracion_form.py

# 5. Ejecutar tests
pytest tests/ -q --tb=no -k configuracion

# 6. Verificar que no hay regresiones
pytest tests/ -q --tb=no
```

---

## 📦 TAREA 2: Dividir profesor_form.py (1389 líneas)

### Análisis Pendiente ⏳

**Estructura esperada:**
```
profesor_form.py (1389 líneas)
├─ Datos básicos widget
├─ Horario/disponibilidad widget
├─ Validaciones widget
└─ Form principal (orquestador)
```

**Estimación:** ~250 líneas por widget, ~300 líneas form principal

---

## 🧪 TESTING

### Tests a Ejecutar Después de Cada Widget

```bash
# 1. Tests específicos del formulario
pytest tests/test_configuracion_form.py -v

# 2. Tests de integración
pytest tests/ -k "configuracion" -v

# 3. Coverage del módulo
pytest tests/test_configuracion_form.py --cov=src/presentation/forms/config_widgets

# 4. Todos los tests (regresión)
pytest tests/ -q --tb=no
```

### Validación de Éxito

✅ 719+ tests pasando
✅ Sin errores de imports
✅ UI se carga correctamente
✅ Guardar/cargar funcionan
✅ SMTP/SFTP prueban conexión

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Antes | Objetivo | Medición |
|---------|-------|----------|----------|
| configuracion_form.py | 1935 líneas | <500 líneas | `wc -l` |
| Archivos gigantes | 19 | 17 | `find -name "*.py" -exec wc -l {} + | awk '$1 > 500'` |
| Tests pasando | 719 | 719+ | `pytest --co -q` |
| Coverage forms | 0% | 20% | `pytest --cov` |

---

## ⏱️ ESTIMACIÓN DE TIEMPO

| Tarea | Tiempo Estimado | Prioridad |
|-------|----------------|-----------|
| Crear smtp_widget.py | 1 hora | ALTA |
| Crear sftp_widget.py | 1.5 horas | ALTA |
| Crear dates_recreos_widget.py | 45 min | MEDIA |
| Crear ajustes_widget.py | 30 min | MEDIA |
| Refactorizar configuracion_form.py | 1 hora | ALTA |
| Testing y ajustes | 1 hora | ALTA |
| **TOTAL configuracion_form.py** | **5.5 horas** | |
| Dividir profesor_form.py | 3 horas | MEDIA |
| **TOTAL SPRINT 1.2** | **8-9 horas** | |

---

## 🎯 PRÓXIMA SESIÓN

**Comando para empezar:**
```bash
# Leer este documento
cat documentacion/SPRINT_1.2_PLAN_DETALLADO.md

# Ejecutar paso 1.1
mkdir -p src/presentation/forms/config_widgets
touch src/presentation/forms/config_widgets/__init__.py

# Empezar con smtp_widget.py (más fácil)
# Copiar líneas 411-549 y 900-1100 de configuracion_form.py
```

**Objetivos de la sesión:**
1. Crear smtp_widget.py ✅
2. Crear sftp_widget.py ✅  
3. Actualizar configuracion_form.py para usarlos ✅
4. Tests pasando ✅

**Reducción esperada:** 1935 → ~800 líneas (-58%)

---

## 📚 REFERENCIAS

- Documento base: `PLAN_REFACTORIZACION_V3.0.md`
- Sesión anterior: `RESUMEN_SESION_01NOV2025.md`
- Métricas: `./scripts/metrics_baseline.sh`
- Tests: `pytest tests/test_configuracion_form.py`

---

**Última actualización:** 1 de Noviembre de 2025, 15:45
**Estado:** Plan completado, listo para ejecución
**Próximo paso:** Crear smtp_widget.py
