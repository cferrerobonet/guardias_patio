# Guía Rápida: Probar Algoritmo v3.0 Simple Determinista

**Fecha**: 2025-01-31  
**Versión**: v3.0  
**Autor**: GitHub Copilot

---

## 🎯 Objetivo

Probar el nuevo **algoritmo v3.0 Simple Determinista** y comparar sus resultados con el algoritmo v2.9 clásico.

---

## 📋 Prerrequisitos

✅ Migración Alembic ejecutada (`880e0e1ef795`)  
✅ Código actualizado (commits `93d3dc2` y `0cbff3f`)  
✅ Datos de configuración existentes (profesores, zonas, recreos)

---

## 🚀 Pasos para Probar

### 1. **Abrir la Aplicación**

```bash
cd "/Users/cferrerobonet/Documents/04 DESARROLLADOR/Python/Guardias de patio"
/opt/homebrew/bin/python3.11 src/main.py
```

---

### 2. **Ir a Configuración**

1. Menú: **Configuración** → **Configuración del Curso**
2. Scroll hasta **🔧 Ajustes Adicionales**
3. Verás el nuevo selector:

```
Algoritmo de asignación:
[v2.9 - Clásico (7 fases)        ▼]
```

---

### 3. **Probar con v2.9 (Baseline)**

1. Asegúrate de que esté seleccionado: **v2.9 - Clásico (7 fases)**
2. Guarda la configuración
3. Ve a **Guardias** → **Generar Calendario**
4. Genera guardias
5. **Anota los resultados**:
   - Total de guardias generadas: `______`
   - % Cobertura: `______%`
   - Slots vacíos: `______`
   - Tiempo de generación: `______ segundos`
6. Ve a **Guardias** → **Vista Calendario**
7. **Revisa visualmente**:
   - ¿Hay slots sin rellenar? ❌ / ✅
   - ¿Profesores sin guardias? ❌ / ✅

---

### 4. **Probar con v3.0 (Nuevo)**

1. **IMPORTANTE**: Elimina las guardias existentes:
   - Ve a **Guardias** → **Generar Calendario**
   - Confirma eliminar guardias existentes
   - O usa SQL:
     ```sql
     DELETE FROM guardia;
     ```

2. Ve a **Configuración** → **Configuración del Curso**

3. Cambia el selector a: **v3.0 - Simple Determinista ⚡**

4. **Lee el tooltip** (pasa el mouse sobre el selector):
   ```
   v2.9: Algoritmo clásico de 7 fases (CSP, Simulated Annealing)
   v3.0: Algoritmo simple determinista que garantiza 100% cobertura
   ```

5. Guarda la configuración

6. Ve a **Guardias** → **Generar Calendario**

7. Genera guardias

8. **Observa el progreso**:
   ```
   PASO 1 (0-10%): Calcular cuotas por profesor
   PASO 2 (10-20%): Generar todos los slots disponibles
   PASO 3 (20-30%): Calcular prioridades y ordenar profesores
   PASO 4 (30-90%): Asignar guardias profesor por profesor
   PASO 5 (90-100%): Validación y estadísticas
   ```

9. **Anota los resultados**:
   - Total de guardias generadas: `______`
   - % Cobertura: `______%`
   - Slots vacíos: `______`
   - Tiempo de generación: `______ segundos`

10. Ve a **Guardias** → **Vista Calendario**

11. **Revisa visualmente**:
    - ¿Hay slots sin rellenar? ❌ / ✅
    - ¿Profesores sin guardias? ❌ / ✅

---

## 📊 Tabla de Comparación

| Métrica | v2.9 Clásico | v3.0 Simple | Mejor |
|---------|--------------|-------------|-------|
| **Guardias generadas** | ______ | ______ | _____ |
| **% Cobertura** | ______% | ______% | _____ |
| **Slots vacíos** | ______ | ______ | _____ |
| **Tiempo (segundos)** | ______ | ______ | _____ |
| **Slots sin rellenar** | ❌ / ✅ | ❌ / ✅ | _____ |
| **Profesores sin guardias** | ❌ / ✅ | ❌ / ✅ | _____ |

---

## 🔍 Qué Esperar

### **Si todo funciona correctamente:**

#### v2.9 Clásico:
- ✅ Genera guardias rápidamente
- ⚠️ Puede dejar algunos slots vacíos
- ⚠️ Algunos profesores pueden quedar sin guardias
- ✅ Buen balance general

#### v3.0 Simple:
- ✅ Genera guardias garantizando 100% cobertura*
- ✅ TODOS los slots cubiertos
- ✅ TODOS los profesores con su cuota exacta
- ✅ Determinista (mismo resultado siempre)
- ✅ Más rápido (una sola pasada)

*Si hay suficientes profesores y las restricciones lo permiten

---

## 🐛 Problemas Posibles y Soluciones

### **Problema 1: Selector no aparece**
**Causa**: Migración no ejecutada  
**Solución**:
```bash
cd "/Users/cferrerobonet/Documents/04 DESARROLLADOR/Python/Guardias de patio"
/opt/homebrew/bin/python3.11 -m alembic upgrade head
```

