# PASO 4: Algoritmo de Asignación de Guardias

## 🎯 Objetivo
Asignar cada slot (fecha × recreo × zona × turno) a un profesor válido respetando la distribución calculada.

## 📄 Archivo
`src/services/asignador_guardias.py`

## 🔁 Flujo General (`generar_calendario_guardias`)
1. Obtener configuración + distribución base de cargas.
2. Generar lista de días lectivos.
3. Iterar días → recreos → turnos → zonas.
4. Seleccionar profesor elegible:
   - No ha excedido su cuota.
   - Turno compatible.
   - No asignado previamente ese día (si se puede evitar).
   - No misma zona que día anterior (soft constraint).
5. Registrar guardia provisional.
6. Persistir al final (`guardar_guardias_en_bd`).

## 🧮 Estructuras Sugeridas
```python
cargas = {profesor_id: total}
asignadas = {profesor_id: 0}
ultimo_por_zona = {zona_id: profesor_id}
guardias_por_dia_profesor = {(fecha, profesor_id): count}
```

## ✅ Selección de Profesor (Heurística)
1. Filtrar elegibles.
2. Ordenar por:
   - Menor guardias asignadas
   - Mayor diferencia (carga_total - asignadas)
   - Aleatoriedad controlada como desempate (para diversidad)

## 🔍 `validar_asignacion(guardia, profesor)`
Comprueba:
- Turno compatible
- No guardia previa en mismo (fecha, recreo)
- No exceder cuota

## 💾 Persistencia
`guardar_guardias_en_bd(calendario)` inserta en lote para optimizar (bulk_save_objects).

## 🧪 Verificación
- Suma de guardias == total slots
- Diferencia por profesor ≤ 2 de su cuota teórica
- Sin duplicados (mismo profesor, mismo día, mismo recreo)

## ⚠️ Errores Potenciales
- Falta de profesores de un turno → levantar excepción clara
- Zonas > profesores disponibles en turno → registrar incidencia

## 🔄 Regeneración
Proveer función `regenerar(calendario_existente=True)` que:
1. Borra guardias previas (confirmación UI)
2. Recalcula y reasigna

---
Continúa con el PASO 5: interfaz de gestión de datos.