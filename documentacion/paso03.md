# PASO 3: Lógica de Cálculo de Guardias

## 🎯 Objetivo
Calcular cuántas guardias corresponden a cada profesor según porcentaje de jornada, turno y estructura del curso.

## 📄 Archivo
`src/services/calculador_guardias.py`

## ✅ Estado
**IMPLEMENTADO** - Módulo completamente funcional con todas las funciones documentadas.

## 🔢 Conceptos Clave
- Días lectivos: rango fecha_inicio → fecha_fin excluyendo fines de semana (y futuros festivos/exclusiones).
- Recreos por día: 2 (mañana y tarde; se ajusta según turnos activos).
- Slots = días_lectivos × recreos_activos × número_zonas.
- Distribución proporcional al porcentaje_jornada (normalizada dentro de cada conjunto de turnos).

## ✅ Criterios de Verificación
- [x] La suma de guardias asignadas == slots totales
- [x] Proporcionalidad dentro de ±1–2 de diferencia por ajustes de redondeo
- [x] Profesores de mañana reciben solo guardias de mañana (factor de participación)
- [x] Profesores mixtos reciben guardias de ambos turnos

## 🧪 Pruebas Realizadas
Ejemplo con configuración actual:
- 206 días lectivos (sep 2025 - jun 2026)
- 2 recreos mañana + 2 tarde = 4 recreos/día
- 2 zonas
- **Slots totales**: 206 × 4 × 2 = 1648
- **Resultado**: ✅ Distribución exacta sin residuos

Script de prueba disponible en: `src/services/test_calculador.py`

## 📊 Funciones Implementadas

### `calcular_dias_lectivos(fecha_inicio, fecha_fin) -> int`
Excluye sábados y domingos entre dos fechas.

### `calcular_recreos_activos(session) -> Tuple[int, int]`
Determina cuántos recreos están configurados para mañana y tarde.

### `calcular_factor_participacion(profesor, recreos_manana, recreos_tarde) -> float`
Calcula el factor de participación según turno del profesor:
- Mañana: `recreos_manana / recreos_totales`
- Tarde: `recreos_tarde / recreos_totales`  
- Mixto: `1.0` (participa en todos)

### `calcular_distribucion_base(session) -> Dict[int, float]`
Calcula la distribución cruda de guardias por profesor:
1. Obtiene configuración, profesores y zonas
2. Calcula slots totales = días × recreos × zonas
3. Pondera participación = porcentaje_jornada × factor_turno
4. Reparte slots proporcionalmente

### `ajustar_redondeo(distribucion_cruda) -> Dict[int, int]`
Ajusta redondeo para suma exacta:
1. Aplica `floor()` a todos
2. Ordena por residuo decimal (mayor a menor)
3. Asigna slots sobrantes a los de mayor residuo

### `calcular_guardias_por_profesor(session) -> Dict[int, int]`
**Función principal**: Orquesta todo el proceso y devuelve `{profesor_id: guardias}`.

### `obtener_estadisticas(session) -> Dict`
Devuelve estadísticas del cálculo para verificación.

## ⚖️ Redondeo y Ajustes
1. Calcular guardias crudas (float).
2. Aplicar `math.floor` a cada una.
3. Repartir los slots sobrantes empezando por quienes tengan mayor residuo decimal.

**Implementación**: La función `ajustar_redondeo()` garantiza que la suma final sea exactamente igual a los slots totales.

## 🧪 Ejemplo Numérico
Escenario: 180 días lectivos, 4 zonas, 2 recreos, 10 profesores jornada completa.
Slots = 180 × 2 × 4 = 1440.
- Profesor 100%: 144 guardias
- Profesor 50%: 72 guardias

**Caso real probado**:
- 206 días lectivos (sep 2025 - jun 2026)
- 4 recreos/día (2 mañana + 2 tarde)
- 2 zonas
- Slots = 206 × 4 × 2 = 1648
- 5 profesores: distribución exacta ✅

## ✅ Criterios de Verificación
- [ ] La suma de guardias asignadas == slots totales
- [ ] Proporcionalidad dentro de ±1–2 de diferencia por ajustes de redondeo
- [ ] Profesores de mañana no reciben guardias de tarde y viceversa

## 💡 Mejoras Futuras
- Ajustar por preferencias y exclusiones.
- Añadir ponderación por saturación de días consecutivos.

---
Sigue con el PASO 4: algoritmo de asignación concreta.