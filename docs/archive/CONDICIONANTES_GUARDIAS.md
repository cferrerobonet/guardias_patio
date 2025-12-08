# Condicionantes para el Cálculo y Asignación de Guardias

## Resumen Ejecutivo

El sistema de guardias calcula **cuántas guardias** corresponden a cada profesor (cuota) y **cuándo/dónde** se asignan (asignación). Este documento explica todos los factores que influyen en ambos procesos.

---

## 1. CÁLCULO DE LA CUOTA (¿Cuántas guardias?)

La cuota de cada profesor se calcula con esta fórmula:

```
cuota = total_slots × factor_profesor / suma_todos_factores
```

Donde `factor_profesor` es el producto de 4 factores:

### 1.1 Factor Turno (`factor_turno`)

| Turno del Profesor | Fórmula | Ejemplo |
|--------------------|---------|---------|
| `mañana` | recreos_mañana ÷ total_recreos | Si hay 2 mañana y 2 tarde → 0.5 |
| `tarde` | recreos_tarde ÷ total_recreos | Si hay 2 mañana y 2 tarde → 0.5 |
| `mixto` / `completo` | 1.0 | Puede cubrir cualquier recreo |

**Ejemplo**: Con 2 recreos de mañana y 2 de tarde:
- Profesor de mañana: factor = 0.5 (solo puede cubrir la mitad)
- Profesor mixto: factor = 1.0 (puede cubrir todo)

### 1.2 Factor Jornada (`factor_horas`)

```
factor_horas = porcentaje_jornada ÷ 100
```

| Porcentaje Jornada | Factor |
|-------------------|--------|
| 100% (30h) | 1.0 |
| 80% (24h) | 0.8 |
| 50% (15h) | 0.5 |
| 33% (10h) | 0.33 |

**Importante**: Se usa `porcentaje_jornada`, NO `horas_contrato` directamente.

### 1.3 Factor Tutoría (`factor_tutoria`)

Valores definidos en la configuración del sistema:

| Condición | Factor (Configuración) |
|-----------|------------------------|
| Es tutor | `ajuste_tutores` (ej: 0.8) |
| No es tutor | `ajuste_no_tutores` (ej: 1.0) |

**Ejemplo**: Si un tutor tiene `ajuste_tutores = 0.8`, su cuota se reduce un 20%.

### 1.4 Proporción de Tiempo (`proporcion_tiempo`)

Para profesores con fechas límite (`fecha_inicio_guardias` o `fecha_fin_guardias`):

```
proporcion_tiempo = días_disponibles ÷ días_lectivos_totales
```

| Situación | Proporción |
|-----------|------------|
| Todo el curso | 1.0 |
| Incorporación tardía (mitad del curso) | ~0.5 |
| Baja anticipada | Según días restantes |

**Ejemplo**: Curso de 180 días lectivos, profesor que empieza a mitad → 90/180 = 0.5

---

## 2. CÁLCULO DEL FACTOR TOTAL

```
factor_total = factor_turno × factor_horas × factor_tutoria × proporcion_tiempo
```

### Ejemplo Comparativo

| Profesor | Turno | Jornada | Tutor | Tiempo | Factor Total |
|----------|-------|---------|-------|--------|--------------|
| A | mañana | 100% | No | 100% | 0.5 × 1.0 × 1.0 × 1.0 = **0.50** |
| B | mixto | 100% | No | 100% | 1.0 × 1.0 × 1.0 × 1.0 = **1.00** |
| C | tarde | 50% | No | 100% | 0.5 × 0.5 × 1.0 × 1.0 = **0.25** |
| D | mixto | 100% | Sí | 100% | 1.0 × 1.0 × 0.8 × 1.0 = **0.80** |
| E | mañana | 80% | No | 50% | 0.5 × 0.8 × 1.0 × 0.5 = **0.20** |

### Distribución de Cuotas

Con 100 slots totales y los profesores anteriores:

```
suma_factores = 0.50 + 1.00 + 0.25 + 0.80 + 0.20 = 2.75

Profesor A: 100 × 0.50 / 2.75 = 18.2 → 18 guardias
Profesor B: 100 × 1.00 / 2.75 = 36.4 → 36 guardias
Profesor C: 100 × 0.25 / 2.75 =  9.1 →  9 guardias
Profesor D: 100 × 0.80 / 2.75 = 29.1 → 29 guardias
Profesor E: 100 × 0.20 / 2.75 =  7.3 →  8 guardias (ajuste redondeo)
                                     ─────
                                Total: 100 guardias
```

---

## 3. ASIGNACIÓN DE GUARDIAS (¿Cuándo y Dónde?)

Una vez calculada la cuota, el algoritmo v4.0 asigna las guardias considerando:

### 3.1 Restricciones HARD (Nunca se violan)

| Restricción | Descripción |
|-------------|-------------|
| **Turno compatible** | Profesor de mañana no puede cubrir recreo de tarde |
| **No ausente** | No se asigna guardia si hay ausencia activa en esa fecha |
| **Fecha en rango** | Respeta `fecha_inicio_guardias` y `fecha_fin_guardias` |
| **Día de semana permitido** | Campo `dias_semana_permitidos` (JSON) |
| **Recreo permitido** | Campo `recreos_permitidos` (JSON) |
| **Slot no ocupado** | No se asigna a un slot ya cubierto |
| **NO simultaneidad** | Un profesor NO puede estar en 2 zonas al mismo tiempo |

### 3.2 Restricciones SOFT (Pueden relajarse para cobertura)

| Restricción | Cuándo se relaja |
|-------------|------------------|
| **Una guardia por día** | Fase de completitud forzada |
| **No exceder cuota** | Si quedan slots sin cubrir |

### 3.3 Formato de Campos JSON

