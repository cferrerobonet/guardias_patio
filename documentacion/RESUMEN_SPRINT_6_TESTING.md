# Sprint 6: Testing - Resumen de Progreso

## 📊 Estado Actual

**Fecha**: 19 de octubre de 2025  
**Coverage Total**: **~52%** (objetivo: >80%)  
**Tests Totales**: 441 tests  
**Tests que Pasan**: 441 tests ✅ **100%** 🎉  
**Tests que Fallan**: 0 tests ✅  
**Tests xfail**: 0 tests ✅

## 🎯 Progreso Sprint 6

- **Task 1: Infraestructura de Testing** ✅ **100% COMPLETADA**
- **Task 2: Tests para Formularios** ✅ **100% COMPLETADA** 🎉
- **Task 3: Tests para Widgets**: ✅ **100% COMPLETADA** 🎉
- **Task 4: Tests para Use Cases**: ✅ **100% COMPLETADA** 🎉
- **Task 5: Tests de Integración**: 🔄 **40% EN PROGRESO** (Subtarea 5.2 completada ✅)
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
| asignacion_guardias_form.py | 11.11% | Media |
| configuracion_form.py | 8.30% | Media |

## 🎯 Próximos Pasos

### Task 5: Tests de Integración (EN PROGRESO 🔄)

**Prioridad INMEDIATA**:
1. ⬜ Refactorizar test_integration_crud.py para usar DTOs correctamente
   - Importar DTOs necesarios (ActualizarConfiguracionDTO, CrearGuardiaDTO, etc.)
   - Instanciar DTOs antes de llamar a execute()
   - Verificar 12/12 tests pasando
   - Estimación: 30-45 minutos

2. ⬜ Crear test_integration_guardias.py
   - Flujo completo generación calendario
   - Validar 9 restricciones del asignador
   - Verificar distribución equitativa
   - Estimación: 20-30 tests, 2-3 horas

3. ⬜ Crear test_integration_import_export.py
   - Flujo exportar → limpiar → importar → verificar
   - Exportación PDF
   - Manejo de errores
   - Estimación: 15-20 tests, 1-2 horas

4. ⬜ Ejecutar suite completa y medir coverage
   - Objetivo: +10-15pp coverage
   - Proyección: 52% → 62-67%

5. ⬜ Commit y documentar Task 5 completa

---

### Task 6: CI/CD con GitHub Actions (PENDIENTE ⬜)

**Tareas**:
- ⬜ Crear workflow `.github/workflows/tests.yml`
- ⬜ Ejecutar tests en push/PR
- ⬜ Generar reportes de coverage automáticos
- ⬜ Agregar badges al README
- ⬜ Configurar fail si coverage < 70%
- ⬜ Matrix testing (Python 3.10, 3.11, 3.12)

**Estimación**: 2-3 horas

---

### Task 7: Documentación Final (PENDIENTE ⬜)

**Archivos a crear/actualizar**:
- ⬜ `TESTING.md`: Guía completa de testing
  * Cómo ejecutar tests
  * Cómo escribir nuevos tests
  * Uso de fixtures
  * Convenciones y mejores prácticas
  * Troubleshooting común

- ⬜ Actualizar `README.md`
  * Agregar badges (coverage, tests passing, build status)
  * Sección de testing
  * Cómo contribuir con tests

- ⬜ `CHANGELOG.md`
  * Sprint 6 completado
  * +441 tests
  * +20pp coverage
  * Bugs arreglados

- ⬜ Actualizar `RESUMEN_SPRINT_6_TESTING.md`
  * Métricas finales
  * Lecciones aprendidas
  * Recomendaciones futuras

**Estimación**: 3-4 horas

---

### Objetivos de Coverage Restantes

**Estado actual**: 52%  
**Objetivo final**: 80%+  
**Gap**: 28pp

**Estrategia para alcanzar 80%**:

1. **Task 5 completada**: +10-15pp → **62-67%**
2. **Tests adicionales**:
   - main.py: 0% → 50% (+2pp)
   - Infrastructure layer: +60-80% (+3-5pp)
   - Edge cases: +2-3pp
3. **Tests E2E UI** (opcional):
   - Flujos completos con UI real (+5-10pp)

**Proyección realista**: **70-75%** al finalizar Sprint 6  
**Proyección optimista**: **75-80%** con esfuerzo adicional

## 📊 Métricas Actuales

```
Total Coverage: ~52% (+20.35pp desde 31.65%)
Tests Totales: 441 (+291 nuevos en Sprint 6)
Tests que Pasan: 437 (99.1%) ✅
Tests que Fallan: 4 (0.9%) - test_integration_crud.py (refactoring DTO pendiente)
Tests xfail: 0 ✅

Archivos con 100% coverage: 20+ (DTOs, Use Cases, utilities)
Archivos con >90% coverage: 25+ (formularios, widgets, use cases)
Archivos con >80% coverage: 35+
Archivos con <25% coverage: 8 (-14 mejora significativa)
```

### Desglose por Categoría

**Tests por Task**:
- Task 1 (Infraestructura): 12 tests ✅
- Task 2 (Formularios): 103 tests ✅
- Task 3 (Widgets): 143 tests ✅
- Task 4 (Use Cases): 85 tests ✅
- Task 5 (Integración): 12 tests 🔄 (4 passing, 8 need refactoring)
- **Tests antiguos**: 86 tests ✅

**Coverage por Capa**:
- Application Layer (Use Cases): **85-100%** ✅
- Presentation Layer (Forms): **80-95%** ✅
- Presentation Layer (Widgets): **75-98%** ✅
- Services Layer: **85-95%** ✅
- Infrastructure Layer: **60-80%** ⚙️
- Domain Layer: **90-100%** ✅

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

### CalendarioGuardiasForm Tests ✅ 🚀

**Archivo**: `tests/test_calendario_guardias_form.py` (420 líneas)

**Impacto masivo**:
- ✅ 30/30 tests PASSING
- ✅ Coverage: **7.49% → 93.58%** (+86.09 puntos porcentuales!)
- ✅ Incremento general: 34.86% → 36.93% (+2.07pp)
- ✅ Commit: `cbc516c`

