# Estrategia de Consecutividad en el Reparto de Guardias

**Fecha:** 2026-04-27  
**Algoritmos analizados:** CP-SAT (`asignador_guardias_cpsat.py`) · v4 Híbrido (`asignador_guardias_v4_hibrido.py`)

---

## 1. Objetivo

Que cada profesor realice todas sus guardias en un bloque compacto y continuo de días lectivos, minimizando la dispersión a lo largo del curso.

**Métrica actual** (usada en la gráfica de concentración):

```
concentración_prof = (n_guardias / días_naturales_entre_primera_y_última) × 100
```

---

## 2. Techo teórico de la métrica — límite físico inamovible

Con días lectivos lunes-viernes, aunque un profesor haga todas sus guardias en días **perfectamente consecutivos** (sin ningún hueco), el denominador siempre incluye los fines de semana, inflando el span natural:

| Guardias | Span lectivo | Span natural (cal.) | Métrica máxima |
|---:|---:|---:|---:|
| 16 | 16 | 21 | **76.2%** |
| 28 | 28 | 37 | **75.7%** |
| 33 | 33 | 44 | **75.0%** |
| 42 | 42 | 57 | **73.7%** |
| 55 | 55 | 74 | **74.3%** |
| 63 | 63 | 86 | **73.3%** |

**Consecuencia directa: la métrica jamás puede superar ~76% en un calendario escolar de lunes a viernes.**  
Un resultado de **70%** equivale prácticamente a "todas las guardias en días lectivos consecutivos" — es el máximo alcanzable en la práctica.

**El objetivo de 70-76% es correcto y realista. El objetivo de "100%" no es posible con esta métrica.**

---

## 3. Diagnóstico: por qué el resultado actual es 6-27%

### 3.1 Causa raíz en el algoritmo v4 Híbrido

El v4 funciona mediante **rondas equitativas**: en cada ronda se da 1 guardia a cada profesor que aún no ha alcanzado su cuota. Las rondas se iteran de 1 a max_cuota (~63).

El problema: **las rondas recorren el calendario completo**. En la ronda 1 todos los profesores reciben su primera guardia (repartida por las primeras semanas disponibles). En la ronda 2 reciben la segunda guardia, intentando ser consecutiva a la primera. Pero los slots cercanos a la guardia de la ronda 1 ya los han tomado otros profesores. Resultado: la segunda guardia cae semanas o meses después.

Aunque `_score_slot` tiene consecutividad como criterio 1 (penalización 0 si la distancia es 1 día), esto solo funciona si el slot consecutivo está disponible en ese momento. Con 70+ profesores compitiendo, los slots de días adyacentes se agotan rápidamente en cada ronda.

**Resultado**: 33 guardias en 222 días naturales = 14.9% (estado actual típico).  
**Objetivo**: 33 guardias en 44 días naturales = 75% (guardias todas consecutivas).

### 3.2 Causa raíz en el algoritmo CP-SAT

El modelo CP-SAT usa **cortes XOR** entre días adyacentes:

```python
corte_{p,d} = 1  iff  tiene_guardia_dia[p][d] XOR tiene_guardia_dia[p][d+1]
```

Con peso `PESO_CONSECUTIVIDAD = 1000`. Los problemas:

1. **No modela el span**: un hueco de 20 días genera exactamente los mismos 2 cortes que un hueco de 1 día. El solver no distingue ambos casos.
2. **Peso insuficiente**: `PESO_EQUIDAD_SUMA = 10,000` domina. El solver acepta cortes múltiples si eso mejora mínimamente la equidad-suma.
3. **No hay objetivo de span directo**: la métrica de la gráfica (`primera/ultima`) no se minimiza en ningún término de la función objetivo.

El término `PESO_SEMANAS_ACTIVAS = 5,000` (minimizar semanas con guardias) ayuda algo, pero solo concentra semanas, no días dentro de las semanas.

---

## 4. Revisión de premisas de configuración

### 4.1 Hard constraints — ¿alguna bloquea la consecutividad?

| Premisa | ¿Bloquea? | Valoración |
|---|---|---|
| Cobertura 100% slots | No | Correcta e inamovible. |
| Máx 1 guardia/día/profesor | No (es el mínimo necesario) | Correcta. |
| Turno compatible | Marginalmente | Correcta. Refleja contrato. |
| No ausencia ese día | Sí (genera huecos inevitables) | Correcta e inamovible. Habrá algún hueco por ausencia. |
| `fecha_inicio_guardias` / `fecha_fin_guardias` | **Sí — el mayor bloqueante** | Ver sección 4.2. |
| `recreos_permitidos` | Sí si es muy restrictivo | Ver sección 4.3. |
| No simultaneidad (misma franja) | No | Correcta. |

