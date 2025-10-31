# Guía de Optimizaciones de Rendimiento v2.9.1

## Descripción General

Este documento describe las optimizaciones implementadas para mejorar el rendimiento del algoritmo de asignación de guardias, especialmente en la Fase 2.1 (pre-asignación equitativa por rondas).

**Versión**: 2.9.1  
**Fecha**: 31 de octubre de 2025  
**Archivo**: `src/services/optimizaciones_asignador.py`

---

## 🚀 Mejoras de Rendimiento

### Problema Original

En la implementación anterior, la Fase 2.1 tenía un cuello de botella en la verificación de slots ocupados:

```python
# LENTO: O(n) por cada slot
slot_zona_asignado = any(
    g.fecha == slot.fecha and g.turno == slot.turno and
    g.recreo == slot.recreo_id and g.zona_id == slot.zona_id
    for g in calendario
)
```

Con **2768 guardias** y **~100 rondas**, esto resultaba en:
- **2768 slots × 100 rondas × 2768 comparaciones** = ~765 millones de operaciones
- Tiempo estimado: **varios minutos** en la Fase 2.1

### Soluciones Implementadas

| Optimización | Mejora | Complejidad |
|--------------|--------|-------------|
| **Índice de slots** | Set de claves únicas | O(n) → O(1) |
| **Caché de elegibilidad** | Reuso de resultados | O(n×m) → O(1) cached |
| **Pre-filtrado** | Reduce conjunto de búsqueda | O(n) → O(n/k) |
| **Batch processing** | Agrupa operaciones | Mejor cache locality |

**Resultado esperado**: Reducción del **80-90%** en tiempo de Fase 2.1

---

## 📦 Componentes

### 1. `IndiceSlots`

Índice hash de slots ocupados para búsquedas instantáneas.

#### Uso

```python
from services.optimizaciones_asignador import IndiceSlots

# Crear índice vacío
indice = IndiceSlots()

# O crear desde calendario existente
indice = IndiceSlots.desde_calendario(calendario)

# Marcar slot ocupado (O(1))
indice.marcar_ocupado(fecha, turno, recreo, zona_id)

# Verificar si está ocupado (O(1))
if not indice.esta_ocupado(fecha, turno, recreo, zona_id):
    # Slot disponible
    asignar_guardia(...)
    indice.marcar_ocupado(fecha, turno, recreo, zona_id)

# Estadísticas
print(f"Slots ocupados: {indice.total_ocupados()}")
```

#### Benchmarks

```
Operación:        | Original (O(n)) | Optimizado (O(1)) | Speedup
-----------------------------------------------------------------
Verificar slot    | 2768 comp/op    | 1 comp/op         | 2768x
100 verificaciones| 276,800 comp    | 100 comp          | 2768x
```

---

### 2. `FiltroProfesores`

Pre-filtrado de profesores por características para evitar evaluaciones innecesarias.

#### Uso

```python
from services.optimizaciones_asignador import FiltroProfesores

# Crear filtro (indexa profesores por turno/zona)
filtro = FiltroProfesores(profesores)

# Obtener solo profesores de mañana (O(1))
profs_manana = filtro.por_turno("mañana")

# Obtener solo profesores de zona 1 (O(1))
profs_zona1 = filtro.por_zona_preferida(1)

# Filtrar por cuota (evita profesores que ya cumplieron)
candidatos = filtro.filtrar_por_cuota(
    profesores=profs_manana,
    asignadas=asignadas,
    cuotas=cuotas_ideales,
    maximo=None  # No limitar máximo
)
```

#### Beneficios

- **Reduce conjunto de búsqueda**: En lugar de evaluar 75 profesores, solo evaluar ~20 del turno correcto
- **Pre-índices**: Búsquedas O(1) en lugar de O(n)
- **Filtrado inteligente**: Evita profesores que ya cumplieron cuota

---

### 3. `CacheElegibilidad`

Caché de resultados de elegibilidad para slots similares.

#### Uso

```python
from services.optimizaciones_asignador import CacheElegibilidad

cache = CacheElegibilidad()

# Intentar obtener de caché
elegibles = cache.obtener(fecha, turno, recreo, zona_id)

if elegibles is None:
    # Cache miss - calcular
    elegibles = calcular_profesores_elegibles(...)
    cache.guardar(fecha, turno, recreo, zona_id, elegibles)
else:
    # Cache hit - usar resultado cacheado
    pass

# Estadísticas
stats = cache.estadisticas()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")

# Limpiar caché si cambian asignaciones
cache.limpiar()
```

#### Cuándo Usar

✅ **Usar caché cuando**:
- Procesamiento en batch (mismos slots repetidos)
- Asignaciones no han cambiado recientemente
- Muchos slots similares (mismo turno/recreo)