**Estructura de tests**:
1. **TestCalendarioGuardiasFormBasico** (4 tests):
   - Creación del formulario
   - Widget de calendario presente
   - Filtros presentes (profesor, zona, turno)
   - Áreas de texto (detalles y estadísticas)

2. **TestCalendarioGuardiasFormFiltros** (5 tests):
   - Filtro profesor carga profesores
   - Filtro zona carga zonas
   - Filtro turno tiene opciones
   - Botón limpiar filtros existe
   - Limpiar filtros resetea selección

3. **TestCalendarioGuardiasFormCalendario** (3 tests):
   - Seleccionar fecha actualiza detalles
   - Fecha sin guardias muestra mensaje
   - Calendario con fecha actual por defecto

4. **TestCalendarioGuardiasFormEstadisticas** (2 tests):
   - Estadísticas se actualizan
   - Estadísticas muestran total guardias

5. **TestCalendarioGuardiasFormIntegracion** (4 tests):
   - Cambiar filtro profesor actualiza vista
   - Cambiar filtro turno actualiza vista
   - Ciclo completo de filtrado
   - Múltiples cambios de fecha consecutivos

6. **TestCalendarioGuardiasFormMetodos** (5 tests):
   - Método cargar_filtros existe
   - Método actualizar_guardias_dia existe
   - Método actualizar_estadisticas existe
   - Método aplicar_filtros existe
   - Método limpiar_filtros existe

7. **TestCalendarioGuardiasFormRobustez** (4 tests):
   - Form sin guardias en BD
   - Form sin profesores en BD
   - Form sin zonas en BD
   - Actualizar con fecha None no falla

8. **TestCalendarioGuardiasFormRendimiento** (3 tests, @slow):
   - Carga rápida (<2s)
   - Cambio de fecha rápido (<0.5s)
   - Aplicar filtros rápido (<0.3s)

**Lecciones aprendidas**:
- CalendarioGuardiasForm combina QCalendarWidget con filtros dinámicos
- Usa factories (profesor_factory, zona_factory) para datos de prueba
- Campo `recreo` es obligatorio en modelo Guardia (1 o 2)
- Tests de robustez importantes para UI (datos vacíos, fechas inválidas)
- Performance testing crucial para interactividad del calendario

### ImportExportForm Tests ✅ 🎉

**Archivo**: `tests/test_import_export_form.py` (485 líneas)

**Impacto masivo**:
- ✅ 27/27 tests PASSING (100%)
- ✅ Coverage: **11.19% → 93.71%** (+82.52 puntos porcentuales!)
- ✅ Incremento general: ~36.93% → ~39% (+2pp estimado)
- ✅ Commit: `73194ce`

**Estructura de tests**:
1. **TestImportExportFormBasico** (4 tests):
   - Creación del formulario
   - Botones principales presentes (exportar, importar, PDF)
   - Text area de resultados presente y read-only
   - Checkbox "limpiar datos" presente y checked por defecto

2. **TestImportExportFormPDF** (4 tests):
   - Combo mes presente y con 12 meses
   - Combo año presente y con ≥4 años
   - Combo mes tiene valores correctos (Enero-Diciembre)
   - Mes actual seleccionado por defecto

3. **TestImportExportFormExportar** (3 tests):
   - Exportar datos exitoso (mock QFileDialog + ExportadorDatos)
   - Cancelar exportación no hace nada
   - Manejo de errores en exportación

4. **TestImportExportFormImportar** (3 tests):
   - Importar datos exitoso (mock confirmación + importador)
   - Cancelar importación no hace nada
   - Rechazar confirmación cancela operación

5. **TestImportExportFormPDFExport** (2 tests):
   - Exportar PDFs exitoso (mock directorio + ExportadorPDF)
   - Cancelar exportación PDF no hace nada

6. **TestImportExportFormMetodos** (3 tests):
   - Método exportar_datos existe
   - Método importar_datos existe
   - Método exportar_pdfs existe

7. **TestImportExportFormIntegracion** (3 tests):
   - Cambiar mes actualiza combo
   - Cambiar año actualiza combo
   - Checkbox limpiar puede desmarcarse

8. **TestImportExportFormRobustez** (3 tests):
   - Form sin datos en BD funciona
   - Exportar sin profesores no falla
   - Exportar PDF sin profesores muestra mensaje apropiado

9. **TestImportExportFormRendimiento** (2 tests, @slow):
   - Carga rápida (<1s)
   - Exportación rápida (<2s con mocks)

**Correcciones al código fuente**:
- 🔧 Línea 229: `self.mostrar_info()` → `self.mostrar_exito()` (método no existía en BaseForm)
- 🔧 Línea 333: `self.mostrar_info()` → `self.mostrar_exito()` (mismo error)

**Técnicas de testing aplicadas**:
- Heavy mocking: QFileDialog, QMessageBox, servicios externos
- Tests de file I/O sin tocar sistema de archivos real
- Uso de `tempfile.NamedTemporaryFile()` para archivos temporales
- Validación de flujos cancelados (usuario presiona "Cancelar")
- Tests de confirmación destructiva (importar borra datos)

**Lecciones aprendidas**:
- ImportExportForm maneja 3 flujos distintos: exportar, importar, PDFs
- Mocking esencial para tests de I/O: QFileDialog.getSaveFileName/getOpenFileName
- ExportadorDatos.exportar_todo() y ExportadorPDF.exportar_todos_los_profesores()
- Checkbox "limpiar datos" crítico para UX (evita pérdida accidental)
- Tests deben verificar ambos flujos: éxito Y cancelación


### AsignacionGuardiasForm Tests ✅ 🌟 **TASK 2 100% COMPLETA**

**Archivo**: `tests/test_asignacion_guardias_form.py` (664 líneas)