### 4.2 Premisa problemática: rango de fechas por profesor

`fecha_inicio_guardias` y `fecha_fin_guardias` acotan el periodo en que un profesor puede recibir guardias. Si ese rango es estrecho (p. ej. solo 2º trimestre), el solver no puede concentrar fuera de él. Además, cuando muchos profesores tienen rangos solapados y cortos, se generan "picos de demanda" que hacen imposible la concentración para todos simultáneamente.

**Recomendación**: Verificar si los rangos son obligatorios (p. ej. un contratado temporal) o convencionales. Un profesor sin rangos definidos (curso completo) es el escenario óptimo para la consecutividad.

Si el rango es real, la consecutividad solo puede garantizarse dentro de ese rango, y el objetivo de 70% aplica solo dentro de él.

### 4.3 Premisa potencialmente sobrerrestrictiva: `recreos_permitidos`

Si un profesor solo tiene permitido el recreo 1, solo puede hacer guardias en esa franja. Esto reduce a la mitad los slots elegibles por día y hace más difícil encontrar slots consecutivos.

**Recomendación**: Asegurarse de que `recreos_permitidos` refleja la realidad del horario de cada profesor, no un valor por defecto restrictivo.

### 4.4 Premisas correctas — no tocar

- **Cuota proporcional al contrato**: correcta y no interfiere con consecutividad (solo determina cuántas, no cuándo).
- **Equidad como prioridad absoluta**: correcta. La consecutividad es secundaria a la equidad.
- **Max 1 guardia/día/profesor**: correcta. Es la base de la consecutividad (sin esto, sería imposible modelarla).

### 4.5 Premisa innecesaria o mal concebida: término de semanas activas

`PESO_SEMANAS_ACTIVAS` es parcialmente redundante con `PESO_CONSECUTIVIDAD`: minimizar semanas activas ya implica concentración, y minimizar el span (sección 5) los sustituye a ambos con mayor precisión. Con el nuevo modelo propuesto, este término puede eliminarse o fusionarse.

---

## 5. Estrategia propuesta

### 5.1 CP-SAT: sustituir XOR cortes por minimización directa del span

En lugar de penalizar transiciones día a día, modelar directamente la variable `span[p] = ultima_guardia[p] - primera_guardia[p]` (en ordinales de días lectivos) y minimizar la suma.

**Modelado correcto en CP-SAT:**

```python
max_dia_ord = len(dias_unicos) - 1
primera: Dict[int, cp_model.IntVar] = {}
ultima:  Dict[int, cp_model.IntVar] = {}
span:    Dict[int, cp_model.IntVar] = {}

for p in profesores:
    if not tiene_guardia_dia[p.id]:
        continue
    primera[p.id] = model.NewIntVar(0, max_dia_ord, f"primera_{p.id}")
    ultima[p.id]  = model.NewIntVar(0, max_dia_ord, f"ultima_{p.id}")
    span[p.id]    = model.NewIntVar(0, max_dia_ord, f"span_{p.id}")

    for dia_ord, tiene in tiene_guardia_dia[p.id].items():
        # Si hay guardia en dia_ord, primera <= dia_ord y ultima >= dia_ord
        model.Add(primera[p.id] <= dia_ord).OnlyEnforceIf(tiene)
        model.Add(ultima[p.id]  >= dia_ord).OnlyEnforceIf(tiene)

    model.Add(span[p.id] == ultima[p.id] - primera[p.id])

# En la función objetivo: minimizar la suma de spans
PESO_SPAN = 300  # ajustar tras pruebas
objetivo += PESO_SPAN * sum(span.values())
```

**Por qué el modelado es correcto**: La restricción `OnlyEnforceIf` garantiza que `primera[p] ≤ dia_ord` solo cuando hay guardia ese día. El solver, al minimizar `ultima - primera`, maximiza `primera` (lo sube hasta el primer día real con guardia) y minimiza `ultima` (lo baja hasta el último día real). No puede "hacer trampa" porque si sube `primera` más allá del primer día real, la restricción lo prohíbe.

**Eliminación de términos redundantes**: Con el span directo, los términos `PESO_CONSECUTIVIDAD` (XOR cortes) y `PESO_SEMANAS_ACTIVAS` pueden eliminarse. Son aproximaciones del span que el nuevo término modela exactamente.

**Pesos recomendados:**

