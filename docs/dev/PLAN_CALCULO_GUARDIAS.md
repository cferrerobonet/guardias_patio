# 📊 Plan de Cálculo y Asignación de Guardias

## 1. Resumen Ejecutivo

Este documento presenta un **análisis completo** de cómo debería funcionar el sistema de cálculo y asignación de guardias, basándose en el modelo de datos existente y los requisitos del dominio.

### Problemas reportados actuales:
- ❌ Se dejan **días y zonas sin asignar**
- ❌ No se respetan las **prioridades** correctamente
- ❌ Distribución desigual entre profesores equivalentes

---

## 2. Modelo de Datos (Input del Sistema)

### 2.1 Entidades Principales

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CursoEscolar   │     │  Configuracion  │     │      Zona       │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │     │ fecha_inicio    │     │ id              │
│ nombre          │     │ fecha_fin       │     │ nombre_zona     │
│ activo          │     │ recreos_config  │     │ fecha_inicio*   │
│                 │     │ ajuste_tutores  │     │ fecha_fin*      │
│                 │     │ ajuste_no_tutores│    └─────────────────┘
│                 │     │ festivos_auto   │
│                 │     │ dias_no_lectivos│
└─────────────────┘     └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Profesor                               │
├─────────────────────────────────────────────────────────────────┤
│ id, nombre_completo, activo                                     │
│ turno: "mañana" | "tarde" | "mixto" | "completo"               │
│ horas_contrato, porcentaje_jornada                             │
│ tutor: bool                                                     │
│ recreos_permitidos: JSON  (ej: [1,2] o {"0":[1,2],"1":[1,2]})  │
│ dias_semana_permitidos: JSON (ej: [0,1,2,3,4])                 │
│ fecha_inicio_guardias*                                          │
│ fecha_fin_guardias*                                             │
│ zona_preferida_id*                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Guardia (OUTPUT)                       │
├─────────────────────────────────────────────────────────────────┤
│ id, curso_id, profesor_id, fecha, turno, recreo, zona_id       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Concepto Clave: SLOT

Un **Slot** es la unidad atómica a asignar:

```
SLOT = (fecha, turno, recreo_id, zona_id)
```

**Total de slots a cubrir:**
```
slots_totales = Σ (días_lectivos × recreos_activos_por_día × zonas_activas_en_fecha)
```

---

## 3. Algoritmo Propuesto (Análisis Conceptual)

### 3.1 Fase 0: Generación de Slots

**Objetivo:** Crear la lista completa de slots a cubrir.

```python
def generar_slots(config, zonas):
    """
    Para cada día lectivo:
        Para cada recreo configurado:
            Para cada zona activa en esa fecha:
                crear Slot(fecha, turno_del_recreo, recreo_id, zona_id)
    
    Consideraciones:
    - Excluir fines de semana
    - Excluir festivos (automáticos + personalizados)
    - Excluir fechas fuera del rango de cada zona
    """
    slots = []
    dias = obtener_dias_lectivos(config)  # Excluye festivos
    
    for dia in dias:
        for recreo in config.recreos:
            for zona in zonas:
                if zona_activa_en_fecha(zona, dia):
                    slots.append(Slot(dia, recreo.turno, recreo.id, zona.id))
    
    return slots
```

**Validación crítica:** El número de slots generados debe coincidir con `slots_totales` calculado en estadísticas.

---

### 3.2 Fase 1: Cálculo de Cuotas Ideales

**Objetivo:** Determinar cuántas guardias corresponden a cada profesor.

#### Fórmula de Participación:

```
participación[p] = factor_turno × factor_horas × factor_tutoria × proporcion_tiempo
```

Donde:
- **factor_turno**: Proporción de recreos accesibles según turno
  - Mañana: `recreos_mañana / total_recreos`
  - Tarde: `recreos_tarde / total_recreos`
  - Mixto/Completo: `1.0`

- **factor_horas**: `porcentaje_jornada / 100` (normalizado)

- **factor_tutoria**: 
  - Tutores: `config.ajuste_tutores` (default: 1.0)
  - No tutores: `config.ajuste_no_tutores` (default: 2.0 = doble carga)