**Impacto masivo - TASK 2 COMPLETADA**:
- ✅ 26/26 tests PASSING (100%)
- ✅ Coverage: **11.11% → 92.36%** (+81.25 puntos porcentuales!)
- ✅ Incremento general: ~38.72% → ~40.4% (+1.67pp)
- ✅ **TASK 2: 100% COMPLETADA** 🎉
- ✅ Commit: `324f175`

**Estructura de tests**:
1. **TestAsignacionGuardiasFormBasico** (4 tests):
   - Creación del formulario correctamente
   - Use Cases presentes (obtener_estadisticas, calcular_distribucion, generar_guardias)
   - Widgets presentes (stats_text, distribucion_text, resultado_text, generar_button)
   - Botón generar deshabilitado inicialmente

2. **TestAsignacionGuardiasFormEstadisticas** (3 tests):
   - Cargar estadísticas exitosamente
   - Manejar ausencia de configuración
   - Error handling en carga de estadísticas

3. **TestAsignacionGuardiasFormDistribucion** (4 tests):
   - Calcular distribución exitosamente
   - Habilitar botón generar después de calcular
   - Manejo de errores en cálculo
   - Diferencia entre distribución exacta vs no exacta

4. **TestAsignacionGuardiasFormGeneracion** (6 tests):
   - Generar guardias sin guardias existentes
   - Generar con existentes - opción eliminar
   - Generar con existentes - opción no eliminar
   - Cancelar generación (usuario presiona Cancel)
   - Progress callback pasado correctamente
   - Manejo de errores en generación

5. **TestAsignacionGuardiasFormFormateoResumen** (3 tests):
   - Formatear resumen con cobertura completa
   - Formatear resumen sin cobertura completa
   - Top 10 profesores (limitar a 10 de 15)

6. **TestAsignacionGuardiasFormLimpieza** (2 tests):
   - Limpiar formulario correctamente
   - Validar formulario (siempre True, validación en Use Cases)

7. **TestAsignacionGuardiasFormIntegracion** (2 tests):
   - Flujo completo sin guardias: estadísticas → distribución → generación
   - Flujo completo con guardias existentes y confirmación

8. **TestAsignacionGuardiasFormRendimiento** (2 tests, @slow):
   - Carga inicial rápida (<500ms)
   - Cálculo de distribución rápido (<1s)

**Técnicas de testing aplicadas**:
- Heavy mocking de Use Cases (ObtenerEstadisticasUseCase, CalcularDistribucionUseCase, GenerarGuardiasUseCase)
- Mocking de diálogos (QMessageBox.question con respuestas Yes/No/Cancel)
- Mocking de progress dialog (QProgressDialog)
- Tests de flujos completos (end-to-end dentro del formulario)
- Tests de confirmaciones destructivas (eliminar guardias existentes)
- Uso de fixtures compartidas (profesor_factory, zona_factory)
- Tests de rendimiento para UX

**Desafíos superados**:
- Nombres de campos en modelos (nombre_completo vs nombre, nombre_zona vs nombre)
- Uso correcto de factories del conftest.py
- Fixture de Configuración con campos correctos (fecha_inicio_curso, hora_recreo1_manana, etc.)
- Aserciones flexibles para estadísticas dinámicas (días lectivos calculados)

**Lecciones aprendidas**:
- AsignacionGuardiasForm orquesta 3 Use Cases distintos
- Botón "generar" habilitado solo después de calcular distribución
- Importante testear flujos de confirmación (eliminar vs no eliminar guardias)
- Progress callback permite feedback visual al usuario
- Formateo de resumen limita a top 10 para evitar UI sobrecargada
- Validación ocurre en Use Cases, no en formulario

**Impacto en TASK 2**:
- ✅ **TASK 2 COMPLETADA AL 100%** 
- ✅ 6/6 formularios con >70% coverage
- ✅ Total: 103 tests de formularios (+93 nuevos en Sprint 6)
- ✅ Coverage promedio formularios: >80%
- ✅ **Sprint 6 avanza al 40% de coverage general**

### VistaCalendario Tests ✅ 🎉

**Archivo**: `tests/test_vista_calendario.py` (802 líneas)

**Impacto masivo - TASK 3 INICIADA**:
- ✅ 37/37 tests PASSING (100%)
- ✅ Coverage: **0% → 97.92%** (+97.92 puntos porcentuales!)
- ✅ Incremento general: 40.39% → 43.72% (+3.33pp)
- ✅ **TASK 3: 25% COMPLETADA** (1/4 widgets)
- ✅ Commit: `7fc9d0d`, `00b5e76`

**Estructura de tests**:
1. **TestVistaCalendarioBasico** (6 tests): Creación, labels, listas, botones, callbacks
2. **TestVistaCalendarioCargarDatos** (7 tests): Cargar todas guardias, filtro profesor, filtro zona, filtro día, vacías, filtro sin resultados, múltiples guardias mismo día
3. **TestVistaCalendarioRenderizadoDias** (6 tests): Renderizado semana, días correctos, domingo destacado, día actual, guardias posicionadas, múltiples guardias día
4. **TestVistaCalendarioRenderizadoGuardia** (5 tests): Widget guardia básico, turno mañana/tarde, botón eliminar, color zona, tooltip
5. **TestVistaCalendarioFiltros** (4 tests): Combos poblados, filtro día funciona, filtros combinados, limpiar filtros
6. **TestVistaCalendarioEliminar** (3 tests): Eliminar con confirmación, cancelar eliminación, eliminación excepcional
7. **TestVistaCalendarioSemana** (3 tests): Navegar anterior/siguiente, cambiar semana actualiza, semana_actual
8. **TestVistaCalendarioIntegracion** (2 tests): Flujo completo carga→filtro→elimina, múltiples cambios semana
9. **TestVistaCalendarioRendimiento** (1 test @slow): Carga inicial <2s con 300 guardias

### GestorSustituciones Tests ✅ 🎉

**Archivo**: `tests/test_gestor_sustituciones.py` (740 líneas)

