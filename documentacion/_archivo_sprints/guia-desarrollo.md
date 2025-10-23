# 📚 Guía de Desarrollo - Guardias de Patio v2.2

## 🎯 Objetivo

Esta guía establece las mejores prácticas para desarrollar nuevas funcionalidades en el proyecto **Guardias de Patio**, aprovechando el sistema de utilidades implementado en la versión 2.2.

---

## 🏗️ Arquitectura del Proyecto

### Estructura de Capas

```
┌─────────────────────────────────────┐
│         UI Layer (PyQt6)            │  → Interfaz gráfica
│         src/main.py                 │
│         src/widgets/                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Services Layer                │  → Lógica de negocio
│    src/services/                    │
│    - asignador_guardias.py          │
│    - calculador_guardias.py         │
│    - exportador.py                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Models Layer (ORM)            │  → Modelos de datos
│    src/models/                      │
│    - profesor.py                    │
│    - zona.py                        │
│    - guardia.py                     │
│    - configuracion.py               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Database Layer                 │  → Persistencia
│    src/database/                    │
│    - connection.py                  │
└─────────────────────────────────────┘

         ┌────────────────┐
         │ Utils Package  │  → Sistema transversal
         │ src/utils/     │
         │ - logger.py    │
         │ - validators.py│
         │ - constants.py │
         │ - exceptions.py│
         └────────────────┘
```

### Flujo de Datos

```
Usuario → UI → Validadores → Services → Models → Database
                    ↓            ↓         ↓
                 Logger      Excepciones  Logger
```

---

## 🛠️ Uso de Utilidades en Desarrollo

### 1. 📝 Sistema de Logging

#### Configuración Inicial

```python
from src.utils.logger import setup_logging, get_logger

# Al inicio de la aplicación (main.py)
setup_logging(
    log_file="logs/guardias.log",
    level="DEBUG",  # INFO en producción
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

#### Uso en Módulos

```python
from src.utils.logger import get_logger, log_function_call

# Al inicio del archivo
logger = get_logger(__name__)

# Logging básico
logger.debug("Información de depuración")
logger.info("Operación exitosa")
logger.warning("Advertencia: comportamiento inesperado")
logger.error("Error recuperable", exc_info=True)
logger.critical("Error crítico del sistema")

# Decorador para funciones importantes
@log_function_call(logger)
def operacion_critica(param1, param2):
    """Esta función se loguea automáticamente."""
    logger.info(f"Procesando {param1} y {param2}")
    return resultado
```

#### Mejores Prácticas de Logging

✅ **SÍ hacer:**
- Loguear el inicio y fin de operaciones críticas
- Incluir contexto relevante (IDs, nombres, fechas)
- Usar niveles apropiados (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Loguear excepciones con `exc_info=True`
- Usar f-strings para mensajes dinámicos

❌ **NO hacer:**
- Loguear en bucles intensivos (afecta rendimiento)
- Incluir información sensible (contraseñas, datos personales)
- Usar `print()` en lugar de logger
- Loguear todo en nivel INFO

**Ejemplo completo:**

```python
from src.utils.logger import get_logger, log_function_call
from src.utils.exceptions import DatabaseError

logger = get_logger(__name__)

@log_function_call(logger)
def crear_profesor(nombre, email, horas_contrato):
    """Crea un nuevo profesor en la base de datos."""
    logger.info(f"Creando profesor: {nombre}")
    
    try:
        # Operación de base de datos
        profesor = Profesor(nombre=nombre, email=email, horas_contrato=horas_contrato)
        session.add(profesor)
        session.commit()
        
        logger.info(f"Profesor creado exitosamente: ID={profesor.id}")
        return profesor
        
    except SQLAlchemyError as e:
        logger.error(f"Error al crear profesor {nombre}", exc_info=True)
        session.rollback()
        raise DatabaseError(f"No se pudo crear el profesor", detalles=str(e))
