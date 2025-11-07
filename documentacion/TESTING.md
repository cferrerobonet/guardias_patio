# 🧪 Testing - Guardias de Patio

**Última actualización**: 7 de noviembre de 2025  
**Framework**: pytest 8.4.2  
**Plugins**: pytest-qt, pytest-cov, pytest-mock

---

## 📊 Estado Actual de Tests

### Resumen General

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Total Tests** | 843 | ✅ |
| **Tests Pasando** | 657 (78%) | ⚠️ |
| **Tests Fallando** | 150 (18%) | ⚠️ |
| **Tests con Error** | 58 (7%) | ⚠️ |
| **Tests Omitidos** | 1 | ✅ |
| **Cobertura Global** | **44.63%** | ❌ |
| **Objetivo Cobertura** | ≥80% | 🎯 |

### Cobertura por Capa

| Capa | Cobertura Estimada | Estado | Notas |
|------|-------------------|--------|-------|
| **Domain** | ~90% | ✅ | Bien testeado (entities, value objects) |
| **Application** | ~85% | ✅ | Use cases con buena cobertura |
| **Infrastructure** | ~70% | ⚠️ | Repositorios testeados, faltan mappers |
| **Presentation** | ~5% | ❌ | UI casi sin tests (PyQt6) |
| **Services** | ~60% | ⚠️ | Algunos servicios sin tests |
| **Core** | ~40% | ⚠️ | Logging/observability parcial |

### Tipos de Tests

| Tipo | Cantidad | Cobertura |
|------|----------|-----------|
| **Unitarios** | ~650 | ✅ 85% |
| **Integración** | ~150 | ⚠️ 70% |
| **E2E** | ~40 | ❌ Muchos fallos |
| **UI** | ~50 | ❌ Muchos errores |

---

## 🏃 Ejecutar Tests

### Comandos Básicos

```bash
# Todos los tests
pytest

# Solo tests rápidos (unitarios)
pytest -m "not slow"

# Con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/test_use_cases_profesor.py

# Un solo test
pytest tests/test_use_cases_profesor.py::TestCrearProfesorUseCase::test_crear_profesor_sin_email

# Verbose con traceback
pytest -v --tb=short

# Detener en el primer fallo
pytest -x

# Solo últimos fallos
pytest --lf

# Tests modificados
pytest --testmon
```

### Modos de Ejecución

```bash
# Modo rápido (sin coverage)
pytest -q

# Modo desarrollo (detener en primer error)
pytest -x -v

# Modo CI (con cobertura y reporte XML)
pytest --cov=src --cov-report=xml --cov-report=term-missing

# Modo debug (con prints)
pytest -s

# Tests en paralelo (más rápido)
pytest -n auto  # Requiere pytest-xdist
```

---

## 📂 Estructura de Tests

```
tests/
├── conftest.py                     # Fixtures globales
├── factories/                      # Factories para tests
│   ├── profesor_factory.py
│   ├── zona_factory.py
│   └── guardia_factory.py
│
├── test_use_cases_*.py            # Tests de Use Cases (✅ 90% passing)
│   ├── test_use_cases_profesor.py       # 53 tests
│   ├── test_use_cases_zona.py           # 30 tests
│   ├── test_use_cases_guardia.py        # 40 tests
│   └── test_use_cases_configuracion.py  # 15 tests
│
├── test_domain_*.py               # Tests de Domain (✅ 95% passing)
│   ├── test_entities.py
│   ├── test_value_objects.py
│   └── test_repositories_interfaces.py
│
├── test_infrastructure_*.py       # Tests de Infrastructure (⚠️ 70% passing)
│   ├── test_repositories.py
│   └── test_mappers.py
│
├── test_*_form.py                 # Tests de UI (❌ Muchos errores)
│   ├── test_profesor_form.py           # Errores PyQt6
│   ├── test_zona_form.py
│   ├── test_asignacion_guardias_form.py
│   └── test_gestionar_ausencias.py     # 46 tests, muchos errores
│
└── test_e2e_*.py                  # Tests E2E (❌ Muchos errores)
    ├── test_e2e_flujo_completo.py
    └── test_e2e_validaciones.py
```