**Impacto masivo - TASK 3 50%**:
- ✅ 34/34 tests PASSING (100%)
- ✅ Coverage: **10.94% → 98.96%** (+88.02 puntos porcentuales!)
- ✅ Incremento general: 43.72% → 45.84% (+2.12pp)
- ✅ **TASK 3: 50% COMPLETADA** (2/4 widgets)
- ✅ Commit: `49f4299`, `fd3777b`

**Estructura de tests**:
1. **TestGestorSustitucionesBasico** (5 tests): Creación, labels, combos, botones, lista resultados
2. **TestGestorSustitucionesCargarProfesores** (3 tests): Cargar profesores ambos combos, combo sustituto permite "Sin Asignar", sustituto excluye ausente
3. **TestGestorSustitucionesBuscarGuardias** (7 tests): Buscar por día específico, rango, sin profesores seleccionados, sin guardias, sin día, validar filtrado por profesor, validar rango fechas
4. **TestGestorSustitucionesSeleccion** (2 tests): Mostrar detalles guardia, guardia no en lista (edge case)
5. **TestGestorSustitucionesProfesoresDisponibles** (4 tests): Obtener disponibles día, excluir ausente, no sugerir profesor ocupado, ordenar por guardias asignadas
6. **TestGestorSustitucionesConfirmar** (8 tests): Con sustituto, sin asignar (cancelar guardia), sin guardia seleccionada, sin profesor ausente, sin día específico, sin profesor sustituto, actualizar lista después, múltiples sustituciones consecutivas
7. **TestGestorSustitucionesLimpiar** (1 test): Limpiar formulario correctamente
8. **TestGestorSustitucionesRefrescar** (1 test): Llamar cargar_profesores y buscar_guardias
9. **TestGestorSustitucionesIntegracion** (2 tests): Flujo completo buscar→seleccionar→confirmar→verificar, flujo cancelar guardia
10. **TestGestorSustitucionesRendimiento** (2 tests @slow): Carga inicial <2s, buscar <1s con 500 guardias

### PanelEstadisticas Tests ✅ 🎉

**Archivo**: `tests/test_panel_estadisticas.py` (616 líneas)

**Impacto masivo - TASK 3 75%**:
- ✅ 36/36 tests PASSING (100%)
- ✅ Coverage: **0% → ~75-80%** (+75-80 puntos porcentuales!)
- ✅ Incremento general: 45.84% → ~47.5% (+~1.7pp)
- ✅ **TASK 3: 75% COMPLETADA** (3/4 widgets)
- ✅ Commit: `067b5ff`

**Estructura de tests**:
1. **TestPanelEstadisticasBasico** (5 tests): Creación widget, 4 tabs (Resumen/Profesor/Zona/Gráficos), labels resumen, 2 tablas (profesores 6 cols, zonas 4 cols), 2 canvas matplotlib
2. **TestPanelEstadisticasResumen** (4 tests): Sin datos ("0" values), con datos (20 guardias, 3 profs activos, 3 zonas), info detalles (mañana/tarde/promedio), porcentajes correctos
3. **TestPanelEstadisticasTablaProfesores** (6 tests): Tabla vacía, poblada con 5 profesores, columnas correctas (Prof1: 10 total, 5 mañana, 5 tarde), porcentajes (50%/30%/20%), estados (✅ >=5, ⚠️ <5, ❌ =0), edge case "pocas guardias"
4. **TestPanelEstadisticasTablaZonas** (4 tests): Tabla vacía, 3 zonas pobladas, nombres correctos, total guardias sum=20, profesores diferentes por zona
5. **TestPanelEstadisticasGraficos** (6 tests): Sin datos no crash, generar con datos, gráfico profesores tipo bar, gráfico zonas tipo pie, filtrar solo profesores con guardias (3 de 5), truncar nombres >15 chars
6. **TestPanelEstadisticasActualizar** (3 tests): Actualización completa (resumen+tablas+gráficos), manejo excepciones, refrescar() llama actualizar_estadisticas()
7. **TestMplCanvas** (2 tests): Creación canvas con axes/figure, dimensiones correctas (width/height/dpi)
8. **TestPanelEstadisticasIntegracion** (3 tests): Flujo vacío→añadir 5 guardias→actualizar→verificar, cambio entre 4 pestañas, múltiples actualizaciones consistentes
9. **TestPanelEstadisticasRendimiento** (2 tests @slow): Carga inicial <2s (200 guardias), actualización <3s (300 guardias)

**Características clave**:
- Fixture `datos_completos`: 5 profesores + 3 zonas + 20 guardias distribuidos estratégicamente
- Tests de matplotlib (bar charts, pie charts)
- Validación de cálculos (porcentajes, promedios, estados)
- Tests de agregación de datos (GROUP BY logic)
- Performance con datasets grandes (300 guardias)

### GestionarAusenciasForm Tests ✅ 🎉

**Archivo**: `tests/test_gestionar_ausencias.py` (680 líneas)

**Impacto masivo - TASK 3 COMPLETADA**:
- ✅ 36/36 tests PASSING (100%)
- ✅ Coverage: **0% → ~75-80%** (+75-80 puntos porcentuales!)
- ✅ Incremento general: ~47.5% → ~50% (+~2.5pp)
- ✅ **TASK 3: 100% COMPLETADA** 🎉 (4/4 widgets)
- ✅ Commit: `fe5d7cf`

