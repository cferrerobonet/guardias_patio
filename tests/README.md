# Guía de Mejores Prácticas para Tests

## 🚨 REGLA DE ORO: NUNCA TOCAR LA BD DE PRODUCCIÓN

### ❌ NUNCA hacer esto

```python
# ❌ MAL - Usa la BD de producción
from database.db_manager import SessionLocal
session = SessionLocal()  # Esto apunta a guardias_patio.db
```

### ✅ SIEMPRE hacer esto

```python
# ✅ BIEN - Usa fixture session con BD en memoria
def test_algo(session):  # session es un fixture de conftest.py
    profesor = Profesor(nombre_completo="Test", ...)
    session.add(profesor)
    session.commit()
    # Al terminar el test, se hace rollback automático
```

---

## 📋 Fixtures Disponibles

### Base de Datos

#### `session` (scope=function)
- **Uso:** BD en memoria con rollback automático
- **Cuándo:** Para TODOS los tests que necesiten BD
- **Ejemplo:**
  ```python
  def test_crear_profesor(session):
      prof = Profesor(nombre_completo="Juan")
      session.add(prof)
      session.commit()
      assert session.query(Profesor).count() == 1
  ```

#### `db_with_data` (scope=function)
- **Uso:** BD con datos de ejemplo pre-cargados
- **Incluye:** 3 profesores y 3 zonas de ejemplo
- **Ejemplo:**
  ```python
  def test_con_datos(db_with_data):
      profesores = db_with_data.query(Profesor).all()
      assert len(profesores) == 3
  ```

### Factories

#### `profesor_factory(session)`
```python
def test_factory(profesor_factory):
    prof = profesor_factory(
        nombre_completo="María García",
        horas_contrato=25,
        turno="mañana"
    )
    assert prof.id is not None  # Ya está en BD
```

#### `zona_factory(session)`
```python
def test_zonas(zona_factory):
    zona = zona_factory(nombre_zona="Patio A")
    assert zona.id is not None
```

#### `guardia_factory(session)`
```python
def test_guardias(guardia_factory, profesor_factory, zona_factory):
    prof = profesor_factory()
    zona = zona_factory()
    guardia = guardia_factory(
        profesor_id=prof.id,
        zona_id=zona.id,
        fecha=date.today()
    )
    assert guardia.id is not None
```

#### `ausencia_factory(session)`
```python
def test_ausencias(ausencia_factory, profesor_factory):
    prof = profesor_factory()
    ausencia = ausencia_factory(
        profesor_id=prof.id,
        tipo="baja_medica",
        activa=True
    )
    assert ausencia.id is not None
```

---

## 🏷️ Markers de Tests

### Uso de Markers

```python
import pytest

@pytest.mark.unit
def test_logica_pura():
    """Test unitario sin dependencias"""
    assert 1 + 1 == 2

@pytest.mark.db
def test_con_bd(session):
    """Test que usa BD en memoria"""
    pass

@pytest.mark.ui
@pytest.mark.skipif(not GUI_AVAILABLE, reason="No GUI")
def test_interfaz(qapp):
    """Test de interfaz PyQt6"""
    pass

@pytest.mark.integration
def test_flujo_completo(session):
    """Test de integración entre componentes"""
    pass

@pytest.mark.slow
def test_proceso_largo():
    """Test que tarda >1 segundo"""
    pass
```

### Ejecutar solo ciertos markers

```bash
# Solo tests unitarios (rápidos)
pytest -m unit

# Solo tests de BD
pytest -m db

# Excluir tests de UI
pytest -m "not ui"

# Excluir tests lentos
pytest -m "not slow"

# Tests unitarios y de BD, pero sin UI
pytest -m "unit or db and not ui"
```

---

## 🧹 Limpieza de Datos

### Después de ejecutar tests

Si accidentalmente se crearon datos de prueba en la BD de producción:

```bash
# Limpiar profesores de prueba
python scripts/cleanup_test_data.py
```

El script detecta y elimina:
- Nombres con patrón "Profesor N"
- Nombres con "Test" en cualquier parte
- Profesores con nombres de prueba genéricos

---

## 📝 Estructura de un Test Completo