```

---

### 2. ✅ Validación de Datos

#### Validar Antes de Procesar

**Todos los datos de entrada deben validarse antes de llegar a la base de datos.**

```python
from src.utils.validators import (
    validar_email,
    validar_nombre_completo,
    validar_horas_contrato,
    validar_turno,
    validar_fecha,
    validar_rango_fechas,
    validar_dias_semana
)
from src.utils.constants import MSG_ERROR_TITULO
from PyQt6.QtWidgets import QMessageBox

def guardar_profesor(self):
    """Guarda un nuevo profesor con validación completa."""
    # 1. Obtener datos del formulario
    nombre = self.input_nombre.text().strip()
    email = self.input_email.text().strip()
    horas = self.input_horas.text().strip()
    
    # 2. Validar nombre
    valido, error = validar_nombre_completo(nombre)
    if not valido:
        QMessageBox.warning(self, MSG_ERROR_TITULO, error)
        self.input_nombre.setFocus()
        return
    
    # 3. Validar email
    valido, error = validar_email(email)
    if not valido:
        QMessageBox.warning(self, MSG_ERROR_TITULO, error)
        self.input_email.setFocus()
        return
    
    # 4. Validar horas
    try:
        horas_int = int(horas)
    except ValueError:
        QMessageBox.warning(self, MSG_ERROR_TITULO, "Las horas deben ser un número")
        return
    
    valido, error = validar_horas_contrato(horas_int)
    if not valido:
        QMessageBox.warning(self, MSG_ERROR_TITULO, error)
        self.input_horas.setFocus()
        return
    
    # 5. Ahora podemos procesar con seguridad
    try:
        self.service.crear_profesor(nombre, email, horas_int)
        QMessageBox.information(self, "Éxito", "Profesor guardado correctamente")
    except Exception as e:
        logger.error(f"Error al guardar profesor", exc_info=True)
        QMessageBox.critical(self, MSG_ERROR_TITULO, str(e))
```

#### Validadores Disponibles

| Validador | Uso | Ejemplo |
|-----------|-----|---------|
| `validar_email(email)` | Formato de email válido | `"usuario@dominio.com"` |
| `validar_nombre_completo(nombre)` | Formato "APELLIDOS, NOMBRE" | `"García López, María"` |
| `validar_horas_contrato(horas)` | 0 ≤ horas ≤ 40 | `25` |
| `validar_turno(turno)` | mañana/tarde/mixto | `"mañana"` |
| `validar_fecha(fecha, minima)` | Fecha válida y >= mínima | `date(2025, 1, 1)` |
| `validar_rango_fechas(inicio, fin)` | inicio < fin | `(date(2025, 1, 1), date(2025, 6, 30))` |
| `validar_dias_semana(dias_str)` | CSV de días válidos | `"lunes,miércoles,viernes"` |

---

### 3. 📊 Uso de Constantes

#### Importar Constantes

```python
from src.utils.constants import (
    # Turnos
    TURNO_MANANA, TURNO_TARDE, TURNO_MIXTO, TURNOS_VALIDOS,
    
    # Días
    DIA_LUNES, DIA_MARTES, DIAS_SEMANA,
    
    # Validación
    MAX_HORAS_CONTRATO, MAX_GUARDIAS_POR_PROFESOR_DIA,
    
    # UI
    MAX_WIDTH_INPUT_SMALL, MAX_WIDTH_INPUT_MEDIUM,
    
    # Mensajes
    MSG_EXITO_GUARDADO, MSG_ERROR_TITULO
)
```

#### Reemplazar Valores Mágicos

❌ **Antes (valores mágicos):**
```python
if turno not in ["mañana", "tarde", "mixto"]:
    QMessageBox.warning(self, "Error", "Turno inválido")

if horas > 40:
    return False

input_nombre.setMaximumWidth(200)
```

✅ **Después (constantes):**
```python
if turno not in TURNOS_VALIDOS:
    QMessageBox.warning(self, MSG_ERROR_TITULO, "Turno inválido")

if horas > MAX_HORAS_CONTRATO:
    return False