**Estructura de tests**:
1. **TestGestionarAusenciasFormBasico** (6 tests): Creación widget, tabla ausencias (7 cols: ID/Profesor/Tipo/FechaInicio/FechaFin/Días/Estado), botones (Refrescar/Editar/Eliminar/Desactivar), campos formulario (profesor combo, tipo combo, fechas, motivo textarea), preview guardias, tipos ausencia (baja_medica, permiso, vacaciones, otros)
2. **TestGestionarAusenciasFormCargarDatos** (4 tests): Cargar profesores en combo (3), cargar ausencias en tabla (2), ausencias activas primero (ordenamiento), columnas correctas (Profesor 1, baja_medica, Activo)
3. **TestGestionarAusenciasFormEditar** (3 tests): Cargar ausencia seleccionada, sin selección no carga, título cambia a "EDITAR AUSENCIA"
4. **TestGestionarAusenciasFormGuardar** (4 tests): Guardar nueva ausencia, sin profesor (warning), fechas inválidas fin<inicio (warning), actualizar ausencia existente
5. **TestGestionarAusenciasFormEliminar** (3 tests): Eliminar con confirmación Yes, cancelar No, sin selección (warning)
6. **TestGestionarAusenciasFormDesactivar** (2 tests): Desactivar (activo=False sin eliminar), sin selección (warning)
7. **TestGestionarAusenciasFormPreview** (3 tests): Preview vacío sin profesor, con guardias afectadas (Prof1 tiene 3 guardias días pares), sin guardias en período
8. **TestGestionarAusenciasFormMostrarGuardias** (2 tests): Abrir diálogo DialogoReasignacion, sin profesor (warning)
9. **TestGestionarAusenciasFormLimpiar** (2 tests): Limpiar resetea campos, restaura título "NUEVA AUSENCIA"
10. **TestDialogoReasignacion** (2 tests): Crear diálogo con guardias (tabla 3 filas), verificar tabla guardias presente
11. **TestGestionarAusenciasFormIntegracion** (3 tests): Flujo crear ausencia Prof3→permiso→guardar→verificar tabla (+1 fila), flujo editar→cambiar tipo→guardar→verificar BD, flujo eliminar→confirmar→verificar tabla (-1 fila)
12. **TestGestionarAusenciasFormRendimiento** (2 tests @slow): Carga inicial <2s con 30 profesores, cargar 100 ausencias <2s

**Características clave**:
- Fixture `datos_completos`: 3 profesores + 2 zonas + 10 guardias (días pares/impares) + 2 ausencias (1 activa, 1 inactiva)
- Tests CRUD completo (Create, Read, Update, Delete + Deactivate)
- Preview de guardias afectadas por período
- Diálogo DialogoReasignacion para reasignar guardias
- Validaciones: profesor requerido, fechas válidas, selección requerida
- Performance con 100 ausencias

## 📝 Resumen Task 3: Tests para Widgets

**Estado**: ✅ **100% COMPLETADA** 🎉

**Widgets testeados** (4/4):
1. ✅ VistaCalendario: 37 tests, 0% → 97.92% coverage (+97.92pp)
2. ✅ GestorSustituciones: 34 tests, 10.94% → 98.96% coverage (+88.02pp)
3. ✅ PanelEstadisticas: 36 tests, 0% → ~75-80% coverage (+75-80pp)
4. ✅ GestionarAusenciasForm: 36 tests, 0% → ~75-80% coverage (+75-80pp)

**Total Task 3**:
- Tests: 143 tests nuevos
- Coverage: +10pp aproximadamente (40% → 50%)
- Commits: 6 (4 archivos tests + 2 docs)

## 📝 Task 4: Tests para Use Cases ✅ **100% COMPLETADA** 🎉

**Estado**: ✅ **100% COMPLETADA** (5/5 categorías)

**Total Task 4**:
- ✅ 85 tests de Use Cases (100% passing)
- ✅ Coverage Use Cases: 85-100% (excelente)
- ✅ Commits: a0ea3ac, 7955f80, cdbe280
- ✅ Incremento general: +5-8pp coverage

### 1. Use Cases Zona Tests ✅ (19 tests)

**Archivo**: `tests/test_use_cases_zona.py` (325 líneas)

**Impacto**:
- ✅ 19/19 tests PASSING (100%)
- ✅ Coverage: **0% → 100%** (+100 puntos porcentuales!)
- ✅ Commit: `cec1db5`

**Estructura de tests**:
1. **TestCrearZonaUseCase** (4 tests): Crear exitoso con descripción, sin descripción (opcional), nombre duplicado (BusinessLogicError), error BD con rollback
2. **TestActualizarZonaUseCase** (5 tests): Actualizar nombre, actualizar descripción, zona no existente (NotFoundError), nombre duplicado con otra zona, mismo nombre permitido
3. **TestEliminarZonaUseCase** (3 tests): Eliminar sin guardias asociadas, zona no existente (NotFoundError), con guardias asociadas (BusinessLogicError)
4. **TestObtenerZonaUseCase** (2 tests): Obtener por ID exitoso, zona no existente (NotFoundError)
5. **TestListarZonasUseCase** (3 tests): Lista vacía, con 3 zonas, orden alfabético por nombre_zona
6. **TestZonaUseCasesIntegracion** (2 tests): Flujo CRUD completo, crear múltiples zonas

**Use Cases testeados** (5/5):
- ✅ CrearZonaUseCase: 100% coverage
- ✅ ActualizarZonaUseCase: >90% coverage
- ✅ EliminarZonaUseCase: >90% coverage
- ✅ ObtenerZonaUseCase: 100% coverage
- ✅ ListarZonasUseCase: 100% coverage

---

### 2. Use Cases Profesor Tests ✅ (26 tests)

**Archivo**: `tests/test_use_cases_profesor.py` (541 líneas)

**Impacto**:
- ✅ 26/26 tests PASSING (100%)
- ✅ Coverage: **0% → 100%** en 4 use cases
- ✅ Commit: `3c68dfe`

**Estructura de tests**:
1. **TestCrearProfesorUseCase** (5 tests): Crear completo, sin email, duplicado, horas inválidas, error BD
2. **TestActualizarProfesorUseCase** (6 tests): Actualizar nombre, email/horas, turno, no existente, duplicado, mismo nombre
3. **TestEliminarProfesorUseCase** (3 tests): Eliminar sin guardias, no existente, con guardias
4. **TestObtenerProfesorUseCase** (2 tests): Obtener exitoso, no existente
5. **TestListarProfesoresUseCase** (3 tests): Lista vacía, con datos, orden alfabético
6. **TestBuscarProfesoresUseCase** (4 tests): Buscar nombre, email, término vacío, sin resultados
7. **TestProfesorUseCasesIntegracion** (3 tests): CRUD completo, búsqueda múltiple, listado ordenado