---

## ✅ Tests que Funcionan Bien

### Use Cases (Application Layer) - 90% passing

```bash
# Profesor Use Cases
pytest tests/test_use_cases_profesor.py  # 53 tests, 49 passing

# Zona Use Cases
pytest tests/test_use_cases_zona.py  # 30 tests, 26 passing

# Guardia Use Cases
pytest tests/test_use_cases_guardia.py  # 40 tests, 35 passing
```

**Ejemplo de test exitoso**:
```python
def test_crear_profesor_sin_email(session: Session):
    """Test: crear profesor sin email corporativo (campo opcional)."""
    use_case = CrearProfesorUseCase(session)

    dto = CrearProfesorDTO(
        nombre_completo="María López",
        email_corporativo=None,  # Email opcional
        horas_contrato=18.0,
        turno="tarde",
        tutor=False,
    )

    resultado = use_case.execute(dto)

    assert resultado.id > 0
    assert resultado.nombre_completo == "María López"
    assert resultado.email_corporativo is None
    assert resultado.horas_contrato == 18.0
```

---

## ⚠️ Tests con Problemas

### 1. Tests de UI (Presentation Layer)

**Problema**: PyQt6 requiere QApplication

**Tests afectados**: 
- `test_profesor_form.py`
- `test_zona_form.py`
- `test_asignacion_guardias_form.py`
- `test_gestionar_ausencias.py` (46 tests, todos con errores)

**Error típico**:
```python
ERROR: fixture 'qtbot' not found
ERROR: QApplication not initialized
```

**Solución temporal**: Saltar tests de UI
```python
@pytest.mark.skip(reason="Requiere QApplication y configuración compleja")
def test_crear_form():
    pass
```

### 2. Tests E2E

**Problema**: Dependencias complejas entre módulos

**Tests afectados**:
- `test_e2e_flujo_completo.py` (5 errores)
- `test_e2e_validaciones.py` (12 errores)

**Solución**: Revisar y simplificar fixtures

### 3. Tests con Transacciones

**Problema**: SQLAlchemy warnings sobre transacciones

**Error típico**:
```
SAWarning: transaction already deassociated from connection
```

**Solución**: Usar `session.rollback()` en teardown

---

## 🎯 Objetivos de Cobertura

### Prioridades

| Módulo | Actual | Objetivo | Prioridad |
|--------|--------|----------|-----------|
| `domain/` | 90% | 95% | 🔵 Baja |
| `application/` | 85% | 90% | 🟢 Media |
| `infrastructure/` | 70% | 85% | 🟡 Alta |
| `services/` | 60% | 80% | 🟡 Alta |
| `core/` | 40% | 70% | 🟠 Crítica |
| `presentation/` | 5% | 40% | 🟣 Baja (UI compleja) |

### Roadmap de Mejora

**Sprint 1 (Semana 1)**: 44% → 60%
- ✅ Arreglar tests rotos de use cases (4 tests)
- ✅ Añadir tests faltantes en `infrastructure/mappers/`
- ✅ Tests para `core/logging.py`

**Sprint 2 (Semana 2)**: 60% → 75%
- ✅ Tests para `services/` principales (asignador, exportador)
- ✅ Tests de integración para repositorios
- ✅ Arreglar fixture de PyQt6 para tests UI

**Sprint 3 (Semana 3)**: 75% → 80%
- ✅ Tests E2E simplificados
- ✅ Tests para `core/observability/`
- ✅ Coverage badge en README

---

## 🔧 Configuración

### pytest.ini

```ini
[pytest]
minversion = 7.0
addopts = 
    -ra
    -q
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
testpaths = tests
pythonpath = .

markers =
    slow: Marca tests lentos (E2E, integración)
    ui: Tests de interfaz (PyQt6)
    unit: Tests unitarios (rápidos)
    integration: Tests de integración
    e2e: Tests end-to-end
```

### Coverage (.coveragerc)

```ini
[run]
source = src
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*
    */.venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
    if __name__ == .__main__.:
    @abstractmethod
    @abc.abstractmethod
```

---

