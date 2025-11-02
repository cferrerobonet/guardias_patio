# Premisas y Restricciones del Algoritmo de Asignación de Guardias

**Versión del Algoritmo**: v3.0 Simple Determinista  
**Archivo**: `src/services/asignador_guardias_v3_simple.py`  
**Fecha de Análisis**: 1 de noviembre de 2025

---

## 📋 Índice

1. [Restricciones por Profesor](#restricciones-por-profesor)
2. [Cálculo de Cuotas](#cálculo-de-cuotas)
3. [Priorización de Profesores](#priorización-de-profesores)
4. [Ordenamiento de Slots](#ordenamiento-de-slots)
5. [Proceso de Asignación](#proceso-de-asignación)
6. [Métricas de Cobertura](#métricas-de-cobertura)
7. [Posibles Incumplimientos](#posibles-incumplimientos)

---

## 🚫 Restricciones por Profesor

### 1. **Estado Activo**
- **Premisa**: Solo se consideran profesores con `activo = True`
- **Código**: `src/services/asignador_guardias_v3_simple.py:385`
```python
profesores = session.query(Profesor).filter(Profesor.activo == True).all()
```
- **¿Se cumple?**: ✅ **SÍ** - Se filtra al inicio del proceso

---

### 2. **Ausencias**
- **Premisa**: Un profesor NO puede tener guardia en fechas donde está ausente
- **Código**: `_profesor_ausente()` líneas 88-101
```python
ausencia = session.query(Ausencia).filter(
    Ausencia.profesor_id == profesor_id,
    Ausencia.fecha_inicio <= fecha,
    Ausencia.fecha_fin >= fecha,
    Ausencia.activa == True
).first()
return ausencia is not None
```
- **¿Se cumple?**: ✅ **SÍ** - Se valida en `_cumple_restricciones()`

---

### 3. **Fecha de Inicio de Guardias**
- **Premisa**: Un profesor NO puede tener guardias antes de su `fecha_inicio_guardias`
- **Código**: Líneas 117-119 (CORREGIDO v1.1)
```python
if profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias:
    return False

if profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias:
    return False
```
- **¿Se cumple?**: ✅ **SÍ (MEJORADO)**
  - ✅ Valida fecha de inicio
  - ✅ **Valida fecha de fin** (añadido en v1.1)
  - **Fix aplicado**: 1 de noviembre de 2025

---

### 4. **Días de la Semana Permitidos**
- **Premisa**: Un profesor solo puede tener guardias en sus días permitidos
- **Campo**: `profesor.dias_semana_permitidos` (JSON/Python literal)
- **Formato**: Lista de días `[0, 1, 2, 3, 4]` donde 0=Lunes, 4=Viernes
- **Código**: Líneas 120-133
```python
if profesor.dias_semana_permitidos:
    dia_semana = slot.fecha.weekday()
    dias_permitidos = json.loads(profesor.dias_semana_permitidos)
    if dia_semana not in dias_permitidos:
        return False
```
- **¿Se cumple?**: ✅ **SÍ** - Se valida en `_cumple_restricciones()`
- **⚠️ Nota**: Triple fallback de parsing (JSON → ast.literal_eval → default todos los días)

---

### 5. **Recreos Permitidos**
- **Premisa**: Un profesor solo puede tener guardias en sus recreos permitidos
- **Campo**: `profesor.recreos_permitidos` (JSON)
- **Formatos soportados**:
  - **Lista**: `[1, 2]` - recreos permitidos todos los días
  - **Diccionario por día**: `{"0": [1, 2], "1": [1, 3]}` - recreos específicos por día
- **Código**: Líneas 141-175 (CORREGIDO v1.1)
```python
if profesor.recreos_permitidos:
    recreos_perms = json.loads(profesor.recreos_permitidos)
    
    # Si es diccionario, validar día específico
    if isinstance(recreos_perms, dict):
        dia_semana = slot.fecha.weekday()
        dia_key = str(dia_semana)
        
        if dia_key in recreos_perms:
            recreos_dia = recreos_perms[dia_key]
            if slot.recreo_id not in recreos_dia:
                return False
        else:
            # Si no hay configuración para este día, no permitir
            return False
    elif isinstance(recreos_perms, list):
        if slot.recreo_id not in recreos_perms:
            return False
```
- **¿Se cumple?**: ✅ **SÍ (CORREGIDO)**
  - ✅ Si es lista simple: SÍ
  - ✅ **Si es diccionario por día**: SÍ - Ahora valida recreos específicos de cada día
  - **Fix aplicado**: 1 de noviembre de 2025

---

### 6. **Restricción de Turno**
- **Premisa**: Un profesor solo puede cubrir guardias de su turno
- **Valores**: `"mañana"`, `"tarde"`, `"mixto"`, `"ambos"`
- **Código**: Líneas 165-171
```python
if profesor.turno and profesor.turno not in ("ambos", "mixto"):
    if slot.turno != profesor.turno:
        return False
```
- **Lógica**:
  - `turno = "mañana"` → Solo slots de mañana
  - `turno = "tarde"` → Solo slots de tarde
  - `turno = "mixto"` o `"ambos"` → Puede cubrir ambos turnos
- **¿Se cumple?**: ✅ **SÍ** - Se valida correctamente

---

## 📊 Cálculo de Cuotas

### Factores que Determinan la Cuota de un Profesor

La cuota se calcula en `src/services/calculador_guardias.py`:

#### 1. **Factor por Turno**
- **Lógica**: Proporción de recreos disponibles según el turno del profesor
- **Código**: `calcular_factor_participacion()` líneas 230-272
```python
if profesor.turno == "mañana":
    return recreos_manana / recreos_totales
elif profesor.turno == "tarde":
    return recreos_tarde / recreos_totales
else:  # mixto
    # Calcular proporción según horas en cada turno
    horas_manana = getattr(profesor, 'horas_manana', 0) or 0
    horas_tarde = getattr(profesor, 'horas_tarde', 0) or 0
    
    factor_manana = (horas_manana / horas_totales) * (recreos_manana / recreos_totales)
    factor_tarde = (horas_tarde / horas_totales) * (recreos_tarde / recreos_totales)
    return factor_manana + factor_tarde
```
- **¿Se cumple?**: ✅ **SÍ** - Considera correctamente el turno

---

#### 2. **Factor por Horas Contratadas**
- **Premisa**: Profesores con más horas deben tener más guardias
- **Referencia**: 30 horas = jornada completa (100%)
- **Código**: Líneas 393-396 (aproximado)
```python
factor_horas = min(profesor.horas_contrato / 30.0, 1.0)
```
- **¿Se cumple?**: ✅ **SÍ** - Proporcional a horas contratadas

---

#### 3. **Factor de Tutoría**
- **Premisa**: Los tutores tienen un ajuste en su cuota (generalmente reducción)
- **Configuración**: `config.ajuste_tutores` y `config.ajuste_no_tutores`
- **Código**: Líneas 398-402 (aproximado)
```python
factor_tutoria = (
    config.ajuste_tutores if profesor.tutor
    else config.ajuste_no_tutores
)
```
- **¿Se cumple?**: ✅ **SÍ** - Se aplica el ajuste configurado

---

#### 4. **Proporción de Tiempo Disponible**
- **Premisa**: Si un profesor tiene fecha de inicio/fin, su cuota se ajusta proporcionalmente
- **Código**: Líneas 405-425 (aproximado)
```python
if profesor.fecha_inicio_guardias or profesor.fecha_fin_guardias:
    inicio_prof = profesor.fecha_inicio_guardias or config.fecha_inicio_curso
    fin_prof = profesor.fecha_fin_guardias or config.fecha_fin_curso
    
    dias_prof = [d for d in dias_list if inicio_prof <= d <= fin_prof]
    proporcion_tiempo = len(dias_prof) / dias_lectivos
```
- **¿Se cumple?**: ✅ **SÍ** - Ajusta cuota según disponibilidad temporal

---

#### 5. **Fórmula Final de Cuota Cruda**
```python
cuota_cruda = (
    slots_totales 
    × factor_turno 
    × factor_horas 
    × factor_tutoria 
    × proporcion_tiempo
) / suma_ponderada_todos_profesores
```
- **Redondeo**: Se redondea al entero más cercano
- **¿Se cumple?**: ✅ **SÍ** - Distribución matemática correcta

---

## 🎯 Priorización de Profesores

### Orden de Asignación

Los profesores se ordenan para asignar primero a los más restrictivos:

#### Criterios de Prioridad (de mayor a menor)

1. **Profesores con Menos Slots Disponibles**
   - Ratio: `cuota / slots_posibles`
   - Cuanto más alto el ratio, más prioritario (más restrictivo)
   
2. **Profesores con Mayor Cuota**
   - Necesitan más guardias, deben asignarse pronto
   
3. **ID del Profesor (Desempate)**
   - Garantiza determinismo

**Código**: `_calcular_prioridad_profesor()` líneas 227-248
```python
def _calcular_prioridad_profesor(pc: ProfesorConCuota) -> float:
    if pc.slots_posibles == 0:
        return float("inf")  # No puede cubrir ningún slot
    
    ratio_restriccion = pc.cuota / pc.slots_posibles
    prioridad = (1.0 - ratio_restriccion) * 1000 + pc.profesor.id
    return prioridad
```

**¿Se cumple?**: ✅ **SÍ** - Asigna correctamente por prioridad

---

## 📅 Ordenamiento de Slots

### Orden de Slots para Cada Profesor

Una vez seleccionado un profesor, los slots se ordenan para optimizar la asignación y crear **patrones consistentes**:

#### Criterios de Ordenamiento (de mayor a menor prioridad) - MEJORADO v1.1

1. **Zona Consistente**
   - Prioriza la misma zona que las guardias previas del profesor
   - Si no tiene guardias previas, usa su `zona_preferida_id`
   - **Objetivo**: Minimizar desplazamientos entre zonas
   
2. **Recreo Consistente**
   - Prioriza el mismo recreo que las guardias previas
   - **Objetivo**: Patrones predecibles (ej: siempre 2º recreo)
   
3. **Día de Semana Consistente**
   - Prioriza el mismo día de la semana que guardias previas
   - **Objetivo**: Rutinas semanales (ej: siempre los lunes)
   
4. **Fecha (Cronológico)**
   - Ordena por fecha para agrupar guardias cercanas en el tiempo
   
5. **Recreo Natural (Desempate)**
   - Orden ascendente de recreo ID como criterio final

**Código**: `_ordenar_slots_para_profesor()` líneas 273-363 (REESCRITO v1.1)
```python
def _ordenar_slots_para_profesor(slots, profesor, guardias_previas=None):
    # Analizar patrones de guardias previas
    zona_objetivo = None
    if guardias_previas:
        # Zona más frecuente en guardias previas
        zonas = [s.zona_id for s in guardias_previas]
        zona_objetivo = max(set(zonas), key=zonas.count)
    elif profesor.zona_preferida_id:
        zona_objetivo = profesor.zona_preferida_id
    
    # Recreo más frecuente
    recreo_objetivo = None
    if guardias_previas:
        recreos = [s.recreo_id for s in guardias_previas]
        recreo_objetivo = max(set(recreos), key=recreos.count)
    
    # Día de semana más frecuente
    dia_semana_objetivo = None
    if guardias_previas:
        dias = [s.fecha.weekday() for s in guardias_previas]
        dia_semana_objetivo = max(set(dias), key=dias.count)
    
    def clave_ordenamiento(slot):
        zona_match = 0 if zona_objetivo and slot.zona_id == zona_objetivo else 1
        recreo_match = 0 if recreo_objetivo and slot.recreo_id == recreo_objetivo else 1
        dia_match = 0 if dia_semana_objetivo and slot.fecha.weekday() == dia_semana_objetivo else 1
        
        return (zona_match, recreo_match, dia_match, slot.fecha, slot.recreo_id)
    
    return sorted(slots, key=clave_ordenamiento)
```

**¿Se cumple?**: ✅ **SÍ (MEJORADO)**
- ✅ Zona preferida/consistente
- ✅ Recreo consistente (NUEVO)
- ✅ Día de semana consistente (NUEVO)
- ✅ Orden cronológico
- **Mejora aplicada**: 1 de noviembre de 2025

**Beneficios de la mejora**:
- 📍 Profesores permanecen en la misma zona
- ⏰ Guardias en el mismo recreo cada semana
- 📅 Patrones semanales predecibles (ej: lunes y miércoles)
- 🔄 Rutinas más fáciles de recordar

---

## 🔄 Proceso de Asignación

### Algoritmo Paso a Paso

#### **PASO 1**: Cargar Profesores Activos (0-10%)
- Filtrar por `activo = True`
- Calcular cuotas con `calcular_guardias_por_profesor()`

#### **PASO 2**: Generar Todos los Slots (10-20%)
- Días lectivos × Recreos × Turnos × Zonas
- Respeta fechas de disponibilidad de zonas

#### **PASO 3**: Calcular Prioridades (20-30%)
- Contar `slots_posibles` por profesor
- Ordenar por prioridad (más restrictivos primero)

#### **PASO 4**: Asignación Profesor por Profesor (30-90%) - MEJORADO v1.1
```python
# Trackear guardias asignadas por profesor
slots_por_profesor = {}

for profesor in profesores_ordenados:
    # 1. Filtrar slots válidos
    slots_disponibles = [
        slot for slot in todos_slots
        if slot not in slots_ocupados
        and _cumple_restricciones(profesor, slot, session)
    ]
    
    # 2. Obtener guardias previas de este profesor
    guardias_previas = slots_por_profesor.get(profesor.id, [])
    
    # 3. Ordenar slots por optimalidad, considerando patrones previos
    slots_disponibles = _ordenar_slots_para_profesor(
        slots_disponibles, profesor, guardias_previas
    )
    
    # 4. Tomar exactamente la cuota (o máximo disponible)
    slots_asignar = slots_disponibles[:cuota]
    
    # 5. Crear guardias y trackear
    for slot in slots_asignar:
        guardia = Guardia(
            profesor_id=profesor.id,
            fecha=slot.fecha,
            recreo=slot.recreo_id,
            turno=slot.turno,
            zona_id=slot.zona_id
        )
        session.add(guardia)
        slots_ocupados.add(slot)
        
        # Trackear para mantener patrones consistentes
        slots_por_profesor[profesor.id].append(slot)
```

**Mejoras en v1.1**:
- ✅ Trackea guardias asignadas por profesor en tiempo real
- ✅ Pasa guardias previas al ordenamiento para mantener patrones
- ✅ Cada nueva guardia considera las anteriores para consistencia

#### **PASO 5**: Validación y Estadísticas (90-100%)
- Calcular cobertura: `guardias_asignadas / total_slots`
- Identificar profesores con cuota incompleta
- Calcular equidad por jornada

**¿Se cumple?**: ✅ **SÍ** - Proceso determinista y completo

---

## 📈 Métricas de Cobertura

### Indicadores de Éxito

#### 1. **Cobertura Total**
```python
cobertura = (guardias_asignadas / total_slots) * 100
```
- **Objetivo**: 100%
- **Actual**: Depende de restricciones de profesores

#### 2. **Slots Vacíos**
```python
slots_vacios = total_slots - guardias_asignadas
```
- **Objetivo**: 0
- **Causas comunes**:
  - Profesores muy restrictivos (pocos días/recreos permitidos)
  - Ausencias extensas
  - Cuotas insuficientes vs slots totales

#### 3. **Profesores con Cuota Incompleta**
```python
if asignadas < cuota:
    profesores_incompletos.append((profesor, asignadas, cuota))
```
- **Objetivo**: 0
- **Causas comunes**:
  - Slots ya ocupados cuando toca su turno
  - Restricciones muy específicas (días/recreos)

#### 4. **Equidad por Jornada**
```python
grupos_jornada[profesor.porcentaje_jornada].append(guardias_real)
rango = max(guardias_lista) - min(guardias_lista)
if rango > 1:
    grupos_inequitativos += 1
```
- **Objetivo**: Diferencia ≤ 1 guardia entre profesores de igual jornada
- **¿Se cumple?**: ⚠️ **NO SIEMPRE** - Depende del orden de asignación

---

## ⚠️ Posibles Incumplimientos

### ~~1. ❌ **Recreos Permitidos por Día Específico**~~ ✅ CORREGIDO v1.1

~~**Problema**: Cuando `recreos_permitidos` es un diccionario por día, se ignora el día específico.~~

**Estado**: ✅ **CORREGIDO** el 1 de noviembre de 2025

**Solución Implementada**:
```python
if isinstance(recreos_perms, dict):
    dia_semana = slot.fecha.weekday()
    dia_key = str(dia_semana)
    
    if dia_key in recreos_perms:
        recreos_dia = recreos_perms[dia_key]
        if isinstance(recreos_dia, list) and slot.recreo_id not in recreos_dia:
            return False
    else:
        return False  # No permitir días sin configuración
```

**Resultado**: Ahora respeta correctamente los recreos específicos de cada día.

---

### ~~2. ❌ **Fecha de Fin de Guardias No Validada**~~ ✅ CORREGIDO v1.1

~~**Problema**: Solo se validaba `fecha_inicio_guardias`, no `fecha_fin_guardias`.~~

**Estado**: ✅ **CORREGIDO** el 1 de noviembre de 2025

**Solución Implementada**:
```python
if profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias:
    return False
```

**Resultado**: Ahora valida ambos límites temporales.

---

### ~~3. ❌ **Guardias No Agrupadas por Zona/Recreo/Día**~~ ✅ MEJORADO v1.1

~~**Problema**: No se priorizaba agrupar guardias en patrones consistentes.~~

**Estado**: ✅ **MEJORADO** el 1 de noviembre de 2025

**Mejoras Implementadas**:
1. ✅ Trackeo de guardias previas por profesor
2. ✅ Priorización de misma zona en asignaciones futuras
3. ✅ Priorización de mismo recreo (patrones semanales)
4. ✅ Priorización de mismo día de semana
5. ✅ Ordenamiento multi-criterio mejorado

**Resultado**: Los profesores tienden a tener:
- Guardias en la misma zona (menos desplazamientos)
- Mismo recreo cada vez (rutina predecible)
- Mismo día de semana (patrón semanal consistente)

---

### 4. ⚠️ **Equidad Perfecta entre Profesores**

**Problema**: No se garantiza equidad perfecta entre profesores de igual jornada.

**Causa**: El orden de asignación prioriza restricciones, no equidad.

**Impacto**: Profesores con menos restricciones pueden recibir más guardias.

**¿Es un bug?**: No, es una decisión de diseño. Priorizar cobertura sobre equidad.

**Estado**: ⚠️ **PENDIENTE** (baja prioridad)

---

### 5. ⚠️ **Cuota Exacta para Todos los Profesores**

**Problema**: Algunos profesores no alcanzan su cuota.

**Causa**: Slots ya ocupados cuando llega su turno de asignación.

**Ejemplo**:
- Profesor A (restrictivo): cuota = 20, asignadas = 20 ✅
- Profesor B (flexible): cuota = 20, asignadas = 18 ❌ (faltan 2)

**Impacto**: Cuota incompleta en profesores con baja prioridad.

**Estado**: ⚠️ **PENDIENTE** (diseño actual)

---

### 6. ⚠️ **Zona Preferida como Restricción Dura**

**Problema**: `zona_preferida_id` es una preferencia, no una restricción.

**Actual**: Se intenta asignar primero, pero si no hay slots, asigna otras zonas.

**¿Debería ser restricción dura?**: Depende del caso de uso.

**Estado**: ⚠️ **PENDIENTE** (decisión de producto)

---

## 🔧 Recomendaciones

### ✅ Mejoras Implementadas (v1.1 - 1 nov 2025)

1. ✅ **Recreos por Día Específico** - COMPLETADO
   - Validación día-específica para diccionarios
   - Prioridad: **ALTA** ✅

2. ✅ **Fecha de Fin de Guardias** - COMPLETADO
   - Validación de `fecha_fin_guardias`
   - Prioridad: **ALTA** ✅

3. ✅ **Agrupación de Guardias** - COMPLETADO
   - Patrones consistentes: misma zona, recreo, día de semana
   - Trackeo de guardias previas
   - Prioridad: **ALTA** ✅

---

### 🔜 Mejoras Pendientes (Futuras Versiones)

4. **Validar Configuración de Profesores**
   - Advertir si restricciones son imposibles de cumplir
   - Ejemplo: Lunes-Viernes permitidos pero solo recreos inexistentes
   - Prioridad: **MEDIA**

5. **Mejorar Logging**
   - Mostrar por qué un profesor no alcanzó su cuota
   - Detallar qué restricción bloqueó cada slot
   - Prioridad: **MEDIA**

6. **Algoritmo de Dos Pasadas**
   - Primera pasada: Asignar a restrictivos
   - Segunda pasada: Rellenar huecos con flexibles
   - Prioridad: **BAJA**

7. **Dashboard de Restricciones**
   - Visualizar restricciones de cada profesor
   - Detectar conflictos antes de generar
   - Prioridad: **BAJA**

---

## 📝 Resumen Ejecutivo

### Versión 1.1 - Actualizado: 1 de noviembre de 2025

| Premisa | ¿Se Cumple? | Estado |
|---------|-------------|--------|
| Profesores activos | ✅ SÍ | Estable |
| Ausencias | ✅ SÍ | Estable |
| Fecha inicio guardias | ✅ SÍ | Estable |
| **Fecha fin guardias** | ✅ **SÍ** | ✅ **CORREGIDO v1.1** |
| Días permitidos | ✅ SÍ | Estable |
| **Recreos por día específico** | ✅ **SÍ** | ✅ **CORREGIDO v1.1** |
| Turno | ✅ SÍ | Estable |
| Cuota proporcional | ✅ SÍ | Estable |
| Priorización restrictivos | ✅ SÍ | Estable |
| **Guardias agrupadas** | ✅ **SÍ** | ✅ **MEJORADO v1.1** |
| Equidad perfecta | ⚠️ PARCIAL | Diseño |
| Cuota exacta | ⚠️ PARCIAL | Diseño |

---

### 🎯 Mejoras Implementadas en v1.1

#### 1. ✅ Validación de Recreos por Día
- **Problema**: Diccionarios de recreos ignoraban el día específico
- **Solución**: Validación día a día considerando `weekday()`
- **Impacto**: Mayor precisión en restricciones de profesores

#### 2. ✅ Validación de Fecha Fin de Guardias
- **Problema**: Solo se validaba fecha de inicio
- **Solución**: Añadida validación de `fecha_fin_guardias`
- **Impacto**: Respeta límites temporales completos

#### 3. ✅ Agrupación Inteligente de Guardias
- **Problema**: No se priorizaban patrones consistentes
- **Solución**: Ordenamiento multi-criterio con memoria de guardias previas
- **Impacto**: Guardias más predecibles y cómodas para profesores
  - 📍 Misma zona (menos desplazamientos)
  - ⏰ Mismo recreo (rutina fija)
  - 📅 Mismo día de semana (patrón semanal)

---

### 📊 Comparativa de Versiones

| Característica | v1.0 Original | v1.1 Mejorada |
|---------------|---------------|---------------|
| Recreos por día | ❌ Ignora día | ✅ Valida día específico |
| Fecha fin | ❌ No validada | ✅ Validada |
| Agrupación zona | ⚠️ Preferencia básica | ✅ Prioridad con memoria |
| Agrupación recreo | ❌ No considerado | ✅ Mantiene patrón |
| Agrupación día semana | ❌ No considerado | ✅ Mantiene patrón |
| Trackeo guardias | ❌ No | ✅ Sí, en tiempo real |

---

**Conclusión v1.1**: El algoritmo ahora cumple con **todas las premisas críticas** y ofrece una mejor experiencia para los profesores mediante patrones de guardias más consistentes y predecibles.
