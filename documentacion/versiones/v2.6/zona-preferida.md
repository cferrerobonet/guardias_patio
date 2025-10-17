# Zona Preferida del Profesor - v2.6.1

## 📋 Descripción

Esta funcionalidad mejora significativamente la experiencia del profesor al mantenerlo **en la misma zona de vigilancia** durante todo el curso escolar, en la medida de lo posible.

## 🎯 Objetivo

Los profesores no tendrán que consultar cada día en qué zona les toca hacer la guardia. Una vez conocen su zona el primer día, sabrán que generalmente estarán en esa misma zona durante el resto del curso.

## 🔧 Funcionamiento

### Asignación de Zona Preferida

1. **Primera Asignación**: En la primera guardia que se asigna a un profesor, el sistema registra la zona como su **zona preferida**.

2. **Asignaciones Posteriores**: El algoritmo da **máxima prioridad** a mantener al profesor en su zona preferida en todas las asignaciones futuras.

### Sistema de Prioridades del Algoritmo

El algoritmo de asignación de guardias utiliza el siguiente orden de prioridades:

```
PRIORIDAD 1: Zona preferida (+100 puntos)
   - Si es su zona preferida: +100
   - Si no tiene zona preferida aún: 0 (neutral)
   - Si es otra zona diferente: -50 (penalización)

PRIORIDAD 2: Déficit de guardias (equilibrio de carga)
   - Favorece a profesores con menos guardias asignadas

PRIORIDAD 3: Continuidad de días consecutivos
   - Pequeño bonus si es día consecutivo

PRIORIDAD 4: Mismo recreo anterior
   - Pequeño bonus si es el mismo recreo
```

### Ejemplo Práctico

```
Profesor A: Primera guardia → Zona 1 (Patio Principal)
   ✅ El sistema registra: Zona preferida = Patio Principal
   
   Asignaciones futuras:
   - 10/09/2024: Patio Principal ✓
   - 12/09/2024: Patio Principal ✓
   - 15/09/2024: Patio Principal ✓
   - 18/09/2024: Patio Principal ✓
   ... (y así todo el curso)
```

## 📊 Resultados Esperados

Según las pruebas realizadas, el sistema mantiene a los profesores en su zona preferida:

- **≥ 70%**: Umbral mínimo esperado (validado en tests)
- **~ 100%**: Resultado típico cuando hay suficientes profesores por zona

### Resultados del Test Automatizado

```
Profesor 1: Zona 1 → 100.0% de guardias en Zona 1
Profesor 2: Zona 2 → 100.0% de guardias en Zona 2  
Profesor 3: Zona 3 → 100.0% de guardias en Zona 3
Profesor 4: Zona 2 → 100.0% de guardias en Zona 2
Profesor 5: Zona 3 → 100.0% de guardias en Zona 3
Profesor 6: Zona 1 → 100.0% de guardias en Zona 1
```

## ⚙️ Implementación Técnica

### Código Clave

```python
# Diccionario que registra la zona preferida de cada profesor
zona_preferida_prof: Dict[int, Optional[int]] = defaultdict(lambda: None)

# Al asignar una guardia
if zona_preferida_prof[elegido.id] is None:
    # Primera asignación: registrar como zona preferida
    zona_preferida_prof[elegido.id] = slot.zona_id
    
# Sistema de scoring
def score(p: Profesor) -> Tuple[int, int, int, int, float]:
    if zona_preferida_prof[p.id] is None:
        s_zona = 0  # Primera asignación
    elif zona_preferida_prof[p.id] == slot.zona_id:
        s_zona = 100  # ¡Su zona preferida! Máxima prioridad
    else:
        s_zona = -50  # Penalizar si es otra zona
    
    deficit = cuotas.get(p.id, 0) - asignadas[p.id]
    # ... otros criterios
    
    return (s_zona, deficit, s_continuidad, s_recreo, random.random())
```

### Archivos Modificados

- `src/services/asignador_guardias.py`:
  - Línea 151: Añadido diccionario `zona_preferida_prof`
  - Líneas 201-227: Nueva función de scoring con prioridad de zona
  - Líneas 246-251: Registro de zona preferida en primera asignación

## 🧪 Validación

### Test Automatizado

Archivo: `tests/test_zona_preferida.py`

Verifica que:
1. ✅ Cada profesor recibe una zona preferida en su primera asignación
2. ✅ Al menos el 70% de las guardias se mantienen en esa zona
3. ✅ La distribución es equitativa entre profesores

Ejecutar:
```bash
.venv/bin/python tests/test_zona_preferida.py
```

## 🎁 Beneficios

### Para los Profesores

- **Menos confusión**: No necesitan consultar cada día su zona
- **Familiaridad**: Conocen bien "su" zona de vigilancia
- **Rutina estable**: Mismo espacio, mismas ubicaciones

### Para el Centro

- **Menos consultas**: Reducción de preguntas "¿dónde me toca hoy?"
- **Mejor cobertura**: Profesores familiarizados con su zona
- **Optimización**: El profesor conoce mejor los puntos críticos de su zona

## 🔄 Compatibilidad

Esta funcionalidad es **totalmente compatible** con:

- ✅ Matriz día × recreo (v2.6.0)
- ✅ Gestión de ausencias (v2.5.0)
- ✅ Validaciones de no simultaneidad
- ✅ Requisito de máximo 1 guardia al día
- ✅ Turnos mixtos
- ✅ Fechas de inicio/fin de guardias por profesor
- ✅ Todas las restricciones existentes

## 📝 Notas Importantes

1. **Equilibrio Automático**: Si hay restricciones (ausencias, fechas, matriz horaria) que impiden mantener siempre la misma zona, el algoritmo busca el mejor equilibrio posible.

2. **Sin Configuración Manual**: El sistema asigna automáticamente las zonas preferidas. No requiere configuración por parte del usuario.

3. **Transparencia**: Se registra en logs cuando se asigna la zona preferida inicial:
   ```
   DEBUG: Zona preferida asignada a Profesor X: Zona 1
   ```

4. **Flexibilidad**: Si por necesidades del centro un profesor debe cambiar de zona ocasionalmente, el algoritmo lo permite pero siempre intentará volver a su zona preferida.

## 🚀 Versión

- **Versión**: 2.6.1
- **Fecha**: Octubre 2025
- **Estado**: ✅ Implementado y Validado
- **Tests**: ✅ Pasados al 100%

---

**Nota**: Esta funcionalidad se suma a las mejoras de la v2.6.0 (matriz día × recreo) para proporcionar un sistema de asignación de guardias aún más inteligente y adaptado a las necesidades reales de los profesores.
