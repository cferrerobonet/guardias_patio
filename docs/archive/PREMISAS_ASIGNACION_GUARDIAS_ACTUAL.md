# Premisas de Cálculo y Asignación de Guardias - INFORME EXACTO

**Algoritmo Actual**: v3.1 Simple Determinista (Mejorado 14/11/2025)  
**Archivos Analizados**:
- `src/services/asignador_guardias_v3_simple.py` (860 líneas)
- `src/services/calculador_guardias.py` (585 líneas)
- `src/services/validador_guardias.py` (nuevo)

**Estado**: ✅ Código analizado directamente (no inferencias)

---

## 📊 CLASIFICACIÓN POR PRIORIDAD

### 🔴 **PRIORIDAD MÁXIMA** - Restricciones Inviolables

#### 1. **Ausencias del Profesor**
- **Descripción**: Un profesor NO puede tener guardia en fechas donde está ausente
- **Código**: `_profesor_ausente()` líneas 87-100
- **Validación**: En cada slot antes de asignar
- **Cumplimiento**: ✅ 100% - Última auditoría: 0 guardias durante ausencias

```python
def _profesor_ausente(session, profesor_id, fecha):
    ausencia = session.query(Ausencia).filter(
        Ausencia.profesor_id == profesor_id,
        Ausencia.fecha_inicio <= fecha,
        Ausencia.fecha_fin >= fecha,
        Ausencia.activa == True
    ).first()
    return ausencia is not None
```

**Orden de evaluación**: 1º (se rechaza inmediatamente si hay ausencia)

---

#### 2. **Fecha de Inicio de Guardias** 
- **Descripción**: Un profesor NO puede tener guardias ANTES de su `fecha_inicio_guardias`
- **Código**: `_cumple_restricciones()` líneas 115-117
- **Campo BD**: `profesores.fecha_inicio_guardias` (DATE, nullable)
- **Cumplimiento**: ⚠️ 31.6% - 13/19 profesores tienen retraso (43-84 días)
- **Causa del incumplimiento**: Priorización insuficiente + competencia por slots

```python
if profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias:
    return False  # RECHAZO INMEDIATO
```

**Orden de evaluación**: 2º (después de ausencias)  
**⚠️ PROBLEMA ACTUAL**: El algoritmo lo valida pero no garantiza asignación temprana

---

#### 3. **Fecha de Fin de Guardias**
- **Descripción**: Un profesor NO puede tener guardias DESPUÉS de su `fecha_fin_guardias`
- **Código**: `_cumple_restricciones()` líneas 119-121
- **Campo BD**: `profesores.fecha_fin_guardias` (DATE, nullable)
- **Cumplimiento**: ✅ N/A - Actualmente ningún profesor tiene fecha_fin configurada

```python
if profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias:
    return False
```

**Orden de evaluación**: 3º

---

#### 4. **Días de la Semana Permitidos**
- **Descripción**: Un profesor solo puede tener guardias en sus días permitidos
- **Código**: `_cumple_restricciones()` líneas 123-135
- **Campo BD**: `profesores.dias_semana_permitidos` (TEXT/JSON)
- **Formato**: Lista `[0,1,2,3,4]` donde 0=Lunes, 6=Domingo
- **Cumplimiento**: ✅ Asumido 100% (sin auditoría específica)

```python
if profesor.dias_semana_permitidos:
    dia_semana = slot.fecha.weekday()
    dias_permitidos = json.loads(profesor.dias_semana_permitidos)
    if dia_semana not in dias_permitidos:
        return False
```

**Parsing**: Triple fallback (JSON → ast.literal_eval → default todos permitidos)  
**Orden de evaluación**: 4º

---

#### 5. **Recreos Permitidos**
- **Descripción**: Un profesor solo puede tener guardias en sus recreos permitidos
- **Código**: `_cumple_restricciones()` líneas 137-173
- **Campo BD**: `profesores.recreos_permitidos` (TEXT/JSON)
- **Formatos soportados**:
  - **Lista simple**: `[1, 2]` → Recreos 1 y 2 todos los días
  - **Diccionario por día**: `{"0": [1, 2], "1": [1, 3]}` → Recreos específicos por día
- **Cumplimiento**: ✅ Asumido 100%