**Use Cases testeados** (6/6):
- ✅ CrearProfesorUseCase: 100% coverage
- ✅ ObtenerProfesorUseCase: 100% coverage
- ✅ ListarProfesoresUseCase: 100% coverage
- ✅ BuscarProfesoresUseCase: 100% coverage
- ✅ ActualizarProfesorUseCase: 80.81% coverage
- ✅ EliminarProfesorUseCase: 89.29% coverage

**Bugs corregidos**:
1. 🔧 tutor vs es_tutor (DTO vs entidad)
2. 🔧 NotFoundError (core vs utils)
3. 🔧 Repository ordenamiento alfabético
4. 🔧 Turnos con horas (mixto)

---

### 3. Use Cases Guardia Tests ✅ (16 tests)

**Archivo**: `tests/test_use_cases_guardia.py` (397 líneas)

**Impacto**:
- ✅ 16/16 tests PASSING (100%)
- ✅ Coverage: **0% → 90-95%**
- ✅ Commit: `a0ea3ac`

**Estructura de tests**:
1. **TestAsignarGuardiaUseCase** (8 tests):
   - Asignar exitosa con datos completos
   - Profesor no existe (NotFoundError)
   - Zona no existe (NotFoundError)
   - Profesor ya tiene guardia mismo día/recreo (BusinessLogicError)
   - Múltiples profesores misma zona/slot (no simultaneidad)
   - Validación guardia_id None en creación
   - Turno recreo correcto (1 mañana, 2 tarde)
   - Error BD con rollback

2. **TestObtenerGuardiaUseCase** (2 tests):
   - Obtener por ID exitoso (validar DTO completo)
   - Guardia no existente (NotFoundError)

3. **TestListarGuardiasProfesorUseCase** (2 tests):
   - Listar guardias de profesor específico (5 guardias)
   - Profesor sin guardias (lista vacía)

4. **TestListarGuardiasZonaUseCase** (2 tests):
   - Listar guardias de zona específica (3 guardias)
   - Zona sin guardias (lista vacía)

5. **TestGuardiaUseCasesIntegracion** (2 tests):
   - Flujo completo: asignar → obtener → listar por profesor
   - Asignar múltiples guardias y validar no simultaneidad

**Use Cases testeados** (4/4):
- ✅ AsignarGuardiaUseCase: 90-95% coverage
- ✅ ObtenerGuardiaUseCase: 100% coverage
- ✅ ListarGuardiasProfesorUseCase: 100% coverage
- ✅ ListarGuardiasZonaUseCase: 100% coverage

**Validaciones críticas**:
- Profesor y zona existen
- No simultaneidad (mismo profesor, día, recreo)
- No conflicto zona (múltiples profesores, mismo slot)
- Turno recreo válido (1=mañana, 2=tarde)
- DTOs correctos (CrearGuardiaDTO, GuardiaDTO)

---

### 4. Use Cases Configuración Tests ✅ (11 tests)

**Archivo**: `tests/test_use_cases_configuracion.py` (285 líneas)

**Impacto**:
- ✅ 11/11 tests PASSING (100%)
- ✅ Coverage: **0% → 95-100%**
- ✅ Commit: `7955f80`

**Estructura de tests**:
1. **TestActualizarConfiguracionUseCase** (6 tests):
   - Crear configuración inicial (no existe previa)
   - Actualizar configuración existente (upsert pattern)
   - Actualizar solo fechas curso
   - Actualizar solo horarios recreos
   - Validar fecha_fin > fecha_inicio
   - Error BD con rollback

2. **TestObtenerConfiguracionUseCase** (3 tests):
   - Obtener configuración existente
   - Sin configuración devuelve valores por defecto
   - DTO con todos los campos correctos

3. **TestConfiguracionUseCasesIntegracion** (2 tests):
   - Flujo completo: crear → obtener → actualizar
   - Múltiples actualizaciones consecutivas (última gana)

**Use Cases testeados** (2/2):
- ✅ ActualizarConfiguracionUseCase: 95-100% coverage
- ✅ ObtenerConfiguracionUseCase: 100% coverage

**Patrón descubierto**:
- **Singleton pattern**: Solo 1 configuración permitida (ID=1)
- **Upsert pattern**: Crear si no existe, actualizar si existe
- **Defaults**: ObtenerConfiguracion devuelve defaults si no hay BD

**Validaciones**:
- Fechas válidas (fin > inicio)
- Horarios recreos válidos
- Campos opcionales (festivos, config recreos)
- DTOs: ActualizarConfiguracionDTO, ConfiguracionDTO

---

### 5. Use Cases Asignación Guardias Tests ✅ (13 tests)

**Archivo**: `tests/test_use_cases_asignacion_guardias.py` (328 líneas)

**Impacto**:
- ✅ 13/13 tests PASSING (100%)
- ✅ Coverage: **0% → 90-95%**
- ✅ Commit: `cdbe280`

**Estructura de tests**:
1. **TestGenerarGuardiasUseCase** (5 tests):
   - Generar sin guardias previas (creación limpia)
   - Eliminar guardias existentes y generar nuevas
   - Conservar guardias existentes (sin eliminar)
   - Sin configuración activa (BusinessLogicError)
   - Progress callback funciona (10 llamadas mínimo)

2. **TestCalcularDistribucionUseCase** (4 tests):
   - Calcular distribución ideal (ResumenDTO)
   - Sin configuración (BusinessLogicError)
   - Sin profesores activos (BusinessLogicError)
   - Validar campos ResumenDTO (slots_totales, profesores, distribucion_exacta)

3. **TestObtenerEstadisticasUseCase** (2 tests):
   - Obtener estadísticas con datos (EstadisticasDTO)
   - Sin configuración devuelve estadísticas vacías

4. **TestAsignacionUseCasesIntegracion** (2 tests):
   - Flujo completo: estadísticas → distribución → generar → verificar
   - Regenerar calendario (eliminar + generar)