- **proporcion_tiempo**: Solo si tiene fechas limitadas
  - `días_disponibles_profesor / días_lectivos_totales`

#### Cálculo de Cuota Ideal:

```
suma_ponderada = Σ participación[todos_profesores]

cuota_ideal[p] = (participación[p] / suma_ponderada) × slots_totales
```

**Redondeo:** Se aplica `floor()` a todos y se redistribuyen los sobrantes a quienes tienen mayor parte decimal.

---

### 3.3 Fase 2: Matriz de Elegibilidad

**Objetivo:** Pre-calcular qué profesores pueden cubrir qué slots.

#### Condiciones de Elegibilidad:

Un profesor `p` es **elegible** para un slot `s` si cumple TODAS estas condiciones:

| # | Condición | Descripción |
|---|-----------|-------------|
| 1 | **Turno compatible** | `p.turno ∈ {s.turno, 'mixto', 'completo'}` |
| 2 | **Recreo permitido** | `s.recreo_id ∈ p.recreos_permitidos[s.dia_semana]` |
| 3 | **Día permitido** | `s.fecha.weekday() ∈ p.dias_semana_permitidos` |
| 4 | **Fecha en rango** | `p.fecha_inicio <= s.fecha <= p.fecha_fin` |
| 5 | **Sin ausencia** | No existe `Ausencia` activa para `p` en `s.fecha` |
| 6 | **Slot libre** | El slot no está ya asignado a otro profesor |
| 7 | **Una guardia/día** | `p` no tiene otra guardia en `s.fecha` |
| 8 | **Zona activa** | La zona del slot está activa en esa fecha |

**Matriz resultado:**
```
elegibles[slot] = [profesor_ids que cumplen todas las condiciones]
```

**Detección de problemas:**
- Profesores con cuota > 0 pero 0 slots compatibles → Ajustar cuota a 0 y redistribuir
- Slots con 0 profesores elegibles → Marcar como "sin cobertura posible"

---

### 3.4 Fase 3: Asignación Principal

**Enfoque recomendado: Asignación por Rondas Equitativas**

```
ALGORITMO: RONDAS EQUITATIVAS
==============================

1. Ordenar profesores por PRIORIDAD:
   a) Profesores con fecha_inicio cercana (menos días disponibles = más urgente)
   b) Profesores con menos slots compatibles (más restrictivos)
   c) Profesores con mayor cuota (necesitan más)
   d) ID como desempate determinista

2. Para ronda = 1 hasta max(cuotas):
   Para cada profesor en orden de prioridad:
       Si asignadas[p] < cuota[p] AND asignadas[p] < ronda:
           slot = seleccionar_mejor_slot_disponible(p)
           Si slot existe:
               asignar(p, slot)
               marcar_slot_ocupado(slot)

3. Garantía: Todos los profesores reciben guardias proporcionalmente
   ANTES de que cualquiera supere su cuota.
```

#### Selección del Mejor Slot (Scoring):

```python
def score_slot(profesor, slot, guardias_previas):
    """
    Prioridades de selección (mayor = mejor):
    
    1. ZONA PREFERIDA: +100 si coincide con zona_preferida_id
    2. CONSISTENCIA ZONA: +50 si coincide con zonas de guardias previas
    3. CONSISTENCIA RECREO: +30 si coincide con recreos de guardias previas
    4. FECHAS AGRUPADAS: +20 si está cerca de última guardia asignada
    5. DÍA SEMANA: +10 si coincide con días de guardias previas
    6. FECHA TEMPRANA: Menor fecha = mejor (cronológico)
    """
```

---

### 3.5 Fase 4: Completitud de Cobertura

**Objetivo:** Garantizar que TODOS los slots queden asignados.

