# 🧭 PLAN INTEGRAL DE REFACTORIZACIÓN Y MEJORA CONTINUA

## Aplicación: Guardias de Patio (Python + SQLite + PyQt6)

---

## 🎯 OBJETIVO GENERAL

Optimizar y estabilizar una aplicación Python con base de datos SQLite, que ya dispone de una arquitectura funcional, reforzando su calidad técnica, mantenibilidad y escalabilidad.

El propósito es **mejorar sin romper**, garantizando cumplimiento de buenas prácticas, trazabilidad, testeo, seguridad y documentación profesional.

---

## � ANÁLISIS DEL ESTADO ACTUAL

### ✅ Lo que YA está implementado (NO refactorizar)

La aplicación ya tiene implementadas muchas buenas prácticas:

#### Arquitectura
- ✅ **Clean Architecture** bien definida (`domain/`, `application/`, `infrastructure/`, `presentation/`)
- ✅ **Use Cases** implementados con cache inteligente (12 Use Cases)
- ✅ **DTOs con Pydantic 2.0** para validación automática
- ✅ **Patrón Repository** con SQLAlchemy 2.0

#### Calidad y Observabilidad
- ✅ **Logging estructurado** (`src/core/logging.py`) con structlog
- ✅ **Sistema de métricas** (`src/core/observability/`) con Prometheus
- ✅ **Performance monitoring** con decoradores
- ✅ **Health checks** implementados

#### Testing
- ✅ **843 tests** colectados (buena cobertura)
- ✅ **pytest** configurado con plugins (qt, cov, mock)
- ✅ **conftest.py** con fixtures

#### Configuración
- ✅ **Pydantic Settings** ya implementado
- ✅ **python-dotenv** para variables de entorno
- ✅ **pyproject.toml** con ruff y mypy configurados

#### Base de Datos
- ✅ **Alembic** configurado para migraciones
- ✅ **SQLAlchemy 2.0** (versión moderna)

### ⚠️ Lo que SÍ necesita atención

#### Problemas Detectados
1. **Carpeta `/ui` duplicada** - Solo 2 archivos (sync dialogs), consolidar en `/presentation`
2. **Archivo obsoleto** - `restricciones_widget_old.py` (517 líneas sin usar)
3. **Test roto** - `test_calendario_guardias_form.py` (importa módulo inexistente)
4. **Documentación dispersa** - 30+ archivos markdown en `/documentacion`
5. **Sin CI/CD** - No hay GitHub Actions configurado
6. **Cobertura no medida** - Tests existen pero sin reporte de cobertura

#### Mejoras de Valor
1. Limpiar archivos obsoletos (mínimo impacto, máximo valor)
2. Consolidar documentación (15 archivos vs 30+)
3. Configurar CI/CD básico (automatizar lo que ya funciona)
4. Medir y reportar cobertura (mostrar el buen trabajo ya hecho)

---

## 📋 ÍNDICE DE FASES (AJUSTADO)