| Término | Actual | Propuesto | Motivo |
|---|---|---|---|
| `PESO_EQUIDAD` (max_dev) | 1.000.000 | 1.000.000 | Sin cambio. |
| `PESO_EQUIDAD_SUMA` | 10.000 | 10.000 | Sin cambio. |
| `PESO_SEMANAS_ACTIVAS` | 5.000 | **0** (eliminar) | Sustituido por span. |
| `PESO_CONSECUTIVIDAD` (XOR) | 1.000 | **0** (eliminar) | Sustituido por span. |
| `PESO_SPAN` (nuevo) | — | **300** | Minimiza directamente la métrica. |
| `PESO_ZONA` | 3 | 3 | Sin cambio. |

Con `PESO_SPAN = 300` y una reducción de span esperada de ~125 días lectivos por profesor × 70 profesores = 8,750 días: la mejora en la función objetivo sería de 2,625,000 puntos — sustancial y bien por debajo del umbral de equidad (1,000,000 × max_dev), por lo que la equidad nunca se sacrifica.

**Riesgo**: Aumentar demasiado `PESO_SPAN` podría hacer que el solver acepte romper la equidad-suma para ganar compacidad. Con PESO_SPAN ≤ 500 el riesgo es mínimo dado el dominio del modelo.

### 5.2 v4 Híbrido: asignación por bloques temporales

El problema de fondo del v4 es estructural: las **rondas iteran el calendario completo**. La solución es cambiar a una **asignación por bloques** antes de la asignación por rondas:

#### Fase 0 nueva: pre-asignación de ventana temporal por profesor

```python
# 1. Calcular la ventana ideal para cada profesor:
#    span_ideal[p] = ceil(cuota[p] / slots_por_dia_disponibles_para_p)
#    ventana[p] = (dia_inicio, dia_inicio + span_ideal[p])

# 2. Asignar ventanas sin solapamiento total, distribuyendo inicio en el tiempo:
#    Ordenar profesores por cuota descendente (primero los que necesitan más días).
#    Asignar inicio de ventana usando un "cursor" que avanza.

# 3. Modificar _score_slot para penalizar fuertemente slots fuera de la ventana:
#    si slot.fecha fuera de ventana[prof]: penalización = 1000
#    si slot.fecha dentro de ventana[prof] y consecutivo: penalización = 0
```

**Algoritmo de asignación de ventanas:**

```python
def calcular_ventanas_bloque(profesores, cuotas, dias_lectivos, slots_por_dia):
    ventanas = {}
    cursor = 0  # día lectivo de inicio
    
    for p in sorted(profesores, key=lambda p: -cuotas[p.id]):
        cuota = cuotas[p.id]
        # Días necesarios = cuota (1 guardia/día máx)
        # Añadir margen del 20% para absorber ausencias y días sin slot
        dias_necesarios = max(cuota, int(cuota * 1.2))
        
        inicio = cursor
        fin = min(cursor + dias_necesarios, len(dias_lectivos) - 1)
        ventanas[p.id] = (inicio, fin)
        
        # Solapamiento del 30%: el siguiente empieza cuando este lleva 70%
        cursor = inicio + int(dias_necesarios * 0.7)
    
    return ventanas
```

Con solapamiento del 30%, los bloques se solapan parcialmente, lo que distribuye la carga y permite cubrir todos los slots de cada día con distintos profesores en fase.

**Modificación de `_score_slot`:**

```python
# En _score_slot, añadir como criterio 0 (máxima prioridad):
ventana_prof = ctx.ventanas_bloque.get(profesor.id)
if ventana_prof:
    dia_ord = ctx.dia_a_ordinal[slot.fecha]
    inicio, fin = ventana_prof
    fuera_ventana = 0 if inicio <= dia_ord <= fin else 1
else:
    fuera_ventana = 0

return (fuera_ventana, consecutividad, zona_match, recreo_match, dia_match, slot.fecha, slot.recreo_id)
```

**Completitud forzada**: Si al terminar la fase de rondas algún slot queda sin cubrir (porque los profesores de su bloque ya alcanzaron su cuota), el mecanismo de completitud forzada ya existente toma el relevo con relajación progresiva.

### 5.3 Hint greedy para CP-SAT: semilla con lógica de bloques

El hint greedy actual mezcla equidad y consecutividad desde el inicio. Propuesta: aplicar la misma lógica de ventanas del v4 como semilla:

```python
# Fase de hint: pre-calcular ventana por profesor
ventanas = calcular_ventanas_bloque(profesores, cuotas_ideales, dias_unicos, ...)

def score_candidato_hint(pid, dia_ord):
    ratio = asig_greedy[pid] / max(cuotas_ideales[pid], 0.1)
    
    # Penalización fuerte si está fuera de su ventana
    inicio, fin = ventanas[pid]
    fuera = 0 if inicio <= dia_ord <= fin else 10.0  # penalización fuerte
    
    # Bonus consecutividad (dentro de ventana)
    bonus_consec = 0
    if pid in ultimo_dia_guardia:
        diff = dia_ord - ultimo_dia_guardia[pid]
        if diff == 1:
            bonus_consec = -0.3
    
    return ratio + fuera + bonus_consec
```

