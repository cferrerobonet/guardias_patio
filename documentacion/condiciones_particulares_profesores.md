# Condiciones Particulares por Profesor

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