```
ALGORITMO: RELLENO DE SLOTS VACÍOS
===================================

slots_sin_cubrir = slots - slots_asignados

Para cada slot_vacio en orden cronológico:
    elegibles = obtener_elegibles(slot_vacio, ignorar_cuota=True)
    
    Si elegibles vacío:
        # Relajación progresiva
        Nivel 1: Permitir cuota +10%
        Nivel 2: Permitir cuota +25%
        Nivel 3: Permitir múltiples guardias/día
        Nivel 4: Sin límite de cuota
    
    Si aún elegibles vacío:
        MARCAR slot como SIN_COBERTURA_POSIBLE
        (Registrar en informe de errores)
    Sino:
        elegido = profesor con mayor déficit entre elegibles
        asignar(elegido, slot_vacio)
```

---

### 3.6 Fase 5: Optimización (Opcional)

**Objetivo:** Mejorar la distribución sin romper cobertura.

```
ALGORITMO: INTERCAMBIOS DE EQUILIBRIO
======================================

Para cada par de profesores (A, B) donde |asignadas_A - cuota_A| > 1:
    Si A tiene EXCESO y B tiene DÉFICIT:
        Para cada guardia_A de A:
            Si B es elegible para guardia_A.slot:
                Si existe guardia_B de B donde A es elegible:
                    INTERCAMBIAR(guardia_A, guardia_B)
                    (Mejora el equilibrio sin perder cobertura)
```

---

## 4. Comparativa con Implementación Actual

### 4.1 Algoritmo v2.9 (asignador_guardias.py)

| Aspecto | Implementado | Ideal | Estado |
|---------|--------------|-------|--------|
| Generación de slots | ✅ _build_slots() | ✅ | OK |
| Cálculo de cuotas | ✅ calcular_guardias_por_profesor() | ✅ | OK |
| Matriz elegibilidad | ✅ Fase 0 pre-análisis | ✅ | OK |
| Rondas equitativas | ✅ Fase 2.1 | ✅ | OK |
| Scoring determinista | ✅ Sin factor aleatorio | ✅ | OK |
| Completitud forzada | ⚠️ 7 fases pero a veces falla | ✅ | **MEJORAR** |
| Prioridad fecha_inicio | ✅ Profesores urgentes primero | ✅ | OK |

**Problemas identificados en v2.9:**
1. Múltiples fases pueden crear inconsistencias
2. El scoring de zona/recreo puede no ser óptimo
3. La relajación progresiva puede ser demasiado permisiva

### 4.2 Algoritmo v3.0 (asignador_guardias_v3_simple.py)

| Aspecto | Implementado | Ideal | Estado |
|---------|--------------|-------|--------|
| Enfoque simple | ✅ Profesor por profesor | ✅ | OK |
| Prioridad fecha_inicio | ✅ v3.1 mejorado | ✅ | OK |
| Slots agrupados | ✅ Fechas consecutivas | ✅ | OK |
| Consistencia zona/recreo | ✅ Ordenamiento optimizado | ✅ | OK |
| Completitud | ⚠️ Puede dejar slots sin cubrir | ✅ | **MEJORAR** |

**Problemas identificados en v3.0:**
1. Asigna profesor por profesor → puede agotar slots antes de cubrir todos
2. No tiene fase de relleno forzado
3. Menos robusto ante casos límite

---

## 5. Propuesta de Mejora: Algoritmo Híbrido v4.0

### 5.1 Principios de Diseño

1. **COBERTURA PRIMERO**: Todo slot debe quedar cubierto (si es matemáticamente posible)
2. **EQUIDAD GARANTIZADA**: Profesores equivalentes reciben ±1 guardia
3. **DETERMINISMO**: Mismo input → mismo output (sin aleatoridad)
4. **PRIORIDADES CLARAS**: Profesores urgentes (fecha_inicio cercana) primero
5. **CONSISTENCIA DE PATRONES**: Mantener zona/recreo/día cuando sea posible

### 5.2 Estructura del Algoritmo

