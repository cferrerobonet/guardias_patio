# Contributing to Guardias de Patio

¡Gracias por tu interés en contribuir a **Guardias de Patio**! Este documento te guiará en el proceso de configuración, desarrollo y envío de contribuciones.

**Versión**: 3.0.0  
**Última actualización**: 8 de noviembre de 2025

---

## 📋 Tabla de Contenidos

1. [Valores del Proyecto](#valores-del-proyecto)
2. [Configuración del Entorno](#configuración-del-entorno)
3. [Flujo de Trabajo](#flujo-de-trabajo)
4. [Estándares de Código](#estándares-de-código)
5. [Guías UX](#guías-ux) 🆕
6. [Testing](#testing)
7. [Proceso de Pull Request](#proceso-de-pull-request)
8. [Añadir Funcionalidades](#añadir-funcionalidades)
9. [Historia del Proyecto](#historia-del-proyecto)
10. [Mantenimiento](#mantenimiento)

---

## 🎯 Valores del Proyecto

- ✅ **Calidad sobre velocidad**: Código bien testeado y documentado
- ✅ **Clean Architecture**: Separación de responsabilidades en 4 capas
- ✅ **Type Safety**: Type hints y validación con Pydantic
- ✅ **Testing exhaustivo**: Mínimo 70% de cobertura
- ✅ **Comunicación clara**: Issues y PRs descriptivos

---

## 🛠️ Configuración del Entorno

### Prerrequisitos

- **Python**: 3.11 o superior (obligatorio)
- **Git**: 2.30 o superior
- **Sistema Operativo**: macOS, Linux o Windows

### Instalación

#### 1. Fork y Clonar

```bash
# Fork del repositorio en GitHub
git clone https://github.com/TU_USUARIO/guardias_patio.git
cd guardias_patio

# Añadir repositorio original como "upstream"
git remote add upstream https://github.com/cferrerobonet/guardias_patio.git
```

#### 2. Entorno Virtual

```bash
# Crear entorno virtual con Python 3.11+
python3.11 -m venv venv

# Activar (macOS/Linux)
source venv/bin/activate

# Activar (Windows)
venv\Scripts\activate
```

#### 3. Dependencias

```bash
# Instalar dependencias principales
pip install -r requirements.txt

# Instalar dependencias de desarrollo
pip install pytest pytest-cov pytest-qt pytest-mock mypy ruff

# Verificar instalación
pip list | grep -E 'PyQt6|SQLAlchemy|pydantic|pytest'
```

#### 4. Pre-commit Hooks (Opcional pero Recomendado)

El proyecto usa **pre-commit hooks** para validar código antes de commits:

```bash
# Instalar pre-commit
pip install pre-commit

# Activar hooks
pre-commit install

# Ejecutar manualmente (opcional)
pre-commit run --all-files
```

**Hooks activos**:
- `ruff` - Linting y formato de código
- Validación automática en cada `git commit`

**Desactivar temporalmente** (no recomendado):
```bash
git commit --no-verify -m "mensaje"
```

#### 5. Base de Datos

```bash
# Aplicar migraciones
alembic upgrade head

# Verificar
ls -lh guardias_patio.db
```

#### 5. Verificar Instalación

```bash
# Ejecutar tests
pytest tests/ -v

# Ejecutar aplicación
python src/main.py
```

---

## 🔀 Flujo de Trabajo

### Estructura de Ramas

```
main (producción)
  │
  ├─── develop (desarrollo principal)
  │     │
  │     ├─── feature/nueva-funcionalidad
  │     ├─── bugfix/corregir-error
  │     └─── refactor/mejorar-codigo
  │
  └─── hotfix/arreglo-urgente
```

### Crear Nueva Rama

```bash
# Actualizar repositorio local
git checkout develop
git pull upstream develop

# Crear rama para tu feature/bugfix
git checkout -b feature/nombre-descriptivo
```

### Nomenclatura de Ramas

| Tipo | Prefijo | Ejemplo |
|------|---------|---------|
| **Feature** | `feature/` | `feature/validador-email` |
| **Bugfix** | `bugfix/` | `bugfix/fix-duplicados-guardias` |
| **Hotfix** | `hotfix/` | `hotfix/critical-db-error` |
| **Refactor** | `refactor/` | `refactor/improve-repositories` |
| **Docs** | `docs/` | `docs/update-readme` |
| **Test** | `test/` | `test/add-validator-tests` |

### Commits Semánticos

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
<tipo>(<alcance>): <descripción corta>

[cuerpo opcional]

[footer opcional]
```

#### Tipos de Commit

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(validadores): añadir validador de DNI` |
| `fix` | Corrección de bug | `fix(guardias): corregir duplicados en asignación` |
| `docs` | Documentación | `docs(readme): actualizar instrucciones` |
| `style` | Formato (no afecta lógica) | `style(ui): ajustar espaciado en formularios` |
| `refactor` | Refactorización | `refactor(repos): mejorar mappers de entidades` |
| `test` | Tests | `test(validadores): añadir tests para Email` |
| `perf` | Performance | `perf(db): añadir índices a tabla guardias` |
| `chore` | Mantenimiento | `chore(deps): actualizar dependencias` |

#### Ejemplos

```bash
# Feature con cuerpo
git commit -m "feat(validadores): añadir ValidadorDNI con validación NIF/NIE

- Implementa validación de letra de control
- Soporta formato con y sin guiones
- Añade tests con 95% cobertura"

# Bugfix que cierra issue
git commit -m "fix(asignador): evitar asignar más de una guardia por día

Cierra #142"

# Refactor simple
git commit -m "refactor(repos): extraer lógica de mapeo a ProfesorMapper"
```

### Mantener Rama Actualizada

```bash
# Periódicamente, actualiza desde upstream
git checkout develop
git pull upstream develop

# Rebase tu rama sobre develop actualizado
git checkout feature/tu-feature
git rebase develop

# Si hay conflictos, resuélvelos y continúa
git add .
git rebase --continue
```

---

## 📝 Estándares de Código

### PEP 8 - Guía de Estilo

Seguimos [PEP 8](https://peps.python.org/pep-0008/) con adaptaciones:

#### Longitud de Línea

- **Máximo**: 88 caracteres (black default)

#### Indentación

- **4 espacios** (no tabs)

#### Imports

```python
# ✅ BIEN: Ordenados y agrupados
# 1. Standard library
import os
from datetime import datetime
from typing import List, Optional

# 2. Third-party
from sqlalchemy import Column, Integer, String
from PyQt6.QtWidgets import QWidget

# 3. Local
from src.domain.entities import ProfesorEntity
from src.application.dtos import ProfesorDTO

# ❌ MAL: Desordenados
from src.domain.entities import ProfesorEntity
import os
from PyQt6.QtWidgets import QWidget
```

### Type Hints

Siempre usa type hints en funciones públicas:

```python
# ✅ BIEN
def crear_profesor(
    nombre: str,
    email: str,
    horas_contrato: float,
    tutor: bool = False
) -> ProfesorEntity:
    """Crea un nuevo profesor."""
    return ProfesorEntity(nombre, email, horas_contrato, tutor)

def obtener_profesores(activos: bool = True) -> List[ProfesorEntity]:
    """Obtiene lista de profesores."""
    pass

def buscar_profesor(id: int) -> Optional[ProfesorEntity]:
    """Busca profesor por ID."""
    pass

# ❌ MAL: Sin type hints
def crear_profesor(nombre, email, horas_contrato, tutor=False):
    return ProfesorEntity(nombre, email, horas_contrato, tutor)
```

### Docstrings

Usa [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):

```python
def calcular_guardias_pendientes(
    profesor_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime
) -> int:
    """Calcula las guardias pendientes de un profesor en un periodo.
    
    Args:
        profesor_id: ID del profesor.
        fecha_inicio: Fecha de inicio del periodo (inclusive).
        fecha_fin: Fecha de fin del periodo (inclusive).
        
    Returns:
        Número de guardias pendientes en el periodo.
        
    Raises:
        ValueError: Si fecha_fin es anterior a fecha_inicio.
        ProfesorNoEncontradoError: Si el profesor no existe.
        
    Example:
        >>> calcular_guardias_pendientes(1, date(2024,1,1), date(2024,1,31))
        5
    """
    if fecha_fin < fecha_inicio:
        raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
    
    return 5
```

### Clean Code Principles

#### 1. Funciones Pequeñas

```python
# ✅ BIEN: Funciones enfocadas
def validar_email(email: str) -> bool:
    """Valida formato de email."""
    return "@" in email and "." in email.split("@")[1]

def validar_horas_contrato(horas: float) -> bool:
    """Valida que las horas sean positivas."""
    return 0 < horas <= 40

def validar_profesor(email: str, horas: float) -> bool:
    """Valida datos de profesor."""
    return validar_email(email) and validar_horas_contrato(horas)

# ❌ MAL: Función gigante que hace todo
def validar_profesor(email, horas, nombre, dni, ...):
    # 200 líneas de validaciones mezcladas
    pass
```

#### 2. DRY (Don't Repeat Yourself)

```python
# ✅ BIEN: Extraer lógica común
def formatear_nombre_profesor(nombre: str, apellidos: str) -> str:
    """Formatea nombre en formato APELLIDOS, Nombre."""
    return f"{apellidos.upper()}, {nombre.title()}"

# ❌ MAL: Código duplicado
profesor1 = f"{apellidos1.upper()}, {nombre1.title()}"
profesor2 = f"{apellidos2.upper()}, {nombre2.title()}"
```

#### 3. Single Responsibility

```python
# ✅ BIEN: Cada clase una responsabilidad
class ProfesorRepository:
    """Solo maneja persistencia de profesores."""
    def guardar(self, profesor): pass
    def obtener(self, id): pass

class ValidadorProfesor:
    """Solo valida datos de profesores."""
    def validar(self, profesor): pass

# ❌ MAL: Clase que hace todo
class ProfesorManager:
    def guardar(self, profesor): pass
    def validar(self, profesor): pass
    def enviar_email(self, profesor): pass
    def generar_pdf(self, profesor): pass
```

---

## 🎨 Guías UX

### Documentación UX

El proyecto mantiene estándares UX bien documentados (Fase 7 - Nov 2025):

| Documento | Propósito | Cuándo Consultar |
|-----------|-----------|------------------|
| **[UX_AUDIT.md](UX_AUDIT.md)** | Auditoría completa (8.2/10) | Ver estado actual de UX |
| **[guias/UX_PATTERNS.md](guias/UX_PATTERNS.md)** | Patrones y convenciones | Al crear formularios/widgets |
| **[guias/KEYBOARD_SHORTCUTS.md](guias/KEYBOARD_SHORTCUTS.md)** | 50+ atajos | Al añadir funcionalidad nueva |

### Checklist UX para Nuevos Formularios

Al crear un nuevo formulario o widget, asegúrate de:

- [ ] **Tooltips informativos**: Todos los campos complejos tienen tooltip con:
  ```python
  campo.setToolTip(
      "Descripción del campo\n"
      "Información adicional o rango válido"
  )
  ```
  
- [ ] **Placeholders con ejemplos**: Campos de entrada muestran formato esperado:
  ```python
  self.nombre_input.setPlaceholderText("GARCÍA LÓPEZ, JUAN")
  self.email_input.setPlaceholderText("profesor@colegio.edu")
  ```

- [ ] **Confirmaciones apropiadas**: Solo para acciones destructivas:
  ```python
  # ✅ SÍ confirmar: Eliminar, limpiar datos masivamente
  # ❌ NO confirmar: Guardar, refrescar, cancelar sin cambios
  ```

- [ ] **Atajos de teclado**: Implementar shortcuts estándar:
  ```python
  QShortcut(QKeySequence("F5"), self, self.refrescar)
  QShortcut(QKeySequence.StandardKey.Save, self, self.guardar)
  ```

- [ ] **Estilos consistentes**: Usar estilos predefinidos:
  ```python
  from presentation.styles import styles
  self.guardar_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
  self.eliminar_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
  ```

- [ ] **Validación en tiempo real**: Feedback inmediato en campos críticos:
  ```python
  self.campo.editingFinished.connect(self._validar_campo)
  ```

**📖 Guía completa**: [UX_PATTERNS.md](guias/UX_PATTERNS.md)

### Métricas UX Actuales (v3.0.2)

- ✅ **85% cobertura tooltips/placeholders** (objetivo: ≥80%)
- ✅ **100% confirmaciones apropiadas**
- ✅ **8.2/10 puntuación global** (auditoría independiente)
- ✅ **50+ atajos documentados**

**Mantén estos estándares** en nuevo código.

---

## 🧪 Testing

### Estado Actual (Nov 2025)

**Métricas**:
- ✅ **990 tests** pasando (100%)
- ✅ **46.31% coverage** global
- ✅ **92-96% coverage** en entidades de dominio (ProfesorEntity, GuardiaEntity, ZonaEntity)
- ⚠️ **23-25% coverage** en repositories (área de mejora)
- ⚠️ **0% coverage** en use cases (área de mejora)

**Objetivo**: Mantener >45% coverage, priorizando tests en domain layer.

📖 **Documentación completa**: [TESTING.md](TESTING.md)

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_validadores_ui.py

# Con cobertura
pytest --cov=src --cov-report=html

# Solo tests rápidos
pytest -m "not slow"

# Verbose
pytest -v
```

### Estructura de Tests

```python
import pytest
from src.domain.value_objects import Email

class TestEmail:
    """Suite de tests para Email value object."""
    
    def test_email_valido_acepta_formato_correcto(self):
        """Debe aceptar email con formato válido."""
        # Arrange
        email_str = "usuario@example.com"
        
        # Act
        email = Email(email_str)
        
        # Assert
        assert email.valor == email_str
    
    def test_email_sin_arroba_lanza_excepcion(self):
        """Debe rechazar email sin @."""
        with pytest.raises(ValueError, match="Email inválido"):
            Email("usuario.example.com")
    
    @pytest.mark.parametrize("email_invalido", [
        "sin_arroba",
        "@sin_usuario",
        "usuario@",
    ])
    def test_emails_invalidos(self, email_invalido):
        """Debe rechazar emails con formato inválido."""
        with pytest.raises(ValueError):
            Email(email_invalido)
```

### Cobertura Mínima

- **Domain**: 90%+ (lógica crítica)
- **Application**: 80%+ (use cases)
- **Infrastructure**: 70%+ (repositorios)
- **Presentation**: 30%+ (UI difícil de testear)

```bash
# Generar reporte de cobertura
pytest --cov=src --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html
```

---

## 🔍 Proceso de Pull Request

### 1. Preparar el PR

```bash
# Asegúrate de que todo funciona
pytest
pytest --cov=src --cov-report=term

# Actualiza tu rama con develop
git checkout develop
git pull upstream develop
git checkout feature/tu-feature
git rebase develop

# Push a tu fork
git push origin feature/tu-feature
```

### 2. Crear el PR en GitHub

**Título**: Formato de commit semántico

```
feat(validadores): añadir validador de DNI con NIF/NIE
```

**Descripción**: Usa esta plantilla

```markdown
## 📋 Descripción

Breve descripción de los cambios.

## 🎯 Motivación

¿Por qué es necesario este cambio?

## 🔧 Cambios Realizados

- [ ] Implementación de ValidadorDNI
- [ ] Tests con 95% cobertura
- [ ] Documentación actualizada

## 🧪 Tests

```bash
pytest tests/test_validador_dni.py -v
# 15 passed in 0.32s
```

## ✅ Checklist

- [x] Tests añadidos y pasando
- [x] Documentación actualizada
- [x] Sin conflictos con develop
- [x] Código sigue estándares
- [x] Commits siguen Conventional Commits

## 🔗 Issues Relacionados

Cierra #123
```

### 3. Code Review

**La rama `main` está protegida con las siguientes reglas**:

#### Branch Protection Rules

| Regla | Requerido | Descripción |
|-------|-----------|-------------|
| **Pull Request** | ✅ Sí | No se permite push directo a `main` |
| **Approving Reviews** | ✅ 1 aprobación | Mínimo un revisor debe aprobar |
| **Status Checks** | ✅ Obligatorios | CI/CD debe pasar antes de merge |
| **Linear History** | ✅ Sí | No se permiten merge commits |
| **Conversation Resolution** | ✅ Sí | Resolver todos los comentarios |

#### Status Checks Obligatorios

Estos checks **deben pasar** antes de hacer merge:

| Check | Descripción | Bloquea Merge |
|-------|-------------|---------------|
| `test (ubuntu-latest, 3.11)` | Tests en Python 3.11 + Ubuntu | ✅ Sí |
| `test (macos-latest, 3.11)` | Tests en Python 3.11 + macOS | ✅ Sí |
| `lint` | Linting y formateo | ✅ Sí |
| `security` | Auditoría de seguridad | ⚠️ No (informativo) |

**¿Qué significa esto para ti?**:

1. ✅ **Tu PR debe pasar CI** antes de que pueda ser mergeado
2. ✅ **Necesitas 1 aprobación** de un maintainer
3. ✅ **Tu rama debe estar actualizada** con `main`
4. ✅ **Todos los comentarios** deben ser resueltos

**Ver detalles en**: [CI_CD.md](CI_CD.md) - Sección "Branch Protection"

#### Estados del Review

- ✅ **Aprobar**: Merge automático (si CI pasa)
- ⚠️ **Request Changes**: Hacer ajustes y solicitar re-review
- 💬 **Comment**: Responder dudas (no bloquea merge)

---

## ➕ Añadir Funcionalidades

### Patrón para Nuevas Features

#### 1. Diseño

Crear documento en `documentacion/`:

```markdown
# Feature: Validador de DNI

## Contexto
Necesitamos validar DNI/NIE de profesores...

## Diseño
- ValidadorDNI value object
- Validación de letra de control
- Soporte NIF/NIE

## Alternativas Consideradas
1. Usar librería externa
2. Implementación propia

## Decisión
Implementación propia por control y simplicidad.

## Consecuencias
+ Control completo
+ Sin dependencias extras
- Mantenimiento propio
```

#### 2. Implementación

Seguir Clean Architecture:

```
1. Domain Layer (entities, value objects)
   ↓
2. Application Layer (use cases, DTOs)
   ↓
3. Infrastructure Layer (repositories, services)
   ↓
4. Presentation Layer (UI, controllers)
```

#### 3. Testing

- Tests unitarios para domain
- Tests de integración para use cases
- Tests de UI manuales

#### 4. Documentación

- Actualizar README si es necesario
- Añadir docstrings
- Crear ejemplos de uso

---

## 📚 Historia del Proyecto

### Evolución por Versiones

Consulta [CHANGELOG.md](../CHANGELOG.md) para ver el historial completo de cambios desde v1.0.0 hasta v3.0.0.

### Sprints de Desarrollo

El proyecto evolucionó a través de 12 sprints principales:

#### Sprints 1-4: Features Core (40%)
- CRUD de profesores y zonas
- Algoritmo de distribución
- Configuración del sistema

#### Sprint 5: Widgets Avanzados (50%)
- Calculador de guardias
- Vista de calendario
- Panel de estadísticas
- Gestión de ausencias

#### Sprint 6: Testing Inicial (60%)
- 300+ tests unitarios
- 60% coverage
- CI/CD setup

#### Sprints 7-8: Observabilidad (70%)
- Logging estructurado
- Sistema de métricas
- Decoradores `@with_metrics`

#### Sprint 9: Clean Architecture (80%)
- Separación en capas
- Dependency injection
- Patrón Repository

#### Sprint 10: Consolidación Testing (85%)
- 873+ tests
- 85% coverage
- Tests de integración

#### Sprint 11: Cleanup & Refactor (87%)
- Eliminación de código duplicado
- Reorganización de archivos
- Documentación consolidada

#### Sprint 12: Finalización (100%)
- v3.0 lanzado
- Refactorización arquitectónica
- Sistema de PDFs corporativos
- Algoritmo v3.0

**Resultado**: Sistema completo, optimizado y documentado en ~100 horas de trabajo.

### Hitos Importantes

| Fecha | Versión | Hito |
|-------|---------|------|
| Mar 2024 | v1.0.0 | Release inicial |
| May 2024 | v2.0.0 | Reescritura con PyQt6 |
| Oct 2024 | v2.5.0 | Gestión de ausencias |
| Dic 2024 | v2.6.0 | Sistema de zona preferida |
| Oct 2025 | v2.9.0 | Fix compilación macOS |
| Oct 2025 | v2.9.1 | Optimizaciones de rendimiento |
| Nov 2025 | v3.0.0 | **Refactorización arquitectónica completa** |

---

## 🧹 Mantenimiento

### Historial de Limpiezas

El proyecto ha tenido varias limpiezas importantes:

#### Noviembre 2025 - Post-Refactorización
- **Eliminado**: 21 archivos obsoletos
- **Archivado**: 3 documentos completados
- **Reorganizado**: ~30 archivos mejor organizados
- **Resultado**: -40% archivos innecesarios

#### Noviembre 2025 - Usuarios y BD
- **Espacio liberado**: ~70 MB
- **Archivos eliminados**: 28
- Usuario activo: `Jefatura_FpBach`

#### Octubre 2025 - Reorganización Completa
- **Archivos eliminados**: 25+
- **Archivos reubicados**: 19
- **Líneas eliminadas**: 4,544
- Scripts organizados en `scripts/{build,dev,maintenance}/`
- Documentación categorizada temáticamente

### Buenas Prácticas Establecidas

1. **Logs**: No commitear archivos `.log`
2. **Builds**: No commitear `build/`, `dist/`
3. **Backups**: No commitear `.backup_*` de BD
4. **Scripts**: Organizar en subdirectorios
5. **Docs**: Categorizar temáticamente
6. **Temporales**: Archivar o eliminar después de cada sesión
7. **Consolidación**: Unir docs relacionados

---

## 📦 Estructura del Proyecto

```
guardias_patio/
├── src/                    # Código fuente
│   ├── application/        # Casos de uso
│   ├── core/               # Núcleo (observability)
│   ├── database/           # Gestión de BD
│   ├── domain/             # Entidades y value objects
│   ├── infrastructure/     # Repositorios y servicios
│   ├── models/             # Modelos SQLAlchemy
│   ├── presentation/       # UI (PyQt6)
│   │   ├── components/     # Componentes reutilizables
│   │   ├── dialogs/        # Diálogos
│   │   ├── forms/          # Formularios principales
│   │   ├── themes/         # Temas Fluent Design
│   │   └── widgets/        # Widgets personalizados
│   ├── services/           # Servicios de negocio
│   ├── sync/               # Sincronización SFTP
│   └── utils/              # Utilidades
├── tests/                  # Tests (976+ tests, 46% coverage)
├── scripts/                # Scripts de utilidad
│   ├── build/              # Compilación
│   ├── dev/                # Desarrollo
│   └── maintenance/        # Mantenimiento BD
├── documentacion/          # Documentación
│   ├── TECHNICAL_GUIDE.md  # Guía técnica completa
│   ├── DEPLOYMENT.md       # Despliegue y distribución
│   ├── USER_GUIDE.md       # Guía de usuario
│   ├── CHANGELOG.md        # Histórico de versiones
│   ├── CONTRIBUTING.md     # Este documento
│   └── archivo/            # Documentación histórica
├── alembic/                # Migraciones de BD
└── ...
```

---

## 🔗 Enlaces Útiles

- **Repositorio**: https://github.com/cferrerobonet/guardias_patio
- **Issues**: https://github.com/cferrerobonet/guardias_patio/issues
- **Releases**: https://github.com/cferrerobonet/guardias_patio/releases
- **Documentación técnica**: [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)
- **Guía de despliegue**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Guía de usuario**: [USER_GUIDE.md](USER_GUIDE.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

## ❓ FAQ

**¿Qué versión de Python necesito?**  
Python 3.11 o superior es obligatorio.

**¿Puedo usar Windows?**  
Sí, la aplicación funciona en Windows, macOS y Linux.

**¿Dónde reporto bugs?**  
En [GitHub Issues](https://github.com/cferrerobonet/guardias_patio/issues).

**¿Cómo propongo una nueva feature?**  
Abre un issue con etiqueta `enhancement` explicando el caso de uso.

**¿Necesito experiencia con PyQt6?**  
No es obligatorio, pero ayuda. La documentación técnica incluye ejemplos.

**¿Cuánto tiempo toma configurar el entorno?**  
Aproximadamente 15-20 minutos siguiendo esta guía.

---

**Última actualización**: 8 de noviembre de 2025  
**Versión**: 3.0.0  
**Mantenido por**: Equipo Guardias de Patio

¡Gracias por contribuir! 🎉
