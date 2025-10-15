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
- Si se activan o desactivan recreos por día (no homogéneo), los slots se sumarán por fecha en lugar de asumir uniformidad.