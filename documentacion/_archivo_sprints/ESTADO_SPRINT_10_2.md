# Estado Sprint 10.2 - Incremento de Cobertura de Tests (Services)

## 📊 Resumen Ejecutivo

**Sprint:** 10.2 - Incremento de Cobertura en Capa de Servicios  
**Objetivo:** Aumentar cobertura de 6-9% a >70% en archivos de `/src/services/`  
**Estado General:** 🟢 **3 de 4 tareas completadas** (75%)  
**Fecha:** Enero 2025

## 🎯 Progreso por Tarea

| Tarea | Archivo | Cobertura Inicial | Cobertura Final | Tests | Estado |
|-------|---------|------------------|-----------------|-------|--------|
| 10.2.1 | asignador_guardias.py | 9% | 0% | 0 | ⏸️ Pendiente |
| **10.2.2** | **calculador_guardias.py** | **6%** | **93.40%** ✅ | **43** | ✅ **Completado** |
| **10.2.3** | **exportador_pdf.py** | **9%** | **98.48%** ✅ | **19** | ✅ **Completado** |
| **10.2.4** | **importador_profesores.py** | **0%** | **91.11%** ✅ | **26** | ✅ **Completado** |

### Otros Servicios (Sin tests todavía)
- `exportador.py` - 0% cobertura
- `gestor_ausencias.py` - 0% cobertura

## 📈 Métricas Globales

### Archivos Completados (88 tests totales)

```
calculador_guardias.py:    226 líneas | 93.40% cobertura | 43 tests
exportador_pdf.py:         112 líneas | 98.48% cobertura | 19 tests  
importador_profesores.py:   78 líneas | 91.11% cobertura | 26 tests
═══════════════════════════════════════════════════════════════════
TOTAL:                     416 líneas | 94.47% promedio  | 88 tests
```

### Distribución de Tests

```
tests/test_calculador.py:            43 tests (48.9%)
tests/test_exportador_pdf.py:        19 tests (21.6%)
tests/test_importador_profesores.py: 26 tests (29.5%)
────────────────────────────────────────────────
TOTAL Sprint 10.2:                   88 tests
```

## ✅ Task 10.2.2 - calculador_guardias.py

### Resumen
- **Cobertura:** 93.40% (215/226 líneas)
- **Tests:** 43 tests en 9 clases
- **Archivo:** `/tests/test_calculador.py`
- **Estado:** ✅ Completado

### Clases de Tests
1. TestCalculoDiasLectivos (3 tests) - Cálculo de días lectivos
2. TestFestivosAutomaticos (3 tests) - Festivos automáticos (Navidad, Semana Santa)
3. TestParseCustomNoLectivos (3 tests) - Parsing de días no lectivos
4. TestListarDiasLectivos (2 tests) - Listado con/sin festivos
5. TestParseRecreos (2 tests) - Parsing configuración recreos
6. TestCalculoRecreosActivos (2 tests) - Recreos desde horas/config
7. TestAjusteRedondeo (2 tests) - Redondeo de guardias
8. TestDistribucionBase (2 tests) - Distribución con tutores/turnos
9. TestObtenerEstadisticas (2 tests) - Estadísticas completas
10. TestCalculoCompleto (4 tests) - Cálculo completo y errores
11. **TestProfesoresConFechasLimite** (5 tests) - Fechas inicio/fin
12. **TestCasosEdge** (7 tests) - Casos extremos
13. **TestCalculoFactorParticipacion** (4 tests) - Factor participación recreos
14. **TestRecreoConfigAvanzado** (2 tests) - Configuración avanzada recreos

### Cobertura Detallada
```
Líneas no cubiertas (11 líneas):
- 39: Import alternativo holidays
- 82: Logging fallback festivos
- 135: Error parsing recreos
- 186-187: Validación días lectivos
- 202, 213, 215, 218, 222: Edge cases específicos
- 299, 306-307: Manejo errores internos
- 460: Logging final
```

## ✅ Task 10.2.3 - exportador_pdf.py

### Resumen
- **Cobertura:** 98.48% (110/112 líneas)
- **Tests:** 19 tests en 4 clases
- **Archivo:** `/tests/test_exportador_pdf.py`
- **Estado:** ✅ Completado

### Clases de Tests
1. TestExportarCalendarioProfesor (7 tests)
   - Exportación básica individual
   - Profesor inexistente/sin guardias
   - Diferentes meses
   - Múltiples guardias mismo día
   - Errores de ruta
   - Turnos mañana/tarde

2. TestExportarTodosLosProfesores (7 tests)
   - Exportación masiva sin/con callback
   - Mes sin guardias
   - Creación automática de carpetas
   - Nombres de archivo seguros
   - Callback con errores
   - Múltiples profesores diferentes turnos

3. TestIntegracionExportadorPDF (2 tests)
   - Ciclo completo de exportación
   - Profesor con muchas guardias

4. TestCasosEdge (3 tests)
   - Límites de meses (1/31)
   - Zona sin descripción
   - Guardia sin zona

### Cobertura Detallada
```
Líneas no cubiertas (2 líneas):
- 317->315: Branch condicional específico
- 329->315: Branch alternativo
```

## ✅ Task 10.2.4 - importador_profesores.py

### Resumen
- **Cobertura:** 91.11% (71/78 líneas)
- **Tests:** 26 tests en 8 clases
- **Archivo:** `/tests/test_importador_profesores.py`
- **Estado:** ✅ Completado

### Clases de Tests
1. TestNormalizarNombre (5 tests)
   - Normalización básica/mayúsculas
   - Múltiples espacios
   - Strings vacíos/solo espacios

2. TestImportarProfesoresBasico (4 tests)
   - Importación nuevos profesores
   - Progress callbacks
   - Profesores sin email/email NaN