input_nombre.setMaximumWidth(MAX_WIDTH_INPUT_MEDIUM)
```

---

### 4. ⚠️ Manejo de Excepciones

#### Jerarquía de Excepciones

```
GuardiasBaseException
├── ValidationError              # Errores de validación
├── DatabaseError                # Errores de base de datos
├── ConfiguracionError           # Errores de configuración
├── ProfesorNotFoundError        # Profesor no encontrado
├── ZonaNotFoundError            # Zona no encontrada
├── GuardiaConflictError         # Base para conflictos
│   ├── MaxGuardiasExceededError # Máximo de guardias excedido
│   └── DuplicateGuardiaError    # Guardia duplicada
├── InsufficientProfesoresError  # Profesores insuficientes
├── ExportError                  # Error en exportación
└── ImportError                  # Error en importación
```

#### Lanzar Excepciones

```python
from src.utils.exceptions import (
    ValidationError,
    ProfesorNotFoundError,
    MaxGuardiasExceededError
)

# Validación
if not nombre:
    raise ValidationError("El nombre del profesor es obligatorio")

# Entidad no encontrada
profesor = session.query(Profesor).get(profesor_id)
if not profesor:
    raise ProfesorNotFoundError(profesor_id=profesor_id)

# Regla de negocio
if guardias_hoy >= MAX_GUARDIAS_POR_PROFESOR_DIA:
    raise MaxGuardiasExceededError(
        profesor_nombre=profesor.nombre,
        fecha=fecha.isoformat()
    )
```

#### Capturar Excepciones

```python
from src.utils.exceptions import (
    ValidationError,
    DatabaseError,
    ProfesorNotFoundError
)

try:
    profesor = self.service.obtener_profesor(profesor_id)
    
except ProfesorNotFoundError as e:
    logger.warning(f"Profesor no encontrado: {e.profesor_id}")
    QMessageBox.warning(self, MSG_ERROR_TITULO, str(e))
    
except DatabaseError as e:
    logger.error(f"Error de BD: {e.detalles}", exc_info=True)
    QMessageBox.critical(self, MSG_ERROR_TITULO, "Error al acceder a la base de datos")
    
except ValidationError as e:
    logger.info(f"Validación fallida: {e}")
    QMessageBox.warning(self, MSG_ERROR_TITULO, str(e))
    
except Exception as e:
    logger.critical(f"Error inesperado", exc_info=True)
    QMessageBox.critical(self, MSG_ERROR_TITULO, "Error inesperado del sistema")
```

---

## 🧪 Testing

### Estructura de Tests

```python
import unittest
from src.utils.validators import validar_email

class TestValidarEmail(unittest.TestCase):
    """Tests del validador de email."""
    
    def test_email_valido(self):
        """Debe aceptar email válido."""
        valido, error = validar_email("profesor@colegio.es")
        self.assertTrue(valido)
        self.assertIsNone(error)
    
    def test_email_sin_arroba(self):
        """Debe rechazar email sin @."""
        valido, error = validar_email("profesorcolegio.es")
        self.assertFalse(valido)
        self.assertIn("formato inválido", error.lower())
    
    def test_email_vacio(self):
        """Debe rechazar email vacío."""
        valido, error = validar_email("")
        self.assertFalse(valido)
        self.assertIn("no puede estar vacío", error.lower())

if __name__ == '__main__':
    unittest.main()
```

### Ejecutar Tests

```bash
# Todos los tests
python -m unittest discover tests

# Módulo específico
python -m unittest tests.test_validators

# Test específico
python -m unittest tests.test_validators.TestValidarEmail

# Con cobertura (requiere pytest y pytest-cov)
pytest tests/ -v --cov=src/utils --cov-report=html
```

---

## 📝 Convenciones de Código

### Nomenclatura

```python
# Clases: PascalCase
class ProfesorService:
    pass

# Funciones/métodos: snake_case
def calcular_guardias_profesor():
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_HORAS_CONTRATO = 40

