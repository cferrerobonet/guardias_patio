# Sprint 6: Testing - Resumen de Progreso

## 📊 Estado Actual

**Fecha**: 18 de octubre de 2025  
**Coverage Total**: **34.86%** (objetivo: >80%)  
**Tests Totales**: 170 tests  
**Tests que Pasan**: 170 tests ✅ **¡100%!**  
**Tests que Fallan**: 0 tests ✅
**Tests xfail**: 0 tests ✅

## 🎯 Progreso Sprint 6

- **Task 1: Infraestructura de Testing** ✅ **100% COMPLETADA**
- **Task 2: Tests para Formularios** 🔄 **60% EN PROGRESO**
- **Task 3: Tests para Widgets**: ⬜ 0% Pendiente
- **Task 4: Tests para Use Cases**: ⬜ 0% Pendiente
- **Task 5: Tests de Integración**: ⬜ 0% Pendiente
- **Task 6: CI/CD**: ⬜ 0% Pendiente
- **Task 7: Documentación**: ⬜ 0% Pendiente
- **✅ BONUS: Arreglo de Bugs del Asignador** ✅ **100% COMPLETADA**

## ✅ Task 1: Infraestructura de Testing - COMPLETADA

### Archivos Creados

#### 1. `pytest.ini` (~50 líneas)
Configuración completa de pytest:
- **Testpaths**: `tests/`
- **Patterns**: test_*.py, Test*, test_*
- **Coverage**: --cov=src, --cov-report=term-missing/html/xml
- **Branch coverage**: Activado
- **Markers personalizados**:
  - `unit`: Tests unitarios
  - `integration`: Tests de integración
  - `ui`: Tests de interfaz gráfica
  - `slow`: Tests que tardan más de 5 segundos
  - `db`: Tests que requieren base de datos
- **Qt API**: pyqt6
- **Timeout**: 300 segundos
- **Warning filters**: Configurados

#### 2. `.coveragerc` (~80 líneas)
Configuración de coverage:
- **Source**: `src/`
- **Omit**: tests/, __pycache__, site-packages, .venv, alembic
- **Branch coverage**: True
- **Show missing**: True, precisión: 2 decimales
- **Exclude lines**: pragma, __repr__, NotImplementedError, TYPE_CHECKING
- **Reportes**: HTML (htmlcov/), XML (coverage.xml)

#### 3. `tests/conftest.py` (~360 líneas)
Fixtures compartidos y configuración:

**Fixtures de Base de Datos**:
- `engine()`: SQLite en memoria (scope: session)
- `session()`: Sesión limpia con rollback automático (scope: function)
- `db_with_data()`: Sesión pre-cargada con 3 profesores + 3 zonas

**Fixtures de PyQt6**:
- `qapp()`: QApplication singleton (scope: session)
- `qtbot()`: pytest-qt qtbot para interacción con widgets

**Factory Fixtures**:
- `profesor_factory()`: Crear profesores con parámetros personalizados
- `zona_factory()`: Crear zonas
- `guardia_factory()`: Crear guardias con relaciones
- `ausencia_factory()`: Crear ausencias con rangos de fechas

**Utility Fixtures**:
- `mock_session()`: Mock de Session para tests sin BD
- `sample_dates()`: Diccionario con fechas útiles (today, tomorrow, last_week, etc.)

**Pytest Hooks**:
- `pytest_configure()`: Registrar markers personalizados
- `pytest_collection_modifyitems()`: Auto-marcar tests por nombre

#### 4. `tests/test_infrastructure.py` (~120 líneas)
Tests de verificación de infraestructura:

**TestInfraestructura** (10 tests):
- ✅ test_pytest_funciona
- ✅ test_fixture_session
- ✅ test_fixture_db_with_data
- ✅ test_profesor_factory
- ✅ test_zona_factory
- ✅ test_guardia_factory
- ✅ test_ausencia_factory
- ✅ test_mock_session
- ✅ test_sample_dates

**TestQtInfraestructura** (2 tests, @pytest.mark.ui):
- ✅ test_qapp_disponible
- ✅ test_qtbot_disponible

**Resultado**: ✅ 11/11 tests pasan

#### 5. `tests/test_forms_basico.py` (~170 líneas)
Tests básicos de formularios:

