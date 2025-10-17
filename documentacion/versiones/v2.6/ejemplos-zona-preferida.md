# 💡 Ejemplos Prácticos - Zona Preferida del Profesor

## Ejemplo 1: Caso Simple - 3 Zonas, 6 Profesores

### Configuración del Centro

```
Zonas disponibles:
  - Zona 1: Patio Principal
  - Zona 2: Patio Infantil  
  - Zona 3: Polideportivo

Profesores:
  - Ana García
  - Juan Pérez
  - María López
  - Carlos Ruiz
  - Laura Martín
  - Pedro Sánchez
```

### Primera Semana (Asignación Inicial)

**Lunes 02/09/2024 - Recreo 1**

```
Patio Principal:     Ana García     ← Zona preferida registrada
Patio Infantil:      Juan Pérez     ← Zona preferida registrada
Polideportivo:       María López    ← Zona preferida registrada
```

**Martes 03/09/2024 - Recreo 1**

```
Patio Principal:     Carlos Ruiz    ← Zona preferida registrada
Patio Infantil:      Laura Martín   ← Zona preferida registrada
Polideportivo:       Pedro Sánchez  ← Zona preferida registrada
```

### Resto del Curso (Mantenimiento de Zonas)

**Miércoles 04/09/2024 - Recreo 1**

```
Patio Principal:     Ana García     ✓ (su zona preferida)
Patio Infantil:      Juan Pérez     ✓ (su zona preferida)
Polideportivo:       María López    ✓ (su zona preferida)
```

**Jueves 05/09/2024 - Recreo 1**

```
Patio Principal:     Carlos Ruiz    ✓ (su zona preferida)
Patio Infantil:      Laura Martín   ✓ (su zona preferida)
Polideportivo:       Pedro Sánchez  ✓ (su zona preferida)
```

**Viernes 06/09/2024 - Recreo 1**

```
Patio Principal:     Ana García     ✓ (su zona preferida)
Patio Infantil:      Juan Pérez     ✓ (su zona preferida)
Polideportivo:       María López    ✓ (su zona preferida)
```

### Resultado Final del Mes

```
Ana García:
  ✓ Zona preferida: Patio Principal
  ✓ 21 guardias → 21 en Patio Principal (100%)
  ✓ 0 guardias en otras zonas

Juan Pérez:
  ✓ Zona preferida: Patio Infantil
  ✓ 21 guardias → 21 en Patio Infantil (100%)
  ✓ 0 guardias en otras zonas

María López:
  ✓ Zona preferida: Polideportivo
  ✓ 21 guardias → 21 en Polideportivo (100%)
  ✓ 0 guardias en otras zonas

(Y así con todos los profesores...)
```

---

## Ejemplo 2: Con Ausencias

### Escenario

```
Profesor: Ana García
Zona preferida: Patio Principal
Ausencia: 15/09 - 20/09 (baja médica)
```

### Semana del 15 al 20 de Septiembre

**Lunes 15/09/2024**

```
Ana García está ausente
→ Sistema busca sustituto para Patio Principal
→ Carlos Ruiz (zona preferida: Patio Principal) disponible
→ Asignación: Carlos Ruiz a Patio Principal ✓

Resultado: Patio Principal cubierto por Carlos (que ya conoce la zona)
```

**Lunes 22/09/2024 (Ana regresa)**

```
Ana García disponible
→ Sistema asigna a Patio Principal (su zona preferida)
→ Ana vuelve a su zona habitual ✓

Resultado: Ana retoma su zona sin problemas
```

### Beneficio

- ✅ Ana mantiene su zona preferida antes y después de la ausencia
- ✅ El sustituto (Carlos) también conoce la zona
- ✅ Transición fluida sin confusión

---

## Ejemplo 3: Con Matriz Día × Recreo

### Configuración de Profesor

```
Profesor: Juan Pérez
Zona preferida: Patio Infantil
Restricción: Solo puede Lunes, Miércoles y Viernes en Recreo 1
```

**Matriz Configurada:**
```
Lunes     → Recreo 1 ✓, Recreo 2 ✗
Martes    → Recreo 1 ✗, Recreo 2 ✗
Miércoles → Recreo 1 ✓, Recreo 2 ✗
Jueves    → Recreo 1 ✗, Recreo 2 ✗
Viernes   → Recreo 1 ✓, Recreo 2 ✗
```

### Resultado del Algoritmo

**Lunes 02/09 - Recreo 1**
```
Patio Infantil: Juan Pérez ✓ (zona preferida + día permitido)
```

**Miércoles 04/09 - Recreo 1**
```
Patio Infantil: Juan Pérez ✓ (zona preferida + día permitido)
```

**Viernes 06/09 - Recreo 1**
```
Patio Infantil: Juan Pérez ✓ (zona preferida + día permitido)
```

### Beneficio

- ✅ Respeta la matriz día × recreo
- ✅ Mantiene zona preferida en días permitidos
- ✅ Juan solo vigila Lunes-Miércoles-Viernes en Patio Infantil

---

## Ejemplo 4: Turno Mixto

### Configuración de Profesor

```
Profesor: Laura Martín
Turno: Mixto
Horas mañana: 15
Horas tarde: 10
Zona preferida: Polideportivo
```