# Variables: snake_case
profesor_nombre = "García, Juan"
```

### Docstrings

```python
def asignar_guardia(profesor_id: int, fecha: date, turno: str, recreo: int, zona_id: int) -> Guardia:
    """
    Asigna una guardia a un profesor en una fecha y zona específicas.
    
    Args:
        profesor_id: ID del profesor
        fecha: Fecha de la guardia
        turno: Turno (mañana/tarde)
        recreo: Número de recreo (1 o 2)
        zona_id: ID de la zona asignada
    
    Returns:
        Guardia: Objeto Guardia creado
    
    Raises:
        ProfesorNotFoundError: Si el profesor no existe
        ZonaNotFoundError: Si la zona no existe
        MaxGuardiasExceededError: Si el profesor ya tiene máximo de guardias
        DuplicateGuardiaError: Si ya existe una guardia idéntica
    
    Example:
        >>> guardia = asignar_guardia(1, date(2025, 1, 15), "mañana", 1, 2)
        >>> print(guardia.id)
        42
    """
    pass
```

### Imports

```python
# 1. Librerías estándar
import os
import sys
from datetime import date, datetime
from typing import List, Optional, Tuple

# 2. Librerías de terceros
from PyQt6.QtWidgets import QWidget, QMessageBox
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

# 3. Módulos del proyecto
from src.models.profesor import Profesor
from src.services.calculador_guardias import CalculadorGuardias
from src.utils.logger import get_logger
from src.utils.validators import validar_email
from src.utils.constants import TURNO_MANANA, MSG_ERROR_TITULO
from src.utils.exceptions import ValidationError, DatabaseError
```

---

## 🚀 Checklist para Nueva Funcionalidad

### Antes de Empezar
- [ ] Leer documentación de la funcionalidad
- [ ] Identificar modelos/servicios afectados
- [ ] Revisar utilidades disponibles (validators, constants, exceptions)
- [ ] Crear rama feature: `git checkout -b feat/nueva-funcionalidad`

### Durante el Desarrollo
- [ ] Usar constantes en lugar de valores mágicos
- [ ] Validar todos los datos de entrada
- [ ] Implementar logging apropiado
- [ ] Usar excepciones personalizadas
- [ ] Agregar docstrings a funciones públicas
- [ ] Escribir tests unitarios (objetivo: 80%+ cobertura)

### Antes de Commit
- [ ] Ejecutar linter: `ruff check src/`
- [ ] Ejecutar tests: `python -m unittest discover tests`
- [ ] Verificar logging funciona correctamente
- [ ] Actualizar documentación si es necesario
- [ ] Commit con convención: `feat: descripción de la funcionalidad`

### Pull Request
- [ ] Título descriptivo: `feat: nueva funcionalidad XYZ`
- [ ] Descripción detallada de cambios
- [ ] Screenshots si es UI
- [ ] Tests pasan en CI/CD
- [ ] Documentación actualizada

---

## 🔧 Herramientas de Desarrollo

### Linter (Ruff)

```bash
# Verificar código
ruff check src/

# Autofix
ruff check src/ --fix

# Formateo
ruff format src/
```

### Git Workflow

```bash
# Nueva funcionalidad
git checkout -b feat/nombre-funcionalidad

# Commits
git add .
git commit -m "feat: descripción corta"

# Push
git push origin feat/nombre-funcionalidad

# Tipos de commits
# feat: nueva funcionalidad
# fix: corrección de bug
# docs: cambios en documentación
# refactor: refactorización sin cambios funcionales
# test: agregar o modificar tests
# chore: tareas de mantenimiento
```

---

## 📚 Recursos

### Documentación del Proyecto
- [README.md](../README.md) - Información general
- [REFACTORIZACION_v2.2.md](REFACTORIZACION_v2.2.md) - Detalles técnicos de utilidades
- [RESUMEN_v2.2.1.md](RESUMEN_v2.2.1.md) - Resumen ejecutivo

### Documentación Externa
- [PyQt6 Docs](https://doc.qt.io/qtforpython-6/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Python Logging Docs](https://docs.python.org/3/library/logging.html)

---

## 💡 Ejemplos Completos

### Ejemplo 1: Crear un Nuevo Servicio

```python
"""
Servicio para gestión de ausencias de profesores.
"""
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.ausencia import Ausencia
from src.models.profesor import Profesor
from src.utils.logger import get_logger, log_function_call
from src.utils.validators import validar_fecha, validar_rango_fechas
from src.utils.constants import MSG_ERROR_TITULO
from src.utils.exceptions import (
    ValidationError,
    ProfesorNotFoundError,
    DatabaseError
)

