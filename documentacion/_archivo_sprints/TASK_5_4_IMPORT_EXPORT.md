# Task 5.4: Tests de Integración Import/Export

## 📋 Resumen

**Archivo**: `tests/test_integration_import_export.py`  
**Tests**: 22/22 pasando (100%) ✅  
**Tiempo ejecución**: 1.52s  
**Coverage**:
- `services/exportador.py`: **80.84%**
- `services/exportador_pdf.py`: **95.28%**

## 🎯 Objetivo

Validar la funcionalidad completa de importación/exportación de datos y generación de PDFs:
- Exportar todos los datos del sistema a formato JSON
- Importar datos preservando relaciones e integridad
- Generar calendarios PDF individuales y por lote
- Manejar casos especiales (UTF-8, None, errores)

## 📦 Estructura de Tests

### 1. TestExportacionJSON (6 tests) ✅

#### 1.1 test_exportar_profesores
- Exporta profesores a diccionario
- Valida: nombre, email, horas, turno, porcentaje
- Verifica serialización de fechas (fecha_inicio_guardias)

#### 1.2 test_exportar_zonas
- Exporta zonas a diccionario
- Valida: nombre_zona, descripcion

#### 1.3 test_exportar_configuracion
- Exporta configuración activa
- Serializa correctamente:
  - Fechas → formato ISO (YYYY-MM-DD)
  - Horas → formato HH:MM

#### 1.4 test_exportar_guardias
- Exporta guardias con relaciones
- Verifica: profesor_id, zona_id, fecha, recreo
- Mantiene FKs correctas

#### 1.5 test_exportar_todo_archivo
- Exporta todo el sistema a archivo JSON
- Estructura:
  ```json
  {
    "version": "1.0",
    "fecha_exportacion": "2024-10-19",
    "profesores": [...],
    "zonas": [...],
    "configuracion": {...},
    "guardias": [...]
  }
  ```
- Verifica archivo creado y legible

#### 1.6 test_exportar_configuracion_sin_datos
- Maneja caso sin configuración
- Retorna diccionario vacío {}

### 2. TestImportacionJSON (5 tests) ✅

#### 2.1 test_importar_profesores
- Importa profesores desde diccionario
- Deserializa fechas correctamente
- Valida creación en BD

#### 2.2 test_importar_zonas
- Importa zonas desde diccionario
- Verifica campos opcionales (descripción)

#### 2.3 test_importar_configuracion
- Importa configuración única
- Deserializa:
  - Fechas desde ISO
  - Horas desde HH:MM

#### 2.4 test_importar_guardias
- Importa guardias con relaciones
- Verifica FK correctas a profesores/zonas

#### 2.5 test_importar_con_limpieza
- Importa con flag `limpiar=True`
- Elimina datos existentes antes de importar
- Verifica solo datos nuevos presentes
- **Fix aplicado**: `session.expunge_all()` para evitar warning SQLAlchemy

### 3. TestIntegridadImportExport (2 tests) ✅

#### 3.1 test_ciclo_completo_export_import
- Exporta datos → Limpia BD → Importa → Verifica
- Valida integridad total:
  - Mismo número de profesores
  - Mismo número de zonas
  - Mismo número de guardias
  - Configuración idéntica

#### 3.2 test_relaciones_despues_importar
- Verifica relaciones FK después de import
- Comprueba: guardia.profesor, guardia.zona
- Valida nombres correctos

### 4. TestExportacionPDF (5 tests) ✅

#### 4.1 test_exportar_pdf_individual
- Genera PDF individual para profesor
- Verifica:
  - Archivo creado
  - Tamaño > 0 bytes
  - Función retorna True

#### 4.2 test_exportar_pdf_profesor_sin_guardias
- Genera PDF para profesor sin guardias asignadas
- Verifica archivo vacío creado correctamente

#### 4.3 test_exportar_pdf_profesor_inexistente
- Maneja profesor_id inválido
- Retorna False
- No crea archivo

#### 4.4 test_exportar_todos_los_profesores_pdfs
- Genera PDFs por lote
- Un archivo por profesor
- Verifica conteo correcto de archivos

#### 4.5 test_exportar_pdfs_mes_sin_guardias
- Mes sin datos no genera archivos
- Retorna sin errores

### 5. TestCasosEspecialesExport (4 tests) ✅

#### 5.1 test_exportar_con_campos_none
- Maneja valores None en campos opcionales
- Serializa como null en JSON

#### 5.2 test_importar_json_malformado
- Detecta JSON inválido
- Lanza JSONDecodeError

#### 5.3 test_exportar_caracteres_especiales
- Preserva UTF-8: tildes, eñes, acentos
- Verifica encoding="utf-8"
- Comprueba: "García", "Martínez", "José"

#### 5.4 test_archivo_json_legibilidad
- JSON formateado con indent=2
- Legible por humanos
- Contiene saltos de línea

## 🔧 Fixtures Utilizados

```python
@pytest.fixture
def temp_dir():
    """Directorio temporal con cleanup automático."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def engine():
    """Motor SQLite en memoria."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine):
    """Sesión de BD para cada test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def datos_base(session):
    """
    Datos de prueba:
    - 1 configuración activa
    - 2 profesores
    - 2 zonas
    - 3 guardias
    """
    # Setup completo...
```

## 📊 Servicios Validados