---

### **Problema 2: Error al generar con v3.0**
**Causa**: Falta algún dato en configuración  
**Solución**:
1. Revisa logs en: `logs/guardias_patio.log`
2. Busca líneas con `[ERROR]` o `[WARNING]`
3. Verifica:
   - ¿Hay profesores activos?
   - ¿Hay zonas configuradas?
   - ¿Hay recreos configurados?

---

### **Problema 3: v3.0 no cubre 100%**
**Causa**: Restricciones imposibles de satisfacer  
**Indicios**:
```
⚠️  Profesor X no pudo completar su cuota (asignadas: Y de Z)
⚠️  Slots vacíos: N
```

**Solución**:
1. Revisa ausencias: ¿Hay profesores con muchas ausencias?
2. Revisa restricciones de horario: ¿Profesores solo disponibles en mañana/tarde?
3. Aumenta el número de profesores
4. O usa v2.9 que es más flexible

---

## 📝 Notas de los Logs

El algoritmo v3.0 genera logs muy detallados:

```
INFO  [services.asignador_guardias_v3_simple] 🔧 PASO 1: Calcular cuotas
INFO  [services.asignador_guardias_v3_simple]   Profesor Juan (ID=1): cuota=15 guardias
INFO  [services.asignador_guardias_v3_simple]   Profesor María (ID=2): cuota=18 guardias
...
INFO  [services.asignador_guardias_v3_simple] 🔧 PASO 4: Asignar guardias
INFO  [services.asignador_guardias_v3_simple]   Profesor Juan: 15/15 ✅
INFO  [services.asignador_guardias_v3_simple]   Profesor María: 18/18 ✅
...
INFO  [services.asignador_guardias_v3_simple] ✅ PASO 5: Validación
INFO  [services.asignador_guardias_v3_simple]   Total asignado: 350 guardias
INFO  [services.asignador_guardias_v3_simple]   Cobertura: 100.0%
INFO  [services.asignador_guardias_v3_simple]   Slots vacíos: 0
```

---

## 🎯 Criterios de Éxito

### **El v3.0 es exitoso si:**

✅ **Cobertura 100%** (o muy cercana)  
✅ **0 slots vacíos** (o muy pocos)  
✅ **Todos los profesores con guardias**  
✅ **Cuotas equitativas** (desviación estándar < 2)  
✅ **Tiempo < 60 segundos**  

### **Comparado con v2.9:**

✅ **Más cobertura** (v3.0 ≥ v2.9)  
✅ **Menos slots vacíos** (v3.0 ≤ v2.9)  
✅ **Más equitativo** (desviación v3.0 ≤ v2.9)  

---

## 📊 Análisis de Equidad

Para analizar la equidad de la distribución:

```sql
-- Ver distribución de guardias por profesor
SELECT 
    p.nombre,
    COUNT(g.id) as total_guardias,
    COUNT(DISTINCT g.fecha) as dias_con_guardia
FROM profesor p
LEFT JOIN guardia g ON g.profesor_id = p.id
GROUP BY p.id, p.nombre
ORDER BY total_guardias;
```

**Interpretación**:
- **Ideal**: Todos los profesores con número similar de guardias
- **Problema**: Algunos con 0, otros con muchas

---

## 🔄 Cambiar Entre Algoritmos

Puedes cambiar de algoritmo en cualquier momento:

1. Ve a **Configuración** → **Configuración del Curso**
2. Cambia el selector
3. Guarda
4. **Elimina guardias existentes**
5. Regenera

**IMPORTANTE**: Siempre elimina guardias antes de regenerar para evitar duplicados.

---

## 📚 Más Información

- **Propuesta original**: `documentacion/tecnico/PROPUESTA_ALGORITMO_SIMPLE.md`
- **Integración completa**: `documentacion/tecnico/INTEGRACION_ALGORITMO_V3.md`
- **Código v3.0**: `src/services/asignador_guardias_v3_simple.py`
- **Código v2.9**: `src/services/asignador_guardias.py`

---

## 🎉 Siguiente Paso

Si el v3.0 funciona bien:

1. ✅ Úsalo como default en futuras configuraciones
2. ✅ Compila una nueva versión (v3.0.0)
3. ✅ Actualiza el manual de usuario
4. ✅ Documenta las diferencias para los usuarios finales

Si el v2.9 funciona mejor en algunos casos:

1. ✅ Mantén ambos algoritmos disponibles
2. ✅ Documenta cuándo usar cada uno
3. ✅ Añade recomendaciones en la UI

---

## 💡 Recomendaciones Generales

### **Usa v2.9 si:**
- Tienes muchas restricciones complejas
- Prefieres flexibilidad sobre cobertura 100%
- El tiempo no es crítico

### **Usa v3.0 si:**
- Necesitas 100% cobertura
- Quieres resultados predecibles
- Prefieres simplicidad y rapidez
- Necesitas debuggear fácilmente

---

¡Buena suerte probando el nuevo algoritmo! 🚀