```
ALGORITMO V4.0 HÍBRIDO
=======================

FASE 0: PREPARACIÓN (0-10%)
- Generar todos los slots
- Calcular cuotas ideales
- Construir matriz de elegibilidad
- Detectar y reportar problemas (profesores bloqueados, slots imposibles)

FASE 1: PRE-ASIGNACIÓN URGENTE (10-25%)
- Ordenar profesores por urgencia (fecha_inicio, restricciones)
- Asignar PRIMERO a profesores con ventanas temporales limitadas
- Garantizar que tengan oportunidad de cumplir su cuota

FASE 2: ASIGNACIÓN POR RONDAS (25-60%)
- Ronda por ronda, dar 1 guardia a cada profesor
- Usar scoring optimizado para seleccionar mejor slot
- Mantener patrones de zona/recreo consistentes

FASE 3: COMPLETITUD FORZADA (60-85%)
- Recorrer slots no asignados
- Asignar al profesor elegible con mayor déficit
- Relajar restricciones progresivamente si es necesario
- Registrar slots imposibles

FASE 4: OPTIMIZACIÓN FINAL (85-95%)
- Intercambios de equilibrio entre profesores
- Mejorar consistencia de patrones sin perder cobertura

FASE 5: VALIDACIÓN (95-100%)
- Verificar cobertura total
- Verificar límites de cuota
- Generar informe detallado
```

### 5.3 Función de Scoring Mejorada

```python
def score_asignacion(profesor, slot, contexto):
    """
    Scoring multi-criterio para seleccionar el mejor slot.
    
    Mayor puntuación = mejor elección.
    """
    score = 0
    
    # 1. DÉFICIT (más importante)
    # Profesores que más necesitan guardias tienen prioridad
    deficit = contexto.cuota[profesor.id] - contexto.asignadas[profesor.id]
    score += deficit * 1000  # Peso alto
    
    # 2. ZONA PREFERIDA
    if profesor.zona_preferida_id == slot.zona_id:
        score += 100
    elif profesor.zona_preferida_id is None:
        score += 0
    else:
        score -= 50  # Penalizar si tiene preferencia y no coincide
    
    # 3. CONSISTENCIA DE ZONA
    if contexto.ultima_zona.get(profesor.id) == slot.zona_id:
        score += 50
    
    # 4. CONSISTENCIA DE RECREO
    if contexto.ultimo_recreo.get(profesor.id) == slot.recreo_id:
        score += 30
    
    # 5. FECHAS AGRUPADAS
    if contexto.ultima_fecha.get(profesor.id):
        dias_desde_ultima = (slot.fecha - contexto.ultima_fecha[profesor.id]).days
        score += max(0, 20 - dias_desde_ultima)  # Bonus por cercanía
    
    # 6. DÍA DE SEMANA CONSISTENTE
    if contexto.ultimo_dia_semana.get(profesor.id) == slot.fecha.weekday():
        score += 10
    
    # 7. DESEMPATE DETERMINISTA
    # Menor ID = mayor prioridad (para reproducibilidad)
    score -= profesor.id * 0.001
    
    return score
```

---

## 6. Métricas de Éxito

Para validar que el algoritmo funciona correctamente:

| Métrica | Objetivo | Fórmula |
|---------|----------|---------|
| **Cobertura** | 100% | `slots_asignados / slots_totales` |
| **Participación** | 100% | `profesores_con_guardias / profesores_con_cuota` |
| **Desviación promedio** | <5% | `avg(abs(asignadas - cuota) / cuota)` |
| **Desviación máxima** | <15% | `max(abs(asignadas - cuota) / cuota)` |
| **Equidad de grupos** | ±1 | Profesores equivalentes deben tener misma cantidad |
| **Consistencia zona** | >70% | `guardias_en_zona_preferida / total` |

---

## 7. Casos Especiales a Manejar

### 7.1 Profesor Sin Elegibilidad

```
Situación: Profesor tiene cuota > 0 pero 0 slots compatibles
Causa: Restricciones demasiado estrictas o configuración incorrecta

Solución:
1. Detectar en Fase 0
2. Ajustar cuota a 0
3. Redistribuir cuota entre elegibles
4. Registrar en informe de advertencias
```

### 7.2 Slot Sin Cobertura Posible

```
Situación: Ningún profesor puede cubrir un slot específico
Causa: Combinación de ausencias + restricciones

Solución:
1. Detectar en Fase 3 (tras relajación máxima)
2. Marcar como SIN_COBERTURA
3. Continuar con el resto
4. Registrar en informe de errores
```

