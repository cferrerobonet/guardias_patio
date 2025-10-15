# Validaciones de Asignación de Guardias

## 🎯 Propósito
Este documento describe todas las validaciones implementadas en el sistema de asignación de guardias para garantizar la integridad de los datos y el cumplimiento de las reglas establecidas.

## 🔒 Validaciones Críticas (HARD CONSTRAINTS)

### 1. No simultaneidad de zonas
**Regla**: Un mismo profesor NO puede estar asignado a múltiples zonas al mismo tiempo.

**Criterio**: Mismo día + mismo turno + mismo recreo

**Justificación**: Es físicamente imposible que un profesor esté en dos lugares al mismo tiempo.

**Implementación**:
- Se mantiene un diccionario `guardias_por_slot_prof` con claves `(profesor_id, fecha, turno, recreo)`
- Antes de asignar un slot a un profesor, se verifica que no exista ya una entrada para esa combinación
- Si existe, el profesor NO es elegible para ese slot

**Ejemplo**:
```python
# ❌ INVÁLIDO - Mismo profesor en dos zonas simultáneas
Guardia 1: Profesor "Ana García" - 2025-09-01 - mañana - recreo 1 - Patio Principal
Guardia 2: Profesor "Ana García" - 2025-09-01 - mañana - recreo 1 - Patio Infantil

# ✅ VÁLIDO - Mismo profesor en diferentes recreos o turnos
Guardia 1: Profesor "Ana García" - 2025-09-01 - mañana - recreo 1 - Patio Principal
Guardia 2: Profesor "Ana García" - 2025-09-01 - mañana - recreo 2 - Patio Infantil
```

**Test**: `test_no_duplicados_profesor_mismo_slot` en `tests/test_asignador.py`

### 2. Compatibilidad de turno
**Regla**: Los profesores solo reciben guardias compatibles con su turno.

**Criterios**:
- Profesor turno "mañana": solo guardias de mañana
- Profesor turno "tarde": solo guardias de tarde
- Profesor turno "mixto": puede recibir guardias de ambos turnos

**Implementación**: Función `_turno_de_recreo()` que verifica compatibilidad

**Test**: `test_turno_compatible` en `tests/test_asignador.py`

### 3. Respeto de cuota máxima
**Regla**: Ningún profesor puede superar su cuota asignada de guardias.

**Justificación**: Garantiza equidad en la distribución de la carga de trabajo.

**Implementación**: 
- Se calcula la cuota de cada profesor con `calcular_guardias_por_profesor()`
- Se mantiene un contador `asignadas[profesor_id]`
- Se verifica `asignadas[profesor_id] < cuotas[profesor_id]` antes de asignar

**Test**: `test_respeta_cuotas` en `tests/test_asignador.py`

## ✅ Validaciones de Restricciones por Profesor

### 4. Fecha de inicio de guardias
**Regla**: Un profesor solo puede recibir guardias a partir de su fecha de inicio configurada.

**Campo**: `Profesor.fecha_inicio_guardias` (opcional)

**Uso**: Permite configurar incorporaciones tardías o inicios diferidos.

**Implementación**: 
```python
if p.fecha_inicio_guardias and slot.fecha < p.fecha_inicio_guardias:
    continue  # No elegible
```

**Test**: `test_respeta_fecha_inicio` en `tests/test_asignador.py`

### 5. Días de semana permitidos
**Regla**: Un profesor solo puede recibir guardias en los días de semana especificados.

**Campo**: `Profesor.dias_semana_permitidos` (CSV: "0,1,2,3,4,5,6" donde 0=Lunes, 6=Domingo)

**Valor por defecto**: Lunes a Viernes (0-4) si no se especifica

**Uso**: Permite configurar disponibilidad parcial (ej: "solo lunes, miércoles y viernes")

**Implementación**: Función `_dias_semana_ok()` que parsea el CSV y verifica

**Test**: `test_respeta_dias_permitidos` en `tests/test_asignador.py`

### 6. Recreos permitidos
**Regla**: Un profesor solo puede cubrir los recreos especificados en su configuración.

**Campo**: `Profesor.recreos_permitidos` (CSV: "1,2,3,4" según IDs de recreo)

**Valor por defecto**: Todos los recreos de su turno si no se especifica

**Uso**: Permite excluir profesores de ciertos recreos por motivos específicos

**Implementación**: Función `_recreo_ok()` que parsea el CSV y verifica

## 🛡️ Validaciones de Datos (pre-asignación)

### 7. Configuración del curso
**Validaciones**:
- Debe existir al menos un registro de `Configuracion`
- `fecha_fin_curso` debe ser posterior a `fecha_inicio_curso`
- Debe haber al menos un recreo configurado (mañana o tarde)

