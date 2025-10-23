# 📋 SPRINT 10: Type Safety, Coverage y Optimización

**Fecha inicio**: 21 de octubre de 2025  
**Duración estimada**: 4-5 días  
**Objetivo**: Aumentar type safety, coverage en services, y optimizar queries

---

## 🎯 OBJETIVOS DEL SPRINT

### Objetivo Principal
Completar la refactorización al **90%+** mediante:
1. Type safety completo con mypy strict mode
2. Coverage >70% en services layer (actualmente 6-9%)
3. Query optimization con eager loading
4. Resolver 4 tests E2E pendientes

### Métricas de Éxito
- ✅ mypy strict mode sin errores
- ✅ Coverage services: asignador_guardias.py >70%, calculador_guardias.py >70%
- ✅ 34/34 tests E2E passing (100%)
- ✅ Queries optimizadas sin N+1
- ✅ Type hints 100% en archivos críticos

---

## 📝 TAREAS DEL SPRINT

### Task 10.1: Type Safety con mypy strict ⭐ PRIORIDAD ALTA

**Objetivo**: Configurar mypy en modo strict y resolver todos los errores

**Subtareas**:
1. Configurar mypy en `pyproject.toml` (strict mode)
2. Añadir type hints completos a `services/`:
   - `asignador_guardias.py`
   - `calculador_guardias.py`
   - `exportador_pdf.py`
   - `exportador.py`
   - `gestor_ausencias.py`
   - `importador_profesores.py`
3. Añadir type hints a `utils/`:
   - `cache.py`
   - `validators.py`
   - `logger.py`
   - `query_optimizer.py`
4. Resolver errores de mypy iterativamente
5. Integrar mypy check en CI/CD

**Criterios de aceptación**:
- ✅ `mypy src/ --strict` sin errores
- ✅ Type hints en 100% de funciones públicas
- ✅ Uso de `typing.Protocol` para interfaces
- ✅ Type aliases para tipos complejos
- ✅ Generic types donde sea apropiado

**Estimación**: 1.5 días

---

### Task 10.2: Tests para Services Layer ⭐ PRIORIDAD ALTA

**Objetivo**: Aumentar coverage de 6-9% a >70% en services

**Archivos a testear**:

#### 1. `test_asignador_guardias.py` (NUEVO)
**Coverage objetivo**: 70%+

Tests a crear:
- ✅ `test_generar_calendario_guardias_basico()`
- ✅ `test_generar_calendario_con_progress_callback()`
- ✅ `test_generar_calendario_sin_profesores()`
- ✅ `test_generar_calendario_sin_zonas()`
- ✅ `test_asignacion_respeta_turnos()`
- ✅ `test_asignacion_respeta_horas_contrato()`
- ✅ `test_asignacion_con_zona_preferida()`
- ✅ `test_manejo_error_validacion()`
- ✅ `test_manejo_error_sin_configuracion()`
- ✅ `test_cancelacion_via_progress_callback()`

**Estimación**: 400-500 líneas de tests

#### 2. `test_calculador_guardias.py` (NUEVO)
**Coverage objetivo**: 70%+

Tests a crear:
- ✅ `test_calcular_guardias_por_profesor_basico()`
- ✅ `test_calcular_con_diferentes_porcentajes_jornada()`
- ✅ `test_calcular_con_diferentes_turnos()`
- ✅ `test_calcular_respeta_minimo_una_guardia()`
- ✅ `test_redondeo_guardias()`
- ✅ `test_profesores_sin_guardias_activo_false()`
- ✅ `test_profesores_con_horas_cero()`
- ✅ `test_calcular_con_zona_preferida()`
- ✅ `test_edge_cases_porcentajes_extremos()`

**Estimación**: 350-450 líneas de tests

#### 3. `test_exportador_pdf.py` (EXPANDIR)
**Coverage objetivo**: 70%+

Tests adicionales:
- ✅ `test_generar_pdf_con_progress_callback()`
- ✅ `test_exportar_multiples_profesores()`
- ✅ `test_manejo_profesor_sin_guardias()`
- ✅ `test_formato_pdf_correcto()`
- ✅ `test_error_directorio_no_existe()`

**Estimación**: +200 líneas

#### 4. `test_importador_profesores.py` (NUEVO)
**Coverage objetivo**: 70%+