```python
if profesor.recreos_permitidos:
    recreos_perms = json.loads(profesor.recreos_permitidos)
    
    if isinstance(recreos_perms, dict):
        dia_semana = slot.fecha.weekday()
        dia_key = str(dia_semana)
        if dia_key in recreos_perms:
            if slot.recreo_id not in recreos_perms[dia_key]:
                return False
        else:
            return False  # Si no hay config para este día, no permitir
    elif isinstance(recreos_perms, list):
        if slot.recreo_id not in recreos_perms:
            return False
```

**Orden de evaluación**: 5º  
**Nota**: Implementación corregida 01/11/2025 para soportar diccionario por día

---

#### 6. **Restricción de Turno**
- **Descripción**: Un profesor solo puede cubrir guardias de su turno
- **Código**: `_cumple_restricciones()` líneas 175-178
- **Valores posibles**: `"mañana"`, `"tarde"`, `"mixto"`, `"ambos"`
- **Lógica**:
  - `turno="mañana"` → Solo slots de turno mañana
  - `turno="tarde"` → Solo slots de turno tarde
  - `turno="mixto"` o `"ambos"` → Cualquier turno
- **Cumplimiento**: ✅ 100% - Sin violaciones detectadas

```python
if profesor.turno and profesor.turno not in ("ambos", "mixto"):
    if slot.turno != profesor.turno:
        return False
```

**Orden de evaluación**: 6º (último check)

---

#### 7. **Múltiples Guardias por Día** 
- **Descripción**: Un profesor NO puede tener más de 1 guardia en el mismo día
- **Código**: `generar_guardias_v3_simple()` líneas 619-623
- **Cumplimiento**: ❌ **PROBLEMA DETECTADO** - 1 profesor (GONZÁLEZ AZANZA) con 5 días duplicados

```python
fechas_ya_asignadas = {slot.fecha for slot in slots_por_profesor.get(profesor.id, [])}

slots_disponibles = [
    slot for slot in todos_slots
    if slot not in slots_ocupados
    and slot.fecha not in fechas_ya_asignadas  # Evitar múltiples guardias por día
    and _cumple_restricciones(profesor, slot, session)
]
```

**Orden de evaluación**: Durante la asignación (antes de filtrar slots)  
**⚠️ BUG ACTUAL**: La lógica existe pero falla en casos específicos

---

### 🟠 **PRIORIDAD ALTA** - Cálculo de Cuotas

#### 8. **Factor por Turno**
- **Descripción**: La cuota se ajusta según la proporción de recreos disponibles en el turno
- **Código**: `calculador_guardias.py:230-272` `calcular_factor_participacion()`
- **Lógica**:
  ```
  Si turno = "mañana":
      factor = recreos_mañana / recreos_totales
  
  Si turno = "tarde":
      factor = recreos_tarde / recreos_totales
  
  Si turno = "mixto":
      factor_mañana = (horas_mañana / horas_totales) × (recreos_mañana / recreos_totales)
      factor_tarde = (horas_tarde / horas_totales) × (recreos_tarde / recreos_totales)
      factor = factor_mañana + factor_tarde
  ```
- **Ejemplo Real**:
  - 2 recreos mañana, 2 recreos tarde → profesor de mañana: factor = 0.5
  - Profesor mixto 15h mañana + 15h tarde → factor = 0.5 × 0.5 + 0.5 × 0.5 = 0.5

**Peso en cuota final**: 25% (1 de 4 factores multiplicativos)

---

#### 9. **Factor por Horas Contratadas**
- **Descripción**: Profesores con más horas deben tener proporcionalmente más guardias
- **Código**: `calculador_guardias.py:391-393`
- **Referencia**: 30 horas = jornada completa (100%)
- **Fórmula**: `factor_horas = min(horas_contrato / 30.0, 1.0)`
- **Ejemplos**:
  - 30h → 1.0 (100%)
  - 22.5h → 0.75 (75%)
  - 15h → 0.5 (50%)
  - 7.5h → 0.25 (25%)
  - 0.3h (1%) → 0.01 (1%)

**Peso en cuota final**: 25% (1 de 4 factores multiplicativos)

---

#### 10. **Factor de Tutoría**
- **Descripción**: Ajuste en la cuota según si es tutor o no
- **Código**: `calculador_guardias.py:395-399`
- **Configuración**: Campos `config.ajuste_tutores` y `config.ajuste_no_tutores`
- **Valores típicos**:
  - `ajuste_tutores`: 0.9 - 1.1 (reducción o incremento del 10%)
  - `ajuste_no_tutores`: 1.0 (sin ajuste)