### 7.3 Profesor con Fecha Inicio Tardía

```
Situación: Profesor empieza en octubre pero la cuota se calcula sobre todo el año
Problema: Si no se prioriza, puede no alcanzar su cuota

Solución:
1. Calcular cuota proporcional (días_disponibles / días_totales)
2. Asignar con prioridad alta (Fase 1)
3. Concentrar guardias en su ventana temporal
```

### 7.4 Zona Temporal (Aparece/Desaparece)

```
Situación: Una zona solo existe durante parte del curso
Ejemplo: "Patio exterior" solo de abril a junio

Solución:
1. En generación de slots: filtrar por fecha_inicio/fin de zona
2. Slots se crean SOLO cuando la zona está activa
3. No afecta al cálculo de cuotas (ya está considerado)
```

---

## 8. Próximos Pasos Recomendados

### Opción A: Mejorar v2.9 Existente
1. ✅ El algoritmo ya tiene la estructura correcta
2. 🔧 Revisar y optimizar la Fase de completitud
3. 🔧 Mejorar el scoring para garantizar consistencia de patrones
4. 📊 Añadir métricas de validación al final

### Opción B: Simplificar con v3.0 Mejorado
1. ✅ Más simple y predecible
2. 🔧 Añadir fase de completitud forzada
3. 🔧 Mejorar manejo de casos especiales
4. 📊 Validar resultados con métricas

### Opción C: Crear v4.0 Híbrido (Recomendado)
1. 📝 Tomar lo mejor de v2.9 (fases) y v3.0 (simplicidad)
2. 🎯 Enfoque en cobertura + equidad
3. ⚡ Optimizar rendimiento
4. 📊 Métricas integradas desde el diseño

---

## 9. Conclusiones

El modelo de datos actual es **adecuado** para el problema. Los algoritmos existentes (v2.9 y v3.0) implementan la mayoría de la lógica necesaria, pero presentan problemas en:

1. **Garantía de cobertura total** - Faltan mecanismos de relleno forzado
2. **Manejo de casos especiales** - Zonas temporales, profesores urgentes
3. **Consistencia de patrones** - El scoring podría mejorarse

La propuesta v4.0 consolida las buenas prácticas de ambos algoritmos y añade robustez para garantizar cobertura completa manteniendo equidad.

---

## 10. Comparativa Detallada: Plan Propuesto vs Implementación Actual

### 10.1 Algoritmo v2.9 (asignador_guardias.py) - ~2400 líneas

| Fase | Implementado | Plan Propuesto | Diferencia | Impacto |
|------|--------------|----------------|------------|---------|
| **Fase 0: Pre-análisis** | ✅ Matriz elegibilidad, redistribución cuotas | ✅ Igual | NINGUNA | ✅ OK |
| **Fase 1: Ordenamiento** | ✅ Por fecha, turno, recreo, zona | ✅ Igual | NINGUNA | ✅ OK |
| **Fase 2.1: Rondas** | ✅ Profesores prioritarios por fecha_inicio | ✅ Igual | NINGUNA | ✅ OK |
| **Fase 2.2: Masiva** | ⚠️ Usa cuotas_ideales (sin relajación) | ✅ Igual | Correcto en v2.9 | ✅ OK |
| **Fase 3: CSP** | ⚠️ Forward checking básico | ✅ Forward checking | Similar | ⚠️ Mejorable |
| **Fase 4: SA** | ⚠️ Simulated Annealing completo | ⛔ No necesario | SA es costoso y poco efectivo | ⚠️ Eliminar |
| **Fase 5: Hungarian** | ⛔ DESHABILITADO (conflictos) | ⛔ No necesario | CORRECTO deshabilitarlo | ✅ OK |
| **Fase 5B: Completitud** | ✅ Relajación de cuotas + swaps | ✅ Igual | NINGUNA | ✅ OK |
| **Fase 6-7: Validación** | ✅ EquidadService, métricas | ✅ Igual | NINGUNA | ✅ OK |