## 🏗️ Fixtures Importantes

### conftest.py - Fixtures Globales

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models.models import Base

@pytest.fixture(scope="function")
def session() -> Session:
    """Sesión de BD en memoria para cada test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.rollback()
    session.close()

@pytest.fixture
def profesor_factory(session):
    """Factory para crear profesores en tests."""
    def _create_profesor(**kwargs):
        from models.models import Profesor
        defaults = {
            "nombre_completo": "TEST, Profesor",
            "horas_contrato": 25.0,
            "tutor": False,
            "turno": "manana"
        }
        defaults.update(kwargs)
        profesor = Profesor(**defaults)
        session.add(profesor)
        session.commit()
        session.refresh(profesor)
        return profesor
    return _create_profesor
```

---

## 📈 Mejores Prácticas

### 1. Naming Conventions

```python
# ✅ Buenos nombres
def test_crear_profesor_sin_email():
    pass

def test_actualizar_profesor_email_invalido():
    pass

# ❌ Malos nombres
def test_1():
    pass

def test_profesor():
    pass
```

### 2. Estructura AAA (Arrange-Act-Assert)

```python
def test_crear_profesor_exitoso(session):
    # ARRANGE - Preparar datos
    dto = CrearProfesorDTO(
        nombre_completo="Juan Pérez",
        email_corporativo="juan@example.com",
        horas_contrato=25.0,
        turno="manana",
        tutor=True
    )
    use_case = CrearProfesorUseCase(session)
    
    # ACT - Ejecutar acción
    resultado = use_case.execute(dto)
    
    # ASSERT - Verificar resultado
    assert resultado.id > 0
    assert resultado.nombre_completo == "Juan Pérez"
    assert resultado.tutor is True
```

### 3. Usar Factories

```python
# ✅ Con factory (reutilizable)
def test_con_factory(session, profesor_factory):
    prof1 = profesor_factory(nombre_completo="Juan")
    prof2 = profesor_factory(nombre_completo="Ana")
    assert prof1.id != prof2.id

# ❌ Sin factory (duplicación)
def test_sin_factory(session):
    prof1 = Profesor(nombre_completo="Juan", horas_contrato=25.0, ...)
    session.add(prof1)
    session.commit()
    # ... repetir código
```

### 4. Tests Independientes

```python
# ✅ Test independiente
def test_independiente(session, profesor_factory):
    profesor = profesor_factory()  # Crear datos propios
    assert profesor.id > 0

# ❌ Test dependiente (evitar)
shared_profesor = None

def test_dependiente_1(session):
    global shared_profesor
    shared_profesor = Profesor(...)
    session.add(shared_profesor)

def test_dependiente_2():  # Depende de test_dependiente_1
    assert shared_profesor is not None
```

---

## 🐛 Debugging Tests

### Ver output de tests

```bash
# Ver prints
pytest -s

# Ver logs
pytest --log-cli-level=DEBUG

# Ver traceback completo
pytest --tb=long

# Ver solo resumen de errores
pytest --tb=line
```

### Debugger

```python
# Añadir breakpoint en test
def test_debug(session):
    profesor = Profesor(...)
    breakpoint()  # Python 3.7+
    assert profesor.id > 0
```

```bash
# Ejecutar con pdb
pytest --pdb  # Para en el primer fallo

pytest --pdb --maxfail=1  # Para en el primer fallo y abre debugger
```

---

## 📊 Reportes

### Generar Reportes

```bash
# HTML (visual, interactivo)
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal (rápido)
pytest --cov=src --cov-report=term

# XML (para CI/CD)
pytest --cov=src --cov-report=xml

# JSON (programático)
pytest --json-report --json-report-file=report.json
```

### Coverage Badge

```markdown
[![Coverage](https://img.shields.io/badge/coverage-44.63%25-orange)]()
```

Objetivo:
```markdown
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)]()
```

---

## 🚀 CI/CD Integration

### GitHub Actions (ejemplo)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 📚 Referencias

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Estado**: ⚠️ En mejora continua  
**Próxima meta**: 60% cobertura (Sprint 1)  
**Meta final**: 80% cobertura global
