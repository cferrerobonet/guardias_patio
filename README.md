# Guardias de Patio

![MIT License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-2.6.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-orange.svg)
![Arquitectura](https://img.shields.io/badge/Arquitectura-Clean-brightgreen.svg)

Aplicación de escritorio para planificar, asignar, visualizar y exportar las guardias de patio de un centro educativo de forma equitativa y transparente.

## 🆕 Novedades v2.6.0 (18 de Octubre de 2025)

### 🏗️ Sprint 5 Completado: Arquitectura Limpia al 100%

**Migración completa de widgets a Presentation Layer** ✅

Hemos completado la refactorización arquitectónica de todos los widgets, estableciendo un patrón consistente de diseño limpio con inyección de dependencias y separación de responsabilidades.

**Widgets refactorizados (1,813 líneas)**:
- ✅ **VistaCalendario** (349 líneas): Visualización mensual con color-coding
- ✅ **GestorSustituciones** (347 líneas): Sistema de asignación de sustitutos
- ✅ **PanelEstadisticas** (401 líneas): Dashboard con gráficos matplotlib
- ✅ **GestionarAusenciasForm** (716 líneas): CRUD completo de ausencias + reasignación automática

**Beneficios de la refactorización**:
- 🎯 **Arquitectura consistente**: Todos los componentes siguen el mismo patrón
- � **Mantenibilidad mejorada**: Código organizado y documentado
- ✅ **Testeable**: Session injection facilita unit tests
- 📈 **Escalable**: Fácil agregar nuevos componentes

**Total refactorizado (Sprints 4 + 5)**: **~4,280 líneas** de código limpio

📚 **Documentación completa**:
- [Sprint 5: Migración de Widgets](documentacion/SPRINT_5_WIDGETS.md)
- [Changelog v2.6](documentacion/CHANGELOG_v2.6.md)
- [Resumen de Arquitectura v2.6](documentacion/RESUMEN_ARQUITECTURA_v2.6.md)

## 🚀 Objetivo
Automatizar el cálculo y la asignación de guardias (recreos) entre el profesorado según:
- Porcentaje de jornada
- Turno (mañana / tarde / completo)
- Zonas del patio
- Periodo lectivo del curso
- Preferencias y exclusiones (futuro)

## 🏗️ Arquitectura v2.6 - Clean Architecture

Estructura en capas con **separación clara de responsabilidades** y **inyección de dependencias**.

```
src/
 ├── presentation/              # 🆕 CAPA DE PRESENTACIÓN
 │   ├── forms/                 # Formularios CRUD (Sprint 4)
 │   │   ├── base_form.py       # ⭐ Clase base compartida
 │   │   ├── profesor_form.py
 │   │   ├── zona_form.py
 │   │   ├── configuracion_form.py
 │   │   ├── asignacion_guardias_form.py
 │   │   ├── calendario_guardias_form.py
 │   │   └── import_export_form.py
 │   └── widgets/               # Widgets visualización (Sprint 5) 🆕
 │       ├── vista_calendario.py
 │       ├── gestor_sustituciones.py
 │       ├── panel_estadisticas.py
 │       └── gestionar_ausencias.py
 ├── services/                  # CAPA DE SERVICIOS
 │   ├── asignador_guardias.py
 │   ├── calculador_guardias.py
 │   ├── exportador_pdf.py
 │   ├── exportador.py
 │   └── gestor_ausencias.py
 ├── models/                    # CAPA DE DOMINIO
 │   └── models.py              # Profesor, Zona, Guardia, Ausencia, etc.
 ├── database/                  # CAPA DE DATOS
 │   └── db_manager.py          # SessionLocal, engine
 ├── utils/                     # UTILIDADES
 │   ├── logger.py              # Sistema de logging centralizado
 │   ├── validators.py          # Validadores de entrada
 │   ├── constants.py           # Constantes de aplicación
 │   ├── exceptions.py          # Jerarquía de excepciones
 │   └── __init__.py
 ├── ui_styles.py               # Estilos CSS centralizados
 ├── main.py                    # Punto de entrada (MainWindow)
 └── widgets/                   # ⚠️ LEGACY (deprecado)
tests/                          # 124 tests unitarios (98% cobertura utils)
 ├── test_validators.py
 ├── test_exceptions.py
 ├── test_logger.py
 └── ...
alembic/                        # Migraciones de base de datos
documentacion/                  # Documentación completa del proyecto
requirements.txt                # Dependencias
```

**Patrón de diseño establecido**:
```python
class ComponenteUI(BaseForm):
    def __init__(self, session):
        """Session inyectada desde MainWindow"""
        super().__init__(session)
        self.setup_ui()
```

📚 **Documentación de arquitectura**: [RESUMEN_ARQUITECTURA_v2.6.md](documentacion/RESUMEN_ARQUITECTURA_v2.6.md)

## 🗄️ Modelo de Datos (Base inicial)
Tablas principales:
- Profesores: id, nombre, apellidos, horas_contrato, porcentaje_jornada, turno
- Zonas: id, nombre_zona, descripcion
- Configuracion: fechas de curso y horarios de recreos
- Guardias: asignaciones concretas (profesor, fecha, turno, recreo, zona)

Futuro:
- Exclusiones (ausencias temporales)
- Preferencias (afinidad o evitación de zonas)
- Histórico de calendarios

---

## 🛠️ Sistema de Utilidades v2.2

### 📝 Logger (`src/utils/logger.py`)

Sistema de logging centralizado con soporte para archivo y consola.

**Ejemplo de uso básico:**
```python
from src.utils.logger import get_logger, log_function_call

# Obtener logger para el módulo
logger = get_logger(__name__)

# Logging simple
logger.info("Operación iniciada")
logger.error("Error detectado", exc_info=True)

# Decorador para logging automático de funciones
@log_function_call(logger)
def procesar_datos(param1, param2):
    logger.debug(f"Procesando {param1} y {param2}")
    return resultado
```

**Configuración:**
```python
from src.utils.logger import setup_logging

setup_logging(
    log_file="app.log",
    level="DEBUG",
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### ✅ Validadores (`src/utils/validators.py`)

7 validadores con interfaz consistente: `Tuple[bool, Optional[str]]`

**Ejemplos:**
```python
from src.utils.validators import (
    validar_email,
    validar_nombre_completo,
    validar_horas_contrato,
    validar_turno,
    validar_dias_semana
)

# Validar email
valido, error = validar_email("profesor@colegio.es")
if not valido:
    mostrar_error(error)

# Validar nombre en formato "APELLIDOS, NOMBRE"
valido, error = validar_nombre_completo("García López, María")

# Validar horas de contrato (0-40)
valido, error = validar_horas_contrato(25)

# Validar turno (mañana/tarde/mixto)
valido, error = validar_turno("mañana")

# Validar días de la semana
valido, error = validar_dias_semana("lunes,miércoles,viernes")
```

### 📊 Constantes (`src/utils/constants.py`)

Más de 80 constantes organizadas por categorías:

```python
from src.utils.constants import (
    # Metadata
    APP_NAME, APP_VERSION, APP_AUTHOR,
    
    # Turnos
    TURNO_MANANA, TURNO_TARDE, TURNO_MIXTO, TURNOS_VALIDOS,
    
    # Días
    DIA_LUNES, DIA_MARTES, DIAS_SEMANA,
    
    # Validación
    MAX_HORAS_CONTRATO, MAX_GUARDIAS_POR_PROFESOR_DIA,
    
    # UI
    MAX_WIDTH_INPUT_SMALL, MAX_WIDTH_INPUT_MEDIUM,
    
    # Mensajes
    MSG_EXITO_GUARDADO, MSG_ERROR_TITULO, MSG_CONFIRMACION_ELIMINAR
)

# Ejemplo de uso
if horas > MAX_HORAS_CONTRATO:
    QMessageBox.warning(self, MSG_ERROR_TITULO, "Horas excedidas")
```

### ⚠️ Excepciones (`src/utils/exceptions.py`)

Jerarquía de 11 excepciones personalizadas:

```python
from src.utils.exceptions import (
    ValidationError,
    DatabaseError,
    ProfesorNotFoundError,
    MaxGuardiasExceededError,
    InsufficientProfesoresError
)

# Manejo de errores específicos
try:
    profesor = buscar_profesor(profesor_id)
except ProfesorNotFoundError as e:
    logger.error(f"Profesor no encontrado: {e.profesor_id}")
    mostrar_mensaje_error(str(e))
except DatabaseError as e:
    logger.critical(f"Error de BD: {e.detalles}")
    reconectar_base_datos()

# Lanzar excepciones con contexto
if guardias_hoy >= MAX_GUARDIAS:
    raise MaxGuardiasExceededError(
        profesor_nombre=profesor.nombre,
        fecha=fecha.isoformat()
    )
```

### 🧪 Testing

**124 tests unitarios** con **98% de cobertura**:

```bash
# Ejecutar todos los tests
python -m unittest discover tests

# Tests específicos
python -m unittest tests.test_validators
python -m unittest tests.test_exceptions
python -m unittest tests.test_logger

# Con pytest (requiere instalación)
pytest tests/ -v --cov=src/utils
```

**Cobertura por módulo:**
- `validators.py`: 100% (86 tests)
- `exceptions.py`: 100% (23 tests)
- `logger.py`: 95% (15 tests)

---

## 🔢 Algoritmos Clave
1. Cálculo de cargas: determina cuántas guardias debe asumir cada profesor proporcionalmente a su porcentaje de jornada y turno.
2. Asignación: distribuye slots (fecha × recreo × zona × turno) minimizando desequilibrios y evitando conflictos.
3. Reglas de asignación:
   - Prioriza profesor con menor número acumulado de guardias
   - Respeta turno
   - Evita dos guardias el mismo día para la misma persona (si es posible)
   - Evita repetir zona consecutiva (si es posible)

## 🖥️ Interfaz de Usuario
Módulos implementados:
- ✅ **Gestión de profesores**: Alta, visualización y eliminación
- ✅ **Gestión de zonas**: Creación y gestión de zonas de vigilancia
- ✅ **Configuración de curso**: Fechas, horarios de recreos, festivos automáticos, multiplicadores
- ✅ **Generación de calendario**: Cálculo automático de guardias con distribución equitativa
- ✅ **Vista de Calendario**: Visualización interactiva de guardias asignadas con filtros por profesor, zona y turno
- ✅ **Importar/Exportar datos**: Portabilidad completa de datos entre equipos (ver [documentación](documentacion/importar_exportar.md))

Módulos previstos:
- Vista detalle por profesor y por zona
- Regeneración controlada
- Exportación avanzada (Excel / PDF)

## 📤 Exportación e Importación

### ✅ Importar/Exportar Datos (Implementado)
La aplicación permite exportar e importar **todos los datos** (profesores, zonas, configuración, guardias) en formato JSON para:
- **Portabilidad**: Transferir datos entre diferentes equipos
- **Respaldo**: Hacer copias de seguridad completas
- **Migración**: Facilitar actualizaciones de la aplicación

**Características**:
- Exportación completa a archivo JSON con un clic
- Importación con opción de limpieza de datos existentes
- Preservación de todas las relaciones (profesores ↔ guardias, zonas ↔ guardias)
- Formato legible y editable manualmente si es necesario

**Documentación completa**: Ver [documentacion/importar_exportar.md](documentacion/importar_exportar.md)

### 🔜 Exportación Avanzada (Roadmap)
- Excel (openpyxl, pandas): calendario completo + resumen por profesor + distribución por zona
- PDF (reportlab): calendario completo y PDFs individuales por profesor

## ✅ Validaciones & Robustez
- Porcentajes de jornada 0–100
- Fechas válidas (fin > inicio)
- No eliminar entidades en uso (profesores con guardias, zonas asignadas)
- Detección de imposibilidad de cubrir turnos
- Logging centralizado (`utils/logger.py`)

## 🧪 Testing

### ✅ Tests Implementados (v2.2)
- **124 tests unitarios** con **98% de cobertura** del sistema de utilidades
- `tests/test_validators.py`: 86 tests de validación de datos
- `tests/test_exceptions.py`: 23 tests de jerarquía de excepciones
- `tests/test_logger.py`: 15 tests del sistema de logging

### 🔜 Pruebas Previstas
- Unitarias: cálculo de guardias, asignador, servicios CRUD
- Integración: flujo completo (crear datos → configurar → generar → validar)
- Futuro: pruebas sobre ajustes manuales y preferencias

## 🧱 Migraciones
Se gestionan con Alembic. Flujo típico:
```
alembic revision -m "crear tablas base"
alembic upgrade head
```

## 📦 Instalación

### Requisitos Previos
- Python 3.9 o superior
- pip
- macOS, Linux o Windows

### Pasos de Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/cferrerobonet/guardias_patio.git
   cd guardias_patio
   ```

2. **Crear y activar entorno virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

   **⚠️ Nota para macOS**: Si encuentras errores con PyQt6, ejecuta:
   ```bash
   ./fix_pyqt6.sh
   ```
   O consulta `documentacion/solucion_pyqt6.md` para más detalles.

4. **Configurar la base de datos**:
   ```bash
   alembic upgrade head
   ```

5. **Ejecutar la aplicación**:
   ```bash
   ./run_app.sh  # En macOS/Linux
   python src/main.py  # En Windows
   ```

### Solución de Problemas
- **Error de importación de PyQt6**: Ver `documentacion/solucion_pyqt6.md`
- **Error de base de datos**: Asegúrate de ejecutar `alembic upgrade head`
- **Otros errores**: Revisa los logs y reporta issues en GitHub

## 📁 requirements.txt (Inicial sugerido)
```
SQLAlchemy
alembic
PyQt6
python-dateutil
reportlab        # (fase exportación PDF)
openpyxl         # (fase exportación Excel)
pandas           # (fase exportación / estadísticas)
matplotlib       # (fase estadísticas)
```
(Instala solo lo necesario según la fase.)

## ▶️ Ejecución (Esquema preliminar)
```
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
alembic upgrade head
python src/ui/main_window.py
```

## 🤝 Convenciones
Commits (Conventional Commits):
- feat:, fix:, docs:, refactor:, test:, chore:
Ramas: `feat/`, `fix/`, `chore/`, `refactor/`

## 📂 Estructura de Servicios
```
services/
 ├── calculador_guardias.py   # Cálculo de cargas y generación de calendario
 ├── exportador.py            # Exportación e importación de datos JSON
```

Servicios previstos:
```
 ├── profesor_service.py      # CRUD profesores (futuro)
 ├── zona_service.py          # CRUD zonas (futuro)
 ├── configuracion_service.py # Configuración curso (futuro)
 ├── exportador_excel.py      # Exportaciones Excel (roadmap)
 ├── exportador_pdf.py        # Exportaciones PDF (roadmap)
```

## 🧠 Diseño y Patrones
- Repository / DAO para acceso a datos
- Strategy para variantes de asignación futura
- Separación estricta UI ↔ lógica

## 🛡️ Calidad
- Docstrings en funciones públicas
- Tipado opcional (PEP 484) recomendado
- Linter: `ruff` o `flake8` (a incorporar)

## 🗓️ Ejemplo de Cálculo (Escenario base)
Con 180 días lectivos, 4 zonas, 2 recreos/día, turnos completos:
- Slots totales = 180 × 2 × 4 = 1440
- Profesor 100% ≈ 144 guardias si hay 10 profesores equivalentes a jornada completa
- Profesor 50% ≈ 72 guardias

## 🔍 Próximos Pasos Inmediatos
1. Crear `requirements.txt` mínimo e instalar dependencias base
2. Definir modelos SQLAlchemy
3. Inicializar Alembic y primera migración
4. Implementar servicios CRUD
5. Desarrollar algoritmo de cálculo y asignación
6. Conectar con interfaz (PyQt6)

## � Documentación

### Guías de Usuario
- [Vista de Calendario](documentacion/vista_calendario.md) - Visualización interactiva de guardias asignadas
- [Tutorial de Importación/Exportación](documentacion/TUTORIAL_IMPORTAR_EXPORTAR.md) - Guía paso a paso para transferir datos
- [Importar/Exportar Datos](documentacion/importar_exportar.md) - Documentación técnica de portabilidad

### Documentación Técnica
- [Validaciones de Asignación](documentacion/validaciones_asignacion.md) - Guía completa de todas las validaciones del sistema
- [Condiciones Generales de Asignación](documentacion/condiciones_generales_asignacion.md) - Reglas globales de asignación
- [Condiciones Particulares por Profesor](documentacion/condiciones_particulares_profesores.md) - Restricciones individuales

### Guías de Desarrollo
- Pasos de implementación: [paso01](documentacion/paso01.md) a [paso10](documentacion/paso10.md)
- [Solución PyQt6 en macOS](documentacion/solucion_pyqt6.md) - Resolución de problemas de instalación

### Refactorización y Utilidades v2.2
- **[NUEVO]** [Refactorización v2.2](documentacion/REFACTORIZACION_v2.2.md) - Guía completa de utilidades (570 líneas)
- **[NUEVO]** [Resumen Ejecutivo v2.2.1](documentacion/RESUMEN_v2.2.1.md) - Resumen con métricas (255 líneas)

### Arquitectura y Refactorización
- **[NUEVO]** [Resumen de Arquitectura v2.6](documentacion/RESUMEN_ARQUITECTURA_v2.6.md) - Arquitectura limpia completa
- **[NUEVO]** [Sprint 5: Widgets](documentacion/SPRINT_5_WIDGETS.md) - Migración de widgets a Presentation Layer
- **[NUEVO]** [Changelog v2.6](documentacion/CHANGELOG_v2.6.md) - Release notes Sprint 5
- [Refactorización v2.2](documentacion/REFACTORIZACION_v2.2.md) - Sistema de utilidades
- [Resumen Ejecutivo v2.2.1](documentacion/RESUMEN_v2.2.1.md) - Métricas de utilidades

### Notas de Versión
- **[ACTUAL]** [Versión 2.6.0](documentacion/CHANGELOG_v2.6.md) - Arquitectura limpia al 100% (Sprints 4 + 5)
- [Versión 2.2.0](documentacion/RESUMEN_v2.2.1.md) - Sistema de utilidades completo
- [Versión 1.2.0](documentacion/RESUMEN_VALIDACION_NO_SIMULTANEIDAD.md) - Validación de no simultaneidad
- [Versión 1.1.0](documentacion/NOTAS_VERSION_1_1_0.md) - Sistema de importación/exportación

## �📄 Licencia
(Define la licencia: MIT / GPL / privativa según corresponda.)

---
Si necesitas guías más detalladas de cada fase, consulta la carpeta `documentacion/` o solicita un desglose adicional.
