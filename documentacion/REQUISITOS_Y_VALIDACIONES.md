# Requisitos y Validaciones del Sistema de Guardias de Patio

**Versión:** 2.0  
**Fecha:** 15 de octubre de 2025  
**Proyecto:** Gestión de Guardias de Patio

---

## 📋 Índice

1. [Requisitos Funcionales Básicos](#requisitos-funcionales-básicos)
2. [Validaciones Críticas del Algoritmo](#validaciones-críticas-del-algoritmo)
3. [Restricciones por Profesor](#restricciones-por-profesor)
4. [Configuración del Sistema](#configuración-del-sistema)
5. [Integridad de Datos](#integridad-de-datos)
6. [Prevención de Errores Operativos](#prevención-de-errores-operativos)

---

## 1. Requisitos Funcionales Básicos

### 1.1 Gestión de Profesores

- ✅ **Campo unificado de nombre**: Los profesores deben tener un único campo `nombre_completo` en formato **"APELLIDOS, NOMBRE"**
  - Migración: `5fc6681ada26_unificar_nombre_apellidos_en_nombre_completo`
  - Archivo: `src/models/models.py` - clase `Profesor`
  
- ✅ **CRUD completo**: Crear, Leer, Actualizar y Eliminar profesores
  - Archivo: `src/main.py` - clase `ProfesorForm`
  - Métodos: `guardar_profesor()`, `editar_profesor()`, `eliminar_profesor()`

- ✅ **Interfaz profesional**: UI moderna con QGroupBox, CSS styling y tabla visual
  - Archivo: `src/main.py` - líneas 174-410

### 1.2 Gestión de Guardias

- ✅ **Generación automática**: Algoritmo que distribuye guardias según configuración
  - Archivo: `src/services/asignador_guardias.py`
  
- ✅ **Distribución equilibrada**: Reparto proporcional según disponibilidad de profesores
  - Archivo: `src/services/calculador_guardias.py` - función `calcular_guardias_por_profesor()`

---

## 2. Validaciones Críticas del Algoritmo

### 2.1 ⚠️ **VALIDACIÓN CRÍTICA 1: No Duplicidad de Ubicaciones**

**Requisito**: Un profesor **NO puede estar en dos zonas diferentes al mismo tiempo**.

**Definición "mismo tiempo":**
- Mismo **día** (fecha)
- Mismo **turno** (mañana o tarde)
- Mismo **recreo** (1º, 2º, etc.)

**Implementación:**
```python
# Archivo: src/services/asignador_guardias.py
# Líneas: ~127-129

guardias_por_slot_prof: Dict[Tuple[int, date, str, int], bool] = {}

# En el loop de asignación:
if (p.id, slot.fecha, slot.turno, slot.recreo_id) in guardias_por_slot_prof:
    continue  # Excluir de elegibles
```

**Ejemplo de violación:**
```
❌ INCORRECTO:
- Profesor: "GARCÍA LÓPEZ, JUAN"
- Fecha: 2024-09-15
- Turno: mañana
- Recreo 1:
  * Guardia en Zona A (Patio Principal)  ← IMPOSIBLE FÍSICAMENTE
  * Guardia en Zona B (Porche)           ← IMPOSIBLE FÍSICAMENTE
```

**Test de validación:**
- Archivo: `tests/test_no_duplicados_profesor_mismo_slot.py`

---

### 2.2 ⚠️ **VALIDACIÓN CRÍTICA 2: Máximo 1 Guardia por Día**

**Requisito**: Un profesor **sólo puede hacer como máximo 1 guardia al día**, sumando turnos de mañana y tarde.

**Justificación**: 
- Distribución equitativa de la carga
- Evitar sobrecarga de trabajo diario
- Permitir planificación personal del profesorado

**Implementación:**
```python
# Archivo: src/services/asignador_guardias.py
# Líneas: ~106, 130-133, 174

guardias_por_dia_prof: Dict[Tuple[int, date], bool] = {}

# En el loop de asignación:
if (p.id, slot.fecha) in guardias_por_dia_prof:
    continue  # Excluir de elegibles

# Al asignar:
guardias_por_dia_prof[(elegido.id, slot.fecha)] = True
```

**Ejemplos:**

✅ **CORRECTO:**
```
Profesor: "MARTÍNEZ SANZ, ANA"
- 2024-09-15 - MAÑANA - Recreo 1 - Zona A  ✓
- 2024-09-16 - TARDE  - Recreo 3 - Zona B  ✓
- 2024-09-17 - MAÑANA - Recreo 2 - Zona C  ✓
```

❌ **INCORRECTO:**
```
Profesor: "MARTÍNEZ SANZ, ANA"
- 2024-09-15 - MAÑANA - Recreo 1 - Zona A  
- 2024-09-15 - TARDE  - Recreo 3 - Zona B  ← VIOLACIÓN: 2 guardias mismo día
```

**Test de validación:**
- Archivo: `tests/test_max_una_guardia_dia.py`

---

## 3. Restricciones por Profesor

### 3.1 Turno del Profesor

**Opciones:**
- `mañana`: Solo puede cubrir recreos de mañana
- `tarde`: Solo puede cubrir recreos de tarde
- `mixto`: Puede cubrir ambos turnos

**Validación:**
```python
# Archivo: src/services/asignador_guardias.py - Función _turno_de_recreo()
def _turno_de_recreo(turno_prof: str, recreo_turno: str) -> bool:
    if turno_prof == 'mixto':
        return True
    return turno_prof == recreo_turno
```

### 3.2 Fecha de Inicio de Guardias

**Requisito**: Un profesor puede tener una fecha de inicio específica para empezar a hacer guardias.

**Ejemplo:**
- Profesor de nueva incorporación: `fecha_inicio_guardias = 2024-10-01`
- No se le asignarán guardias antes de esa fecha

**Validación:**
```python
if p.fecha_inicio_guardias and slot.fecha < p.fecha_inicio_guardias:
    continue
```

### 3.3 Días de Semana Permitidos

**Requisito**: Un profesor puede restringir qué días de la semana puede hacer guardias.

**Formato**: CSV de números (0=Lunes, 1=Martes, ..., 6=Domingo)
- Ejemplo: `"0,1,2,3,4"` = Solo de Lunes a Viernes
- Ejemplo: `"0,2,4"` = Solo Lunes, Miércoles y Viernes
- Si está vacío: por defecto Lunes-Viernes

**Validación:**
```python
def _dias_semana_ok(fecha: date, dias_csv: Optional[str]) -> bool:
    if not dias_csv:
        return fecha.weekday() < 5  # L-V por defecto
    permitidos = {int(x.strip()) for x in dias_csv.split(',') if x.strip()}
    return fecha.weekday() in permitidos
```

### 3.4 Recreos Permitidos

**Requisito**: Un profesor puede restringir en qué recreos puede hacer guardias.

**Formato**: CSV de IDs de recreos
- Ejemplo: `"1,3"` = Solo puede hacer el 1er recreo de mañana y 1er recreo de tarde
- Si está vacío: puede cubrir todos los recreos

**Validación:**
```python
def _recreo_ok(recreo_id: int, recreos_csv: Optional[str]) -> bool:
    if not recreos_csv:
        return True
    permitidos = {int(x.strip()) for x in recreos_csv.split(',') if x.strip()}
    return recreo_id in permitidos
```

---

## 4. Configuración del Sistema

### 4.1 Configuración del Curso

**Campos obligatorios:**
- `curso_escolar`: "2024-2025"
- `fecha_inicio`: Fecha de inicio del periodo lectivo
- `fecha_fin`: Fecha de fin del periodo lectivo
- `recreos_json`: Configuración de recreos en formato JSON

**Ejemplo recreos_json:**
```json
[
  {"id": 1, "turno": "mañana", "zonas": 3},
  {"id": 2, "turno": "mañana", "zonas": 3},
  {"id": 3, "turno": "tarde", "zonas": 2},
  {"id": 4, "turno": "tarde", "zonas": 2}
]
```

### 4.2 Días Lectivos

**Cálculo automático:**
- Se excluyen sábados y domingos (por defecto)
- Se excluyen festivos configurados
- Se excluyen periodos vacacionales

**Archivo:** `src/services/calculador_guardias.py` - función `listar_dias_lectivos()`

---

## 5. Integridad de Datos

### 5.1 Migración de Esquema

✅ **Migración aplicada:** `5fc6681ada26_unificar_nombre_apellidos_en_nombre_completo`

**Cambios:**
- Eliminados campos: `nombre`, `apellidos`
- Añadido campo: `nombre_completo` (tipo String, no nullable)
- Migración de datos: concatenación automática "APELLIDOS, NOMBRE"

**Archivo:** `alembic/versions/5fc6681ada26_unificar_nombre_apellidos_en_nombre_completo.py`

### 5.2 Compatibilidad de Exportación

✅ **Retrocompatibilidad**: El exportador mantiene el formato antiguo para compatibilidad.

**Archivo:** `src/services/exportador.py` - método `exportar_profesores()`

```python
# Se exporta nombre_completo pero también se descompone en nombre/apellidos
# para mantener compatibilidad con sistemas antiguos
```

---

## 6. Prevención de Errores Operativos

### 6.1 ⚠️ Prevención de Duplicados por Ejecución Múltiple

**Problema**: Si el usuario ejecuta "Generar Guardias" varias veces, se acumulan guardias duplicadas.

**Solución implementada**: Diálogo de confirmación automático

**Ubicación:** `src/main.py` - método `generar_guardias()` líneas ~1133-1166

**Funcionamiento:**
1. Al hacer clic en "Generar Guardias", se verifica si ya existen guardias
2. Si existen, se muestra un diálogo:
   ```
   Ya existen N guardias en la base de datos.
   
   ¿Deseas eliminarlas antes de generar el calendario nuevo?
   
   SÍ: Eliminar y regenerar
   NO: Mantener y añadir más
   CANCELAR: Abortar operación
   ```
3. El usuario decide conscientemente qué hacer

**Test de validación:**
- Verificado manualmente en ejecución de aplicación
- Documentación: `documentacion/SOLUCION_DUPLICADOS_GUARDIAS.md`

### 6.2 Validación de Datos Obligatorios

**Antes de generar guardias:**
- ✅ Debe existir configuración del curso
- ✅ Debe haber al menos 1 profesor registrado
- ✅ Debe haber al menos 1 zona registrada

**Archivo:** `src/services/asignador_guardias.py` - función `generar_calendario_guardias()`

```python
if not config:
    raise ValueError("No existe configuración del curso")
if not profesores:
    raise ValueError("No hay profesores registrados")
if not zonas:
    raise ValueError("No hay zonas registradas")
```

---

## 📊 Resumen de Tests

### Suite de Pruebas

| Test | Archivo | Estado | Descripción |
|------|---------|--------|-------------|
| ✅ test_no_duplicados_profesor_mismo_slot | test_no_duplicados_profesor_mismo_slot.py | PASSING | Valida que no haya duplicidad en mismo slot |
| ✅ test_max_una_guardia_por_dia | test_max_una_guardia_dia.py | NUEVO | Valida máximo 1 guardia/día por profesor |
| ✅ test_distribucion_equilibrada_con_limite_diario | test_max_una_guardia_dia.py | NUEVO | Valida distribución equilibrada con límite |
| ✅ 52 tests totales | tests/* | PASSING | Suite completa de pruebas unitarias |

**Comando para ejecutar:**
```bash
pytest tests/ -v --tb=line
```

---

## 🎯 Algoritmo de Asignación - Flujo Completo

### Pasos del Algoritmo

1. **Construcción de Slots**: 
   - Generar todos los slots (día, turno, recreo, zona)
   - Archivo: `_build_slots()`

2. **Cálculo de Cuotas**: 
   - Calcular guardias proporcionales por profesor
   - Archivo: `calcular_guardias_por_profesor()`

3. **Iteración por Slot**: Para cada slot:
   
   a. **Filtrado de Elegibles** (en orden):
      - ❌ Excluir si cuota completa
      - ❌ Excluir si turno incompatible
      - ❌ Excluir si antes de fecha_inicio_guardias
      - ❌ Excluir si día de semana no permitido
      - ❌ Excluir si recreo no permitido
      - ❌ **VALIDACIÓN 1**: Excluir si ya tiene guardia en este slot (fecha+turno+recreo)
      - ❌ **VALIDACIÓN 2**: Excluir si ya tiene guardia en este día (cualquier turno)
   
   b. **Scoring y Selección**:
      - Puntuar por continuidad (día consecutivo)
      - Puntuar por misma zona
      - Puntuar por mismo recreo
      - Puntuar por déficit de guardias
      - Aleatorización para desempate
      - Seleccionar el de mayor puntuación
   
   c. **Asignación**:
      - Crear objeto Guardia
      - Incrementar contador de asignadas
      - Actualizar último_por_zona
      - Actualizar último_recreo_prof
      - Actualizar último_dia_prof
      - **Marcar slot ocupado** → `guardias_por_slot_prof`
      - **Marcar día ocupado** → `guardias_por_dia_prof`

4. **Persistencia**:
   - Guardar todas las guardias en base de datos
   - Commit de la transacción

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2025-10-14 | Requisito inicial: unificación de nombre/apellidos |
| 1.1 | 2025-10-14 | Mejora CRUD completo de profesores |
| 1.2 | 2025-10-15 | Mejora UI y estética profesional |
| 1.3 | 2025-10-15 | Fix: Duplicados en mismo slot (Validación 1) |
| **2.0** | **2025-10-15** | **Nuevo: Máximo 1 guardia por día (Validación 2)** |

---

## 🔍 Referencias Técnicas

### Archivos Clave

- **Modelos**: `src/models/models.py`
- **Algoritmo**: `src/services/asignador_guardias.py`
- **Calculador**: `src/services/calculador_guardias.py`
- **Interfaz**: `src/main.py`
- **Tests**: `tests/test_*.py`

### Documentación Relacionada

- `documentacion/SOLUCION_DUPLICADOS_GUARDIAS.md` - Solución a problema de duplicados
- `alembic/versions/5fc6681ada26_*.py` - Migración de base de datos

---

**Fin del documento**