❌ **NO usar caché cuando**:
- Asignaciones cambian constantemente
- Slots muy heterogéneos
- Poca repetición de patrones

---

### 4. Funciones Auxiliares

#### `agrupar_slots_por_fecha()`

Agrupa slots por fecha para procesamiento en batch.

```python
from services.optimizaciones_asignador import agrupar_slots_por_fecha
from datetime import date

grupos = agrupar_slots_por_fecha(
    slots=todos_los_slots,
    fecha_inicio=date(2025, 9, 8),
    fecha_fin=date(2025, 12, 31)
)

# Procesar por fecha
for fecha, slots_del_dia in grupos.items():
    print(f"{fecha}: {len(slots_del_dia)} slots")
    # Procesar todos los slots del mismo día juntos
```

**Ventajas**:
- Mejor cache locality (datos del mismo día juntos)
- Permite paralelización por fecha
- Facilita reporting progresivo

---

#### `ordenar_profesores_equitativamente()`

Ordena profesores priorizando equidad y eficiencia.

```python
from services.optimizaciones_asignador import ordenar_profesores_equitativamente

profesores_ordenados = ordenar_profesores_equitativamente(
    profesores=candidatos,
    asignadas=asignadas,
    cuotas=cuotas_ideales,
    zona_actual=zona_id  # Prioriza profesores de esta zona
)

# Primeros = menos guardias asignadas (más equitativo)
# Si empate, primero los de zona preferida = zona_actual
```

**Criterios de ordenación**:
1. Ratio `asignadas/cuota` (menor = más prioritario)
2. Zona preferida coincide con zona actual (sí = más prioritario)
3. ID del profesor (determinismo)

---

#### `validar_indices()`

Valida sincronización entre índice y calendario (debugging).

```python
from services.optimizaciones_asignador import validar_indices

# Verificar consistencia
if not validar_indices(indice_slots, calendario):
    logger.error("¡Índice desincronizado!")
    # Reconstruir índice
    indice_slots = IndiceSlots.desde_calendario(calendario)
```

---

#### `estadisticas_rendimiento()`

Recopila métricas de rendimiento.

```python
from services.optimizaciones_asignador import estadisticas_rendimiento

stats = estadisticas_rendimiento(
    indice_slots=indice,
    cache_elegibilidad=cache,
    total_slots=2768
)

logger.info(f"Cobertura: {stats['cobertura']:.2f}%")
logger.info(f"Cache hit rate: {stats['hit_rate']:.1f}%")
```

---

## 🔧 Integración con Algoritmo Actual

### Ejemplo de Uso en Fase 2.1

```python
from services.optimizaciones_asignador import (
    IndiceSlots,
    FiltroProfesores,
    ordenar_profesores_equitativamente
)

def asignar_guardias_optimizado(profesores, slots_ordenados, ...):
    # 1. Crear índice de slots ocupados
    indice_slots = IndiceSlots.desde_calendario(calendario)
    
    # 2. Crear filtro de profesores
    filtro = FiltroProfesores(profesores)
    
    # 3. Pre-asignación por rondas (OPTIMIZADA)
    logger.info("FASE 2.1: Pre-asignación equitativa por rondas (OPTIMIZADA)")
    
    ronda = 0
    max_rondas = max(cuotas_ideales.values())
    
    while ronda < max_rondas:
        ronda += 1
        asignaciones_ronda = 0
        
        # Obtener profesores del turno/zona apropiados
        for prof in profesores_prioritarios:
            # Verificaciones de cuota
            if asignadas[prof.id] >= cuotas_ideales[prof.id]:
                continue
            if asignadas[prof.id] >= ronda:
                continue
            
            # Buscar slot compatible
            for slot in slots_ordenados:
                # OPTIMIZACIÓN: Usar índice O(1) en lugar de any() O(n)
                if indice_slots.esta_ocupado(
                    slot.fecha, slot.turno, slot.recreo_id, slot.zona_id
                ):
                    continue  # Slot ocupado
                
                # Verificar elegibilidad
                if es_elegible(prof, slot, ...):
                    # Asignar
                    guardia = _registrar_guardia(...)
                    
                    # CRÍTICO: Actualizar índice
                    indice_slots.marcar_ocupado(
                        slot.fecha, slot.turno, slot.recreo_id, slot.zona_id
                    )
                    
                    asignaciones_ronda += 1
                    break  # Siguiente profesor
        
        if asignaciones_ronda == 0:
            break  # No hay más asignaciones posibles
    
    logger.info(f"✓ {ronda} rondas completadas con optimizaciones")
```

### Modificaciones Requeridas