logger = get_logger(__name__)

class AusenciaService:
    """Servicio para gestión de ausencias."""
    
    def __init__(self, session: Session):
        self.session = session
    
    @log_function_call(logger)
    def crear_ausencia(
        self,
        profesor_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        motivo: str
    ) -> Ausencia:
        """
        Registra una nueva ausencia de un profesor.
        
        Args:
            profesor_id: ID del profesor
            fecha_inicio: Fecha de inicio de ausencia
            fecha_fin: Fecha de fin de ausencia
            motivo: Motivo de la ausencia
        
        Returns:
            Ausencia creada
        
        Raises:
            ProfesorNotFoundError: Si el profesor no existe
            ValidationError: Si las fechas son inválidas
            DatabaseError: Si hay error en la BD
        """
        logger.info(f"Creando ausencia para profesor {profesor_id}")
        
        # 1. Validar fechas
        valido, error = validar_fecha(fecha_inicio)
        if not valido:
            raise ValidationError(f"Fecha inicio inválida: {error}")
        
        valido, error = validar_rango_fechas(fecha_inicio, fecha_fin)
        if not valido:
            raise ValidationError(f"Rango de fechas inválido: {error}")
        
        # 2. Validar profesor existe
        profesor = self.session.query(Profesor).get(profesor_id)
        if not profesor:
            raise ProfesorNotFoundError(profesor_id=profesor_id)
        
        # 3. Crear ausencia
        try:
            ausencia = Ausencia(
                profesor_id=profesor_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo
            )
            self.session.add(ausencia)
            self.session.commit()
            
            logger.info(f"Ausencia creada: ID={ausencia.id}")
            return ausencia
            
        except Exception as e:
            logger.error("Error al crear ausencia", exc_info=True)
            self.session.rollback()
            raise DatabaseError(
                "No se pudo crear la ausencia",
                detalles=str(e)
            )
    
    def obtener_ausencias_profesor(
        self,
        profesor_id: int,
        fecha_desde: Optional[date] = None
    ) -> List[Ausencia]:
        """Obtiene las ausencias de un profesor."""
        logger.debug(f"Obteniendo ausencias del profesor {profesor_id}")
        
        query = self.session.query(Ausencia).filter(
            Ausencia.profesor_id == profesor_id
        )
        
        if fecha_desde:
            query = query.filter(Ausencia.fecha_fin >= fecha_desde)
        
        return query.order_by(Ausencia.fecha_inicio).all()
```

### Ejemplo 2: Integración en UI

```python
"""
Widget para gestión de ausencias.
"""
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QDateEdit, QPushButton,
    QMessageBox, QTableWidget
)
from PyQt6.QtCore import QDate

from src.services.ausencia_service import AusenciaService
from src.utils.logger import get_logger
from src.utils.constants import (
    MAX_WIDTH_INPUT_LARGE,
    MSG_EXITO_GUARDADO,
    MSG_ERROR_TITULO,
    MSG_CONFIRMACION_ELIMINAR
)
from src.utils.exceptions import (
    ValidationError,
    ProfesorNotFoundError,
    DatabaseError
)

logger = get_logger(__name__)

