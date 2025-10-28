# Validaciones y Reglas de Negocio del Sistema

**Versión:** 3.0  
**Fecha:** Diciembre 2025  
**Proyecto:** Guardias de Patio v2.9.0

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Validaciones Críticas (Hard Constraints)](#validaciones-críticas-hard-constraints)
3. [Validaciones de Restricciones por Profesor](#validaciones-de-restricciones-por-profesor)
4. [Validaciones de Datos del Sistema](#validaciones-de-datos-del-sistema)
5. [Preferencias y Heurísticas (Soft Constraints)](#preferencias-y-heurísticas-soft-constraints)
6. [Función de Scoring](#función-de-scoring)
7. [Requisitos del Sistema](#requisitos-del-sistema)
8. [Criterios de Verificación](#criterios-de-verificación)
9. [Casos de Uso](#casos-de-uso)
10. [Mantenimiento y Extensión](#mantenimiento-y-extensión)

---

## 1. Introducción

Este documento centraliza **todas las validaciones y reglas de negocio** del sistema de asignación de guardias de patio. Incluye reglas críticas (que NO pueden violarse), restricciones configurables por profesor, y preferencias (que se optimizan cuando es posible).

### Propósito

- Garantizar la **integridad física y lógica** de las asignaciones (un profesor no puede estar en dos lugares a la vez)
- Asegurar **equidad** en la distribución de la carga de trabajo
- Cumplir con **normativa laboral** y acuerdos del centro
- Optimizar la **continuidad y rutinas** del profesorado

### Alcance

El sistema gestiona la asignación de guardias considerando:
- **Slots**: Combinaciones de (fecha × recreo × zona × turno)
- **Profesores**: Con turnos, jornadas, tutorías y restricciones personales
- **Configuración**: Recreos, zonas, festivos y ajustes de carga

---

## 2. Validaciones Críticas (Hard Constraints)

Estas reglas **NUNCA pueden violarse**. Si no se cumplen, el profesor NO es elegible para ese slot.

### 2.1 ⚠️ **No Simultaneidad de Zonas** (CRÍTICA)

**Regla**: Un mismo profesor NO puede estar asignado a múltiples zonas al mismo tiempo.

**Definición de "mismo tiempo"**:
- Mismo **día** (fecha)
- Mismo **turno** (mañana o tarde)
- Mismo **recreo** (1º, 2º, etc.)

**Justificación**: Es físicamente imposible que una persona esté en dos lugares simultáneamente.

**Implementación**:
```python
# Archivo: src/services/asignador_guardias.py
guardias_por_slot_prof: Dict[Tuple[int, date, str, int], bool] = {}

# Validación en bucle de elegibilidad
if (p.id, slot.fecha, slot.turno, slot.recreo_id) in guardias_por_slot_prof:
    continue  # No elegible
```

**Ejemplo de violación**:
```
❌ INVÁLIDO:
Profesor: "GARCÍA LÓPEZ, ANA"
- Fecha: 2025-09-15
- Turno: mañana
- Recreo 1:
  * Zona A: Patio Principal  ← IMPOSIBLE
  * Zona B: Porche          ← IMPOSIBLE
```

**Test**: `test_no_duplicados_profesor_mismo_slot` en `tests/test_asignador.py`

---

### 2.2 ⚠️ **Máximo 1 Guardia por Día** (CRÍTICA)

**Regla**: Un profesor sólo puede hacer **como máximo 1 guardia al día**, independientemente del turno (mañana/tarde).

**Justificación**:
- Distribución equitativa de la carga
- Evitar sobrecarga diaria
- Permitir planificación personal del profesorado
- Cumplimiento de normativa y acuerdos laborales

**Implementación**:
```python
# Archivo: src/services/asignador_guardias.py
guardias_por_dia_prof: Dict[Tuple[int, date], bool] = {}

# Validación en bucle
if (p.id, slot.fecha) in guardias_por_dia_prof:
    continue  # No elegible

# Al asignar
guardias_por_dia_prof[(elegido.id, slot.fecha)] = True
```

**Ejemplos**:

✅ **VÁLIDO**:
```
Profesor: "MARTÍNEZ SANZ, JUAN"
- 2025-09-15 - MAÑANA - Recreo 1 - Zona A  ✓
- 2025-09-16 - TARDE  - Recreo 3 - Zona B  ✓
- 2025-09-17 - MAÑANA - Recreo 2 - Zona C  ✓
```

❌ **INVÁLIDO**:
```
Profesor: "MARTÍNEZ SANZ, JUAN"
- 2025-09-15 - MAÑANA - Recreo 1 - Zona A  
- 2025-09-15 - TARDE  - Recreo 3 - Zona B  ← VIOLACIÓN
```

**Test**: `test_max_una_guardia_por_dia` en `tests/test_max_una_guardia_dia.py`

---

### 2.3 ✅ **Compatibilidad de Turno**

**Regla**: Los profesores solo reciben guardias compatibles con su turno declarado.

**Criterios**:
- Turno **"mañana"**: solo guardias de mañana
- Turno **"tarde"**: solo guardias de tarde
- Turno **"mixto"**: puede recibir guardias de ambos turnos

**Implementación**:
```python
def _turno_de_recreo(turno_prof: str, recreo_turno: str) -> bool:
    if turno_prof == 'mixto':
        return True
    return turno_prof == recreo_turno
```

**Test**: `test_turno_compatible` en `tests/test_asignador.py`

---

### 2.4 ✅ **Respeto de Cuota Máxima**

**Regla**: Ningún profesor puede superar su cuota asignada de guardias.

**Justificación**: Garantiza equidad en la distribución proporcional según:
- Horas de contrato (% de jornada)
- Turno (mañana/tarde/mixto)
- Tutoría (aplicación de ajuste_tutores/ajuste_no_tutores)

**Cálculo de cuota**:
```python
peso_profesor = porcentaje_jornada × factor_turno × factor_tutoría
cuota_profesor = round(total_slots × peso_profesor / Σ pesos_profesores)
```

**Implementación**:
```python
asignadas: Dict[int, int] = defaultdict(int)
cuotas: Dict[int, int] = calcular_guardias_por_profesor(...)

# Validación
if asignadas[p.id] >= cuotas.get(p.id, 0):
    continue  # Cuota completa
```

**Test**: `test_respeta_cuotas` en `tests/test_asignador.py`

---

## 3. Validaciones de Restricciones por Profesor

Estas restricciones son **configurables por profesor** y se respetan de forma absoluta.

### 3.1 📅 **Fecha de Inicio de Guardias**

**Campo**: `Profesor.fecha_inicio_guardias` (opcional)

**Regla**: Un profesor solo puede recibir guardias a partir de su fecha de inicio configurada.

**Uso**: Incorporaciones tardías, reincorporaciones, bajas programadas.

**Implementación**:
```python
if p.fecha_inicio_guardias and slot.fecha < p.fecha_inicio_guardias:
    continue  # No elegible
```

**Ejemplo**:
```python
# Profesor de nueva incorporación
profesor.fecha_inicio_guardias = date(2025, 10, 1)

# Resultado:
# - No recibe guardias en septiembre
# - Empieza a recibir guardias desde 01/10/2025
```

**Test**: `test_respeta_fecha_inicio` en `tests/test_asignador.py`

---

### 3.2 📆 **Días de Semana Permitidos**

**Campo**: `Profesor.dias_semana_permitidos` (CSV: "0,1,2,3,4,5,6")

**Formato**: Números separados por comas donde:
- 0 = Lunes
- 1 = Martes
- 2 = Miércoles
- 3 = Jueves
- 4 = Viernes
- 5 = Sábado
- 6 = Domingo

**Valor por defecto**: "0,1,2,3,4" (Lunes a Viernes) si está vacío

**Uso**: Disponibilidad parcial, jornadas reducidas, permisos recurrentes.

**Implementación**:
```python
def _dias_semana_ok(fecha: date, dias_csv: Optional[str]) -> bool:
    if not dias_csv:
        return fecha.weekday() < 5  # L-V por defecto
    permitidos = {int(x.strip()) for x in dias_csv.split(',') if x.strip()}
    return fecha.weekday() in permitidos
```

**Ejemplos**:
```python
# Solo lunes, miércoles y viernes
profesor.dias_semana_permitidos = "0,2,4"

# Solo martes y jueves
profesor.dias_semana_permitidos = "1,3"

# Lunes a viernes (por defecto)
profesor.dias_semana_permitidos = "0,1,2,3,4"
```

**Test**: `test_respeta_dias_permitidos` en `tests/test_asignador.py`

---

### 3.3 🕐 **Recreos Permitidos**

**Campo**: `Profesor.recreos_permitidos` (CSV: "1,2,3,4")

**Formato**: IDs de recreo separados por comas según configuración del curso.

**Valor por defecto**: Todos los recreos de su turno si está vacío

**Uso**: Excluir profesores de ciertos recreos por motivos organizativos, pedagógicos o personales.

**Implementación**:
```python
def _recreo_ok(recreo_id: int, recreos_csv: Optional[str]) -> bool:
    if not recreos_csv:
        return True  # Todos los recreos
    permitidos = {int(x.strip()) for x in recreos_csv.split(',') if x.strip()}
    return recreo_id in permitidos
```

**Ejemplos**:
```python
# Solo puede cubrir recreos 1 y 3
profesor.recreos_permitidos = "1,3"

# Solo el primer recreo de mañana
profesor.recreos_permitidos = "1"

# Todos los recreos (por defecto)
profesor.recreos_permitidos = ""
```

**Test**: `test_respeta_recreos_permitidos` en `tests/test_asignador.py`

---

## 4. Validaciones de Datos del Sistema

Estas validaciones se ejecutan **antes de iniciar** la generación de guardias.

### 4.1 ⚙️ **Configuración del Curso**

**Validaciones**:
- ✅ Debe existir al menos un registro de `Configuracion`
- ✅ `fecha_fin_curso` debe ser posterior a `fecha_inicio_curso`
- ✅ Debe haber al menos un recreo configurado (mañana o tarde)

**Excepción lanzada**:
```python
raise ValueError("No existe configuración del curso")
```

**Implementación**:
```python
config = session.query(Configuracion).first()
if not config:
    raise ValueError("No existe configuración del curso")

if config.fecha_fin_curso <= config.fecha_inicio_curso:
    raise ValueError("Fecha fin debe ser posterior a fecha inicio")
```

---

### 4.2 👥 **Existencia de Profesores**

**Validación**: Debe haber al menos un profesor registrado.

**Excepción lanzada**:
```python
raise ValueError("No hay profesores registrados")
```

**Implementación**:
```python
profesores = session.query(Profesor).all()
if not profesores:
    raise ValueError("No hay profesores registrados")
```

**Test**: `test_error_sin_profesores` en `tests/test_asignador.py`

---

### 4.3 🏫 **Existencia de Zonas**

**Validación**: Debe haber al menos una zona registrada.

**Excepción lanzada**:
```python
raise ValueError("No hay zonas registradas")
```

**Implementación**:
```python
zonas = session.query(Zona).all()
if not zonas:
    raise ValueError("No hay zonas registradas")
```

**Test**: `test_error_sin_zonas` en `tests/test_asignador.py`

---

## 5. Preferencias y Heurísticas (Soft Constraints)

Estas reglas **se intentan cumplir** pero NO son bloqueantes. Se usan para **optimizar** la asignación.

### 5.1 📅 **Continuidad de Días Consecutivos**

**Preferencia**: Favorecer asignar guardias en días consecutivos al mismo profesor.

**Puntuación**: `+1` si el día anterior también tuvo guardia

**Justificación**: Facilita la planificación y crea rutinas consistentes.

**Implementación**:
```python
ultimo_dia_prof: Dict[int, date] = {}

# En scoring
s1 = 1 if (ultimo_dia_prof[p.id] and (slot.fecha - ultimo_dia_prof[p.id]).days == 1) else 0
```

---

### 5.2 🏫 **Continuidad de Zona**

**Preferencia**: Favorecer asignar la misma zona que el día anterior.

**Puntuación**: `+1` si la zona coincide con la última asignada al profesor

**Justificación**: Familiaridad con el espacio y rutinas establecidas.

**Implementación**:
```python
ultimo_por_zona: Dict[int, int] = {}  # zona_id -> profesor_id

# En scoring
s2 = 1 if ultimo_por_zona.get(slot.zona_id) == p.id else 0
```

---

### 5.3 🕐 **Continuidad de Recreo**

**Preferencia**: Favorecer asignar el mismo recreo (misma hora) que anteriormente.

**Puntuación**: `+1` si el recreo coincide con el último asignado al profesor

**Justificación**: Consistencia horaria para el profesor.

**Implementación**:
```python
ultimo_recreo_prof: Dict[int, int] = {}  # profesor_id -> recreo_id

# En scoring
s3 = 1 if ultimo_recreo_prof[p.id] == slot.recreo_id else 0
```

---

### 5.4 ⚖️ **Balance de Carga**

**Preferencia**: Favorecer profesores con menos guardias asignadas.

**Puntuación**: `-asignadas[p.id]` (negativo para priorizar menor carga)

**Justificación**: Distribución equitativa continua a lo largo del proceso.

---

### 5.5 📊 **Déficit de Cuota**

**Preferencia**: Favorecer profesores más alejados de su cuota objetivo.

**Puntuación**: `cuotas[p.id] - asignadas[p.id]`

**Justificación**: Asegurar que todos alcancen su cuota proporcional.

---

## 6. Función de Scoring

La función de puntuación combina todas las preferencias para seleccionar el mejor candidato.

### Implementación Completa

```python
def score(p: Profesor) -> Tuple[int, int, int, float]:
    # Continuidad de días
    s1 = 1 if (ultimo_dia_prof.get(p.id) and 
               (slot.fecha - ultimo_dia_prof[p.id]).days == 1) else 0
    
    # Continuidad de zona
    s2 = 1 if ultimo_por_zona.get(slot.zona_id) == p.id else 0
    
    # Continuidad de recreo
    s3 = 1 if ultimo_recreo_prof.get(p.id) == slot.recreo_id else 0
    
    # Déficit de cuota
    deficit = cuotas.get(p.id, 0) - asignadas[p.id]
    
    return (
        s1 + s2 + s3,          # (1) Suma de continuidades (0-3)
        -asignadas[p.id],      # (2) Balance de carga (menor es mejor)
        deficit,               # (3) Déficit de cuota (mayor es mejor)
        random.random()        # (4) Factor aleatorio para desempate
    )
```

### Orden de Prioridad

1. **Suma de continuidades** (máximo 3 puntos): Días + Zona + Recreo
2. **Balance de carga**: Menor número de guardias asignadas
3. **Déficit de cuota**: Mayor distancia respecto a su cuota objetivo
4. **Factor aleatorio**: Desempate para variedad

### Ejemplo de Evaluación

```python
# Escenario: Slot = (2025-09-15, mañana, recreo 1, zona A)

Profesor A:
- Última guardia: 2025-09-14 (ayer) → s1 = 1
- Última zona asignada: zona B → s2 = 0
- Último recreo: recreo 2 → s3 = 0
- Asignadas: 5
- Cuota: 20
- Déficit: 15
- Score: (1, -5, 15, 0.734)

Profesor B:
- Última guardia: 2025-09-10 (hace 5 días) → s1 = 0
- Última zona asignada: zona A → s2 = 1
- Último recreo: recreo 1 → s3 = 1
- Asignadas: 8
- Cuota: 20
- Déficit: 12
- Score: (2, -8, 12, 0.412)

Resultado: Se elige Profesor B (mayor suma de continuidades: 2 > 1)
```

---

## 7. Requisitos del Sistema

### 7.1 Configuración del Curso

**Campos obligatorios** en modelo `Configuracion`:

```python
class Configuracion:
    curso_escolar: str           # "2024-2025"
    fecha_inicio_curso: date     # 2024-09-01
    fecha_fin_curso: date        # 2025-06-30
    recreos_json: str            # JSON con recreos configurados
    ajuste_tutores: float        # 0.90 (reduce 10% carga)
    ajuste_no_tutores: float     # 1.00 (sin ajuste)
```

**Ejemplo recreos_json**:
```json
[
  {"id": 1, "turno": "mañana", "zonas": 3, "hora": "11:00"},
  {"id": 2, "turno": "mañana", "zonas": 3, "hora": "13:00"},
  {"id": 3, "turno": "tarde", "zonas": 2, "hora": "16:00"},
  {"id": 4, "turno": "tarde", "zonas": 2, "hora": "18:00"}
]
```

---

### 7.2 Días Lectivos

**Cálculo automático**:
- Se excluyen **sábados y domingos** (por defecto)
- Se excluyen **festivos** configurados (9-12 Oct, 1 Nov, 6-8 Dic, Navidad, Semana Santa, 1 Mayo)
- Se excluyen **días no lectivos personalizados** (puentes, jornadas, etc.)

**Implementación**:
```python
# Archivo: src/services/calculador_guardias.py
def listar_dias_lectivos(fecha_inicio: date, fecha_fin: date, 
                        festivos: List[date] = None) -> List[date]:
    dias = []
    actual = fecha_inicio
    while actual <= fecha_fin:
        # Excluir sábados y domingos
        if actual.weekday() < 5:  # 0-4 = L-V
            # Excluir festivos
            if festivos is None or actual not in festivos:
                dias.append(actual)
        actual += timedelta(days=1)
    return dias
```

---

### 7.3 Regla de Proporcionalidad (CLAVE)

La asignación de guardias es **estrictamente proporcional** a:

1. **Horas contratadas** (porcentaje de jornada)
2. **Tutoría** (aplicando ajuste_tutores o ajuste_no_tutores)
3. **Turno** (participación en recreos de mañana/tarde)

**Fórmula base**:
```
peso_profesor = porcentaje_jornada × factor_turno × factor_tutoría

donde:
- porcentaje_jornada = horas_contrato / 30
- factor_turno = recreos_turno / recreos_totales (para M/T), 1.0 (para mixto)
- factor_tutoría = ajuste_tutores (si es tutor), ajuste_no_tutores (si no)

cuota_profesor = round(total_slots × peso_profesor / Σ pesos_profesores)
```

**Ejemplo**:
```python
# Configuración
total_slots = 1000
ajuste_tutores = 0.90
ajuste_no_tutores = 1.00

# Profesor 1: 100% jornada, tutor, mixto
peso_p1 = 1.0 × 1.0 × 0.90 = 0.90

# Profesor 2: 100% jornada, no tutor, mixto
peso_p2 = 1.0 × 1.0 × 1.00 = 1.00

# Suma de pesos
suma = 0.90 + 1.00 = 1.90

# Cuotas
cuota_p1 = round(1000 × 0.90 / 1.90) = 474
cuota_p2 = round(1000 × 1.00 / 1.90) = 526

# Total: 474 + 526 = 1000 ✓
```

---

## 8. Criterios de Verificación

### 8.1 Post-Generación

El sistema debe garantizar:

1. ✅ **No duplicados críticos**: Ningún profesor tiene dos guardias en el mismo (fecha, turno, recreo)
2. ✅ **Respeto de cuotas**: Ningún profesor supera su cuota calculada
3. ✅ **Compatibilidad de turno**: Todos los profesores reciben solo guardias de su turno
4. ✅ **Restricciones individuales**: Se respetan fechas de inicio, días permitidos y recreos permitidos
5. ⚠️ **Cobertura completa**: Se intenta cubrir todos los slots, registrando incidencias si no es posible
6. ⚠️ **Preferencias suaves**: Se maximizan en la medida de lo posible sin violar restricciones duras

### 8.2 Verificación en Tests

```python
# Test de no duplicados en mismo slot
def test_no_duplicados_profesor_mismo_slot():
    guardias = generar_calendario_guardias(session)
    slots_por_profesor = {}
    
    for g in guardias:
        key = (g.profesor_id, g.fecha, g.turno, g.recreo_id)
        assert key not in slots_por_profesor, \
            f"Profesor {g.profesor_id} duplicado en slot {key}"
        slots_por_profesor[key] = True
```

---

## 9. Casos de Uso

### 9.1 Instituto Pequeño

**Escenario**:
```
- 15 profesores
- 100 días lectivos
- 2 recreos/día (1 mañana + 1 tarde)
- 2 zonas por recreo

Slots totales = 100 × 2 × 2 = 400

Con límite 1 guardia/día:
- Cada profesor puede hacer máximo 100 guardias
- 15 profesores × 100 días = 1500 "profesor-días" disponibles
- 400 slots / 15 profesores = ~27 guardias/profesor

✅ VIABLE: 27 < 100
```

---

### 9.2 Instituto Grande

**Escenario**:
```
- 50 profesores
- 180 días lectivos
- 4 recreos/día (2 mañana + 2 tarde)
- 3 zonas por recreo

Slots totales = 180 × 4 × 3 = 2160

Con límite 1 guardia/día:
- Cada profesor puede hacer máximo 180 guardias
- 50 profesores × 180 días = 9000 "profesor-días" disponibles
- 2160 slots / 50 profesores = ~43 guardias/profesor

✅ VIABLE: 43 < 180
```

---

### 9.3 Escenario Problemático

**Escenario**:
```
- 8 profesores
- 100 días lectivos
- 6 recreos/día
- 4 zonas por recreo

Slots totales = 100 × 6 × 4 = 2400

Con límite 1 guardia/día:
- Cada profesor puede hacer máximo 100 guardias
- 8 profesores × 100 días = 800 "profesor-días" disponibles
- Pero se necesitan cubrir 2400 slots

⚠️ PROBLEMA: No se pueden cubrir todos los slots

Solución: Añadir más profesores o reducir recreos/zonas
```

---

## 10. Mantenimiento y Extensión

### 10.1 Agregar Nueva Validación Crítica

**Pasos**:

1. Agregar la verificación en el bucle de elegibilidad de `generar_calendario_guardias()`
2. Documentar la regla en este archivo (sección 2)
3. Crear un test en `tests/test_asignador.py`
4. Actualizar referencias en documentación relacionada

**Ejemplo**:
```python
# Archivo: src/services/asignador_guardias.py

# 1. Agregar diccionario de control
nueva_validacion_dict: Dict[...] = {}

# 2. Agregar verificación en bucle
if <condición_que_viola_regla>:
    continue  # Excluir de elegibles

# 3. Actualizar diccionario al asignar
nueva_validacion_dict[<clave>] = True
```

---

### 10.2 Agregar Nueva Preferencia (Soft Constraint)

**Pasos**:

1. Modificar la función `score()` en `generar_calendario_guardias()`
2. Documentar la preferencia en este archivo (sección 5)
3. Ajustar la documentación de heurísticas
4. Validar que no degrada el rendimiento (benchmarks)

**Ejemplo**:
```python
def score(p: Profesor) -> Tuple[...]:
    # ... scoring existente ...
    
    # Nueva preferencia
    s_nueva = 1 if <condición_preferencia> else 0
    
    return (
        s1 + s2 + s3 + s_nueva,  # Incluir en continuidades
        -asignadas[p.id],
        deficit,
        random.random()
    )
```

---

## 📚 Referencias

### Archivos Fuente

- **Modelos**: `src/models/models.py`
- **Algoritmo Principal**: `src/services/asignador_guardias.py`
- **Calculador de Cuotas**: `src/services/calculador_guardias.py`
- **Interfaz de Usuario**: `src/main.py`

### Tests

- **Suite Completa**: `tests/test_asignador.py` (12 tests)
- **Límite Diario**: `tests/test_max_una_guardia_dia.py` (2 tests)
- **No Duplicados**: `tests/test_no_duplicados_profesor_mismo_slot.py` (1 test)

### Documentación Relacionada

- **Condiciones Generales**: `documentacion/condiciones_generales_asignacion.md`
- **Condiciones por Profesor**: `documentacion/condiciones_particulares_profesores.md`
- **Solución Duplicados**: `documentacion/SOLUCION_DUPLICADOS_GUARDIAS.md`

---

**Fin del documento**