**Diagnóstico v2.9:**
- ✅ **Fortalezas**: Pre-análisis robusto, rondas equitativas, múltiples estrategias de recuperación
- ⚠️ **Debilidades**: SA no mejora significativamente, demasiadas fases añaden complejidad
- 🎯 **Recomendación**: Simplificar eliminando SA (Fase 4), mantener resto

---

### 10.2 Algoritmo v3.0 (asignador_guardias_v3_simple.py) - ~923 líneas

| Paso | Implementado | Plan Propuesto | Diferencia | Impacto |
|------|--------------|----------------|------------|---------|
| **Paso 1: Carga** | ✅ Config, profesores, cuotas | ✅ Igual | NINGUNA | ✅ OK |
| **Paso 2: Slots** | ✅ Con fechas de zonas | ✅ Igual | NINGUNA | ✅ OK |
| **Paso 3: Prioridad** | ✅ fecha_inicio urgente primero | ✅ Igual | NINGUNA | ✅ OK |
| **Paso 4: Asignación** | ⚠️ Profesor por profesor | ❌ Rondas equitativas | **CRÍTICO** | 🔴 PROBLEMA |
| **Paso 5: Validación** | ✅ EstadisticasService | ✅ Igual | NINGUNA | ✅ OK |
| **Completitud forzada** | ⛔ NO IMPLEMENTADA | ✅ Obligatorio | **CRÍTICO** | 🔴 PROBLEMA |

**Diagnóstico v3.0:**
- ✅ **Fortalezas**: Simple, rápido, ordenamiento óptimo de slots por consistencia
- 🔴 **Debilidades críticas**:
  1. **No tiene rondas equitativas**: Asigna TODO a un profesor antes de pasar al siguiente
  2. **No tiene fase de completitud forzada**: Si un profesor "agota" slots, quedan huecos
  3. **No valida restricciones post-asignación** de forma completa
- 🎯 **Recomendación**: Añadir fase de completitud O cambiar a modelo de rondas

---

### 10.3 Análisis de los Problemas Reportados

#### Problema 1: "Se dejan días y zonas sin asignar"

| Algoritmo | Causa Probable | Solución |
|-----------|----------------|----------|
| **v2.9** | Fase 5B no se ejecuta si Hungarian falla | ✅ Ya deshabilitado Hungarian, Fase 5B sí funciona |
| **v3.0** | ⛔ NO hay fase de completitud | 🔧 Añadir paso de relleno forzado |

**Código v3.0 actual (problemático):**
```python
# v3.0 - Paso 4: Solo asigna lo que puede
slots_asignar = slots_disponibles[:cuota]
# Si slots_disponibles < cuota → profesor incompleto Y slots sin cubrir
```

**Código v3.0 necesario (faltante):**
```python
# v3.0 - Paso 6 (FALTANTE): Completitud forzada
for slot in todos_slots:
    if slot not in slots_ocupados:
        elegibles = obtener_elegibles(slot, ignorar_cuota=True)
        if elegibles:
            asignar(mejor_elegible, slot)
        else:
            registrar_sin_cobertura(slot)
```

#### Problema 2: "No sigue las prioridades"

| Algoritmo | Causa Probable | Solución |
|-----------|----------------|----------|
| **v2.9** | ✅ Prioridad correcta (fecha_inicio primero) | Ya funciona bien |
| **v3.0** | ⚠️ Prioridad correcta PERO asigna todo a uno antes de pasar al siguiente | Modelo de rondas |

**v3.0 - Comportamiento actual:**
```
1. Profesor A (cuota=30): Toma 30 guardias de slots preferidos
2. Profesor B (cuota=30): Solo quedan slots "malos" → recibe 30 peores
3. Resultado: A tiene las mejores fechas/zonas, B las peores
```

**v3.0 - Comportamiento ideal (rondas):**
```
Ronda 1: A toma 1, B toma 1, C toma 1...
Ronda 2: A toma 1, B toma 1, C toma 1...
...
Resultado: Todos tienen mix de slots "buenos" y "regulares"
```

---

### 10.4 Scoring de Selección de Profesor