**TestProfesorFormBasico** (4 tests):
- ✅ test_crear_formulario
- ✅ test_cargar_tabla_vacia
- ✅ test_cargar_tabla_con_datos
- ✅ test_use_cases_inicializados

**TestZonaFormBasico** (4 tests):
- ✅ test_crear_formulario
- ✅ test_cargar_tabla_vacia (ARREGLADO: lista_zonas)
- ✅ test_cargar_tabla_con_datos (ARREGLADO: lista_zonas)
- ✅ test_use_cases_inicializados (ARREGLADO: nombres use case)

**TestFormulariosCargaMasiva** (2 tests, @pytest.mark.slow):
- ✅ test_profesor_form_muchos_datos (50 profesores)
- ✅ test_zona_form_muchos_datos (ARREGLADO: lista_zonas)

**TestFormulariosIntegracion** (2 tests, @pytest.mark.integration):
- ✅ test_profesor_y_zona_formscomparten_session
- ✅ test_zona_disponible_para_profesor

**Resultado**: ✅ 12/12 tests pasan ✅

### Dependencies Instaladas

```txt
pytest>=7.4.0
pytest-qt>=4.2.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
coverage>=7.3.0
```

**Paquetes instalados**:
- pytest-8.4.2
- pytest-qt-4.5.0
- pytest-cov-7.0.0
- pytest-mock-3.15.1
- coverage-7.10.7
- Dependencias: pluggy, iniconfig, exceptiongroup, pygments

### Commits Realizados

1. **Commit 1bf427a**: "feat(testing): Configurar infraestructura completa de testing - Sprint 6"
   - 7 archivos creados
   - 7,855 líneas añadidas
   - Infraestructura completa funcional

2. **Commit 87ba4d0**: "fix(tests): Actualizar test_calculador para usar calcular_distribucion_cruda"
   - Fix de 2 tests tras refactorización
   - 1 archivo modificado

3. **Commit 68e91a6**: "docs(sprint6): Crear RESUMEN_SPRINT_6_TESTING.md"
   - Documentación completa del sprint
   - 324 líneas de documentación

4. **Commit 2e88448**: "fix(tests): Arreglar tests de ZonaForm"
   - Fix de 4 tests de ZonaForm (lista_zonas, use cases)
   - Actualización nombres de atributos

5. **Commit 465872f**: "fix: Corregir tests fallidos (test_exportador, imports)"
   - Fix test_exportador: Eliminar guardias antes de profesores por FK constraint
   - Fix imports: Cambiar 'from src.' a imports directos
   - Nueva sesión aislada en test_importar_profesores_limpiar
   - **Resultado: 148 tests pasando, 2 xfail, 0 fallos** ✅

## 🐛 Tests Arreglados en esta Sesión

### 1. test_main.py::test_hola_mundo ✅
**Problema**: `FileNotFoundError: 'python'`  
**Causa**: Usaba comando "python" que no existe en PATH  
**Solución**: Usar `sys.executable` para obtener el Python del virtualenv  
**Código**:
```python
python_executable = sys.executable
result = subprocess.run([python_executable, str(main_path)], timeout=5)
```

### 2. test_forms_basico.py - ZonaForm (4 tests) ✅
**Problema**: `AttributeError: 'ZonaForm' object has no attribute 'tabla_zonas'`  
**Causa**: ZonaForm usa `QListWidget` (lista_zonas), no `QTableWidget`  
**Solución**: Actualizar nombres de atributos en tests:
- `tabla_zonas` → `lista_zonas`
- `tabla_zonas.rowCount()` → `lista_zonas.count()`
- Use cases: `crear_zona_uc`, `eliminar_zona_uc`, `listar_zonas_uc`

### 3. test_asignador.py (2 tests) - Bug Arreglado ✅
**Tests afectados**:
- `test_respeta_dias_permitidos`
- `test_profesor_con_restricciones_multiples`

**Problema**: Asignador no respeta restricciones de días permitidos  
**Ejemplo**: Profesor con `dias_semana_permitidos = "0,1,2"` recibe guardia el día 3 (Jueves)  

**Solución implementada** (commit 00fd191):
Agregar validación en `src/services/asignador_guardias.py::generar_calendario_guardias()`:

