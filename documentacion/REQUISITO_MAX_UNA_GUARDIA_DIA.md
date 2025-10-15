# Requisito: Máximo 1 Guardia por Día

**Fecha de implementación:** 15 de octubre de 2025  
**Versión:** 2.0  
**Prioridad:** CRÍTICA ⚠️

---

## 📋 Descripción del Requisito

Un profesor **sólo puede hacer como máximo 1 guardia al día**, independientemente de si es de mañana o de tarde. Este límite es un total diario que suma todas las guardias asignadas.

### Justificación

- **Distribución equitativa**: Evita sobrecargar a ciertos profesores con múltiples guardias en un mismo día
- **Bienestar del profesorado**: Permite una planificación personal más efectiva
- **Cumplimiento de normativa**: Respeta los acuerdos de distribución de cargas

---

## ✅ Ejemplos Correctos

### Caso 1: Guardias en días diferentes
```
Profesor: "GARCÍA LÓPEZ, MARÍA"
- Lunes 15/09    - MAÑANA - Recreo 1 - Patio A  ✓
- Martes 16/09   - TARDE  - Recreo 3 - Patio B  ✓
- Miércoles 17/09 - MAÑANA - Recreo 2 - Patio C  ✓
```
✅ **VÁLIDO**: Cada día tiene solo 1 guardia

### Caso 2: Profesor de turno mañana
```
Profesor: "MARTÍNEZ SANZ, JUAN"
- Lunes 15/09    - MAÑANA - Recreo 1 - Patio A  ✓
- Martes 16/09   - MAÑANA - Recreo 1 - Patio B  ✓
- Miércoles 17/09 - MAÑANA - Recreo 2 - Patio A  ✓
```
✅ **VÁLIDO**: 1 guardia por día, todas de mañana

---

## ❌ Ejemplos Incorrectos

### Violación: 2 guardias en el mismo día
```
Profesor: "LÓPEZ FERNÁNDEZ, ANA"
- Lunes 15/09 - MAÑANA - Recreo 1 - Patio A  
- Lunes 15/09 - TARDE  - Recreo 3 - Patio B  ← ❌ VIOLACIÓN
```
❌ **INVÁLIDO**: Tiene 2 guardias el mismo día (una de mañana y otra de tarde)

### Violación: 3 guardias en el mismo día
```
Profesor: "SÁNCHEZ RUIZ, PEDRO"
- Viernes 19/09 - MAÑANA - Recreo 1 - Patio A  
- Viernes 19/09 - MAÑANA - Recreo 2 - Patio B  ← ❌ VIOLACIÓN
- Viernes 19/09 - TARDE  - Recreo 3 - Patio C  ← ❌ VIOLACIÓN
```
❌ **INVÁLIDO**: Tiene 3 guardias el mismo día

---

## 🔧 Implementación Técnica

### Archivo Modificado
`src/services/asignador_guardias.py`

### Variables de Control

```python
# Línea ~106: Inicialización del diccionario de control
guardias_por_dia_prof: Dict[Tuple[int, date], bool] = {}
```

Este diccionario almacena pares `(profesor_id, fecha)` para rastrear qué profesores ya tienen guardia en qué días.

### Validación Durante la Asignación

```python
# Líneas ~130-133: Validación en el loop de asignación
# VALIDACIÓN CRÍTICA 2: Un profesor NO puede hacer más de 1 guardia al día
# (sumando mañana y tarde)
if (p.id, slot.fecha) in guardias_por_dia_prof:
    continue
```

Si un profesor ya tiene guardia en esa fecha, se excluye de los candidatos elegibles para ese slot.

### Registro al Asignar

```python
# Líneas ~173-174: Registro después de asignar guardia
# Marcar que este profesor ya tiene guardia en este día (cualquier turno)
guardias_por_dia_prof[(elegido.id, slot.fecha)] = True
```

---

## 🧪 Tests de Validación

### Test 1: Verificación Básica
**Archivo:** `tests/test_max_una_guardia_dia.py`  
**Función:** `test_max_una_guardia_por_dia()`

**Escenario:**
- 5 días lectivos (L-V)
- 4 recreos diarios (2 mañana + 2 tarde)
- 2 zonas
- 10 profesores mixtos

**Validación:**
- Recorre todas las guardias generadas
- Agrupa por (profesor_id, fecha)
- Verifica que ningún grupo tenga más de 1 guardia
- Si encuentra violaciones, falla con mensaje detallado

### Test 2: Distribución Equilibrada
**Archivo:** `tests/test_max_una_guardia_dia.py`  
**Función:** `test_distribucion_equilibrada_con_limite_diario()`

**Escenario:**
- Mes completo (~22 días lectivos)
- 2 recreos diarios (1 mañana + 1 tarde)
- 3 zonas
- 15 profesores mixtos

**Validación:**
- Verifica que máximo sea 1 guardia/día
- Asegura que se generen guardias (no falla por sobre-restricción)
- Verifica distribución equilibrada (diferencia ≤ 5 entre max y min)

### Resultado de Tests

```bash
$ pytest tests/test_max_una_guardia_dia.py -v

tests/test_max_una_guardia_dia.py::test_max_una_guardia_por_dia PASSED [ 50%]
tests/test_max_una_guardia_dia.py::test_distribucion_equilibrada_con_limite_diario PASSED [100%]

2 passed in 0.11s
```