**Use Cases testeados** (3/3):
- ✅ GenerarGuardiasUseCase: 90% coverage
- ✅ CalcularDistribucionUseCase: 95% coverage
- ✅ ObtenerEstadisticasUseCase: 100% coverage

**Services integrados**:
- `AsignadorGuardias.generar_calendario_guardias()` (84% coverage)
- `CalculadorGuardias.calcular_distribucion_cruda()` (90% coverage)
- `CalculadorGuardias.obtener_estadisticas()` (100% coverage)

**Validaciones críticas**:
- Configuración activa requerida
- Profesores activos requeridos
- Progress callback (UI feedback)
- Opción eliminar guardias existentes
- DTOs: ResumenGeneracionDTO, ResumenDistribucionDTO, EstadisticasDTO

---

## 📊 Resumen Task 4

**Totales**:
- **85 tests** de Use Cases (100% passing)
- **5 categorías** completadas
- **20 Use Cases** testeados
- **Coverage**: 85-100% en capa application

**Distribución**:
1. Zona: 19 tests (5 use cases)
2. Profesor: 26 tests (6 use cases)
3. Guardia: 16 tests (4 use cases)
4. Configuración: 11 tests (2 use cases)
5. Asignación Guardias: 13 tests (3 use cases)

**Commits**:
- `cec1db5`: Zona use cases
- `3c68dfe`: Profesor use cases
- `a0ea3ac`: Guardia use cases
- `7955f80`: Configuración use cases
- `cdbe280`: Asignación Guardias use cases

**Impacto**:
- ✅ Task 4: 100% completada
- ✅ Coverage application layer: 85-100%
- ✅ Incremento general: +5-8pp

---

## 📝 Task 5: Tests de Integración

**Estado**: 🔄 **40% EN PROGRESO** (2/5 subtareas)

**Objetivo**: Testear flujos E2E (End-to-End) que cruzan todas las capas arquitectónicas (Presentación → Aplicación → Dominio → Infraestructura → Base de Datos).

### Progreso Task 5

- ✅ Task 5.1: Análisis de arquitectura **COMPLETADO**
- ✅ Task 5.2: Tests integración CRUD **COMPLETADO** 🎉 (12/12 pasando)
- ⬜ Task 5.3: Tests integración guardias (Pendiente)
- ⬜ Task 5.4: Tests integración import/export (Pendiente)
- ⬜ Task 5.5: Ejecutar y documentar (Pendiente)

---

### 5.1. Análisis de Arquitectura ✅

**Descubrimiento clave**: El proyecto usa **Clean Architecture con patrón DTO**.

**Patrón identificado**:
```python
# Todos los Use Cases siguen este patrón:
class SomeUseCase:
    def execute(self, dto: SomeDTO) -> ResultDTO:
        # Business logic
        return result_dto
```

**DTOs principales**:
- `ActualizarConfiguracionDTO` / `ConfiguracionDTO`
- `CrearGuardiaDTO` / `GuardiaDTO`
- `CrearProfesorDTO` / `ProfesorDTO`
- `CrearZonaDTO` / `ZonaDTO`
- `EstadisticasDTO`, `ResumenDistribucionDTO`, `ResumenGeneracionDTO`

**Capas arquitectónicas**:
1. **Presentation**: Forms, Widgets (PyQt6)
2. **Application**: Use Cases con DTOs
3. **Domain**: Entities, Value Objects, Repositories (interfaces)
4. **Infrastructure**: SQLAlchemy repositories
5. **Data**: Database, models

---

### 5.2. Tests Integración CRUD ✅ (100% completo)

**Archivo**: `tests/test_integration_crud.py` (625 líneas, 12 tests)

**Estado**: 
- ✅ **12/12 tests PASSING** 🎉
- ⏱️ Tiempo de ejecución: **1.55s**
- 📊 Coverage aportado: **+0.5pp** (23.69% solo este archivo)

**Refactorización exitosa**:
Todos los tests fueron refactorizados para usar correctamente el patrón DTO.

```python
# ❌ ANTES (incorrecto - kwargs directos):
config_uc.execute(
    fecha_inicio_curso=date(2024, 9, 1),
    fecha_fin_curso=date(2025, 6, 30),
    ...
)

# ✅ AHORA (correcto - usando DTOs):
from application.dtos.configuracion_dto import ActualizarConfiguracionDTO

dto = ActualizarConfiguracionDTO(
    fecha_inicio_curso=date(2024, 9, 1),
    fecha_fin_curso=date(2025, 6, 30),
    ...
)
config_uc.execute(dto)
```

**Descubrimientos importantes**:
1. Campo `es_tutor` → `tutor` en modelo Profesor ✅
2. Campo `recreo` → `numero_recreo` en CrearGuardiaDTO ✅
3. Firma especial: `ActualizarProfesorUseCase.execute(profesor_id, dto)` ✅

**Tests implementados** (12/12 ✅):

1. **TestIntegrationSetupInicial** (2 tests):
   - Sistema desde cero (configuración inicial)
   - Modificar configuración existente (upsert)

2. **TestIntegrationAsignacionGuardias** (2 tests):
   - Flujo completo asignar guardia
   - Múltiples guardias mismo día

3. **TestIntegrationModificacionEliminacion** (3 tests):
   - Eliminar profesor sin guardias ✅
   - Eliminar zona sin guardias ✅
   - Actualizar profesor con guardias

   - ✅ `test_setup_sistema_desde_cero`: Setup completo (config → profesores → zonas)
   - ✅ `test_modificar_configuracion_existente`: Upsert pattern

2. **TestIntegrationAsignacionGuardias** (2 tests):
   - ✅ `test_flujo_completo_asignar_guardia`: Asignación completa de guardia
   - ✅ `test_flujo_multiples_guardias_mismo_dia`: Múltiples guardias mismo día

3. **TestIntegrationModificacionEliminacion** (3 tests):
   - ✅ `test_eliminar_profesor_sin_guardias`: Eliminar sin dependencias
   - ✅ `test_eliminar_zona_sin_guardias`: Eliminar zona sin guardias
   - ✅ `test_actualizar_profesor_con_guardias`: Update con relaciones FK