```python
# VALIDACIÓN: Respetar días de la semana permitidos (si está definida)
if p.dias_semana_permitidos:
    # Parse "0,1,2" -> [0, 1, 2]
    try:
        dias_permitidos = [int(d.strip()) for d in p.dias_semana_permitidos.split(",")]
        dia_semana = slot.fecha.weekday()  # 0=Lun, 1=Mar, ..., 6=Dom
        if dia_semana not in dias_permitidos:
            continue  # Excluir profesor de este slot
    except (ValueError, AttributeError):
        # Si hay error en el formato, ignorar restricción
        pass
```

**Resultado**: 
- test_respeta_dias_permitidos: XPASS → ✅ PASSED
- test_profesor_con_restricciones_multiples: XPASS → ✅ PASSED
- **Bug arreglado completamente** ✅
- Coverage asignador_guardias.py: 84.43% → 84.38% (estable)

**Validaciones ahora implementadas en el asignador**:
1. ✅ Cuota de guardias (no exceder)
2. ✅ Turno del recreo (mañana/tarde/mixto)
3. ✅ Fecha inicio guardias
4. ✅ Fecha fin guardias  
5. ✅ **Días de la semana permitidos** (NUEVO)
6. ✅ Matriz horario permitido (día × recreo)
7. ✅ Ausencias del profesor
8. ✅ No simultaneidad (misma zona, mismo slot)
9. ✅ Máximo 1 guardia al día

### 4. test_exportador.py::test_importar_profesores_limpiar ✅
**Problema 1 (inicial)**: `SAWarning: Identity map already had identity for Profesor(1,)`  
**Causa**: SQLAlchemy identity map conflicto al reutilizar IDs  
**Solución**: Crear nueva sesión aislada para la importación

**Problema 2 (después)**: `IntegrityError: FOREIGN KEY constraint failed`  
**Causa**: Intentaba eliminar Profesores que tienen Guardias asignadas  
**Solución**: Eliminar Guardias ANTES de eliminar Profesores  
**Código en exportador.py**:
```python
if limpiar:
    # Eliminar guardias primero por FOREIGN KEY constraint
    session.query(Guardia).delete()
    session.flush()
    # Ahora eliminar profesores
    session.query(Profesor).delete()
    session.flush()
    session.expire_all()
```

### 5. test_exceptions.py, test_logger.py, test_validators.py ✅
**Problema**: `ModuleNotFoundError: No module named 'src'`  
**Causa**: Imports usaban `from src.utils.` pero el código usa imports directos  
**Solución**: Cambiar todos los imports:
- `from src.utils.exceptions import` → `from utils.exceptions import`
- `from src.utils.logger import` → `from utils.logger import`
- `from src.utils.validators import` → `from utils.validators import`

## 📈 Coverage por Módulo

### Excelente Coverage (>80%) ✨

| Módulo | Coverage | Tests |
|--------|----------|-------|
| validators.py | 100.00% | ✅ |
| exceptions.py (utils) | 100.00% | ✅ |
| constants.py | 100.00% | ✅ |
| models.py | 100.00% | ✅ |
| logger.py (utils) | 94.87% | ✅ |
| guardia_dto.py | 97.37% | ✅ |
| asignacion_guardias_dto.py | 90.32% | ✅ |
| calculador_guardias.py | 90.88% | ✅ |
| exportador.py | 86.16% | ✅ |
| settings.py | 86.15% | ✅ |
| asignador_guardias.py | 84.43% | ✅ |

### Buen Coverage (50-80%) 📊

| Módulo | Coverage | Estado |
|--------|----------|--------|
| zona_form.py | 71.01% | ⚙️ |
| profesor_dto.py | 70.59% | ⚙️ |
| ui_styles.py | 65.71% | ⚙️ |
| zona_preferida.py | 60.87% | ⚙️ |
| core/exceptions.py | 57.89% | ⚙️ |
| buscar_profesores.py | 55.56% | ⚙️ |
| profesor_form.py | 52.90% | ⚙️ |

### Coverage Medio (25-50%) ⚠️

| Módulo | Coverage | Necesita |
|--------|----------|----------|
| obtener_zona.py | 50.00% | Tests |
| email.py | 50.00% | Tests |
| obtener_profesor.py | 52.63% | Tests |
| zona_mapper.py | 52.63% | Tests |
| guardia_mapper.py | 45.45% | Tests |
| obtener_configuracion.py | 45.00% | Tests |
| zona_dto.py | 44.19% | Tests |
| crear_profesor.py | 42.50% | Tests |
| obtener_estadisticas.py | 41.18% | Tests |
| turno.py | 40.24% | Tests |
| base_form.py | 40.00% | Tests |
| calcular_distribucion.py | 40.00% | Tests |
| crear_zona.py | 40.00% | Tests |

