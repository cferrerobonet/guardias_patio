# PASO 3: Lógica de Cálculo de Guardias

## 🎯 Objetivo
Calcular cuántas guardias corresponden a cada profesor según porcentaje de jornada, turno y estructura del curso.

## 📄 Archivo
`src/services/calculo_guardias.py`

## 🔢 Conceptos Clave
- Días lectivos: rango fecha_inicio → fecha_fin excluyendo fines de semana (y futuros festivos/exclusiones).
- Recreos por día: 2 (mañana y tarde; se ajusta según turnos activos).
- Slots = días_lectivos × recreos_activos × número_zonas.
- Distribución proporcional al porcentaje_jornada (normalizada dentro de cada conjunto de turnos).

## 🧠 Funciones Propuestas
### `calcular_dias_lectivos(fecha_inicio, fecha_fin) -> int`
Excluye sábados y domingos.

### `calcular_guardias_por_turno(profesor)`
Devuelve factor de participación (mañana, tarde, ambos).

### `calcular_distribucion_base(profesores, zonas, config) -> dict`
Devuelve `{profesor_id: total_guardias_asignables}`.

### `calcular_guardias_por_profesor()`
Orquesta el proceso: obtiene configuración, cuenta días, calcula slots y reparte redondeando.

## ⚖️ Redondeo y Ajustes
1. Calcular guardias crudas (float).
2. Aplicar `math.floor` a cada una.
3. Repartir los slots sobrantes empezando por quienes tengan mayor residuo decimal.

## 🧪 Ejemplo Numérico
Escenario: 180 días lectivos, 4 zonas, 2 recreos, 10 profesores jornada completa.
Slots = 180 × 2 × 4 = 1440.
- Profesor 100%: 144 guardias
- Profesor 50%: 72 guardias

## ✅ Criterios de Verificación
- [ ] La suma de guardias asignadas == slots totales
- [ ] Proporcionalidad dentro de ±1–2 de diferencia por ajustes de redondeo
- [ ] Profesores de mañana no reciben guardias de tarde y viceversa

## 💡 Mejoras Futuras
- Ajustar por preferencias y exclusiones.
- Añadir ponderación por saturación de días consecutivos.

---
Sigue con el PASO 4: algoritmo de asignación concreta.