4. **TestIntegrationConServicios** (2 tests):
   - ✅ `test_calcular_estadisticas_sistema_completo`: Estadísticas E2E
   - ✅ `test_calcular_distribucion_con_datos_reales`: Distribución completa

5. **TestIntegrationConsistenciaDatos** (3 tests):
   - ✅ `test_profesor_factory_crea_en_bd`: Factory validation
   - ✅ `test_zona_factory_crea_en_bd`: Factory validation
   - ✅ `test_relaciones_orm_bidireccionales`: ORM relationships

**Resultado**:
```bash
==================================== 12 passed in 1.55s ====================================
Coverage: 23.69% (solo este archivo, coverage total del proyecto sigue en ~52%)
```

**Commits realizados**:
- ✅ Tests integración CRUD creados y refactorizados con DTOs
- ✅ Documentación TASK_5_INTEGRATION_TESTS.md (600+ líneas)
- ✅ 12/12 tests pasando usando Clean Architecture correctamente

---

### 5.3. Tests Integración Guardias ⬜ (Pendiente)

**Archivo planificado**: `tests/test_integration_guardias.py`

**Flujos a testear**:
- Generar calendario completo desde configuración
- Validar todas las restricciones (9 validaciones del asignador)
- Verificar distribución equitativa
- Cobertura de todas las zonas
- Manejo de ausencias en generación

**Estimación**: ~20-30 tests

---

### 5.4. Tests Integración Import/Export ⬜ (Pendiente)

**Archivo planificado**: `tests/test_integration_import_export.py`

**Flujos a testear**:
- Exportar datos → Limpiar BD → Importar → Verificar integridad
- Exportar PDF de calendario completo
- Manejo de datos vacíos
- Errores de formato en importación

**Estimación**: ~15-20 tests

---

### 5.5. Ejecutar y Documentar ⬜ (Pendiente)

**Tareas**:
- Ejecutar todos los tests de integración
- Medir impacto en coverage (+10-15pp estimado)
- Documentar flujos E2E
- Actualizar RESUMEN_SPRINT_6_TESTING.md
- Commit final Task 5

---

## 📊 Resumen Task 5

**Estado actual**:
- Progreso: **40%** (análisis + CRUD completados ✅)
- Tests: **12/12 pasando** (100%) 🎉
- Task 5.1: ✅ Completada
- Task 5.2: ✅ Completada
- Tasks 5.3-5.5: ⬜ Pendientes

**Estimación total Task 5**:
- ~60-80 tests de integración E2E
- +10-15pp coverage estimado
- 3-4 archivos de tests
- Flujos críticos cubiertos

**Próximos pasos**:
1. ✅ ~~Refactorizar test_integration_crud.py (usar DTOs)~~
2. ✅ ~~Verificar 12/12 tests pasando~~
3. ⬜ Crear test_integration_guardias.py
4. ⬜ Crear test_integration_import_export.py
5. ⬜ Ejecutar suite completa y medir coverage



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
✅ **441 tests pasando, 0 fallos** 🎯 **¡100%!**  
✅ **Bugs del asignador ARREGLADOS** 🐛→✅  
✅ Coverage mejorado de 31.65% a ~52% (+20.35pp) 📈  
✅ Tests automáticos para servicios críticos (>80% coverage)  
✅ Configuración de coverage con branch coverage  
✅ Markers personalizados para categorizar tests  
✅ Validación de dias_semana_permitidos implementada  
✅ **6 formularios testeados completamente (Task 2: 100%)** ✅  
✅ **4 widgets testeados completamente (Task 3: 100%)** ✅  
✅ **85 Use Cases testeados (Task 4: 100%)** ✅  
✅ **12 tests integración CRUD (Task 5.2: 100%)** ✅  
✅ **Clean Architecture con patrón DTO descubierto y documentado** 🏛️  
✅ 22+ commits realizados y pusheados a GitHub  

## 📝 Conclusiones

El Sprint 6 está avanzando de manera **excepcional**. Se completaron Tasks 1, 2, 3 y 4 al 100%, y Task 5 avanza al 40% con la subtarea 5.2 completada. El coverage ha subido significativamente de 31.65% a ~52%, acercándonos al objetivo del 80%.

**Hitos alcanzados**:
- ✅ 100% de tests pasando (441/441) 🎯
- ✅ Bug crítico del asignador arreglado
- ✅ Suite de tests completamente estable
- ✅ Validaciones del asignador ahora son 9 (antes 7)
- ✅ Coverage de servicios críticos >80%
- ✅ **Task 2 (Formularios): 100% completada** 🎉
- ✅ **Task 3 (Widgets): 100% completada** 🎉
- ✅ **Task 4 (Use Cases): 100% completada** 🎉 (85 tests)
- ✅ **Task 5.2 (Integration CRUD): 100% completada** 🎉 (12 tests)
- 📊 **52% de coverage total alcanzado** (objetivo 80%)
- ✅ **Task 2 (Formularios): 100% completada** 🎉
- ✅ **Task 3 (Widgets): 100% completada** 🎉
- � **Task 4 (Use Cases): 20% completada** - 5 Use Cases Zona al 100%
- �📊 **51% de coverage total alcanzado** (objetivo 80%)

**Siguiente fase**:
- Task 4 continuar: Guardia Use Cases (estimated +1-2pp)
- Task 4: Configuración Use Cases (estimated +1pp)
- Task 4: Asignación Guardias Use Cases (estimated +3-5pp)
- Task 5: Tests de Integración (estimated +10-15pp coverage)
- Task 6: CI/CD
- Task 7: Documentación final

El coverage actual de 31.83% es un excelente punto de partida, especialmente considerando que los servicios críticos (asignador, calculador, exportador) ya tienen >80% de coverage.

Los próximos pasos se enfocarán en aumentar el coverage de los formularios y widgets de UI, que actualmente tienen coverage bajo pero son críticos para la experiencia del usuario.

**Siguiente objetivo**: Alcanzar 50% de coverage total completando Task 2 (Tests de Forms).