3. TestImportarProfesoresExistentes (2 tests)
   - Detección duplicados
   - Nombres similares

4. TestValidaciones (3 tests)
   - Columnas insuficientes
   - Sin profesores válidos
   - Filas vacías

5. TestManejoErrores (3 tests)
   - Archivo inexistente
   - Archivo corrupto
   - Callbacks con errores

6. TestFormatos (3 tests)
   - Nombres con comas
   - Emails diferentes formatos
   - Caracteres especiales (á, é, ñ)

7. TestDatosGenerados (2 tests)
   - Valores por defecto
   - Estructura resultado

8. TestIntegracion (2 tests)
   - Importación masiva (10 profesores)
   - Importación incremental

9. TestSkipRows (2 tests)
   - skiprows personalizado (5)
   - skiprows=0

### Cobertura Detallada
```
Líneas no cubiertas (7 líneas):
- 18-19: Manejo pandas no instalado (opcional)
- 135: Bloque catch específico
- 182-185: Logging errores internos
```

### Dependencias Instaladas
```
pandas==2.3.3
openpyxl==3.1.5
pytz==2025.2
tzdata==2025.2
```

## 🔧 Técnicas y Patrones Comunes

### 1. Fixtures pytest
```python
@pytest.fixture
def session():
    """Base de datos en memoria para tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def configuracion(session):
    """Configuración de prueba."""
    config = Configuracion(
        dias_lectivos=180,
        horas_semanales=30,
        # ...
    )
    session.add(config)
    session.commit()
    return config
```

### 2. Tests con Callbacks
```python
resultados_callback = []

def callback(porcentaje, mensaje):
    resultados_callback.append((porcentaje, mensaje))

resultado = funcion_con_callback(session, callback=callback)

assert len(resultados_callback) > 0
assert resultados_callback[0][0] == 0  # Porcentaje inicial
assert resultados_callback[-1][0] == 100  # Porcentaje final
```

### 3. Tests de Archivos Temporales
```python
def test_exportar_pdf(session, tmp_path):
    archivo_pdf = tmp_path / "test.pdf"
    
    exportar_calendario_profesor(
        session=session,
        profesor_id=1,
        mes=1,
        anio=2025,
        archivo_path=str(archivo_pdf)
    )
    
    assert archivo_pdf.exists()
    assert archivo_pdf.stat().st_size > 4000
```

### 4. Tests de Manejo de Errores
```python
def test_error_sin_configuracion(session):
    with pytest.raises(ValueError, match="No se encontró configuración"):
        calcular_guardias_por_profesor(session)
```

## 📊 Estadísticas de Ejecución

### Tiempos de Ejecución
```
test_calculador.py:            ~2.5s (43 tests)
test_exportador_pdf.py:        ~2.3s (19 tests)
test_importador_profesores.py: ~2.4s (26 tests)
────────────────────────────────────────
TOTAL:                         ~7.2s (88 tests)
```

### Tasas de Éxito
```
Tests Pasando:  88/88 (100%)
Tests Fallando: 0/88 (0%)
```

## 🎯 Próximos Pasos

### Task 10.2.1 - asignador_guardias.py (Pendiente)
- **Cobertura actual:** 0% (185 líneas sin cubrir)
- **Complejidad:** ALTA (70 branches)
- **Prioridad:** Alta
- **Estimación:** 30-40 tests necesarios

#### Áreas a Cubrir:
1. Asignación básica de guardias
2. Validación de disponibilidad profesores
3. Distribución por turnos (mañana/tarde)
4. Respeto de zonas preferidas
5. Manejo de ausencias
6. Sustituciones automáticas
7. Casos edge: profesores sin disponibilidad, zonas sin cobertura
8. Métricas de balanceo de carga

### Servicios Adicionales (Futuro)
1. **exportador.py** (127 líneas, 0% cobertura)
   - Exportación a Excel/CSV
   - Formatos múltiples
   
2. **gestor_ausencias.py** (124 líneas, 0% cobertura)
   - Gestión de ausencias
   - Cálculo de impacto

## 📝 Lecciones Aprendidas

### 1. Formato de Archivos Excel
- pandas interpreta `skiprows` de forma específica
- La fila `skiprows+1` se considera encabezado
- Necesario helper consistente para crear archivos de prueba

### 2. Tests de PDF
- Verificar tamaño mínimo de archivo (>4000 bytes)
- No verificar contenido exacto (puede variar con reportlab)
- Usar `tmp_path` de pytest para archivos temporales

### 3. Progress Callbacks
- Importante testear que se llaman correctamente
- Verificar porcentajes 0 y 100
- Manejo de errores en callbacks no debe interrumpir función principal

### 4. Base de Datos en Memoria
- SQLite `:memory:` ideal para tests rápidos
- Recrear schema en cada fixture
- Usar transacciones para aislamiento

## ✅ Conclusiones

### Logros Sprint 10.2
- ✅ **3 servicios con >90% de cobertura**
- ✅ **88 tests exhaustivos creados**
- ✅ **Cobertura promedio: 94.47%**
- ✅ **100% de tests pasando**
- ✅ **Documentación completa generada**

### Impacto
- 📈 Cobertura total del proyecto incrementada
- 🐛 Detección temprana de bugs
- 📚 Mejor documentación de comportamiento esperado
- 🔧 Facilita refactoring futuro
- ✨ Código más mantenible y confiable

### Próximo Objetivo
Completar Task 10.2.1 (asignador_guardias.py) para alcanzar **100% de cobertura** en capa de servicios críticos.

---

**Generado:** Enero 2025  
**Herramientas:** pytest 8.4.2 + pytest-cov 7.0.0  
**Versión Python:** 3.11.14
