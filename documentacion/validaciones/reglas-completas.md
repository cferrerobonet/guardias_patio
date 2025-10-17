# Condiciones Generales de Asignación de Guardias

## 🎯 Propósito
Establecer las reglas globales para asignar cada guardia (slot) respetando el calendario lectivo, los recreos definidos, las zonas disponibles y la disponibilidad por turnos.

## 🧩 Definiciones
- Slot: combinación (fecha × recreo × zona × turno).
- Días lectivos: rango [fecha_inicio, fecha_fin] excluyendo fines de semana (y, en el futuro, festivos personalizados).
- Recreos activos: los definidos en la Configuración (pueden ser 0–2 por mañana y 0–2 por tarde).
- Zonas: espacios donde se cubren guardias en cada recreo.

## 🔢 Principios de cálculo previos
- Slots totales (por curso) = días_lectivos × sum(zonas_por_recreo_en_un_día).
- La distribución base por profesor se calcula proporcionalmente a su porcentaje de jornada, participación por turno y ajuste por tutoría:
  - Mañana: factor_turno = recreos_mañana / recreos_totales
  - Tarde: factor_turno = recreos_tarde / recreos_totales
  - Mixto: factor_turno = 1.0
  - Ajuste por tutoría: factor_tutoría = `ajuste_tutores` si es tutor, en caso contrario `ajuste_no_tutores` (ver Panel de configuración).
  - Peso profesor = porcentaje_jornada × factor_turno × factor_tutoría.
- Ajuste de redondeo: se garantiza que la suma final por profesor coincide exactamente con los slots totales.

### 🧭 Regla de proporcionalidad (CLAVE)
La asignación de guardias será estrictamente proporcional a:
1) Las horas contratadas (porcentaje de jornada), y
2) Si es o no tutor, aplicando el porcentaje/multiplicador indicado en los campos de configuración.

Fórmula base:
- peso_profesor = porcentaje_jornada × factor_turno × factor_tutoría
- factor_tutoría = `ajuste_tutores` (si tutor) o `ajuste_no_tutores` (si no tutor)
- cuota_profesor = round_slots(total_slots × peso_profesor / Σ pesos_profesores)

Campos involucrados:
- En Configuración: `ajuste_tutores`, `ajuste_no_tutores`.
- En Profesor: `tutor` (sí/no) y `porcentaje_jornada` (derivado de horas_contrato/30).

Ejemplo rápido:
- total_slots = 1000. Dos profesores a turno equivalente.
- P1: 100% jornada y tutor (ajuste_tutores = 0.90) → peso = 1.0 × 1.0 × 0.90 = 0.90
- P2: 100% jornada y no tutor (ajuste_no_tutores = 1.00) → peso = 1.0 × 1.0 × 1.00 = 1.00
- Σ pesos = 1.90 → cuotas ≈ P1: 474, P2: 526 (redondeo asegura suma = 1000)

## 📅 Días no lectivos automáticos y personalizados
Además de excluir fines de semana, se considerarán NO LECTIVOS de forma automática (cada curso):
- Todos los sábados y domingos entre fecha_inicio y fecha_fin del curso.
- 9 y 12 de octubre (ambos inclusive, cada año en rango del curso).
- 1 de noviembre.
- 6 y 8 de diciembre.
- Del 22 de diciembre al 6 de enero (ambos inclusive).
- Del 16 al 19 de marzo (ambos inclusive).
- Jueves Santo (fecha móvil cada año) hasta 12 días después inclusive.
- 1 de mayo.

Personalización:
- Se podrá añadir una lista de fechas específicas no lectivas (puentes, festivos locales, días de libre disposición) desde la Configuración.

Notas de cálculo:
- Para fechas móviles (p. ej., Jueves Santo) se calculará la fecha según el año académico y se generará el rango [Jueves Santo, Jueves Santo + 12].
- Si el curso abarca dos años (ej. sep–jun), se evaluarán festivos para ambos años.