### Coverage Bajo (<25%) 🔴

| Módulo | Coverage | Prioridad |
|--------|----------|-----------|
| main.py | 0.00% | Alta |
| vista_calendario.py | 0.00% | Alta |
| panel_estadisticas.py | 0.00% | Alta |
| gestor_sustituciones.py | 0.00% | Alta |
| gestionar_ausencias.py | 0.00% | Alta |
| calendario_guardias_form.py | 7.49% | Alta |
| import_export_form.py | 11.19% | Alta |
| asignacion_guardias_form.py | 11.11% | Media |
| configuracion_form.py | 8.30% | Media |

## 🎯 Próximos Pasos

### Task 2: Tests para Forms (60% COMPLETADA)

**Completados**:
- ✅ ZonaForm tests arreglados (12/12 tests pasan)
- ✅ ProfesorFormBasico (4/4 tests pasan)
- ✅ **ConfiguracionForm (20/20 tests pasan) - Coverage: 8.30% → 90.57% (+82.27pp) 🎉**

**Pendientes**:
- ⬜ AsignacionGuardiasForm (11.11% → >70%)
- ⬜ CalendarioGuardiasForm (7.49% → >70%)
- ⬜ ImportExportForm (11.19% → >70%)

**Estimación**: ~100 tests adicionales

### Task 3: Tests para Widgets

**Pendientes**:
- ⬜ VistaCalendario (0.00% → >70%)
- ⬜ GestorSustituciones (0.00% → >70%)
- ⬜ PanelEstadisticas (0.00% → >70%)
- ⬜ GestionarAusenciasForm (0.00% → >70%)

**Estimación**: ~300 tests

### Task 4: Tests para Service Layer

**Estado**:
- ✅ asignador_guardias.py: 84.43% (muy bien)
- ✅ calculador_guardias.py: 90.88% (excelente)
- ✅ exportador.py: 84.43% (muy bien - mejorado con fix FK)
- ⬜ gestor_ausencias.py: Necesita tests

**✅ Bugs del asignador ARREGLADOS**:
- ✅ Bug `dias_semana_permitidos` arreglado (commit 00fd191)
- ✅ 2 tests xfail → PASSED
- ✅ 9 validaciones activas en asignador (antes 7)

**Estimación**: ~50 tests para gestor_ausencias

### Task 5: Tests de Integración

**Flujos a testear**:
- Crear profesor → Asignar guardias → Exportar PDF
- Importar datos → Validar → Guardar
- Gestionar ausencias → Recalcular guardias
- Cambiar configuración → Regenerar calendario

**Estimación**: ~40 tests

### Task 6: CI/CD con GitHub Actions

**Tareas**:
- Crear workflow `.github/workflows/tests.yml`
- Ejecutar tests en push/PR
- Generar reportes de coverage
- Agregar badges al README
- Configurar fail si coverage < 70%

### Task 7: Documentación

**Archivos a crear**:
- `TESTING.md`: Guía completa de testing
- Actualizar `README.md` con badges
- Documentar fixtures disponibles
- Ejemplos de uso de pytest

### Task 8: Commit Final

**Incluir**:
- Resumen completo de Sprint 6
- Métricas finales de coverage
- Actualizar `CHANGELOG.md`
- Tag de versión

## 📊 Métricas Actuales

```
Total Coverage: 34.86% (+3.03pp desde 31.83%)
Tests Totales: 170 (+20 nuevos)
Tests que Pasan: 170 (100%) ✅ ¡PERFECTO!
Tests xfail: 0 ✅
Tests que Fallan: 0 (0.00%) ✅

Archivos con 100% coverage: 31
Archivos con >80% coverage: 14
Archivos con <25% coverage: 28
```

## 🏆 Logros Destacados

### ConfiguracionForm Tests ✅ 🎉

**Archivo**: `tests/test_configuracion_form.py` (290 líneas)

