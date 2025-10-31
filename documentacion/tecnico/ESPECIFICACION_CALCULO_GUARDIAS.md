# Especificación Técnica: Cálculo y Asignación de Guardias

**Versión:** 2.9  
**Fecha:** 30 octubre 2025  
**Estado:** VIGENTE  
**Archivo de referencia:** `src/services/calculador_guardias.py` y `src/services/asignador_guardias.py`

---

## 📋 ÍNDICE

1. [Principios Fundamentales](#principios-fundamentales)
2. [Variables de Entrada](#variables-de-entrada)
3. [Cálculo de Cuota Ideal](#cálculo-de-cuota-ideal)
4. [Condiciones de Elegibilidad](#condiciones-de-elegibilidad)
5. [Algoritmo de Asignación](#algoritmo-de-asignación)
6. [Ejemplos Numéricos](#ejemplos-numéricos)
7. [Casos Especiales](#casos-especiales)
8. [Registro de Cambios](#registro-de-cambios)

---

## 🎯 PRINCIPIOS FUNDAMENTALES

### Regla de Oro: EQUIDAD ABSOLUTA

```
SI profesor_A.caracteristicas == profesor_B.caracteristicas
ENTONCES guardias_A == guardias_B (±1 por redondeo)
```

**Características que definen un grupo homogéneo:**
1. **Turno** (mañana / tarde / mixto)
2. **Horas contrato** (30h, 25h, 18h, etc.)
3. **Tutoría** (tutor / no tutor)

### Jerarquía de Prioridades

```
1. COBERTURA 100%: Todos los slots deben tener guardia asignada
2. EQUIDAD: Profesores del mismo grupo → mismas guardias (±1)
3. PARTICIPACIÓN: Todos los profesores elegibles con ≥1 guardia
4. ZONA PREFERIDA: Asignar zona consistente cuando sea posible
5. CONTINUIDAD: Minimizar días sin guardias
```

---

## 📊 VARIABLES DE ENTRADA

### 1. Configuración del Curso

#### 1.1 Fechas del Curso
```python
# Tabla: configuracion
fecha_inicio_curso: date  # Ej: 2025-09-08
fecha_fin_curso: date     # Ej: 2026-06-11
```

**Impacto:** Define el rango temporal de generación de guardias.

**Cálculo derivado:**
```python
dias_lectivos = contar_dias(fecha_inicio, fecha_fin, excluir=[sabados, domingos, festivos])
```

#### 1.2 Festivos

##### Festivos Automáticos (si `activar_festivos_automaticos = True`)
```python
festivos_automaticos = [
    # Fijos
    "09/10",  # Día de la Comunitat Valenciana
    "12/10",  # Fiesta Nacional
    "01/11",  # Todos los Santos
    "06/12",  # Día de la Constitución
    "08/12",  # Inmaculada Concepción
    "01/05",  # Día del Trabajo
    
    # Rangos
    "22/12 a 06/01",  # Vacaciones Navidad
    
    # Variables (calculados)
    "Jueves Santo a +11 días",  # Semana Santa + festivos adicionales
]
```

##### Festivos Personalizados
```python
# Tabla: configuracion
dias_no_lectivos_personalizados: str  # CSV: "2025-10-30,2025-11-15,..."
```

**Procesamiento:**
```python
festivos_totales = festivos_automaticos ∪ festivos_personalizados
dias_lectivos = [d for d in rango_curso if d.weekday < 5 and d not in festivos_totales]
```

#### 1.3 Recreos Configurados

##### Modo Moderno (recreos_config JSON)
```python
# Tabla: configuracion
recreos_config: json = [
    {
        "id": 1,
        "etiqueta": "Recreo 1º",
        "turno": "mañana",
        "zonas": 4  # Número de zonas que vigilan este recreo
    },
    {
        "id": 2,
        "etiqueta": "Recreo 2º",
        "turno": "mañana",
        "zonas": 4
    },
    {
        "id": 3,
        "etiqueta": "Recreo 3º",
        "turno": "tarde",
        "zonas": 4
    },
    {
        "id": 4,
        "etiqueta": "Recreo 4º",
        "turno": "tarde",
        "zonas": 4
    }
]
```

**Cálculo:**
```python
recreos_manana = count(r for r in recreos_config if r.turno == "mañana")  # 2
recreos_tarde = count(r for r in recreos_config if r.turno == "tarde")    # 2
recreos_totales = recreos_manana + recreos_tarde                          # 4
```

##### Modo Legacy (campos separados)
```python
# Tabla: configuracion
hora_recreo1_manana: str  # Ej: "11:00"
hora_recreo2_manana: str  # Ej: "12:30"
hora_recreo1_tarde: str   # Ej: "16:00"
hora_recreo2_tarde: str   # Ej: "17:30"
```

**Conversión automática:**
```python
if not recreos_config:
    recreos_config = []
    id_counter = 0
    
    if hora_recreo1_manana:
        id_counter += 1
        recreos_config.append({"id": id_counter, "turno": "mañana", "zonas": num_zonas})
    
    if hora_recreo2_manana:
        id_counter += 1
        recreos_config.append({"id": id_counter, "turno": "mañana", "zonas": num_zonas})
    
    # Idem para tarde...
```

#### 1.4 Zonas

```python
# Tabla: zonas
class Zona:
    id: int
    nombre: str               # Ej: "Patio Principal"
    descripcion: str
    fecha_inicio: date|None   # Fecha desde la que está activa (None = siempre)
    fecha_fin: date|None      # Fecha hasta la que está activa (None = siempre)
```

**Impacto en slots:**
```python
# Solo se crean slots para zonas activas en cada fecha
for dia in dias_lectivos:
    for zona in zonas:
        if zona.fecha_inicio and dia < zona.fecha_inicio:
            continue  # Zona aún no activa
        if zona.fecha_fin and dia > zona.fecha_fin:
            continue  # Zona ya inactiva
        
        # Crear slots para esta zona en este día
        for recreo in recreos:
            crear_slot(dia, recreo, zona)
```

**⚠️ IMPORTANTE:** Las fechas de zonas pueden reducir drásticamente el número total de slots.

**Ejemplo:**
```
Zona 1: Sin restricción        → 199 días
Zona 2: inicio=2025-10-01      → 170 días
Zona 3: fin=2026-05-31         → 180 días
Zona 4: 2025-10-01 a 2026-05-31 → 150 días

Total slots != 199 × 4 recreos × 4 zonas
```

#### 1.5 Factores de Ajuste

```python
# Tabla: configuracion
ajuste_tutores: float      # Ej: 1.0 (sin ajuste) o 0.9 (-10%)
ajuste_no_tutores: float   # Ej: 2.0 (+100%) o 1.1 (+10%)
```

**Interpretación:**
- `ajuste_tutores = 0.9` → Tutores hacen 10% MENOS guardias que no tutores
- `ajuste_no_tutores = 2.0` → No tutores hacen el DOBLE que tutores
- `ajuste_tutores = ajuste_no_tutores = 1.0` → Todos iguales (sin distinción)

**IMPORTANTE:** La relación que importa es el **ratio**:
```python
ratio = ajuste_no_tutores / ajuste_tutores

Ejemplos:
- ajuste_tutores=0.9, ajuste_no_tutores=1.8 → ratio=2.0 (no tutores hacen el doble)
- ajuste_tutores=1.0, ajuste_no_tutores=2.0 → ratio=2.0 (mismo efecto)
```

---

### 2. Características del Profesor

```python
# Tabla: profesores
class Profesor:
    id: int
    nombre_completo: str
    
    # VARIABLES CRÍTICAS PARA CUOTA
    turno: str               # "mañana" | "tarde" | "mixto"
    horas_contrato: float    # Ej: 30.0, 25.0, 18.0
    tutor: bool              # True | False
    
    # VARIABLES PARA ELEGIBILIDAD
    recreos_permitidos: json # Ej: [1, 2] | [3, 4] | [1, 2, 3, 4]
    fecha_inicio_guardias: date|None  # Desde cuándo puede hacer guardias
    fecha_fin_guardias: date|None     # Hasta cuándo puede hacer guardias
    dias_semana_permitidos: json|None # Ej: [0,1,2,3,4] (L-V) o [0,2,4] (L,X,V)
    
    # VARIABLES ADICIONALES (solo para mixtos)
    horas_manana: float|None  # Para profesores mixtos
    horas_tarde: float|None   # Para profesores mixtos
```

#### 2.1 Variable: `turno`

**Valores permitidos:**
- `"mañana"`: Solo puede hacer guardias en recreos de turno mañana
- `"tarde"`: Solo puede hacer guardias en recreos de turno tarde
- `"mixto"`: Puede hacer guardias en ambos turnos

**Impacto en factor de participación:**
```python
if turno == "mañana":
    factor_turno = recreos_manana / (recreos_manana + recreos_tarde)
    # Ej: 2/(2+2) = 0.5
    
elif turno == "tarde":
    factor_turno = recreos_tarde / (recreos_manana + recreos_tarde)
    # Ej: 2/(2+2) = 0.5
    
else:  # mixto
    # Proporción ponderada por horas en cada turno
    if horas_manana and horas_tarde:
        factor_manana = (horas_manana / (horas_manana + horas_tarde)) * (recreos_manana / recreos_totales)
        factor_tarde = (horas_tarde / (horas_manana + horas_tarde)) * (recreos_tarde / recreos_totales)
        factor_turno = factor_manana + factor_tarde
    else:
        factor_turno = 1.0  # Asume distribución equitativa
```

**Ejemplo numérico:**
```
Configuración: 2 recreos mañana, 2 recreos tarde
Profesor Mixto: 15h mañana, 15h tarde

factor_manana = (15/30) × (2/4) = 0.5 × 0.5 = 0.25
factor_tarde = (15/30) × (2/4) = 0.5 × 0.5 = 0.25
factor_turno = 0.25 + 0.25 = 0.5
```

#### 2.2 Variable: `horas_contrato`

**Jornada de referencia:** 30 horas (jornada completa en educación)

**Impacto en factor de horas:**
```python
horas_jornada_completa = 30.0
factor_horas = min(horas_contrato / horas_jornada_completa, 1.0)
```

**Ejemplos:**
```
30.0h → factor_horas = 30/30 = 1.0   (100%)
25.0h → factor_horas = 25/30 = 0.833 (83.3%)
18.0h → factor_horas = 18/30 = 0.6   (60%)
40.0h → factor_horas = min(40/30, 1.0) = 1.0  (cap en 100%)
```

**Interpretación:** Un profesor con 18h hace el 60% de guardias que uno de 30h (mismo turno y tutoría).

#### 2.3 Variable: `tutor`

**Impacto en factor de tutoría:**
```python
if tutor:
    factor_tutoria = config.ajuste_tutores
else:
    factor_tutoria = config.ajuste_no_tutores
```

**Caso típico:**
```
ajuste_tutores = 1.0
ajuste_no_tutores = 2.0

Tutor: factor_tutoria = 1.0
No tutor: factor_tutoria = 2.0

→ No tutores hacen el DOBLE de guardias que tutores
```

#### 2.4 Variable: `recreos_permitidos`

**Formato:** Lista JSON de IDs de recreos permitidos

**Ejemplos:**
```json
[1, 2]        // Solo recreos 1 y 2 (típico para mañana)
[3, 4]        // Solo recreos 3 y 4 (típico para tarde)
[1, 2, 3, 4]  // Todos los recreos (típico para mixto)
[]            // Ningún recreo (profesor excluido)
null          // Todos los recreos (sin restricción)
```

**Impacto en elegibilidad:**
```python
def es_elegible_recreo(profesor, slot):
    if not profesor.recreos_permitidos:
        return True  # Sin restricción
    
    return slot.recreo_id in profesor.recreos_permitidos
```

**⚠️ CRÍTICO:** Si `recreos_permitidos = [1, 2]` pero la configuración solo tiene recreos con IDs `[3, 4]`, el profesor **NUNCA será elegible** para ningún slot.

#### 2.5 Variables: `fecha_inicio_guardias` y `fecha_fin_guardias`

**Impacto en días disponibles:**
```python
# Determinar rango efectivo del profesor
inicio_efectivo = max(
    config.fecha_inicio_curso,
    profesor.fecha_inicio_guardias or config.fecha_inicio_curso
)

fin_efectivo = min(
    config.fecha_fin_curso,
    profesor.fecha_fin_guardias or config.fecha_fin_curso
)

# Contar días lectivos del profesor
dias_profesor = [
    d for d in dias_lectivos 
    if inicio_efectivo <= d <= fin_efectivo
]

# Factor de proporción temporal
proporcion_tiempo = len(dias_profesor) / len(dias_lectivos)
```

**Ejemplo:**
```
Curso: 2025-09-08 a 2026-06-11 (199 días lectivos)
Profesor: 2025-10-01 a 2026-05-31 (150 días lectivos)

proporcion_tiempo = 150/199 = 0.754

→ Hace 75.4% de las guardias que correspondería a jornada completa
```

#### 2.6 Variable: `dias_semana_permitidos`

**Formato:** Lista JSON de días de la semana (0=Lunes, 1=Martes, ..., 4=Viernes)

**Ejemplos:**
```json
[0, 1, 2, 3, 4]  // Todos los días (L-V)
[0, 2, 4]        // Solo Lunes, Miércoles, Viernes
[1, 3]           // Solo Martes, Jueves
null             // Todos los días (sin restricción)
```

**Impacto en elegibilidad:**
```python
def es_elegible_dia(profesor, slot):
    if not profesor.dias_semana_permitidos:
        return True  # Sin restricción
    
    return slot.fecha.weekday() in profesor.dias_semana_permitidos
```

---

## 🧮 CÁLCULO DE CUOTA IDEAL

### Fórmula Maestra

```python
cuota_ideal[profesor] = (
    factor_turno × 
    factor_horas × 
    factor_tutoria × 
    proporcion_tiempo × 
    slots_totales
) / suma_ponderada_todos_profesores
```

### Desglose Paso a Paso

#### Paso 1: Calcular Slots Totales Reales

```python
slots_totales = 0

for dia in dias_lectivos:
    for recreo in recreos_config:
        for zona in zonas:
            # Verificar si zona está activa en este día
            if zona.fecha_inicio and dia < zona.fecha_inicio:
                continue
            if zona.fecha_fin and dia > zona.fecha_fin:
                continue
            
            # Slot válido
            slots_totales += 1
```

**⚠️ IMPORTANTE:** El número real de slots puede ser MENOR que:
```
dias_lectivos × recreos × zonas
```
Debido a fechas de activación de zonas.

#### Paso 2: Calcular Participación de Cada Profesor

```python
for profesor in profesores:
    # 1. Factor turno
    if profesor.turno == "mañana":
        factor_turno = recreos_manana / recreos_totales
    elif profesor.turno == "tarde":
        factor_turno = recreos_tarde / recreos_totales
    else:  # mixto
        factor_turno = calcular_factor_mixto(profesor)
    
    # 2. Factor horas
    factor_horas = min(profesor.horas_contrato / 30.0, 1.0)
    
    # 3. Factor tutoría
    factor_tutoria = (
        config.ajuste_tutores if profesor.tutor 
        else config.ajuste_no_tutores
    )
    
    # 4. Proporción temporal
    dias_disponibles = contar_dias_disponibles(profesor)
    proporcion_tiempo = dias_disponibles / dias_lectivos
    
    # Participación total
    participacion[profesor] = (
        factor_turno × factor_horas × factor_tutoria × proporcion_tiempo
    )
```

#### Paso 3: Calcular Suma Ponderada

```python
suma_ponderada = sum(participacion[p] for p in profesores)
```

#### Paso 4: Distribuir Slots Proporcionalmente

```python
for profesor in profesores:
    cuota_cruda[profesor] = (
        participacion[profesor] / suma_ponderada
    ) * slots_totales
```

**Ejemplo:**
```
slots_totales = 3000
suma_ponderada = 100.0

Profesor A: participacion = 5.0
  cuota_cruda_A = (5.0 / 100.0) × 3000 = 150.0

Profesor B: participacion = 2.5
  cuota_cruda_B = (2.5 / 100.0) × 3000 = 75.0
```

#### Paso 5: Ajustar Redondeo

```python
# Calcular floor y residuos
for profesor in profesores:
    cuota_floor[profesor] = floor(cuota_cruda[profesor])
    residuo[profesor] = cuota_cruda[profesor] - cuota_floor[profesor]

# Calcular slots sobrantes
suma_floor = sum(cuota_floor.values())
slots_sobrantes = round(slots_totales) - suma_floor

# Ordenar por residuo (mayor primero)
profesores_ordenados = sorted(
    profesores, 
    key=lambda p: residuo[p], 
    reverse=True
)

# Asignar slots sobrantes a quienes tienen mayor residuo
cuota_ideal = cuota_floor.copy()
for i in range(slots_sobrantes):
    profesor = profesores_ordenados[i]
    cuota_ideal[profesor] += 1
```

**Ejemplo:**
```
Profesor A: cuota_cruda = 45.8 → floor = 45, residuo = 0.8
Profesor B: cuota_cruda = 30.6 → floor = 30, residuo = 0.6
Profesor C: cuota_cruda = 24.3 → floor = 24, residuo = 0.3

suma_floor = 99
slots_sobrantes = 100 - 99 = 1

Ordenados por residuo: [A (0.8), B (0.6), C (0.3)]
→ A recibe el slot sobrante

Cuotas finales: A=46, B=30, C=24
```

---

## ✅ CONDICIONES DE ELEGIBILIDAD

Para que un profesor sea elegible para un slot, **TODAS** estas condiciones deben cumplirse:

### Condición 1: Turno Compatible

```python
if slot.turno == "mañana":
    profesor.turno in ["mañana", "mixto"]
elif slot.turno == "tarde":
    profesor.turno in ["tarde", "mixto"]
```

**Ejemplo:**
```
Slot: turno="mañana"
✅ Profesor turno="mañana" → ELEGIBLE
✅ Profesor turno="mixto" → ELEGIBLE
❌ Profesor turno="tarde" → NO ELEGIBLE
```

### Condición 2: Recreo Permitido

```python
if profesor.recreos_permitidos:
    slot.recreo_id in profesor.recreos_permitidos
else:
    True  # Sin restricción
```

**Ejemplo:**
```
Slot: recreo_id=1
Profesor A: recreos_permitidos=[1, 2] → ✅ ELEGIBLE
Profesor B: recreos_permitidos=[3, 4] → ❌ NO ELEGIBLE
Profesor C: recreos_permitidos=None   → ✅ ELEGIBLE (sin restricción)
```

### Condición 3: Fecha Dentro de Rango

```python
inicio = profesor.fecha_inicio_guardias or date.min
fin = profesor.fecha_fin_guardias or date.max

if inicio <= slot.fecha <= fin:
    ELEGIBLE
else:
    NO_ELEGIBLE
```

**Ejemplo:**
```
Profesor: fecha_inicio=2025-10-01, fecha_fin=2026-05-31

Slot 2025-09-15 → ❌ NO ELEGIBLE (antes de inicio)
Slot 2025-11-10 → ✅ ELEGIBLE
Slot 2026-06-05 → ❌ NO ELEGIBLE (después de fin)
```

### Condición 4: Día de Semana Permitido

```python
if profesor.dias_semana_permitidos:
    slot.fecha.weekday() in profesor.dias_semana_permitidos
else:
    True  # Sin restricción
```

**Ejemplo:**
```
Profesor: dias_semana_permitidos=[0, 2, 4]  # L, X, V

Slot Lunes    (weekday=0) → ✅ ELEGIBLE
Slot Martes   (weekday=1) → ❌ NO ELEGIBLE
Slot Miércoles (weekday=2) → ✅ ELEGIBLE
```

### Condición 5: Sin Guardia Previa Mismo Día

```python
if exists guardia where:
    guardia.profesor_id == profesor.id
    AND guardia.fecha == slot.fecha
then:
    NO_ELEGIBLE
else:
    ELEGIBLE
```

**Excepción:** En niveles de relajación altos (nivel 3+), se puede permitir.

### Condición 6: Slot No Ocupado

```python
# Verificar que no exista guardia para este slot específico
if exists guardia where:
    guardia.fecha == slot.fecha
    AND guardia.turno == slot.turno
    AND guardia.recreo == slot.recreo_id
    AND guardia.zona_id == slot.zona_id
then:
    SLOT_OCUPADO
else:
    SLOT_LIBRE
```

### Condición 7: No Exceder Cuota (Opcional)

```python
if respetar_cuotas:
    if asignadas[profesor] < cuota_ideal[profesor]:
        ELEGIBLE
    else:
        NO_ELEGIBLE
else:
    ELEGIBLE  # Ignorar cuota
```

**Uso:**
- **Fase 2.1 (Pre-asignación):** `respetar_cuotas=False` (garantizar participación)
- **Fase 2.2 (Asignación masiva):** `respetar_cuotas=True` (no exceder cuotas)
- **Fases 3-7 (Relajación):** Depende del nivel

### Condición 8: Sin Ausencia Activa

```python
if exists ausencia where:
    ausencia.profesor_id == profesor.id
    AND ausencia.activa == True
    AND ausencia.fecha_inicio <= slot.fecha <= ausencia.fecha_fin
then:
    NO_ELEGIBLE
else:
    ELEGIBLE
```

---

## 🔄 ALGORITMO DE ASIGNACIÓN

### Fase 0: Pre-análisis de Elegibilidad (0% - 30%)

**Objetivo:** Identificar profesores bloqueados y redistribuir sus cuotas.

```python
# 1. Simular slots (sin guardar en BD)
slots = _build_slots(session, config)

# 2. Calcular matriz de elegibilidad
matriz_elegibilidad = {}
for profesor in profesores:
    slots_compatibles = 0
    for slot in slots:
        if es_elegible(profesor, slot, ignorar_asignaciones=True):
            slots_compatibles += 1
    
    matriz_elegibilidad[profesor.id] = slots_compatibles

# 3. Identificar profesores sin elegibilidad
profesores_bloqueados = [
    p for p in profesores 
    if matriz_elegibilidad[p.id] == 0 and cuotas_ideales[p.id] > 0
]

# 4. Redistribuir cuotas de bloqueados
if profesores_bloqueados:
    cuotas_perdidas = sum(cuotas_ideales[p.id] for p in profesores_bloqueados)
    profesores_elegibles = [
        p for p in profesores 
        if matriz_elegibilidad[p.id] > 0
    ]
    
    suma_participacion_elegibles = sum(
        participacion[p.id] for p in profesores_elegibles
    )
    
    for profesor in profesores_elegibles:
        proporcion = participacion[profesor.id] / suma_participacion_elegibles
        cuotas_ideales[profesor.id] += int(cuotas_perdidas * proporcion)
    
    # Poner cuota = 0 a bloqueados
    for profesor in profesores_bloqueados:
        cuotas_ideales[profesor.id] = 0
```

**Output:**
- `cuotas_ideales` ajustadas (bloqueados = 0, elegibles aumentadas)
- `matriz_elegibilidad[prof_id]` = número de slots compatibles

---

### Fase 1: Ordenamiento Óptimo de Slots (30% - 35%)

**Objetivo:** Ordenar slots para facilitar asignación eficiente.

```python
slots_ordenados = sorted(
    slots,
    key=lambda s: (s.fecha, s.turno, s.recreo_id, s.zona_id)
)
```

**Criterios de ordenamiento:**
1. **Fecha** (ascendente): Asignar primero fechas tempranas
2. **Turno** (mañana < tarde): Priorizar mañanas
3. **Recreo ID** (ascendente): Orden natural de recreos
4. **Zona ID** (ascendente): Orden natural de zonas

**Razón:** Asignación cronológica facilita continuidad y permite detectar problemas temprano.

---

### Fase 2.1: Pre-asignación Equitativa por Rondas (35% - 45%)

**Objetivo:** Garantizar que TODOS los profesores elegibles reciban guardias de forma equitativa.

**Algoritmo:**

```python
profesores_prioritarios = sorted(profesores_con_cuota, key=lambda p: p.id)
max_rondas = max(cuotas_ideales.values())

for ronda in range(1, max_rondas + 1):
    for profesor in profesores_prioritarios:
        # ¿Ya alcanzó su cuota?
        if asignadas[profesor] >= cuotas_ideales[profesor]:
            continue
        
        # ¿Ya tiene suficientes para esta ronda?
        if asignadas[profesor] >= ronda:
            continue
        
        # Buscar primer slot compatible
        for slot in slots_ordenados:
            if slot_ocupado(slot):
                continue
            
            if es_elegible(profesor, slot, respetar_cuotas=False):
                asignar_guardia(profesor, slot)
                break  # Pasar al siguiente profesor
```

**Características clave:**
- ✅ **Orden determinista** (por ID, no aleatorio)
- ✅ **Rondas progresivas** (1 a todos antes que 2 a cualquiera)
- ✅ **Sin límite de cuota** en pre-asignación (respetar_cuotas=False)
- ✅ **Equidad garantizada** desde el inicio

**Ejemplo:**
```
Ronda 1:
  Profesor A (cuota=3): 0→1 guardia
  Profesor B (cuota=3): 0→1 guardia
  Profesor C (cuota=2): 0→1 guardia

Ronda 2:
  Profesor A: 1→2 guardias
  Profesor B: 1→2 guardias
  Profesor C: 1→2 guardias (alcanzó cuota)

Ronda 3:
  Profesor A: 2→3 guardias (alcanzó cuota)
  Profesor B: 2→3 guardias (alcanzó cuota)
  Profesor C: 2 guardias (ya alcanzó, skip)
```

---

### Fase 2.2: Asignación Masiva con Scoring Equitativo (45% - 60%)

**Objetivo:** Completar asignación respetando cuotas y optimizando criterios secundarios.

```python
for slot in slots_ordenados:
    if slot_ocupado(slot):
        continue
    
    # Obtener profesores elegibles
    elegibles = obtener_elegibles(
        slot, 
        respetar_cuotas=True  # ← Respetar cuotas ahora
    )
    
    if not elegibles:
        slots_sin_cubrir.append(slot)
        continue
    
    # Seleccionar mejor profesor
    elegido = seleccionar_profesor_optimizado(
        elegibles, 
        slot, 
        asignadas, 
        cuotas_ideales
    )
    
    asignar_guardia(elegido, slot)
```

**Función de Scoring (v2.9 - EQUITATIVA):**

```python
def seleccionar_profesor_optimizado(elegibles, slot, asignadas, cuotas_ideales):
    def score(profesor):
        # 1. DÉFICIT ABSOLUTO (más importante)
        cuota_ideal = cuotas_ideales[profesor.id]
        deficit = cuota_ideal - asignadas[profesor.id]
        
        # 2. ZONA PREFERIDA (secundario)
        if zona_preferida[profesor.id] == slot.zona_id:
            s_zona = 100
        elif zona_preferida[profesor.id] is None:
            s_zona = 0
        else:
            s_zona = -50
        
        # 3. DÍAS SIN GUARDIA (terciario)
        if ultimo_dia[profesor.id]:
            dias_sin_guardia = (slot.fecha - ultimo_dia[profesor.id]).days
        else:
            dias_sin_guardia = 9999  # Nunca ha tenido
        
        # 4. DESEMPATE DETERMINISTA (ID menor = prioridad)
        desempate = -profesor.id
        
        return (deficit, s_zona, dias_sin_guardia, desempate)
    
    return max(elegibles, key=score)
```

**Orden de prioridad:**
1. **Déficit** (DESC): Quien más necesita guardias
2. **Zona preferida** (DESC): 100 > 0 > -50
3. **Días sin guardia** (DESC): Más olvidado = más prioridad
4. **ID profesor** (ASC): Desempate reproducible

**Cambios respecto a versión anterior:**
- ❌ **Eliminado:** `factor_random` (causaba inequidad)
- ❌ **Eliminado:** Penalización × 100 por exceso (bloqueaba profesores)
- ❌ **Eliminado:** Bonus por horas (discriminaba parciales)
- ✅ **Añadido:** Desempate por ID (determinista)

---

### Fase 3: CSP con Forward Checking (60% - 70%)

**Objetivo:** Asignar slots críticos que quedaron sin cubrir usando búsqueda con restricciones.

```python
slots_criticos = [s for s in slots if not asignado(s)]

for slot in slots_criticos:
    # Nivel 1: Relajar cuotas +10%
    cuotas_relajadas = {p: cuota * 1.1 for p, cuota in cuotas_ideales.items()}
    
    elegibles = obtener_elegibles(slot, cuotas=cuotas_relajadas)
    
    if elegibles:
        # Forward checking: verificar que no bloquea slots futuros
        for candidato in elegibles:
            if no_bloquea_futuros(candidato, slot):
                asignar_guardia(candidato, slot)
                break
```

**Relajaciones progresivas:**
```python
Nivel 1: cuotas × 1.10   (permitir +10%)
Nivel 2: cuotas × 1.25   (permitir +25%)
Nivel 3: ignorar_zonas = True
Nivel 4: permitir_multiples_por_dia = True
Nivel 5: cuotas × 2.0    (permitir doble)
```

---

### Fase 4: Simulated Annealing (70% - 75%)

**Objetivo:** Optimizar distribución global mediante intercambios inteligentes.

```python
temperatura = 100.0
enfriamiento = 0.95
mejor_energia = calcular_energia(asignadas, cuotas_ideales)

while temperatura > 0.1:
    # Seleccionar dos profesores con guardias
    prof_a, prof_b = seleccionar_aleatorios()
    
    # Seleccionar una guardia de cada uno
    guardia_a = seleccionar_guardia(prof_a)
    guardia_b = seleccionar_guardia(prof_b)
    
    # Verificar si swap es válido (elegibilidad cruzada)
    if es_elegible(prof_a, slot_b) and es_elegible(prof_b, slot_a):
        # Calcular cambio de energía
        energia_antes = calcular_energia(asignadas, cuotas_ideales)
        
        realizar_swap(guardia_a, guardia_b)
        
        energia_despues = calcular_energia(asignadas, cuotas_ideales)
        delta = energia_despues - energia_antes
        
        # Criterio de Metropolis
        if delta < 0 or random.random() < exp(-delta / temperatura):
            # Aceptar swap
            mejor_energia = min(mejor_energia, energia_despues)
        else:
            # Rechazar, deshacer swap
            deshacer_swap(guardia_a, guardia_b)
    
    temperatura *= enfriamiento
```

**Función de energía:**
```python
def calcular_energia(asignadas, cuotas_ideales):
    return sum(
        abs(asignadas[p] - cuotas_ideales[p]) 
        for p in profesores
    )
```

**Parámetros:**
- Temperatura inicial: 100.0
- Enfriamiento: 0.95 (cada iteración)
- Criterio parada: temperatura < 0.1
- Swaps intentados: ~1000-5000

---

### Fase 5: Hungarian Algorithm + Completitud (75% - 85%)

**Objetivo:** Garantizar 100% cobertura asignando profesores óptimos a slots restantes.

```python
slots_sin_asignar = [s for s in slots if not asignado(s)]

# Crear matriz de costos (profesor × slot)
costos = []
for slot in slots_sin_asignar:
    fila = []
    for profesor in profesores:
        if es_elegible(profesor, slot, respetar_cuotas=False):
            # Costo = desviación de cuota + penalización
            deficit = cuotas_ideales[profesor] - asignadas[profesor]
            costo = -deficit  # Negativo porque queremos maximizar déficit
        else:
            costo = INFINITO  # Inelegible
        fila.append(costo)
    costos.append(fila)

# Resolver asignación óptima
asignacion = hungarian_algorithm(costos)

# Aplicar asignación
for slot_idx, prof_idx in asignacion:
    asignar_guardia(profesores[prof_idx], slots_sin_asignar[slot_idx])
```

---

### Fase 6: Validación y Corrección de Anomalías (85% - 95%)

**Objetivo:** Detectar y corregir problemas en la asignación final.

```python
# 1. Detectar duplicados
duplicados = detectar_guardias_duplicadas()
for dup in duplicados:
    eliminar_guardia(dup)

# 2. Detectar profesores sin guardias (con cuota > 0)
sin_guardias = [
    p for p in profesores 
    if asignadas[p] == 0 and cuotas_ideales[p] > 0
]

# 3. Intentar asignar mediante swaps forzados
for profesor in sin_guardias:
    # Buscar slot que tenga profesor con exceso
    for slot in slots:
        prof_actual = slot.profesor
        if asignadas[prof_actual] > cuotas_ideales[prof_actual]:
            if es_elegible(profesor, slot):
                # Swap forzado
                reasignar_guardia(slot, nuevo_profesor=profesor)
                break
```

---

### Fase 7: Pasadas Múltiples Progresivas (95% - 100%)

**Objetivo:** Refinamiento final con múltiples pasadas específicas.

```python
# Pasada 1: Profesores sin guardias
profesores_sin = [p for p in profesores if asignadas[p] == 0]
for profesor in profesores_sin:
    asignar_mejor_slot_disponible(profesor)

# Pasada 2: Profesores con déficit >20%
profesores_deficit = [
    p for p in profesores 
    if asignadas[p] < cuotas_ideales[p] * 0.8
]
for profesor in profesores_deficit:
    asignar_slots_faltantes(profesor)

# Pasada 3: Cualquier profesor elegible para slots vacíos
slots_vacios = [s for s in slots if not asignado(s)]
for slot in slots_vacios:
    asignar_cualquier_elegible(slot)

# Pasada 4: Swaps de equilibrio
realizar_swaps_equilibrio()
```

---

## 📐 EJEMPLOS NUMÉRICOS

### Ejemplo 1: Profesor Básico (Mañana, Tutor, 30h)

**Configuración:**
```
- Curso: 199 días lectivos
- Recreos: 2 mañana, 2 tarde (4 total)
- Zonas: 4 (todas activas todo el curso)
- Slots totales: 199 × 4 × 4 = 3,184
- Ajuste tutores: 1.0
- Ajuste no tutores: 2.0
```

**Profesor:**
```
- Turno: mañana
- Horas: 30.0
- Tutor: True
- Sin restricciones de fechas ni recreos
```

**Cálculo:**

1. **Factor turno:**
   ```
   recreos_manana / recreos_totales = 2 / 4 = 0.5
   ```

2. **Factor horas:**
   ```
   30.0 / 30.0 = 1.0
   ```

3. **Factor tutoría:**
   ```
   ajuste_tutores = 1.0
   ```

4. **Proporción tiempo:**
   ```
   199 / 199 = 1.0
   ```

5. **Participación:**
   ```
   0.5 × 1.0 × 1.0 × 1.0 = 0.5
   ```

6. **Cuota (asumiendo 75 profesores, suma_ponderada=100):**
   ```
   (0.5 / 100) × 3,184 = 15.92 ≈ 16 guardias
   ```

---

### Ejemplo 2: Profesor NO Tutor (Mañana, 30h)

**Misma configuración, pero:**
```
- Tutor: False
```

**Cálculo:**

1-2. Igual que Ejemplo 1

3. **Factor tutoría:**
   ```
   ajuste_no_tutores = 2.0
   ```

4. **Proporción tiempo:** 1.0

5. **Participación:**
   ```
   0.5 × 1.0 × 2.0 × 1.0 = 1.0
   ```

6. **Cuota:**
   ```
   (1.0 / 100) × 3,184 = 31.84 ≈ 32 guardias
   ```

**Relación:** NO tutor hace **2× guardias** que tutor (32 vs 16) ✅

---

### Ejemplo 3: Profesor Parcial (Mañana, Tutor, 18h)

**Profesor:**
```
- Turno: mañana
- Horas: 18.0
- Tutor: True
```

**Cálculo:**

1. **Factor turno:** 0.5

2. **Factor horas:**
   ```
   18.0 / 30.0 = 0.6
   ```

3. **Factor tutoría:** 1.0

4. **Proporción tiempo:** 1.0

5. **Participación:**
   ```
   0.5 × 0.6 × 1.0 × 1.0 = 0.3
   ```

6. **Cuota:**
   ```
   (0.3 / 100) × 3,184 = 9.55 ≈ 10 guardias
   ```

**Relación con Ejemplo 1:**
```
10 / 16 = 0.625 ≈ 18/30 ✅
```

---

### Ejemplo 4: Profesor Mixto (30h, NO Tutor, 15h mañana + 15h tarde)

**Profesor:**
```
- Turno: mixto
- Horas: 30.0 (15 mañana + 15 tarde)
- Tutor: False
```

**Cálculo:**

1. **Factor turno (mixto ponderado):**
   ```
   factor_manana = (15/30) × (2/4) = 0.5 × 0.5 = 0.25
   factor_tarde = (15/30) × (2/4) = 0.5 × 0.5 = 0.25
   factor_turno = 0.25 + 0.25 = 0.5
   ```

2. **Factor horas:** 1.0

3. **Factor tutoría:** 2.0

4. **Proporción tiempo:** 1.0

5. **Participación:**
   ```
   0.5 × 1.0 × 2.0 × 1.0 = 1.0
   ```

6. **Cuota:**
   ```
   (1.0 / 100) × 3,184 = 31.84 ≈ 32 guardias
   ```

**Mismo que Ejemplo 2 (NO tutor mañana 30h)** ✅

---

### Ejemplo 5: Profesor con Fechas Restringidas

**Profesor:**
```
- Turno: mañana
- Horas: 30.0
- Tutor: True
- Fecha inicio: 2025-10-01
- Fecha fin: 2026-05-31
```

**Cálculo:**

1. **Factor turno:** 0.5

2. **Factor horas:** 1.0

3. **Factor tutoría:** 1.0

4. **Proporción tiempo:**
   ```
   # Días lectivos del profesor en su rango
   dias_disponibles = 150  (aproximado, L-V entre oct y may)
   dias_totales = 199
   
   proporcion_tiempo = 150 / 199 = 0.754
   ```

5. **Participación:**
   ```
   0.5 × 1.0 × 1.0 × 0.754 = 0.377
   ```

6. **Cuota:**
   ```
   (0.377 / 100) × 3,184 = 12.0 guardias
   ```

**Relación con Ejemplo 1:**
```
12 / 16 = 0.75 ≈ 150/199 ✅
```

---

## ⚠️ CASOS ESPECIALES

### Caso 1: Profesor Sin Elegibilidad

**Situación:**
```
Profesor: recreos_permitidos = [1, 2]
Configuración: solo tiene recreos [3, 4]
```

**Resultado:**
```
matriz_elegibilidad[profesor.id] = 0
cuota_ideal[profesor.id] = 0  (tras Fase 0)
asignadas[profesor.id] = 0
```

**Acción:** Advertencia en logs, cuota redistribuida a otros profesores.

---

### Caso 2: Zonas con Fechas de Activación

**Situación:**
```
Zona 1: fecha_inicio = None, fecha_fin = None  → 199 días
Zona 2: fecha_inicio = 2025-10-01             → 170 días
Zona 3: fecha_fin = 2026-05-31                → 180 días
Zona 4: 2025-10-01 a 2026-05-31               → 150 días
```

**Cálculo de slots:**
```
Slots totales != 199 × 4 recreos × 4 zonas

Slots reales = sum(días_activos_zona × recreos_compatible_zona)
             = (199×4) + (170×4) + (180×4) + (150×4)
             = 796 + 680 + 720 + 600
             = 2,796 slots (NO 3,184)
```

**Impacto:** Cuotas se calculan sobre 2,796, no 3,184. Profesores reciben **menos guardias** de lo esperado.

---

### Caso 3: Profesores con Días Semana Restringidos

**Situación:**
```
Profesor: dias_semana_permitidos = [0, 2, 4]  # L, X, V
```

**Impacto en elegibilidad:**
```
Días lectivos totales: 199
Días elegibles (L,X,V): ~120 (60%)

matriz_elegibilidad reducida en ~40%
```

**Cuota NO se ajusta automáticamente** por días semana (solo por fechas inicio/fin).

**Consecuencia:** Profesor puede NO alcanzar su cuota si sus días compatibles se agotan.

---

### Caso 4: Múltiples Profesores Mismo Grupo

**Situación:**
```
24 profesores: turno=mañana, tutor=True, horas=30
```

**Objetivo v2.9:**
```
TODOS deben tener guardias_A == guardias_B (±1)
```

**Garantía del algoritmo:**
1. Pre-asignación por rondas: Todos empiezan igual
2. Scoring determinista: Orden reproducible
3. Sin factor aleatorio: Sin dispersión

**Resultado esperado:**
```
Cuota ideal = 23.5

Redondeo:
- 12 profesores: 24 guardias
- 12 profesores: 23 guardias

Rango = 24 - 23 = 1 ✅ PERFECTO
```

---

### Caso 5: Ausencias Activas

**Situación:**
```
Profesor: ausencia del 2025-11-01 al 2025-11-15 (activa=True)
```

**Impacto:**
```
Slots en ese rango: NO ELEGIBLE
Cuota ideal: NO se ajusta automáticamente

Consecuencia: Puede quedar con déficit
```

**Solución (manual):**
```
Opción 1: Ajustar fecha_fin_guardias del profesor
Opción 2: Regenerar guardias excluyendo el período
Opción 3: Reasignar manualmente las guardias afectadas
```

---

### Caso 6: Slots Totales < Suma de Cuotas Ideales

**Situación (error de configuración):**
```
Slots totales: 1,000
Suma cuotas ideales: 1,050
```

**Causa:** Error en ajustes de tutoría o cálculo.

**Síntoma:**
```
Algunos profesores NO alcanzarán su cuota ideal
```

**Validación:**
```python
assert sum(cuotas_ideales.values()) == slots_totales, \
    "Error matemático: suma de cuotas != slots totales"
```

**Prevención:** El algoritmo de redondeo (Paso 5) garantiza que la suma coincida.

---

## 📝 REGISTRO DE CAMBIOS

### Versión 2.9 (30 octubre 2025)

**Cambios en Scoring:**
- ✅ Eliminado `factor_random` de `_seleccionar_profesor_optimizado()`
- ✅ Eliminada penalización × 100 por exceder cuota ideal
- ✅ Añadido desempate determinista por ID de profesor
- ✅ Simplificado cálculo de déficit (sin bonus por horas)

**Cambios en Pre-asignación:**
- ✅ Reescrita Fase 2.1 con asignación por rondas equitativas
- ✅ Orden determinista (por ID, no por elegibilidad)
- ✅ Garantía: 1 guardia a TODOS antes que 2 a CUALQUIERA

**Cambios en Cuotas Dinámicas:**
- ✅ Eliminado ajuste dinámico de cuotas durante asignación
- ✅ Cuotas ideales son FIJAS durante todo el proceso

**Impacto:**
```
ANTES: Rango 4-27 guardias entre profesores idénticos
AHORA: Rango ≤ 1 guardia (equidad perfecta)
```

---

### Versión 2.8 (anterior)

**Características:**
- Scoring con 6 factores (incluido factor_random)
- Penalización × 100 por exceder cuota
- Pre-asignación basada en elegibilidad (menos elegibles primero)
- Cuotas dinámicas ajustables durante asignación

**Problemas identificados:**
- ❌ Inequidad brutal (rangos 4-27)
- ❌ Algunos profesores sin guardias
- ❌ Distribución impredecible

---

## 🔧 MANTENIMIENTO Y EVOLUCIÓN

### Antes de Modificar el Algoritmo

**✅ HACER:**
1. Documentar el cambio en este archivo (sección "Registro de Cambios")
2. Ejecutar `scripts/validar_equidad.py` ANTES de implementar
3. Crear tests unitarios para el cambio
4. Validar con datos de producción reales
5. Ejecutar `scripts/validar_equidad.py` DESPUÉS de implementar
6. Verificar que rango ≤ 1 en todos los grupos

**❌ NO HACER:**
1. Introducir aleatoriedad (rompe equidad)
2. Ajustar cuotas dinámicamente (rompe equidad entre iguales)
3. Dar prioridad por factores no contemplados en cuota ideal
4. Modificar sin actualizar este documento

### Validación de Cambios

**Script de validación:**
```bash
python3 scripts/validar_equidad.py \
    --db data/users/XXX/guardias_patio.db \
    --verbose
```

**Criterios de aceptación:**
```
✅ Cobertura: 100% (todos los slots asignados)
✅ Participación: ≥95% (profesores con cuota > 0 tienen guardias)
✅ Equidad: Rango ≤ 1 en TODOS los grupos
✅ Suma: sum(guardias) == slots_totales
```

### Ejemplos de Cambios Permitidos

**✅ PERMITIDO - Ajustar factor de tutoría:**
```python
# En configuracion
ajuste_tutores = 0.8      # De 1.0 a 0.8 (-20%)
ajuste_no_tutores = 1.6   # De 2.0 a 1.6 (ratio = 2.0 se mantiene)
```
**Impacto:** Cambia cuotas absolutas, pero mantiene equidad intra-grupo.

**✅ PERMITIDO - Añadir criterio de scoring secundario:**
```python
# En _seleccionar_profesor_optimizado()
def score(profesor):
    # ... criterios existentes ...
    
    # NUEVO: Priorizar veteranos en caso de empate
    antiguedad = -profesor.fecha_incorporacion.year  # Menor año = más antiguo
    
    return (deficit, s_zona, dias_sin_guardia, antiguedad, desempate)
```
**Condición:** Solo usar para desempate entre profesores con mismo déficit.

**❌ PROHIBIDO - Ajuste dinámico de cuotas:**
```python
# NO HACER ESTO
if asignadas[profesor] >= cuotas[profesor]:
    cuotas[profesor] *= 1.1  # ← ROMPE EQUIDAD
```

**❌ PROHIBIDO - Factor aleatorio:**
```python
# NO HACER ESTO
score = (deficit, random.random())  # ← ROMPE EQUIDAD
```

---

## 📚 REFERENCIAS

### Archivos de Código

1. **`src/services/calculador_guardias.py`**
   - `calcular_guardias_por_profesor()`: Función principal de cálculo de cuotas
   - `calcular_distribucion_cruda()`: Cálculo de participación por profesor
   - `ajustar_redondeo()`: Algoritmo de redondeo justo
   - `listar_dias_lectivos()`: Cálculo de días lectivos con festivos

2. **`src/services/asignador_guardias.py`**
   - `generar_calendario_guardias()`: Función principal de asignación
   - `_seleccionar_profesor_optimizado()`: Scoring equitativo (v2.9)
   - `_build_slots()`: Construcción de slots con fechas de zonas
   - `_obtener_profesores_elegibles()`: Verificación de elegibilidad

3. **`src/models/models.py`**
   - Clase `Profesor`: Definición de atributos
   - Clase `Configuracion`: Parámetros del curso
   - Clase `Zona`: Configuración de zonas con fechas
   - Clase `Guardia`: Registro de asignaciones

### Scripts de Validación

1. **`scripts/validar_equidad.py`**
   - Validación automática de equidad
   - Agrupamiento por (turno, tutoría, horas)
   - Verificación de rango ≤ 1

2. **`scripts/diagnostico_guardias.py`**
   - Diagnóstico exhaustivo del sistema
   - Análisis de elegibilidad
   - Detección de problemas de configuración

### Documentación

1. **`documentacion/tecnico/ESPECIFICACION_CALCULO_GUARDIAS.md`** (este archivo)
   - Especificación técnica completa
   - Referencia para modificaciones

2. **`documentacion/versiones/CORRECCION_EQUIDAD_v2.9.md`**
   - Changelog detallado v2.9
   - Comparativa antes/después
   - Ejemplos de inequidad corregida

3. **`documentacion/tecnico/ALGORITMO_PASADA_6.md`**
   - Detalles de Fases 3-7
   - Técnicas avanzadas (CSP, SA, Hungarian)

---

## ✅ CHECKLIST DE VERIFICACIÓN

Usa este checklist antes de cualquier cambio en el algoritmo:

### Antes de Modificar

- [ ] He leído completamente este documento
- [ ] Entiendo la Regla de Oro de equidad
- [ ] He identificado qué variables/funciones afecta mi cambio
- [ ] He documentado el cambio en "Registro de Cambios"
- [ ] He ejecutado validador con datos actuales (baseline)

### Durante la Implementación

- [ ] El cambio no introduce aleatoriedad
- [ ] El cambio no ajusta cuotas dinámicamente
- [ ] He añadido logging para el cambio
- [ ] He actualizado docstrings afectados
- [ ] El código sigue el estilo del proyecto

### Después de Implementar

- [ ] He ejecutado validador con datos de prueba
- [ ] Rango ≤ 1 en todos los grupos de prueba
- [ ] He ejecutado validador con datos de producción
- [ ] Rango ≤ 1 en todos los grupos de producción
- [ ] Cobertura = 100%
- [ ] Participación ≥ 95%
- [ ] He actualizado este documento si es necesario
- [ ] He creado/actualizado tests unitarios

---

**Mantenido por:** Equipo de Desarrollo  
**Última actualización:** 30 octubre 2025  
**Próxima revisión:** Ante cualquier cambio en el algoritmo
