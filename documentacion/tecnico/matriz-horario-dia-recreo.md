# Matriz de Horario: Restricciones por Día y Recreo

## 📋 Descripción General

A partir de esta versión, el sistema permite definir restricciones de disponibilidad de profesores de forma mucho más granular mediante una **matriz visual de días × recreos**.

Anteriormente, las restricciones se configuraban mediante dos campos de texto separados:
- Días de la semana permitidos (ej: `0,1,2,3,4`)
- Recreos permitidos (ej: `1,2`)

El problema era que **no había relación entre ambos**: un profesor podía estar disponible lunes y miércoles, pero no se podía especificar que los lunes solo estaba disponible en el recreo 1, mientras que los miércoles estaba disponible en todos los recreos.

## 🎯 Nueva Funcionalidad

### Interfaz Visual

El formulario de profesor ahora incluye una matriz interactiva:

```
┌─────────────────────────────────────────────────────────┐
│  ☑️ Usar restricciones personalizadas de horario       │
│                                                          │
│  📅 Disponibilidad por día y recreo:                    │
│                                                          │
│         R1    R2    R3    R4                            │
│  Lun    ☑️    ☑️    ☐     ☐                             │
│  Mar    ☑️    ☐     ☑️    ☐                             │
│  Mié    ☑️    ☑️    ☑️    ☑️                             │
│  Jue    ☐     ☐     ☐     ☐                             │
│  Vie    ☑️    ☑️    ☐     ☐                             │
│  Sáb    ☐     ☐     ☐     ☐                             │
│  Dom    ☐     ☐     ☐     ☐                             │
│                                                          │
│  [✓ Marcar todos] [✗ Desmarcar todos]                  │
└─────────────────────────────────────────────────────────┘
```

### Características

1. **Checkbox principal**: Activa/desactiva toda la funcionalidad de restricciones
2. **Matriz 7×4**: 7 días de la semana × 4 recreos
3. **Selección granular**: Marca combinaciones específicas día+recreo
4. **Botones de utilidad**: 
   - "Marcar todos": Selecciona todas las casillas
   - "Desmarcar todos": Deselecciona todas las casillas
5. **100% opcional**: Si no se activa el checkbox, el sistema aplica el comportamiento por defecto (L-V, todos los recreos)

## 🔧 Funcionamiento Técnico

### Formato de Almacenamiento

Los datos se almacenan en formato JSON en el campo `recreos_permitidos` de la tabla `profesores`:

```json
{
  "0": [1, 2],        // Lunes: recreos 1 y 2
  "1": [1, 3],        // Martes: recreos 1 y 3
  "2": [1, 2, 3, 4],  // Miércoles: todos los recreos
  "4": [1, 2]         // Viernes: recreos 1 y 2
}
```

**Nota importante**: 
- Las claves son números del 0 al 6 (donde 0=Lunes, 6=Domingo)
- Los valores son listas de IDs de recreo (1-4)
- Solo se incluyen los días que tienen al menos un recreo marcado

### Validación en el Algoritmo

El algoritmo de asignación de guardias (`asignador_guardias.py`) valida automáticamente estas restricciones mediante la función `_horario_permitido()`:

```python
def _horario_permitido(
    fecha: date, recreo_id: int, horario_json: Optional[str]
) -> bool:
    """
    Valida si un día+recreo está permitido según la matriz JSON.
    
    Si no hay restricciones definidas, permite L-V y todos los recreos.
    """
    if not horario_json:
        return fecha.weekday() < 5  # Por defecto L-V
    
    try:
        import json
        datos = json.loads(horario_json)
        dia_str = str(fecha.weekday())
        
        if dia_str not in datos:
            return False
        
        return recreo_id in datos[dia_str]
    except:
        return fecha.weekday() < 5
```

## 📝 Casos de Uso

### Ejemplo 1: Profesor con Reducción Horaria

Un profesor que trabaja media jornada y solo está disponible lunes, miércoles y viernes por las mañanas (recreos 1 y 2):

```json
{
  "0": [1, 2],  // Lunes
  "2": [1, 2],  // Miércoles
  "4": [1, 2]   // Viernes
}
```

### Ejemplo 2: Profesor con Disponibilidad Variable

Un profesor que tiene reuniones los martes y jueves por las tardes:

```json
{
  "0": [1, 2, 3, 4],  // Lunes: todo el día
  "1": [1, 2],        // Martes: solo mañanas
  "2": [1, 2, 3, 4],  // Miércoles: todo el día
  "3": [1, 2],        // Jueves: solo mañanas
  "4": [1, 2, 3, 4]   // Viernes: todo el día
}
```

### Ejemplo 3: Profesor con Turno Partido Irregular

Un profesor que algunos días trabaja por la mañana y otros por la tarde:

```json
{
  "0": [1, 2],     // Lunes: mañanas
  "1": [3, 4],     // Martes: tardes
  "2": [1, 2],     // Miércoles: mañanas
  "3": [3, 4],     // Jueves: tardes
  "4": [1, 2, 3, 4] // Viernes: todo el día
}
```

## ⚙️ Integración con Otras Funcionalidades

La matriz de horario se combina con las demás restricciones del profesor:

1. **Turno**: El sistema sigue respetando el turno del profesor (mañana/tarde/mixto)
2. **Fechas de guardias**: Si se define `fecha_inicio_guardias` o `fecha_fin_guardias`, estas siguen aplicándose
3. **Ausencias**: Las ausencias registradas siguen teniendo prioridad
4. **Límite diario**: La restricción de "máximo 1 guardia por día" sigue activa

## 🎨 Experiencia de Usuario

### Al Crear un Profesor

1. Por defecto, la matriz está **desactivada y oculta**
2. Al marcar el checkbox principal, la matriz se habilita
3. Se pueden marcar las combinaciones deseadas
4. Los botones de "Marcar/Desmarcar todos" facilitan la configuración masiva

### Al Editar un Profesor

1. Si el profesor tiene restricciones definidas:
   - El checkbox principal se marca automáticamente
   - La matriz se carga con los datos guardados
2. Si no tiene restricciones:
   - Todo aparece desactivado

### Al Guardar

- Solo se guarda el JSON si el checkbox principal está marcado
- Si está desmarcado, se guarda `NULL` (comportamiento por defecto)

## 🚀 Ventajas de este Enfoque

1. **Intuitivo**: Representación visual clara
2. **Sin errores de formato**: No hay que escribir JSON manualmente
3. **Flexible**: Permite cualquier combinación día×recreo
4. **Compatible**: Reutiliza el campo `recreos_permitidos` existente
5. **Retrocompatible**: Profesores sin restricciones siguen funcionando igual
6. **Escalable**: Fácil adaptar a más recreos o configuraciones futuras

## 🔄 Migración desde Versión Anterior

**No se requiere migración de datos** porque:
- Se reutiliza el campo `recreos_permitidos` existente
- El campo `dias_semana_permitidos` queda en desuso pero no se elimina
- Profesores antiguos sin restricciones siguen funcionando (NULL = comportamiento por defecto)

## 📊 Impacto en el Algoritmo

El algoritmo de asignación de guardias ahora:

1. **Consulta la matriz JSON** de cada profesor
2. **Valida cada slot (día+recreo)** antes de considerar al profesor
3. **Excluye automáticamente** combinaciones no permitidas
4. **Respeta prioridades**: Ausencias > Fechas límite > Matriz horario > Turno

## ⚠️ Consideraciones

1. **Configuración avanzada**: Esta funcionalidad es opcional y para casos específicos
2. **Responsabilidad del usuario**: Asegurarse de marcar suficientes casillas para que el profesor pueda cubrir guardias
3. **Coherencia con turno**: Si un profesor es de "mañana", no tiene sentido marcar solo recreos de tarde
4. **Verificación visual**: Siempre revisar la matriz antes de guardar

## 🎓 Tutorial Rápido

1. **Abrir formulario de profesor** (nuevo o edición)
2. **Marcar** el checkbox "☑️ Usar restricciones personalizadas de horario"
3. **Seleccionar** las casillas de los días y recreos deseados
4. **Opcional**: Usar botones de "Marcar/Desmarcar todos" como punto de partida
5. **Guardar** el profesor

¡Listo! El algoritmo respetará automáticamente estas restricciones.

---

**Versión**: 2.6.0  
**Fecha**: Octubre 2025  
**Autor**: Sistema de Guardias de Patio