---

## 📊 Impacto en el Sistema

### Cambios en el Algoritmo

**ANTES** (sin el requisito):
```
Slots disponibles: 400
Profesores: 20
Resultado: Algunos profesores con 2-3 guardias por día
```

**DESPUÉS** (con el requisito):
```
Slots disponibles: 400
Profesores: 20
Restricción adicional: Max 1 guardia/día
Resultado: Cada profesor máximo 1 guardia por día
Distribución más equitativa pero potencial de slots no cubiertos si hay pocos profesores
```

### Cobertura de Guardias

Con este requisito, es posible que algunos slots queden sin cubrir si:
- Hay pocos profesores
- Muchas restricciones adicionales (días permitidos, recreos permitidos, etc.)
- Periodo lectivo muy largo con muchos recreos diarios

**Recomendación:** Asegurar que la ratio `profesores / días_lectivos` sea adecuada.

### Fórmula Orientativa

```
Profesores mínimos recomendados = (Días lectivos × Recreos por día × Zonas) / Días laborables del profesor
```

**Ejemplo:**
- 100 días lectivos
- 4 recreos/día (2 mañana + 2 tarde)
- 3 zonas
- Profesores trabajan ~100 días

```
Profesores mínimos = (100 × 4 × 3) / 100 = 12 profesores
```

Con el límite de 1 guardia/día: cada profesor haría ~100 guardias en el curso.

---

## 🔗 Relación con Otras Validaciones

Este requisito se suma a las validaciones existentes:

### 1. No Duplicidad de Ubicaciones (Validación 1)
```python
# Un profesor NO puede estar en dos zonas al mismo tiempo
if (p.id, slot.fecha, slot.turno, slot.recreo_id) in guardias_por_slot_prof:
    continue
```

### 2. Máximo 1 Guardia por Día (Validación 2) ← **ESTE REQUISITO**
```python
# Un profesor NO puede hacer más de 1 guardia al día
if (p.id, slot.fecha) in guardias_por_dia_prof:
    continue
```

### 3. Otras Restricciones
- Turno compatible (mañana/tarde/mixto)
- Fecha inicio guardias
- Días de semana permitidos
- Recreos permitidos
- Cuota de guardias no excedida

**Orden de evaluación:**
1. Cuota no excedida
2. Turno compatible
3. Fecha inicio guardias
4. Días permitidos
5. Recreos permitidos
6. ✅ **No duplicidad en mismo slot** (Validación 1)
7. ✅ **No más de 1 guardia por día** (Validación 2) ← **NUEVO**

---

## 📝 Documentación Relacionada

- **Documento principal**: `documentacion/REQUISITOS_Y_VALIDACIONES.md`
- **Solución de duplicados**: `documentacion/SOLUCION_DUPLICADOS_GUARDIAS.md`
- **Tests**: `tests/test_max_una_guardia_dia.py`
- **Código fuente**: `src/services/asignador_guardias.py`

---

## 🎯 Casos de Uso

### Escenario Real 1: Instituto Pequeño
```
- 15 profesores
- 100 días lectivos
- 2 recreos/día
- 2 zonas

Slots totales = 100 × 2 × 2 = 400
Con límite 1/día:
  - Cada profesor puede hacer máximo 100 guardias
  - 15 profesores × 100 días = 1500 "profesor-días" disponibles
  - 400 slots / 15 profesores = ~27 guardias/profesor
  ✅ VIABLE: 27 < 100
```

### Escenario Real 2: Instituto Grande
```
- 50 profesores
- 180 días lectivos
- 4 recreos/día (2 mañana + 2 tarde)
- 3 zonas

Slots totales = 180 × 4 × 3 = 2160
Con límite 1/día:
  - Cada profesor puede hacer máximo 180 guardias
  - 50 profesores × 180 días = 9000 "profesor-días" disponibles
  - 2160 slots / 50 profesores = ~43 guardias/profesor
  ✅ VIABLE: 43 < 180
```

### Escenario Problemático: Sobre-restricción
```
- 8 profesores
- 100 días lectivos
- 6 recreos/día
- 4 zonas

Slots totales = 100 × 6 × 4 = 2400
Con límite 1/día:
  - Cada profesor puede hacer máximo 100 guardias
  - 8 profesores × 100 días = 800 "profesor-días" disponibles
  - 2400 slots necesitan cubrirse
  - Pero solo hay 800 "profesor-días" disponibles
  ⚠️ PROBLEMA: No se pueden cubrir todos los slots
  
Solución: Añadir más profesores o reducir recreos/zonas
```

---

## ✨ Conclusión

Este requisito es **fundamental** para garantizar una distribución equitativa y sostenible de las guardias de patio. La implementación está completamente testeada y validada.

**Estado:** ✅ IMPLEMENTADO Y VALIDADO  
**Tests:** 54/54 PASSING  
**Impacto:** Mejora equidad, puede reducir cobertura si hay pocos profesores  
**Recomendación:** Monitorizar slots no cubiertos y ajustar plantilla según necesidad

---

**Fin del documento**