### Asignaciones

**Semana 1**

```
Lunes mañana:    Polideportivo (Laura) ✓
Martes tarde:    Polideportivo (Laura) ✓
Jueves mañana:   Polideportivo (Laura) ✓
```

**Semana 2**

```
Miércoles mañana: Polideportivo (Laura) ✓
Viernes tarde:    Polideportivo (Laura) ✓
```

### Beneficio

- ✅ Laura vigila en turnos mixtos (mañana Y tarde)
- ✅ Siempre en Polideportivo (su zona preferida)
- ✅ Sin confusión sobre "dónde" (solo sobre "cuándo")

---

## Ejemplo 5: Profesor Nuevo a Mitad de Curso

### Escenario

```
Fecha: 15 de Enero (mitad de curso)
Nuevo profesor: Roberto Torres
Zonas existentes:
  - Patio Principal: Ana, Carlos
  - Patio Infantil: Juan, Laura
  - Polideportivo: María, Pedro
```

### Primera Asignación de Roberto

**Lunes 15/01/2025 - Recreo 1**

```
Sistema analiza:
  - Patio Principal: 2 profesores asignados
  - Patio Infantil: 2 profesores asignados
  - Polideportivo: 2 profesores asignados
  
→ Todas equilibradas, elige aleatoriamente
→ Asigna: Patio Infantil
→ Registra: Zona preferida de Roberto = Patio Infantil
```

### Resto del Curso para Roberto

```
Martes 16/01:    Patio Infantil ✓
Miércoles 17/01: Patio Infantil ✓
Jueves 18/01:    Patio Infantil ✓
Viernes 19/01:   Patio Infantil ✓
...
(Todo el semestre en Patio Infantil)
```

### Beneficio

- ✅ Roberto aprende rápido UNA sola zona
- ✅ Se integra bien con Juan y Laura
- ✅ No tiene que aprender las 3 zonas

---

## Ejemplo 6: Centro Grande (30 Profesores, 4 Zonas)

### Configuración

```
Zonas:
  1. Patio Principal (Profesores 1-8)
  2. Patio Infantil (Profesores 9-16)
  3. Polideportivo (Profesores 17-24)
  4. Zona Exterior (Profesores 25-30)
```

### Distribución Automática

El algoritmo asigna automáticamente ~7-8 profesores por zona:

```
Patio Principal:
  ✓ Profesor 1, 2, 3, 4, 5, 6, 7, 8
  ✓ Cada uno siempre en Patio Principal

Patio Infantil:
  ✓ Profesor 9, 10, 11, 12, 13, 14, 15, 16
  ✓ Cada uno siempre en Patio Infantil

Polideportivo:
  ✓ Profesor 17, 18, 19, 20, 21, 22, 23, 24
  ✓ Cada uno siempre en Polideportivo

Zona Exterior:
  ✓ Profesor 25, 26, 27, 28, 29, 30
  ✓ Cada uno siempre en Zona Exterior
```

### Resultado Final del Curso

```
📊 Estadísticas:
  - 30 profesores
  - 4 zonas
  - ~180 días lectivos
  - ~7-8 profesores por zona

✅ Resultado:
  - Cada profesor: 95-100% en su zona preferida
  - Cero confusión sobre zonas
  - Sistema predecible y profesional
```

---

## Ejemplo 7: Cambio Excepcional de Zona

### Escenario Especial

```
Profesor: Ana García
Zona preferida: Patio Principal
Fecha: 20/03/2025

Situación:
  - Patio Principal: Ana y Carlos disponibles
  - Patio Infantil: Juan ausente, Laura ausente
  - Polideportivo: María, Pedro disponibles
```

### Decisión del Algoritmo

```
Análisis:
  1. Patio Infantil necesita cobertura urgente
  2. Ana es candidata (disponible)
  3. Scoring:
     - Zona preferida (Patio Principal): +100
     - Zona no preferida (Patio Infantil): -50
     - Déficit muy alto (necesita cubrirse): +80
     
  4. Total: -50 + 80 = +30 (positivo, puede asignarse)
  
→ Ana asignada excepcionalmente a Patio Infantil
```

**Día siguiente (21/03/2025)**

```
Situación:
  - Juan y Laura regresan
  - Patio Infantil: normal de nuevo
  
→ Ana vuelve a Patio Principal (su zona preferida) ✓
```

### Beneficio

- ✅ Sistema flexible ante necesidades excepcionales
- ✅ Prioriza zona preferida, pero no es rígido
- ✅ Vuelve a la normalidad automáticamente

---

## 🎯 Conclusiones de los Ejemplos

### Lo que hace el sistema:

1. ✅ **Asigna zona preferida** en primera guardia
2. ✅ **Mantiene consistencia** el resto del curso
3. ✅ **Respeta restricciones** (ausencias, matriz, fechas)
4. ✅ **Es flexible** cuando es necesario
5. ✅ **Recupera normalidad** automáticamente

### Lo que NO hace el sistema:

1. ❌ No requiere configuración manual
2. ❌ No fuerza zonas cuando hay restricciones
3. ❌ No rompe otras validaciones
4. ❌ No impacta rendimiento

---

**Versión**: 2.6.1  
**Fecha**: 17 de octubre de 2025