---

## 6. Plan de implementación

### Fase A — CP-SAT (cambio de modelo, alto impacto)

- [x] ~~En `asignador_guardias_cpsat.py`, reemplazar los bloques de `penalizacion_consecutividad` y `penalizacion_semanas_activas` por el modelo `primera / ultima / span`.~~ ✅ RESUELTO v5.32.0
- [x] ~~Ajustar la función objetivo: eliminar `PESO_CONSECUTIVIDAD` y `PESO_SEMANAS_ACTIVAS`, añadir `PESO_SPAN * sum(span.values())`.~~ ✅ RESUELTO v5.32.0
- [x] ~~Actualizar métricas finales (fase 8) para calcular y logar el span medio y la concentración resultante.~~ ✅ RESUELTO v5.32.0
- [x] ~~Ejecutar `pytest tests/ -q` y comparar métricas de concentración antes/después.~~ ✅ RESUELTO v5.32.0 (2138 passed)

**Impacto esperado**: métrica de concentración de ~15% → ~65-72% en CP-SAT.

### Fase B — Hint greedy con ventanas (mejora de velocidad de convergencia)

- [x] ~~Implementar `calcular_ventanas_bloque()` en `_asignador_v4_helpers.py`.~~ ✅ RESUELTO v5.32.0
- [x] ~~Aplicar la lógica de ventanas en la fase de hint greedy (fase 5 del CP-SAT).~~ ✅ RESUELTO v5.32.0
- [x] ~~El solver parte de una solución inicial ya concentrada → converge antes → mejor resultado en el tiempo de timeout.~~ ✅ RESUELTO v5.32.0

### Fase C — v4 Híbrido: asignación por bloques

- [x] ~~Implementar `calcular_ventanas_bloque()` (compartida con Fase B).~~ ✅ RESUELTO v5.32.0
- [x] ~~Añadir `ventanas_bloque` a `ContextoAsignacion`.~~ ✅ RESUELTO v5.32.0
- [x] ~~Modificar `_score_slot` para penalizar slots fuera de la ventana.~~ ✅ RESUELTO v5.32.0
- [x] ~~Añadir una fase 0.5 en `generar_guardias_v4_hibrido` que calcule y registre las ventanas.~~ ✅ RESUELTO v5.32.0
- [x] ~~Verificar que la completitud forzada sigue cubriendo todos los slots.~~ ✅ RESUELTO v5.32.0 (sin cambios en completitud, mecanismo existente intacto)

**Impacto esperado**: métrica de concentración de ~15% → ~60-70% en v4 Híbrido (el v4 al ser heurístico no garantiza el óptimo, pero debería acercarse mucho).

---

## 7. Límites inevitables que persisten incluso con el nuevo modelo

Aunque se implementen todas las fases, habrá profesores que no alcancen el 70% por razones estructurales:

1. **Ausencias largas** dentro del bloque: un profesor ausente 2 semanas en medio de su bloque tiene ese hueco en el span natural, bajando su métrica inevitablemente.
2. **Rangos de fecha estrechos** (`fecha_inicio/fin_guardias`): si el rango es de 60 días pero el profesor necesita 42 guardias, el span mínimo ya es ~57 días naturales → métrica máxima 73.7%. Pero si hay ausencias en esos 60 días, la ocupación efectiva baja.
3. **Pocos slots disponibles en días concretos** (festivos, días con pocas zonas abiertas): fuerzan huecos inevitables.
4. **Centro con un único turno**: si solo hay mañana, los slots/día se reducen a la mitad, y la concentración es más difícil de lograr para todos simultáneamente.

---

## 8. Resumen ejecutivo

| Aspecto | Estado actual | Meta con nuevo modelo |
|---|---|---|
| Concentración típica | 6-27% | 65-75% |
| Techo teórico posible | — | ~76% (días consecutivos perfectos) |
| Modelo CP-SAT | XOR cortes (débil, no mide span) | Span directo primera/ultima |
| Modelo v4 | Rondas temporales dispersas | Bloques por profesor con solapamiento |
| Pesos CP-SAT | Consecutividad 1.000, semanas 5.000 | Span 300 (los dos anteriores eliminados) |
| Premisa problemática | `fecha_inicio/fin` estrechos | Revisar caso a caso; no es un bug |
| Premisa mal concebida | Semanas activas (redundante con span) | Eliminar del modelo |