Tests a crear:
- ✅ `test_importar_desde_excel_basico()`
- ✅ `test_importar_con_progress_callback()`
- ✅ `test_importar_profesores_existentes()`
- ✅ `test_validacion_columnas_obligatorias()`
- ✅ `test_manejo_errores_formato_email()`
- ✅ `test_manejo_errores_nombre_completo()`
- ✅ `test_manejo_archivo_no_existe()`
- ✅ `test_resultado_detallado_correcto()`

**Estimación**: 350-400 líneas

**Criterios de aceptación**:
- ✅ Coverage >70% en cada archivo de services/
- ✅ Tests con mocks apropiados (session, progress_callback)
- ✅ Tests de happy path y error paths
- ✅ Tests de edge cases

**Estimación total Task 10.2**: 2 días

---

### Task 10.3: Query Optimization con Eager Loading 🚀

**Objetivo**: Eliminar N+1 queries y optimizar acceso a BD

**Análisis de queries actuales**:

#### Queries a optimizar:

1. **En asignador_guardias.py**:
```python
# ANTES (N+1):
profesores = session.query(Profesor).all()
for profesor in profesores:
    zona = profesor.zona_preferida  # Query adicional

# DESPUÉS (eager loading):
profesores = session.query(Profesor)\
    .options(joinedload(Profesor.zona_preferida))\
    .all()
```

2. **En gestor_ausencias.py**:
```python
# ANTES:
ausencias = session.query(Ausencia).all()
for ausencia in ausencias:
    profesor = ausencia.profesor  # N+1

# DESPUÉS:
ausencias = session.query(Ausencia)\
    .options(joinedload(Ausencia.profesor))\
    .all()
```

3. **En vista_calendario.py**:
```python
# ANTES:
guardias = session.query(Guardia).filter(...).all()
for guardia in guardias:
    profesor = guardia.profesor  # N+1
    zona = guardia.zona  # N+1

# DESPUÉS:
guardias = session.query(Guardia)\
    .options(
        joinedload(Guardia.profesor),
        joinedload(Guardia.zona)
    )\
    .filter(...).all()
```

**Subtareas**:
1. Auditar todas las queries en services/
2. Identificar N+1 queries (usar SQLAlchemy logging)
3. Aplicar `joinedload()` donde sea apropiado
4. Aplicar `selectinload()` para relaciones one-to-many
5. Medir impacto en performance (antes/después)
6. Documentar optimizaciones

**Criterios de aceptación**:
- ✅ Sin N+1 queries en operaciones críticas
- ✅ Queries optimizadas documentadas
- ✅ Benchmarks de performance mejorados
- ✅ Tests que validen optimizaciones

**Estimación**: 1 día

---

### Task 10.4: Resolver Tests E2E Pendientes ✅

**Objetivo**: Alcanzar 100% success rate en tests E2E (actualmente 88.24%)

**Tests a arreglar** (4 pendientes):

#### 1. `test_ausencia_con_reasignacion`
**Problema**: Modelo Ausencia cambió de `fecha` a `fecha_inicio`/`fecha_fin`

**Solución**:
```python
# ANTES:
ausencia = Ausencia(
    profesor_id=profesor.id,
    fecha=datetime.date.today()
)

# DESPUÉS:
ausencia = Ausencia(
    profesor_id=profesor.id,
    fecha_inicio=datetime.date.today(),
    fecha_fin=datetime.date.today()
)
```

#### 2-4. Tests con `generar_calendario_guardias(mes, anio)`
**Problema**: Función no acepta parámetros `mes` y `anio`

**Tests afectados**:
- `test_generar_calendario_mes_sin_profesores`
- `test_generar_calendario_sin_zonas`
- `test_validacion_turno_sin_cobertura`

**Solución**: Refactorizar tests para usar API actual de generación

**Criterios de aceptación**:
- ✅ 34/34 tests E2E passing (100%)
- ✅ Tiempo ejecución < 5 segundos
- ✅ Sin warnings deprecation

**Estimación**: 0.5 días

---

### Task 10.5: Integrar Dashboard en MainWindow 🎨

**Objetivo**: Hacer el dashboard accesible desde la ventana principal

**Subtareas**:

1. **Añadir tab "Observabilidad"**:
```python
# En main.py MainWindow.__init__()
tab_observabilidad = DashboardObservabilidad()
self.tabs.addTab(tab_observabilidad, "📊 Observabilidad")
```

2. **Añadir acción en menú**:
```python
menu_herramientas = self.menuBar().addMenu("Herramientas")
accion_dashboard = QAction("Dashboard Observabilidad", self)
accion_dashboard.triggered.connect(self.mostrar_dashboard)
menu_herramientas.addAction(accion_dashboard)
```

