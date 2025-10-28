# Scripts del Proyecto

Este directorio contiene todos los scripts del proyecto **Guardias de Patio**.

---

## 📁 Estructura

```
scripts/
├── build/          # Scripts de compilación y distribución
├── dev/            # Scripts de desarrollo
└── *.py            # Scripts de análisis y utilidades
```

---

## 🔨 Build Scripts (`/scripts/build/`)

### `build_simple.sh`
**Propósito:** Compilación principal de la aplicación para macOS

**Uso:**
```bash
./scripts/build/build_simple.sh
```

### `create_dmg.sh`
**Propósito:** Creación del instalador DMG

**Uso:**
```bash
./scripts/build/create_dmg.sh
```

### `create_icon.sh`
**Propósito:** Generación de iconos

**Uso:**
```bash
./scripts/build/create_icon.sh
```

Ver `documentacion/build/` para documentación detallada de compilación.

---

## 💻 Development Scripts (`/scripts/dev/`)

### `run_app.sh`
**Propósito:** Ejecutar la aplicación en modo desarrollo

**Uso:**
```bash
./scripts/dev/run_app.sh
```

---

## 🛠️ Utility Scripts (Python)

### 📊 Importación y Gestión de Datos
- [`importar_profesores_desde_excel.py`](#-importar_profesores_desde_excelpy) - Importación masiva de profesores desde Excel
- [`cleanup_test_data.py`](#-cleanup_test_datapy) - Limpieza de datos de prueba

### 🔍 Análisis y Performance
- [`analyze_indices.py`](#-analyze_indicespy) - Análisis de índices de base de datos
- [`audit_n_plus_1.py`](#-audit_n_plus_1py) - Auditoría de problemas N+1
- [`audit_queries_n1.py`](#-audit_queries_n1py) - Auditoría de queries N+1
- [`benchmark_performance.py`](#-benchmark_performancepy) - Benchmarks de rendimiento
- [`profile_app.py`](#-profile_apppy) - Profiling de la aplicación
- [`profile_performance.py`](#-profile_performancepy) - Profiling de performance

### 📈 Observabilidad y Métricas
- [`demo_observability.py`](#-demo_observabilitypy) - Demo del sistema de observabilidad
- [`ver_metricas.py`](#-ver_metricaspy) - Visualización de métricas

### 🧪 Testing y Desarrollo
- [`test_branding.py`](#-test_brandingpy) - Tests del sistema de branding

### 🔧 Integración de Formularios
- [`integrar_asignacion_guardias_form.py`](#-integrar_asignacion_guardias_formpy) - Integración de formulario de asignación
- [`integrar_configuracion_form.py`](#-integrar_configuracion_formpy) - Integración de formulario de configuración
- [`integrar_zona_form.py`](#-integrar_zona_formpy) - Integración de formulario de zonas

---

## 📊 Importar Profesores desde Excel

### `importar_profesores_desde_excel.py`

### Funcionalidad
- Lee archivos `.xlsx` con datos de profesores
- Extrae: Nombre completo y Correo electrónico
- **Valida duplicados**: Si el profesor ya existe (por nombre), lo omite
- **Crea nuevos profesores** con valores por defecto:
  - `horas_contrato`: 30h
  - `porcentaje_jornada`: 100%
  - `turno`: completo
  - `email_corporativo`: del archivo Excel

### Uso

```bash
python scripts/importar_profesores_desde_excel.py
```

### Formato de archivos Excel esperado

Los archivos deben tener:
- **9 filas de encabezado** (se saltan automáticamente)
- **Fila 10**: Columnas del tipo: `Apellidos y nombre | Tel. fijo | Tel. móvil | Correo electrónico`
- **Fila 11+**: Datos de profesores

**Ejemplo de estructura:**
```
[Filas 1-9: Encabezados institucionales]
Fila 10: Apellidos y nombre | Tel. fijo | Tel. móvil | Correo electrónico
Fila 11: GARCÍA LÓPEZ, JUAN | 96123456 | 612345678 | juan.garcia@epla.es
Fila 12: MARTÍNEZ RUIZ, ANA | 96234567 | 623456789 | ana.martinez@epla.es
...
```

### Salida

El script muestra estadísticas detalladas:

```
================================================================================
🎓 IMPORTACIÓN DE PROFESORES DESDE EXCEL
================================================================================

📂 Procesando: bach.xlsx
--------------------------------------------------------------------------------
   Profesores leídos: 30
   ✅ Importados: 13
   ⏭️  Ya existentes: 17
   ❌ Errores: 0

📂 Procesando: fp_mañana.xlsx
...

================================================================================
📊 RESUMEN FINAL
================================================================================
Archivos procesados: 4
Total profesores leídos: 127
✅ Total importados: 41
⏭️  Total ya existentes: 86
❌ Total errores: 0
================================================================================
```

### Logs

El script registra operaciones en el log de la aplicación:
- ✅ Profesores importados exitosamente
- ⏭️ Profesores que ya existían (omitidos)
- ❌ Errores encontrados (con detalles)

### Notas importantes

1. **Seguridad**: El script hace commit automático solo después de procesar cada archivo completo
2. **Validación**: Omite filas vacías o con nombres inválidos
3. **Emails opcionales**: Si un profesor no tiene email, se guarda con `None`
4. **Idempotente**: Puedes ejecutar el script múltiples veces sin duplicar datos
5. **Normalización**: Los nombres se validan y comparan ignorando mayúsculas/minúsculas

### Dependencias

```bash
pip install pandas openpyxl
```

---

## � Análisis de Performance

### `analyze_indices.py`
Analiza los índices de la base de datos SQLite para optimización de queries.

### `audit_n_plus_1.py` y `audit_queries_n1.py`
Detectan problemas de N+1 queries en el código mediante análisis estático y logging.

### `benchmark_performance.py`
Ejecuta benchmarks de operaciones críticas para medir rendimiento.

### `profile_app.py` y `profile_performance.py`
Herramientas de profiling para identificar cuellos de botella en la aplicación.

**Uso típico:**
```bash
python scripts/profile_app.py
python scripts/benchmark_performance.py
```

---

## 📈 Observabilidad

### `demo_observability.py`
Demostración del sistema de observabilidad con métricas y health checks.

### `ver_metricas.py`
Visualiza métricas actuales del sistema desde la base de datos.

**Uso:**
```bash
python scripts/ver_metricas.py
```

---

## 🧹 Limpieza de Datos

### `cleanup_test_data.py`
Limpia datos de prueba de la base de datos.

**Uso:**
```bash
python scripts/cleanup_test_data.py
```

**⚠️ Precaución**: Este script elimina datos. Asegúrate de tener un backup antes de ejecutarlo.

---

## 🧪 Testing

### `test_branding.py`
Tests para verificar la correcta implementación del sistema de branding corporativo.

**Uso:**
```bash
python scripts/test_branding.py
```

---

## 🔧 Scripts de Integración

### `integrar_asignacion_guardias_form.py`
Script helper para integrar el formulario de asignación de guardias.

### `integrar_configuracion_form.py`
Script helper para integrar el formulario de configuración.

### `integrar_zona_form.py`
Script helper para integrar el formulario de gestión de zonas.

> **Nota**: Estos scripts son principalmente para desarrollo y testing de la integración de formularios.

---

## 📝 Notas Generales

### Ejecutar Scripts

Todos los scripts deben ejecutarse desde la raíz del proyecto:

```bash
# Desde la raíz del proyecto
python scripts/nombre_script.py
```

### Dependencias

La mayoría de scripts usan las mismas dependencias del proyecto principal. Algunos scripts de análisis pueden requerir:

```bash
pip install pandas openpyxl  # Para importar_profesores_desde_excel.py
```

### Logs

Los scripts registran su actividad en:
- **Consola**: Salida estándar con formato legible
- **Archivo**: `logs/application.log` (si aplica)

---

## 🚀 Scripts Futuros Planeados
- `migrar_guardias.py` - Migración de datos históricos
- `backup_database.py` - Copias de seguridad automáticas
- `generar_reportes.py` - Reportes estadísticos
- etc.