1. **Inicializar estructuras optimizadas** al inicio de `generar_guardias()`
2. **Reemplazar verificación `any()`** por `indice_slots.esta_ocupado()`
3. **Actualizar índice** después de cada asignación con `marcar_ocupado()`
4. **Usar FiltroProfesores** para pre-filtrar candidatos por turno
5. **Ordenar con `ordenar_profesores_equitativamente()`** antes de cada ronda

---

## 📊 Resultados Esperados

### Tiempos Estimados (75 profesores, 2768 guardias)

| Fase | Antes | Después | Mejora |
|------|-------|---------|--------|
| Fase 2.1 (100 rondas) | ~5-8 min | ~30-60 seg | **83-88%** |
| Fase 2.2 (masiva) | ~2-3 min | ~1-2 min | **33-50%** |
| Fase 3 (CSP) | ~1 min | ~45 seg | **25%** |
| **TOTAL** | **~8-12 min** | **~2.5-4 min** | **~67-75%** |

### Métricas de Cache

Con **2768 slots** y **4 recreos**, esperamos:
- **Hit rate**: 40-60% (slots similares reutilizan cálculos)
- **Memoria adicional**: ~1-2 MB (insignificante)
- **Speedup en hits**: 10-100x (evita re-cálculo completo)

---

## ⚠️ Consideraciones

### Sincronización Crítica

**IMPORTANTE**: El índice debe mantenerse sincronizado con el calendario.

```python
# ✅ CORRECTO
calendario.append(guardia)
indice_slots.marcar_ocupado(fecha, turno, recreo, zona_id)

# ❌ INCORRECTO (desincronización)
calendario.append(guardia)
# Olvidamos actualizar el índice!
```

### Uso de Memoria

Las optimizaciones añaden **mínima overhead** de memoria:

- `IndiceSlots`: ~50 KB (2768 slots × ~20 bytes/slot)
- `FiltroProfesores`: ~10 KB (75 profesores × índices)
- `CacheElegibilidad`: ~100-500 KB (depende de hit rate)

**Total**: <1 MB adicional

### Thread-Safety

**NOTA**: Las estructuras NO son thread-safe. Si se paraleliza en el futuro, usar locks o estructuras thread-safe.

---

## 🧪 Testing

### Test de Validación

```python
def test_indice_slots_sincronizacion():
    """Verificar que IndiceSlots se mantiene sincronizado."""
    from services.optimizaciones_asignador import IndiceSlots, validar_indices
    
    calendario = []
    indice = IndiceSlots()
    
    # Asignar 100 guardias
    for i in range(100):
        guardia = crear_guardia_test(i)
        calendario.append(guardia)
        indice.marcar_ocupado(
            guardia.fecha, guardia.turno, guardia.recreo, guardia.zona_id
        )
    
    # Verificar sincronización
    assert validar_indices(indice, calendario)
    assert indice.total_ocupados() == len(calendario)
```

### Benchmark Comparativo

```python
import time

def benchmark_verificacion_slots():
    """Comparar rendimiento original vs optimizado."""
    calendario = generar_calendario_test(2768)
    
    # Original (any con lista)
    start = time.time()
    for _ in range(10000):
        ocupado = any(
            g.fecha == test_fecha and g.recreo == test_recreo
            for g in calendario
        )
    tiempo_original = time.time() - start
    
    # Optimizado (IndiceSlots)
    indice = IndiceSlots.desde_calendario(calendario)
    start = time.time()
    for _ in range(10000):
        ocupado = indice.esta_ocupado(test_fecha, turno, test_recreo, zona)
    tiempo_optimizado = time.time() - start
    
    speedup = tiempo_original / tiempo_optimizado
    print(f"Speedup: {speedup:.1f}x")
    assert speedup > 100  # Esperamos >100x
```

---

## 🔜 Próximos Pasos

1. **Integrar optimizaciones** en `asignador_guardias.py`
2. **Ejecutar tests** de regresión (equidad debe mantenerse)
3. **Benchmark real** con datos de producción (BD 66f06c9433d74e80)
4. **Documentar resultados** en CHANGELOG
5. **Considerar optimizaciones adicionales**:
   - Paralelización de Fase 2.2 por fecha
   - Índice de ausencias por fecha (pre-cálculo)
   - Cache de restricciones de horario

---

## 📚 Referencias

- **Algoritmo base**: v2.9 (equidad perfecta por rondas)
- **Documento técnico**: `ESPECIFICACION_CALCULO_GUARDIAS.md`
- **Changelog**: `CHANGELOG_v2.9.1.md`
- **Código**: `src/services/asignador_guardias.py`
- **Optimizaciones**: `src/services/optimizaciones_asignador.py`

---

**Autor**: Sistema de Guardias de Patio  
**Versión**: 2.9.1  
**Fecha**: 31 de octubre de 2025