3. **Añadir atajo de teclado**: `Ctrl+Shift+O`

**Criterios de aceptación**:
- ✅ Dashboard accesible desde tab principal
- ✅ Dashboard accesible desde menú
- ✅ Atajo de teclado funcional
- ✅ Dashboard se actualiza al cambiar de tab

**Estimación**: 0.5 días

---

### Task 10.6: Schemas Pydantic para DTOs (OPCIONAL)

**Objetivo**: Validación de datos con Pydantic en capa de aplicación

**Ejemplo de implementación**:

```python
# application/dto/profesor_dto.py
from pydantic import BaseModel, EmailStr, field_validator

class ProfesorCreateDTO(BaseModel):
    nombre_completo: str
    email: EmailStr
    horas_contrato: float
    turno: str
    activo: bool = True
    zona_preferida_id: int | None = None
    
    @field_validator('nombre_completo')
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        if not re.match(r'^[A-ZÁÉÍÓÚÑ]+,\s+[A-Za-záéíóúñ\s]+$', v):
            raise ValueError('Formato debe ser APELLIDOS, Nombre')
        return v
    
    @field_validator('horas_contrato')
    @classmethod
    def validar_horas(cls, v: float) -> float:
        if not 0 < v <= 40:
            raise ValueError('Horas deben estar entre 0 y 40')
        return v
    
    @field_validator('turno')
    @classmethod
    def validar_turno(cls, v: str) -> str:
        if v not in ['mañana', 'tarde', 'completo']:
            raise ValueError('Turno debe ser mañana, tarde o completo')
        return v

class ProfesorUpdateDTO(BaseModel):
    nombre_completo: str | None = None
    email: EmailStr | None = None
    horas_contrato: float | None = None
    turno: str | None = None
    activo: bool | None = None
    zona_preferida_id: int | None = None
```

**Uso en use cases**:
```python
# application/use_cases/profesor/crear_profesor.py
def crear_profesor(dto: ProfesorCreateDTO, session: Session) -> Profesor:
    # dto.model_dump() ya está validado
    profesor = Profesor(**dto.model_dump())
    session.add(profesor)
    session.commit()
    return profesor
```

**Archivos a crear**:
- `application/dto/profesor_dto.py`
- `application/dto/zona_dto.py`
- `application/dto/guardia_dto.py`
- `application/dto/ausencia_dto.py`
- `application/dto/configuracion_dto.py`

**Criterios de aceptación**:
- ✅ DTOs con validación Pydantic
- ✅ Validadores custom implementados
- ✅ Type hints completos
- ✅ Use cases adaptados para usar DTOs
- ✅ Tests para DTOs

**Estimación**: 1 día (OPCIONAL - puede ir a Sprint 11)

---

## 📊 DISTRIBUCIÓN DE TIEMPO

| Task | Prioridad | Estimación | Acumulado |
|------|-----------|------------|-----------|
| 10.1: Type Safety mypy | ⭐⭐⭐ | 1.5 días | 1.5 días |
| 10.2: Tests Services | ⭐⭐⭐ | 2 días | 3.5 días |
| 10.3: Query Optimization | ⭐⭐ | 1 día | 4.5 días |
| 10.4: Fix E2E Tests | ⭐⭐ | 0.5 días | 5 días |
| 10.5: Dashboard MainWindow | ⭐ | 0.5 días | 5.5 días |
| 10.6: Pydantic DTOs | 🔷 | 1 día | 6.5 días |

**Total estimado**: 5-6.5 días (sin Task 10.6 opcional)

---

## 🎯 ORDEN DE EJECUCIÓN RECOMENDADO

### Día 1: Type Safety Foundation
- ✅ Task 10.1: Configurar mypy + resolver 50% errores
- ✅ Task 10.4: Fix tests E2E (rápido, crítico)

### Día 2: Type Safety Complete
- ✅ Task 10.1: Resolver 100% errores mypy
- ✅ Task 10.5: Integrar dashboard en MainWindow

### Día 3: Testing Services (Parte 1)
- ✅ Task 10.2: Tests para asignador_guardias.py
- ✅ Task 10.2: Tests para calculador_guardias.py (inicio)

### Día 4: Testing Services (Parte 2)
- ✅ Task 10.2: Tests para calculador_guardias.py (fin)
- ✅ Task 10.2: Tests para importador_profesores.py