### services/exportador.py (80.84% coverage)

**Métodos de exportación:**
- `exportar_profesores(session)` → List[Dict]
- `exportar_zonas(session)` → List[Dict]
- `exportar_configuracion(session)` → Dict
- `exportar_guardias(session)` → List[Dict]
- `exportar_todo(session, archivo)` → None

**Métodos de importación:**
- `importar_profesores(session, data, limpiar=False)` → int
- `importar_zonas(session, data, limpiar=False)` → int
- `importar_configuracion(session, data)` → None
- `importar_guardias(session, data, limpiar=False)` → int
- `importar_todo(session, archivo)` → None

**Helpers:**
- `_serializar_fecha(fecha)` → str ISO
- `_serializar_hora(tiempo)` → str HH:MM
- `_deserializar_fecha(fecha_str)` → date
- `_deserializar_hora(hora_str)` → time

### services/exportador_pdf.py (95.28% coverage)

**Métodos:**
- `exportar_calendario_profesor(session, profesor_id, mes, anio, ruta_salida)` → bool
- `exportar_todos_los_profesores(session, mes, anio, directorio_salida)` → int

**Características:**
- Formato: Landscape A4
- Librería: reportlab
- Estructura: Tabla con guardias por día
- Resumen: Estadísticas incluidas

## 🐛 Problemas Resueltos

### Warning SQLAlchemy Identity Map

**Síntoma:**
```
SAWarning: Identity map already had an identity for 
(<class 'models.models.Profesor'>, (1,), None), 
replacing it with newly flushed object.
```

**Causa:**
Test `test_importar_con_limpieza` creaba objetos, luego `limpiar=True` eliminaba y recreaba con mismo ID (autoincrement reutiliza). La sesión tenía objetos cacheados.

**Solución aplicada:**
```python
def test_importar_con_limpieza(self, session):
    # Crear datos iniciales
    prof1 = Profesor(...)
    session.add(prof1)
    session.commit()
    
    # 🔧 FIX: Limpiar caché de sesión
    session.expunge_all()
    
    # Importar con limpieza (sin warnings)
    count = ExportadorDatos.importar_profesores(
        session, data, limpiar=True
    )
```

**Resultado**: ✅ 22/22 tests pasando sin warnings

## 📈 Valor Agregado

### Funcionalidades Validadas

1. **Portabilidad de Datos** ✅
   - Exportar todo el sistema a JSON portable
   - Importar en otra instalación
   - Backup completo

2. **Integridad Referencial** ✅
   - FKs preservadas en export/import
   - Relaciones profesor↔zona↔guardia intactas

3. **Manejo de Encodings** ✅
   - UTF-8 completo (español con tildes)
   - Caracteres especiales preservados

4. **Generación Profesional PDF** ✅
   - Calendarios individuales
   - Generación por lote
   - Formato imprimible

5. **Robustez** ✅
   - Manejo de errores (JSON malformado)
   - Campos None/null
   - Profesores sin guardias

## 🎓 Aprendizajes

### 1. SQLAlchemy Session Management
- `session.expunge_all()` limpia identity map
- Evita conflictos al reutilizar IDs
- Importante en tests de ciclo completo

### 2. Serialización Temporal
- Fechas: ISO 8601 (YYYY-MM-DD)
- Horas: HH:MM
- Portabilidad entre sistemas

### 3. Testing de Archivos
- tempfile.TemporaryDirectory() para cleanup automático
- Path de pathlib para manejo cross-platform
- Verificar tamaño > 0 para PDFs

### 4. UTF-8 en JSON
- `encoding="utf-8"` en open()
- `ensure_ascii=False` en json.dump()
- Preserva caracteres españoles

## ✅ Checklist de Validación

- [x] Export JSON de profesores con todos los campos
- [x] Export JSON de zonas
- [x] Export JSON de configuración (fechas/horas serializadas)
- [x] Export JSON de guardias con relaciones
- [x] Export todo a archivo JSON legible
- [x] Import profesores desde JSON
- [x] Import zonas desde JSON
- [x] Import configuración (deserialización)
- [x] Import guardias con FKs correctas
- [x] Import con limpieza de datos previos
- [x] Ciclo completo export→import→verify
- [x] Preservación de relaciones FK
- [x] PDF individual generado correctamente
- [x] PDF para profesor sin guardias
- [x] Error handling profesor inexistente
- [x] Generación por lote de PDFs
- [x] Mes sin datos no genera archivos
- [x] Campos None manejados correctamente
- [x] JSON malformado detectado
- [x] Caracteres UTF-8 preservados
- [x] JSON formateado legible
- [x] Sin warnings SQLAlchemy
- [x] Cobertura > 80% en ambos servicios

## 🚀 Próximos Pasos

Con Task 5.4 completada (100%), el Sprint 6 está casi finalizado:

- ✅ Task 5.1: Calculador (12/12 - 100%)
- ✅ Task 5.2: Use Cases (12/12 - 100%)
- ✅ Task 5.3: Integración guardias (11/15 - 73%)
- ✅ Task 5.4: Integración import/export (22/22 - 100%)
- ⬜ Task 5.5: Documentación y reporte final

**Total tests Sprint 6**: 57/61 pasando (93.44%)

**Siguiente**: Task 5.5 - Ejecutar todos los tests juntos y generar reporte consolidado de coverage con métricas finales.