class AusenciaWidget(QWidget):
    """Widget para registrar ausencias de profesores."""
    
    def __init__(self, session, profesor_id: int):
        super().__init__()
        self.session = session
        self.profesor_id = profesor_id
        self.service = AusenciaService(session)
        
        self.init_ui()
        self.cargar_ausencias()
    
    def init_ui(self):
        """Inicializa la interfaz."""
        layout = QVBoxLayout()
        
        # Formulario
        form_layout = QVBoxLayout()
        
        # Fecha inicio
        self.input_fecha_inicio = QDateEdit()
        self.input_fecha_inicio.setDate(QDate.currentDate())
        self.input_fecha_inicio.setCalendarPopup(True)
        form_layout.addWidget(QLabel("Fecha Inicio:"))
        form_layout.addWidget(self.input_fecha_inicio)
        
        # Fecha fin
        self.input_fecha_fin = QDateEdit()
        self.input_fecha_fin.setDate(QDate.currentDate())
        self.input_fecha_fin.setCalendarPopup(True)
        form_layout.addWidget(QLabel("Fecha Fin:"))
        form_layout.addWidget(self.input_fecha_fin)
        
        # Motivo
        self.input_motivo = QLineEdit()
        self.input_motivo.setMaximumWidth(MAX_WIDTH_INPUT_LARGE)
        self.input_motivo.setPlaceholderText("Motivo de la ausencia")
        form_layout.addWidget(QLabel("Motivo:"))
        form_layout.addWidget(self.input_motivo)
        
        # Botón guardar
        self.btn_guardar = QPushButton("Registrar Ausencia")
        self.btn_guardar.clicked.connect(self.guardar_ausencia)
        form_layout.addWidget(self.btn_guardar)
        
        layout.addLayout(form_layout)
        
        # Tabla de ausencias
        self.tabla_ausencias = QTableWidget()
        layout.addWidget(self.tabla_ausencias)
        
        self.setLayout(layout)
    
    def guardar_ausencia(self):
        """Guarda una nueva ausencia."""
        # Obtener datos
        fecha_inicio = self.input_fecha_inicio.date().toPyDate()
        fecha_fin = self.input_fecha_fin.date().toPyDate()
        motivo = self.input_motivo.text().strip()
        
        # Validar motivo
        if not motivo:
            QMessageBox.warning(
                self,
                MSG_ERROR_TITULO,
                "El motivo de la ausencia es obligatorio"
            )
            return
        
        try:
            # Crear ausencia
            ausencia = self.service.crear_ausencia(
                profesor_id=self.profesor_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo
            )
            
            # Éxito
            QMessageBox.information(
                self,
                "Éxito",
                MSG_EXITO_GUARDADO
            )
            
            # Limpiar formulario
            self.input_motivo.clear()
            self.cargar_ausencias()
            
        except ValidationError as e:
            logger.warning(f"Validación fallida: {e}")
            QMessageBox.warning(self, MSG_ERROR_TITULO, str(e))
            
        except ProfesorNotFoundError as e:
            logger.error(f"Profesor no encontrado: {e.profesor_id}")
            QMessageBox.critical(
                self,
                MSG_ERROR_TITULO,
                "El profesor no existe en la base de datos"
            )
            
        except DatabaseError as e:
            logger.error(f"Error de BD: {e.detalles}", exc_info=True)
            QMessageBox.critical(
                self,
                MSG_ERROR_TITULO,
                "Error al guardar la ausencia"
            )
        
        except Exception as e:
            logger.critical("Error inesperado", exc_info=True)
            QMessageBox.critical(
                self,
                MSG_ERROR_TITULO,
                f"Error inesperado: {str(e)}"
            )
    
    def cargar_ausencias(self):
        """Carga las ausencias en la tabla."""
        try:
            ausencias = self.service.obtener_ausencias_profesor(
                self.profesor_id
            )
            
            # Actualizar tabla
            self.tabla_ausencias.setRowCount(len(ausencias))
            # ... (código de actualización de tabla)
            
        except Exception as e:
            logger.error("Error al cargar ausencias", exc_info=True)
            QMessageBox.warning(
                self,
                MSG_ERROR_TITULO,
                "Error al cargar las ausencias"
            )
```

---

## 🎓 Conclusión

Esta guía establece las bases para un desarrollo consistente y mantenible del proyecto **Guardias de Patio**. Al seguir estas convenciones:

✅ El código será más legible y mantenible  
✅ Los errores se detectarán tempranamente  
✅ El debugging será más sencillo  
✅ Las nuevas funcionalidades se integrarán de forma natural  
✅ El proyecto escalará sin problemas técnicos  

Para dudas o sugerencias, consulta la documentación completa en `documentacion/` o contacta al equipo de desarrollo.

---

**Versión**: 2.2  
**Última actualización**: Enero 2025  
**Mantenedor**: Carlos Ferrero Bonet
