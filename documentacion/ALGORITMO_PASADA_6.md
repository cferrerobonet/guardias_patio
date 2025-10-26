# Algoritmo de Asignación de Guardias - Pasada 6

## Objetivo

Garantizar que **todos los profesores elegibles** reciban **al menos una guardia** asignada, además de cubrir el máximo número de slots posibles.

## ¿Qué es un Profesor Elegible?

Un profesor se considera elegible para recibir guardias si cumple **todos** estos criterios:

1. **Tiene cuota > 0**: Su cuota de guardias configurada es mayor que cero
2. **Tiene zonas asignadas**: Tiene al menos una zona de vigilancia asignada
3. **Está disponible**: No tiene ausencias que cubran todo el período del curso

## Problema que Resuelve

Antes de la Pasada 6, el algoritmo priorizaba:
1. ✅ Cubrir el máximo número de slots (ranuras de guardias)
2. ✅ Equilibrar la carga entre profesores
3. ❌ **No garantizaba** que todos los profesores elegibles recibieran al menos una guardia

Esto podía resultar en situaciones donde:
- Todos los slots estaban cubiertos (100% de cobertura)
- Pero algunos profesores con cuota > 0 quedaban sin ninguna guardia asignada
- La carga se concentraba en un subconjunto de profesores

## Solución: Pasada 6 (96% - 98% del progreso)

### Estrategia

La Pasada 6 se ejecuta **después** de las 5 pasadas principales de asignación y utiliza una estrategia de **swapping inteligente**:

1. **Identificar profesores sin guardias**:
   - Recorrer todos los profesores
   - Filtrar aquellos que:
     - Tienen `cuota > 0`
     - Tienen `len(zonas) > 0`
     - Tienen `asignadas[profesor_id] == 0`

2. **Para cada profesor sin guardias**:
   - Buscar una guardia ya asignada donde este profesor **puede** hacer guardia
   - Verificar que cumpla todas las restricciones:
     - Turno compatible
     - Zona asignada
     - No está ausente
     - No tiene otra guardia ese mismo día
     - Recreos permitidos, etc.

3. **Realizar swap (intercambio)**:
   - Si se encuentra un slot compatible:
     - Buscar otro slot donde el profesor actual pueda ser reasignado
     - Si existe ese slot alternativo:
       - ✅ **Reasignar** el slot original al profesor sin guardias
       - ✅ **Actualizar** todos los contadores y tracking
       - ✅ **Incrementar** el contador de profesores asignados en Pasada 6

4. **Registrar resultados**:
   - Logs informativos de cada swap exitoso
   - Warnings para profesores que no pudieron ser asignados
   - Estadísticas finales de distribución

### Flujo de la Pasada 6

```
┌─────────────────────────────────────┐
│  Identificar Profesores Sin Guardias│
│  (cuota>0, zonas>0, asignadas=0)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Para cada profesor sin guardias:   │
│  ┌──────────────────────────────┐  │
│  │ Buscar guardia compatible    │  │
│  │ en calendario existente      │  │
│  └──────────┬───────────────────┘  │
│             │                        │
│             ▼                        │
│  ┌──────────────────────────────┐  │
│  │ ¿Profesor puede hacer        │  │
│  │ esta guardia?                │  │
│  └──────────┬───────────────────┘  │
│             │                        │
│        SÍ   ▼   NO                  │
│  ┌──────────────────┐               │
│  │ Buscar slot      │   (siguiente  │
│  │ alternativo para │    guardia)   │
│  │ profesor actual  │               │
│  └────┬─────────────┘               │
│       │                              │
│  ¿Existe slot alternativo?          │
│       │                              │
│   SÍ  ▼  NO                         │
│  ┌─────────────┐                    │
│  │ SWAP        │  (siguiente        │
│  │ EXITOSO!    │   guardia)         │
│  │             │                    │
│  │ 1. Reasignar│                    │
│  │ 2. Actualizar│                   │
│  │ 3. Log      │                    │
│  └─────────────┘                    │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Estadísticas Finales:              │
│  - Profesores asignados en Pasada 6 │
│  - Profesores sin guardias (final)  │
│  - Distribución total               │
└─────────────────────────────────────┘
```

## Restricciones que se Respetan

Durante la Pasada 6, se respetan **todas** las restricciones de elegibilidad:

- ✅ Turnos compatibles (mañana/tarde/completo/mixto)
- ✅ Zonas asignadas al profesor
- ✅ Ausencias del profesor
- ✅ Días de la semana permitidos
- ✅ Recreos permitidos (matriz de horario)
- ✅ Fechas de inicio/fin de guardias
- ✅ **No múltiples guardias por día** (se mantiene la restricción)
- ✅ **No dos zonas simultáneas** (misma fecha + turno + recreo)

