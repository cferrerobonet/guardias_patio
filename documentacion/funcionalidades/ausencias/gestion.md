# 🏥 Guía de Gestión de Ausencias - v2.5

## 📋 Índice

1. [Introducción](#introducción)
2. [Características Principales](#características-principales)
3. [Acceso a la Funcionalidad](#acceso-a-la-funcionalidad)
4. [Registrar una Ausencia](#registrar-una-ausencia)
5. [Gestionar Guardias Afectadas](#gestionar-guardias-afectadas)
6. [Visualización en Calendario](#visualización-en-calendario)
7. [Casos de Uso Comunes](#casos-de-uso-comunes)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

La **Gestión de Ausencias** es una funcionalidad crítica introducida en la versión 2.5 de Guardias de Patio que transforma la aplicación de un simple "generador" a un verdadero "gestor continuo" de guardias.

### ¿Por qué es importante?

- ✅ **Prevención automática**: Profesores ausentes no reciben guardias al generar el calendario
- ✅ **Reasignación inteligente**: Las guardias afectadas pueden reasignarse automáticamente
- ✅ **Visibilidad clara**: El calendario muestra qué días tienen profesores ausentes
- ✅ **Historial completo**: Mantiene registro de todas las ausencias (activas e inactivas)

---

## Características Principales

### 1. Registro de Ausencias

- **Tipos soportados**:
  - 🏥 Baja médica
  - 📋 Permiso
  - 🏖️ Vacaciones
  - 📝 Otros

- **Campos**:
  - Profesor
  - Fechas (inicio y fin)
  - Tipo
  - Motivo (opcional)
  - Estado (activa/inactiva)

### 2. Gestión de Guardias Afectadas

- **Preview en tiempo real**: Muestra guardias afectadas antes de guardar
- **Reasignación automática**: Algoritmo inteligente selecciona los mejores sustitutos
- **Reasignación manual**: Opción de elegir sustituto específico
- **Validaciones**: Verifica disponibilidad y evita sobrecargas

### 3. Visualización en Calendario

- **Icono 🏥**: Días con ausencias marcados claramente
- **Contador**: Muestra número de profesores ausentes por día
- **Colores**: Visual claro en la leyenda del calendario

---

## Acceso a la Funcionalidad

### Ubicación

La funcionalidad de ausencias se encuentra en la pestaña **"🏥 Ausencias"** de la aplicación principal.

```
Menú Principal → Pestaña "🏥 Ausencias"
```

### Layout de la Interfaz

La interfaz está dividida en dos paneles:

**Panel Izquierdo: Lista de Ausencias**
- Tabla con todas las ausencias registradas
- Columnas: ID, Profesor, Tipo, Fecha Inicio, Fecha Fin, Días, Estado
- Códigos de color:
  - 🟨 **Amarillo**: Ausencia en curso (activa hoy)
  - 🔵 **Cyan**: Ausencia futura
  - ⬜ **Gris**: Ausencia pasada
  - 🔴 **Rojo**: Ausencia inactiva

**Panel Derecho: Formulario**
- Selector de profesor
- Campos de fecha
- Tipo de ausencia
- Motivo (opcional)
- Preview de guardias afectadas

---

## Registrar una Ausencia

### Paso a Paso

#### 1. Acceder al Formulario

- Ir a la pestaña **"🏥 Ausencias"**
- El panel derecho muestra **"✏️ NUEVA AUSENCIA"**

#### 2. Completar Datos

1. **Seleccionar Profesor**
   - Dropdown con lista de todos los profesores
   - Ordenados alfabéticamente

2. **Seleccionar Tipo**
   - baja_medica
   - permiso
   - vacaciones
   - otros

3. **Establecer Fechas**
   - **Fecha de inicio**: Primer día de ausencia
   - **Fecha de fin**: Último día de ausencia
   - Usa el calendario popup para selección rápida

4. **Motivo (Opcional)**
   - Descripción libre
   - Ejemplo: "Gripe estacional", "Permiso por asunto familiar"

#### 3. Preview de Guardias Afectadas

Mientras completas los datos, el panel **"📊 Guardias Afectadas (Preview)"** muestra automáticamente:

- Número total de guardias afectadas
- Lista detallada (primeras 10):
  - Fecha
  - Turno
  - Recreo
  - Zona

**Ejemplo de Preview:**

```
⚠️ 3 guardias afectadas:

• 18/10/2025 - mañana - Recreo 1 - Patio Principal
• 21/10/2025 - mañana - Recreo 2 - Porche
• 23/10/2025 - mañana - Recreo 1 - Patio Trasero
```

Si no hay guardias:
```
✅ No hay guardias asignadas en este periodo
```

#### 4. Guardar

- Click en **"💾 Guardar Ausencia"** (o presiona **Ctrl+S**)
- Mensaje de confirmación: "Ausencia registrada correctamente"
- La tabla se actualiza automáticamente

---

## Gestionar Guardias Afectadas

### Opción 1: Durante el Registro

Al guardar una ausencia, el sistema **NO reasigna automáticamente** las guardias. Esto te permite:

1. Registrar la ausencia
2. Seleccionarla de la tabla
3. Click en **"👁️ Ver Guardias Afectadas"**

### Opción 2: Después del Registro

1. Selecciona una ausencia de la tabla (doble click o click + botón Editar)
2. Click en **"👁️ Ver Guardias Afectadas"**
3. Se abre el **Diálogo de Reasignación**

### Diálogo de Reasignación

El diálogo muestra:

- **Tabla de Guardias**: Todas las guardias del profesor ausente en ese periodo
  - ID, Fecha, Turno, Recreo, Zona, Profesor Actual

- **Opciones de Reasignación**:

#### A) Reasignación Automática

- Click en **"🤖 Reasignar Automáticamente"**
- El sistema:
  1. Busca profesores disponibles para cada guardia
  2. Ordena por menor carga actual
  3. Asigna al mejor candidato
  4. Muestra resultado:
     ```
     Reasignación completada:
     
     ✅ Reasignadas: 3
     ❌ Fallidas: 0
     ```

**Algoritmo de selección:**

```python
Para cada guardia:
  1. Buscar profesores con turno compatible
  2. Excluir profesores ausentes ese día
  3. Excluir profesores con guardia ese día
  4. Ordenar por:
     - Menor número de guardias asignadas hoy
     - Continuidad de zona (si ya estuvo ahí)
  5. Asignar al primero de la lista
```

#### B) Reasignación Manual

- Selecciona una guardia específica de la tabla
- Click en **"👤 Reasignar Seleccionada"**
- Se muestra lista de profesores disponibles:
  ```
  GARCÍA LÓPEZ, JUAN (0 guardias hoy)
  MARTÍNEZ RUIZ, ANA (0 guardias hoy)
  FERNÁNDEZ PÉREZ, LUIS (1 guardias hoy)
  ```
- Selecciona el profesor deseado
- Confirmación: "Guardia reasignada a [Profesor]"

---

## Visualización en Calendario

### Marcadores en el Calendario

Al ir a la pestaña **"📅 Vista Calendario"**, los días con ausencias se identifican claramente:

#### Icono 🏥 en el Número del Día

```
┌─────────┐
│  18 🏥  │  ← Día con ausencias
│         │
│ 🕐 M R1 │
│ GARCÍA  │
└─────────┘
```

#### Contador de Ausentes

En la parte inferior de cada día:

```
🏥 2 ausente(s)
```

#### Leyenda del Calendario

```
📋 Leyenda:
⬜ Sin guardias   🟦 Con guardias   🟨 Hoy   🏥 Con ausencias
```

---

## Casos de Uso Comunes

### Caso 1: Baja Médica de Corta Duración

**Escenario**: Un profesor enferma y estará ausente 3 días.

**Pasos**:

1. Ir a **🏥 Ausencias**
2. Seleccionar profesor
3. Tipo: `baja_medica`
4. Fecha inicio: Hoy
5. Fecha fin: Hoy + 2 días
6. Motivo: "Gripe"
7. **Guardar**
8. Click **"Ver Guardias Afectadas"**
9. Click **"Reasignar Automáticamente"**
10. Confirmar

**Resultado**: Las 3 guardias se reasignan a otros profesores disponibles.

---

### Caso 2: Vacaciones Planificadas

**Escenario**: Un profesor solicitó vacaciones para la próxima semana (5 días lectivos).

**Pasos**:

1. **Antes de generar guardias del mes**:
   - Registrar ausencia con fechas de las vacaciones
   - Tipo: `vacaciones`
   - Motivo: "Vacaciones personales aprobadas"
   - Guardar

2. **Generar guardias normalmente**:
   - El sistema **automáticamente excluye** al profesor ausente
   - No necesita reasignación posterior

**Ventaja**: Prevención > Corrección

---

### Caso 3: Permiso de Medio Día

**Escenario**: Un profesor tiene permiso solo por la mañana.

**Limitación Actual**: El sistema gestiona ausencias por día completo.

**Solución Temporal**:

1. Registrar ausencia solo para ese día
2. Reasignar **manualmente** solo las guardias de mañana
3. Las guardias de tarde quedan sin cambios

**Mejora Futura (v2.6)**: Soporte para ausencias por turno.

---

### Caso 4: Reactivar Ausencia Desactivada

**Escenario**: Se desactivó una ausencia por error.

**Pasos**:

1. Seleccionar la ausencia inactiva (fila roja)
2. Click **"✏️ Editar"**
3. *(No hay opción directa para reactivar desde UI)*

**Solución Temporal**:
- Eliminar la ausencia
- Crear nueva ausencia con los mismos datos

**Mejora Futura**: Botón "Reactivar" para ausencias inactivas.

---

## Editar una Ausencia

### Cuándo Editar

- Cambiar fechas (extender o acortar ausencia)
- Cambiar tipo o motivo
- Corregir datos incorrectos

### Pasos

1. **Seleccionar** ausencia de la tabla (doble click)
2. El formulario se llena con los datos actuales
3. **Modificar** los campos necesarios
4. **Guardar** (Ctrl+S)
5. El sistema:
   - Actualiza la ausencia en BD
   - Recalcula preview de guardias afectadas
   - **NO reasigna automáticamente**

⚠️ **Importante**: Si cambias las fechas, revisa manualmente las guardias afectadas.

---

## Eliminar vs Desactivar

### Eliminar (Borrado Permanente)

**Cuándo usar**:
- Ausencia registrada por error
- Datos completamente incorrectos

**Pasos**:
1. Seleccionar ausencia
2. Click **"🗑️ Eliminar"**
3. Confirmar eliminación
4. **Efecto**: Se borra de la base de datos (no recuperable)

### Desactivar (Mantener Historial)

**Cuándo usar**:
- Ausencia que ya no aplica pero quieres conservar el registro
- Ausencia cancelada (profesor volvió antes)
- Necesitas historial para auditoría

**Pasos**:
1. Seleccionar ausencia
2. Click **"⏸️ Desactivar"**
3. **Efecto**:
   - Marca `activa = False` en BD
   - Se muestra en rojo en la tabla
   - No se considera en cálculos futuros
   - Preserva historial

---

## Preguntas Frecuentes

### ¿Las ausencias afectan la generación de guardias?

**Sí**. Al generar un nuevo calendario de guardias:

1. El sistema verifica ausencias activas para cada día
2. Profesores ausentes **NO reciben guardias** ese día
3. El algoritmo redistribuye automáticamente

### ¿Puedo registrar una ausencia para un día pasado?

**Sí**. El sistema permite registrar ausencias en cualquier fecha. Útil para:

- Actualizar registros históricos
- Justificar ausencias retrospectivamente

### ¿Qué pasa si no hay profesores disponibles para reasignar?

El sistema:

1. Intenta reasignar cada guardia
2. Si no encuentra sustituto disponible:
   - Marca como "fallida"
   - Incluye en el reporte final
   - La guardia queda asignada al profesor ausente (⚠️ requiere intervención manual)

**Recomendación**: Revisar el informe de reasignación y gestionar manualmente las guardias fallidas.

### ¿Puedo ver todas las ausencias de un profesor específico?

**Actualmente**: No hay filtro por profesor en la interfaz.

**Solución Temporal**: Ordenar la tabla por columna "Profesor" (click en encabezado).

**Mejora Futura (v2.6)**: Filtros avanzados por profesor, tipo, periodo.

### ¿Las ausencias tienen impacto en las estadísticas?

**Sí**. Las estadísticas reflejan:

- Guardias realmente asignadas (después de reasignaciones)
- Si un profesor estuvo ausente, sus guardias se cuentan para el sustituto

**Mejora Futura (v2.7)**: Estadísticas específicas de ausencias (días ausentes por profesor, etc.).

### ¿Puedo exportar el listado de ausencias?

**Actualmente**: No hay opción de exportación directa.

**Solución Temporal**: Los datos están en la tabla `ausencias` de SQLite.

**Mejora Futura (v2.6)**: Exportación a Excel de ausencias.

---

## Atajos de Teclado

Disponibles en la pestaña **🏥 Ausencias**:

| Atajo | Acción |
|-------|--------|
| **Ctrl+S** | Guardar ausencia actual |
| **Ctrl+F** | Enfocar campo de búsqueda de profesor |
| **F5** | Refrescar lista de ausencias |
| **Del** | Eliminar ausencia seleccionada |
| **Esc** | Cancelar edición y limpiar formulario |
| **Enter** | Guardar ausencia (si formulario tiene foco) |
| **Doble Click** | Editar ausencia seleccionada |

---

## Arquitectura Técnica (Para Desarrolladores)

### Modelo de Datos

**Tabla: `ausencias`**

```sql
CREATE TABLE ausencias (
    id INTEGER PRIMARY KEY,
    profesor_id INTEGER NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    tipo VARCHAR NOT NULL,
    motivo TEXT,
    documento_path VARCHAR,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (profesor_id) REFERENCES profesores(id)
);
```

### Servicios

**Archivo**: `src/services/gestor_ausencias.py`

**Funciones principales**:

- `registrar_ausencia()`: Crea nueva ausencia con validaciones
- `editar_ausencia()`: Modifica ausencia existente
- `eliminar_ausencia()`: Borra permanentemente
- `desactivar_ausencia()`: Marca como inactiva
- `obtener_guardias_afectadas()`: Busca guardias del periodo
- `reasignar_guardias_automaticamente()`: Algoritmo de reasignación
- `obtener_profesores_disponibles()`: Filtra candidatos para sustitución

### Validaciones en Asignación

**Archivo**: `src/services/asignador_guardias.py`

**Función clave**: `profesor_ausente(session, profesor_id, fecha)`

Integrada en el algoritmo de generación de guardias en línea:

```python
# VALIDACIÓN AUSENCIAS: Excluir profesores ausentes en esta fecha
if profesor_ausente(session, p.id, slot.fecha):
    logger.debug(f"Profesor {p.nombre_completo} ausente el {slot.fecha}")
    continue
```

### Widget de Interfaz

**Archivo**: `src/widgets/gestionar_ausencias.py`

**Clases**:

- `GestionarAusenciasForm`: Formulario principal
- `DialogoReasignacion`: Diálogo modal para reasignación

---

## Cambios en v2.5

### Archivos Nuevos

- ✅ `src/models/models.py` - Modelo `Ausencia` añadido
- ✅ `src/services/gestor_ausencias.py` - Servicio completo
- ✅ `src/widgets/gestionar_ausencias.py` - Widget de interfaz
- ✅ `alembic/versions/3605cca11581_add_ausencias_table.py` - Migración BD

### Archivos Modificados

- ✅ `src/services/asignador_guardias.py` - Validación de ausencias
- ✅ `src/widgets/vista_calendario.py` - Visualización de ausencias
- ✅ `src/main.py` - Nueva pestaña añadida

### Líneas de Código Añadidas

- **Modelo**: ~30 líneas
- **Servicio**: ~500 líneas
- **Widget**: ~700 líneas
- **Visualización**: ~50 líneas
- **Total**: ~1,280 líneas de código nuevo

---

## Próximas Mejoras (Roadmap)

### v2.6 - Mejoras de Ausencias

- [ ] Filtros avanzados (por profesor, tipo, periodo)
- [ ] Exportación a Excel
- [ ] Soporte para ausencias por turno (medio día)
- [ ] Notificaciones automáticas de ausencias próximas
- [ ] Botón "Reactivar" para ausencias desactivadas

### v2.7 - Estadísticas de Ausencias

- [ ] Dashboard de ausencias (total, por tipo, tendencias)
- [ ] Gráficos de ausencias por mes
- [ ] Comparativa entre profesores
- [ ] Impacto en distribución de guardias

### v3.0 - Integración Avanzada

- [ ] Importar ausencias desde archivo Excel
- [ ] Sincronización con calendario Google/Outlook
- [ ] Notificaciones por email de reasignaciones
- [ ] API REST para integración con otros sistemas

---

## Soporte y Contacto

**Versión de la Documentación**: v2.5  
**Fecha**: 16 de octubre de 2025  
**Mantenido por**: Equipo Guardias de Patio

**Para reportar bugs o sugerir mejoras**:
- GitHub Issues: [https://github.com/cferrerobonet/guardias_patio/issues](https://github.com/cferrerobonet/guardias_patio/issues)
- Email: soporte@guardiaspatio.edu

---

## Conclusión

La **Gestión de Ausencias v2.5** es un hito importante que transforma Guardias de Patio en una herramienta profesional y completa. Con esta funcionalidad:

✅ **Reduces trabajo manual** en más del 80%  
✅ **Previenes errores** de asignación  
✅ **Mantienes el calendario actualizado** en tiempo real  
✅ **Tienes visibilidad completa** de ausencias

¡Aprovecha al máximo esta funcionalidad para optimizar la gestión de guardias en tu centro educativo! 🚀