**Excepción**: `ValueError("No existe configuración del curso")`

### 8. Existencia de profesores
**Validación**: Debe haber al menos un profesor registrado

**Excepción**: `ValueError("No hay profesores registrados")`

**Tests**: `test_error_sin_profesores` en `tests/test_asignador.py`

### 9. Existencia de zonas
**Validación**: Debe haber al menos una zona registrada

**Excepción**: `ValueError("No hay zonas registradas")`

**Tests**: `test_error_sin_zonas` en `tests/test_asignador.py`

## 🎨 Preferencias y Heurísticas (SOFT CONSTRAINTS)

Estas reglas se intentan cumplir pero no son bloqueantes:

### 10. Continuidad de días consecutivos
**Preferencia**: Favorecer asignar guardias en días consecutivos al mismo profesor

**Puntuación**: `+1` si el día anterior también tuvo guardia

**Justificación**: Facilita la planificación y crea rutinas consistentes

### 11. Continuidad de zona
**Preferencia**: Favorecer asignar la misma zona que el día anterior

**Puntuación**: `+1` si la zona coincide con la última asignada

**Justificación**: Familiaridad con el espacio y rutinas establecidas

### 12. Continuidad de recreo
**Preferencia**: Favorecer asignar el mismo recreo (hora) que anteriormente

**Puntuación**: `+1` si el recreo coincide con el último asignado

**Justificación**: Consistencia horaria para el profesor

### 13. Balance de carga
**Preferencia**: Favorecer profesores con menos guardias asignadas

**Puntuación**: `-asignadas[p.id]` (negativo para priorizar menor carga)

**Justificación**: Distribución equitativa continua

### 14. Déficit de cuota
**Preferencia**: Favorecer profesores más alejados de su cuota objetivo

**Puntuación**: `cuotas[p.id] - asignadas[p.id]`

**Justificación**: Asegurar que todos alcancen su cuota proporcional

## 📊 Función de Scoring

La función de puntuación combina todas las preferencias:

```python
def score(p: Profesor) -> Tuple[int, int, int, float]:
    s1 = 1 if (ultimo_dia_prof[p.id] and (slot.fecha - ultimo_dia_prof[p.id]).days == 1) else 0
    s2 = 1 if ultimo_por_zona.get(slot.zona_id) == p.id else 0
    s3 = 1 if ultimo_recreo_prof[p.id] == slot.recreo_id else 0
    deficit = cuotas.get(p.id, 0) - asignadas[p.id]
    return (s1 + s2 + s3, -asignadas[p.id], deficit, random.random())
```

**Orden de prioridad**:
1. Suma de continuidades (días + zona + recreo): máximo 3 puntos
2. Menor número de guardias asignadas (balance)
3. Mayor déficit respecto a cuota objetivo
4. Factor aleatorio para desempate

## 🧪 Criterios de Verificación Post-Generación

El sistema debe garantizar:

1. ✅ **No duplicados críticos**: Ningún profesor tiene dos guardias en el mismo (fecha, turno, recreo)
2. ✅ **Respeto de cuotas**: Ningún profesor supera su cuota calculada
3. ✅ **Compatibilidad de turno**: Todos los profesores reciben solo guardias de su turno
4. ✅ **Restricciones individuales**: Se respetan fechas de inicio, días permitidos y recreos permitidos
5. ⚠️ **Cobertura completa**: Se intenta cubrir todos los slots, registrando incidencias si no es posible
6. ⚠️ **Preferencias suaves**: Se maximizan en la medida de lo posible sin violar restricciones duras

## 🔧 Mantenimiento y Extensión

### Agregar nueva validación crítica

1. Agregar la verificación en el bucle de elegibilidad de `generar_calendario_guardias()`
2. Documentar la regla en este archivo
3. Crear un test en `tests/test_asignador.py`
4. Actualizar `documentacion/condiciones_generales_asignacion.md` si aplica

### Agregar nueva preferencia (soft constraint)

1. Modificar la función `score()` en `generar_calendario_guardias()`
2. Documentar la preferencia en este archivo
3. Ajustar la documentación de heurísticas
4. Validar que no degrada el rendimiento (benchmarks)

## 📚 Referencias

- **Código fuente**: `src/services/asignador_guardias.py`
- **Tests**: `tests/test_asignador.py`
- **Condiciones generales**: `documentacion/condiciones_generales_asignacion.md`
- **Condiciones por profesor**: `documentacion/condiciones_particulares_profesores.md`

---
**Última actualización**: 15 de octubre de 2025
