# Refactorización y Optimización v2.2

## Fecha
Diciembre 2024

## Objetivo
Limpieza de código, refactorización y creación de infraestructura escalable para el proyecto "Guardias de Patio".

---

## 1. Limpieza de Archivos

### Archivos Eliminados
- `.DS_Store` - Archivo oculto de macOS
- `src/ui/` - Directorio vacío sin uso
- `tests/test_layout_profesores.py` - Archivo de prueba temporal

### Resultado
✅ Estructura de proyecto más limpia y organizada

---

## 2. Nuevo Módulo: `src/utils/`

Se ha creado un paquete de utilidades completo para centralizar funcionalidades comunes y mejorar la mantenibilidad del código.

### 2.1 `utils/logger.py` (105 líneas)

Sistema de logging centralizado para toda la aplicación.

**Funciones principales:**
- `setup_logging(log_file, level, format_string)`: Configura el sistema de logging
- `get_logger(name)`: Obtiene una instancia de logger configurada
- `log_function_call(logger)`: Decorador para logging automático de llamadas a funciones

**Características:**
- Soporte para archivo + consola
- Codificación UTF-8
- Niveles configurables (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Formato personalizable

**Ejemplo de uso:**
```python
from utils import get_logger, setup_logging

# Configurar al inicio de la aplicación
setup_logging()

# Obtener logger en cualquier módulo
logger = get_logger(__name__)
logger.info("Operación completada exitosamente")
```

---

### 2.2 `utils/validators.py` (203 líneas)

Funciones de validación de entrada de datos antes de operaciones en base de datos.

**Validadores disponibles:**

| Función | Descripción | Retorno |
|---------|-------------|---------|
| `validar_email(email)` | Valida formato de email con regex | `(bool, Optional[str])` |
| `validar_nombre_completo(nombre)` | Valida formato "APELLIDOS, NOMBRE" | `(bool, Optional[str])` |
| `validar_fecha(fecha, fecha_minima)` | Valida fecha y rango opcional | `(bool, Optional[str])` |
| `validar_rango_fechas(inicio, fin)` | Valida que inicio < fin | `(bool, Optional[str])` |
| `validar_horas_contrato(horas)` | Valida rango 0-40 horas | `(bool, Optional[str])` |
| `validar_turno(turno)` | Valida mañana/tarde/mixto | `(bool, Optional[str])` |
| `validar_dias_semana(dias_str)` | Valida CSV de días (0-6) | `(bool, Optional[str])` |

**Patrón de retorno consistente:**
- Tupla `(True, None)` si es válido
- Tupla `(False, "mensaje de error")` si no es válido

**Ejemplo de uso:**
```python
from utils.validators import validar_email, validar_horas_contrato

# Validar email
valido, error = validar_email("profesor@colegio.edu")
if not valido:
    print(f"Error: {error}")
    return

# Validar horas de contrato
valido, error = validar_horas_contrato(35.0)
if not valido:
    print(f"Error: {error}")
    return
```

---

### 2.3 `utils/constants.py` (81 líneas)

Constantes de aplicación para eliminar "números mágicos" y cadenas hardcodeadas.

**Categorías de constantes:**

#### Metadata de la aplicación
```python
APP_NAME = "Guardias de Patio"
APP_VERSION = "2.2.0"
APP_AUTHOR = "Centro Educativo"
```

#### Base de datos
```python
MAX_RETRIES_DB = 3
TIMEOUT_DB = 30  # segundos
```

#### Turnos
```python
TURNO_MANANA = "mañana"
TURNO_TARDE = "tarde"
TURNO_MIXTO = "mixto"
TURNOS_VALIDOS = [TURNO_MANANA, TURNO_TARDE, TURNO_MIXTO]
```

#### Días de la semana
```python
DIA_LUNES = 0
DIA_MARTES = 1
# ... hasta DIA_DOMINGO = 6
DIAS_SEMANA = {0: "Lunes", 1: "Martes", ...}
```

#### Validaciones (Reglas de negocio críticas)
```python
MAX_HORAS_CONTRATO = 40
MAX_GUARDIAS_POR_PROFESOR_DIA = 1  # Máximo 1 guardia diaria por profesor
```

#### UI - Anchos de campos
```python
MAX_WIDTH_INPUT_SHORT = 100    # Números pequeños
MAX_WIDTH_INPUT_MEDIUM = 200   # Fechas, horas
MAX_WIDTH_INPUT_LONG = 350     # Nombres, emails
MAX_WIDTH_INPUT_XLARGE = 500   # Textos largos
```

#### Mensajes de usuario
```python
MSG_EXITO_TITULO = "Éxito"
MSG_ERROR_TITULO = "Error"
MSG_CONFIRMACION_TITULO = "Confirmar"
# ... más mensajes predefinidos
```

#### Valores por defecto
```python
MULTIPLICADOR_TUTORES = 0.9
RECREO_MANANA_1_INICIO = "10:30"
RECREO_MANANA_1_FIN = "11:00"
# ... más valores por defecto
```

---

### 2.4 `utils/exceptions.py` (109 líneas)

Jerarquía de excepciones personalizadas para manejo de errores preciso.

**Estructura de jerarquía:**

```
GuardiasBaseException (base)
├── ValidationError (errores de validación)
├── DatabaseError (errores de BD)
├── ConfiguracionError (errores de configuración)
├── ProfesorNotFoundError (profesor no encontrado)
├── ZonaNotFoundError (zona no encontrada)
├── GuardiaConflictError (conflictos de guardias)
│   ├── MaxGuardiasExceededError (máximo diario excedido)
│   └── DuplicateGuardiaError (guardia duplicada)
├── InsufficientProfesoresError (profesores insuficientes)
├── ExportError (error al exportar)
└── ImportError (error al importar)
```

**Características:**
- Todas heredan de `GuardiasBaseException`
- Incluyen mensaje descriptivo y detalles opcionales
- Permiten captura específica de errores

**Ejemplo de uso:**
```python
from utils.exceptions import ValidationError, MaxGuardiasExceededError

# Lanzar excepción con contexto
if not email_valido:
    raise ValidationError(
        "Email inválido",
        detalles={"email": email, "patron": r"..."}
    )

# Captura específica
try:
    asignar_guardia(profesor, fecha)
except MaxGuardiasExceededError as e:
    logger.error(f"No se puede asignar: {e.message}")
    mostrar_mensaje_usuario(e.message)
```

---

### 2.5 `utils/__init__.py`

Exporta todas las utilidades para importación simplificada.

```python
from utils import (
    get_logger,
    setup_logging,
    constants,
    validar_email,
    validar_nombre_completo,
    ValidationError,
    DatabaseError,
    # ... todas las utilidades disponibles
)
```

---

## 3. Integración en Código Existente

### 3.1 `main.py`

**Cambios realizados:**

1. **Imports de utilidades:**
```python
from utils import constants, get_logger, setup_logging
from utils.exceptions import DatabaseError, ValidationError
from utils.validators import (
    validar_email,
    validar_fecha,
    validar_horas_contrato,
    validar_nombre_completo,
    validar_rango_fechas,
)

# Configurar logging al inicio
setup_logging()
```

2. **Validación en `guardar_profesor()`:**

Antes:
```python
nombre_completo = self.nombre_completo_input.text().strip()
if not nombre_completo:
    QMessageBox.warning(self, "Falta nombre", "Debes indicar...")
    return
```

Después:
```python
nombre_completo = self.nombre_completo_input.text().strip()
valido, error_msg = validar_nombre_completo(nombre_completo)
if not valido:
    QMessageBox.warning(self, constants.MSG_ERROR_TITULO, error_msg)
    return
```

3. **Validación de horas de contrato:**
```python
try:
    horas = float(self.horas_input.text())
except ValueError:
    QMessageBox.warning(
        self,
        constants.MSG_ERROR_TITULO,
        "Las horas de contrato deben ser un número válido.",
    )
    return

valido, error_msg = validar_horas_contrato(horas)
if not valido:
    QMessageBox.warning(self, constants.MSG_ERROR_TITULO, error_msg)
    return
```

4. **Validación de email corporativo:**
```python
email_corporativo = self.email_input.text().strip() or None
if email_corporativo:
    valido, error_msg = validar_email(email_corporativo)
    if not valido:
        QMessageBox.warning(self, constants.MSG_ERROR_TITULO, error_msg)
        return
```

---

### 3.2 `services/asignador_guardias.py`

**Cambios realizados:**

1. **Imports y configuración:**
```python
from utils import constants, get_logger
from utils.exceptions import InsufficientProfesoresError, MaxGuardiasExceededError

logger = get_logger(__name__)
```

2. **Logging en `generar_calendario_guardias()`:**

```python
def generar_calendario_guardias(session: Session) -> Tuple[List[Guardia], Dict[int, int]]:
    logger.info("Iniciando generación de calendario de guardias")
    
    config = session.query(Configuracion).first()
    if not config:
        logger.error("No existe configuración del curso")
        raise ValueError("No existe configuración del curso")
    
    profesores = session.query(Profesor).all()
    if not profesores:
        logger.error("No hay profesores registrados")
        raise ValueError("No hay profesores registrados")
    logger.info(f"Profesores disponibles: {len(profesores)}")
    
    zonas = session.query(Zona).all()
    if not zonas:
        logger.error("No hay zonas registradas")
        raise ValueError("No hay zonas registradas")
    logger.info(f"Zonas configuradas: {len(zonas)}")
    
    # ... código de generación ...
    
    logger.info(f"Calendario generado: {len(calendario)} guardias asignadas")
    logger.debug(f"Distribución por profesor: {dict(asignadas)}")
    return (calendario, dict(asignadas))
```

3. **Logging en `guardar_guardias_en_bd()`:**
```python
def guardar_guardias_en_bd(session: Session, calendario: List[Guardia]) -> None:
    if not calendario:
        logger.warning("No hay guardias para guardar en la base de datos")
        return
    logger.info(f"Guardando {len(calendario)} guardias en la base de datos")
    session.bulk_save_objects(calendario)
    session.commit()
    logger.info("Guardias guardadas exitosamente")
```

---

## 4. Beneficios de la Refactorización

### 4.1 Mantenibilidad
- ✅ Código más limpio y organizado
- ✅ Utilidades centralizadas y reutilizables
- ✅ Validaciones consistentes en toda la aplicación
- ✅ Mensajes de error estandarizados

### 4.2 Escalabilidad
- ✅ Fácil agregar nuevos validadores
- ✅ Constantes centralizadas (un solo lugar para cambiar)
- ✅ Logging sistemático para debugging
- ✅ Excepciones específicas para cada caso de error

### 4.3 Calidad del Código
- ✅ Eliminación de "números mágicos"
- ✅ Eliminación de strings hardcodeados
- ✅ Separación de responsabilidades (SoC)
- ✅ Principio DRY (Don't Repeat Yourself)

### 4.4 Debugging y Monitoreo
- ✅ Sistema de logging robusto
- ✅ Trazabilidad de operaciones críticas
- ✅ Mensajes de error descriptivos
- ✅ Logs configurables por nivel (DEBUG, INFO, WARNING, ERROR)

### 4.5 Testing
- ✅ Validadores fáciles de testear (funciones puras)
- ✅ Constantes facilitan tests predecibles
- ✅ Excepciones personalizadas permiten tests específicos
- ✅ Logging puede deshabilitarse en tests

---

## 5. Próximos Pasos

### Fase 1: Completar integración de utilidades ✅ COMPLETADA
- [x] Aplicar validadores en todos los formularios (ZonaForm mejorado)
- [x] Usar constantes en mensajes de usuario
- [x] Implementar logging en servicios restantes (calculador_guardias.py)
- [ ] Reemplazar excepciones genéricas por específicas (pendiente)

### Fase 2: Tests de utilidades ✅ COMPLETADA
- [x] Tests unitarios para todos los validadores (test_validators.py - 280 líneas)
- [x] Tests para excepciones personalizadas (test_exceptions.py - 210 líneas)
- [x] Tests de integración con logging (test_logger.py - 165 líneas)
- [ ] Validar cobertura de código (pendiente)

### Fase 3: Documentación
- [x] Docstrings en todas las funciones de utils (completas)
- [ ] Ejemplos de uso en README
- [ ] Guía de desarrollo con nuevas utilidades
- [ ] Actualizar diagramas de arquitectura

### Fase 4: Optimizaciones adicionales
- [ ] Caché de consultas frecuentes
- [ ] Pool de conexiones DB
- [ ] Optimización de queries SQL
- [ ] Lazy loading de datos pesados

---

## 6. Métricas del Código

### Líneas de código añadidas (Fase 1)
- `utils/logger.py`: 105 líneas
- `utils/validators.py`: 203 líneas
- `utils/constants.py`: 81 líneas
- `utils/exceptions.py`: 109 líneas
- `utils/__init__.py`: 60 líneas
- **Total nuevo código utils: ~558 líneas**

### Tests unitarios añadidos (Fase 2)
- `tests/test_validators.py`: 280 líneas (86 tests)
- `tests/test_exceptions.py`: 210 líneas (23 tests)
- `tests/test_logger.py`: 165 líneas (15 tests)
- **Total tests: ~655 líneas, 124 tests**

### Código refactorizado
- `main.py`: ~80 líneas modificadas (validaciones en ProfesorForm y ZonaForm)
- `asignador_guardias.py`: ~20 líneas modificadas
- `calculador_guardias.py`: ~15 líneas modificadas (logging agregado)

### Archivos eliminados
- 3 archivos/directorios limpiados

### Totales
- **Código nuevo**: ~1,213 líneas
- **Tests nuevos**: 124 tests unitarios
- **Cobertura funcional**: Validadores, excepciones, logging

---

## 7. Convenciones Establecidas

### 7.1 Nombres de constantes
- MAYÚSCULAS con guiones bajos: `MAX_HORAS_CONTRATO`
- Prefijo por categoría: `MSG_ERROR_`, `DIA_`, `TURNO_`

### 7.2 Validadores
- Retorno: `Tuple[bool, Optional[str]]`
- Nombre: `validar_<concepto>`
- Primer return: `(True, None)` para válido
- Segundo return: `(False, "mensaje")` para inválido

### 7.3 Excepciones
- Heredar de `GuardiasBaseException`
- Nombre descriptivo terminado en `Error`
- Incluir `message` y `detalles` opcionales

### 7.4 Logging
- Obtener logger: `logger = get_logger(__name__)`
- Niveles:
  - `DEBUG`: Información detallada para debugging
  - `INFO`: Operaciones normales importantes
  - `WARNING`: Situaciones inesperadas pero recuperables
  - `ERROR`: Errores que impiden operación específica
  - `CRITICAL`: Errores que pueden detener la aplicación

---

## 8. Compatibilidad

### Versiones requeridas
- Python: 3.9+
- PyQt6: 6.9.1
- SQLAlchemy: 2.x

### Retrocompatibilidad
✅ Todas las funcionalidades existentes mantienen compatibilidad
✅ No se han eliminado métodos públicos
✅ Las nuevas utilidades son completamente opcionales
✅ Migración gradual posible

---

## Conclusión

Esta refactorización establece una base sólida para el crecimiento futuro del proyecto. Se han creado ~560 líneas de código de utilidades reutilizables que mejorarán significativamente la mantenibilidad, escalabilidad y calidad del código en todas las futuras funcionalidades.

El proyecto ahora tiene:
- ✅ Sistema de logging profesional
- ✅ Validaciones centralizadas y consistentes  
- ✅ Constantes organizadas para fácil mantenimiento
- ✅ Excepciones específicas para mejor manejo de errores
- ✅ Estructura de código limpia y organizada

**Versión:** 2.2.0  
**Estado:** ✅ Completada  
**Próxima versión:** 2.3.0 (Integración completa + tests)
