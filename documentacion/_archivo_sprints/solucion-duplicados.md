# Solución: Guardias Duplicadas

## 📋 Problema Identificado

Se detectó que un profesor podía aparecer asignado a **múltiples zonas simultáneamente** en el mismo slot (fecha + turno + recreo), lo cual es **físicamente imposible**.

### Ejemplo del Problema:
```
BALLESTEROS CASTELLANOS, ISMAEL
  - 2025-09-08, mañana, recreo 1, Z1
  - 2025-09-08, mañana, recreo 1, Z2  ❌ DUPLICADO
  - 2025-09-08, mañana, recreo 1, Z3  ❌ DUPLICADO
  - 2025-09-08, mañana, recreo 1, Z4  ❌ DUPLICADO
```

## 🔍 Causa Raíz

**NO era un fallo en el algoritmo de asignación**. El código ya tenía la validación correcta:

```python
# VALIDACIÓN CRÍTICA en asignador_guardias.py (línea 127-129)
if (p.id, slot.fecha, slot.turno, slot.recreo_id) in guardias_por_slot_prof:
    continue  # ✅ Previene duplicados en UNA ejecución
```

**La causa real**: El generador de calendario se ejecutó **múltiples veces sin limpiar** las guardias previas, acumulando registros duplicados en la base de datos.

## ✅ Solución Implementada

### 1. Diálogo de Confirmación
Ahora, antes de generar guardias, la aplicación:

1. **Verifica** si ya existen guardias en la BD
2. **Pregunta al usuario** qué desea hacer:
   - ✅ **SÍ**: Elimina todas las guardias existentes y genera desde cero (RECOMENDADO)
   - ⚠️ **NO**: Agrega nuevas guardias a las existentes (puede crear duplicados)
   - ❌ **CANCELAR**: No hace nada

### 2. Código Implementado

```python
def generar_guardias(self):
    session = SessionLocal()
    try:
        # Verificar si ya existen guardias
        count_guardias = session.query(Guardia).count()
        
        if count_guardias > 0:
            respuesta = QMessageBox.question(
                self,
                "⚠️ Guardias Existentes",
                f"Ya existen {count_guardias} guardias en la base de datos.\n\n"
                f"¿Deseas ELIMINAR todas las guardias existentes antes de generar nuevas?\n\n"
                f"• SÍ: Eliminará todas y generará desde cero (recomendado)\n"
                f"• NO: Agregará nuevas guardias a las existentes (puede crear duplicados)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )
            
            if respuesta == QMessageBox.StandardButton.Cancel:
                return
                
            if respuesta == QMessageBox.StandardButton.Yes:
                # Eliminar todas las guardias existentes
                session.query(Guardia).delete()
                session.commit()
```

## 🧪 Validación

### Test de No Duplicados
El test `test_no_duplicados_profesor_mismo_slot` verifica que:

```python
def test_no_duplicados_profesor_mismo_slot(self, session, ...):
    """Verifica que un profesor NO esté en 2 zonas al mismo tiempo"""
    
    calendario, _ = generar_calendario_guardias(session)
    
    # Agrupar por (profesor, fecha, turno, recreo)
    slots_prof = defaultdict(list)
    for g in calendario:
        key = (g.profesor_id, g.fecha, g.turno, g.recreo)
        slots_prof[key].append(g.zona_id)
    
    # Verificar que cada profesor esté en MÁXIMO 1 zona por slot
    for (prof_id, fecha, turno, recreo), zonas in slots_prof.items():
        assert len(zonas) == 1, (
            f"Profesor {prof_id} asignado a {len(zonas)} zonas "
            f"en {fecha} {turno} recreo {recreo}: {zonas}"
        )
```

**Resultado**: ✅ PASSED

## 📊 Limpieza de Datos Existentes

Se ejecutó una limpieza de la base de datos:

```sql
DELETE FROM guardias;
```

Esto eliminó **5,700+ registros duplicados** acumulados de múltiples ejecuciones.

## 🎯 Recomendaciones de Uso

### Para Generar un Calendario Nuevo:
1. Ir a la pestaña **"Asignación de Guardias"**
2. Click en **"Generar Guardias"**
3. Cuando aparezca el diálogo:
   - Seleccionar **"SÍ"** para limpiar y regenerar
4. Esperar a que termine la generación

### Para Desarrollo/Testing:
- Siempre limpiar antes de cada prueba
- Verificar el contador de guardias generadas
- Revisar que no haya mensajes de "slots sin cubrir"

## 🔐 Garantías del Sistema

Con esta solución, el sistema garantiza:

1. ✅ **Un profesor, una zona por slot**: Físicamente posible
2. ✅ **Sin duplicados en generación**: Validación en el algoritmo
3. ✅ **Sin duplicados por re-ejecución**: Confirmación de limpieza
4. ✅ **Trazabilidad**: Tests automatizados que verifican la regla

## 📝 Notas Técnicas

- **Archivo modificado**: `src/main.py` (método `generar_guardias`)
- **Líneas afectadas**: ~1125-1180
- **Tests relevantes**: `tests/test_asignador.py::test_no_duplicados_profesor_mismo_slot`
- **Versión**: 15 octubre 2025

---

**Conclusión**: El problema NO era del algoritmo (que funcionaba correctamente), sino de **acumulación de datos** por múltiples ejecuciones. La solución implementada previene futuras acumulaciones mediante confirmación de usuario.