1. [Diagnóstico y Limpieza Inicial](#fase-1) ⚡ *Rápido*
2. [Consolidación de Código](#fase-2) ⚡ *Rápido*
3. [Tests: Arreglar y Medir](#fase-3) 🎯 *Alto valor*
4. [Documentación: Consolidar y Simplificar](#fase-4) 🎯 *Alto valor*
5. [CI/CD Básico](#fase-5) 🎯 *Alto valor*
6. [Seguridad y Cumplimiento](#fase-6) 🔒 *Importante*
7. [Experiencia de Usuario (UX)](#fase-7) 🎨 *Mejora usabilidad*
8. [Mantenimiento Continuo](#fase-8) 🔄 *Sostenibilidad*

**Fases ELIMINADAS del plan original** (ya implementadas o innecesarias):
- ~~Fase 2 original: Arquitectura~~ → Ya está bien implementada
- ~~Fase 3 original: Herramientas~~ → Ya están configuradas (ruff, mypy, pytest)
- ~~Fase 4 original: Base de datos~~ → Alembic ya funciona, SQLAlchemy 2.0 OK
- ~~Fase 5 original: Tipado y Logging~~ → Ya implementado con structlog
- ~~Fase 8 original: Configuración~~ → Pydantic Settings ya funciona
- ~~Fase 12 original: Rendimiento~~ → Ya tiene monitoring y métricas

---

## <a name="fase-1"></a>1️⃣ FASE 1 – Diagnóstico y Limpieza Inicial

### 🎯 Objetivo
Identificar y eliminar archivos obsoletos, duplicados y tests rotos sin valor.

### 📝 Acciones

#### 1.1 Auditoría Rápida de Archivos Obsoletos
```bash
# Buscar archivos con sufijos obsoletos
find src/ -name "*_old.py" -o -name "*_backup.py" -o -name "*_test.py"

# Resultado esperado:
# src/presentation/forms/profesor_widgets/restricciones_widget_old.py (517 líneas)
```

**Acción**: Eliminar `restricciones_widget_old.py` - ya hay versión actualizada

#### 1.2 Consolidar Carpeta `/ui` Duplicada
```bash
# Contenido actual de src/ui:
# - dialogs/session_locked_dialog.py
# - widgets/sync_progress_dialog.py

# Mover a src/presentation/dialogs/ (donde corresponde)
mv src/ui/dialogs/session_locked_dialog.py src/presentation/dialogs/
mv src/ui/widgets/sync_progress_dialog.py src/presentation/widgets/

# Actualizar imports en archivos que los usen
rg "from ui.dialogs" src/
rg "from ui.widgets" src/

# Eliminar carpeta vacía
rm -rf src/ui/
```

#### 1.3 Arreglar Test Roto
```bash
# Test que falla:
# tests/test_calendario_guardias_form.py
# Error: ModuleNotFoundError: No module named 'presentation.forms.calendario_guardias_form'

# Opciones:
# A) Si el formulario existe con otro nombre → actualizar import
# B) Si el formulario no existe → eliminar test obsoleto
```

#### 1.4 Auditoría de Documentación
```bash
# Contar archivos markdown
find documentacion/ -name "*.md" | wc -l
# Resultado: ~30+ archivos

# Listar por tipo
tree documentacion/ -L 2
```

### 📦 Entregables
- ✅ `restricciones_widget_old.py` eliminado
- ✅ Carpeta `/ui` consolidada en `/presentation`
- ✅ Test roto arreglado o eliminado
- ✅ Lista de archivos de documentación a consolidar
- ✅ `documentacion/auditoria/limpieza_fase1.md` con resumen

### ⏱️ Estimación
**1 día** (4-6 horas efectivas)

---

## <a name="fase-2"></a>2️⃣ FASE 2 – Consolidación de Código

### 🎯 Objetivo
Mejorar consistencia sin romper la arquitectura ya buena.

### 📝 Acciones

#### 2.1 Verificar Violaciones Arquitectónicas (si existen)
```bash
# Verificar que domain no importe infrastructure
grep -r "from infrastructure" src/domain/ || echo "✅ Domain limpio"

# Verificar que domain no importe presentation
grep -r "from presentation" src/domain/ || echo "✅ Domain limpio"

# Verificar que application solo use puertos
grep -r "from infrastructure" src/application/ | grep -v "ports" || echo "✅ Application limpio"
```

**Si NO hay violaciones** → Documentar y seguir.
**Si hay violaciones** → Listar y planificar correcciones puntuales.

#### 2.2 Actualizar Diagrama de Arquitectura
```bash
# Generar diagrama actualizado con pyreverse
pip install pylint
pyreverse -o png -p guardias_patio src/
mv classes_guardias_patio.png documentacion/diagramas/arquitectura_actual.png
```

#### 2.3 Documentar Arquitectura Real
```markdown
# documentacion/ARCHITECTURE.md

## Estructura Actual

src/
├── domain/              # ✅ Entidades, Value Objects, Reglas de negocio
│   ├── entities/
│   ├── value_objects/
│   └── repositories/    # Interfaces (Protocols)
├── application/         # ✅ Use Cases con cache, DTOs con Pydantic
│   ├── use_cases/
│   └── dtos/
├── infrastructure/      # ✅ Repos SQLAlchemy, Mappers, DB
│   ├── repositories/
│   └── mappers/
├── presentation/        # ✅ PyQt6 Forms, Widgets, Dialogs
│   ├── forms/
│   ├── widgets/
│   └── dialogs/
├── core/                # ✅ Logging, Observability, Config
│   ├── logging.py
│   └── observability/
└── services/            # ⚠️ Revisar si pertenecen a application/

## Dependencias

✅ domain → (nada)
✅ application → domain
✅ infrastructure → domain, application
✅ presentation → application (no domain directamente)
✅ services → ¿? (analizar)
```

### 📦 Entregables
- ✅ `documentacion/ARCHITECTURE.md` con estructura real
- ✅ Diagrama de arquitectura actualizado
- ✅ Lista de violaciones (si existen) con plan de corrección
- ✅ Verificación de que la arquitectura actual es sólida

### ⏱️ Estimación
**1 día**

---

## <a name="fase-3"></a>3️⃣ FASE 3 – Tests: Arreglar y Medir

### 🎯 Objetivo
Hacer que los 843 tests existentes pasen 100% y medir cobertura real.

### 📝 Acciones

#### 3.1 Arreglar Tests Rotos
```bash
# Ejecutar tests y capturar errores
pytest --tb=short -v > documentacion/auditoria/test_failures.txt 2>&1

# Arreglar uno por uno (empezar por los más fáciles)
# Prioridad: imports rotos, fixtures faltantes, mocks desactualizados
```

#### 3.2 Medir Cobertura Real
```bash
# Ejecutar tests con cobertura
pytest --cov=src --cov-report=html --cov-report=term-missing

# Generar reporte legible
coverage html
open htmlcov/index.html

# Exportar métricas
coverage json -o documentacion/auditoria/coverage.json
```

#### 3.3 Identificar Gaps de Cobertura
```bash
# Ver módulos con <80% cobertura
coverage report --skip-covered

# Documentar gaps
coverage report --show-missing > documentacion/auditoria/coverage_gaps.txt
```

#### 3.4 NO Escribir Tests Nuevos (a menos que sea crítico)
La app ya tiene 843 tests. El objetivo es **hacer que funcionen**, no añadir más.

### 📦 Entregables
- ✅ **100% de tests pasando** (843/843)
- ✅ Reporte de cobertura HTML en `htmlcov/`
- ✅ Badge de cobertura en README
- ✅ `documentacion/TESTING.md` actualizado con:
  - Cómo ejecutar tests
  - Interpretación de cobertura
  - Gaps conocidos (si existen)

### ⏱️ Estimación
**2-3 días**

---

## <a name="fase-4"></a>4️⃣ FASE 4 – Documentación: Consolidar y Simplificar

### 🎯 Objetivo
Reducir de 30+ archivos markdown a 12-15 archivos principales bien organizados.

### 📝 Acciones

#### 4.1 Plan de Consolidación

**Archivos a MANTENER (12 archivos principales):**
```
documentacion/
├── README.md                    # Índice general
├── ARCHITECTURE.md              # Arquitectura (recién creado en Fase 2)
├── DEVELOPMENT.md               # Setup, instalación, comandos
├── TESTING.md                   # Guía de testing (actualizado en Fase 3)
├── DEPLOYMENT.md                # Build, distribución, instalación
├── USER_GUIDE.md                # Manual de usuario
├── CHANGELOG.md                 # Historial de versiones
├── CONTRIBUTING.md              # Guía de contribución
├── SECURITY.md                  # Políticas de seguridad
├── PREMISAS_ASIGNACION.md       # Reglas de negocio (ya existe)
├── API_REFERENCE.md             # Referencia API (generado)
└── MAINTENANCE.md               # Guía de mantenimiento
```

**Carpetas auxiliares:**
```
documentacion/
├── auditoria/           # Reportes de auditorías
├── diagramas/           # Diagramas técnicos
└── ejemplos/            # Ejemplos de uso
```

**Archivos/Carpetas a CONSOLIDAR O ELIMINAR:**
```bash
# Consolidar en DEVELOPMENT.md:
- desarrollo/
- guias/
- tecnico/ (parte técnica)

# Consolidar en DEPLOYMENT.md:
- build/
- BUILD_WINDOWS.md

# Consolidar en CHANGELOG.md:
- versiones/
- CALENDARIO_MEJORADO_v3.md (versiones antiguas)

# Consolidar en USER_GUIDE.md:
- funcionalidades/

# ARCHIVAR fuera de Git:
- archivo/
- roadmap/ (mover a GitHub Issues/Projects)
- LIMPIEZA_NOV_2025.md (temporal, ya completado)

# Consolidar en DEPLOYMENT.md:
- sftp/ (configuración)
```

#### 4.2 Ejecutar Consolidación
```bash
# Script de consolidación
bash scripts/consolidate_docs.sh

# O manualmente:
# 1. Crear nuevos archivos principales
# 2. Copiar contenido relevante
# 3. Mover archivos obsoletos a documentacion/archivo/
# 4. Actualizar enlaces en README.md
```

#### 4.3 Generar Documentación API
```bash
# Con pdoc (más simple)
pip install pdoc
pdoc src/ -o documentacion/api/ --html

# Resultado: documentacion/api/index.html
```

#### 4.4 Actualizar README Principal
```markdown
# README.md (raíz del proyecto)

## 📚 Documentación

### Para Usuarios
- 📖 [Guía de Usuario](documentacion/USER_GUIDE.md)
- 🚀 [Instalación](documentacion/DEPLOYMENT.md)

### Para Desarrolladores
- 🏗️ [Arquitectura](documentacion/ARCHITECTURE.md)
- 💻 [Desarrollo](documentacion/DEVELOPMENT.md)
- 🧪 [Testing](documentacion/TESTING.md)
- 📘 [API Reference](documentacion/api/index.html)

### Operaciones
- 🚀 [Despliegue](documentacion/DEPLOYMENT.md)
- 🔧 [Mantenimiento](documentacion/MAINTENANCE.md)
- 🔒 [Seguridad](documentacion/SECURITY.md)

### Referencia
- 📋 [Premisas de Asignación](documentacion/PREMISAS_ASIGNACION.md)
- 📜 [Changelog](documentacion/CHANGELOG.md)
- 🤝 [Contribuir](documentacion/CONTRIBUTING.md)
```

### 📦 Entregables
- ✅ 12 archivos markdown principales (vs 30+ originales)
- ✅ `documentacion/README.md` como índice claro
- ✅ Carpetas `desarrollo/`, `guias/`, `tecnico/`, etc. consolidadas
- ✅ Documentación API generada
- ✅ README principal actualizado con estructura clara
- ✅ Archivos obsoletos archivados o eliminados

### ⏱️ Estimación
**2 días**

---

## <a name="fase-5"></a>5️⃣ FASE 5 – CI/CD Básico

### 🎯 Objetivo
Automatizar lo que ya funciona: tests, linting, coverage.

### 📝 Acciones

#### 5.1 GitHub Actions: Tests y Coverage
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-qt
      
      - name: Run tests
        run: pytest --cov=src --cov-report=xml --cov-report=term-missing
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

#### 5.2 GitHub Actions: Linting
```yaml
# .github/workflows/lint.yml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install ruff mypy
      
      - name: Lint with ruff
        run: ruff check src/
      
      - name: Type check with mypy
        run: mypy src/ --config-file=pyproject.toml
        continue-on-error: true  # No bloquear por warnings de tipos
```

#### 5.3 Badges en README
```markdown
# README.md

[![Tests](https://github.com/usuario/guardias_patio/workflows/Tests/badge.svg)](https://github.com/usuario/guardias_patio/actions)
[![Coverage](https://codecov.io/gh/usuario/guardias_patio/branch/main/graph/badge.svg)](https://codecov.io/gh/usuario/guardias_patio)
[![Lint](https://github.com/usuario/guardias_patio/workflows/Lint/badge.svg)](https://github.com/usuario/guardias_patio/actions)
```

#### 5.4 Configurar Branch Protection (GitHub Settings)
```yaml
main:
  require_pull_request: true
  required_status_checks:
    - test (ubuntu-latest, 3.11)
    - test (macos-latest, 3.11)
    - lint
  require_linear_history: true
```

### 📦 Entregables
- ✅ `.github/workflows/tests.yml` funcional
- ✅ `.github/workflows/lint.yml` funcional
- ✅ Badges en README mostrando estado
- ✅ Branch protection configurado
- ✅ Codecov integrado (opcional)

### ⏱️ Estimación
**1 día**

---

## <a name="fase-6"></a>6️⃣ FASE 6 – Seguridad y Cumplimiento

### 🎯 Objetivo
Auditorías de seguridad y protección de datos sensibles.

### 📝 Acciones

#### 6.1 Auditoría de Dependencias
```bash
# Instalar herramientas
pip install pip-audit bandit safety

# Auditar vulnerabilidades
pip-audit > documentacion/auditoria/pip_audit.txt

# Análisis de código con Bandit
bandit -r src/ -f json -o documentacion/auditoria/bandit.json
bandit -r src/ -ll  # Solo medium/high severity

# Safety check
safety check --json > documentacion/auditoria/safety.json
```

#### 6.2 Verificar Secretos NO en Git
```bash
# Verificar .gitignore
cat .gitignore | grep -E "\.env|\.db|\.sqlite|logs/" || echo "⚠️ Añadir a .gitignore"

# Buscar secretos hardcodeados
grep -r "password\s*=\s*['\"]" src/ --include="*.py" || echo "✅ Sin contraseñas"
grep -r "api_key\s*=\s*['\"]" src/ --include="*.py" || echo "✅ Sin API keys"

# Verificar que archivos sensibles no están en Git
git ls-files | grep -E "\.env$|\.db$|\.sqlite$" || echo "✅ Sin archivos sensibles"
```

#### 6.3 Documento de Seguridad
```markdown
# documentacion/SECURITY.md

## 🔒 Política de Seguridad

### Versiones Soportadas
| Versión | Soportada |
|---------|-----------|
| 3.x.x   | ✅        |
| < 3.0   | ❌        |

### Reportar Vulnerabilidad
Email: seguridad@example.com (NO abrir issue público)

### Auditorías
Ejecutar auditoría:
\`\`\`bash
pip-audit
bandit -r src/ -ll
\`\`\`

### Mejores Prácticas
- ✅ Usar variables de entorno para secretos
- ✅ No commitear `.env` o `.db`
- ✅ Actualizar dependencias mensualmente
- ✅ Ejecutar `pip-audit` antes de releases
```

#### 6.4 GitHub Actions: Security Audit
```yaml
# .github/workflows/security.yml
name: Security

on:
  schedule:
    - cron: '0 0 * * 1'  # Semanal, lunes a medianoche
  workflow_dispatch:

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pip-audit bandit
      
      - name: Audit dependencies
        run: pip-audit
        continue-on-error: true
      
      - name: Run Bandit
        run: bandit -r src/ -f json -o bandit-report.json
        continue-on-error: true
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: bandit-report.json
```

### 📦 Entregables
- ✅ `documentacion/SECURITY.md` completo
- ✅ Auditorías ejecutadas (pip-audit, bandit, safety)
- ✅ `.gitignore` actualizado
- ✅ GitHub Actions para auditoría semanal
- ✅ Sin vulnerabilidades críticas

### ⏱️ Estimación
**1 día**

---

## <a name="fase-7"></a>7️⃣ FASE 7 – Experiencia de Usuario (UX)

### 🎯 Objetivo
Mejorar la usabilidad sin alterar lógica de negocio ni layouts drásticos.

**Contexto**: La aplicación ya tiene elementos UX básicos (tooltips, placeholders, TableManager, progress indicators). Esta fase los **extiende** y añade ayuda contextual basada en el TODO list actual.

### 📝 Acciones

#### 7.1. Auditoría de Formularios Actuales
**Revisar Use Cases y sus formularios asociados**:

```bash
# Listar formularios complejos
find src/presentation/forms -name "*.py" -exec wc -l {} + | sort -rn | head -10

# Identificar campos sin tooltip
grep -r "QLineEdit\|QComboBox\|QSpinBox" src/presentation/forms --include="*.py" | \
  grep -v "setToolTip" > ux_audit_no_tooltips.txt

# Revisar confirmaciones actuales
grep -r "QMessageBox.question" src/presentation --include="*.py" -n
```

**Salida**: Crear `documentacion/UX_AUDIT.md`:
```markdown
## Formularios Prioritarios

### 1. Restricciones Widget ⚠️ (en mejora según TODO)
**Problema**: 5 botones redundantes
- "Aplicar a este día" → Redundante si hay auto-save
- "Limpiar este día" → Usar checkboxes directamente

**Solución**: 
- ✅ Auto-guardado al cambiar checkboxes
- ✅ Mantener solo "Aplicar a todos" y "Limpiar todo"
- ✅ Feedback visual "✓ Guardado automáticamente"

### 2. Calendario Guardias ⚠️
**Problema**: Click en tabla recarga datos innecesariamente
**Solución**: Auto-save al cambiar de día seleccionado

### 3. Gestión Ausencias ✅
**Estado**: Ya tiene buenos tooltips y placeholders

### 4. Configuración Curso
**Mejora**: Añadir iconos de ayuda "?" junto a campos complejos
```

#### 7.2. Mejoras de Ayuda Contextual
**Implementación SIN alterar lógica**:

**A. Tooltips Informativos Extendidos**
```python
# src/presentation/forms/profesor_widgets/horario_widget.py

# ANTES (ya existe algo así)
self.horas_input.setPlaceholderText("Ej: 30.0")

# DESPUÉS (expandir con más contexto)
self.horas_input.setToolTip(
    "Horas de contrato semanal\n"
    "📘 Rango típico: 18-25 horas\n"
    "💡 Tutores: suelen tener 21-22h"
)
self.horas_input.setPlaceholderText("Ej: 22.0 (tutores típico)")
```

**B. Labels con Iconos de Ayuda**
```python
# src/presentation/widgets/help_icon.py (NUEVO)
from PyQt6.QtWidgets import QPushButton, QMessageBox
from PyQt6.QtCore import QSize

class HelpIcon(QPushButton):
    """Icono de ayuda '?' junto a labels complejos."""
    
    def __init__(self, help_text: str, parent=None):
        super().__init__("?", parent)
        self.help_text = help_text
        self.setMaximumSize(QSize(20, 20))
        self.setToolTip("Click para ver ayuda")
        self.clicked.connect(self.show_help)
    
    def show_help(self):
        QMessageBox.information(self, "Ayuda", self.help_text)

# USO en formularios:
from presentation.widgets.help_icon import HelpIcon

layout.addWidget(QLabel("Ajuste Tutores:"))
layout.addWidget(HelpIcon(
    "Factor de ajuste para tutores.\n\n"
    "Valores < 1.0 reducen guardias asignadas.\n"
    "Ejemplo: 0.90 = 10% menos guardias"
))
layout.addWidget(self.ajuste_tutores_input)
```

**C. Status Bar con Contexto**
```python
# En formularios complejos (profesor_form.py, zona_form.py, etc.)

def _setup_statusbar(self):
    """Configurar mensajes de ayuda en status bar."""
    if hasattr(self.parent(), 'statusBar'):
        self.statusbar = self.parent().statusBar()
    else:
        self.statusbar = None

def on_table_selection_changed(self):
    """Mostrar hint en status bar al seleccionar."""
    if self.statusbar:
        if self.table.currentRow() >= 0:
            self.statusbar.showMessage(
                "💡 Doble-click para editar | Del para eliminar", 
                3000
            )
        else:
            self.statusbar.clearMessage()
```

**D. Confirmaciones Inteligentes** (revisar según TODO)
```python
# Eliminar debe SIEMPRE confirmar (OK, ya existe)
def _eliminar_clicked(self):
    respuesta = QMessageBox.question(
        self,
        "Confirmar eliminación",
        "¿Eliminar este registro?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if respuesta == QMessageBox.StandardButton.Yes:
        self._do_delete()

# Cancelar SOLO confirma si hay cambios pendientes
def _cancelar_clicked(self):
    if self._form_has_changes():
        respuesta = QMessageBox.question(
            self,
            "Cambios sin guardar",
            "Hay cambios sin guardar. ¿Descartar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.No:
            return
    
    self._clear_form()  # Sin recargar tabla innecesariamente

def _form_has_changes(self) -> bool:
    """Detectar si hay cambios pendientes."""
    if not hasattr(self, '_original_data'):
        return False
    
    current = self._get_form_data()
    return current != self._original_data
```

#### 7.3. Auto-save en Matriz Restricciones
**Implementar según TODO list**:

```python
# src/presentation/forms/profesor_widgets/restricciones_widget.py

class RestriccionesWidget(QWidget):
    """Widget de restricciones con auto-save."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_save_enabled = True
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save)
        
        self._setup_ui()
        self._setup_status_indicator()
    
    def _setup_status_indicator(self):
        """Indicador de guardado automático."""
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green; font-size: 10px;")
        # Añadir al layout principal
    
    def on_checkbox_changed(self, state):
        """Checkbox cambió → Auto-save con debouncing."""
        if self._auto_save_enabled:
            # Debouncing: esperar 300ms antes de guardar
            self._save_timer.start(300)
            self.show_saving_indicator()
    
    def _do_save(self):
        """Guardar estado en memoria/BD."""
        try:
            # Guardar restricciones...
            self._save_restrictions_to_state()
            self.show_saved_indicator()
        except Exception as e:
            self.show_error_indicator(str(e))
    
    def show_saved_indicator(self):
        """Mostrar feedback de guardado."""
        self.status_label.setText("✓ Guardado automáticamente")
        self.status_label.setStyleSheet("color: green;")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))
    
    def show_saving_indicator(self):
        """Mostrar feedback de guardando..."""
        self.status_label.setText("💾 Guardando...")
        self.status_label.setStyleSheet("color: orange;")
```

**Eliminar botones redundantes**:
```python
# ANTES (5 botones según TODO)
# - "Aplicar a este día" → ELIMINAR (auto-save)
# - "Aplicar a todos" → MANTENER
# - "Limpiar este día" → ELIMINAR (usar checkboxes)
# - "Limpiar todo" → MANTENER

# DESPUÉS (2 botones + auto-save)
self.aplicar_todos_btn = QPushButton("Aplicar a todos los días")
self.limpiar_todo_btn = QPushButton("Limpiar todas las restricciones")
# Auto-save reemplaza "Aplicar a este día"
```

#### 7.4. Atajos de Teclado Documentados
**Extender atajos existentes**:

```python
# src/presentation/forms/base_form.py (o en cada form)

def _setup_shortcuts(self):
    """Configurar atajos de teclado."""
    QShortcut(QKeySequence("Ctrl+S"), self, self.guardar)
    QShortcut(QKeySequence("Ctrl+N"), self, self.nuevo)
    QShortcut(QKeySequence("Esc"), self, self.cancelar)
    QShortcut(QKeySequence("F5"), self, self.refresh)
    QShortcut(QKeySequence("Ctrl+F"), self, self.buscar)
    
    # Actualizar tooltips de botones con shortcuts
    self.guardar_btn.setToolTip("Guardar cambios (Ctrl+S)")
    self.nuevo_btn.setToolTip("Nuevo registro (Ctrl+N)")
    self.refresh_btn.setToolTip("Recargar datos (F5)")
```

**Documento de atajos**:
```markdown
# documentacion/guias/KEYBOARD_SHORTCUTS.md

## Atajos de Teclado

### Globales
- `Ctrl+S` - Guardar
- `Ctrl+N` - Nuevo registro
- `Esc` - Cancelar operación
- `F5` - Refrescar datos
- `Ctrl+F` - Buscar

### En Tablas
- `Enter` o `Doble Click` - Editar selección
- `Del` - Eliminar selección
- `Flechas` - Navegar registros
```

#### 7.5. Documentación de Patrones UX
**Crear guía para futuras mejoras**:

```markdown
# documentacion/guias/UX_PATTERNS.md

# Patrones UX de Guardias de Patio

## 🎯 Principios

1. **Feedback Inmediato**: Toda acción debe tener respuesta visual
2. **Auto-save cuando sea posible**: Menos clics, menos fricción
3. **Confirmaciones solo para destructivas**: No molestar innecesariamente
4. **Tooltips informativos**: Descripción + contexto + ejemplo

## 📋 Checklist de UX para Nuevos Formularios

- [ ] Todos los campos tienen `placeholder` o `tooltip` informativo
- [ ] Atajos de teclado documentados en tooltips (ej: "Guardar (Ctrl+S)")
- [ ] Status bar muestra hints contextuales
- [ ] Auto-save implementado para operaciones no-críticas
- [ ] Confirmación solo en acciones destructivas (eliminar)
- [ ] Feedback visual en operaciones largas (progress indicators)
- [ ] Focus management (después de guardar, focus en campo principal)

## 🎨 Formato de Tooltips

```python
campo.setToolTip(
    "Descripción breve del campo\n"
    "📘 Info adicional o rango válido\n"
    "💡 Tip o valor recomendado"
)
```

## 🔔 Confirmaciones

### ✅ SIEMPRE confirmar:
- Eliminar registros
- Limpiar datos masivamente
- Sobrescribir datos existentes

### ❌ NO confirmar:
- Cancelar sin cambios
- Refrescar datos
- Navegar entre registros (con auto-save)

### ⚠️ Confirmar SOLO si hay cambios:
- Cancelar con cambios pendientes
- Cerrar ventana con edición activa

## 💾 Auto-save

### Cuándo usar:
- Checkboxes de configuración (ej: matriz restricciones)
- Campos de preferencias
- Navegación entre días/registros

### Cuándo NO usar:
- Datos críticos (profesores, zonas)
- Operaciones con validación compleja

### Implementación con debouncing:
```python
self._save_timer = QTimer()
self._save_timer.setSingleShot(True)
self._save_timer.timeout.connect(self._do_save)

def on_field_changed(self):
    self._save_timer.start(300)  # Esperar 300ms
```

## 🎨 Feedback Visual

| Estado | Color | Icono | Ejemplo |
|--------|-------|-------|---------|
| Success | Verde | ✓ | "✓ Guardado automáticamente" |
| Error | Rojo | ✗ | "✗ Error al guardar" |
| Warning | Naranja | ⚠️ | "⚠️ Campo obligatorio" |
| Info | Azul | ℹ️ | "ℹ️ Doble-click para editar" |
| Loading | Naranja | 💾 | "💾 Guardando..." |
```

### 📦 Entregables
- ✅ `documentacion/UX_AUDIT.md` con análisis de formularios
- ✅ `documentacion/guias/UX_PATTERNS.md` con patrones y guidelines
- ✅ `documentacion/guias/KEYBOARD_SHORTCUTS.md` con atajos documentados
- ✅ Mejoras del TODO list implementadas:
  - Auto-save en matriz restricciones
  - Simplificación de botones (5→2 + auto-save)
  - Navegación mejorada entre días
- ✅ ≥80% de campos con tooltip o placeholder informativo
- ✅ Status bar con hints contextuales en formularios principales
- ✅ Confirmaciones inteligentes (solo cuando necesarias)

### ⏱️ Estimación
**2-3 días**

**Priorización**:
1. **Alta**: Auto-save indicators + Navegación mejorada (según TODO) - **1 día**
2. **Media**: Tooltips/placeholders extendidos + Help icons - **1 día**
3. **Baja**: Documentación UX_PATTERNS + Shortcuts - **0.5 días**

### ⚠️ NO Hacer (Evitar Scope Creep)
- ❌ Rediseño visual completo
- ❌ Cambio de framework UI (mantener PyQt6)
- ❌ Reorganización de layouts complejos
- ❌ Sistema de onboarding (tours, walkthroughs)
- ❌ Animaciones elaboradas
- ❌ Cambios en lógica de negocio o use cases

---

## <a name="fase-8"></a>8️⃣ FASE 8 – Mantenimiento Continuo

### 🎯 Objetivo
Establecer procesos recurrentes para mantener la calidad.

### 📝 Acciones

#### 7.1 Script de Mantenimiento Semanal
```bash
# scripts/weekly_maintenance.sh
#!/bin/bash

echo "🔧 Mantenimiento Semanal - $(date)"
echo "================================="

# 1. Actualizar dependencias
echo "📦 Dependencias outdated:"
pip list --outdated

# 2. Ejecutar tests
echo "🧪 Ejecutando tests..."
pytest --quiet

# 3. Coverage
echo "📊 Cobertura actual:"
pytest --cov=src --cov-report=term --quiet | grep "TOTAL"

# 4. Linting
echo "🔍 Linting:"
ruff check src/ | wc -l | xargs echo "Warnings:"

# 5. Métricas de BD
echo "💾 Tamaño BD:"
ls -lh data/*.db 2>/dev/null || echo "Sin BD"

echo "✅ Mantenimiento completado"
```

#### 7.2 Documento de Mantenimiento
```markdown
# documentacion/MAINTENANCE.md

## 🔧 Guía de Mantenimiento

### Tareas Semanales
- [ ] Ejecutar `./scripts/weekly_maintenance.sh`
- [ ] Revisar issues y PRs en GitHub
- [ ] Verificar logs de CI/CD

### Tareas Mensuales
- [ ] Actualizar dependencias: `pip list --outdated`
- [ ] Ejecutar auditorías: `pip-audit`
- [ ] Backup completo de datos

### Tareas Trimestrales
- [ ] Revisión completa de documentación
- [ ] Análisis de cobertura de tests
- [ ] Planificación de nuevas features

### Comandos Útiles
\`\`\`bash
# Tests
pytest

# Coverage
pytest --cov=src --cov-report=html

# Lint
ruff check src/

# Type check
mypy src/

# Audit
pip-audit
\`\`\`
```

#### 7.3 Configurar Cron Job (opcional, local)
```bash
# crontab -e

# Mantenimiento semanal (domingos a las 2 AM)
0 2 * * 0 cd /path/to/guardias_patio && ./scripts/weekly_maintenance.sh >> logs/maintenance.log 2>&1
```

### 📦 Entregables
- ✅ `scripts/weekly_maintenance.sh` funcional
- ✅ `documentacion/MAINTENANCE.md` con guía clara
- ✅ Checklists para diferentes frecuencias
- ✅ Proceso documentado y repetible

### ⏱️ Estimación
**0.5 días**

---

## <a name="fase-2"></a>2️⃣ FASE 2 – Revisión y Consolidación de Arquitectura

### 🎯 Objetivo
Confirmar que la arquitectura es coherente, modular y extensible.

### 🏗️ Estructura Actual vs Recomendada

#### Estructura Actual
```
src/
├── application/     # DTOs y lógica de aplicación
├── domain/          # Entidades y lógica de negocio
├── infrastructure/  # Repositorios, mappers, DB
├── models/          # Modelos SQLAlchemy
├── presentation/    # UI PyQt6
├── services/        # Servicios de aplicación
├── sync/            # Sincronización SFTP
└── ui/              # ¿Duplicado con presentation?
```

#### Estructura Recomendada (Clean Architecture / Hexagonal)
```
src/
├── domain/          # Lógica de negocio pura (sin dependencias externas)
│   ├── entities/
│   ├── value_objects/
│   └── rules/
├── application/     # Casos de uso, puertos y contratos
│   ├── use_cases/
│   ├── dtos/
│   └── ports/       # Interfaces (Protocols)
├── infrastructure/  # Implementaciones de puertos
│   ├── persistence/ # Repositorios SQLAlchemy
│   ├── mappers/     # Conversión Model ↔ Entity
│   └── external/    # SFTP, exportadores
├── presentation/    # Interfaz de usuario
│   ├── forms/
│   ├── widgets/
│   └── windows/
└── shared/          # Utilidades compartidas
    ├── config/
    ├── logging/
    ├── errors/
    └── utils/
```

### 📝 Acciones

#### 2.1 Análisis de Dependencias entre Capas
```bash
# Detectar importaciones que violan arquitectura
# domain NO debe importar infrastructure ni presentation
grep -r "from infrastructure" src/domain/ || echo "✅ Domain limpio"
grep -r "from presentation" src/domain/ || echo "✅ Domain limpio"

# application NO debe importar infrastructure (solo ports)
grep -r "from infrastructure" src/application/ | grep -v "ports" || echo "✅ Application limpio"
```

#### 2.2 Validación de Contratos
- Verificar que repositorios implementan `Protocol` de `application.ports`
- Confirmar que no hay lógica de negocio en `infrastructure`
- Validar que `presentation` solo depende de `application` (no de `domain` directamente)

#### 2.3 Consolidación de Módulos Duplicados
- **Identificar**: `src/ui/` vs `src/presentation/` → unificar
- **Analizar**: Funciones duplicadas entre módulos
- **Consolidar**: Mover a `shared/` lo común

#### 2.4 Diagramas de Arquitectura
```bash
# Generar diagrama de dependencias
pydeps src --only src -o documentacion/diagramas/dependencias.png

# O manualmente con pyreverse
pyreverse -o png -p guardias_patio src/
```

### 📦 Entregables
- ✅ `documentacion/ARCHITECTURE.md` actualizado
- ✅ Diagrama de capas y flujo de datos
- ✅ Diagrama de dependencias entre módulos
- ✅ Lista de violaciones arquitectónicas a corregir
- ✅ Plan de consolidación de módulos duplicados

### ⏱️ Estimación
**3-4 días**

---

## <a name="fase-3"></a>3️⃣ FASE 3 – Estándares de Código y Herramientas de Control

### 🎯 Objetivo
Garantizar coherencia, legibilidad y control automatizado de calidad.

### 📝 Acciones

#### 3.1 Configurar `pyproject.toml`
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "C90", "I", "N", "UP", "B", "A", "C4", "SIM", "PL"]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --cov=src --cov-report=term-missing"
testpaths = ["tests"]
pythonpath = ["."]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:"
]
```

#### 3.2 Crear `Makefile`
```makefile
.PHONY: fmt lint typecheck test audit clean install help

help:  ## Mostrar ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Instalar dependencias
	pip install -e .[dev]

fmt:  ## Formatear código
	ruff format .
	black .

lint:  ## Analizar código
	ruff check .

typecheck:  ## Verificar tipos
	mypy src/

test:  ## Ejecutar tests
	pytest

test-cov:  ## Tests con cobertura HTML
	pytest --cov=src --cov-report=html

audit:  ## Auditoría de seguridad
	bandit -r src/
	pip-audit

clean:  ## Limpiar archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

all: fmt lint typecheck test audit  ## Ejecutar todos los checks
```

#### 3.3 Configurar `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, src/, -ll]
```

#### 3.4 Activar Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Prueba inicial
```

#### 3.5 Actualizar `.gitignore`
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Database
*.db
*.sqlite
*.sqlite3
data/*.db
!data/.gitkeep

# Logs
logs/
*.log

# Environment
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/
*.spec

# Documentation
documentacion/auditoria/
```

### 📦 Entregables
- ✅ `pyproject.toml` completo y funcional
- ✅ `.pre-commit-config.yaml` configurado
- ✅ `Makefile` con comandos de control
- ✅ `.env.example` con variables de configuración
- ✅ `.gitignore` actualizado
- ✅ Pre-commit hooks activados

### ⏱️ Estimación
**2 días**

---

## <a name="fase-4"></a>4️⃣ FASE 4 – Gestión de Base de Datos (SQLite)

### 🎯 Objetivo
Optimizar persistencia, rendimiento y preparación para migraciones futuras.

### 📝 Acciones

#### 4.1 Optimizar Conexión SQLite
```python
# src/infrastructure/persistence/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configurar PRAGMAs de SQLite para optimizar rendimiento"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")        # Integridad referencial
    cursor.execute("PRAGMA journal_mode=WAL")       # Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")     # Balance rendimiento/seguridad
    cursor.execute("PRAGMA temp_store=MEMORY")      # Tablas temp en RAM
    cursor.execute("PRAGMA mmap_size=30000000000")  # Memory-mapped I/O
    cursor.execute("PRAGMA page_size=4096")         # Tamaño de página
    cursor.close()
```

#### 4.2 Revisar y Crear Índices
```bash
# Analizar queries lentas
sqlite3 data/guardias.db "EXPLAIN QUERY PLAN SELECT * FROM profesores WHERE activo = 1;"

# Crear índices necesarios
sqlite3 data/guardias.db "CREATE INDEX IF NOT EXISTS idx_profesores_activo ON profesores(activo);"
sqlite3 data/guardias.db "CREATE INDEX IF NOT EXISTS idx_guardias_fecha ON guardias(fecha);"
```

#### 4.3 Implementar Patrón Repository
```python
# src/application/ports/repository.py
from typing import Protocol, TypeVar, Generic, Optional, List
from domain.entities import Entity

T = TypeVar('T', bound=Entity)

class Repository(Protocol, Generic[T]):
    """Contrato de repositorio genérico"""
    
    def add(self, entity: T) -> T:
        """Agregar entidad"""
        ...
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Obtener por ID"""
        ...
    
    def list_all(self) -> List[T]:
        """Listar todas"""
        ...
    
    def update(self, entity: T) -> T:
        """Actualizar entidad"""
        ...
    
    def delete(self, id: int) -> bool:
        """Eliminar por ID"""
        ...
```

#### 4.4 Configurar Alembic (Migraciones)
```bash
# Inicializar Alembic (si no existe)
alembic init alembic

# Configurar para SQLite con modo batch
# alembic/env.py: render_as_batch=True
```

```python
# alembic/env.py
def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Necesario para SQLite
    )
```

#### 4.5 Script de Mantenimiento
```python
# scripts/maintain_sqlite.py
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

def maintain_database(db_path: Path) -> None:
    """Mantener base de datos SQLite"""
    
    # Backup
    backup_dir = Path("data/backups")
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"guardias_backup_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    
    # Mantenimiento
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # VACUUM: Reconstruir DB y liberar espacio
    print("🔧 Ejecutando VACUUM...")
    cursor.execute("VACUUM")
    
    # ANALYZE: Actualizar estadísticas del query optimizer
    print("📊 Ejecutando ANALYZE...")
    cursor.execute("ANALYZE")
    
    # Verificar integridad
    print("🔍 Verificando integridad...")
    result = cursor.execute("PRAGMA integrity_check").fetchone()
    if result[0] == "ok":
        print("✅ Integridad OK")
    else:
        print(f"⚠️ Problemas de integridad: {result}")
    
    conn.commit()
    conn.close()
    
    # Limpiar backups antiguos (mantener últimos 10)
    backups = sorted(backup_dir.glob("guardias_backup_*.db"))
    for old_backup in backups[:-10]:
        old_backup.unlink()
        print(f"🗑️ Eliminado backup antiguo: {old_backup.name}")

if __name__ == "__main__":
    maintain_database(Path("data/guardias.db"))
```

### 📦 Entregables
- ✅ `src/infrastructure/persistence/database.py` con PRAGMAs optimizados
- ✅ Índices creados y documentados
- ✅ `src/application/ports/repository.py` con contratos
- ✅ Carpeta `alembic/` configurada con modo batch
- ✅ `scripts/maintain_sqlite.py` funcional
- ✅ Documentación de esquema en `documentacion/DATABASE.md`

### ⏱️ Estimación
**3-4 días**

---

## <a name="fase-5"></a>5️⃣ FASE 5 – Tipado, Errores y Logging

### 🎯 Objetivo
Mejorar trazabilidad, robustez y detección de fallos mediante tipado estricto y logging estructurado.

### 📝 Acciones

#### 5.1 Activar Tipado Estricto con MyPy
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reoptional = true

# Configuración por módulo (gradual)
[[tool.mypy.overrides]]
module = "domain.*"
disallow_untyped_defs = true
disallow_any_explicit = true

[[tool.mypy.overrides]]
module = "application.*"
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "infrastructure.*"
warn_return_any = false  # Más flexible con SQLAlchemy

[[tool.mypy.overrides]]
module = "PyQt6.*"
ignore_missing_imports = true
```

#### 5.2 Crear Jerarquía de Errores
```python
# src/shared/errors.py
"""
Jerarquía de excepciones de la aplicación.
Todas las excepciones personalizadas heredan de AppError.
"""
from typing import Optional, Dict, Any


class AppError(Exception):
    """Excepción base de la aplicación"""
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


# Errores de Dominio
class DomainError(AppError):
    """Error en lógica de negocio"""
    pass


class ValidationError(DomainError):
    """Error de validación de datos"""
    pass


class BusinessRuleViolation(DomainError):
    """Violación de regla de negocio"""
    pass


# Errores de Aplicación
class ApplicationError(AppError):
    """Error en capa de aplicación"""
    pass


class UseCaseError(ApplicationError):
    """Error en caso de uso"""
    pass


# Errores de Infraestructura
class InfrastructureError(AppError):
    """Error en capa de infraestructura"""
    pass


class RepositoryError(InfrastructureError):
    """Error en repositorio"""
    pass


class DatabaseError(InfrastructureError):
    """Error de base de datos"""
    pass


class ExternalServiceError(InfrastructureError):
    """Error en servicio externo (SFTP, etc.)"""
    pass


# Errores de Presentación
class PresentationError(AppError):
    """Error en capa de presentación"""
    pass


class FormValidationError(PresentationError):
    """Error de validación de formulario"""
    pass
```

#### 5.3 Implementar Logging Estructurado
```python
# src/shared/logging.py
"""
Configuración de logging estructurado para la aplicación.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """Formatter que genera logs en formato JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Agregar campos extra si existen
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "elapsed_ms"):
            log_data["elapsed_ms"] = record.elapsed_ms
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Agregar excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False
) -> None:
    """
    Configurar logging de la aplicación.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta del archivo de log (opcional)
        json_format: Si True, usa formato JSON estructurado
    """
    # Remover handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configurar nivel
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Formato
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para archivo (si se especifica)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Silenciar logs de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("paramiko").setLevel(logging.WARNING)


# Logger para uso en módulos
def get_logger(name: str) -> logging.Logger:
    """Obtener logger con el nombre del módulo"""
    return logging.getLogger(name)
```

#### 5.4 Reemplazar `print()` por `logging`
```bash
# Buscar todos los print() en el código
grep -r "print(" src/ --include="*.py" > documentacion/auditoria/print_statements.txt

# Revisar y reemplazar manualmente por logger.info/debug/warning/error
```

```python
# ANTES
print(f"Guardando profesor: {nombre}")
print(f"Error al conectar: {e}")

# DESPUÉS
logger = get_logger(__name__)
logger.info("Guardando profesor", extra={"nombre": nombre})
logger.error("Error al conectar", exc_info=True, extra={"error": str(e)})
```

#### 5.5 Agregar Context Managers para Tracking
```python
# src/shared/logging.py (continuación)
import time
import uuid
from contextlib import contextmanager
from typing import Generator


@contextmanager
def log_operation(
    operation_name: str,
    logger: logging.Logger,
    **context
) -> Generator[dict, None, None]:
    """
    Context manager para trackear operaciones con timing.
    
    Usage:
        with log_operation("guardar_profesor", logger, profesor_id=123) as ctx:
            # hacer operación
            ctx["rows_affected"] = 5
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    ctx = {"request_id": request_id}
    
    logger.info(
        f"Iniciando: {operation_name}",
        extra={"request_id": request_id, **context}
    )
    
    try:
        yield ctx
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Completado: {operation_name}",
            extra={
                "request_id": request_id,
                "elapsed_ms": round(elapsed_ms, 2),
                **context,
                **ctx
            }
        )
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Error en: {operation_name}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "elapsed_ms": round(elapsed_ms, 2),
                "error": str(e),
                **context
            }
        )
        raise
```

### 📦 Entregables
- ✅ `src/shared/errors.py` con jerarquía completa de excepciones
- ✅ `src/shared/logging.py` con logging estructurado
- ✅ `pyproject.toml` actualizado con configuración MyPy estricta
- ✅ Todos los `print()` reemplazados por `logger.*`
- ✅ Context managers para tracking de operaciones
- ✅ Documentación en `documentacion/LOGGING.md`

### ⏱️ Estimación
**3-4 días**

---

## <a name="fase-6"></a>6️⃣ FASE 6 – Sistema de Pruebas Unitarias e Integración

### 🎯 Objetivo
Asegurar el correcto funcionamiento de la aplicación con cobertura adecuada y diferentes tipos de tests.

### 📊 Objetivos de Cobertura

| Tipo de Test | Capa | Cobertura Objetivo |
|--------------|------|-------------------|
| **Unitarias** | Domain | 100% |
| **Unitarias** | Application | ≥95% |
| **Integración** | Infrastructure | ≥85% |
| **Integración** | Presentation | ≥70% |
| **E2E** | Flujos completos | Críticos |

### 📝 Acciones

#### 6.1 Estructurar Carpeta de Tests
```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartidas
├── unit/                    # Tests unitarios (sin DB, sin UI)
│   ├── __init__.py
│   ├── domain/
│   │   ├── test_entities.py
│   │   ├── test_value_objects.py
│   │   └── test_business_rules.py
│   └── application/
│       ├── test_use_cases.py
│       └── test_dtos.py
├── integration/             # Tests con DB, archivos, SFTP
│   ├── __init__.py
│   ├── infrastructure/
│   │   ├── test_repositories.py
│   │   ├── test_mappers.py
│   │   └── test_database.py
│   └── services/
│       ├── test_exportador.py
│       └── test_sync_manager.py
├── e2e/                     # Tests end-to-end
│   ├── __init__.py
│   └── test_flujos_principales.py
└── fixtures/                # Datos de prueba
    ├── profesores.json
    ├── guardias.json
    └── test.db
```

#### 6.2 Configurar Fixtures en `conftest.py`
```python
# tests/conftest.py
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.models import Base
from datetime import date


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory) -> Path:
    """Base de datos temporal para tests"""
    return tmp_path_factory.mktemp("data") / "test.db"


@pytest.fixture(scope="session")
def engine(test_db_path):
    """Motor de BD para tests"""
    engine = create_engine(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine) -> Session:
    """Sesión de BD con rollback automático"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def profesor_dto_valido():
    """DTO de profesor válido para tests"""
    from application.dtos.profesor_dto import ProfesorDTO
    
    return ProfesorDTO(
        nombre_completo="Test Profesor",
        activo=True,
        zona_preferida_id=None,
        dias_semana_permitidos=[0, 1, 2, 3, 4],
        recreos_permitidos={0: [1, 2, 3, 4]},
        fecha_inicio_guardias=date.today(),
        fecha_fin_guardias=None
    )


@pytest.fixture
def mock_session(mocker):
    """Sesión mockeada para tests unitarios"""
    return mocker.MagicMock(spec=Session)
```

#### 6.3 Ejemplo de Tests Unitarios (Domain)
```python
# tests/unit/domain/test_profesor_entity.py
import pytest
from datetime import date
from domain.entities.profesor import Profesor
from shared.errors import ValidationError


class TestProfesorEntity:
    """Tests para entidad Profesor"""
    
    def test_crear_profesor_valido(self):
        """Debe crear profesor con datos válidos"""
        profesor = Profesor(
            id=1,
            nombre_completo="Juan Pérez",
            activo=True,
            dias_semana_permitidos=[0, 1, 2, 3, 4],
            recreos_permitidos=[1, 2, 3, 4]
        )
        
        assert profesor.nombre_completo == "Juan Pérez"
        assert profesor.activo is True
        assert len(profesor.dias_semana_permitidos) == 5
    
    def test_nombre_vacio_lanza_excepcion(self):
        """Debe lanzar ValidationError si nombre vacío"""
        with pytest.raises(ValidationError) as exc_info:
            Profesor(
                id=1,
                nombre_completo="",
                activo=True
            )
        
        assert "nombre" in str(exc_info.value).lower()
    
    def test_dias_semana_invalidos_lanza_excepcion(self):
        """Debe lanzar ValidationError si días inválidos"""
        with pytest.raises(ValidationError):
            Profesor(
                id=1,
                nombre_completo="Juan Pérez",
                dias_semana_permitidos=[0, 1, 7]  # 7 no existe
            )
    
    def test_puede_trabajar_dia_correcto(self):
        """Debe indicar correctamente si puede trabajar un día"""
        profesor = Profesor(
            id=1,
            nombre_completo="Juan Pérez",
            dias_semana_permitidos=[0, 2, 4]  # Lunes, Miércoles, Viernes
        )
        
        assert profesor.puede_trabajar_dia(0) is True   # Lunes
        assert profesor.puede_trabajar_dia(1) is False  # Martes
        assert profesor.puede_trabajar_dia(2) is True   # Miércoles
```

#### 6.4 Ejemplo de Tests de Integración (Infrastructure)
```python
# tests/integration/infrastructure/test_profesor_repository.py
import pytest
from infrastructure.repositories.profesor_repository import ProfesorRepositorySQLAlchemy
from domain.entities.profesor import Profesor


class TestProfesorRepository:
    """Tests de integración para repositorio de profesores"""
    
    def test_agregar_y_obtener_profesor(self, session):
        """Debe agregar y recuperar profesor correctamente"""
        repo = ProfesorRepositorySQLAlchemy(session)
        
        profesor = Profesor(
            nombre_completo="Test Profesor",
            activo=True,
            dias_semana_permitidos=[0, 1, 2, 3, 4],
            recreos_permitidos=[1, 2, 3, 4]
        )
        
        # Agregar
        profesor_guardado = repo.add(profesor)
        assert profesor_guardado.id is not None
        
        # Recuperar
        profesor_recuperado = repo.get_by_id(profesor_guardado.id)
        assert profesor_recuperado is not None
        assert profesor_recuperado.nombre_completo == "Test Profesor"
    
    def test_listar_profesores_activos(self, session):
        """Debe listar solo profesores activos"""
        repo = ProfesorRepositorySQLAlchemy(session)
        
        # Crear activo
        activo = Profesor(nombre_completo="Activo", activo=True)
        repo.add(activo)
        
        # Crear inactivo
        inactivo = Profesor(nombre_completo="Inactivo", activo=False)
        repo.add(inactivo)
        
        # Listar activos
        activos = repo.list_active()
        assert len(activos) == 1
        assert activos[0].nombre_completo == "Activo"
    
    def test_actualizar_profesor(self, session):
        """Debe actualizar profesor correctamente"""
        repo = ProfesorRepositorySQLAlchemy(session)
        
        profesor = Profesor(nombre_completo="Original", activo=True)
        profesor_guardado = repo.add(profesor)
        
        # Actualizar
        profesor_guardado.nombre_completo = "Modificado"
        profesor_actualizado = repo.update(profesor_guardado)
        
        # Verificar
        profesor_verificado = repo.get_by_id(profesor_actualizado.id)
        assert profesor_verificado.nombre_completo == "Modificado"
```

#### 6.5 Tests Property-Based (Hypothesis)
```python
# tests/unit/domain/test_profesor_properties.py
from hypothesis import given, strategies as st
from domain.entities.profesor import Profesor


class TestProfesorProperties:
    """Tests basados en propiedades para Profesor"""
    
    @given(
        nombre=st.text(min_size=1, max_size=100),
        dias=st.lists(st.integers(min_value=0, max_value=4), min_size=1, max_size=5, unique=True)
    )
    def test_profesor_siempre_tiene_al_menos_un_dia_disponible(self, nombre, dias):
        """Propiedad: Profesor con días permitidos siempre puede trabajar al menos un día"""
        profesor = Profesor(
            id=1,
            nombre_completo=nombre,
            dias_semana_permitidos=dias
        )
        
        # Al menos uno de los días debe ser True
        puede_trabajar = any(profesor.puede_trabajar_dia(dia) for dia in range(5))
        assert puede_trabajar
```

#### 6.6 Ejecutar Tests y Medir Cobertura
```bash
# Tests unitarios
pytest tests/unit/ -v

# Tests de integración
pytest tests/integration/ -v

# Todos los tests con cobertura
pytest --cov=src --cov-report=html --cov-report=term-missing

# Tests con marcadores
pytest -m "not slow" -v  # Excluir tests lentos

# Tests en paralelo (más rápido)
pytest -n auto --cov=src
```

#### 6.7 Configurar Marcadores en `pytest.ini`
```ini
# pytest.ini
[pytest]
markers =
    unit: Tests unitarios rápidos
    integration: Tests de integración con DB
    slow: Tests que tardan >1 segundo
    e2e: Tests end-to-end completos
    requires_sftp: Tests que necesitan conexión SFTP

# Opciones por defecto
addopts = 
    -ra
    -q
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --tb=short

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### 📦 Entregables
- ✅ Carpeta `tests/` completamente estructurada
- ✅ `conftest.py` con fixtures reutilizables
- ✅ Tests unitarios para `domain/` (cobertura 100%)
- ✅ Tests unitarios para `application/` (cobertura ≥95%)
- ✅ Tests de integración para `infrastructure/` (cobertura ≥85%)
- ✅ Tests property-based para reglas críticas
- ✅ Reporte de cobertura HTML en `htmlcov/`
- ✅ Configuración pytest optimizada
- ✅ Documentación en `documentacion/TESTING.md`

### ⏱️ Estimación
**5-7 días**

---

## <a name="fase-7"></a>7️⃣ FASE 7 – Detección de Duplicados y Limpieza Técnica

### 🎯 Objetivo
Reducir deuda técnica, eliminar código muerto, consolidar duplicados y simplificar complejidad.

### 📝 Acciones

#### 7.1 Detectar Código Duplicado
```bash
# Con ruff (integrado)
ruff check --select SIM,PL,C90 src/

# Detección avanzada de duplicados
pip install pydups
pydups src/

# Análisis de complejidad ciclomática
radon cc src/ -a -s > documentacion/auditoria/complejidad.txt
xenon --max-absolute B --max-modules A --max-average A src/
```

#### 7.2 Detectar Código Muerto
```bash
# Detectar imports y funciones sin uso
vulture src/ --min-confidence 80 > documentacion/auditoria/codigo_muerto.txt

# Detectar dependencias no usadas
deptry . > documentacion/auditoria/dependencias_no_usadas.txt
```

#### 7.3 Identificar Archivos Obsoletos
```bash
# Archivos no importados por ningún módulo
find src/ -name "*.py" -type f | while read file; do
    basename=$(basename "$file" .py)
    if ! grep -r "import.*$basename" src/ --exclude="$file" > /dev/null; then
        echo "❓ $file - posiblemente no usado"
    fi
done
```

**Candidatos a revisar:**
- `/src/ui/` → ¿Duplicado de `/src/presentation/`?
- Scripts en raíz sin uso
- Archivos `_old.py`, `_backup.py`, `_test.py` en src/
- Imágenes/recursos no referenciados

#### 7.4 Consolidar Funciones Duplicadas
```python
# ANTES: Función duplicada en 3 archivos
# profesor_form.py
def formatear_fecha(fecha):
    return fecha.strftime("%d/%m/%Y")

# guardia_form.py  
def formatear_fecha(fecha):
    return fecha.strftime("%d/%m/%Y")

# exportador.py
def formatear_fecha(fecha):
    return fecha.strftime("%d/%m/%Y")

# DESPUÉS: Función única en shared/utils.py
# shared/utils.py
from datetime import date, datetime

def formatear_fecha(fecha: date | datetime) -> str:
    """Formatear fecha en formato DD/MM/YYYY"""
    return fecha.strftime("%d/%m/%Y")

# Todos los archivos importan:
from shared.utils import formatear_fecha
```

#### 7.5 Reducir Complejidad Ciclomática
```python
# ANTES: CC = 15 (complejo)
def calcular_disponibilidad(profesor, fecha, recreo):
    if not profesor.activo:
        return False
    if fecha < profesor.fecha_inicio:
        return False
    if profesor.fecha_fin and fecha > profesor.fecha_fin:
        return False
    dia_semana = fecha.weekday()
    if dia_semana not in profesor.dias_permitidos:
        return False
    if recreo not in profesor.recreos_permitidos:
        return False
    # ... más condiciones
    return True

# DESPUÉS: CC = 3 (simple)
def calcular_disponibilidad(profesor, fecha, recreo):
    """Verificar si profesor está disponible"""
    return all([
        _esta_activo(profesor),
        _fecha_en_rango(profesor, fecha),
        _dia_permitido(profesor, fecha),
        _recreo_permitido(profesor, recreo)
    ])

def _esta_activo(profesor) -> bool:
    return profesor.activo

def _fecha_en_rango(profesor, fecha) -> bool:
    if fecha < profesor.fecha_inicio:
        return False
    if profesor.fecha_fin and fecha > profesor.fecha_fin:
        return False
    return True

def _dia_permitido(profesor, fecha) -> bool:
    return fecha.weekday() in profesor.dias_permitidos

def _recreo_permitido(profesor, recreo) -> bool:
    return recreo in profesor.recreos_permitidos
```

#### 7.6 Eliminar Imports Innecesarios
```bash
# Autoremover imports no usados con ruff
ruff check --select F401 --fix src/

# O con autoflake
autoflake --remove-all-unused-imports --in-place --recursive src/
```

#### 7.7 Simplificar Expresiones
```bash
# Detectar simplificaciones posibles
ruff check --select SIM src/
```

```python
# Ejemplos de simplificación

# ANTES
if condicion == True:
    return True
else:
    return False

# DESPUÉS
return condicion

# ANTES
lista = []
for item in items:
    lista.append(item.valor)

# DESPUÉS
lista = [item.valor for item in items]

# ANTES
try:
    resultado = operacion()
except Exception:
    pass

# DESPUÉS (más explícito)
try:
    resultado = operacion()
except SpecificException:
    logger.warning("Operación falló, continuando")
    resultado = None
```

### 📦 Entregables
- ✅ `documentacion/auditoria/complejidad.txt` - Análisis de CC
- ✅ `documentacion/auditoria/codigo_muerto.txt` - Código sin uso
- ✅ `documentacion/auditoria/duplicados.txt` - Funciones duplicadas
- ✅ `documentacion/limpieza_codigo.md` - Resumen de mejoras aplicadas
- ✅ Archivos obsoletos eliminados
- ✅ Funciones duplicadas consolidadas en `shared/utils.py`
- ✅ CC reducida a ≤10 en funciones críticas
- ✅ Imports limpiados automáticamente

### ⏱️ Estimación
**3-4 días**

---

## <a name="fase-8"></a>8️⃣ FASE 8 – Configuración y Entornos

### 🎯 Objetivo
Unificar y proteger la configuración de la aplicación con soporte multi-entorno.

### 📝 Acciones

#### 8.1 Implementar Configuración con Pydantic Settings
```python
# src/shared/settings.py
"""
Configuración de la aplicación usando Pydantic Settings.
Carga variables de entorno y valida tipos automáticamente.
"""
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Configuración principal de la aplicación"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Aplicación
    app_name: str = "Guardias de Patio"
    app_version: str = "2.0.0"
    environment: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    
    # Base de datos
    database_url: str = Field(
        default="sqlite:///data/guardias.db",
        description="URL de conexión a la base de datos"
    )
    db_echo: bool = False  # Log de queries SQL
    db_pool_size: int = 5
    db_pool_recycle: int = 3600  # segundos
    
    # Logging
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"
    log_file: Optional[Path] = Path("logs/app.log")
    
    # Rutas
    data_dir: Path = Path("data")
    backup_dir: Path = Path("data/backups")
    export_dir: Path = Path("data/exports")
    logs_dir: Path = Path("logs")
    
    # SFTP (Sincronización)
    sftp_enabled: bool = False
    sftp_host: Optional[str] = None
    sftp_port: int = 22
    sftp_username: Optional[str] = None
    sftp_password: Optional[str] = None
    sftp_remote_path: str = "/guardias"
    
    # Feature Flags
    enable_auto_backup: bool = True
    enable_notifications: bool = False
    enable_estadisticas: bool = True
    
    # Performance
    max_workers: int = 4  # Para operaciones paralelas
    request_timeout: int = 30  # segundos
    
    @field_validator("data_dir", "backup_dir", "export_dir", "logs_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Crear directorios si no existen"""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validar nivel de log"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level debe ser uno de: {valid_levels}")
        return v_upper
    
    @property
    def is_development(self) -> bool:
        """True si está en modo desarrollo"""
        return self.environment == "dev"
    
    @property
    def is_production(self) -> bool:
        """True si está en modo producción"""
        return self.environment == "prod"
    
    def get_database_url(self) -> str:
        """Obtener URL de BD con configuración apropiada"""
        if self.database_url.startswith("sqlite"):
            # Asegurar que el directorio existe
            db_path = Path(self.database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return self.database_url


# Instancia global de configuración
settings = Settings()
```

#### 8.2 Crear Archivos de Entorno
```bash
# .env.example
# Copiar a .env y configurar valores reales

# === APLICACIÓN ===
APP_NAME=Guardias de Patio
APP_VERSION=2.0.0
ENVIRONMENT=dev
DEBUG=true

# === BASE DE DATOS ===
DATABASE_URL=sqlite:///data/guardias.db
DB_ECHO=false

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FORMAT=text
LOG_FILE=logs/app.log

# === RUTAS ===
DATA_DIR=data
BACKUP_DIR=data/backups
EXPORT_DIR=data/exports
LOGS_DIR=logs

# === SFTP (Sincronización en la nube) ===
SFTP_ENABLED=false
SFTP_HOST=
SFTP_PORT=22
SFTP_USERNAME=
SFTP_PASSWORD=
SFTP_REMOTE_PATH=/guardias

# === FEATURE FLAGS ===
ENABLE_AUTO_BACKUP=true
ENABLE_NOTIFICATIONS=false
ENABLE_ESTADISTICAS=true

# === PERFORMANCE ===
MAX_WORKERS=4
REQUEST_TIMEOUT=30
```

```bash
# .env.test (para tests)
ENVIRONMENT=test
DEBUG=false
DATABASE_URL=sqlite:///:memory:
LOG_LEVEL=WARNING
SFTP_ENABLED=false
```

```bash
# .env.prod (para producción)
ENVIRONMENT=prod
DEBUG=false
DATABASE_URL=sqlite:///data/guardias_prod.db
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_AUTO_BACKUP=true
```

#### 8.3 Usar Configuración en la Aplicación
```python
# src/main.py
from shared.settings import settings
from shared.logging import setup_logging
from infrastructure.persistence.database import init_database

def main():
    """Punto de entrada de la aplicación"""
    
    # Configurar logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file if settings.log_file else None,
        json_format=(settings.log_format == "json")
    )
    
    logger = get_logger(__name__)
    logger.info(
        f"Iniciando {settings.app_name} v{settings.app_version}",
        extra={"environment": settings.environment}
    )
    
    # Inicializar base de datos
    engine = init_database(
        url=settings.get_database_url(),
        echo=settings.db_echo
    )
    
    # Crear directorios necesarios
    if settings.enable_auto_backup:
        settings.backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Iniciar aplicación...
```

#### 8.4 Validar Configuración al Inicio
```python
# src/shared/config_validator.py
"""
Validador de configuración al inicio de la aplicación.
"""
from pathlib import Path
from shared.settings import settings
from shared.logging import get_logger

logger = get_logger(__name__)


def validate_configuration() -> bool:
    """
    Validar configuración antes de iniciar aplicación.
    
    Returns:
        True si configuración es válida, False si hay errores críticos
    """
    errors = []
    warnings = []
    
    # Validar base de datos
    if not settings.database_url:
        errors.append("DATABASE_URL no configurada")
    
    # Validar SFTP si está habilitado
    if settings.sftp_enabled:
        if not settings.sftp_host:
            errors.append("SFTP habilitado pero SFTP_HOST no configurado")
        if not settings.sftp_username:
            errors.append("SFTP habilitado pero SFTP_USERNAME no configurado")
        if not settings.sftp_password:
            warnings.append("SFTP sin contraseña (se usará clave SSH)")
    
    # Validar directorios escribibles
    for dir_path in [settings.data_dir, settings.logs_dir, settings.backup_dir]:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"No se puede crear directorio {dir_path}: {e}")
    
    # Reportar resultados
    if errors:
        logger.error("❌ Errores de configuración:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    if warnings:
        logger.warning("⚠️ Advertencias de configuración:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    logger.info("✅ Configuración validada correctamente")
    return True
```

### 📦 Entregables
- ✅ `src/shared/settings.py` con Pydantic Settings
- ✅ `.env.example` documentado
- ✅ `.env.test` para entorno de tests
- ✅ `.env.prod` para entorno de producción
- ✅ `src/shared/config_validator.py` para validación al inicio
- ✅ Documentación en `README.md` sección "Configuración"
- ✅ `.gitignore` actualizado (incluir `.env`)

### ⏱️ Estimación
**2 días**

---

## <a name="fase-9"></a>9️⃣ FASE 9 – Consolidación y Limpieza de Documentación

### 🎯 Objetivo
Unificar, actualizar y reducir la documentación eliminando archivos obsoletos y duplicados.

### 📝 Acciones

#### 9.1 Auditoría de Documentación Actual
```bash
# Listar todos los archivos de documentación
find documentacion/ -type f -name "*.md" | sort

# Detectar archivos obsoletos (no modificados en >6 meses)
find documentacion/ -type f -name "*.md" -mtime +180
```

**Estructura actual `/documentacion`:**
```
documentacion/
├── BUILD_WINDOWS.md
├── CALENDARIO_MEJORADO_v3.md
├── LIMPIEZA_NOV_2025.md
├── PREMISAS_ASIGNACION_GUARDIAS.md
├── README.md
├── PLAN_REFACTORIZACION.md (este archivo)
├── archivo/          # ¿Archivos viejos?
├── build/            # ¿Instrucciones de build duplicadas?
├── datos ejemplo/
├── desarrollo/       # ¿Notas de desarrollo dispersas?
├── funcionalidades/  # ¿Especificaciones?
├── guias/            # ¿Guías de usuario?
├── roadmap/          # ¿Planes futuros?
├── sftp/             # ¿Config SFTP?
├── tecnico/          # ¿Documentación técnica dispersa?
└── versiones/        # ¿Changelog manual?
```

#### 9.2 Plan de Consolidación

**Documentación a MANTENER (simplificada):**
```
documentacion/
├── README.md                    # Índice general
├── ARCHITECTURE.md              # Arquitectura del sistema
├── DATABASE.md                  # Esquema y migraciones
├── DEVELOPMENT.md               # Guía de desarrollo
├── TESTING.md                   # Guía de testing
├── LOGGING.md                   # Sistema de logging
├── DEPLOYMENT.md                # Despliegue y build
├── USER_GUIDE.md                # Guía de usuario
├── CHANGELOG.md                 # Historial de cambios
├── CONTRIBUTING.md              # Cómo contribuir
├── SECURITY.md                  # Políticas de seguridad
├── API_REFERENCE.md             # Referencia de API interna
├── PREMISAS_ASIGNACION.md       # Reglas de negocio
├── auditoria/                   # Reportes de auditoría
│   └── .gitkeep
├── diagramas/                   # Diagramas y esquemas
│   └── .gitkeep
└── ejemplos/                    # Ejemplos de uso
    └── .gitkeep
```

**Documentación a ELIMINAR/CONSOLIDAR:**
- `archivo/` → Archivar fuera de Git o eliminar
- `build/` + `BUILD_WINDOWS.md` → Consolidar en `DEPLOYMENT.md`
- `desarrollo/` → Contenido relevante a `DEVELOPMENT.md`, resto eliminar
- `funcionalidades/` → Consolidar en `USER_GUIDE.md` y `ARCHITECTURE.md`
- `guias/` → Consolidar en `USER_GUIDE.md`
- `roadmap/` → Consolidar en issues de GitHub o archivo externo
- `sftp/` → Mover config a `.env.example` y docs a `DEPLOYMENT.md`
- `tecnico/` → Distribuir entre `ARCHITECTURE.md`, `DATABASE.md`, etc.
- `versiones/` → Consolidar en `CHANGELOG.md`
- `CALENDARIO_MEJORADO_v3.md` → Versiones antiguas a `/archivo` o eliminar
- `LIMPIEZA_NOV_2025.md` → Temporal, mover a issues o eliminar después de completar

#### 9.3 Estructura de Cada Documento

**Template estándar:**
```markdown
# [Título del Documento]

> **Última actualización:** 07/11/2025  
> **Versión:** 2.0.0  
> **Estado:** ✅ Actualizado | ⚠️ En revisión | ❌ Obsoleto

## 📋 Índice
- [Sección 1](#seccion-1)
- [Sección 2](#seccion-2)

## Introducción
[Breve descripción del propósito del documento]

## [Sección 1]
[Contenido...]

## Referencias
- [Documento relacionado](./OTRO.md)
- [Enlace externo](https://example.com)

## Historial de Cambios
| Fecha | Versión | Cambios |
|-------|---------|---------|
| 07/11/2025 | 2.0.0 | Creación inicial |
```

#### 9.4 Crear/Actualizar Documentos Clave

##### `documentacion/README.md` (Índice General)
```markdown
# 📚 Documentación - Guardias de Patio

> Sistema de gestión de guardias de patio para centros educativos

## 🗂️ Índice de Documentación

### Para Usuarios
- 📖 **[Guía de Usuario](USER_GUIDE.md)** - Cómo usar la aplicación
- 🚀 **[Instalación](DEPLOYMENT.md#instalación)** - Instalar y configurar

### Para Desarrolladores
- 🏗️ **[Arquitectura](ARCHITECTURE.md)** - Diseño del sistema
- 💻 **[Desarrollo](DEVELOPMENT.md)** - Configurar entorno de desarrollo
- 🧪 **[Testing](TESTING.md)** - Ejecutar y escribir tests
- 📊 **[Base de Datos](DATABASE.md)** - Esquema y migraciones
- 📝 **[Logging](LOGGING.md)** - Sistema de trazas
- 🔐 **[Seguridad](SECURITY.md)** - Políticas y auditorías

### Operaciones
- 🚀 **[Despliegue](DEPLOYMENT.md)** - Build y distribución
- 📦 **[Dependencias](DEVELOPMENT.md#dependencias)** - Gestión de paquetes
- 🔧 **[Mantenimiento](DEPLOYMENT.md#mantenimiento)** - Backups y limpieza

### Referencia
- 📘 **[API Interna](API_REFERENCE.md)** - Documentación de clases y funciones
- 📋 **[Premisas de Asignación](PREMISAS_ASIGNACION.md)** - Reglas de negocio
- 📜 **[Changelog](CHANGELOG.md)** - Historial de versiones
- 🤝 **[Contribuir](CONTRIBUTING.md)** - Guía de contribución

## 🔍 Búsqueda Rápida

| Necesito... | Ver documento |
|-------------|---------------|
| Instalar la app | [DEPLOYMENT.md](DEPLOYMENT.md#instalación) |
| Configurar entorno dev | [DEVELOPMENT.md](DEVELOPMENT.md#setup) |
| Ejecutar tests | [TESTING.md](TESTING.md#ejecutar-tests) |
| Entender arquitectura | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Conectar a SFTP | [DEPLOYMENT.md](DEPLOYMENT.md#sftp) |
| Ver reglas de guardias | [PREMISAS_ASIGNACION.md](PREMISAS_ASIGNACION.md) |
| Reportar un bug | [CONTRIBUTING.md](CONTRIBUTING.md#reportar-bugs) |

## 📊 Diagramas

Los diagramas están en `/documentacion/diagramas/`:
- `arquitectura.png` - Diagrama de capas
- `dependencias.png` - Grafo de dependencias
- `flujo_asignacion.png` - Flujo de asignación de guardias
- `modelo_datos.png` - Esquema de base de datos

## 🛠️ Generación Automática

La documentación de la API se genera automáticamente:
```bash
make docs  # Genera documentación en docs/api/
```

## 📝 Mantenimiento

- Revisar y actualizar documentación en cada PR
- Marcar documentos obsoletos con ❌
- Actualizar campo "Última actualización" al modificar
```

##### `documentacion/DEVELOPMENT.md` (consolidar guías de desarrollo)
```markdown
# 💻 Guía de Desarrollo

## Setup Inicial

### 1. Clonar repositorio
\`\`\`bash
git clone https://github.com/usuario/guardias_patio.git
cd guardias_patio
\`\`\`

### 2. Crear entorno virtual
\`\`\`bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\\Scripts\\activate  # Windows
\`\`\`

### 3. Instalar dependencias
\`\`\`bash
pip install -e .[dev]
\`\`\`

### 4. Configurar entorno
\`\`\`bash
cp .env.example .env
# Editar .env con valores apropiados
\`\`\`

### 5. Inicializar base de datos
\`\`\`bash
alembic upgrade head
\`\`\`

## Comandos Útiles

\`\`\`bash
make fmt        # Formatear código
make lint       # Analizar código
make typecheck  # Verificar tipos
make test       # Ejecutar tests
make test-cov   # Tests con cobertura HTML
make audit      # Auditoría de seguridad
make all        # Ejecutar todos los checks
\`\`\`

## Workflow de Desarrollo

1. Crear rama para feature/fix
2. Hacer cambios
3. Ejecutar \`make all\` antes de commit
4. Hacer commit (Conventional Commits)
5. Push y crear PR

## Pre-commit Hooks

Se ejecutan automáticamente al hacer commit:
\`\`\`bash
pre-commit install  # Solo primera vez
\`\`\`

## Ver documentación completa...
```

##### `documentacion/DEPLOYMENT.md` (consolidar BUILD_WINDOWS.md + sftp/)
```markdown
# 🚀 Despliegue y Distribución

## Instalación de Usuario Final

### Windows
1. Descargar instalador \`GuardiasDePatio_Setup.exe\`
2. Ejecutar instalador
3. Seguir wizard de instalación

### Instalación Manual
\`\`\`bash
pip install guardias-patio
guardias-patio
\`\`\`

## Build desde Código

### Requisitos
- Python 3.11+
- PyInstaller
- Inno Setup (Windows)

### Build Ejecutable
\`\`\`bash
# Windows
pyinstaller GuardiasDePatio.spec

# El ejecutable estará en dist/
\`\`\`

### Crear Instalador Windows
\`\`\`bash
# Con Inno Setup
iscc installer_windows.iss

# El instalador estará en Output/
\`\`\`

## Configuración SFTP

Ver \`.env.example\` para variables:
\`\`\`bash
SFTP_ENABLED=true
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=usuario
SFTP_PASSWORD=contraseña  # O usar clave SSH
SFTP_REMOTE_PATH=/guardias
\`\`\`

## Mantenimiento

### Backup Automático
\`\`\`bash
python scripts/maintain_sqlite.py
\`\`\`

### Limpieza Manual
\`\`\`bash
# Limpiar logs antiguos (>30 días)
find logs/ -name "*.log" -mtime +30 -delete

# Limpiar backups antiguos (mantener últimos 10)
ls -t data/backups/*.db | tail -n +11 | xargs rm
\`\`\`
```

##### `documentacion/CHANGELOG.md` (Conventional Commits)
```markdown
# 📜 Changelog

Todos los cambios notables de este proyecto serán documentados aquí.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- Sistema de logging estructurado con JSON
- Jerarquía de excepciones personalizadas
- Tests unitarios para capa de dominio

### Changed
- Migración a SQLAlchemy 2.0
- Refactorización de arquitectura a Clean Architecture

### Fixed
- Corrección de validación en recreos_permitidos

## [2.0.0] - 2025-11-07

### Added
- Matriz de restricciones día/recreo con auto-guardado
- Sincronización SFTP con la nube
- Sistema de migraciones con Alembic
- Exportación/importación de datos JSON

### Changed
- Migración a PyQt6 desde PyQt5
- Nueva UI con tema CCleaner/Fluent

### Fixed
- Corrección de crash al maximizar ventana
- Validación de tipos en ProfesorDTO

## [1.0.0] - 2024-XX-XX

### Added
- Versión inicial
- Gestión básica de profesores y guardias
```

#### 9.5 Generar Documentación Automática (API)
```bash
# Con pdoc
pip install pdoc
pdoc src/ -o documentacion/api/ --html --force

# Con Sphinx (más completo)
pip install sphinx sphinx-rtd-theme
sphinx-quickstart documentacion/sphinx
sphinx-apidoc -o documentacion/sphinx/source src/
cd documentacion/sphinx && make html
```

#### 9.6 Script de Limpieza
```bash
# scripts/cleanup_docs.sh
#!/bin/bash

echo "🧹 Limpiando documentación obsoleta..."

# Mover archivos antiguos a archivo/
mkdir -p documentacion/archivo
mv documentacion/desarrollo documentacion/archivo/ 2>/dev/null
mv documentacion/versiones documentacion/archivo/ 2>/dev/null
mv documentacion/roadmap documentacion/archivo/ 2>/dev/null

# Eliminar carpetas vacías
find documentacion/ -type d -empty -delete

echo "✅ Limpieza completada"
```

### 📦 Entregables
- ✅ `documentacion/README.md` - Índice consolidado
- ✅ `documentacion/ARCHITECTURE.md` - Arquitectura unificada
- ✅ `documentacion/DATABASE.md` - Esquema y migraciones
- ✅ `documentacion/DEVELOPMENT.md` - Guía desarrollo consolidada
- ✅ `documentacion/TESTING.md` - Guía de testing
- ✅ `documentacion/LOGGING.md` - Sistema de logging
- ✅ `documentacion/DEPLOYMENT.md` - Build y despliegue unificado
- ✅ `documentacion/USER_GUIDE.md` - Guía de usuario
- ✅ `documentacion/CHANGELOG.md` - Con Conventional Commits
- ✅ `documentacion/CONTRIBUTING.md` - Guía de contribución
- ✅ `documentacion/SECURITY.md` - Políticas de seguridad
- ✅ Archivos obsoletos eliminados o archivados
- ✅ Carpetas innecesarias consolidadas
- ✅ Documentación API generada en `/documentacion/api/`

### ⏱️ Estimación
**3-4 días**

---

## <a name="fase-10"></a>🔟 FASE 10 – Integración Continua (CI/CD)

### 🎯 Objetivo
Automatizar control de calidad y seguridad en cada commit o PR.

### 📝 Acciones

#### 10.1 Crear Pipeline de GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint-and-format:
    name: Lint y Formato
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      
      - name: Check formatting with black
        run: black --check .
      
      - name: Lint with ruff
        run: ruff check .
      
      - name: Check imports
        run: ruff check --select I .

  typecheck:
    name: Type Checking
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e .[dev]
      
      - name: Type check with mypy
        run: mypy src/

  test:
    name: Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e .[dev]
      
      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml --cov-report=term-missing
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
      
      - name: Check coverage threshold
        run: |
          coverage report --fail-under=85

  security:
    name: Security Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e .[dev]
      
      - name: Run Bandit
        run: bandit -r src/ -f json -o bandit-report.json
        continue-on-error: true
      
      - name: Run pip-audit
        run: pip-audit --format json --output pip-audit-report.json
        continue-on-error: true
      
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            pip-audit-report.json

  build:
    name: Build Executable
    needs: [lint-and-format, typecheck, test, security]
    runs-on: windows-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -e .[dev]
          pip install pyinstaller
      
      - name: Build with PyInstaller
        run: pyinstaller GuardiasDePatio.spec
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: guardias-patio-windows
          path: dist/GuardiasDePatio/
```

#### 10.2 Badge en README
```markdown
# README.md

# Guardias de Patio

[![CI/CD](https://github.com/usuario/guardias_patio/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/usuario/guardias_patio/actions)
[![codecov](https://codecov.io/gh/usuario/guardias_patio/branch/main/graph/badge.svg)](https://codecov.io/gh/usuario/guardias_patio)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
```

#### 10.3 Configurar Branch Protection
```yaml
# Configuración en GitHub Settings > Branches > Branch protection rules

main:
  require_pull_request: true
  required_approving_reviews: 1
  require_status_checks_to_pass: true
  required_status_checks:
    - lint-and-format
    - typecheck
    - test
    - security
  enforce_admins: false
  require_linear_history: true
  allow_force_pushes: false
  allow_deletions: false
```

#### 10.4 Automatizar Releases
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

### 📦 Entregables
- ✅ `.github/workflows/ci.yml` - Pipeline completo
- ✅ `.github/workflows/release.yml` - Automatización de releases
- ✅ Branch protection configurado
- ✅ Badges en README.md
- ✅ Integración con Codecov (opcional)
- ✅ Artefactos de build en cada release

### ⏱️ Estimación
**2 días**

---

## <a name="fase-11"></a>1️⃣1️⃣ FASE 11 – Seguridad y Cumplimiento

### 🎯 Objetivo
Prevenir vulnerabilidades, proteger datos sensibles y cumplir con buenas prácticas de seguridad.

### 📝 Acciones

#### 11.1 Auditoría de Seguridad Automatizada
```bash
# Bandit - Análisis de código
bandit -r src/ -f json -o documentacion/auditoria/bandit_report.json
bandit -r src/ -ll  # Solo severidad medium y high

# pip-audit - Vulnerabilidades en dependencias
pip-audit --format json --output documentacion/auditoria/pip_audit.json

# Safety - Alternativa a pip-audit
safety check --json > documentacion/auditoria/safety_report.json
```

#### 11.2 Protección de Datos Sensibles

**Verificar que NO estén en Git:**
```bash
# Buscar posibles secretos en código
grep -r "password\s*=\s*['\"]" src/ --include="*.py" || echo "✅ Sin contraseñas hardcodeadas"
grep -r "api_key\s*=\s*['\"]" src/ --include="*.py" || echo "✅ Sin API keys hardcodeadas"
grep -r "secret\s*=\s*['\"]" src/ --include="*.py" || echo "✅ Sin secretos hardcodeados"

# Verificar .gitignore
cat .gitignore | grep -E "\.env|\.db|\.sqlite|logs/" || echo "⚠️ Revisar .gitignore"
```

**Actualizar `.gitignore`:**
```gitignore
# === SENSIBLES ===
.env
.env.*
!.env.example

# Bases de datos
*.db
*.sqlite
*.sqlite3
data/*.db
!data/.gitkeep

# Logs
logs/
*.log

# Backups (pueden contener datos sensibles)
*.bak
*.backup
data/backups/

# Credenciales
**/secrets.json
**/credentials.json
**/*_credentials*

# === TEMPORALES ===
__pycache__/
*.py[cod]
*.so
.Python
.venv/
venv/

# Cache
.mypy_cache/
.pytest_cache/
.ruff_cache/
*.cover
.coverage
htmlcov/

# Build
dist/
build/
*.egg-info/
*.spec

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
```

#### 11.3 Validación de Inputs de Usuario
```python
# src/shared/validators.py
"""
Validadores de seguridad para inputs de usuario.
"""
import re
from pathlib import Path
from typing import Optional


def sanitize_filename(filename: str) -> str:
    """
    Sanitizar nombre de archivo para prevenir path traversal.
    
    Elimina: ../, .., caracteres especiales peligrosos
    """
    # Eliminar caracteres peligrosos
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Eliminar path traversal
    filename = filename.replace('..', '')
    filename = filename.strip('. ')
    
    if not filename:
        raise ValueError("Nombre de archivo inválido")
    
    return filename


def validate_sql_param(param: str, allow_wildcards: bool = False) -> str:
    """
    Validar parámetro SQL para prevenir inyección.
    
    NOTA: Usar siempre parámetros bound de SQLAlchemy.
    Esta función es una capa adicional de seguridad.
    """
    if not allow_wildcards and ('%' in param or '_' in param):
        raise ValueError("Comodines SQL no permitidos")
    
    # Detectar intentos de inyección obvios
    dangerous_patterns = [
        r'--',          # Comentarios SQL
        r';',           # Múltiples statements
        r'\bDROP\b',    # Comandos peligrosos
        r'\bDELETE\b',
        r'\bTRUNCATE\b',
        r'\bEXEC\b',
        r'\bUNION\b',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, param, re.IGNORECASE):
            raise ValueError(f"Patrón SQL peligroso detectado: {pattern}")
    
    return param


def validate_path(path: Path, base_dir: Path) -> Path:
    """
    Validar que path esté dentro de directorio base (prevenir path traversal).
    """
    try:
        resolved_path = path.resolve()
        resolved_base = base_dir.resolve()
        
        # Verificar que el path esté dentro del directorio base
        if not str(resolved_path).startswith(str(resolved_base)):
            raise ValueError(f"Path fuera de directorio permitido: {path}")
        
        return resolved_path
    
    except Exception as e:
        raise ValueError(f"Path inválido: {e}")
```

#### 11.4 Cifrado de Datos Sensibles (Opcional)
```python
# src/shared/encryption.py
"""
Cifrado de contraseñas y datos sensibles.
"""
from cryptography.fernet import Fernet
from pathlib import Path
import base64
import hashlib


def generate_key_from_password(password: str, salt: bytes = b'guardias_salt') -> bytes:
    """Generar clave de cifrado desde contraseña"""
    kdf = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.urlsafe_b64encode(kdf[:32])


def encrypt_data(data: str, key: bytes) -> str:
    """Cifrar datos con Fernet"""
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted: str, key: bytes) -> str:
    """Descifrar datos con Fernet"""
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()


# Uso en configuración SFTP
# settings.py
def get_sftp_password() -> Optional[str]:
    """Obtener contraseña SFTP (cifrada en .env)"""
    encrypted_pwd = os.getenv("SFTP_PASSWORD_ENCRYPTED")
    if encrypted_pwd:
        master_key = generate_key_from_password(os.getenv("MASTER_PASSWORD", "default"))
        return decrypt_data(encrypted_pwd, master_key)
    return None
```

#### 11.5 Auditar Dependencias Regularmente
```bash
# Script de auditoría mensual
# scripts/security_audit.sh
#!/bin/bash

echo "🔒 Auditoría de Seguridad - $(date)"
echo "================================"

# Dependencias vulnerables
echo -e "\n📦 Verificando dependencias..."
pip-audit || echo "⚠️ Vulnerabilidades encontradas"

# Código inseguro
echo -e "\n🔍 Analizando código..."
bandit -r src/ -ll -f txt

# Secretos hardcodeados
echo -e "\n🔐 Buscando secretos..."
grep -r "password\s*=\s*['\"][^'\"]\+['\"]" src/ && echo "⚠️ Contraseñas hardcodeadas" || echo "✅ Sin contraseñas hardcodeadas"

# Permisos de archivos sensibles
echo -e "\n🔑 Verificando permisos..."
[ -f .env ] && [ "$(stat -c %a .env)" = "600" ] && echo "✅ .env con permisos correctos" || echo "⚠️ .env debe tener permisos 600"

echo -e "\n✅ Auditoría completada"
```

#### 11.6 Políticas de Seguridad
```markdown
# documentacion/SECURITY.md

# 🔒 Política de Seguridad

## Versiones Soportadas

| Versión | Soportada |
|---------|-----------|
| 2.x.x   | ✅        |
| 1.x.x   | ❌        |

## Reportar Vulnerabilidad

Si encuentras una vulnerabilidad de seguridad:

1. **NO** abras un issue público
2. Envía email a: seguridad@example.com
3. Incluye:
   - Descripción detallada
   - Pasos para reproducir
   - Impacto potencial
   - Versión afectada

Responderemos en 48 horas.

## Mejores Prácticas

### Para Usuarios
- ✅ Mantener aplicación actualizada
- ✅ Usar contraseñas fuertes para SFTP
- ✅ Hacer backups regulares
- ✅ Revisar logs de acceso
- ❌ No compartir archivo `.env`
- ❌ No ejecutar con permisos de administrador innecesarios

### Para Desarrolladores
- ✅ Usar variables de entorno para secretos
- ✅ Validar TODOS los inputs de usuario
- ✅ Usar parámetros bound en queries SQL
- ✅ Auditar dependencias mensualmente
- ✅ Ejecutar `make audit` antes de cada commit
- ❌ NUNCA commitear `.env` o `.db`
- ❌ NUNCA hardcodear contraseñas o API keys

## Dependencias Seguras

Ejecutar auditoría:
\`\`\`bash
make audit  # Ejecuta bandit + pip-audit
\`\`\`

Actualizar dependencias:
\`\`\`bash
pip list --outdated
pip install --upgrade <paquete>
\`\`\`

## Cifrado de Datos

- **BD SQLite**: No cifrada por defecto (solo local)
- **SFTP**: Protocolo seguro con SSH
- **Contraseñas**: Usar variables de entorno o cifrado Fernet
- **Backups**: Mantener en ubicación segura

## Cumplimiento

- ✅ RGPD: No almacenamos datos personales sensibles
- ✅ Logs: Sin información sensible en logs
- ✅ Auditoría: Reportes automáticos mensuales

## Historial de Vulnerabilidades

### 2025-11-07 - v2.0.0
- ✅ Sin vulnerabilidades conocidas
```

### 📦 Entregables
- ✅ `documentacion/SECURITY.md` - Políticas de seguridad
- ✅ `src/shared/validators.py` - Validadores de inputs
- ✅ `src/shared/encryption.py` - Sistema de cifrado (opcional)
- ✅ `scripts/security_audit.sh` - Script de auditoría
- ✅ `.gitignore` actualizado con archivos sensibles
- ✅ Reportes de Bandit y pip-audit
- ✅ Documentación de mejores prácticas

### ⏱️ Estimación
**2-3 días**

---

## <a name="fase-12"></a>1️⃣2️⃣ FASE 12 – Rendimiento y Salud del Sistema

### 🎯 Objetivo
Garantizar estabilidad, rendimiento óptimo y mantenimiento preventivo de la aplicación.

### 📝 Acciones

#### 12.1 Profiling y Medición de Rendimiento
```python
# src/shared/performance.py
"""
Utilidades para medir y optimizar rendimiento.
"""
import time
import functools
import cProfile
import pstats
from io import StringIO
from typing import Callable, Any
from shared.logging import get_logger

logger = get_logger(__name__)


def measure_time(func: Callable) -> Callable:
    """Decorador para medir tiempo de ejecución"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time
        
        logger.info(
            f"⏱️ {func.__name__} ejecutado",
            extra={
                "function": func.__name__,
                "elapsed_ms": round(elapsed_time * 1000, 2)
            }
        )
        
        return result
    return wrapper


def profile_function(func: Callable) -> Callable:
    """Decorador para profiling detallado"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        s = StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 funciones más lentas
        
        logger.debug(
            f"📊 Profile de {func.__name__}:\n{s.getvalue()}",
            extra={"function": func.__name__}
        )
        
        return result
    return wrapper


# Uso
@measure_time
def generar_guardias(fecha_inicio, fecha_fin):
    """Generar guardias (medido)"""
    # ... lógica
    pass
```

#### 12.2 Monitoreo de Métricas Clave
```python
# src/shared/metrics.py
"""
Sistema de métricas y monitoreo.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import psutil
import os


@dataclass
class AppMetrics:
    """Métricas de la aplicación"""
    
    # Performance
    total_queries: int = 0
    avg_query_time_ms: float = 0.0
    slow_queries: int = 0  # >100ms
    
    # Recursos
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    
    # Base de datos
    db_size_mb: float = 0.0
    total_records: int = 0
    
    # Errores
    errors_count: int = 0
    warnings_count: int = 0
    
    # Timestamp
    collected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario"""
        return {
            "performance": {
                "total_queries": self.total_queries,
                "avg_query_time_ms": self.avg_query_time_ms,
                "slow_queries": self.slow_queries
            },
            "resources": {
                "memory_mb": self.memory_usage_mb,
                "cpu_percent": self.cpu_percent
            },
            "database": {
                "size_mb": self.db_size_mb,
                "total_records": self.total_records
            },
            "health": {
                "errors": self.errors_count,
                "warnings": self.warnings_count
            },
            "timestamp": self.collected_at.isoformat()
        }


def collect_metrics(db_path: str) -> AppMetrics:
    """Recolectar métricas actuales"""
    metrics = AppMetrics()
    
    # Recursos del sistema
    process = psutil.Process(os.getpid())
    metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
    metrics.cpu_percent = process.cpu_percent(interval=1.0)
    
    # Tamaño de BD
    if os.path.exists(db_path):
        metrics.db_size_mb = os.path.getsize(db_path) / 1024 / 1024
    
    return metrics
```

#### 12.3 Script de Mantenimiento Mejorado
```python
# scripts/maintain_sqlite.py
"""
Script de mantenimiento automático de la base de datos SQLite.

Ejecutar:
    - Manualmente: python scripts/maintain_sqlite.py
    - Cron (semanal): 0 2 * * 0 /path/to/python /path/to/maintain_sqlite.py
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def maintain_database(db_path: Path, backup_dir: Path) -> None:
    """
    Realizar mantenimiento completo de la base de datos.
    
    Args:
        db_path: Ruta a la base de datos
        backup_dir: Directorio para backups
    """
    logger.info("🔧 Iniciando mantenimiento de base de datos...")
    
    # 1. Verificar que existe
    if not db_path.exists():
        logger.error(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    # 2. Backup antes de mantenimiento
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"guardias_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Backup creado: {backup_path.name}")
    except Exception as e:
        logger.error(f"❌ Error al crear backup: {e}")
        return
    
    # 3. Conectar a BD
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 4. Verificar integridad
        logger.info("🔍 Verificando integridad...")
        result = cursor.execute("PRAGMA integrity_check").fetchone()
        if result[0] == "ok":
            logger.info("✅ Integridad OK")
        else:
            logger.error(f"❌ Problemas de integridad: {result}")
            conn.close()
            return
        
        # 5. Obtener estadísticas pre-mantenimiento
        size_before = db_path.stat().st_size / 1024 / 1024
        logger.info(f"📊 Tamaño antes: {size_before:.2f} MB")
        
        # 6. VACUUM - Reconstruir BD y liberar espacio
        logger.info("🧹 Ejecutando VACUUM...")
        cursor.execute("VACUUM")
        conn.commit()
        
        # 7. ANALYZE - Actualizar estadísticas del query optimizer
        logger.info("📊 Ejecutando ANALYZE...")
        cursor.execute("ANALYZE")
        conn.commit()
        
        # 8. Reindex (si hay índices corruptos)
        logger.info("🔄 Reindexando...")
        cursor.execute("REINDEX")
        conn.commit()
        
        # 9. Estadísticas post-mantenimiento
        size_after = db_path.stat().st_size / 1024 / 1024
        saved_mb = size_before - size_after
        logger.info(f"📊 Tamaño después: {size_after:.2f} MB")
        logger.info(f"💾 Espacio liberado: {saved_mb:.2f} MB ({saved_mb/size_before*100:.1f}%)")
        
    except Exception as e:
        logger.error(f"❌ Error durante mantenimiento: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    # 10. Limpiar backups antiguos (mantener últimos 10)
    cleanup_old_backups(backup_dir, keep=10)
    
    logger.info("✅ Mantenimiento completado")


def cleanup_old_backups(backup_dir: Path, keep: int = 10) -> None:
    """Eliminar backups antiguos, mantener solo los últimos N"""
    backups = sorted(backup_dir.glob("guardias_backup_*.db"), key=lambda p: p.stat().st_mtime)
    
    if len(backups) > keep:
        for old_backup in backups[:-keep]:
            try:
                old_backup.unlink()
                logger.info(f"🗑️ Eliminado backup antiguo: {old_backup.name}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar {old_backup.name}: {e}")


def cleanup_old_logs(logs_dir: Path, days: int = 30) -> None:
    """Eliminar logs antiguos (>N días)"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for log_file in logs_dir.glob("*.log"):
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if mtime < cutoff_date:
            try:
                log_file.unlink()
                logger.info(f"🗑️ Eliminado log antiguo: {log_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar {log_file.name}: {e}")


if __name__ == "__main__":
    # Configuración
    DB_PATH = Path("data/guardias.db")
    BACKUP_DIR = Path("data/backups")
    LOGS_DIR = Path("logs")
    
    # Ejecutar mantenimiento
    maintain_database(DB_PATH, BACKUP_DIR)
    
    # Limpiar logs antiguos (>30 días)
    if LOGS_DIR.exists():
        cleanup_old_logs(LOGS_DIR, days=30)
```

#### 12.4 Optimizaciones de SQLite
```python
# src/infrastructure/persistence/database.py (mejoras)

# Añadir más PRAGMAs para rendimiento
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configurar PRAGMAs optimizados"""
    cursor = dbapi_conn.cursor()
    
    # Integridad y seguridad
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # Rendimiento
    cursor.execute("PRAGMA journal_mode=WAL")         # Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")       # Balance seguridad/velocidad
    cursor.execute("PRAGMA cache_size=-64000")        # 64MB de cache
    cursor.execute("PRAGMA temp_store=MEMORY")        # Tablas temp en RAM
    cursor.execute("PRAGMA mmap_size=30000000000")    # 30GB memory-mapped I/O
    cursor.execute("PRAGMA page_size=4096")           # Tamaño de página 4KB
    cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")  # Auto-limpieza incremental
    
    cursor.close()
```

#### 12.5 Índices Optimizados
```sql
-- scripts/optimize_indexes.sql
-- Ejecutar: sqlite3 data/guardias.db < scripts/optimize_indexes.sql

-- Índices para profesores
CREATE INDEX IF NOT EXISTS idx_profesores_activo ON profesores(activo);
CREATE INDEX IF NOT EXISTS idx_profesores_nombre ON profesores(nombre_completo COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_profesores_zona ON profesores(zona_preferida_id);

-- Índices para guardias
CREATE INDEX IF NOT EXISTS idx_guardias_fecha ON guardias(fecha);
CREATE INDEX IF NOT EXISTS idx_guardias_profesor ON guardias(profesor_id);
CREATE INDEX IF NOT EXISTS idx_guardias_recreo ON guardias(recreo);
CREATE INDEX IF NOT EXISTS idx_guardias_fecha_recreo ON guardias(fecha, recreo);

-- Índices compuestos para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_guardias_profesor_fecha ON guardias(profesor_id, fecha);

-- Analizar queries
ANALYZE;
```

### 📦 Entregables
- ✅ `src/shared/performance.py` - Decoradores de medición
- ✅ `src/shared/metrics.py` - Sistema de métricas
- ✅ `scripts/maintain_sqlite.py` - Mantenimiento automatizado
- ✅ `scripts/optimize_indexes.sql` - Scripts de optimización
- ✅ PRAGMAs de SQLite optimizados
- ✅ Índices creados y documentados
- ✅ Cron job para mantenimiento semanal (documentado)

### ⏱️ Estimación
**2-3 días**

---

## <a name="fase-13"></a>1️⃣3️⃣ FASE 13 – Mantenimiento Continuo

### 🎯 Objetivo
Mantener la calidad alcanzada a largo plazo con procesos y checklists recurrentes.

### 📝 Acciones Recurrentes

#### 13.1 Checklist Diario (Desarrollo)
```markdown
## ✅ Checklist Diario

- [ ] Ejecutar `make all` antes de commit
- [ ] Pre-commit hooks pasaron sin errores
- [ ] Tests pasaron localmente
- [ ] PR tiene descripción clara
- [ ] Commits siguen Conventional Commits
- [ ] Documentación actualizada si hubo cambios en API
```

#### 13.2 Checklist Semanal
```markdown
## ✅ Checklist Semanal

### Código
- [ ] Revisar coverage report (debe ser ≥85%)
- [ ] Ejecutar `make audit` (Bandit + pip-audit)
- [ ] Revisar logs de errores acumulados
- [ ] Verificar tamaño de BD (si >100MB, ejecutar VACUUM)

### Tests
- [ ] Tests de integración pasaron
- [ ] Tests E2E críticos pasaron
- [ ] No hay tests skipped sin justificación

### Documentación
- [ ] README actualizado si hubo cambios importantes
- [ ] CHANGELOG actualizado con cambios de la semana
```

#### 13.3 Checklist Mensual
```markdown
## ✅ Checklist Mensual

### Dependencias
- [ ] Ejecutar `pip list --outdated`
- [ ] Actualizar dependencias con vulnerabilidades:
      \`\`\`bash
      pip-audit
      pip install --upgrade <paquete>
      \`\`\`
- [ ] Ejecutar tests después de actualizar
- [ ] Crear PR con actualizaciones

### Seguridad
- [ ] Revisar reporte de Bandit
- [ ] Verificar que `.env` no esté en Git
- [ ] Rotar credenciales SFTP (si aplica)
- [ ] Revisar logs de acceso

### Performance
- [ ] Revisar métricas de rendimiento
- [ ] Identificar queries lentas (>100ms)
- [ ] Ejecutar `scripts/maintain_sqlite.py`
- [ ] Verificar espacio en disco

### Base de Datos
- [ ] Backup manual completo
- [ ] Verificar integridad: `PRAGMA integrity_check`
- [ ] Revisar tamaño de backups automáticos
- [ ] Limpiar backups >3 meses

### Documentación
- [ ] Actualizar diagramas si hubo cambios arquitectónicos
- [ ] Revisar y cerrar issues resueltos
- [ ] Actualizar roadmap
```

#### 13.4 Checklist Trimestral
```markdown
## ✅ Checklist Trimestral

### Auditoría Completa
- [ ] Ejecutar todas las herramientas de Fase 1:
      \`\`\`bash
      ruff check .
      mypy src/
      bandit -r src/
      pip-audit
      vulture src/
      radon cc -s -a src/
      \`\`\`
- [ ] Documentar hallazgos en `documentacion/auditoria/YYYY-QX.md`

### Arquitectura
- [ ] Revisar violaciones de capas
- [ ] Identificar nuevos candidatos a refactorizar
- [ ] Actualizar `ARCHITECTURE.md` si hubo cambios

### Tests
- [ ] Coverage ≥85% global
- [ ] Coverage ≥95% en domain
- [ ] Tests property-based actualizados
- [ ] Agregar tests para bugs encontrados

### Performance
- [ ] Profiling de funciones críticas
- [ ] Optimizar queries lentas identificadas
- [ ] Revisar y actualizar índices de BD

### Limpieza
- [ ] Ejecutar detección de duplicados
- [ ] Eliminar código muerto detectado
- [ ] Consolidar funciones similares
- [ ] Reducir CC de funciones complejas (>10)

### Documentación
- [ ] Generar nueva documentación API:
      \`\`\`bash
      pdoc src/ -o documentacion/api/ --html --force
      \`\`\`
- [ ] Revisar y archivar documentos obsoletos
- [ ] Actualizar todos los diagramas
```

#### 13.5 Script de Mantenimiento Automatizado
```bash
# scripts/weekly_maintenance.sh
#!/bin/bash

echo "🔧 Mantenimiento Semanal Automatizado"
echo "====================================="
echo "Fecha: $(date)"
echo ""

# 1. Mantenimiento de BD
echo "📊 Mantenimiento de base de datos..."
python scripts/maintain_sqlite.py

# 2. Auditoría de seguridad
echo -e "\n🔒 Auditoría de seguridad..."
pip-audit > logs/pip_audit_$(date +%Y%m%d).log 2>&1

# 3. Limpiar logs antiguos
echo -e "\n🗑️ Limpiando logs antiguos..."
find logs/ -name "*.log" -mtime +30 -delete

# 4. Verificar espacio en disco
echo -e "\n💾 Espacio en disco:"
df -h | grep -E "^/dev"

# 5. Métricas de BD
echo -e "\n📊 Métricas de base de datos:"
sqlite3 data/guardias.db "SELECT 'Profesores:', COUNT(*) FROM profesores; SELECT 'Guardias:', COUNT(*) FROM guardias;"

# 6. Verificar backups recientes
echo -e "\n💾 Backups recientes:"
ls -lh data/backups/ | tail -n 5

echo -e "\n✅ Mantenimiento completado"
```

#### 13.6 Configurar Cron Jobs
```bash
# crontab -e

# Mantenimiento semanal (domingos a las 2 AM)
0 2 * * 0 /path/to/guardias_patio/scripts/weekly_maintenance.sh >> /path/to/logs/cron.log 2>&1

# Backup diario (todos los días a las 3 AM)
0 3 * * * python /path/to/guardias_patio/scripts/maintain_sqlite.py backup >> /path/to/logs/backup.log 2>&1

# Auditoría mensual (primer día del mes a las 4 AM)
0 4 1 * * /path/to/guardias_patio/scripts/monthly_audit.sh >> /path/to/logs/audit.log 2>&1
```

#### 13.7 Documento de Mantenimiento
```markdown
# documentacion/MAINTENANCE.md

# 🔧 Guía de Mantenimiento

## Tareas Programadas

### Diarias
- **3:00 AM** - Backup automático de BD

### Semanales
- **Domingo 2:00 AM** - Mantenimiento completo:
  - VACUUM + ANALYZE de BD
  - Auditoría de seguridad
  - Limpieza de logs antiguos
  - Verificación de backups

### Mensuales
- **Día 1, 4:00 AM** - Auditoría completa:
  - Dependencias outdated
  - Vulnerabilidades de seguridad
  - Análisis de código completo

## Comandos Útiles

\`\`\`bash
# Mantenimiento manual
python scripts/maintain_sqlite.py

# Auditoría de seguridad
make audit

# Ver logs recientes
tail -f logs/app.log

# Estadísticas de BD
sqlite3 data/guardias.db "SELECT name, COUNT(*) FROM sqlite_master GROUP BY name;"
\`\`\`

## Métricas Clave

| Métrica | Objetivo | Alarma |
|---------|----------|--------|
| Coverage | ≥85% | <80% |
| CC Máxima | ≤10 | >15 |
| Tamaño BD | <200MB | >500MB |
| Tiempo respuesta | <500ms | >2s |
| Vulnerabilidades | 0 | >3 |

## Registro de Mantenimiento

| Fecha | Tipo | Acción | Resultado |
|-------|------|--------|-----------|
| 2025-11-07 | Mensual | Actualizar dependencias | ✅ 5 paquetes actualizados |
| 2025-11-03 | Semanal | VACUUM BD | ✅ Liberados 15MB |
```

### 📦 Entregables
- ✅ `documentacion/MAINTENANCE.md` - Guía de mantenimiento
- ✅ `scripts/weekly_maintenance.sh` - Script semanal automatizado
- ✅ `scripts/monthly_audit.sh` - Script auditoría mensual
- ✅ Cron jobs configurados y documentados
- ✅ Checklists para diferentes frecuencias
- ✅ Registro de mantenimiento (template)
- ✅ Métricas y umbrales definidos

### ⏱️ Estimación
**2 días**

---

## ✅ CHECKLIST FINAL (Definition of Done) - AJUSTADO

### Fase 1: Diagnóstico y Limpieza
- [ ] Archivo `restricciones_widget_old.py` eliminado (517 líneas)
- [ ] Carpeta `/ui` consolidada en `/presentation` (2 archivos movidos)
- [ ] Test `test_calendario_guardias_form.py` arreglado o eliminado
- [ ] Lista de archivos de documentación auditada
- [ ] Resumen de limpieza documentado

### Fase 2: Consolidación de Código
- [ ] Arquitectura verificada (sin violaciones domain→infrastructure)
- [ ] Diagrama de arquitectura generado y actualizado
- [ ] `ARCHITECTURE.md` creado con estructura real
- [ ] Carpeta `/services` analizada y documentada su rol

### Fase 3: Tests
- [ ] **100% de tests pasando** (843/843 ✅)
- [ ] Cobertura medida y documentada
- [ ] Reporte HTML de cobertura generado
- [ ] Badge de cobertura en README
- [ ] `TESTING.md` actualizado con comandos

### Fase 4: Documentación
- [ ] De 30+ archivos → 12 archivos principales
- [ ] `README.md` en `/documentacion` como índice
- [ ] Carpetas `desarrollo/`, `guias/`, `tecnico/` consolidadas
- [ ] BUILD_WINDOWS.md consolidado en `DEPLOYMENT.md`
- [ ] Archivos obsoletos archivados
- [ ] Documentación API generada con pdoc

### Fase 5: CI/CD
- [ ] `.github/workflows/tests.yml` funcional
- [ ] `.github/workflows/lint.yml` funcional
- [ ] Tests corriendo en Ubuntu y macOS
- [ ] Badges en README mostrando estado
- [ ] Codecov integrado (opcional)
- [ ] Branch protection configurado

### Fase 6: Seguridad
- [ ] `pip-audit` ejecutado sin vulnerabilidades críticas
- [ ] `bandit` ejecutado sin issues de seguridad high
- [ ] `.gitignore` verificado (no .env, no .db en Git)
- [ ] `SECURITY.md` creado con políticas
- [ ] GitHub Actions para auditoría semanal

### Fase 7: Experiencia de Usuario (UX)
- [ ] Auditoría de formularios completada (`UX_AUDIT.md`)
- [ ] Mejoras del TODO list implementadas (auto-save, simplificación botones)
- [ ] ≥80% de campos con tooltip o placeholder informativo
- [ ] Confirmaciones solo en acciones destructivas
- [ ] Status bar con contexto en formularios principales
- [ ] Atajos de teclado documentados
- [ ] Guía `UX_PATTERNS.md` creada

### Fase 8: Mantenimiento
- [ ] `scripts/weekly_maintenance.sh` creado
- [ ] `MAINTENANCE.md` con guía de tareas
- [ ] Checklists semanales/mensuales documentados
- [ ] Proceso de mantenimiento probado

---

## 🎯 FASES ELIMINADAS (Ya Implementadas)

### ❌ NO Necesarias - Ya Existen
- ~~Fase "Revisión de Arquitectura"~~ → **Ya está bien** (Clean Architecture implementada)
- ~~Fase "Estándares y Herramientas"~~ → **Ya está** (ruff, mypy, pytest configurados)
- ~~Fase "Gestión de BD"~~ → **Ya está** (Alembic funcional, SQLAlchemy 2.0)
- ~~Fase "Tipado y Logging"~~ → **Ya está** (structlog implementado, type hints extensivos)
- ~~Fase "Configuración"~~ → **Ya está** (Pydantic Settings funcional)
- ~~Fase "Rendimiento"~~ → **Ya está** (Sistema de métricas y monitoring implementado)
- ~~Fase "Duplicados"~~ → **Incluido en Fase 1** (limpieza inicial)

### ✅ Consolidadas
- "Sistema de Pruebas" → **Fase 3** (arreglar y medir, no reescribir)
- "Documentación" → **Fase 4** (consolidar, no crear desde cero)
- "CI/CD" → **Fase 5** (automatizar lo que funciona)
- "Seguridad" → **Fase 6** (auditar y documentar)
- "UX" → **Fase 7** (mejorar usabilidad, implementar TODO list)
- "Mantenimiento" → **Fase 8** (establecer proceso)

---

## 📊 MÉTRICAS DE ÉXITO (Simplificadas)

### Código
| Métrica | Antes | Objetivo | Medición |
|---------|-------|----------|----------|
| Archivos obsoletos | 1 | 0 | ✅ Eliminado |
| Carpetas duplicadas | 1 (`/ui`) | 0 | ✅ Consolidado |
| Tests pasando | ? | 843/843 | `pytest --tb=line` |
| Cobertura | ? | ≥80% | `pytest --cov` |

### Documentación
| Métrica | Antes | Objetivo | Medición |
|---------|-------|----------|----------|
| Archivos `.md` | ~30+ | ≤15 | `find documentacion -name "*.md" \| wc -l` |
| Carpetas | ~10+ | 3 | `tree documentacion -L 1` |
| Docs sin actualizar | ? | 0 | Fecha en header |

### UX (NUEVO)
| Métrica | Antes | Objetivo | Medición |
|---------|-------|----------|----------|
| Campos con tooltip/placeholder | ~60% | ≥80% | Auditoría manual |
| Botones redundantes (restricciones) | 5 | 2 | `UX_AUDIT.md` |
| Confirmaciones innecesarias | ? | 0 | Revisión de QMessageBox |
| Atajos documentados | Parcial | 100% | `KEYBOARD_SHORTCUTS.md` |

### CI/CD
| Métrica | Antes | Objetivo | Medición |
|---------|-------|----------|----------|
| Workflows | 0 | 3 | GitHub Actions |
| Coverage automático | ❌ | ✅ | Codecov badge |
| Tests en CI | ❌ | ✅ | Tests badge verde |

### Seguridad
| Métrica | Antes | Objetivo | Medición |
|---------|-------|----------|----------|
| Vulnerabilidades | ? | 0 críticas | `pip-audit` |
| Issues Bandit high | ? | 0 | `bandit -r src/ -ll` |
| Secretos en Git | ? | 0 | `.gitignore` check |

---

## 🚀 ROADMAP SIMPLIFICADO (ACTUALIZADO)

### Sprint 1 (Semana 1) - Limpieza Rápida ⚡
- **Lunes-Martes**: Fase 1 (Limpieza inicial)
- **Miércoles**: Fase 2 (Arquitectura)
- **Jueves-Viernes**: Fase 3 inicio (Arreglar tests)

### Sprint 2 (Semana 2) - Tests y Docs 🎯
- **Lunes-Martes**: Fase 3 fin (Tests 100% pasando)
- **Miércoles-Jueves**: Fase 4 (Consolidar docs)
- **Viernes**: Fase 5 inicio (CI/CD setup)

### Sprint 3 (Semana 3) - Automatización ✅
- **Lunes**: Fase 5 fin (CI/CD completo)
- **Martes**: Fase 6 (Seguridad)
- **Miércoles-Jueves**: Fase 7 (UX) 🎨 **NUEVA**
- **Viernes**: Fase 8 (Mantenimiento)

### Sprint 4 (Semana 4) - Buffer y Cierre 🎉
- **Lunes-Martes**: Ajustes finales y revisión
- **Miércoles-Viernes**: Documentación final y handoff

**Duración total: 4 semanas** (vs 10 semanas originales)

**Reducción: -60% del tiempo** manteniendo el valor + mejoras UX

---

## 📊 MÉTRICAS DE ÉXITO

### Código
| Métrica | Objetivo | Actual | Estado |
|---------|----------|--------|--------|
| Cobertura Global | ≥85% | __% | ⬜ |
| Cobertura Domain | ≥95% | __% | ⬜ |
| CC Máxima | ≤10 | __ | ⬜ |
| Warnings MyPy | 0 | __ | ⬜ |
| Errores Ruff | 0 | __ | ⬜ |

### Seguridad
| Métrica | Objetivo | Actual | Estado |
|---------|----------|--------|--------|
| Vulnerabilidades | 0 | __ | ⬜ |
| Secretos en Git | 0 | __ | ⬜ |
| Warnings Bandit | ≤5 | __ | ⬜ |

### Performance
| Métrica | Objetivo | Actual | Estado |
|---------|----------|--------|--------|
| Queries lentas (>100ms) | 0 | __ | ⬜ |
| Tiempo startup | <2s | __s | ⬜ |
| Tamaño BD | <200MB | __MB | ⬜ |
| Uso memoria | <200MB | __MB | ⬜ |

### Documentación
| Métrica | Objetivo | Actual | Estado |
|---------|----------|--------|--------|
| Docs actualizados | 100% | __% | ⬜ |
| Archivos `.md` principales | ≤15 | __ | ⬜ |
| Archivos obsoletos | 0 | __ | ⬜ |
| Diagramas | ≥3 | __ | ⬜ |

---

## 🚀 ROADMAP DE EJECUCIÓN

### Sprint 1 (Semana 1-2) - Diagnóstico y Setup
- ✅ **Fase 1**: Diagnóstico Inicial
- ✅ **Fase 2**: Revisión de Arquitectura
- ✅ **Fase 3**: Estándares y Herramientas

### Sprint 2 (Semana 3-4) - Base Técnica
- ✅ **Fase 4**: Gestión de Base de Datos
- ✅ **Fase 5**: Tipado, Errores y Logging
- ✅ **Fase 7**: Limpieza Técnica (adelantado)

### Sprint 3 (Semana 5-6) - Testing y Calidad
- ✅ **Fase 6**: Sistema de Pruebas
- ✅ **Fase 8**: Configuración y Entornos

### Sprint 4 (Semana 7-8) - Documentación y Operaciones
- ✅ **Fase 9**: Consolidación de Documentación
- ✅ **Fase 10**: CI/CD
- ✅ **Fase 11**: Seguridad

### Sprint 5 (Semana 9-10) - Optimización y Cierre
- ✅ **Fase 12**: Rendimiento y Salud
- ✅ **Fase 13**: Mantenimiento Continuo
- ✅ Revisión final y ajustes

**Duración total estimada: 10 semanas (2.5 meses)**

---

## 📎 REFERENCIAS Y RECURSOS

### Herramientas de Calidad
- [Ruff](https://docs.astral.sh/ruff/) - Linter y formatter ultrarrápido
- [MyPy](https://mypy.readthedocs.io/) - Tipado estático para Python
- [Black](https://black.readthedocs.io/) - Formatter opinionado
- [Bandit](https://bandit.readthedocs.io/) - Análisis de seguridad
- [pip-audit](https://pypi.org/project/pip-audit/) - Auditoría de dependencias
- [Vulture](https://github.com/jendrikseipp/vulture) - Detección de código muerto
- [Radon](https://radon.readthedocs.io/) - Métricas de complejidad

### Testing
- [pytest](https://docs.pytest.org/) - Framework de testing
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage para pytest
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing
- [pytest-mock](https://pytest-mock.readthedocs.io/) - Mocking

### Documentación
- [pdoc](https://pdoc.dev/) - Generación de documentación API
- [Sphinx](https://www.sphinx-doc.org/) - Documentación avanzada
- [MkDocs](https://www.mkdocs.org/) - Documentación con Material theme
- [Keep a Changelog](https://keepachangelog.com/es-ES/) - Formato CHANGELOG

### Python & SQLAlchemy
- [PEP 8](https://peps.python.org/pep-0008/) - Style Guide for Python Code
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/) - ORM moderno
- [Alembic](https://alembic.sqlalchemy.org/) - Migraciones de BD
- [Pydantic](https://docs.pydantic.dev/) - Validación de datos
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Gestión de configuración

### Arquitectura
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) - Alistair Cockburn
- [The Twelve-Factor App](https://12factor.net/es/) - Metodología para apps modernas

### CI/CD
- [GitHub Actions](https://docs.github.com/en/actions) - Automatización de workflows
- [Codecov](https://about.codecov.io/) - Reportes de cobertura
- [Pre-commit](https://pre-commit.com/) - Git hooks framework

### Seguridad
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Vulnerabilidades más críticas
- [Safety](https://pyup.io/safety/) - Auditoría de vulnerabilidades
- [Cryptography](https://cryptography.io/) - Librería de cifrado

---

## 🎯 RESULTADO FINAL ESPERADO

Al completar todas las fases de este plan, la aplicación **Guardias de Patio** será:

### ✨ Calidad de Código
- **100% tipada** con MyPy strict
- **Totalmente testeada** con cobertura ≥85%
- **Lint-free** sin warnings ni errores
- **Sin duplicados** ni código muerto
- **Complejidad baja** (CC ≤10)

### 🏗️ Arquitectura Sólida
- **Clean Architecture** bien definida
- **Capas desacopladas** sin dependencias circulares
- **Extensible** y preparada para crecer
- **Modular** con responsabilidades claras

### 🔒 Segura
- **Sin vulnerabilidades** conocidas
- **Inputs validados** contra inyecciones
- **Secretos protegidos** fuera de Git
- **Auditorías automatizadas** mensualmente

### 📚 Bien Documentada
- **Documentación técnica** completa y actualizada
- **Guías de usuario** claras
- **API documentada** automáticamente
- **Arquitectura diagramada** y explicada

### 🚀 Operativamente Excelente
- **CI/CD funcional** con GitHub Actions
- **Tests automáticos** en cada PR
- **Backups automáticos** diarios
- **Mantenimiento programado** semanal/mensual

### ⚡ Performante
- **Queries optimizadas** (<100ms)
- **BD optimizada** con índices correctos
- **Métricas monitorizadas** continuamente
- **Recursos eficientes** (<200MB RAM)

### 🔄 Mantenible
- **Proceso claro** de desarrollo
- **Checklists** para cada frecuencia
- **Scripts automatizados** de mantenimiento
- **Registro histórico** de cambios

### 🌐 Lista para Escalar
- **Multi-entorno** (dev/test/prod)
- **Migraciones** con Alembic
- **Preparada** para PostgreSQL/MySQL
- **Arquitectura** lista para microservicios

---

## 📞 SOPORTE Y CONTRIBUCIÓN

### ¿Necesitas Ayuda?
- 📧 Email: desarrollo@example.com
- 🐛 Reportar bugs: [GitHub Issues](https://github.com/usuario/guardias_patio/issues)
- 💬 Discusiones: [GitHub Discussions](https://github.com/usuario/guardias_patio/discussions)

### Contribuir
Ver [CONTRIBUTING.md](./CONTRIBUTING.md) para guía completa de contribución.

---

## 📝 NOTAS FINALES

### Adaptación del Plan
Este plan es una **guía**, no una camisa de fuerza:
- Puedes ajustar el orden de las fases según prioridades
- Algunas fases pueden ejecutarse en paralelo
- Los tiempos son estimaciones, ajusta según tu equipo
- Documenta las desviaciones del plan

### Revisión Continua
- Revisar progreso semanalmente
- Actualizar métricas en cada sprint
- Documentar decisiones importantes
- Celebrar hitos completados 🎉

### Próximos Pasos
Una vez completado el plan:
1. Mantener checklists de Fase 13
2. Planificar nuevas features con arquitectura limpia
3. Mentorizar al equipo en buenas prácticas
4. Compartir aprendizajes con la comunidad

---

**✅ Plan creado:** 07/11/2025  
**📌 Versión:** 1.0.0  
**👤 Autor:** Equipo de Desarrollo Guardias de Patio  
**🔄 Última actualización:** 07/11/2025

---

<div align="center">

**🚀 ¡Que comience la refactorización! 🚀**

_"Cualquier código que no esté testeado, documentado y mantenible es deuda técnica."_

</div>