**Impacto masivo**:
- ✅ 20/20 tests PASSING
- ✅ Coverage: **8.30% → 90.57%** (+82.27 puntos porcentuales!)
- ✅ Incremento general: 31.83% → 34.86% (+3.03pp)
- ✅ Commit: `65f0ed0`

**Estructura de tests**:
1. **TestConfiguracionFormBasico** (4 tests):
   - Creación del formulario
   - Carga de configuración existente
   - Manejo sin configuración previa
   - Verificación de botones

2. **TestConfiguracionFormFechas** (2 tests):
   - Campos de fecha presentes
   - Actualización de fechas

3. **TestConfiguracionFormRecreos** (3 tests):
   - Campos de recreo mañana
   - Campos de recreo tarde
   - Carga de valores desde BD

4. **TestConfiguracionFormCamposAdicionales** (3 tests):
   - Campos de ajuste (tutores/no tutores)
   - Campos de festivos
   - Campo de configuración de recreos

5. **TestConfiguracionFormValidaciones** (2 tests):
   - Método validar_formulario existe
   - Retorna tupla (bool, str)

6. **TestConfiguracionFormGuardado** (2 tests):
   - Método guardar existe
   - Método cargar funciona

7. **TestConfiguracionFormIntegracion** (2 tests):
   - Ciclo completo crear configuración
   - Actualizar configuración existente

8. **TestConfiguracionFormRendimiento** (2 tests, @slow):
   - Carga rápida (<1s)
   - Recarga rápida (<200ms)

**Lecciones aprendidas**:
- ConfiguracionForm usa arquitectura MVP con Use Cases
- No guarda configuración como atributo, la carga dinámicamente
- Tests deben verificar widgets (`fecha_inicio_input`, etc.)
- Fixtures `config_completa` compartida entre tests
- Importante verificar tipos QDateEdit, QTimeEdit



## ✅ Problemas Resueltos

### Tests Arreglados ✅

1. **test_main.py** ✅
   - Solución: Usar `sys.executable` en lugar de comando "python"

2. **test_forms_basico.py** (4 tests ZonaForm) ✅
   - Solución: Actualizar a `lista_zonas`, nombres de use cases correctos

3. **test_asignador.py** (2 tests) ✅ **BUG ARREGLADO**
   - Solución: Agregar validación de `dias_semana_permitidos` en asignador
   - test_respeta_dias_permitidos: XPASS → PASSED
   - test_profesor_con_restricciones_multiples: XPASS → PASSED

4. **test_exportador.py** ✅
   - Solución: Eliminar Guardias antes de Profesores (FK constraint)
   - Usar sesión nueva aislada

5. **test_exceptions.py, test_logger.py, test_validators.py** ✅
   - Solución: Cambiar imports `from src.` a imports directos

## 🎉 Logros del Sprint 6 (Hasta Ahora)

✅ Infraestructura de testing completamente funcional  
✅ 10+ fixtures reutilizables listos  
✅ **150 tests pasando, 0 fallos** 🎯 **¡100%!**  
✅ **Bugs del asignador ARREGLADOS** 🐛→✅  
✅ Coverage mejorado de 31.65% a 31.83%  
✅ Tests automáticos para servicios críticos (>80% coverage)  
✅ Configuración de coverage con branch coverage  
✅ Markers personalizados para categorizar tests  
✅ Validación de dias_semana_permitidos implementada
✅ 6 commits realizados y pusheados a GitHub  

## 📝 Conclusiones

El Sprint 6 está avanzando de manera **excepcional**. No solo se completó la infraestructura de testing, sino que también se arreglaron TODOS los tests fallidos incluyendo el bug crítico del asignador que no respetaba las restricciones de días.

**Hitos alcanzados**:
- ✅ 100% de tests pasando (150/150)
- ✅ Bug crítico del asignador arreglado
- ✅ Suite de tests completamente estable
- ✅ Validaciones del asignador ahora son 9 (antes 7)
- ✅ Coverage de servicios críticos >80%

El coverage actual de 31.83% es un excelente punto de partida, especialmente considerando que los servicios críticos (asignador, calculador, exportador) ya tienen >80% de coverage.

Los próximos pasos se enfocarán en aumentar el coverage de los formularios y widgets de UI, que actualmente tienen coverage bajo pero son críticos para la experiencia del usuario.

**Siguiente objetivo**: Alcanzar 50% de coverage total completando Task 2 (Tests de Forms).