**`dias_semana_permitidos`**:
```json
[0, 1, 2, 3, 4]  // 0=Lunes, 4=Viernes
```

**`recreos_permitidos`** (formato simple):
```json
[1, 2, 3, 4]  // IDs de recreos permitidos
```

**`recreos_permitidos`** (formato por día):
```json
{
  "0": [1, 2],     // Lunes: recreos 1 y 2
  "1": [1, 2, 3],  // Martes: recreos 1, 2 y 3
  "4": [1]         // Viernes: solo recreo 1
}
```

---

## 4. FASES DEL ALGORITMO v4.0

### Fase 0: Preparación
- Genera todos los slots (fecha × recreo × zona)
- Calcula cuotas ideales con la fórmula anterior
- Redistribuye cuotas de profesores "bloqueados" (sin elegibilidad)

### Fase 1: Pre-asignación Urgente
Prioriza profesores con `fecha_inicio_guardias` cercana:
- Calcula "urgencia" = días hasta que empieza
- Asigna primero a los más urgentes

### Fase 2: Asignación por Rondas Equitativas
```
Para cada ronda (1 hasta max_cuota):
    Para cada profesor (ordenado):
        Si no ha alcanzado su cuota:
            Buscar slot elegible
            Asignar si encuentra
```

**Objetivo**: TODOS los profesores avanzan simultáneamente, nadie "monopoliza" slots.

### Fase 3: Completitud Forzada
Si quedan slots sin cubrir:
1. **Relajar cuota**: Asignar aunque exceda cuota ideal
2. **Relajar 1-guardia/día**: Permitir múltiples guardias por día

### Fase 4: Validación
- Calcular métricas de cobertura
- Detectar profesores con déficit/exceso
- Generar resumen

---

## 5. PROBLEMA DE EQUIDAD DETECTADO

### Síntoma
Profesores con "condiciones iguales" reciben diferente número de guardias.

### Causas Posibles

#### 5.1 Orden de Asignación en Rondas
El algoritmo asigna por orden de profesor. Si hay más candidatos que slots:
```
Slot disponible: Lunes-Mañana-Recreo1-Zona1
Profesores elegibles: A, B, C (misma cuota)
→ Se asigna al primero (A) por orden de iteración
```

**Solución**: Implementar ordenación por "déficit actual":
```
ordenar_por(cuota_ideal - asignadas_actual)
```

#### 5.2 Restricciones Ocultas
Profesores "iguales" pueden tener diferencias en:
- `dias_semana_permitidos`
- `recreos_permitidos`
- Ausencias registradas
- Fechas de inicio/fin ligeramente diferentes

#### 5.3 Geometría del Problema
Con 2 profesores de mañana y 3 recreos de mañana × 2 zonas = 6 slots/día:
- Profesor A: 3 slots
- Profesor B: 3 slots ✓

Pero si un día tiene ausencia de A:
- Profesor B: 6 slots ese día
- Desequilibrio acumulado

#### 5.4 Fase de Completitud
Si hay slots sin cubrir, se relajan restricciones:
- Profesores "disponibles" reciben más guardias
- Profesores con más restricciones reciben menos

---

## 6. RECOMENDACIONES PARA MEJORAR EQUIDAD

### 6.1 Ordenar por Déficit en Cada Ronda
```python
# Actual (orden fijo)
for profesor in profesores_ordenados:
    asignar_si_elegible(profesor, slot)

# Mejorado (orden dinámico por déficit)
for profesor in sorted(profesores, key=lambda p: cuota[p.id] - asignadas[p.id], reverse=True):
    asignar_si_elegible(profesor, slot)
```

### 6.2 Balanceo Post-Asignación
Después de Fase 2:
1. Detectar desequilibrios (diferencia > 1 entre iguales)
2. Intercambiar guardias entre profesores
3. Respetar restricciones HARD

### 6.3 Garantía de ±1 Guardia
```
Para profesores con MISMO factor_total:
    diferencia_maxima = 1 guardia

Verificar y corregir al final de Fase 2.
```

### 6.4 Visualizar Factores
Añadir log detallado:
```
Profesor | Turno | Jornada | Tutor | Tiempo | Factor | Cuota | Real | Diff
---------|-------|---------|-------|--------|--------|-------|------|-----
Prof A   | mix   | 100%    | No    | 100%   | 1.00   | 18    | 17   | -1
Prof B   | mix   | 100%    | No    | 100%   | 1.00   | 18    | 19   | +1
```

---

## 7. RESUMEN DE CONDICIONANTES

### Afectan a la CUOTA (número de guardias):
1. ✅ Turno (mañana/tarde/mixto)
2. ✅ Porcentaje de jornada
3. ✅ Condición de tutor
4. ✅ Fechas de inicio/fin de guardias

### Afectan a la ASIGNACIÓN (cuándo/dónde):
1. ✅ Turno (limita recreos disponibles)
2. ✅ Ausencias activas
3. ✅ Fechas de inicio/fin
4. ✅ Días de semana permitidos
5. ✅ Recreos permitidos
6. ✅ No simultaneidad (una zona por momento)
7. ⚠️ Una guardia por día (puede relajarse)
8. ⚠️ No exceder cuota (puede relajarse)

### NO deberían afectar a profesores "iguales":
- ❌ Orden en la base de datos
- ❌ Nombre del profesor
- ❌ ID del profesor

---

## 8. PRÓXIMOS PASOS

1. **Diagnóstico**: Añadir log detallado para identificar dónde se produce el desequilibrio
2. **Ordenación dinámica**: Implementar ordenación por déficit en cada ronda
3. **Post-balanceo**: Añadir fase de intercambio para garantizar ±1
4. **Tests específicos**: Crear tests que verifiquen equidad entre profesores iguales