- **Fórmula**: 
  ```
  factor_tutoria = config.ajuste_tutores if profesor.tutor else config.ajuste_no_tutores
  ```

**Peso en cuota final**: 25% (1 de 4 factores multiplicativos)

---

#### 11. **Proporción de Tiempo Disponible** 
- **Descripción**: Si un profesor tiene fecha_inicio/fin, su cuota se reduce proporcionalmente
- **Código**: `calculador_guardias.py:401-432`
- **Lógica**:
  ```
  inicio_efectivo = fecha_inicio_guardias OR fecha_inicio_curso
  fin_efectivo = fecha_fin_guardias OR fecha_fin_curso
  
  dias_disponibles = COUNT(dias_lectivos WHERE dia BETWEEN inicio_efectivo AND fin_efectivo)
  proporcion_tiempo = dias_disponibles / total_dias_lectivos
  ```
- **Ejemplo Real** (Auditoría actual):
  - Curso: 169 días lectivos (08/09/2025 - 05/06/2026)
  - Profesor con fecha_inicio=08/09/2025: 169/169 = 100%
  - Profesor hipotético con fecha_inicio=01/01/2026: ~100/169 = 59%

**Peso en cuota final**: 25% (1 de 4 factores multiplicativos)  
**⚠️ IMPORTANTE**: Este ajuste es CORRECTO pero el algoritmo de asignación no prioriza fechas tempranas

---

#### **Fórmula Final de Cuota**

```python
participacion_ponderada = factor_turno × factor_horas × factor_tutoria × proporcion_tiempo

cuota_profesor = (participacion_ponderada / suma_total_participaciones) × slots_totales
```

**Redondeo**: Por defecto se redondea al entero más cercano  
**Ajuste fino**: Si suma de cuotas ≠ slots_totales, se distribuyen las diferencias

---

### 🟡 **PRIORIDAD MEDIA** - Orden de Asignación

#### 12. **Priorización por Urgencia (fecha_inicio)** ⭐ NUEVO v3.1
- **Descripción**: Profesores con fecha_inicio y menos días disponibles se asignan PRIMERO
- **Código**: `_calcular_prioridad_profesor()` líneas 241-278
- **Fórmula de prioridad** (menor = más prioritario):
  ```python
  Si tiene fecha_inicio:
      dias_disponibles = fecha_fin_curso - fecha_inicio_guardias
      proporcion_tiempo = dias_disponibles / dias_lectivos_totales
      factor_urgencia = proporcion_tiempo × 1000  # Rango 0-1000
  Sino:
      factor_urgencia = 2000  # Baja prioridad
  
  ratio_restriccion = cuota / slots_posibles
  prioridad = factor_urgencia + (1.0 - ratio_restriccion) × 1000 + profesor.id × 0.01
  ```

**Ejemplos de Prioridad**:
- Profesor con fecha_inicio y 50% tiempo disponible: ~500 (ALTA PRIORIDAD)
- Profesor con fecha_inicio y 100% tiempo disponible: ~1000 (MEDIA PRIORIDAD)
- Profesor sin fecha_inicio: ~2000 (BAJA PRIORIDAD)

**Implementación**: 14/11/2025  
**Efectividad actual**: ⚠️ **PARCIAL** - Mejora el cumplimiento pero insuficiente (31.6% vs 15.8% anterior)

---

#### 13. **Priorización por Restricciones**
- **Descripción**: Profesores con menos slots disponibles (más restrictivos) se asignan antes
- **Código**: Componente de `prioridad` en línea 274
- **Lógica**: 
  ```
  ratio_restriccion = cuota / slots_posibles
  
  Contribución a prioridad = (1.0 - ratio_restriccion) × 1000
  ```
- **Ejemplo**:
  - Profesor A: cuota=30, slots_posibles=100 → ratio=0.3 → contribución=700
  - Profesor B: cuota=30, slots_posibles=500 → ratio=0.06 → contribución=940
  - **Resultado**: Profesor A se asigna ANTES (más restrictivo)

**Peso**: Secundario tras urgencia por fecha_inicio

---

### 🟢 **PRIORIDAD BAJA** - Optimizaciones de Asignación

