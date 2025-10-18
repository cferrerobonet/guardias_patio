# Sprint 6: Testing - Resumen de Progreso

## 📊 Estado Actual

**Fecha**: 18 de octubre de 2025  
**Coverage Total**: **~45.8%** (objetivo: >80%)  
**Tests Totales**: 324 tests (+34)  
**Tests que Pasan**: 324 tests ✅ **¡100%!**  
**Tests que Fallan**: 0 tests ✅
**Tests xfail**: 0 tests ✅

## 🎯 Progreso Sprint 6

- **Task 1: Infraestructura de Testing** ✅ **100% COMPLETADA**
- **Task 2: Tests para Formularios** ✅ **100% COMPLETADA** 🎉
- **Task 3: Tests para Widgets**: 🔄 **50% EN PROGRESO** (2/4 widgets)
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
| asignacion_guardias_form.py | 11.11% | Media |
| configuracion_form.py | 8.30% | Media |

## 🎯 Próximos Pasos

### Task 2: Tests para Forms (100% COMPLETADA) ✅ 🎉

**Completados**:
- ✅ ZonaForm tests arreglados (12/12 tests pasan)
- ✅ ProfesorFormBasico (4/4 tests pasan)
- ✅ ConfiguracionForm (20/20 tests pasan) - Coverage: 8.30% → 90.57% (+82.27pp) 🎉
- ✅ CalendarioGuardiasForm (30/30 tests pasan) - Coverage: 7.49% → 93.58% (+86.09pp) 🚀
- ✅ ImportExportForm (27/27 tests pasan) - Coverage: 11.19% → 93.71% (+82.52pp) 🔥
- ✅ **AsignacionGuardiasForm (26/26 tests pasan) - Coverage: 11.11% → 92.36% (+81.25pp) 🌟**

**Progreso**: 6/6 formularios completados = 100% ✅
**Impacto**: +140 tests, +4.56pp cobertura global

### Task 3: Tests para Widgets

**Estado**: 🔄 **25% EN PROGRESO** (1/4 widgets completos)

#### ✅ 1. VistaCalendario - COMPLETADO (97.92% coverage)

**Archivo**: `tests/test_vista_calendario.py` (~800 líneas, 37 tests)

**Coverage**: 0.00% → **97.92%** (+97.92pp) ✨

**Clases de Tests**:

1. **TestVistaCalendarioBasico** (6 tests):
   - Creación del widget con session
   - Inicialización con fecha actual (datetime.now())
   - Existencia de botones de navegación (anterior/siguiente/hoy)
   - Existencia de label mes/año
   - Existencia de calendario layout
   - Window title

2. **TestVistaCalendarioNavegacion** (6 tests):
   - Mes siguiente dentro del año (Oct → Nov)
   - Mes siguiente con cambio de año (Dic → Ene)
   - Mes anterior dentro del año (Nov → Oct)
   - Mes anterior con cambio de año (Ene → Dic)
   - Botón "Ir a hoy" (actualiza a fecha actual)
   - Navegación múltiple meses (5 meses forward, 3 back)

3. **TestVistaCalendarioRenderizado** (5 tests):
   - Actualizar calendario sin guardias (grid vacía)
   - Encabezados días semana (L, M, X, J, V, S, D)
   - Actualizar calendario con guardias (datos visibles)
   - Label mes mostrado se actualiza
   - Limpieza calendario anterior (no data overlap)

4. **TestVistaCalendarioGuardias** (3 tests):
   - Cargar guardias del mes (5 guardias octubre)
   - Guardias de otros meses no afectan vista
   - Múltiples guardias en mismo día (stack correctamente)

5. **TestVistaCalendarioAusencias** (3 tests):
   - Cargar ausencias del mes con ícono 🏥
   - Ausencias múltiples días (span 3 días: 10-12 Oct)
   - Ausencias inactivas no aparecen (filtrado)

6. **TestVistaCalendarioEstilos** (4 tests):
   - Estilo día hoy: fondo amarillo (#fff9c4)
   - Estilo día con guardias: fondo azul (#e3f2fd)
   - Estilo día sin guardias: fondo gris (#fafafa)
   - Prioridad estilo hoy > guardias (amarillo gana)

7. **TestVistaCalendarioCeldas** (4 tests):
   - Crear celda día básica (número día visible)
   - Celda con guardias (nombre profesor + zona)
   - Celda con ausencias muestra ícono (🏥)
   - Celda limita guardias mostradas (max 3 + contador)

8. **TestVistaCalendarioIntegracion** (3 tests):
   - Flujo completo navegación con datos (crear guardias → navegar → verificar)
   - Método refrescar (actualizar vista sin navegación)
   - Crear celda con datos completos (guardias + ausencias)

9. **TestVistaCalendarioRendimiento** (3 tests, @slow):
   - Carga inicial rápida (<1s)
   - Navegación rápida (<500ms por mes)
   - Calendario con muchas guardias (<2s para 100+ guardias)

**Fixtures utilizadas**:
- `vista_calendario`: VistaCalendario(session)
- `fecha_fija`: date(2024, 10, 15) para tests determinísticos
- `guardias_mes`: 5 guardias en octubre 2024
- `ausencias_mes`: Ausencia multi-día (10-12 Oct)

**Técnicas de testing aplicadas**:
- Mocking de `datetime.now()` para tests determinísticos
- Uso de `patch` para control de fechas en navegación
- Tests de estilos con verificación CSS (#fff9c4, #e3f2fd, #fafafa)
- Tests de celdas con validación de contenido (texto, iconos)
- Tests de rendimiento con `@pytest.mark.slow`
- Fixtures compartidas para datos de prueba (guardias_mes, ausencias_mes)

**Desafíos superados**:
- Mockear `datetime.now()` en módulo correcto (`presentation.widgets.vista_calendario`)
- Transiciones de mes con cambio de año (Dic ↔ Ene)
- Validación de estilos CSS en QLabel (styleSheet())
- Límite de 3 guardias por día + contador ("...y X más")
- Ausencias multi-día que se marcan en todos los días del rango
- Prioridad de estilos (hoy > guardias > normal)

**Lecciones aprendidas**:
- VistaCalendario usa `calendar.monthcalendar()` para generar grid
- Ausencias se agrupan por `fecha_inicio` en dict para búsqueda rápida
- Estilos se aplican con `setStyleSheet()` en QLabel
- Navegación actualiza `self.mes_actual` y `self.anio_actual`, luego llama `actualizar_calendario()`
- Método `refrescar()` permite actualizar vista sin cambiar mes
- Widget carga guardias y ausencias del mes mostrado, no de todo el año

**Impacto en TASK 3**:
- ✅ **1/4 widgets completados (25%)**
- ✅ VistaCalendario: 0% → 97.92% coverage
- ✅ +37 tests
- ✅ +3.33pp coverage general (40.39% → 43.72%)

#### Widgets Pendientes:

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
Total Coverage: ~40.4% (+8.6pp desde 31.83%)
Tests Totales: 253 (+103 nuevos en Sprint 6)
Tests que Pasan: 253 (100%) ✅ ¡PERFECTO!
Tests xfail: 0 ✅
Tests que Fallan: 0 (0.00%) ✅

Archivos con 100% coverage: 35
Archivos con >80% coverage: 20 (+4)
Archivos con <25% coverage: 22 (-4)
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