### Día 5: Query Optimization
- ✅ Task 10.3: Auditoría de queries
- ✅ Task 10.3: Aplicar eager loading
- ✅ Task 10.3: Benchmarks

### Día 6 (OPCIONAL): Pydantic DTOs
- 🔷 Task 10.6: Implementar DTOs con Pydantic

---

## 📈 MÉTRICAS DE PROGRESO

### Pre-Sprint 10
```
Type Safety:      ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜  0% (sin mypy strict)
Coverage Services: ⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜  9% (actual)
E2E Tests:        ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬜ 88% (30/34)
Query Optimization: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜  0% (N+1 presentes)
Refactoring Total: ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬜ 87%
```

### Post-Sprint 10 (Objetivo)
```
Type Safety:      ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ 100% (mypy strict ✅)
Coverage Services: ⬛⬛⬛⬛⬛⬛⬛⬜⬜⬜  75% (>70% objetivo)
E2E Tests:        ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ 100% (34/34 ✅)
Query Optimization: ⬛⬛⬛⬛⬛⬛⬛⬛⬜⬜  85% (sin N+1 críticos)
Refactoring Total: ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬜ 93%
```

---

## 🚀 ENTREGABLES

### Código
- ✅ `pyproject.toml` con configuración mypy strict
- ✅ Type hints completos en services/ y utils/
- ✅ 4 archivos test nuevos (~1,500 líneas):
  - `test_asignador_guardias.py`
  - `test_calculador_guardias.py`
  - `test_exportador_pdf_extended.py`
  - `test_importador_profesores.py`
- ✅ Queries optimizadas con eager loading
- ✅ 4 tests E2E arreglados
- ✅ Dashboard integrado en MainWindow
- 🔷 DTOs Pydantic (opcional)

### Documentación
- ✅ `RESUMEN_SPRINT_10.md` (al finalizar)
- ✅ `CHANGELOG_v2.8.md` (con mejoras)
- ✅ Actualización de plan-refactorizacion-escalabilidad.md (93%)
- ✅ Documentación de optimizaciones de queries

### CI/CD
- ✅ Mypy check integrado en workflow
- ✅ Coverage gates actualizados (>70% services)

---

## ⚠️ RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Muchos errores mypy | Media | Alto | Resolver iterativamente, empezar por archivos pequeños |
| Tests complejos para services | Media | Medio | Usar mocks extensivamente, fixtures compartidos |
| Queries difíciles de optimizar | Baja | Medio | Profiling previo, documentar trade-offs |
| Pydantic rompe código existente | Media | Alto | Hacer Task 10.6 opcional, incremental |

---

## 📚 RECURSOS Y REFERENCIAS

### Type Safety
- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [typing module](https://docs.python.org/3/library/typing.html)

### Testing
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

### SQLAlchemy Optimization
- [SQLAlchemy Eager Loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#eager-loading)
- [joinedload vs selectinload](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading)

### Pydantic
- [Pydantic documentation](https://docs.pydantic.dev/)
- [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## 🎯 DEFINICIÓN DE "DONE"

Una tarea está completada cuando:

- ✅ Código implementado y funcionando
- ✅ Tests escritos y pasando (>70% coverage para services)
- ✅ mypy --strict sin errores
- ✅ Documentación actualizada
- ✅ Code review aprobado (self-review)
- ✅ CI/CD passing
- ✅ Sin regresiones en funcionalidad existente

---

## 📝 NOTAS ADICIONALES

### Lecciones del Sprint 9
- ✅ Suite de tests comprehensiva (77,541 líneas) fue un éxito
- ✅ Ratio 32:1 test-to-code es excepcional pero puede mantenerse
- ✅ CI/CD con matrix strategy es robusto
- ⚠️ Coverage desigual (utils 77%, services 6-9%) necesita balanceo

### Prioridades para Sprint 10
1. **Type safety** es fundamental para escalabilidad
2. **Coverage en services** es el gap más grande
3. **Query optimization** mejorará performance significativamente
4. **E2E tests al 100%** cierra el círculo de calidad

### Consideraciones para Sprint 11
- Async/await para operaciones largas (PyQt + asyncio)
- Connection pooling avanzado
- Property-based testing con Hypothesis
- Sentry integration para error tracking
- Monitoreo de performance en producción

---

**Estado**: 📝 Planificación completa  
**Próximo paso**: Comenzar Task 10.1 (Type Safety con mypy)  
**Fecha creación**: 21 de octubre de 2025