### Lo que NO se respeta:

- ❌ **Cuotas máximas**: Un profesor puede recibir más guardias de su cuota si eso permite dar al menos una guardia a alguien sin guardias

## Ejemplo de Funcionamiento

### Situación Inicial (Después de Pasada 5)

```
Profesor A: 15 guardias (cuota: 12) ✅
Profesor B: 12 guardias (cuota: 12) ✅
Profesor C: 10 guardias (cuota: 10) ✅
Profesor D:  0 guardias (cuota: 8)  ❌ Sin guardias!
Profesor E:  0 guardias (cuota: 6)  ❌ Sin guardias!

Total: 37/40 slots cubiertos
Cobertura: 92.5%
```

### Ejecución de Pasada 6

**Paso 1**: Identificar profesores sin guardias
- Profesor D (cuota 8, sin guardias)
- Profesor E (cuota 6, sin guardias)

**Paso 2**: Buscar slot para Profesor D
- Guardia del 15/10/2025, Recreo 1, Zona A → Asignada a Profesor A
- ¿Profesor D puede hacer esta guardia? ✅ Sí
- ¿Hay slot alternativo para Profesor A? ✅ Sí (17/10/2025, Recreo 2, Zona B)
- **SWAP EXITOSO**: 
  - Profesor D → 15/10/2025, Recreo 1, Zona A
  - Profesor A → 17/10/2025, Recreo 2, Zona B

**Paso 3**: Buscar slot para Profesor E
- Guardia del 20/10/2025, Recreo 1, Zona B → Asignada a Profesor B
- ¿Profesor E puede hacer esta guardia? ✅ Sí
- ¿Hay slot alternativo para Profesor B? ✅ Sí (22/10/2025, Recreo 1, Zona A)
- **SWAP EXITOSO**:
  - Profesor E → 20/10/2025, Recreo 1, Zona B
  - Profesor B → 22/10/2025, Recreo 1, Zona A

### Situación Final

```
Profesor A: 15 guardias (cuota: 12) ✅
Profesor B: 12 guardias (cuota: 12) ✅
Profesor C: 10 guardias (cuota: 10) ✅
Profesor D:  1 guardia  (cuota: 8)  ✅ Ahora tiene al menos una!
Profesor E:  1 guardia  (cuota: 6)  ✅ Ahora tiene al menos una!

Total: 39/40 slots cubiertos
Cobertura: 97.5%
Profesores con guardias: 5/5 (100%)
```

## Beneficios

1. ✅ **Equidad mejorada**: Todos los profesores elegibles participan en guardias
2. ✅ **Transparencia**: Ningún profesor puede quejarse de "no tener ninguna guardia"
3. ✅ **Flexibilidad**: Se mantienen todas las restricciones de seguridad
4. ✅ **Rendimiento**: Solo se ejecuta si hay profesores sin guardias
5. ✅ **Visibilidad**: Logs detallados de cada swap realizado

## Limitaciones

- Si un profesor tiene restricciones muy estrictas (ej: solo 1 día de la semana, solo 1 recreo, solo 1 zona) puede ser imposible asignarle una guardia
- La Pasada 6 intenta pero no **garantiza** al 100% - depende de la compatibilidad de restricciones
- Si no hay slots compatibles, el profesor seguirá sin guardias (con warning en logs)

## Logs y Monitoreo

La Pasada 6 genera logs detallados:

```
INFO: Iniciando PASADA 6: Garantizar que todos los profesores elegibles...
INFO: Encontrados 2 profesores sin guardias asignadas
INFO: Swap para Juan Pérez: María García movido
INFO: Swap para Ana López: Pedro Martínez movido
INFO: Pasada 6: 2 profesores sin guardias ahora tienen al menos una
INFO: Profesores con guardias: 75/75
```

Si hay profesores que no pudieron ser asignados:

```
WARNING: No se pudo asignar guardia a Carlos Ruiz
WARNING: Profesores elegibles sin guardias: Carlos Ruiz, Elena Torres
```

## Integración con el Sistema

La Pasada 6 es **transparente** para el usuario final:
- Se ejecuta automáticamente después de la Pasada 5
- Reporta progreso (96% - 98%)
- No requiere configuración adicional
- Funciona con cualquier configuración de profesores/zonas/recreos

## Conclusión

La Pasada 6 convierte el algoritmo de asignación de guardias en un sistema que prioriza:

1. **Primero**: Cubrir todos los slots posibles (Pasadas 1-5)
2. **Segundo**: Garantizar que nadie quede excluido (Pasada 6)

Esto asegura tanto la **cobertura** como la **equidad** en la distribución de guardias.