## ✅ Reglas de elegibilidad por slot
Para asignar un slot (fecha, recreo, zona, turno) a un profesor, se deben cumplir:
1. Turno compatible (el profesor solo puede recibir guardias en su turno; mixto en ambos).
2. No exceder su cuota total asignable (de la distribución base).
3. **[CRÍTICO] No simultaneidad de zonas**: Un mismo profesor NO puede estar asignado a múltiples zonas al mismo tiempo (mismo día, mismo turno, mismo recreo). Esta es una restricción física fundamental: un profesor solo puede estar en un lugar a la vez.
4. Disponibilidad ese día y recreo:
   - Evitar, si es posible, que un profesor tenga más de una guardia en el mismo día.
   - Evitar, si es posible, asignar la misma zona de forma consecutiva al mismo profesor (día anterior).

## 🔁 Criterios de selección (heurística)
- Entre los elegibles, priorizar:
  1. Continuidad para cada profesor, cuando sea posible:
     - Preferir días consecutivos (extender rachas ya existentes del profesor).
     - Preferir misma zona/patio que su último día asignado (consistencia).
     - Preferir mismo recreo (misma hora) que su patrón previo.
  2. Menor número de guardias ya asignadas (balance global).
  3. Mayor diferencia entre su cuota y lo ya asignado (déficit de cuota).
  4. Desempate con un ligero factor aleatorio controlado, para diversidad.

## 🔍 Validaciones y errores
- Si no hay profesores suficientes para un turno (p. ej., recreos de tarde sin profesorado de tarde/mixto), se debe:
  - Registrar la incidencia y
  - Lanzar una excepción clara indicando el turno y la fecha afectada.
- Si el número de zonas en un recreo supera al de profesores elegibles, se asignarán tantos como sea posible y se registrará la imposibilidad de cubrir el resto.

## 💾 Persistencia
- Las asignaciones se acumulan en memoria durante la generación y se persisten en bloque (bulk) para eficiencia.
- Debe existir la opción de regenerar: borrar asignaciones previas y recalcular con confirmación desde la interfaz.

## 🧪 Criterios de verificación
- La suma de guardias generadas coincide con los slots totales, o se justifican los huecos no cubiertos con incidencias.
- Ningún profesor supera su cuota.
- **No hay duplicados de profesor en el mismo (fecha, turno, recreo)** - Un profesor solo puede estar en una zona a la vez.
- No hay duplicados de profesor en el mismo (fecha, recreo, zona).
- Las restricciones "suaves" (una al día y evitar misma zona consecutiva) se respetan en la mayoría de los casos; si no, quedan registradas como avisos no bloqueantes.

## 📈 Observaciones
- La distribución base garantiza equidad global; la asignación concreta intenta minimizar desequilibrios locales.
- En el futuro se incorporarán preferencias, exclusiones temporales y ponderación por saturación de días consecutivos.

## 🛠️ Panel de configuración (campos requeridos)
Añadir o actualizar los siguientes campos para soportar estas reglas:

1) Curso y no lectivos
- fecha_inicio (date)
- fecha_fin (date)
- dias_no_lectivos_personalizados: lista[date]
- activar_festivos_automaticos: bool (aplica listado anterior, incluidos fines de semana)

2) Recreos y zonas
- numero_recreos_por_dia: int ≥ 0
- recreos: lista de objetos con:
  - id_recreo (1..N)
  - etiqueta (str) p. ej., "R1 mañana", "R2 tarde"
  - hora (opcional)
  - zonas (int ≥ 1) número de zonas/patios a cubrir en ese recreo

3) Ajuste por tutoría
- ajuste_tutores: float (multiplicador, p. ej., 0.90 reduce un 10% la carga)
- ajuste_no_tutores: float (multiplicador, normalmente 1.00)

Notas:
- El cálculo de slots por día será: slots_día = sum(recreo.zonas para recreo in recreos activos del día). Slots totales del curso = días_lectivos × slots_día (si la estructura es homogénea por día).
- Si se activan o desactivan recreos por día (no homogéneo), los slots se sumarán por fecha en lugar de asumir uniformidad.# Condiciones Particulares por Profesor

## 🎯 Propósito
Definir las reglas que afectan a cada profesor individualmente durante el cálculo y la asignación de guardias.