#### 14. **Ordenamiento de Slots - Consistencia de Zona**
- **Descripción**: Priorizar asignar siempre la misma zona al mismo profesor
- **Código**: `_ordenar_slots_para_profesor()` líneas 288-425
- **Lógica**:
  ```
  zona_objetivo = zona_más_frecuente_en_guardias_previas OR zona_preferida OR zona_más_común
  
  Peso zona = 0 si zona == zona_objetivo, sino 100000
  ```
- **Objetivo**: Consistencia y familiaridad con la zona

**Orden en clave de ordenamiento**: 1º (máxima prioridad en sorting)

---

#### 15. **Ordenamiento de Slots - Consistencia de Recreo**
- **Descripción**: Priorizar asignar siempre el mismo recreo al mismo profesor
- **Código**: `_ordenar_slots_para_profesor()` líneas 288-425
- **Lógica**:
  ```
  recreo_objetivo = recreo_más_frecuente_previo OR recreo_mínimo_disponible
  
  Peso recreo = 0 si recreo == recreo_objetivo, sino 10000
  ```

**Orden en clave de ordenamiento**: 2º

---

#### 16. **Ordenamiento de Slots - Fechas Agrupadas** ⭐ MEJORADO v1.3
- **Descripción**: Agrupar guardias en fechas cercanas/consecutivas para liberar períodos
- **Código**: `_ordenar_slots_para_profesor()` líneas 288-425
- **Objetivo**: Que el profesor complete sus guardias lo antes posible
- **Lógica**:
  ```
  fecha_base = última_guardia_asignada OR fecha_mínima_disponible
  
  distancia_dias = abs((slot.fecha - fecha_base).days)
  Peso distancia = distancia_dias  # Menor distancia = mejor
  ```

**Orden en clave de ordenamiento**: 3º  
**⚠️ LIMITACIÓN**: Solo optimiza dentro de slots disponibles, no garantiza fechas tempranas

---

#### 17. **Ordenamiento de Slots - Día de Semana Consistente**
- **Descripción**: Preferencia por asignar el mismo día de la semana
- **Código**: `_ordenar_slots_para_profesor()` líneas 288-425
- **Lógica**:
  ```
  dia_objetivo = dia_más_frecuente_previo OR dia_con_más_slots
  
  Peso dia = 0 si dia_semana == dia_objetivo, sino 1000
  ```

**Orden en clave de ordenamiento**: 4º (menor prioridad que fechas agrupadas)

---

#### 18. **Ordenamiento de Slots - Orden Cronológico**
- **Descripción**: Desempate por fecha cronológica ascendente
- **Código**: `_ordenar_slots_para_profesor()` líneas 288-425

**Orden en clave de ordenamiento**: 5º (desempate)

---

## 🎯 RESUMEN EJECUTIVO

### **Orden de Evaluación Completo**

**Fase 1: Validación de Restricciones** (Rechazar slots inválidos)
1. Ausencias ✅
2. Fecha inicio guardias ⚠️ (valida pero no prioriza suficiente)
3. Fecha fin guardias ✅
4. Días semana permitidos ✅
5. Recreos permitidos ✅
6. Turno ✅

**Fase 2: Cálculo de Cuota** (Determinar cuántas guardias)
7. Factor turno (25%)
8. Factor horas (25%)
9. Factor tutoría (25%)
10. Proporción tiempo disponible (25%)

**Fase 3: Orden de Asignación** (Quién primero)
11. ⭐ Urgencia por fecha_inicio (nuevo v3.1)
12. Restricciones (más limitado primero)

**Fase 4: Optimización de Slots** (Qué slots asignar)
13. Consistencia zona
14. Consistencia recreo
15. ⭐ Fechas agrupadas (mejorado v1.3)
16. Día semana consistente
17. Orden cronológico
18. Evitar múltiples guardias/día (⚠️ BUG detectado)

---

## 📐 PREMISAS DE COBERTURA Y COMPLETITUD

### ❌ **NO EXISTE: Mínimo de Guardias por Día**
- **Pregunta**: ¿Hay algo que obligue a cubrir `guardias/día = recreos × zonas`?
- **Respuesta**: **NO existe restricción obligatoria**
- **Realidad**: 
  - El algoritmo calcula `slots_totales = días_lectivos × recreos × zonas`
  - Luego **intenta** asignar todos los slots pero **NO garantiza** que todos se cubran
  - Solo **reporta** cuántos slots quedan vacíos
- **Código**: `asignador_guardias_v3_simple.py` líneas 694-730