```python
import pytest
from datetime import date
from models.models import Profesor, Zona, Guardia

@pytest.mark.db
class TestCrearGuardia:
    """Suite de tests para creación de guardias"""
    
    def test_crear_guardia_exitosa(
        self, 
        session, 
        profesor_factory, 
        zona_factory
    ):
        """
        DADO un profesor y una zona existentes
        CUANDO se crea una guardia
        ENTONCES la guardia se guarda correctamente
        """
        # Arrange (Preparar)
        profesor = profesor_factory(nombre_completo="Juan Pérez")
        zona = zona_factory(nombre_zona="Patio A")
        
        # Act (Actuar)
        guardia = Guardia(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2025, 10, 19),
            turno="mañana",
            recreo=1
        )
        session.add(guardia)
        session.commit()
        
        # Assert (Verificar)
        guardias = session.query(Guardia).all()
        assert len(guardias) == 1
        assert guardias[0].profesor_id == profesor.id
        assert guardias[0].zona_id == zona.id
    
    def test_crear_guardia_sin_profesor(self, session, zona_factory):
        """
        DADO una zona pero sin profesor
        CUANDO se intenta crear una guardia
        ENTONCES falla con IntegrityError
        """
        from sqlalchemy.exc import IntegrityError
        
        zona = zona_factory()
        guardia = Guardia(
            profesor_id=9999,  # ID que no existe
            zona_id=zona.id,
            fecha=date.today(),
            turno="mañana",
            recreo=1
        )
        session.add(guardia)
        
        with pytest.raises(IntegrityError):
            session.commit()
```

---

## 🎯 Tests de UI con PyQt6

```python
import pytest
from PyQt6.QtWidgets import QApplication

@pytest.mark.ui
def test_ventana_principal(qapp):
    """
    Test de componente UI con QApplication
    """
    from src.main import MainWindow
    
    # qapp es el fixture que proporciona QApplication
    window = MainWindow()
    window.show()
    
    # Verificar que se creó correctamente
    assert window.isVisible()
    assert window.windowTitle() == "Guardias de Patio - Gestión"
    
    # Limpiar
    window.close()
```

---

## 🔧 Configuración de pytest.ini

El archivo `pytest.ini` ya está configurado con:

- ✅ Búsqueda automática de tests en carpeta `tests/`
- ✅ Markers personalizados registrados
- ✅ Coverage habilitado por defecto
- ✅ Output verbose
- ✅ API de Qt configurada (PyQt6)

---

## 📊 Ejecutar Tests con Coverage

```bash
# Coverage completo
pytest

# Coverage solo de un módulo
pytest tests/test_calculador.py

# Ver reporte HTML
pytest && open htmlcov/index.html

# Solo mostrar líneas sin cobertura
pytest --cov-report=term-missing

# Sin coverage (más rápido)
pytest --no-cov
```

---

## 🚀 Comandos Útiles

```bash
# Tests rápidos (solo unitarios, sin UI)
pytest -m "unit and not ui"

# Tests de un archivo específico
pytest tests/test_calculador.py

# Tests que contienen una palabra
pytest -k "profesor"

# Re-ejecutar solo los tests que fallaron
pytest --lf  # last failed

# Re-ejecutar los fallidos primero, luego el resto
pytest --ff  # failed first

# Detener en el primer fallo
pytest -x

# Mostrar prints (sin captura de stdout)
pytest -s

# Tests en paralelo (requiere pytest-xdist)
pytest -n auto
```

---

## ⚠️ Troubleshooting

### Problema: "No module named 'src'"

**Causa:** El path no está configurado

**Solución:** El fixture `conftest.py` ya lo configura automáticamente. Asegúrate de:
1. Ejecutar pytest desde la raíz del proyecto
2. No ejecutar tests con `python tests/test_algo.py`
3. Usar siempre `pytest tests/test_algo.py`

### Problema: "QApplication already created"

**Causa:** Múltiples tests de UI en la misma sesión

**Solución:** El fixture `qapp` ya maneja esto con `scope="session"`

### Problema: "Database is locked"

**Causa:** Múltiples sesiones accediendo a la BD de producción

**Solución:** 
1. ¡Usa el fixture `session`!
2. Nunca uses `SessionLocal()` en tests
3. Si realmente necesitas la BD real, cierra todas las sesiones antes

---

## 📚 Recursos Adicionales

- [Documentación de pytest](https://docs.pytest.org/)
- [pytest-qt documentation](https://pytest-qt.readthedocs.io/)
- [SQLAlchemy testing patterns](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

---

## ✅ Checklist para Crear un Nuevo Test

- [ ] ¿Usa el fixture `session` en lugar de `SessionLocal()`?
- [ ] ¿Tiene el marker apropiado (`@pytest.mark.unit`, `@pytest.mark.db`, etc.)?
- [ ] ¿Usa factories en lugar de crear objetos manualmente?
- [ ] ¿Tiene un docstring descriptivo?
- [ ] ¿Sigue el patrón Arrange-Act-Assert?
- [ ] ¿Verifica solo una cosa (un assert principal)?
- [ ] ¿Tiene un nombre descriptivo (`test_que_hace_cuando_condicion`)?
- [ ] ¿Puede ejecutarse independientemente de otros tests?
- [ ] ¿Se limpia automáticamente (rollback, close, etc.)?