**v2.9 - _seleccionar_profesor_optimizado():**
```python
def score_equitativo(p):
    # 1. DÉFICIT (más importante)
    deficit = cuotas_ideales[p.id] - asignadas[p.id]
    
    # 2. ZONA PREFERIDA
    s_zona = 100 if zona_preferida == slot.zona_id else (-50 if zona_preferida else 0)
    
    # 3. FECHAS CONSECUTIVAS (NUEVO v1.3)
    puntuacion_fechas = -distancia_dias si ultimo_dia else 0
    
    # 4. RECREO CONSISTENTE
    s_recreo = 50 si mismo_recreo else (-25 si diferente)
    
    # 5. DESEMPATE DETERMINISTA
    desempate = -p.id
    
    return (deficit, s_zona, puntuacion_fechas, s_recreo, desempate)
```

**v3.0 - _ordenar_slots_para_profesor():**
```python
def clave_ordenamiento(slot):
    # 1. ZONA (mantener consistencia)
    zona_match = 0 si zona_objetivo else 1
    
    # 2. RECREO (mantener consistencia)
    recreo_match = 0 si recreo_objetivo else 1
    
    # 3. FECHAS AGRUPADAS (distancia desde última)
    distancia_dias = abs((slot.fecha - fecha_base).days)
    
    # 4. DÍA SEMANA
    dia_semana_match = 0 si día_objetivo else 1
    
    # 5. FECHA (cronológico)
    # 6. RECREO (desempate)
    
    return (zona_match, recreo_match, distancia_dias, dia_semana_match, fecha, recreo_id)
```

**Diferencia clave:**
- v2.9: Selecciona PROFESOR para un SLOT (quien más necesita)
- v3.0: Selecciona SLOT para un PROFESOR (qué slot es mejor)

**Impacto:**
- v2.9: Garantiza que profesores con déficit tengan prioridad → más equitativo
- v3.0: Garantiza que cada profesor tenga slots consistentes → mejor experiencia individual

---

### 10.5 Conclusiones de la Comparativa

| Criterio | v2.9 | v3.0 | Ideal |
|----------|------|------|-------|
| **Cobertura total** | ✅ Múltiples fases de recuperación | ❌ Sin completitud forzada | v2.9 |
| **Equidad** | ✅ Rondas equitativas + scoring | ⚠️ Por orden de prioridad | v2.9 |
| **Simplicidad** | ❌ 7+ fases, ~2400 líneas | ✅ 5 pasos, ~923 líneas | v3.0 |
| **Rendimiento** | ⚠️ SA es costoso | ✅ Una pasada | v3.0 |
| **Consistencia patrones** | ⚠️ Scoring básico | ✅ Ordenamiento optimizado | v3.0 |
| **Mantenibilidad** | ⚠️ Complejo | ✅ Claro | v3.0 |

### 10.6 Recomendaciones Finales

#### Opción A: Mejorar v3.0 (RECOMENDADO)
```diff
+ Añadir Paso 6: Completitud forzada con relajación de cuotas
+ Cambiar Paso 4: De "profesor por profesor" a "por rondas"
= Mantener: Ordenamiento optimizado de slots
= Mantener: Simplicidad y claridad
```

**Esfuerzo estimado:** ~200 líneas nuevas

#### Opción B: Simplificar v2.9
```diff
- Eliminar Fase 4 (Simulated Annealing): Costoso, poco beneficio
- Eliminar código Hungarian (ya deshabilitado)
= Mantener: Fases 0-3, 5B, 6-7
```

**Esfuerzo estimado:** ~500 líneas menos

#### Opción C: Crear v4.0 Híbrido
```diff
+ Estructura simple de v3.0 (5 pasos)
+ Rondas equitativas de v2.9 (Fase 2.1)
+ Completitud forzada de v2.9 (Fase 5B)
+ Scoring de consistencia de v3.0
```

**Esfuerzo estimado:** ~600-800 líneas totales (nuevo archivo)

---

*Documento generado para análisis del sistema de guardias*
*Última actualización: 4 diciembre 2025*