```python
slots_vacios = total_slots - guardias_asignadas
cobertura = (guardias_asignadas / total_slots * 100)

if slots_vacios > 0:
    logger.warning(f"⚠️ Quedan {slots_vacios} slots sin cubrir")
else:
    logger.info("✓ 100% de cobertura alcanzada")
```

**Comportamiento**: Si no hay profesores suficientes o tienen muchas restricciones, puede haber días con menos guardias de las necesarias. **Solo avisa, no obliga.**

---

### ❌ **NO EXISTE: Cobertura 100% Obligatoria de Slots**
- **Pregunta**: ¿Hay algo que obligue a cubrir todos los slots calculados?
- **Respuesta**: **NO existe restricción obligatoria**
- **Objetivo declarado**: "Garantiza 100% cobertura si es matemáticamente posible" (línea 21)
- **Realidad**: 
  - El algoritmo **aspira** a 100% pero **NO falla** si no lo consigue
  - Solo genera un **WARNING** si quedan slots vacíos
  - La ejecución **continúa normalmente** con cobertura parcial
- **Última Auditoría (14/11/2025)**: 
  - Total slots: 2516
  - Guardias asignadas: 2423
  - Cobertura: **96.3%** (93 slots sin cubrir)
  - Estado: ✅ Sistema aceptó el resultado

**Comportamiento**: El algoritmo hace su "mejor esfuerzo" pero acepta coberturas <100%.

---

### ❌ **NO EXISTE: Cuota Mínima Garantizada por Profesor**
- **Pregunta**: ¿Hay algo que obligue a que cada profesor reciba su cuota calculada?
- **Respuesta**: **NO existe restricción obligatoria**
- **Realidad**:
  - El algoritmo calcula la cuota teórica de cada profesor
  - Luego **intenta** asignar esa cuota exacta
  - Pero **acepta** asignaciones inferiores si no hay slots disponibles
  - Solo genera un **WARNING** si la cuota es incompleta
- **Código**: `asignador_guardias_v3_simple.py` líneas 656-663, 750-790

```python
# Durante la asignación
if asignadas < cuota:
    logger.warning(f"⚠️ {asignadas}/{cuota} guardias (faltan {cuota - asignadas})")
    profesores_incompletos.append((profesor, asignadas, cuota))

# Verificación final
if guardias_asignadas != cuota:
    diferencia = guardias_asignadas - cuota
    if diferencia < 0:
        profesores_con_deficit.append((profesor, guardias_asignadas, cuota, abs(diferencia)))
        logger.warning(f"• {profesor.nombre_completo}: {guardias_asignadas}/{cuota} (faltan {abs(diferencia)})")
```

**Causas de déficit**:
1. Restricciones demasiado estrictas (pocos días/recreos permitidos)
2. Slots compatibles ya ocupados por profesores anteriores
3. Turnos incompatibles con slots disponibles

**Última Auditoría (14/11/2025)**:
- **3 profesores con DÉFICIT total** (0 guardias recibidas de cuota esperada):
  - MARTÍ LUÑO, VICENTE JUAN (turno: tarde, jornada: 75%)
  - MORENO SÁNCHEZ, MARTA (turno: tarde, jornada: 20%)
  - TOMÁS MONTESA, MIGUEL (turno: tarde, jornada: 75%)
- Estado: ⚠️ Sistema generó WARNING pero aceptó el resultado

**Comportamiento**: El algoritmo prioriza la cobertura posible sobre la garantía de cuota individual.

---

## ⚠️ PROBLEMAS ACTUALES DETECTADOS

### 🔴 **Crítico**
1. **Múltiples guardias por día**: 1 profesor afectado (5 días)
2. **3 profesores sin guardias**: Todos turno tarde (❌ incumple completitud)
3. **13/19 con retraso en fecha_inicio**: 43-84 días (mejora insuficiente)
4. **93 slots sin cubrir**: 96.3% cobertura (❌ incumple objetivo 100%)

### 🟠 **Alto**
5. **Desequilibrio >20%**: 63 profesores (94%)
6. **Cumplimiento fecha_inicio**: Solo 31.6% (objetivo: 100%)

### 🟡 **Medio**
7. **Retraso promedio**: 74 días (mejoró desde 136 días, pero insuficiente)

---

**Fecha del Informe**: 14 de noviembre de 2025  
**Basado en**: Análisis directo del código + Auditoría ejecutada hoy  
**Versión Algoritmo**: v3.1 (Mejorado con priorización fecha_inicio)