## 👤 Atributos relevantes del profesor
- Horas de contrato: base para calcular el porcentaje de jornada.
- Porcentaje de jornada: horas_contrato / 30 (30h = 100%).
- Turno: mañana | tarde | mixto.
- Distribución mixta: horas de mañana y de tarde cuando el turno es mixto.
 - Tutoría: indica si el profesor es tutor (afecta a su cuota mediante un factor de ajuste configurable).

## 🧮 Cálculo de participación
- Cuota total de guardias del profesor = slots_totales × (porcentaje_jornada_normalizado × factor_turno × factor_tutoría_normalizado).
- Factor por turno:
  - Mañana: participa proporcionalmente a los recreos de mañana activos.
  - Tarde: participa proporcionalmente a los recreos de tarde activos.
  - Mixto: participa en ambos turnos (factor 1.0) y su cuota se reparte internamente según horas_mañana vs horas_tarde.
 - Ajuste por tutoría: multiplicador `ajuste_tutores` si es tutor, `ajuste_no_tutores` en caso contrario (ver configuración general).

  Regla de proporcionalidad (clave):
  - La cuota depende proporcionalmente de las horas contratadas y del estado de tutor, aplicando los multiplicadores configurados. Si dos profesores tienen el mismo turno y horas, pero uno es tutor (ajuste 0.90) y otro no (ajuste 1.00), el no tutor recibirá más guardias en proporción 1.00/0.90.

## 🔗 Compatibilidad de turno
- Profesores de mañana no reciben guardias de tarde.
- Profesores de tarde no reciben guardias de mañana.
- Profesores mixtos pueden recibir en ambos turnos; el reparto se aproxima a su proporción de horas (p. ej., 60% mañana, 40% tarde).

## 🚫 Límites diarios y locales (suaves)
- Intentar que cada profesor tenga como máximo 1 guardia por día.
- Intentar repetir la misma zona todos los días consecutivos para el mismo profesor.

## ➕ Preferencias de continuidad (cuando sea posible)
- Días consecutivos: al asignar, favorecer extender rachas ya existentes del profesor.
- Misma zona/patio: favorecer mantener la misma zona del día anterior del profesor si es viable.
- Mismo recreo: favorecer mantener el mismo recreo (misma hora) para facilitar hábitos y coordinación.

## 📅 Preferencias y exclusiones (futuro)
- Exclusiones temporales por fechas (bajas, permisos) que anulan elegibilidad en esos días.
- Preferencias por zonas o franjas a priorizar o evitar.
- Límites de carga semanal o mensual.

## 🧪 Verificación por profesor
- La suma de guardias asignadas a cada profesor no debe exceder su cuota calculada.
- Desviaciones de ±1–2 pueden darse por ajustes de redondeo y restricciones; deben compensarse en reasignaciones o iteraciones futuras.

## 📝 Notas de implementación
- Mantener contadores: asignadas_por_profesor, últimas_zonas_por_profesor, guardias_por_dia_profesor.
- El algoritmo de selección debe usar estos contadores para priorizar al profesor más equilibrado y compatible.
- Registrar avisos cuando una restricción suave no pueda cumplirse para un profesor concreto.

## 🔧 Restricciones configurables por profesor
Añadir a la ficha del profesor (o panel específico) los siguientes campos:

- fecha_inicio_guardias: date — a partir de qué fecha puede empezar a realizar guardias.
- dias_semana_permitidos: set[int] — números 0..6 (lunes..domingo) que indican qué días de la semana puede hacer guardia.
- recreos_permitidos: set[int] — identificadores de recreo (1..N) que puede cubrir.

Reglas de selección con estas restricciones:
1. Un profesor solo es elegible en una fecha si fecha >= fecha_inicio_guardias (si está definido).
2. Un profesor solo es elegible si el día de la semana de la fecha ∈ dias_semana_permitidos (si está definido; por defecto, lunes–viernes).
3. Un profesor solo es elegible para recreos cuyo id ∈ recreos_permitidos (si está definido; por defecto, todos los recreos de su turno).
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
